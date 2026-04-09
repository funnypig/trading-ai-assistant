"""Fundamental data service — composes Finviz data layer for agent consumption."""

from src.app.data.finviz.fundamental import get_fundamental_info, get_stock_descriptive
from src.app.domain.models import StockDescriptiveInfo


def fetch_financial_statements(ticker: str) -> str:
    """Return formatted income statement, balance sheet, and cash flow for a ticker."""
    return get_fundamental_info(ticker)


def fetch_stock_overview(ticker: str) -> str:
    """Return markdown-formatted company description, metrics, and ownership for a ticker."""
    return get_stock_descriptive(ticker).to_markdown()


def fetch_stock_descriptive(ticker: str) -> StockDescriptiveInfo:
    """Return structured StockDescriptiveInfo for a ticker (used by synthesize node)."""
    return get_stock_descriptive(ticker)
