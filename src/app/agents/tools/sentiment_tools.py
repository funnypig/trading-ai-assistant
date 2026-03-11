"""LangChain tools for sentiment analysis tasks."""

from __future__ import annotations

from langchain.tools import tool

from src.app.data.finviz.get_news import get_stock_news, get_market_news
from src.app.tools.news.extractor import extract_article
from src.app.tools.news.registry import register, resolve


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
    url = resolve(article_id)
    if url is None:
        return f"[No article found with ID {article_id}. Call a news feed tool first.]"
    return extract_article(url)


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
    news = get_stock_news(ticker)
    if not news:
        return f"No news found for {ticker}."
    lines = [f"[{register(item.url)}] {item.date} | {item.title}" for item in news]
    return f"Recent news for {ticker}:\n" + "\n".join(lines)


@tool
def get_market_news_feed() -> str:
    """Fetch recent broad market and macro news headlines.

    Each headline is prefixed with a numeric ID in brackets. Pass the ID to
    fetch_article_content to retrieve the full text of any article.

    Returns:
        A formatted string with numbered, dated market-wide news headlines.
    """
    news = get_market_news()
    if not news:
        return "No market news available."
    lines = [f"[{register(item.url)}] {item.date} | {item.title}" for item in news]
    return "Recent market news:\n" + "\n".join(lines)


if __name__ == "__main__":
    print(get_stock_news_feed.invoke({"ticker": "NVDA"}))
    print()
    print(fetch_article_content.invoke({"article_id": 1}))
    print()
    print(fetch_article_content.invoke({"article_id": 999}))
