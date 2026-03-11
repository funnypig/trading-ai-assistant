import pandas as pd
import numpy as np
from src.app.tools.options.common import FinvizOptionChainKeys as FK, OptionLiquidityScore, OptionLiquidityResult


def is_option_chain_liquid(chain: pd.DataFrame) -> OptionLiquidityResult:
    delta_from, delta_to = 0.2, 0.8
    cf = chain[
        (chain[FK.DELTA].abs() >= delta_from) &
        (chain[FK.DELTA].abs() <= delta_to)
    ].copy()
    
    cf.loc[:, [FK.BID, FK.ASK]] = cf[[FK.BID, FK.ASK]].fillna(0)
    cf["mid"] = cf[FK.ASK] * 0.5 + cf[FK.BID] * 0.5
    cf["spread"] = (cf[FK.ASK] - cf[FK.BID]).abs()
    cf["spread_percent"] = cf["spread"] / cf["mid"]
    cf["exec_size"] = cf[[FK.BID, FK.ASK]].min(axis=1)

    # Calc rule-based spread score
    # good at 0.30 and tighter, bad at 1.50 and wider
    tight_spread, wide_spread = 0.6, 2.0
    cf["spread_score"] = np.clip(1 - (cf["spread_percent"] - tight_spread) / (wide_spread - tight_spread), 0, 1)

    # Calc OI score 
    min_oi_size, ok_oi_size = 20, 500
    cf["oi_score"] = (np.log(cf[FK.OPEN_INTEREST]) - np.log(min_oi_size)) / (np.log(ok_oi_size) - np.log(min_oi_size))
    cf.loc[cf[FK.OPEN_INTEREST] <= min_oi_size, "oi_score"] = 0.
    cf.loc[cf[FK.OPEN_INTEREST] >= ok_oi_size, "oi_score"] = 1.

    # Calc Vol score 
    min_vol_size, ok_vol_size = 10, 100
    cf["vol_score"] = (np.log(cf[FK.VOLUME]) - np.log(min_vol_size)) / (np.log(ok_vol_size) - np.log(min_vol_size))
    cf.loc[cf[FK.OPEN_INTEREST] <= min_vol_size, "vol_score"] = 0.
    cf.loc[cf[FK.OPEN_INTEREST] >= ok_vol_size, "vol_score"] = 1.

    # Overall
    is_liquid_threshold = 0.60
    cf["liquidity_score"] = 0.66 * cf["spread_score"] + 0.17 * cf["oi_score"] + 0.17 * cf["vol_score"]
    
    call = cf[cf[FK.TYPE] == "call"]
    call_overall = call["liquidity_score"].median()

    put = cf[cf[FK.TYPE] == "put"]
    put_overall = put["liquidity_score"].median()

    result = OptionLiquidityResult(
        put_score=OptionLiquidityScore(
            spread_score=float(round(put["spread_score"].median(), 3)),
            volume_score=float(round(put["vol_score"].median(), 3)),
            oi_score=float(round(put["oi_score"].median(), 3)),
            total_score=float(round(put_overall, 3)),
            is_option_liquid=bool(put_overall > is_liquid_threshold),
        ),
        call_score=OptionLiquidityScore(
            spread_score=float(round(call["spread_score"].median(), 3)),
            volume_score=float(round(call["vol_score"].median(), 3)),
            oi_score=float(round(call["oi_score"].median(), 3)),
            total_score=float(round(call_overall, 3)),
            is_option_liquid=bool(call_overall > is_liquid_threshold),
        )
    )

    return result


if __name__ == "__main__":
    from src.app.data.finviz.get_option_chain import get_option_chain
    from pathlib import Path

    """
    MSFT - all liquid
    CCCX - Call liquid, Put not liquid
    QNCX - shit options
    """
    ticker = 'QNCX'
    file_path = Path(f'/tmp/{ticker}_chain.csv')
    
    if file_path.exists():
        chain = pd.read_csv(file_path)
    else:
        chain = get_option_chain(ticker, expiration='2026-02-20', file_path=file_path)
    
    result = is_option_chain_liquid(chain)

    print(result)
