from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

import pandas as pd

from src.app.tools.options.common import FinvizOptionChainKeys as FK


@dataclass
class OptionActivity:
    call_volume: float
    put_volume: float
    call_open_interest: float
    put_open_interest: float
    put_call_ratio: Optional[float]


@dataclass
class OpenInterestEntry:
    strike: float
    open_interest: float


def calculate_call_put_activity(
    chain: pd.DataFrame,
) -> OptionActivity:
    if chain is None or chain.empty:
        return OptionActivity(
            call_volume=0.0,
            put_volume=0.0,
            call_open_interest=0.0,
            put_open_interest=0.0,
            put_call_ratio=None,
        )

    types = chain[FK.TYPE].astype(str).str.lower()
    volume = pd.to_numeric(chain[FK.VOLUME], errors="coerce").fillna(0.0)
    open_interest = pd.to_numeric(chain[FK.OPEN_INTEREST], errors="coerce").fillna(0.0)

    call_mask = types == "call"
    put_mask = types == "put"

    call_volume = float(volume[call_mask].sum())
    put_volume = float(volume[put_mask].sum())
    call_oi = float(open_interest[call_mask].sum())
    put_oi = float(open_interest[put_mask].sum())

    put_call_ratio = (put_volume / call_volume) if call_volume > 0 else None
    return OptionActivity(
        call_volume=call_volume,
        put_volume=put_volume,
        call_open_interest=call_oi,
        put_open_interest=put_oi,
        put_call_ratio=put_call_ratio,
    )


def top_open_interest(
    chain: pd.DataFrame,
    option_type: str,
    top_n: int = 10,
) -> List[OpenInterestEntry]:
    if chain is None or chain.empty:
        return []

    types = chain[FK.TYPE].astype(str).str.lower()
    mask = types == option_type.lower()
    if not bool(mask.any()):
        return []

    strikes = pd.to_numeric(chain.loc[mask, FK.STRIKE], errors="coerce")
    open_interest = pd.to_numeric(chain.loc[mask, FK.OPEN_INTEREST], errors="coerce").fillna(0.0)

    grouped = (
        pd.DataFrame({FK.STRIKE: strikes, FK.OPEN_INTEREST: open_interest})
        .dropna(subset=[FK.STRIKE])
        .groupby(FK.STRIKE, dropna=False)[FK.OPEN_INTEREST]
        .sum()
        .sort_values(ascending=False)
    )

    top = grouped.head(top_n)
    return [OpenInterestEntry(float(strike), float(oi)) for strike, oi in top.items()]


if __name__ == "__main__":
    from pathlib import Path
    from src.app.data.finviz.get_option_chain import get_option_chain

    ticker = "U"
    file_path = Path(f"/tmp/{ticker}_chain.csv")
    chain = pd.read_csv(file_path) if file_path.exists() else get_option_chain(ticker, file_path=file_path)
    print(calculate_call_put_activity(chain))

    print("Call:", *top_open_interest(chain, 'call'), sep="\n")
    print("Put:", *top_open_interest(chain, 'put'), sep="\n")
