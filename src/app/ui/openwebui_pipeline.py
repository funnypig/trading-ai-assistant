"""
OpenWebUI Pipeline adapter for the trading AI assistant.

Implements the OpenWebUI Pipelines interface so the LangGraph agent can be
used as a model in OpenWebUI. The full graph (task classification, parallel
agents, synthesis) runs unchanged — this file is only a transport layer.

Deploy: place this file in the OpenWebUI Pipelines volume and register the
pipeline service URL in OpenWebUI admin → Pipelines.
"""

import asyncio
import logging
import queue
import threading
from typing import Generator

from langchain_core.messages import HumanMessage, AIMessage
from langfuse import Langfuse
from psycopg import AsyncConnection
from pydantic import BaseModel

from src.app.config.settings import settings
from src.app.graph.graph import create_graph
from src.app.observability.langfuse import get_langfuse_handler, flush_handler

log = logging.getLogger(__name__)

_NODE_LABELS = {
    "task_classification": "Classifying task",
    "fundamental": "Fundamental analysis",
    "sentiment": "Sentiment analysis",
    "option": "Options analysis",
    "synthesize": "Synthesizing answer",
    "recurring_task": "Scheduling task",
}

_DONE = object()  # sentinel to signal end of stream


class Pipeline:
    class Valves(BaseModel):
        pass

    def __init__(self):
        self.name = "Trading AI Assistant"
        self._graph = None
        self._loop = asyncio.new_event_loop()
        # run a dedicated event loop in a background thread so async graph
        # calls can be driven from the sync generator that OpenWebUI expects
        threading.Thread(target=self._loop.run_forever, daemon=True).start()

    async def _health_check_db(self) -> None:
        try:
            conn = await AsyncConnection.connect(settings.supabase_db_url, autocommit=True)
            await conn.execute("SELECT 1")
            await conn.close()
            log.info("[health] database: OK")
        except Exception as exc:
            log.error("[health] database: FAILED — %s", exc)

    async def _health_check_langfuse(self) -> None:
        try:
            lf = Langfuse()
            ok = await asyncio.get_running_loop().run_in_executor(None, lf.auth_check)
            if ok:
                log.info("[health] Langfuse: OK")
            else:
                log.error(
                    "[health] Langfuse: auth failed — check LANGFUSE_PUBLIC_KEY / "
                    "LANGFUSE_SECRET_KEY / LANGFUSE_HOST"
                )
        except Exception as exc:
            log.error("[health] Langfuse: FAILED — %s", exc)

    async def on_startup(self):
        await asyncio.gather(
            self._health_check_db(),
            self._health_check_langfuse(),
        )
        future = asyncio.run_coroutine_threadsafe(create_graph(), self._loop)
        self._graph = future.result(timeout=60)

    async def on_shutdown(self):
        pass

    def pipe(
        self,
        user_message: str,
        model_id: str,
        messages: list[dict],
        body: dict,
    ) -> Generator[str, None, None]:
        if self._graph is None:
            future = asyncio.run_coroutine_threadsafe(create_graph(), self._loop)
            self._graph = future.result(timeout=60)

        thread_id = body.get("chat_id", "default")
        langfuse_handler = get_langfuse_handler()
        config = {
            "configurable": {"thread_id": thread_id},
            "callbacks": [langfuse_handler],
        }

        q: queue.Queue = queue.Queue()

        async def _run():
            try:
                final_answer = None
                async for event in self._graph.astream_events(
                    {
                        "query": user_message,
                        "messages": [HumanMessage(content=user_message)],
                        "results": [],
                    },
                    config,
                    version="v2",
                ):
                    kind = event["event"]
                    name = event.get("name", "")

                    if kind == "on_chain_start" and name in _NODE_LABELS:
                        q.put(f"\n> {_NODE_LABELS[name]}...\n")

                    elif kind == "on_chat_model_stream":
                        if event.get("metadata", {}).get("langgraph_node") == "synthesize":
                            token = event["data"]["chunk"].content
                            if token:
                                q.put(token)

                    elif kind == "on_chain_end" and name == "synthesize":
                        final_answer = event["data"].get("output", {}).get("final_answer")

                if final_answer:
                    await self._graph.aupdate_state(
                        config,
                        {"messages": [AIMessage(content=final_answer)]},
                    )
            except Exception:
                log.exception("pipe() async run failed")
                q.put("Error: pipeline failed, check trading-pipeline logs.")
            finally:
                await flush_handler(langfuse_handler)
                q.put(_DONE)

        asyncio.run_coroutine_threadsafe(_run(), self._loop)

        while True:
            item = q.get()
            if item is _DONE:
                break
            yield item
