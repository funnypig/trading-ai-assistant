"""LangChain tools for sentiment analysis tasks."""

from __future__ import annotations

from langchain.tools import tool

from src.app.services.news_service import (
    format_stock_news_feed,
    format_market_news_feed,
    fetch_article_by_id,
)


@tool
def fetch_article_content(article_id: int) -> str:
    """Fetch full article text by its ID from the news feed.

    Call get_stock_news_feed or get_market_news_feed first to populate article IDs,
    then pass the desired ID here to retrieve the full content.

    Args:
        article_id: Integer ID shown in brackets next to the headline (e.g. 3 for [3]).

    Returns:
        Extracted article text, or a short message explaining why extraction failed
        (unknown ID, paywall, bot protection, etc.).
    """
    return fetch_article_by_id(article_id)


@tool
def get_stock_news_feed(ticker: str) -> str:
    """Fetch recent news headlines for a specific stock ticker.

    Each headline is prefixed with a numeric ID in brackets. Pass the ID to
    fetch_article_content to retrieve the full text of any article.

    Args:
        ticker: Equity ticker symbol (e.g., "AAPL").

    Returns:
        A formatted string with numbered, dated news headlines for the given stock.
    """
    return format_stock_news_feed(ticker)


@tool
def get_market_news_feed() -> str:
    """Fetch recent broad market and macro news headlines.

    Each headline is prefixed with a numeric ID in brackets. Pass the ID to
    fetch_article_content to retrieve the full text of any article.

    Returns:
        A formatted string with numbered, dated market-wide news headlines.
    """
    return format_market_news_feed()


if __name__ == "__main__":
    print(get_stock_news_feed.invoke({"ticker": "NVDA"}))
    print()
    print(fetch_article_content.invoke({"article_id": 1}))
    print()
    print(fetch_article_content.invoke({"article_id": 999}))
