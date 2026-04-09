"""Options service — composes Finviz option chain data with analysis calculations."""

from __future__ import annotations

from typing import Sequence

import pandas as pd

from src.app.data.finviz.option_chain import get_option_chain
from src.app.analysis.options.is_option_chain_liquid import is_option_chain_liquid
from src.app.analysis.options.option_max_pain_value import calculate_max_pain
from src.app.analysis.options.get_expiration_date import get_n_nearest_expirations, get_dte_for_expiration
from src.app.analysis.options.implied_volatility import calculate_implied_volatility
from src.app.analysis.options.open_interest import calculate_call_put_activity, top_open_interest
from src.app.analysis.options.gamma_exposure import gex_strike_table, calculate_gamma_flip
from src.app.analysis.options.common import FinvizOptionChainKeys as FK, OptionLiquidityResult, OptionMaxPainResult


def check_option_liquidity(ticker: str) -> OptionLiquidityResult | str:
    """Check whether a ticker's option chain meets liquidity thresholds."""
    try:
        chain = get_option_chain(ticker)
        return is_option_chain_liquid(chain)
    except Exception as exc:
        return f"Error fetching liquidity for {ticker}: {exc}"


def compute_max_pain(ticker: str, expiration: Sequence[str] | str) -> OptionMaxPainResult | str:
    """Compute max-pain values for one or more expiration dates."""
    try:
        if isinstance(expiration, str):
            expiration_list: list[str] = [expiration]
        else:
            expiration_list = list(expiration)
        chains = [get_option_chain(ticker, exp) for exp in expiration_list]
        max_pain_values = [calculate_max_pain(chain) for chain in chains]
        return OptionMaxPainResult(expiration=expiration_list, max_pain_value=max_pain_values)
    except Exception as exc:
        return f"Error computing max pain for {ticker}: {exc}"


def build_options_descriptive(ticker: str, top_n: int = 3) -> str:
    """Return a descriptive options summary for the next top_n weekly expirations."""
    try:
        top_n = max(1, int(top_n))
    except (TypeError, ValueError):
        top_n = 10

    try:
        expiry_dates = get_n_nearest_expirations(n=top_n, years=1)
        expiry_dtes = [get_dte_for_expiration(expiration, years=1) for expiration in expiry_dates]
        expirations = list(zip(expiry_dtes, expiry_dates))
        chains = {dte: get_option_chain(ticker, expiration) for dte, expiration in expirations}

        summary_chain = next(iter(chains.values()))
        iv = calculate_implied_volatility(summary_chain)
        activity = calculate_call_put_activity(summary_chain)

        max_pain_values = {dte: calculate_max_pain(chain) for dte, chain in chains.items()}

        lines: list[str] = []
        lines.append(f"Stock {ticker.upper()}")
        lines.append(f"Implied volatility: {_format_number(iv, 2)}")
        lines.append(f"Call Volume: {_format_int(activity.call_volume)}")
        lines.append(f"Put Volume: {_format_int(activity.put_volume)}")
        lines.append(f"Call OI: {_format_int(activity.call_open_interest)}")
        lines.append(f"Put OI: {_format_int(activity.put_open_interest)}")
        lines.append(f"Put / Call ratio: {_format_number(activity.put_call_ratio, 2)}")
        lines.append("")
        lines.append("Max pain value:")
        for dte, expiration in expirations:
            lines.append(f"{dte} DTE ({expiration}): {_format_number(max_pain_values.get(dte), 2)}")

        for dte, expiration in expirations:
            chain = chains.get(dte)
            lines.append("")
            lines.append(f"### Open interest {dte} DTE ({expiration})")
            call_oi_top = top_open_interest(chain, "call")
            put_oi_top = top_open_interest(chain, "put")
            lines.extend(_format_top_list("Top 10 Call OI:", call_oi_top, "OI", "open_interest"))
            lines.extend(_format_top_list("Top 10 Put OI:", put_oi_top, "OI", "open_interest"))

        for dte, expiration in expirations:
            chain = chains.get(dte)
            lines.append("")
            lines.append(f"### Gamma exposure {dte} DTE ({expiration})")
            gamma_flip = calculate_gamma_flip(chain)
            lines.append(f"Gamma flip: {_format_number(gamma_flip, 2)}")
            lines.extend(_format_gex_table(gex_strike_table(chain)))

        return "\n".join(lines).strip()
    except Exception as exc:
        return f"Error fetching options summary for {ticker}: {exc}"


