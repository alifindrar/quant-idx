import yfinance as yf
import json
from datetime import datetime
import pandas as pd
import numpy as np

TICKER = "AAPL"

print(f"--- BLOCK A ---")
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
hist_1y_index_str = hist_1y.index.strftime("%Y-%m-%d")

hist_2y_weekly = tk.history(period="2y", interval="1wk", auto_adjust=True)
hist_2y_weekly.index = hist_2y_weekly.index.strftime("%Y-%m-%d")

output_a = {
    "price_data":       price_data,
    "bar_count_daily":  len(hist_1y),
}
print(json.dumps(output_a, default=str, indent=2))

print(f"--- BLOCK B ---")
try:
    income_annual  = tk.income_stmt
    income_qtrly   = tk.quarterly_income_stmt
    balance_annual = tk.balance_sheet
    cashflow       = tk.cashflow
    earnings_hist  = tk.earnings_history
except Exception:
    income_annual = income_qtrly = balance_annual = cashflow = earnings_hist = None

rev_growth_yoy = None
if income_annual is not None and "Total Revenue" in income_annual.index:
    rev = income_annual.loc["Total Revenue"].dropna()
    if len(rev) >= 2:
        rev_growth_yoy = round((rev.iloc[0] - rev.iloc[1]) / abs(rev.iloc[1]) * 100, 2)

eps_surprises = []
if earnings_hist is not None and not earnings_hist.empty:
    for _, row in earnings_hist.tail(4).iterrows():
        eps_surprises.append({
            "period":        str(row.get("period", "")),
            "actual":        row.get("epsActual"),
            "estimate":      row.get("epsEstimate"),
            "surprise_pct":  row.get("surprisePercent"),
        })

fcf = None
if cashflow is not None and "Free Cash Flow" in cashflow.index:
    fcf_series = cashflow.loc["Free Cash Flow"].dropna()
    if len(fcf_series) > 0:
        fcf = float(fcf_series.iloc[0])

fundamental_data = {
    "trailing_pe":           info.get("trailingPE"),
    "forward_pe":            info.get("forwardPE"),
    "price_to_sales":        info.get("priceToSalesTrailing12Months"),
    "price_to_book":         info.get("priceToBook"),
    "ev_to_ebitda":          info.get("enterpriseToEbitda"),
    "ev_to_revenue":         info.get("enterpriseToRevenue"),
    "peg_ratio":             info.get("pegRatio"),
    "revenue_ttm":           info.get("totalRevenue"),
    "revenue_growth_yoy":    rev_growth_yoy,
    "revenue_growth_qoq":    info.get("revenueGrowth"),
    "earnings_growth_yoy":   info.get("earningsGrowth"),
    "eps_ttm":               info.get("trailingEps"),
    "eps_forward":           info.get("forwardEps"),
    "eps_surprises_last_4q": eps_surprises,
    "gross_margin":          info.get("grossMargins"),
    "operating_margin":      info.get("operatingMargins"),
    "net_margin":            info.get("profitMargins"),
    "total_debt":            info.get("totalDebt"),
    "total_cash":            info.get("totalCash"),
    "debt_to_equity":        info.get("debtToEquity"),
    "current_ratio":         info.get("currentRatio"),
    "quick_ratio":           info.get("quickRatio"),
    "return_on_equity":      info.get("returnOnEquity"),
    "return_on_assets":      info.get("returnOnAssets"),
    "free_cash_flow":        fcf,
    "dividend_yield":        info.get("dividendYield"),
    "payout_ratio":          info.get("payoutRatio"),
}
print(json.dumps(fundamental_data, default=str, indent=2))

print(f"--- BLOCK C ---")
try:
    rec_summary = tk.recommendations_summary
    rec_dict = rec_summary.head(1).to_dict("records")[0] if (
        rec_summary is not None and not rec_summary.empty
    ) else {}
except Exception:
    rec_dict = {}

try:
    calendar = tk.calendar
    earnings_dates = calendar.get("Earnings Date", [None]) if calendar else [None]
    next_earnings = str(earnings_dates[0]) if earnings_dates else None
    eps_est = calendar.get("EPS Estimate") if calendar else None
except Exception:
    next_earnings = None
    eps_est = None

current_price = info.get("currentPrice") or info.get("regularMarketPrice")
mean_pt = info.get("targetMeanPrice")

analyst_data = {
    "analyst_count":          info.get("numberOfAnalystOpinions"),
    "recommendation_key":     info.get("recommendationKey"),
    "recommendation_mean":    info.get("recommendationMean"),
    "mean_price_target":      mean_pt,
    "high_price_target":      info.get("targetHighPrice"),
    "low_price_target":       info.get("targetLowPrice"),
    "median_price_target":    info.get("targetMedianPrice"),
    "current_price":          current_price,
    "upside_to_mean_pct":     round((mean_pt - current_price) / current_price * 100, 2)
                              if mean_pt and current_price else None,
    "strong_buy_count":       rec_dict.get("strongBuy"),
    "buy_count":              rec_dict.get("buy"),
    "hold_count":             rec_dict.get("hold"),
    "sell_count":             rec_dict.get("sell"),
    "strong_sell_count":      rec_dict.get("strongSell"),
    "next_earnings_date":     next_earnings,
    "eps_estimate_current_q": eps_est,
}
print(json.dumps(analyst_data, default=str, indent=2))

