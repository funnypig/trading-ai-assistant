from langchain.chat_models import init_chat_model
from importlib.resources import files


from src.app.domain.schemas import TaskClassificationResult, AgentState
from src.app.config.config import MINI_MODEL

router_llm = init_chat_model(MINI_MODEL)


def classify_query(state: AgentState) -> dict:
    prompt = (
        files("src.app.agents.prompts")
        .joinpath("task_classification_prompt.txt")
        .read_text(encoding="utf-8")
    )
    structured_llm = router_llm.with_structured_output(TaskClassificationResult)
    result = structured_llm.invoke([
        {"role": "system", "content": prompt},
        {"role": "user", "content": state["query"]},
    ])

    return {"task_classification": result}
