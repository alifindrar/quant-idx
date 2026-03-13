import subprocess, sys

def ensure(pkg):
    try:
        __import__(pkg)
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg,
                               "--quiet", "--break-system-packages"])

ensure("yfinance")
ensure("pandas")
ensure("numpy")

import yfinance as yf
import json
import numpy as np
import pandas as pd
from datetime import datetime

TICKERS = ["TAPG.JK", "FAPA.JK", "AALI.JK", "DSNG.JK", "SGRO.JK", 
           "SSMS.JK", "SIMP.JK", "LSIP.JK", "PALM.JK", "TBLA.JK", "BWPT.JK"]

results = []

for ticker in TICKERS:
    try:
        tk = yf.Ticker(ticker)
        info = tk.info
        
        hist = tk.history(period="1y", interval="1d", auto_adjust=True)
        if len(hist) > 0:
            hist.columns = [c.lower() for c in hist.columns]
            close = hist["close"]
            sma50 = close.rolling(50).mean()
            sma200 = close.rolling(200).mean()
            
            delta = close.diff()
            gain = delta.clip(lower=0)
            loss = -delta.clip(upper=0)
            avg_gain = gain.ewm(com=13, adjust=False).mean()
            avg_loss = loss.ewm(com=13, adjust=False).mean()
            rs = avg_gain / avg_loss.replace(0, np.nan)
            rsi = 100 - (100 / (1 + rs))
            
            latest_price = float(close.iloc[-1])
            sma50_val = float(sma50.iloc[-1]) if not np.isnan(sma50.iloc[-1]) else None
            sma200_val = float(sma200.iloc[-1]) if not np.isnan(sma200.iloc[-1]) else None
            rsi_val = float(rsi.iloc[-1]) if not np.isnan(rsi.iloc[-1]) else None
            
            pct_sma50 = ((latest_price - sma50_val) / sma50_val * 100) if sma50_val else None
            pct_sma200 = ((latest_price - sma200_val) / sma200_val * 100) if sma200_val else None
        else:
            latest_price = sma50_val = sma200_val = rsi_val = pct_sma50 = pct_sma200 = None

        res = {
            "Ticker": ticker,
            "Price": latest_price,
            "PE": info.get("trailingPE"),
            "PB": info.get("priceToBook"),
            "ROE": info.get("returnOnEquity"),
            "DivYield": info.get("dividendYield"),
            "OpMargin": info.get("operatingMargins"),
            "DebtEq": info.get("debtToEquity"),
            "SMA50_Pct": pct_sma50,
            "SMA200_Pct": pct_sma200,
            "RSI": rsi_val
        }
        results.append(res)
        print(f"SUCCESS {ticker} fetched.")
    except Exception as e:
        print(f"FAILED {ticker}: {e}")

print("\n--- BATCH RESULTS ---")
print(json.dumps(results, indent=2))
