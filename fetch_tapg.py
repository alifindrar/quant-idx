import subprocess, sys
def ensure(pkg):
    try: __import__(pkg)
    except ImportError: subprocess.check_call([sys.executable, "-m", "pip", "install", pkg, "--quiet", "--break-system-packages"])
ensure("yfinance"); ensure("pandas"); ensure("numpy")

import yfinance as yf, json, pandas as pd, numpy as np
from datetime import datetime

TICKER = "TAPG.JK"
FETCH_TIME = datetime.utcnow().isoformat() + "Z"
print(f"TAPG.JK DATA FETCH -- {FETCH_TIME}")
print("=" * 60)

tk = yf.Ticker(TICKER)
info = tk.info

# ── BLOCK A ─────────────────────────────────────────────────────
print("\n### BLOCK A: Price & Market Data ###")
price = info.get("currentPrice") or info.get("regularMarketPrice")
hist_1y = tk.history(period="1y", interval="1d", auto_adjust=True)
hist_2y_wk = tk.history(period="2y", interval="1wk", auto_adjust=True)
hist_1y.index = hist_1y.index.strftime("%Y-%m-%d")
hist_2y_wk.index = hist_2y_wk.index.strftime("%Y-%m-%d")
block_a = {
    "ticker": TICKER, "currency": info.get("currency","IDR"),
    "company_name": info.get("longName") or info.get("shortName"),
    "sector": info.get("sector"), "industry": info.get("industry"),
    "current_price": price,
    "open": info.get("open"), "day_high": info.get("dayHigh"), "day_low": info.get("dayLow"),
    "prev_close": info.get("previousClose"),
    "volume": info.get("volume"), "avg_volume_10d": info.get("averageVolume10days"),
    "avg_volume_3m": info.get("averageVolume"),
    "market_cap": info.get("marketCap"),
    "52w_high": info.get("fiftyTwoWeekHigh"), "52w_low": info.get("fiftyTwoWeekLow"),
    "beta_5y": info.get("beta"), "shares_outstanding": info.get("sharesOutstanding"),
    "bar_count_daily": len(hist_1y), "bar_count_weekly": len(hist_2y_wk),
    "daily_bars_1y": hist_1y[["Open","High","Low","Close","Volume"]].to_dict("index"),
}
if not price and len(hist_1y) > 0:
    block_a["current_price"] = float(hist_1y[["Close"]].iloc[-1]["Close"])
    block_a["price_flag"] = "ESTIMATED"
if block_a["currency"] != "IDR":
    print(f"CURRENCY GATE: expected IDR, got {block_a['currency']} -- check ticker")
print(json.dumps({k:v for k,v in block_a.items() if k != "daily_bars_1y"}, default=str, indent=2))

# ── BLOCK B ─────────────────────────────────────────────────────
print("\n### BLOCK B: Fundamental Data ###")
try:
    cashflow = tk.cashflow
    fcf = None
    if cashflow is not None and "Free Cash Flow" in cashflow.index:
        fs = cashflow.loc["Free Cash Flow"].dropna()
        if len(fs) > 0: fcf = float(fs.iloc[0])
    income = tk.income_stmt
    rev_growth = None
    if income is not None and "Total Revenue" in income.index:
        rev = income.loc["Total Revenue"].dropna()
        if len(rev) >= 2: rev_growth = round((rev.iloc[0]-rev.iloc[1])/abs(rev.iloc[1])*100, 2)
except: fcf = None; rev_growth = None
fund = {
    "trailing_pe": info.get("trailingPE"), "forward_pe": info.get("forwardPE"),
    "peg_ratio": info.get("pegRatio"),
    "price_to_book": info.get("priceToBook"), "ev_to_ebitda": info.get("enterpriseToEbitda"),
    "price_to_sales": info.get("priceToSalesTrailing12Months"),
    "eps_ttm": info.get("trailingEps"), "eps_forward": info.get("forwardEps"),
    "revenue_ttm": info.get("totalRevenue"),
    "revenue_growth_yoy_calc": rev_growth, "revenue_growth_qoq": info.get("revenueGrowth"),
    "earnings_growth_yoy": info.get("earningsGrowth"),
    "gross_margin": info.get("grossMargins"), "operating_margin": info.get("operatingMargins"),
    "net_margin": info.get("profitMargins"), "total_debt": info.get("totalDebt"),
    "total_cash": info.get("totalCash"), "debt_to_equity": info.get("debtToEquity"),
    "current_ratio": info.get("currentRatio"), "quick_ratio": info.get("quickRatio"),
    "roe": info.get("returnOnEquity"), "roa": info.get("returnOnAssets"),
    "free_cash_flow": fcf, "dividend_yield": info.get("dividendYield"),
    "payout_ratio": info.get("payoutRatio"),
}
print(json.dumps(fund, default=str, indent=2))

# ── BLOCK C ─────────────────────────────────────────────────────
print("\n### BLOCK C: Analyst Data ###")
try:
    rec = tk.recommendations_summary
    rec_d = rec.head(1).to_dict("records")[0] if (rec is not None and not rec.empty) else {}
except: rec_d = {}
cp = info.get("currentPrice") or price
mp = info.get("targetMeanPrice")
analyst = {
    "analyst_count": info.get("numberOfAnalystOpinions"),
    "recommendation_key": info.get("recommendationKey"),
    "recommendation_mean": info.get("recommendationMean"),
    "mean_price_target": mp, "high_price_target": info.get("targetHighPrice"),
    "low_price_target": info.get("targetLowPrice"),
    "current_price": cp,
    "upside_to_mean_pct": round((mp-cp)/cp*100,2) if mp and cp else None,
    "strong_buy": rec_d.get("strongBuy"), "buy": rec_d.get("buy"),
    "hold": rec_d.get("hold"), "sell": rec_d.get("sell"),
}
print(json.dumps(analyst, default=str, indent=2))

