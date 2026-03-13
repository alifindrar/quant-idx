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

TICKER = "JSMR.JK"

print("=" * 60)
print(f"JSMR.JK DATA FETCH — {datetime.utcnow().isoformat()}Z")
print("=" * 60)

# ─────────────────────────────────────────────
# BLOCK A — Price & Market Data
# ─────────────────────────────────────────────
print("\n### BLOCK A: Price & Market Data ###")
try:
    tk = yf.Ticker(TICKER)
    info = tk.info

    price_data = {
        "ticker":             TICKER,
        "fetch_timestamp":    datetime.utcnow().isoformat() + "Z",
        "current_price":      info.get("currentPrice") or info.get("regularMarketPrice"),
        "open":               info.get("open") or info.get("regularMarketOpen"),
        "day_high":           info.get("dayHigh") or info.get("regularMarketDayHigh"),
        "day_low":            info.get("dayLow") or info.get("regularMarketDayLow"),
        "prev_close":         info.get("previousClose") or info.get("regularMarketPreviousClose"),
        "volume":             info.get("volume") or info.get("regularMarketVolume"),
        "avg_volume_10d":     info.get("averageVolume10days"),
        "avg_volume_3m":      info.get("averageVolume"),
        "market_cap":         info.get("marketCap"),
        "52w_high":           info.get("fiftyTwoWeekHigh"),
        "52w_low":            info.get("fiftyTwoWeekLow"),
        "beta_5y":            info.get("beta"),
        "shares_outstanding": info.get("sharesOutstanding"),
        "float_shares":       info.get("floatShares"),
        "short_pct_float":    info.get("shortPercentOfFloat"),
        "company_name":       info.get("longName") or info.get("shortName"),
        "sector":             info.get("sector"),
        "industry":           info.get("industry"),
        "exchange":           info.get("exchange"),
    }

    hist_1y = tk.history(period="1y", interval="1d", auto_adjust=True)
    hist_1y.index = hist_1y.index.strftime("%Y-%m-%d")

    block_a = {
        "price_data":       price_data,
        "daily_bars_1y":    {k: v for k, v in list(hist_1y[["Open","High","Low","Close","Volume"]].to_dict("index").items())[-10:]},
        "bar_count_daily":  len(hist_1y),
    }

    if price_data["current_price"] is None and len(hist_1y) >= 10:
        last_close = hist_1y[["Close"]].iloc[-1]["Close"]
        price_data["current_price"] = float(last_close)
        price_data["current_price_flag"] = "⚠️ ESTIMATED from last bar close"

    print(json.dumps(block_a, default=str, indent=2))
    block_a_ok = True

except Exception as e:
    print(f"FAILED BLOCK A: {e}")
    block_a_ok = False
    block_a = {}

# ─────────────────────────────────────────────
# BLOCK B — Fundamental Data
# ─────────────────────────────────────────────
print("\n### BLOCK B: Fundamental Data ###")
try:
    tk2 = yf.Ticker(TICKER)
    info2 = tk2.info

    try:
        income_annual  = tk2.income_stmt
        cashflow       = tk2.cashflow
    except Exception:
        income_annual = cashflow = None

    rev_growth_yoy = None
    if income_annual is not None and "Total Revenue" in income_annual.index:
        rev = income_annual.loc["Total Revenue"].dropna()
        if len(rev) >= 2:
            rev_growth_yoy = round((rev.iloc[0] - rev.iloc[1]) / abs(rev.iloc[1]) * 100, 2)

    fcf = None
    if cashflow is not None and "Free Cash Flow" in cashflow.index:
        fcf_series = cashflow.loc["Free Cash Flow"].dropna()
        if len(fcf_series) > 0:
            fcf = float(fcf_series.iloc[0])

    fundamental_data = {
        "trailing_pe":           info2.get("trailingPE"),
        "forward_pe":            info2.get("forwardPE"),
        "price_to_book":         info2.get("priceToBook"),
        "ev_to_ebitda":          info2.get("enterpriseToEbitda"),
        "revenue_growth_yoy":    rev_growth_yoy,
        "revenue_growth_qoq":    info2.get("revenueGrowth"),
        "earnings_growth_yoy":   info2.get("earningsGrowth"),
        "gross_margin":          info2.get("grossMargins"),
        "operating_margin":      info2.get("operatingMargins"),
        "net_margin":            info2.get("profitMargins"),
        "total_debt":            info2.get("totalDebt"),
        "total_cash":            info2.get("totalCash"),
        "debt_to_equity":        info2.get("debtToEquity"),
        "return_on_equity":      info2.get("returnOnEquity"),
        "free_cash_flow":        fcf,
        "dividend_yield":        info2.get("dividendYield"),
        "payout_ratio":          info2.get("payoutRatio"),
    }

    print(json.dumps(fundamental_data, default=str, indent=2))

except Exception as e:
    print(f"FAILED BLOCK B: {e}")
    fundamental_data = {}

