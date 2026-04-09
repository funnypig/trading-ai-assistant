# Backward-compatibility shim — use data/finviz/quote.py instead.
from src.app.data.finviz.quote import get_stock_quote, FinvizQuoteParameters

__all__ = ["get_stock_quote", "FinvizQuoteParameters"]
