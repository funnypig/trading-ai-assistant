#!/usr/bin/env python3
"""
Liquidity Dashboard: Repo & USD Liquidity Monitors
--------------------------------------------------
Tracks key liquidity metrics and computes synthetic signals.

Data sources:
- FRED API (requires FRED API key in .env): https://fred.stlouisfed.org/docs/api/fred/
  * Reserve balances with Fed (WRESBAL)
  * Fed balance sheet total assets (WALCL)
  * Treasury General Account (WTREGEN)
  * Overnight Reverse Repo (RRPONTSYD)
  * SOFR (SOFR)
  * Broad USD Dollar Index (DTWEXBGS)

Outputs:
- ./output/liquidity_dashboard.csv (joined time series)
- ./output/liquidity_dashboard_signals.csv (key calculated signals)
- ./output/*.png charts

Usage:
  1) cp .env.example .env  # put your FRED API key
  2) pip install -r requirements.txt (see inline "REQUIREMENTS" block)
  3) python liquidity_dashboard.py --years 5

Author: ChatGPT
"""
import os
import argparse
import datetime as dt
from dataclasses import dataclass
from typing import Dict, List

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import requests

# -----------------------
# REQUIREMENTS (pip):
#   python -m pip install pandas numpy matplotlib python-dotenv requests
# -----------------------

from dotenv import load_dotenv

FRED_API_BASE = "https://api.stlouisfed.org/fred/series/observations"

# Default series map (FRED)
FRED_SERIES = {
    # System "plumbing"
    "WRESBAL": "Reserve Balances with Federal Reserve Banks (level, $)",
    "WTREGEN": "U.S. Treasury General Account (TGA) Balance (level, $)",
    "RRPONTSYD": "Overnight Reverse Repo Operations: Award Amount (level, $)",
    "WALCL": "Federal Reserve Total Assets (level, $)",
    "SOFR": "Secured Overnight Financing Rate (%)",
    "DTWEXBGS": "Broad Trade-Weighted U.S. Dollar Index (index)",
}

@dataclass
class SeriesConfig:
    id: str
    title: str

def fred_fetch(series_id: str, start_date: str, api_key: str) -> pd.Series:
    """Fetch a FRED series as a daily pandas Series indexed by date."""
    params = {
        "series_id": series_id,
        "api_key": api_key,
        "file_type": "json",
        "observation_start": start_date,
    }
    r = requests.get(FRED_API_BASE, params=params, timeout=30)
    r.raise_for_status()
    js = r.json()
    if "observations" not in js:
        raise RuntimeError(f"Unexpected FRED response for {series_id}: {js}")
    obs = js["observations"]
    if not obs:
        return pd.Series(dtype="float64")
    # Build series
    dates = [o["date"] for o in obs]
    # Some series contain "." for missing values—coerce to NaN
    vals = [np.nan if o["value"] in (".", None, "") else float(o["value"]) for o in obs]
    s = pd.Series(vals, index=pd.to_datetime(dates), name=series_id).sort_index()
    return s

def compute_liquidity_index(reserves: pd.Series, rrp: pd.Series, tga: pd.Series) -> pd.Series:
    """
    Synthetic Liquidity Index ≈ Reserves – (RRP + TGA)
    Aligns to daily frequency via forward-fill.
    """
    df = pd.concat([reserves, rrp, tga], axis=1)
    df.columns = ["reserves", "rrp", "tga"]
    df = df.asfreq("D").ffill()
    liq = df["reserves"] - (df["rrp"].fillna(0.0) + df["tga"].fillna(0.0))
    liq.name = "LIQ_IDX"
    return liq

def compute_repo_stress(sofr: pd.Series, policy_upper: float = None) -> pd.Series:
    """
    Simple repo stress proxy: SOFR deviation above a policy anchor (if provided).
    If policy_upper is None, uses a rolling z-score to flag unusual spikes.
    Returns a z-scored stress measure.
    """
    s = sofr.copy().asfreq("D").ffill()
    if policy_upper is not None:
        spread = s - policy_upper
        out = (spread - spread.rolling(60, min_periods=20).mean()) / spread.rolling(60, min_periods=20).std()
        out.name = "REPO_STRESS_Z"
        return out
    z = (s - s.rolling(60, min_periods=20).mean()) / s.rolling(60, min_periods=20).std()
    z.name = "REPO_STRESS_Z"
    return z

def compute_move_proxy(treasury_vol: pd.Series) -> pd.Series:
    """
    Placeholder if you have an implied volatility series or a MOVE proxy.
    Here we simply z-score the input as a 'vol stress' proxy.
    """
    z = (treasury_vol - treasury_vol.rolling(60, min_periods=20).mean()) / treasury_vol.rolling(60, min_periods=20).std()
    z.name = "MOVE_Z_PROXY"
    return z

def make_chart(series: pd.Series, title: str, outfile: str, ylabel: str = ""):
    """Render a single-line matplotlib chart and save to disk."""
    plt.figure(figsize=(10, 5))
    series.plot()
    plt.title(title)
    plt.xlabel("Date")
    plt.ylabel(ylabel)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(outfile, dpi=150)
    plt.close()

def join_and_save(outputs: Dict[str, pd.Series], out_csv: str):
    """Join named series on date index and write to CSV."""
    df = pd.concat(outputs.values(), axis=1)
    df.columns = list(outputs.keys())
    df.to_csv(out_csv, index_label="date")
    return df

