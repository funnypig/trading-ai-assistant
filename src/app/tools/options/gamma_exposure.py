from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

import numpy as np
import pandas as pd

from src.app.tools.options.common import FinvizOptionChainKeys as FK


@dataclass
class GexTableEntry:
    strike: float
    call_gex: float
    put_gex: float
    net_gex: float


def _estimate_underlying_price(chain: pd.DataFrame) -> Optional[float]:
    """Estimate spot using the strike with |delta| closest to 0.5 (ATM proxy)."""
    if chain is None or chain.empty:
        return None

    strikes = pd.to_numeric(chain[FK.STRIKE], errors="coerce")
    delta = pd.to_numeric(chain[FK.DELTA], errors="coerce").abs()
    mask = strikes.notna() & delta.notna()
    if not bool(mask.any()):
        return None

    closest_idx = (delta[mask] - 0.5).abs().idxmin()
    return float(strikes.loc[closest_idx])


def _gamma_scale(underlying_price: Optional[float]) -> float:
    """
    Scale factor for dollar gamma exposure:
    GEX = gamma * OI * contract_multiplier * S^2 * 0.01
    """
    if underlying_price is None or not np.isfinite(underlying_price):
        return 1.0
    return float(underlying_price ** 2)


def _filter_chain_for_gamma(
    chain: pd.DataFrame,
    min_abs_delta: float,
    max_abs_delta: float,
    min_oi_pct: float,
) -> pd.DataFrame:
    """Drop deep ITM/OTM and negligible OI rows to stabilize gamma metrics."""
    if chain is None or chain.empty:
        return chain

    abs_delta = pd.to_numeric(chain[FK.DELTA], errors="coerce").abs()
    delta_mask = (abs_delta >= min_abs_delta) & (abs_delta <= max_abs_delta)
    filtered = chain[delta_mask].copy()

    if filtered.empty:
        return filtered

    open_interest = pd.to_numeric(filtered[FK.OPEN_INTEREST], errors="coerce").fillna(0.0)
    total_oi = float(open_interest.sum())
    min_oi_threshold = total_oi * min_oi_pct
    return filtered[open_interest > min_oi_threshold].copy()


def _compute_gex_by_strike(
    chain: pd.DataFrame,
    scale: float,
) -> pd.DataFrame:
    """Return a DataFrame with columns call_gex and put_gex indexed by strike."""
    types = chain[FK.TYPE].astype(str).str.lower()
    strikes = pd.to_numeric(chain[FK.STRIKE], errors="coerce")
    gamma = pd.to_numeric(chain[FK.GAMMA], errors="coerce").fillna(0.0)
    oi = pd.to_numeric(chain[FK.OPEN_INTEREST], errors="coerce").fillna(0.0)

    call_mask = types == "call"
    put_mask = types == "put"

    def _grouped_gex(mask: pd.Series, sign: float) -> pd.Series:
        df = pd.DataFrame({FK.STRIKE: strikes[mask], "gex": gamma[mask] * oi[mask] * scale * sign})
        return df.dropna(subset=[FK.STRIKE]).groupby(FK.STRIKE, dropna=False)["gex"].sum()

    call_series = _grouped_gex(call_mask, 1.0).rename("call_gex")
    put_series = _grouped_gex(put_mask, -1.0).rename("put_gex")
    return pd.concat([call_series, put_series], axis=1).fillna(0.0)