def get_top_open_interest(
    ticker: str,
    expiration: str,
    option_type: str = "both",
    top_n: int = 10,
) -> str:
    """Return the top open-interest strikes for a specific expiration date."""
    try:
        chain = get_option_chain(ticker, expiration)
        lines = [f"Top OI for {ticker.upper()} expiration {expiration}"]
        types = ["call", "put"] if option_type.lower() == "both" else [option_type.lower()]
        for ot in types:
            entries = top_open_interest(chain, ot, top_n)
            lines.extend(_format_top_list(f"Top {top_n} {ot.capitalize()} OI:", entries, "OI", "open_interest"))
        return "\n".join(lines)
    except Exception as exc:
        return f"Error fetching top OI for {ticker} {expiration}: {exc}"


def get_filtered_option_chain(
    ticker: str,
    expiration: str,
    delta_min: float = 0.1,
    delta_max: float = 0.9,
    option_type: str | None = None,
) -> str:
    """Return a delta-filtered option chain for a specific expiration."""
    try:
        chain = get_option_chain(ticker, expiration)
        cols = [FK.STRIKE, FK.TYPE, FK.BID, FK.ASK, FK.IV, FK.DELTA, FK.GAMMA, FK.THETA, FK.VOLUME, FK.OPEN_INTEREST]
        df = chain[[c for c in cols if c in chain.columns]].copy()
        if FK.DELTA not in df.columns:
            return f"No Delta column available for {ticker} {expiration}"
        df[FK.DELTA] = pd.to_numeric(df[FK.DELTA], errors="coerce")
        mask = df[FK.DELTA].abs().between(delta_min, delta_max)
        if option_type:
            mask &= df[FK.TYPE].astype(str).str.lower() == option_type.lower()
        df = df[mask].sort_values([FK.TYPE, FK.STRIKE])
        if df.empty:
            return f"No contracts found for {ticker} {expiration} with delta {delta_min}-{delta_max}"
        return f"Filtered chain {ticker.upper()} {expiration} (delta {delta_min}-{delta_max}):\n{df.to_string(index=False)}"
    except Exception as exc:
        return f"Error fetching filtered chain for {ticker} {expiration}: {exc}"


def get_raw_option_chain(ticker: str, expiration: str) -> str:
    """Return the full raw option chain for a specific expiration."""
    try:
        chain = get_option_chain(ticker, expiration)
        cols = [FK.STRIKE, FK.TYPE, FK.BID, FK.ASK, FK.IV, FK.DELTA, FK.GAMMA, FK.THETA, FK.VEGA, FK.VOLUME, FK.OPEN_INTEREST]
        present_cols = [c for c in cols if c in chain.columns]
        sort_cols = [c for c in [FK.TYPE, FK.STRIKE] if c in chain.columns]
        df = chain[present_cols].sort_values(sort_cols) if sort_cols else chain[present_cols]
        return f"Option chain {ticker.upper()} {expiration}:\n{df.to_string(index=False)}"
    except Exception as exc:
        return f"Error fetching raw chain for {ticker} {expiration}: {exc}"


# ── Formatting helpers (pure, no I/O) ────────────────────────────────────────

def _format_number(value: float | None, decimals: int = 2) -> str:
    if value is None:
        return "N/A"
    return f"{value:,.{decimals}f}"


def _format_int(value: float | None) -> str:
    if value is None:
        return "N/A"
    return f"{value:,.0f}"


def _format_strike(value: float | None) -> str:
    if value is None:
        return "N/A"
    return f"{value:.2f}".rstrip("0").rstrip(".")


def _format_gex_table(entries: list) -> list[str]:
    if not entries:
        return ["GEX table: N/A"]
    header = f"{'Strike':>8} | {'Call GEX':>12} | {'Put GEX':>12} | {'Net GEX':>12}"
    sep = "-" * len(header)
    rows = [header, sep]
    for e in entries:
        rows.append(
            f"{_format_strike(e.strike):>8} | "
            f"{_format_number(e.call_gex):>12} | "
            f"{_format_number(e.put_gex):>12} | "
            f"{_format_number(e.net_gex):>12}"
        )
    return rows


def _format_top_list(
    title: str,
    items: Sequence[object],
    value_label: str,
    value_attr: str,
    value_formatter=_format_int,
) -> list[str]:
    lines = [title]
    if not items:
        lines.append("- N/A")
        return lines
    for item in items:
        strike = getattr(item, "strike", None)
        value = getattr(item, value_attr, None)
        lines.append(f"- {_format_strike(strike)}: {value_label} {value_formatter(value)}")
    return lines
