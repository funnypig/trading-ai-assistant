from langchain.chat_models import init_chat_model
from langgraph.graph import StateGraph, START, END
from langgraph.graph.state import CompiledStateGraph

from src.app.config.models import MINI_MODEL, SMART_MODEL
from src.app.graph.state import AgentState
from src.app.infrastructure.persistence.checkpointer import create_postgres_checkpointer
from src.app.agents.nodes import (
    TaskClassificationNode,
    FundamentalAnalysisNode,
    SentimentAnalysisNode,
    OptionAnalysisNode,
    SynthesizeNode,
    RecurringTaskNode,
)


def _route_task(state: AgentState) -> list[str]:
    tc = state["task_classification"]
    if tc.task_type == "recurring":
        return ["recurring_task"]
    if not tc.invoke_agents:
        return ["synthesize"]  # Answer from previous_context, no new data needed
    return list(tc.invoke_agents)


def build_graph(checkpointer=None) -> CompiledStateGraph:
    llm_mini = init_chat_model(MINI_MODEL)
    llm_smart = init_chat_model(SMART_MODEL)

    graph = StateGraph(AgentState)

    graph.add_node("task_classification", TaskClassificationNode(llm_mini))
    graph.add_node("recurring_task", RecurringTaskNode())
    graph.add_node("fundamental", FundamentalAnalysisNode())
    graph.add_node("sentiment", SentimentAnalysisNode())
    graph.add_node("option", OptionAnalysisNode())
    graph.add_node("synthesize", SynthesizeNode(llm_smart))

    graph.add_edge(START, "task_classification")

    graph.add_conditional_edges(
        "task_classification",
        _route_task,
        {
            "recurring_task": "recurring_task",
            "synthesize": "synthesize",
            "fundamental": "fundamental",
            "sentiment": "sentiment",
            "option": "option",
        },
    )

    graph.add_edge("fundamental", "synthesize")
    graph.add_edge("sentiment", "synthesize")
    graph.add_edge("option", "synthesize")
    graph.add_edge("recurring_task", END)
    graph.add_edge("synthesize", END)

    return graph.compile(checkpointer=checkpointer)


async def create_graph() -> CompiledStateGraph:
    checkpointer = await create_postgres_checkpointer()
    return build_graph(checkpointer=checkpointer)
