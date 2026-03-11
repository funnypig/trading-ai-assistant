from importlib.resources import files
from langchain_core.prompts import PromptTemplate

from src.app.domain.schemas import AgentState
from src.app.data.finviz.get_fundamental import get_stock_descriptive


synthesize_prompt = (
    files("src.app.agents.prompts")
    .joinpath("synthesize_prompt.txt")
    .read_text(encoding="utf-8")
)

synthesize_prompt_template = PromptTemplate(
    template=synthesize_prompt,
    input_variables=["user_query", "analysis_context"],
)


class SynthesizeNode:
    def __init__(self, llm):
        self.llm = llm
        self.llm_chain = synthesize_prompt_template | llm

    def __build_context(self, state: AgentState) -> str:
        context = []

        if state.task_classification.ticker:
            desc = get_stock_descriptive(state.task_classification.ticker)
            context += ["Stock descriptive:\n", desc]

        for result in state.results:
            context += [f"{result.source}\n{result.result}"]

        return "\n".join(context)

    def __call__(self, state: AgentState):
        response = self.llm_chain.invoke(dict(
            user_query=state.query,
            analysis_context=self.__build_context(state),
        ))
        answer = response["messages"][-1].content

        return dict(final_answer=answer)
