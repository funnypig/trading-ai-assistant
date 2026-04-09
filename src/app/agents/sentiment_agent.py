from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from importlib.resources import files

from src.app.agents.tools.sentiment_tools import get_stock_news_feed, get_market_news_feed, fetch_article_content
from src.app.analysis.news.registry import init as init_registry
from src.app.config.config import MINI_MODEL

model = init_chat_model(MINI_MODEL)

sentiment_analysis_agent = create_agent(
    model,
    tools=[get_stock_news_feed, get_market_news_feed, fetch_article_content],
    system_prompt=(
        files("src.app.agents.prompts")
        .joinpath("sentiment_analysis_agent_prompt.txt")
        .read_text(encoding="utf-8")
    ),
)


if __name__ == "__main__":
    init_registry()

    query = "Analyze sentiment for USAR."

    for step in sentiment_analysis_agent.stream(
        {"messages": [{"role": "user", "content": query}]}
    ):
        for update in step.values():
            for message in update.get("messages", []):
                message.pretty_print()
