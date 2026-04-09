from typing import List, Literal
from pydantic import BaseModel


class TaskClassificationResult(BaseModel):
    """
    Task classification result:
    - task_type is "immediate" agent execution or "recurring"
    - task_schedule for "recurring" tasks, e.g. "1H", "15M"
    - task_query defines conditions, triggers, notifications and other task-related details
    - agent_query defines what agent should do, e.g. stock analysis or option strategy builder
    - invoke_agents defines which agents should be executed to accomplish given task
    - ticker is extracted from user input, e.g. microsoft would be "MSFT"
    """
    task_type: Literal["immediate", "recurring"]
    task_schedule: str | None
    task_query: str | None
    agent_query: str
    agent_queries: dict[str, str] = {}
    invoke_agents: List[Literal["option", "fundamental", "sentiment"]]
    ticker: str | None
