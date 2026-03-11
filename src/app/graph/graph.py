from langchain.chat_models import init_chat_model
from langgraph.graph import StateGraph, START, END
from langgraph.graph.state import CompiledStateGraph

from src.app.config.config import MINI_MODEL, SMART_MODEL
from src.app.domain.schemas import AgentState
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
    return list(tc.invoke_agents)


def build_graph() -> CompiledStateGraph:
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

    return graph.compile()
