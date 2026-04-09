"""Abstract provider interfaces (Protocols) for external data sources.

Concrete implementations live in data/finviz/. New providers (e.g. Polygon,
Yahoo Finance) implement these protocols so services/ can stay provider-agnostic.
"""

from __future__ import annotations

from typing import List, Protocol, runtime_checkable

import pandas as pd

from src.app.domain.models import News, StockDescriptiveInfo


@runtime_checkable
class FundamentalDataProvider(Protocol):
    def get_financial_statements(self, ticker: str) -> str:
        """Return formatted income statement, balance sheet, and cash flow."""
        ...

    def get_stock_descriptive(self, ticker: str) -> StockDescriptiveInfo:
        """Return structured stock description, metrics, and ownership."""
        ...


@runtime_checkable
class OptionsDataProvider(Protocol):
    def get_option_chain(self, ticker: str, expiration: str | None = None) -> pd.DataFrame:
        """Return option chain DataFrame for the given ticker and expiration."""
        ...


@runtime_checkable
class NewsDataProvider(Protocol):
    def get_stock_news(self, ticker: str) -> List[News]:
        """Return recent news items for a specific ticker."""
        ...

    def get_market_news(self) -> List[News]:
        """Return recent broad market news items."""
        ...
