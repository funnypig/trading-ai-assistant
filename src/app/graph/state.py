import operator
from typing import Annotated, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

from src.app.domain.schemas import TaskClassificationResult


class AgentInput(TypedDict):
    """Simple input state for each subagent."""
    query: str


class AgentOutput(TypedDict):
    """Output from each subagent."""
    source: str
    result: str


def _results_reducer(existing: list, new: list) -> list:
    """Empty list = reset (new turn). Non-empty list = append (parallel fan-out within a turn)."""
    if not new:
        return []
    return existing + new


class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]  # Conversation history, persisted by checkpointer
    previous_context: str  # Accumulated synthesis text from prior analysis runs
    query: str
    task_classification: TaskClassificationResult
    results: Annotated[list[AgentOutput], _results_reducer]  # Resets on [] input, appends otherwise
    final_answer: str