def parse_args():
    ap = argparse.ArgumentParser(description="Build Liquidity Dashboard from FRED data.")
    ap.add_argument("--years", type=int, default=5, help="How many years back to fetch")
    ap.add_argument("--policy-upper", type=float, default=None,
                    help="Optional Fed funds upper bound (e.g., 5.50). If provided, repo stress uses SOFR - upper bound.")
    return ap.parse_args()

def main():
    load_dotenv()
    api_key = os.getenv("FRED_API_KEY", "").strip()
    if not api_key:
        raise SystemExit("ERROR: FRED_API_KEY not set. Put it in .env (see .env.example).")

    args = parse_args()

    end = dt.date.today()
    start = end - dt.timedelta(days=365 * args.years)
    start_str = start.strftime("%Y-%m-%d")

    # Fetch time series
    fetched = {}
    titles = {}
    for sid, title in FRED_SERIES.items():
        print(f"Fetching {sid} ...")
        s = fred_fetch(sid, start_str, api_key)
        fetched[sid] = s
        titles[sid] = title

    # Compute key signals
    reserves = fetched.get("WRESBAL")
    rrp = fetched.get("RRPONTSYD")
    tga = fetched.get("WTREGEN")
    walcl = fetched.get("WALCL")
    sofr = fetched.get("SOFR")
    dxy = fetched.get("DTWEXBGS")

    outputs = {}

    if reserves is not None and rrp is not None and tga is not None:
        liq_idx = compute_liquidity_index(reserves, rrp, tga)
        outputs["LIQ_IDX"] = liq_idx

    if sofr is not None:
        repo_stress = compute_repo_stress(sofr, policy_upper=args.policy_upper)
        outputs["REPO_STRESS_Z"] = repo_stress

    if walcl is not None:
        outputs["WALCL"] = walcl.asfreq("D").ffill()

    if dxy is not None:
        outputs["DXY"] = dxy.asfreq("D").ffill()

    # Also include raw key series for reference
    for sid, s in fetched.items():
        outputs[sid] = s.asfreq("D").ffill()

    outdir = Path("./output")
    outdir.mkdir(exist_ok=True, parents=True)

    # Save joined CSV
    joined = join_and_save(outputs, str(outdir / "liquidity_dashboard.csv"))

    # Derive a compact signals CSV
    signals = joined[["LIQ_IDX", "REPO_STRESS_Z", "WRESBAL", "RRPONTSYD", "WTREGEN", "SOFR", "WALCL", "DTWEXBGS"]].copy()
    signals.to_csv(outdir / "liquidity_dashboard_signals.csv", index_label="date")

    # Charts
    if "LIQ_IDX" in outputs:
        make_chart(outputs["LIQ_IDX"], "Synthetic Liquidity Index ≈ Reserves – (RRP + TGA)", str(outdir / "liquidity_index.png"), ylabel="$")

    if "REPO_STRESS_Z" in outputs:
        make_chart(outputs["REPO_STRESS_Z"], "Repo Stress (SOFR z-score or vs policy upper bound)", str(outdir / "repo_stress_z.png"))

    if "WALCL" in outputs:
        make_chart(outputs["WALCL"], "Fed Total Assets (WALCL)", str(outdir / "walcl.png"), ylabel="$")

    if "WRESBAL" in outputs:
        make_chart(outputs["WRESBAL"], "Reserve Balances with Fed (WRESBAL)", str(outdir / "reserves.png"), ylabel="$")

    if "RRPONTSYD" in outputs:
        make_chart(outputs["RRPONTSYD"], "Overnight Reverse Repo Award Amount (RRPONTSYD)", str(outdir / "on_rrp.png"), ylabel="$")

    if "WTREGEN" in outputs:
        make_chart(outputs["WTREGEN"], "Treasury General Account (WTREGEN)", str(outdir / "tga.png"), ylabel="$")

    if "SOFR" in outputs:
        make_chart(outputs["SOFR"], "Secured Overnight Financing Rate (SOFR)", str(outdir / "sofr.png"), ylabel="%")

    if "DTWEXBGS" in outputs:
        make_chart(outputs["DTWEXBGS"], "Trade-Weighted USD (DTWEXBGS)", str(outdir / "dxy.png"), ylabel="index")

    # Simple traffic-light printout
    print("\n=== Liquidity Traffic-Lights (heuristics) ===")
    latest = joined.iloc[-1]
    notes: List[str] = []

    # Heuristic thresholds (tune for your use)
    liq = latest.get("LIQ_IDX", np.nan)
    rrpo = latest.get("RRPONTSYD", np.nan)
    tga_v = latest.get("WTREGEN", np.nan)
    res_v = latest.get("WRESBAL", np.nan)
    repo_z = latest.get("REPO_STRESS_Z", np.nan)

    if not np.isnan(liq):
        m = joined["LIQ_IDX"].rolling(252, min_periods=60).mean().iloc[-1]
        if liq < m * 0.9:
            notes.append("LIQ: RED (below 1y mean by >10%)")
        elif liq < m * 0.98:
            notes.append("LIQ: YELLOW (slightly below 1y mean)")
        else:
            notes.append("LIQ: GREEN (healthy vs 1y mean)")

    if not np.isnan(repo_z):
        if repo_z > 1.5:
            notes.append("REPO: RED (SOFR stress z>1.5)")
        elif repo_z > 0.5:
            notes.append("REPO: YELLOW (SOFR mildly elevated)")
        else:
            notes.append("REPO: GREEN (normal)")

    print("\n".join(notes) or "No signals computed.")

if __name__ == "__main__":
    main()
