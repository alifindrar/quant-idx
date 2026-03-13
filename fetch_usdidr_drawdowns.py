import subprocess, sys
def ensure(pkg):
    try: __import__(pkg)
    except ImportError: subprocess.check_call([sys.executable, "-m", "pip", "install", pkg, "--quiet", "--break-system-packages"])
ensure("yfinance"); ensure("pandas"); ensure("numpy")

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime

TICKER = "USDIDR=X"
CSV_PATH = "usdidr_5y.csv"

# ── STEP 1: Fetch 5-year data and save CSV ──────────────────────────────────
print(f"Fetching {TICKER} 5-year daily history...")
tk = yf.Ticker(TICKER)
hist = tk.history(period="5y", interval="1d", auto_adjust=True)
hist.index = hist.index.tz_localize(None)  # strip tz for clean CSV
hist.to_csv(CSV_PATH)
print(f"Saved {len(hist)} rows -> {CSV_PATH}\n")

# ── STEP 2: Read CSV back and compute drawdowns ─────────────────────────────
df = pd.read_csv(CSV_PATH, index_col=0, parse_dates=True)
close = df["Close"].dropna()

# For USDIDR: a HIGHER value = weaker Rupiah (more IDR per 1 USD)
# A "Rupiah drawdown" = a period where USDIDR rises (IDR depreciates) significantly
# We find peaks-to-troughs in IDR STRENGTH (i.e., troughs in USDIDR)
# then measure magnitude as (local_high - local_low) / local_low * 100

# Algorithm: rolling window to find top-N distinct depreciation episodes
# We compute the running peak, then find contiguous episodes where
# USDIDR rises from a local trough to a local peak by the most.

# Identify all local troughs and peaks with a 30-day cooldown
def find_episodes(series, cooldown=30):
    """Find (trough_date, peak_date, pct_depreciation) episodes."""
    episodes = []
    n = len(series)
    i = 0
    while i < n - cooldown:
        # Find local minimum (IDR at its strongest) as episode start
        window_end = min(i + 252, n)  # look up to 1 year ahead
        local_min_idx = series.iloc[i:window_end].idxmin()
        local_min_val = series[local_min_idx]
        j = series.index.get_loc(local_min_idx)

        # From that trough, find the subsequent peak (worst IDR)
        remaining = series.iloc[j:min(j + 252, n)]
        local_max_idx = remaining.idxmax()
        local_max_val = series[local_max_idx]

        pct_depreciation = (local_max_val - local_min_val) / local_min_val * 100

        if pct_depreciation > 2.0:  # only meaningful moves
            episodes.append({
                "trough_date": local_min_idx.strftime("%Y-%m-%d"),
                "peak_date":   local_max_idx.strftime("%Y-%m-%d"),
                "trough_usdidr": round(local_min_val, 1),
                "peak_usdidr":   round(local_max_val, 1),
                "idr_depreciation_pct": round(pct_depreciation, 2),
            })

        # Advance past the peak to find the next episode
        k = series.index.get_loc(local_max_idx)
        i = max(k + cooldown, i + cooldown)

    return episodes

episodes = find_episodes(close, cooldown=60)

# Sort by magnitude and deduplicate overlapping windows
episodes_sorted = sorted(episodes, key=lambda x: x["idr_depreciation_pct"], reverse=True)

# Keep top-3 non-overlapping (simple filter based on trough_date gap)
top3 = []
used_troughs = []
for ep in episodes_sorted:
    trough_dt = pd.Timestamp(ep["trough_date"])
    if all(abs((trough_dt - pd.Timestamp(t)).days) > 90 for t in used_troughs):
        top3.append(ep)
        used_troughs.append(trough_dt)
    if len(top3) == 3:
        break

print("=" * 65)
print("TOP 3 RUPIAH DRAWDOWN EPISODES (5-Year Window)")
print("=" * 65)
for rank, ep in enumerate(top3, 1):
    print(f"\n#{rank} -- {ep['trough_date']} to {ep['peak_date']}")
    print(f"  USDIDR: {ep['trough_usdidr']:,.0f} -> {ep['peak_usdidr']:,.0f}")
    print(f"  IDR Depreciation: {ep['idr_depreciation_pct']:.2f}%")

print(f"\nBaseline Reference:")
print(f"  5Y Start (earliest available):  {close.index[0].date()} = {close.iloc[0]:,.1f}")
print(f"  Current (latest):               {close.index[-1].date()} = {close.iloc[-1]:,.1f}")
print(f"  5Y Net IDR Change: {((close.iloc[-1] - close.iloc[0]) / close.iloc[0] * 100):+.2f}%")
