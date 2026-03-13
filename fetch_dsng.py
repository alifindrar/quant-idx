import subprocess, sys
def ensure(pkg):
    try: __import__(pkg)
    except ImportError: subprocess.check_call([sys.executable, "-m", "pip", "install", pkg, "--quiet"])
ensure("yfinance"); ensure("pandas"); ensure("numpy")

import yfinance as yf, json, pandas as pd, numpy as np
from datetime import datetime, timezone

TICKER = "DSNG.JK"
FETCH_TIME = datetime.now(timezone.utc).isoformat()
print(f"DSNG.JK DATA FETCH -- {FETCH_TIME}")
print("=" * 60)

tk = yf.Ticker(TICKER)
info = tk.info

# -- BLOCK A --
print("\n### BLOCK A: Price & Market Data ###")
price = info.get("currentPrice") or info.get("regularMarketPrice")
hist = tk.history(period="1y", interval="1d", auto_adjust=True)
bar_count = len(hist)
if bar_count == 0:
    print("[ABORT] Empty history — no price data returned.")
    sys.exit(1)

currency = info.get("currency", "IDR")
block_a = {
    "ticker": TICKER, "currency": currency,
    "company_name": info.get("longName") or info.get("shortName"),
    "sector": info.get("sector"), "industry": info.get("industry"),
    "current_price": price or float(hist["Close"].iloc[-1]),
    "open": info.get("open"), "day_high": info.get("dayHigh"), "day_low": info.get("dayLow"),
    "prev_close": info.get("previousClose"),
    "volume": info.get("volume"), "avg_volume_10d": info.get("averageVolume10days"),
    "avg_volume_3m": info.get("averageVolume"),
    "market_cap": info.get("marketCap"),
    "52w_high": info.get("fiftyTwoWeekHigh"), "52w_low": info.get("fiftyTwoWeekLow"),
    "beta_5y": info.get("beta"), "shares_outstanding": info.get("sharesOutstanding"),
    "bar_count": bar_count,
}
if currency != "IDR":
    print(f"[CURRENCY GATE] Expected IDR, got {currency} -- fix ticker before proceeding.")
print(json.dumps(block_a, default=str, indent=2))

# -- BLOCK B --
print("\n### BLOCK B: Fundamental Data ###")
fund = {
    "trailing_pe": info.get("trailingPE"), "forward_pe": info.get("forwardPE"),
    "price_to_book": info.get("priceToBook"), "ev_to_ebitda": info.get("enterpriseToEbitda"),
    "price_to_sales": info.get("priceToSalesTrailing12Months"),
    "eps_ttm": info.get("trailingEps"), "eps_forward": info.get("forwardEps"),
    "revenue_ttm": info.get("totalRevenue"),
    "revenue_growth_qoq": info.get("revenueGrowth"),
    "earnings_growth_yoy": info.get("earningsGrowth"),
    "gross_margin": info.get("grossMargins"), "operating_margin": info.get("operatingMargins"),
    "net_margin": info.get("profitMargins"), "total_debt": info.get("totalDebt"),
    "total_cash": info.get("totalCash"), "debt_to_equity": info.get("debtToEquity"),
    "current_ratio": info.get("currentRatio"), "quick_ratio": info.get("quickRatio"),
    "roe": info.get("returnOnEquity"), "roa": info.get("returnOnAssets"),
    "free_cash_flow": info.get("freeCashflow"),
    "dividend_yield": info.get("dividendYield"), "payout_ratio": info.get("payoutRatio"),
}
print(json.dumps(fund, default=str, indent=2))

# -- BLOCK C --
print("\n### BLOCK C: Analyst Data ###")
mp = info.get("targetMeanPrice")
cp = block_a["current_price"]
analyst = {
    "analyst_count": info.get("numberOfAnalystOpinions"),
    "recommendation_key": info.get("recommendationKey"),
    "recommendation_mean": info.get("recommendationMean"),
    "mean_price_target": mp, "high_price_target": info.get("targetHighPrice"),
    "low_price_target": info.get("targetLowPrice"), "current_price": cp,
    "upside_to_mean_pct": round((mp - cp) / cp * 100, 2) if mp and cp else None,
}
try:
    rec = tk.recommendations_summary
    if rec is not None and not rec.empty:
        r = rec.head(1).to_dict("records")[0]
        analyst.update({"strong_buy": r.get("strongBuy"), "buy": r.get("buy"),
                         "hold": r.get("hold"), "sell": r.get("sell")})
