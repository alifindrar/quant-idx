import subprocess, sys
def ensure(pkg):
    try: __import__(pkg)
    except ImportError: subprocess.check_call([sys.executable, "-m", "pip", "install", pkg, "--quiet", "--break-system-packages"])
ensure("yfinance"); ensure("pandas"); ensure("numpy")

import yfinance as yf, json, pandas as pd, numpy as np
from datetime import datetime

FETCH_TIME = datetime.utcnow().isoformat() + "Z"
TICKERS = {
    "DX-Y.NYB":  "US Dollar Index (DXY)",
    "^VIX":      "CBOE Volatility Index",
    "CL=F":      "WTI Crude Oil",
    "^JKSE":     "IHSG Jakarta Composite",
    "USDIDR=X":  "USD/IDR Exchange Rate",
    "EIDO":      "MSCI Indonesia ETF",
    "ID10YT=RR": "Indonesia 10-Year Bond Yield",
}

print(f"MACRO FETCH — {FETCH_TIME}\n" + "="*60)
results = {}

for ticker, name in TICKERS.items():
    print(f"\n--- {ticker} ({name}) ---")
    try:
        tk = yf.Ticker(ticker)
        info = tk.info
        hist = tk.history(period="1y", interval="1d", auto_adjust=True)
        if hist.empty:
            print(f"  [X] Empty history"); results[ticker] = {"name": name, "status": "UNAVAILABLE"}; continue
        close = hist["Close"]
        price_raw = info.get("currentPrice") or info.get("regularMarketPrice") or info.get("regularMarketPreviousClose")
        last_close = round(float(close.iloc[-1]), 4)
        price = round(float(price_raw), 4) if price_raw else last_close
        flag = "✅ CONFIRMED" if price_raw else "⚠️ ESTIMATED"
        sma50  = round(float(close.rolling(50).mean().iloc[-1]), 4) if len(close) >= 50 else None
        sma200 = round(float(close.rolling(200).mean().iloc[-1]), 4) if len(close) >= 200 else None
        row = {
            "name": name, "ticker": ticker, "fetch_ts": FETCH_TIME,
            "latest_date": str(hist.index[-1].date()),
            "price": price, "flag": flag,
            "sma50": sma50, "sma200": sma200,
            "above_50": last_close > sma50 if sma50 else None,
            "above_200": last_close > sma200 if sma200 else None,
            "pct_52w_high": round((last_close - float(close.max())) / float(close.max()) * 100, 2),
            "pct_52w_low":  round((last_close - float(close.min())) / float(close.min()) * 100, 2),
            "bars": len(close), "status": "OK"
        }
        print(json.dumps(row, indent=2, default=str))
        results[ticker] = row
    except Exception as e:
        print(f"  [X] FAILED: {e}")
        results[ticker] = {"name": name, "ticker": ticker, "status": f"FAILED: {e}"}

print("\n" + "="*60 + "\nSUMMARY\n" + "="*60)
fmt = "{:<14} {:>12} {:>12} {:>12} {:>7} {:>7}"
print(fmt.format("Ticker","Price","SMA50","SMA200",">50MA",">200MA"))
print("-"*60)
for t,r in results.items():
    if r.get("status")=="OK":
        print(fmt.format(t, str(r["price"]), str(r["sma50"]), str(r["sma200"]),
                         "YES" if r["above_50"] else "NO", "YES" if r["above_200"] else "NO"))
    else:
        print(fmt.format(t,"UNAVAIL","N/A","N/A","-","-"))
print("\nFETCH COMPLETE")
