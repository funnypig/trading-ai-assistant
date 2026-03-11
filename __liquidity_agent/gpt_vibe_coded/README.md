# Liquidity Dashboard (Repo & USD Liquidity)

This creates a small **liquidity dashboard** tracking:
- **Reserves** (WRESBAL)
- **Treasury General Account** (WTREGEN)
- **Overnight Reverse Repo** (RRPONTSYD)
- **Fed balance sheet** (WALCL)
- **SOFR**
- **USD Broad Dollar Index** (DTWEXBGS)

and computes two quick signals:
- **Liquidity Index ≈ Reserves – (RRP + TGA)**
- **Repo Stress** = SOFR z‑score (or SOFR – policy upper bound, if you pass `--policy-upper`)

> ⚠️ Data are fetched from **FRED**. You need a **FRED API key**.

---

## Quick start

```bash
# 1) Create venv (optional)
python -m venv .venv && source .venv/bin/activate

# 2) Install deps
python -m pip install pandas numpy matplotlib python-dotenv requests

# 3) Set API key
cp .env.example .env
# Edit .env, set FRED_API_KEY=...

# 4) Run
python liquidity_dashboard.py --years 5 --policy-upper 5.50
```

Outputs are saved to `./output/`:
- `liquidity_dashboard.csv` (all series)
- `liquidity_dashboard_signals.csv` (compact)
- `*.png` charts

---

## Notes & Tuning

- Series used (FRED IDs):
  - `WRESBAL` — Reserve Balances with Federal Reserve Banks
  - `WTREGEN` — Treasury General Account balance
  - `RRPONTSYD` — Overnight Reverse Repo award amount
  - `WALCL` — Fed total assets
  - `SOFR` — Secured Overnight Financing Rate
  - `DTWEXBGS` — Broad trade‑weighted USD index

- If any ID changes or your access differs, update the `FRED_SERIES` map in the script.
- The **traffic‑light heuristics** are intentionally simple—tune them to your risk preferences.
- To integrate **MOVE** or market depth, plug those series into the code and compute a z‑score similar to `compute_move_proxy`.
- For **production**, consider:
  - Pinning versions
  - Scheduling (cron / GitHub Actions)
  - Persisting to a database and serving via a small FastAPI + chart front‑end
  - Adding alerting (email/Telegram) when thresholds cross

---

## Troubleshooting

- `ERROR: FRED_API_KEY not set.` → copy `.env.example` to `.env`, paste your key.
- HTTP 4xx → verify series IDs and your key.
- Empty series → try increasing `--years` or check if the series has weekly frequency; the code forward‑fills to daily.
- Charts look odd → ensure your timezone/locale isn't confusing matplotlib; data are in **USD** levels where applicable.

---

## License
MIT (as‑is, no warranties).