def gex_strike_table(
    chain: pd.DataFrame,
    underlying_price: Optional[float] = None,
    min_abs_delta: float = 0.2,
    max_abs_delta: float = 0.8,
    min_oi_pct: float = 0.005,
    outlier_threshold: float = 0.2,
) -> List[GexTableEntry]:
    """Build a per-strike GEX table for the delta 0.2–0.8 range plus high-exposure outliers."""
    if chain is None or chain.empty:
        return []

    if underlying_price is None:
        underlying_price = _estimate_underlying_price(chain)

    scale = _gamma_scale(underlying_price)

    # Main range: delta 0.2–0.8
    main_chain = _filter_chain_for_gamma(chain, min_abs_delta, max_abs_delta, min_oi_pct)
    if main_chain is None or main_chain.empty:
        return []

    main_df = _compute_gex_by_strike(main_chain, scale)
    main_df["net_gex"] = main_df["call_gex"] + main_df["put_gex"]

    # Outliers: wider range, strikes not already in main set
    wide_chain = _filter_chain_for_gamma(chain, 0.05, 0.95, min_oi_pct)
    if wide_chain is not None and not wide_chain.empty:
        wide_df = _compute_gex_by_strike(wide_chain, scale)
        wide_df["net_gex"] = wide_df["call_gex"] + wide_df["put_gex"]
        outlier_candidates = wide_df[~wide_df.index.isin(main_df.index)]

        if not outlier_candidates.empty and not main_df.empty:
            max_net = main_df["net_gex"].abs().max()
            if max_net > 0:
                significant = outlier_candidates[outlier_candidates["net_gex"].abs() > outlier_threshold * max_net]
                main_df = pd.concat([main_df, significant]).sort_index()

    return [
        GexTableEntry(float(strike), float(row.call_gex), float(row.put_gex), float(row.net_gex))
        for strike, row in main_df.iterrows()
    ]


def calculate_gamma_flip(
    chain: pd.DataFrame,
    underlying_price: Optional[float] = None,
    min_abs_delta: float = 0.1,
    max_abs_delta: float = 0.9,
    min_oi_pct: float = 0.005,
) -> Optional[float]:
    if chain is None or chain.empty:
        return None

    if underlying_price is None:
        underlying_price = _estimate_underlying_price(chain)

    chain = _filter_chain_for_gamma(chain, min_abs_delta, max_abs_delta, min_oi_pct)
    if chain is None or chain.empty:
        return None

    strikes = pd.to_numeric(chain[FK.STRIKE], errors="coerce")
    gamma = pd.to_numeric(chain[FK.GAMMA], errors="coerce").fillna(0.0)
    open_interest = pd.to_numeric(chain[FK.OPEN_INTEREST], errors="coerce").fillna(0.0)
    types = chain[FK.TYPE].astype(str).str.lower()

    scale = _gamma_scale(underlying_price)

    # Dealer gamma sign convention: calls (+), puts (-).
    sign = np.where(types == "put", -1.0, 1.0)
    net_gex = gamma * open_interest * 100.0 * scale * sign

    grouped = (
        pd.DataFrame({FK.STRIKE: strikes, "net_gex": net_gex})
        .dropna(subset=[FK.STRIKE])
        .groupby(FK.STRIKE, dropna=False)["net_gex"]
        .sum()
        .sort_index()
    )

    if grouped.size < 2:
        return None

    strikes_sorted = grouped.index.to_numpy(dtype=float)
    values = grouped.to_numpy(dtype=float)

    # Find the first strike interval where net gamma changes sign.
    for i in range(1, values.size):
        v0, v1 = values[i - 1], values[i]
        if v0 == 0:
            return float(strikes_sorted[i - 1])
        if v1 == 0:
            return float(strikes_sorted[i])
        if v0 * v1 < 0:
            s0, s1 = strikes_sorted[i - 1], strikes_sorted[i]
            return float(s0 + (0 - v0) * (s1 - s0) / (v1 - v0))

    return None


if __name__ == "__main__":
    from pathlib import Path
    from src.app.data.finviz.get_option_chain import get_option_chain

    ticker = "MSFT"
    file_path = Path(f"/tmp/{ticker}_chain.csv")
    chain = pd.read_csv(file_path) if file_path.exists() else get_option_chain(ticker, file_path=file_path)
    print("Gamma flip:", calculate_gamma_flip(chain))
    print("GEX table:", *gex_strike_table(chain), sep="\n")
