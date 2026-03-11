# Liquidity Monitoring & Early Repo Stress Detection

This document summarizes **what values/metrics to track** to monitor system liquidity and **how to detect repo market issues beforehand**.

---

# ✅ 1. Core Liquidity Metrics to Track

## 🏦 Bank Reserves & Fed Balance Sheet  
- **Reserves (WRESBAL)** — falling = tighter liquidity  
- **Fed Balance Sheet (WALCL)** — QT drains, QE injects  
- **Treasury General Account (TGA)** — rising TGA drains liquidity  
- **Reverse Repo (RRPONTSYD)** — high RRP = liquidity pulled out  

**Formula:** `Liquidity ≈ Reserves – (TGA + RRP)`

---

## 💸 Repo & Funding Market Rates  
- **SOFR** — spikes indicate funding stress  
- **GC Repo rate** — divergence from Fed Funds = early warning  
- **SOFR – Fed Funds spread** — widening = tightening  
- **Standing Repo Facility (SRF) usage** — rising usage = banks need cash  

---

## 📊 Treasury Market Liquidity  
- **MOVE index**  
- **Bid–ask spreads**  
- **Market depth**  
- **Dealer balance sheet capacity**

Treasuries = repo collateral → illiquidity here leads to repo stress.

---

## 🌍 Global USD Liquidity  
- **EUR/USD cross-currency basis**  
- **Fed FX swap line usage**  
- **DXY (Dollar Index)**  

Rising DXY = global USD shortage → repo tightening.

---

# ✅ 2. Early Warning Signs of Repo Issues

## ⚠️ SOFR or GC Repo Spikes  
- Rates drift up or become volatile  
- Prints above policy range  
- Preceded 2019 & 2020 repo events  

---

## ⚠️ SOFR loses anchor  
- Increased volatility  
- Persistent prints above expectations  

---

## ⚠️ Treasury Illiquidity  
- Wide bid–ask  
- Thin order books  
- High MOVE  

Repo stress usually follows.

---

## ⚠️ RRP usage ↓ AND Reserves ↓  
Total system liquidity is shrinking.

---

## ⚠️ TGA ↑ sharply  
Treasury drains cash → banks tighten → repo rates jump.

---

## ⚠️ Dealer Balance Sheet Compression  
Dealers reduce leverage → collateral stops flowing → repo tightens.

---

## ⚠️ Collateral Shortages (“Specials”)  
- Specific CUSIPs trade negative  
- Short-covering stress  
- Leading indicator of repo issues  

---

## ⚠️ Global Dollar Shortage  
- Deep negative basis swaps  
- Swap line usage spikes  
- Rapidly rising DXY  

---

# ✅ TL;DR  
If **3+** conditions below are present:

- SOFR ↑  
- GC Repo ↑  
- Treasuries illiquid  
- Reserves ↓  
- TGA ↑  
- RRP ↓  
- DXY ↑  

→ **High probability of repo stress.**

---

# ✅ Summary  
Track reserves, TGA, RRP, repo rates, Treasury liquidity, global USD conditions.  
Repo stress emerges through rate spikes, collateral scarcity, falling reserves, and rising TGA.  
Monitoring these indicators gives early warnings before systemic funding issues appear.