except: pass
print(json.dumps(analyst, default=str, indent=2))

# -- BLOCK D --
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
        if pub_ts_str:
            pub_date = pub_ts_str
        else:
            pub_ts = item.get("providerPublishTime")
            pub_date = datetime.fromtimestamp(pub_ts, tz=timezone.utc).isoformat() if pub_ts else None
        headlines.append({"title": title, "publisher": publisher, "date": pub_date})
    print(json.dumps({"headline_count": len(headlines), "headlines": headlines}, default=str, indent=2))
except Exception as e:
    print(json.dumps({"headline_count": 0, "error": str(e)}))

# -- BLOCK E --
print("\n### BLOCK E: Technical Indicators ###")
try:
    df = hist.copy()
    df.columns = [c.lower() for c in df.columns]
    close = df["close"]; high = df["high"]; low = df["low"]; vol = df["volume"]
    sma20 = close.rolling(20).mean()
    sma50 = close.rolling(50).mean()
    sma200 = close.rolling(200).mean()
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    macd_sig = macd.ewm(span=9, adjust=False).mean()
    macd_hist = macd - macd_sig
    delta = close.diff(); gain = delta.clip(lower=0); loss = -delta.clip(upper=0)
    rs = gain.ewm(com=13, adjust=False).mean() / loss.ewm(com=13, adjust=False).mean().replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    bb_upper = sma20 + 2 * close.rolling(20).std()
    bb_lower = sma20 - 2 * close.rolling(20).std()
    bb_pct = (close - bb_lower) / (bb_upper - bb_lower)
    obv = (np.sign(close.diff()) * vol).fillna(0).cumsum()
    vol_sma30 = vol.rolling(30).mean()
    above200 = (sma50 > sma200).astype(int)
    cross = above200.diff().replace(0, np.nan).dropna()
    last_cross = None
    if not cross.empty:
        last_cross = {"type": "GOLDEN_CROSS" if cross.iloc[-1] == 1 else "DEATH_CROSS",
                      "date": str(cross.index[-1].date())}
    lx = df.iloc[-1]
    def sf(v, d=4):
        try: return round(float(v), d) if v == v else None
        except: return None
    tech = {
        "latest_date": str(df.index[-1].date()),
        "current_price": sf(lx["close"]),
        "sma20": sf(sma20.iloc[-1]), "sma50": sf(sma50.iloc[-1]), "sma200": sf(sma200.iloc[-1]),
        "macd": sf(macd.iloc[-1]), "macd_signal": sf(macd_sig.iloc[-1]),
        "macd_hist": sf(macd_hist.iloc[-1]), "macd_hist_prev": sf(macd_hist.iloc[-2]),
        "rsi14": sf(rsi.iloc[-1], 2),
        "bb_upper": sf(bb_upper.iloc[-1]), "bb_mid": sf(sma20.iloc[-1]), "bb_lower": sf(bb_lower.iloc[-1]),
        "bb_pct": sf(bb_pct.iloc[-1]),
        "obv_trend": "UP" if float(obv.iloc[-1]) > float(obv.iloc[-10]) else "DOWN",
        "volume_today": int(lx["volume"]),
        "volume_sma30": sf(vol_sma30.iloc[-1], 0),
        "volume_ratio": sf(lx["volume"] / vol_sma30.iloc[-1], 2),
        "last_cross": last_cross,
        "support_20d": sf(low.rolling(20).min().iloc[-1]),
        "support_50d": sf(low.rolling(50).min().iloc[-1]),
        "resistance_20d": sf(high.rolling(20).max().iloc[-1]),
        "resistance_50d": sf(high.rolling(50).max().iloc[-1]),
        "pct_from_52w_high": sf((float(lx["close"]) - float(high.max())) / float(high.max()) * 100, 2),
        "pct_from_52w_low": sf((float(lx["close"]) - float(low.min())) / float(low.min()) * 100, 2),
    }
    print(json.dumps(tech, indent=2))
except Exception as e:
    print(f"BLOCK E FAILED: {e}")
    import traceback; traceback.print_exc()

print("\n" + "=" * 60 + "\nFETCH COMPLETE")
