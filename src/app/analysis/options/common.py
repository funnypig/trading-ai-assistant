from typing import List
from dataclasses import dataclass


@dataclass
class FinvizOptionChainKeys:
    CONTRACT = "Contract"
    NAME = "Name"
    LAST = "Last"
    TRADE = "Trade"
    STRIKE = "Strike"
    LAST_PRICE = "Last Close"
    BID = "Bid"
    ASK = "Ask"
    CHANGE_DOLLAR = "Change $"
    CHANGE_PERCENT = "Change %"
    VOLUME = "Volume"
    OPEN_INTEREST = "Open Int."
    TYPE = "Type"
    IV = "IV"
    DELTA = "Delta"
    GAMMA = "Gamma"
    THETA = "Theta"
    VEGA = "Vega"
    RHO = "Rho"


@dataclass
class OptionLiquidityScore:
    volume_score: float = 0
    oi_score: float = 0
    spread_score: float = 0
    total_score: float = 0
    is_option_liquid: bool = False

    def __str__(self):
        return (
            f"OptionLiquidityScore("
            f"\n\tvolume_score={self.volume_score:.2f}, "
            f"\n\toi_score={self.oi_score:.2f}, "
            f"\n\tspread_score={self.spread_score:.2f}, "
            f"\n\ttotal_score={self.total_score:.2f}, "
            f"\n\tis_option_liquid={self.is_option_liquid})"
        )


@dataclass
class OptionLiquidityResult:
    call_score: OptionLiquidityScore
    put_score: OptionLiquidityScore

    def __str__(self):
        return (
            f"OptionLiquidityResult(\n"
            f"  call_score={self.call_score},\n"
            f"  put_score={self.put_score}\n"
            f")"
        )


@dataclass
class OptionMaxPainResult:
    expiration: List[str] | str
    max_pain_value: List[float] | float
