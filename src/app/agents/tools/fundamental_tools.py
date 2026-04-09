"""LangChain tools for fundamental analysis tasks."""

from __future__ import annotations

from langchain.tools import tool

from src.app.infrastructure.cache.decorator import redis_cache
from src.app.services.fundamental_service import fetch_financial_statements, fetch_stock_overview


@tool
@redis_cache(ttl=86400, dumps=lambda x: x, loads=lambda x: x)
def get_financial_statements(ticker: str) -> str:
    """Fetch quarterly income statement, balance sheet, and cash flow statement for a ticker.

    Args:
        ticker: Equity ticker symbol (e.g., "AAPL").

    Returns:
        A formatted string containing all three financial statements as CSV tables.
    """
    return fetch_financial_statements(ticker)


@tool
@redis_cache(ttl=3600, dumps=lambda x: x, loads=lambda x: x)
def get_stock_overview(ticker: str) -> str:
    """Fetch company description, snapshot financial metrics (P/E, market cap, margins, etc.),
    and top institutional ownership for a ticker.

    Args:
        ticker: Equity ticker symbol (e.g., "AAPL").

    Returns:
        A markdown-formatted string with company overview, financials, and ownership data.
    """
    return fetch_stock_overview(ticker)


if __name__ == "__main__":
    print(get_stock_overview.invoke({"ticker": "MSFT"}))
