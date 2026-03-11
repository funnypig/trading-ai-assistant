from importlib.resources import files

from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate

from src.app.domain.schemas import AgentState, TaskClassificationResult

task_classification_parser = PydanticOutputParser(pydantic_object=TaskClassificationResult)

task_classification_prompt = (
    files("src.app.agents.prompts")
    .joinpath("task_classification_prompt.txt")
    .read_text(encoding="utf-8")
)

task_classification_prompt_template = PromptTemplate(
    template=task_classification_prompt + "\n\n{format_instructions}",
    input_variables=["input_task"],
    partial_variables={"format_instructions": task_classification_parser.get_format_instructions()},
)


class TaskClassificationNode:
    def __init__(self, llm):
        self.llm = llm
        self.llm_chain = task_classification_prompt_template | llm | task_classification_parser

    def __call__(self, state: AgentState):
        parsed_response = self.llm_chain.invoke(dict(input_task=state.query))

        return dict(task_classification=parsed_response)
