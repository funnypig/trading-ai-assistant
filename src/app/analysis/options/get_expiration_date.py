import pandas as pd
import pandas_market_calendars as mcal

from typing import List, Tuple


def _get_trading_days(years: float) -> pd.DatetimeIndex:
    start_date = pd.Timestamp.today().normalize()
    nyse = mcal.get_calendar("NYSE")
    schedule = nyse.schedule(
        start_date=start_date,
        end_date=start_date + pd.Timedelta(days=int(366 * years)),
    )
    return schedule.index


def _get_expiration_days(trading_days: pd.DatetimeIndex) -> List[pd.Timestamp]:
    return [day for day in trading_days if day.weekday() == 4]


def get_n_nearest_expirations(n: int = 1, years: float = 1) -> List[str]:
    """Return the next n expiration dates (as ISO strings) within the next years."""
    trading_days = _get_trading_days(years)
    expirations = [day.isoformat().split("T")[0] for day in _get_expiration_days(trading_days)]

    return expirations[:n]


def get_nearest_expiration() -> str:
    """Return the nearest expiration date as an ISO string."""
    return get_n_nearest_expirations(n=1, years=2/12)[0]


def get_expiration_for_dte(target_dte: int, years: float = 1.0) -> str:
    """Return the nearest listed expiration date for the requested DTE (trading days)."""
    if target_dte < 0:
        raise ValueError("target_dte must be non-negative")

    start_date = pd.Timestamp.today().normalize()
    trading_days = _get_trading_days(years)
    expirations = _get_expiration_days(trading_days)
    if not expirations:
        raise ValueError("No expirations found in the requested window.")

    def _dte(expiration: pd.Timestamp) -> int:
        return int(trading_days[(trading_days > start_date) & (trading_days <= expiration)].size)

    candidates: List[Tuple[int, int, int, pd.Timestamp]] = []
    for expiration in expirations:
        dte = _dte(expiration)
        diff = abs(dte - target_dte)
        penalty = 0 if dte >= target_dte else 1
        candidates.append((diff, penalty, dte, expiration))

    _, _, _, best_expiration = sorted(candidates, key=lambda item: (item[0], item[1], item[2]))[0]
    return best_expiration.date().isoformat()


def get_dte_for_expiration(expiration: str, years: float = 1.0) -> int:
    """Return trading-day DTE for an expiration ISO date string."""
    start_date = pd.Timestamp.today().normalize()
    expiration_ts = pd.Timestamp(expiration).normalize()
    if expiration_ts <= start_date:
        return 0

    trading_days = _get_trading_days(years)
    return int(trading_days[(trading_days > start_date) & (trading_days <= expiration_ts)].size)
