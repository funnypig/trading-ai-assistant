# Backward-compatibility shim — use data/finviz/fundamental.py instead.
from src.app.data.finviz.fundamental import (
    get_income_statement,
    get_balance_sheet,
    get_cash_flow,
    get_fundamental_info,
    get_stock_descriptive,
    data_as_table,
)
from src.app.domain.models import StockDescriptiveInfo

__all__ = [
    "get_income_statement",
    "get_balance_sheet",
    "get_cash_flow",
    "get_fundamental_info",
    "get_stock_descriptive",
    "data_as_table",
    "StockDescriptiveInfo",
]