# ── BLOCK D ─────────────────────────────────────────────────────
print("\n### BLOCK D: News Headlines ###")
try:
    raw_news = tk.news or []
    headlines = []
    for item in raw_news[:10]:
        content = item.get("content", {})
        title = content.get("title") if content else item.get("title")
        pub_info = content.get("provider", {}) if content else {}
        publisher = pub_info.get("displayName") if pub_info else item.get("publisher")
        pub_ts_str = content.get("pubDate") if content else None
        if pub_ts_str: pub_date = pub_ts_str
        else:
            pub_ts = item.get("providerPublishTime")
            pub_date = datetime.utcfromtimestamp(pub_ts).isoformat()+"Z" if pub_ts else None
        headlines.append({"title": title, "publisher": publisher, "date": pub_date})
    print(json.dumps({"headline_count": len(headlines), "headlines": headlines}, default=str, indent=2))
except Exception as e:
    print(json.dumps({"headline_count": 0, "error": str(e)}))

# ── BLOCK E ─────────────────────────────────────────────────────
print("\n### BLOCK E: Technical Indicators ###")
try:
    bars = block_a["daily_bars_1y"]
    df = pd.DataFrame.from_dict(bars, orient="index")
    df.index = pd.to_datetime(df.index); df = df.sort_index()
    df.columns = [c.lower() for c in df.columns]
    df = df[["open","high","low","close","volume"]].apply(pd.to_numeric, errors="coerce").dropna()
    close = df["close"]; high = df["high"]; low = df["low"]; vol = df["volume"]
    df["sma20"] = close.rolling(20).mean(); df["sma50"] = close.rolling(50).mean()
    df["sma200"] = close.rolling(200).mean()
    df["ema12"] = close.ewm(span=12,adjust=False).mean(); df["ema26"] = close.ewm(span=26,adjust=False).mean()
    df["macd"] = df["ema12"]-df["ema26"]; df["macd_signal"] = df["macd"].ewm(span=9,adjust=False).mean()
    df["macd_hist"] = df["macd"]-df["macd_signal"]
    delta = close.diff(); gain = delta.clip(lower=0); loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(com=13,adjust=False).mean(); avg_loss = loss.ewm(com=13,adjust=False).mean()
    rs = avg_gain/avg_loss.replace(0,np.nan); df["rsi14"] = 100-(100/(1+rs))
    df["bb_mid"] = df["sma20"]
    df["bb_upper"] = df["sma20"]+2*close.rolling(20).std()
    df["bb_lower"] = df["sma20"]-2*close.rolling(20).std()
    df["bb_pct"] = (close-df["bb_lower"])/(df["bb_upper"]-df["bb_lower"])
    df["obv"] = (np.sign(close.diff())*vol).fillna(0).cumsum()
    df["vol_sma30"] = vol.rolling(30).mean(); df["vol_ratio"] = vol/df["vol_sma30"]
    df["above_200"] = (df["sma50"]>df["sma200"]).astype(int)
    cross = df["above_200"].diff().replace(0,np.nan).dropna()
    last_cross = None
    if not cross.empty:
        last_cross = {"type":"GOLDEN_CROSS" if cross.iloc[-1]==1 else "DEATH_CROSS",
                      "date":str(cross.index[-1].date())}
    latest = df.iloc[-1]; prev = df.iloc[-2]
    def sf(v,d=4):
        try: return round(float(v),d) if v==v else None
        except: return None
    tech = {
        "latest_date": str(df.index[-1].date()),
        "current_price": sf(latest["close"]),
        "sma20": sf(latest["sma20"]), "sma50": sf(latest["sma50"]), "sma200": sf(latest["sma200"]),
        "macd": sf(latest["macd"]), "macd_signal": sf(latest["macd_signal"]),
        "macd_hist": sf(latest["macd_hist"]), "macd_hist_prev": sf(prev["macd_hist"]),
        "rsi14": sf(latest["rsi14"],2),
        "bb_upper": sf(latest["bb_upper"]), "bb_mid": sf(latest["bb_mid"]),
        "bb_lower": sf(latest["bb_lower"]), "bb_pct": sf(latest["bb_pct"]),
        "obv_trend": "UP" if float(latest["obv"])>float(df["obv"].iloc[-10]) else "DOWN",
        "volume_today": int(latest["volume"]),
        "volume_sma30": sf(latest["vol_sma30"],0), "volume_ratio": sf(latest["vol_ratio"],2),
        "last_cross": last_cross,
        "support_20d": sf(low.rolling(20).min().iloc[-1]),
        "support_50d": sf(low.rolling(50).min().iloc[-1]),
        "resistance_20d": sf(high.rolling(20).max().iloc[-1]),
        "resistance_50d": sf(high.rolling(50).max().iloc[-1]),
        "pct_from_52w_high": sf((float(latest["close"])-float(high.max()))/float(high.max())*100,2),
        "pct_from_52w_low": sf((float(latest["close"])-float(low.min()))/float(low.min())*100,2),
    }
    print(json.dumps(tech, indent=2))
except Exception as e:
    print(f"BLOCK E FAILED: {e}")
    import traceback; traceback.print_exc()

print("\n" + "="*60 + "\nFETCH COMPLETE")
