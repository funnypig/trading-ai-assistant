from typing import Optional
import pandas as pd
import numpy as np

from src.app.analysis.options.common import FinvizOptionChainKeys as FK


def calculate_max_pain(
    df: pd.DataFrame,
    *,
    strike_col: str = FK.STRIKE,
    oi_col: str = FK.OPEN_INTEREST,
    type_col: str = FK.TYPE,
    delta_col: str = FK.DELTA,
    call_value: str = "call",
    put_value: str = "put",
    min_abs_delta: float = 0.05,  # Filter out options with |delta| < 0.05
    max_abs_delta: float = 0.95,  # Filter out deep ITM options
    min_oi_pct: float = 0.005,   # Ignore strikes with <0.5% of total OI
) -> Optional[float]:
    """
    Calculate Max Pain (option strike with minimal total payout) from an option chain.

    Assumptions:
      - df contains both Calls and Puts for the same underlying and expiration.
      - Open interest is used as contract count weight.
      - One option contract controls 100 shares (multiplier cancels for argmin, so omitted).
      - Types are identified by df[type_col] == call_value / put_value (defaults: "Call"/"Put").

    Returns:
      - Strike (float) representing max pain, or None if insufficient data.
    """
    if df is None or df.empty:
        return None

    # Filter out OTM options
    abs_delta = df[delta_col].abs()
    delta_mask = (abs_delta >= min_abs_delta) & (abs_delta <= max_abs_delta)
    df = df[delta_mask].copy()

    # Filter small OI
    total_oi = df[oi_col].sum()
    min_oi_threshold = total_oi * min_oi_pct
    df = df[df[oi_col] > min_oi_threshold]

    # Prepare dataframe
    strikes = pd.to_numeric(df[strike_col], errors="coerce")
    oi = pd.to_numeric(df[oi_col], errors="coerce").fillna(0.0)
    typ = df[type_col].astype(str)

    valid_mask = strikes.notna() & oi.notna() & typ.notna()
    if not bool(valid_mask.any()):
        return None

    chain = df.loc[valid_mask, [strike_col, oi_col, type_col]].copy()
    chain[strike_col] = pd.to_numeric(chain[strike_col], errors="coerce")
    chain[oi_col] = pd.to_numeric(chain[oi_col], errors="coerce").fillna(0.0)
    chain[type_col] = chain[type_col].astype(str)

    chain = chain[chain[strike_col].notna()]
    if chain.empty:
        return None

    # Aggregate OI per strike per type (in case of duplicates)
    grouped = (
        chain.groupby([strike_col, type_col], dropna=False)[oi_col]
        .sum()
        .unstack(type_col, fill_value=0.0)
    )

    # Ensure both columns exist
    call_oi = grouped[call_value] if call_value in grouped.columns else pd.Series(0.0, index=grouped.index)
    put_oi = grouped[put_value] if put_value in grouped.columns else pd.Series(0.0, index=grouped.index)

    strikes_unique = grouped.index.to_numpy(dtype=float)
    if strikes_unique.size == 0:
        return None

    # Candidate settlement prices = observed strikes
    S = strikes_unique  # shape (n,)

    # Build pairwise intrinsic distances (n x n)
    # For each candidate settlement S_j:
    #   calls at K_i pay max(S_j - K_i, 0) * OI_call(K_i)
    #   puts  at K_i pay max(K_i - S_j, 0) * OI_put(K_i)
    K = strikes_unique.reshape(-1, 1)  # (n,1)
    Sj = S.reshape(1, -1)              # (1,n)

    call_pay = np.maximum(Sj - K, 0.0) * call_oi.to_numpy(dtype=float).reshape(-1, 1)
    put_pay = np.maximum(K - Sj, 0.0) * put_oi.to_numpy(dtype=float).reshape(-1, 1)

    total_pain = call_pay.sum(axis=0) + put_pay.sum(axis=0)  # (n,)

    if not np.isfinite(total_pain).any():
        return None

    max_pain_strike = float(S[np.nanargmin(total_pain)])
    return max_pain_strike


if __name__ == "__main__":
    from src.app.data.finviz.get_option_chain import get_option_chain
    from pathlib import Path

    """
    MSFT - all liquid
    CCCX - Call liquid, Put not liquid
    QNCX - shit options
    """
    ticker = 'QQQ'
    file_path = Path(f'/tmp/{ticker}_chain.csv')
    
    if file_path.exists():
        chain = pd.read_csv(file_path)
    else:
        chain = get_option_chain(ticker, expiration='2026-02-13', file_path=file_path)
    
    result = calculate_max_pain(chain)
    print(result)
