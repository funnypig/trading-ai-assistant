from importlib.resources import files

from langchain_core.messages import BaseMessage
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate

from src.app.domain.schemas import TaskClassificationResult
from src.app.graph.state import AgentState

task_classification_parser = PydanticOutputParser(pydantic_object=TaskClassificationResult)

task_classification_prompt = (
    files("src.app.agents.prompts")
    .joinpath("task_classification_prompt.txt")
    .read_text(encoding="utf-8")
)

task_classification_prompt_template = PromptTemplate(
    template=task_classification_prompt + "\n\n{format_instructions}",
    input_variables=["input_task", "conversation_history", "available_context"],
    partial_variables={"format_instructions": task_classification_parser.get_format_instructions()},
)


def _format_messages(messages: list[BaseMessage]) -> str:
    if not messages:
        return "None"
    lines = []
    for msg in messages:
        role = "User" if msg.type == "human" else "Assistant"
        lines.append(f"{role}: {msg.content}")
    return "\n".join(lines)


class TaskClassificationNode:
    def __init__(self, llm):
        self.llm = llm
        self.llm_chain = task_classification_prompt_template | llm | task_classification_parser

    def __call__(self, state: AgentState):
        history = _format_messages(state.get("messages", [])[-6:])
        available = state.get("previous_context", "") or "None"

        parsed_response = self.llm_chain.invoke({
            "input_task": state["query"],
            "conversation_history": history,
            "available_context": available,
        })

        return {"task_classification": parsed_response}
