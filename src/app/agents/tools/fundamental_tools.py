"""LangChain tools for fundamental analysis tasks."""

from __future__ import annotations

from langchain.tools import tool

from src.app.data.finviz.get_fundamental import get_fundamental_info, get_stock_descriptive


@tool
def get_financial_statements(ticker: str) -> str:
    """Fetch quarterly income statement, balance sheet, and cash flow statement for a ticker.

    Args:
        ticker: Equity ticker symbol (e.g., "AAPL").

    Returns:
        A formatted string containing all three financial statements as CSV tables.
    """
    return get_fundamental_info(ticker)


@tool
def get_stock_overview(ticker: str) -> str:
    """Fetch company description, snapshot financial metrics (P/E, market cap, margins, etc.),
    and top institutional ownership for a ticker.

    Args:
        ticker: Equity ticker symbol (e.g., "AAPL").

    Returns:
        A markdown-formatted string with company overview, financials, and ownership data.
    """
    info = get_stock_descriptive(ticker)
    return info.to_markdown()


if __name__ == "__main__":
    print(get_stock_overview.invoke({"ticker": "MSFT"}))
