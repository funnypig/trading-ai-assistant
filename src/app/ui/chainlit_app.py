import asyncio

import chainlit as cl
from langchain_core.messages import HumanMessage, AIMessage
from langfuse.langchain import CallbackHandler

from src.app.graph.graph import create_graph

_graph = None

_NODE_LABELS = {
    "task_classification": "Classifying task",
    "fundamental": "Fundamental analysis",
    "sentiment": "Sentiment analysis",
    "option": "Options analysis",
    "synthesize": "Synthesizing answer",
    "recurring_task": "Scheduling task",
}


@cl.on_chat_start
async def on_chat_start():
    global _graph
    if _graph is None:
        _graph = await create_graph()
    cl.user_session.set("thread_id", cl.context.session.id)


@cl.on_message
async def on_message(message: cl.Message):
    thread_id = cl.user_session.get("thread_id")
    langfuse_handler = CallbackHandler()
    config = {
        "configurable": {"thread_id": thread_id},
        "callbacks": [langfuse_handler],
    }

    msg = cl.Message(content="")
    await msg.send()

    streamed: list[str] = []
    final_answer: str | None = None
    active_steps: dict[str, cl.Step] = {}

    async for event in _graph.astream_events(
        {
            "query": message.content,
            "messages": [HumanMessage(content=message.content)],
            "results": [],
        },
        config,
        version="v2",
    ):
        kind = event["event"]
        name = event.get("name", "")

        if kind == "on_chain_start" and name in _NODE_LABELS:
            step = cl.Step(name=_NODE_LABELS[name], type="tool")
            await step.send()
            active_steps[name] = step

        elif kind == "on_chain_end" and name in _NODE_LABELS:
            step = active_steps.pop(name, None)
            if step:
                output = event["data"].get("output") or {}
                if isinstance(output, dict) and "final_answer" in output:
                    final_answer = output["final_answer"]
                step.output = "Done"
                await step.update()

        elif kind == "on_chat_model_stream":
            if event.get("metadata", {}).get("langgraph_node") == "synthesize":
                token = event["data"]["chunk"].content
                if token:
                    await msg.stream_token(token)
                    streamed.append(token)

    # Non-streamed paths (e.g. recurring_task) — fill message after the fact
    if not streamed and final_answer:
        msg.content = final_answer
        await msg.update()

    final_text = "".join(streamed) or final_answer or ""
    if final_text:
        await _graph.aupdate_state(
            config,
            {"messages": [AIMessage(content=final_text)]},
        )

    # flush blocks until all queued trace events are sent; run_in_executor avoids blocking the event loop
    await asyncio.get_event_loop().run_in_executor(None, langfuse_handler.flush)
