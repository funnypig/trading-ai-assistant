from importlib.resources import files
from langchain_core.messages import BaseMessage
from langchain_core.prompts import PromptTemplate

from src.app.graph.state import AgentState
from src.app.services.fundamental_service import fetch_stock_descriptive


synthesize_prompt = (
    files("src.app.agents.prompts")
    .joinpath("synthesize_prompt.txt")
    .read_text(encoding="utf-8")
)

synthesize_prompt_template = PromptTemplate(
    template=synthesize_prompt,
    input_variables=["user_query", "analysis_context", "previous_context", "conversation_history"],
)


def _format_messages(messages: list[BaseMessage]) -> str:
    if not messages:
        return "None"
    lines = []
    for msg in messages:
        role = "User" if msg.type == "human" else "Assistant"
        lines.append(f"{role}: {msg.content}")
    return "\n".join(lines)


class SynthesizeNode:
    def __init__(self, llm):
        self.llm = llm
        self.llm_chain = synthesize_prompt_template | llm

    def __build_context(self, state: AgentState) -> str:
        context = []

        if state["task_classification"].ticker:
            desc = fetch_stock_descriptive(state["task_classification"].ticker)
            context += ["Stock descriptive:\n", str(desc)]

        for result in state.get("results", []):
            context += [f"{result['source']}\n{result['result']}"]

        return "\n".join(context)

    def __call__(self, state: AgentState):
        response = self.llm_chain.invoke({
            "user_query": state["query"],
            "analysis_context": self.__build_context(state),
            "previous_context": state.get("previous_context", "") or "None",
            "conversation_history": _format_messages(state.get("messages", [])),
        })
        answer = response.content

        prior = state.get("previous_context", "")
        ticker = state["task_classification"].ticker or "unknown"
        updated_context = (prior + f"\n\n--- Analysis: {ticker} ---\n" + answer).strip()

        return {"final_answer": answer, "previous_context": updated_context}