# ─────────────────────────────────────────────
# BLOCK C — Analyst Data
# ─────────────────────────────────────────────
print("\n### BLOCK C: Analyst Data ###")
try:
    tk3 = yf.Ticker(TICKER)
    info3 = tk3.info

    try:
        rec_summary = tk3.recommendations_summary
        rec_dict = rec_summary.head(1).to_dict("records")[0] if (
            rec_summary is not None and not rec_summary.empty
        ) else {}
    except Exception:
        rec_dict = {}

    current_price = info3.get("currentPrice") or info3.get("regularMarketPrice")
    mean_pt = info3.get("targetMeanPrice")

    analyst_data = {
        "analyst_count":          info3.get("numberOfAnalystOpinions"),
        "recommendation_mean":    info3.get("recommendationMean"),
        "mean_price_target":      mean_pt,
        "current_price":          current_price,
        "upside_to_mean_pct":     round((mean_pt - current_price) / current_price * 100, 2)
                                  if mean_pt and current_price else None,
        "strong_buy_count":       rec_dict.get("strongBuy"),
        "buy_count":              rec_dict.get("buy"),
        "hold_count":             rec_dict.get("hold"),
        "sell_count":             rec_dict.get("sell"),
        "strong_sell_count":      rec_dict.get("strongSell"),
    }

    print(json.dumps(analyst_data, default=str, indent=2))

except Exception as e:
    print(f"FAILED BLOCK C: {e}")
    analyst_data = {}

# ─────────────────────────────────────────────
# BLOCK E — Technical Indicators
# ─────────────────────────────────────────────
print("\n### BLOCK E: Technical Indicators ###")
try:
    if not block_a_ok or price_data["current_price"] is None:
        print("FAILED BLOCK E SKIPPED: Block A data unavailable.")
    else:
        tk5 = yf.Ticker(TICKER)
        hist_1y_full = tk5.history(period="1y", interval="1d", auto_adjust=True)
        if len(hist_1y_full) > 0:
            df = hist_1y_full
            df.columns = [c.lower() for c in df.columns]
            df = df[["open","high","low","close","volume"]].apply(pd.to_numeric, errors="coerce").dropna()
            
            close = df["close"]
            high  = df["high"]
            low   = df["low"]
            vol   = df["volume"]
            
            df["sma20"]  = close.rolling(20).mean()
            df["sma50"]  = close.rolling(50).mean()
            df["sma200"] = close.rolling(200).mean()
            df["ema12"]  = close.ewm(span=12, adjust=False).mean()
            df["ema26"]  = close.ewm(span=26, adjust=False).mean()
            
            df["macd"]        = df["ema12"] - df["ema26"]
            df["macd_signal"] = df["macd"].ewm(span=9, adjust=False).mean()
            df["macd_hist"]   = df["macd"] - df["macd_signal"]
            
            delta    = close.diff()
            gain     = delta.clip(lower=0)
            loss     = -delta.clip(upper=0)
            avg_gain = gain.ewm(com=13, adjust=False).mean()
            avg_loss = loss.ewm(com=13, adjust=False).mean()
            rs       = avg_gain / avg_loss.replace(0, np.nan)
            df["rsi14"] = 100 - (100 / (1 + rs))
            
            df["vol_sma30"] = vol.rolling(30).mean()
            df["vol_ratio"] = vol / df["vol_sma30"]
            
            latest = df.iloc[-1]
            prev   = df.iloc[-2] if len(df) >= 2 else df.iloc[-1]
            
            def safe_float(v, decimals=4):
                try: return round(float(v), decimals) if not (v != v) else None
                except: return None
            
            tech_result = {
                "latest_date":       str(df.index[-1].date()),
                "current_price":     safe_float(latest["close"]),
                "sma20":             safe_float(latest["sma20"]),
                "sma50":             safe_float(latest["sma50"]),
                "sma200":            safe_float(latest["sma200"]),
                "macd":              safe_float(latest["macd"]),
                "macd_signal":       safe_float(latest["macd_signal"]),
                "macd_hist":         safe_float(latest["macd_hist"]),
                "macd_hist_prev":    safe_float(prev["macd_hist"]),
                "rsi14":             safe_float(latest["rsi14"], 2),
                "volume_today":      int(latest["volume"]),
                "volume_sma30":      safe_float(latest["vol_sma30"], 0),
                "volume_ratio":      safe_float(latest["vol_ratio"], 2),
                "pct_from_52w_high": safe_float((float(latest["close"]) - float(high.max())) / float(high.max()) * 100, 2),
                "pct_from_52w_low":  safe_float((float(latest["close"]) - float(low.min()))  / float(low.min())  * 100, 2),
            }
            
            print(json.dumps(tech_result, indent=2))
        else:
            print("No daily bars returned.")

except Exception as e:
    print(f"FAILED BLOCK E: {e}")
    import traceback; traceback.print_exc()

print("\n" + "=" * 60)
print("FETCH COMPLETE")
print("=" * 60)
