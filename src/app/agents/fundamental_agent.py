from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from importlib.resources import files

from src.app.agents.tools.fundamental_tools import get_financial_statements, get_stock_overview
from src.app.config.config import DATA_ANALYSIS_MODEL

model = init_chat_model(DATA_ANALYSIS_MODEL)

fundamental_analysis_agent = create_agent(
    model,
    tools=[get_financial_statements, get_stock_overview],
    system_prompt=(
        files("src.app.agents.prompts")
        .joinpath("fundamental_analysis_agent_prompt.txt")
        .read_text(encoding="utf-8")
    ),
)


if __name__ == "__main__":
    query = "Analyze CF fundamentals. What is fair value of the company?"

    for step in fundamental_analysis_agent.stream(
        {"messages": [{"role": "user", "content": query}]}
    ):
        for update in step.values():
            for message in update.get("messages", []):
                message.pretty_print()
