"""LangChain tools for option-chain analysis tasks."""

from __future__ import annotations

from typing import Sequence

from langchain.tools import tool

from src.app.analysis.options.common import OptionLiquidityResult, OptionMaxPainResult
from src.app.services.options_service import (
    check_option_liquidity,
    compute_max_pain,
    build_options_descriptive,
    get_top_open_interest,
    get_filtered_option_chain,
    get_raw_option_chain,
)


@tool
def stock_option_liquidity(ticker: str) -> OptionLiquidityResult | str:
    """Check whether a ticker's option chain meets liquidity thresholds.

    Args:
        ticker: Equity ticker symbol (e.g., "AAPL").

    Returns:
        A structured result describing liquidity status and diagnostics.
    """
    return check_option_liquidity(ticker)


@tool
def option_max_pain_value(ticker: str, expiration: Sequence[str] | str) -> OptionMaxPainResult | str:
    """Compute max-pain values for one or more expiration dates.

    Args:
        ticker: Equity ticker symbol (e.g., "AAPL").
        expiration: Single expiration date string or a sequence of date strings
            formatted as "YYYY-MM-DD".

    Returns:
        A structured result containing the expirations and their max-pain values.
    """
    return compute_max_pain(ticker, expiration)


@tool
def get_options_descriptive(ticker: str, top_n: int = 3) -> str:
    """Return a descriptive options summary for the next top_n weekly expirations:
    - Volume, Open interest
    - Gamma exposure and gamma flip
    - Max pain
    - Descriptive info
    """
    return build_options_descriptive(ticker, top_n)


@tool
def option_chain_top_oi(
    ticker: str,
    expiration: str,
    option_type: str = "both",
    top_n: int = 10,
) -> str:
    """Return the top open-interest strikes for a specific expiration date.

    Use this when you need OI detail for an expiration not covered by
    get_options_descriptive, or when you need more than 10 strikes.

    Args:
        ticker: Equity ticker symbol (e.g., "AAPL").
        expiration: Expiration date formatted as "YYYY-MM-DD".
        option_type: "call", "put", or "both" (default "both").
        top_n: Number of top strikes to return (default 10).
    """
    return get_top_open_interest(ticker, expiration, option_type, top_n)


@tool
def option_chain_filtered(
    ticker: str,
    expiration: str,
    delta_min: float = 0.1,
    delta_max: float = 0.9,
    option_type: str | None = None,
) -> str:
    """Return a filtered option chain for a specific expiration.

    Fetches the full chain and filters by delta range and optionally option type.
    Use this to inspect ATM contracts, specific delta buckets, or directional positioning.

    Args:
        ticker: Equity ticker symbol (e.g., "AAPL").
        expiration: Expiration date formatted as "YYYY-MM-DD".
        delta_min: Minimum absolute delta to include (default 0.1).
        delta_max: Maximum absolute delta to include (default 0.9).
        option_type: "call", "put", or None for both (default None).
    """
    return get_filtered_option_chain(ticker, expiration, delta_min, delta_max, option_type)


@tool
def option_chain_raw(ticker: str, expiration: str) -> str:
    """Return the full raw option chain for a specific expiration as a formatted table.

    Use this when you need complete contract-level data that other tools do not provide,
    such as theta, vega, rho, or bid/ask spreads across all strikes.

    Args:
        ticker: Equity ticker symbol (e.g., "AAPL").
        expiration: Expiration date formatted as "YYYY-MM-DD".
    """
    return get_raw_option_chain(ticker, expiration)


if __name__ == "__main__":
    res = option_max_pain_value.invoke({
        "ticker": "CF",
        "expiration": ["2026-03-13", "2026-03-20", "2026-03-27"]
    })
    print(res)
