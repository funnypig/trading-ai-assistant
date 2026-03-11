from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd

from src.app.tools.options.common import FinvizOptionChainKeys as FK


def calculate_implied_volatility(
    chain: pd.DataFrame,
    weight_col: str = FK.OPEN_INTEREST,
) -> Optional[float]:
    if chain is None or chain.empty:
        return None

    chain = chain[
        (chain[FK.DELTA] < 0.7) &
        (chain[FK.DELTA] > 0.3)
    ]
    iv = pd.to_numeric(chain[FK.IV], errors="coerce")
    weights = pd.to_numeric(chain[weight_col], errors="coerce").fillna(0.0)

    mask = iv.notna() & weights.notna() & (weights > 0)
    if not bool(mask.any()):
        return None

    return float(np.average(iv[mask], weights=weights[mask]))


if __name__ == "__main__":
    from pathlib import Path
    from src.app.data.finviz.get_option_chain import get_option_chain
    ticker = 'U'
    file_path = Path(f'/tmp/{ticker}_chain.csv')
    chain = pd.read_csv(file_path) if file_path.exists() else get_option_chain(ticker,  file_path=file_path)
    print(calculate_implied_volatility(chain))
