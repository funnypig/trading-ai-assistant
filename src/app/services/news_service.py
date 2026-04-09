"""News service — composes Finviz news data with article registry and extraction."""

from typing import List

from src.app.data.finviz.news import get_stock_news, get_market_news
from src.app.domain.models import News
from src.app.analysis.news.registry import register, resolve, init as init_registry
from src.app.analysis.news.extractor import extract_article


def fetch_stock_news(ticker: str) -> List[News]:
    """Return recent news items for a specific ticker."""
    return get_stock_news(ticker)


def fetch_market_news() -> List[News]:
    """Return recent broad market news items."""
    return get_market_news()


def format_stock_news_feed(ticker: str) -> str:
    """Fetch and format stock news as a numbered feed string with registered article IDs."""
    news = get_stock_news(ticker)
    if not news:
        return f"No news found for {ticker}."
    lines = [f"[{register(item.url)}] {item.date} | {item.title}" for item in news]
    return f"Recent news for {ticker}:\n" + "\n".join(lines)


def format_market_news_feed() -> str:
    """Fetch and format market-wide news as a numbered feed string with registered article IDs."""
    news = get_market_news()
    if not news:
        return "No market news available."
    lines = [f"[{register(item.url)}] {item.date} | {item.title}" for item in news]
    return "Recent market news:\n" + "\n".join(lines)


def fetch_article_by_id(article_id: int) -> str:
    """Return full article text for a registered article ID."""
    url = resolve(article_id)
    if url is None:
        return f"[No article found with ID {article_id}. Call a news feed tool first.]"
    return extract_article(url)
