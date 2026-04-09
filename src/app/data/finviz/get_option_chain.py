# Backward-compatibility shim — use data/finviz/option_chain.py instead.
from src.app.data.finviz.option_chain import get_option_chain

__all__ = ["get_option_chain"]