print(f"--- BLOCK D ---")
try:
    raw_news = tk.news or []
except Exception:
    raw_news = []
headlines = []
for item in raw_news[:10]:
    pub_ts = item.get("providerPublishTime")
    pub_date = datetime.utcfromtimestamp(pub_ts).isoformat() + "Z" if pub_ts else None
    headlines.append({
        "title":            item.get("title"),
        "publisher":        item.get("publisher"),
        "date":             pub_date,
    })
print(json.dumps({"headline_count": len(headlines), "headlines": headlines}, default=str, indent=2))

print(f"--- BLOCK E ---")
df = hist_1y[["Open","High","Low","Close","Volume"]].copy()
df.columns = [c.lower() for c in df.columns]
df = df.apply(pd.to_numeric, errors="coerce").dropna()

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

df["bb_mid"]   = df["sma20"]
df["bb_upper"] = df["sma20"] + 2 * close.rolling(20).std()
df["bb_lower"] = df["sma20"] - 2 * close.rolling(20).std()
df["bb_width"] = (df["bb_upper"] - df["bb_lower"]) / df["bb_mid"]
df["bb_pct"]   = (close - df["bb_lower"]) / (df["bb_upper"] - df["bb_lower"])

tr = pd.concat([
    high - low,
    (high - close.shift()).abs(),
    (low  - close.shift()).abs()
], axis=1).max(axis=1)
df["atr14"]   = tr.ewm(com=13, adjust=False).mean()
df["atr_pct"] = df["atr14"] / close * 100

df["obv"] = (np.sign(close.diff()) * vol).fillna(0).cumsum()

df["vol_sma30"] = vol.rolling(30).mean()
df["vol_ratio"] = vol / df["vol_sma30"]

df["above_200"] = (df["sma50"] > df["sma200"]).astype(int)
cross = df["above_200"].diff().replace(0, np.nan).dropna()
last_cross_event = None
if not cross.empty:
    last_cross_event = {
        "type":     "GOLDEN_CROSS" if cross.iloc[-1] == 1 else "DEATH_CROSS",
        "date":     str(cross.index[-1].date()),
        "bars_ago": len(df) - df.index.get_loc(cross.index[-1]) - 1,
    }

latest = df.iloc[-1]
prev   = df.iloc[-2] if len(df) >= 2 else df.iloc[-1]

def safe_float(v, decimals=4):
    try: return round(float(v), decimals) if not (v != v) else None
    except: return None

result = {
    "latest_date":       str(df.index[-1].date()),
    "current_price":     safe_float(latest["close"]),
    "sma20":             safe_float(latest["sma20"]),
    "sma50":             safe_float(latest["sma50"]),
    "sma200":            safe_float(latest["sma200"]),
    "ema12":             safe_float(latest["ema12"]),
    "ema26":             safe_float(latest["ema26"]),
    "macd":              safe_float(latest["macd"]),
    "macd_signal":       safe_float(latest["macd_signal"]),
    "macd_hist":         safe_float(latest["macd_hist"]),
    "macd_hist_prev":    safe_float(prev["macd_hist"]),
    "rsi14":             safe_float(latest["rsi14"], 2),
    "bb_upper":          safe_float(latest["bb_upper"]),
    "bb_mid":            safe_float(latest["bb_mid"]),
    "bb_lower":          safe_float(latest["bb_lower"]),
    "bb_width":          safe_float(latest["bb_width"]),
    "bb_pct":            safe_float(latest["bb_pct"]),
    "atr14":             safe_float(latest["atr14"]),
    "atr_pct":           safe_float(latest["atr_pct"]),
    "obv_trend":         "UP" if float(latest["obv"]) > float(df["obv"].iloc[-10]) else "DOWN",
    "volume_today":      int(latest["volume"]),
    "volume_sma30":      safe_float(latest["vol_sma30"], 0),
    "volume_ratio":      safe_float(latest["vol_ratio"], 2),
    "last_cross":        last_cross_event,
    "support_20d":       safe_float(low.rolling(20).min().iloc[-1]),
    "support_50d":       safe_float(low.rolling(50).min().iloc[-1]),
    "resistance_20d":    safe_float(high.rolling(20).max().iloc[-1]),
    "resistance_50d":    safe_float(high.rolling(50).max().iloc[-1]),
    "pct_from_52w_high": safe_float((float(latest["close"]) - float(high.max())) / float(high.max()) * 100, 2),
    "pct_from_52w_low":  safe_float((float(latest["close"]) - float(low.min()))  / float(low.min())  * 100, 2),
}

print(json.dumps(result, indent=2))
