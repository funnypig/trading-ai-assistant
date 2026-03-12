import asyncio

import chainlit as cl
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.checkpoint.memory import MemorySaver

from src.app.graph.graph import build_graph

_checkpointer = MemorySaver()
_graph = build_graph(checkpointer=_checkpointer)


@cl.on_chat_start
async def on_chat_start():
    cl.user_session.set("thread_id", cl.context.session.id)


@cl.on_message
async def on_message(message: cl.Message):
    thread_id = cl.user_session.get("thread_id")
    config = {"configurable": {"thread_id": thread_id}}

    msg = cl.Message(content="")
    await msg.send()

    result = await asyncio.to_thread(
        _graph.invoke,
        {
            "query": message.content,
            "messages": [HumanMessage(content=message.content)],
            "results": [],  # Reset per-turn results
        },
        config,
    )

    final_answer = result.get("final_answer", "No answer produced.")
    msg.content = final_answer
    await msg.update()

    # Append AI response to message history so TC sees it next turn
    _graph.update_state(
        config,
        {"messages": [AIMessage(content=final_answer)]},
    )
