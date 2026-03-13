import subprocess, sys, os
def ensure(pkg):
    try: __import__(pkg)
    except ImportError: subprocess.check_call([sys.executable, "-m", "pip", "install", pkg, "--quiet", "--break-system-packages"])
ensure("yfinance"); ensure("pandas"); ensure("numpy")

import yfinance as yf, json, pandas as pd, numpy as np
from datetime import datetime

TICKER = "POWR.JK"
FETCH_TIME = datetime.utcnow().isoformat() + "Z"
print(f"POWR.JK DATA FETCH -- {FETCH_TIME}")
print("=" * 60)

# ── BLOCK A: Price & Market Data ───────────────────────────────
print("\n### BLOCK A: Price & Market Data ###")
try:
    tk = yf.Ticker(TICKER)
    info = tk.info
    price_data = {
        "ticker": TICKER, "fetch_timestamp": FETCH_TIME,
        "current_price": info.get("currentPrice") or info.get("regularMarketPrice"),
        "open": info.get("open") or info.get("regularMarketOpen"),
        "day_high": info.get("dayHigh"), "day_low": info.get("dayLow"),
        "prev_close": info.get("previousClose"),
        "volume": info.get("volume") or info.get("regularMarketVolume"),
        "avg_volume_10d": info.get("averageVolume10days"),
        "avg_volume_3m": info.get("averageVolume"),
        "market_cap": info.get("marketCap"),
        "52w_high": info.get("fiftyTwoWeekHigh"),
        "52w_low": info.get("fiftyTwoWeekLow"),
        "beta_5y": info.get("beta"),
        "shares_outstanding": info.get("sharesOutstanding"),
        "company_name": info.get("longName") or info.get("shortName"),
        "sector": info.get("sector"), "industry": info.get("industry"),
        "exchange": info.get("exchange"),
    }
    hist_1y = tk.history(period="1y", interval="1d", auto_adjust=True)
    hist_1y.index = hist_1y.index.strftime("%Y-%m-%d")
    hist_2y_wk = tk.history(period="2y", interval="1wk", auto_adjust=True)
    hist_2y_wk.index = hist_2y_wk.index.strftime("%Y-%m-%d")
    block_a = {"price_data": price_data,
               "daily_bars_1y": hist_1y[["Open","High","Low","Close","Volume"]].to_dict("index"),
               "weekly_bars_2y": hist_2y_wk[["Open","High","Low","Close","Volume"]].to_dict("index"),
               "bar_count_daily": len(hist_1y), "bar_count_weekly": len(hist_2y_wk)}
    if price_data["current_price"] is None and len(hist_1y) < 10:
        print("ABORT: No price data"); sys.exit(1)
    if price_data["current_price"] is None:
        price_data["current_price"] = float(hist_1y[["Close"]].iloc[-1]["Close"])
        price_data["current_price_flag"] = "ESTIMATED"
    print(json.dumps(block_a, default=str, indent=2))
    block_a_ok = True
except Exception as e:
    print(f"BLOCK A FAILED: {e}"); block_a_ok = False; block_a = {}

# ── BLOCK B: Fundamental Data ──────────────────────────────────
print("\n### BLOCK B: Fundamental Data ###")
try:
    tk2 = yf.Ticker(TICKER); info2 = tk2.info
    try:
        income_annual = tk2.income_stmt; cashflow = tk2.cashflow; earnings_hist = tk2.earnings_history
    except: income_annual = cashflow = earnings_hist = None
    rev_growth_yoy = None
    if income_annual is not None and "Total Revenue" in income_annual.index:
        rev = income_annual.loc["Total Revenue"].dropna()
        if len(rev) >= 2: rev_growth_yoy = round((rev.iloc[0]-rev.iloc[1])/abs(rev.iloc[1])*100, 2)
    eps_surprises = []
    if earnings_hist is not None and not earnings_hist.empty:
        for _, row in earnings_hist.tail(4).iterrows():
            eps_surprises.append({"period": str(row.get("period","")), "actual": row.get("epsActual"),
                                  "estimate": row.get("epsEstimate"), "surprise_pct": row.get("surprisePercent")})
    fcf = None
    if cashflow is not None and "Free Cash Flow" in cashflow.index:
        fs = cashflow.loc["Free Cash Flow"].dropna()
        if len(fs) > 0: fcf = float(fs.iloc[0])
    fundamental_data = {
        "trailing_pe": info2.get("trailingPE"), "forward_pe": info2.get("forwardPE"),
        "price_to_sales": info2.get("priceToSalesTrailing12Months"),
        "price_to_book": info2.get("priceToBook"),
        "ev_to_ebitda": info2.get("enterpriseToEbitda"), "ev_to_revenue": info2.get("enterpriseToRevenue"),
        "peg_ratio": info2.get("pegRatio"), "revenue_ttm": info2.get("totalRevenue"),
        "revenue_growth_yoy": rev_growth_yoy, "revenue_growth_qoq": info2.get("revenueGrowth"),
        "earnings_growth_yoy": info2.get("earningsGrowth"),
        "eps_ttm": info2.get("trailingEps"), "eps_forward": info2.get("forwardEps"),
        "eps_surprises_last_4q": eps_surprises,
        "gross_margin": info2.get("grossMargins"), "operating_margin": info2.get("operatingMargins"),
        "net_margin": info2.get("profitMargins"), "total_debt": info2.get("totalDebt"),
        "total_cash": info2.get("totalCash"), "debt_to_equity": info2.get("debtToEquity"),
        "current_ratio": info2.get("currentRatio"), "quick_ratio": info2.get("quickRatio"),
        "return_on_equity": info2.get("returnOnEquity"), "return_on_assets": info2.get("returnOnAssets"),
        "free_cash_flow": fcf, "dividend_yield": info2.get("dividendYield"), "payout_ratio": info2.get("payoutRatio"),
    }
    print(json.dumps(fundamental_data, default=str, indent=2))
except Exception as e:
    print(f"BLOCK B FAILED: {e}"); fundamental_data = {}

# ── BLOCK C: Analyst Data ─────────────────────────────────────
print("\n### BLOCK C: Analyst Data ###")
try:
    tk3 = yf.Ticker(TICKER); info3 = tk3.info
    try:
        rec = tk3.recommendations_summary
        rec_dict = rec.head(1).to_dict("records")[0] if (rec is not None and not rec.empty) else {}
    except: rec_dict = {}
    try:
        cal = tk3.calendar
        next_earn = str(cal.get("Earnings Date",[None])[0]) if cal else None
        eps_est = cal.get("EPS Estimate") if cal else None
    except: next_earn = None; eps_est = None
    cp = info3.get("currentPrice") or info3.get("regularMarketPrice")
    mp = info3.get("targetMeanPrice")
    analyst_data = {
        "analyst_count": info3.get("numberOfAnalystOpinions"),
        "recommendation_key": info3.get("recommendationKey"),
        "recommendation_mean": info3.get("recommendationMean"),
        "mean_price_target": mp, "high_price_target": info3.get("targetHighPrice"),
        "low_price_target": info3.get("targetLowPrice"), "median_price_target": info3.get("targetMedianPrice"),
        "current_price": cp,
        "upside_to_mean_pct": round((mp-cp)/cp*100,2) if mp and cp else None,
        "strong_buy_count": rec_dict.get("strongBuy"), "buy_count": rec_dict.get("buy"),
        "hold_count": rec_dict.get("hold"), "sell_count": rec_dict.get("sell"),
        "strong_sell_count": rec_dict.get("strongSell"),
        "next_earnings_date": next_earn, "eps_estimate_current_q": eps_est,
    }
    print(json.dumps(analyst_data, default=str, indent=2))
except Exception as e:
    print(f"BLOCK C FAILED: {e}"); analyst_data = {}

# ── BLOCK D: News ─────────────────────────────────────────────
print("\n### BLOCK D: News Headlines ###")
try:
    tk4 = yf.Ticker(TICKER)
    raw_news = tk4.news or []
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
        url = content.get("canonicalUrl",{}).get("url") if content else item.get("link")
        headlines.append({"title": title, "publisher": publisher, "date": pub_date, "url": url})
    news_output = {"ticker": TICKER, "headline_count": len(headlines), "headlines": headlines, "fetch_timestamp": FETCH_TIME}
    print(json.dumps(news_output, default=str, indent=2))
except Exception as e:
    print(f"BLOCK D FAILED: {e}"); news_output = {"headline_count": 0, "headlines": []}

# ── BLOCK E: Technical Indicators ─────────────────────────────
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
    df["bb_mid"] = df["sma20"]; df["bb_upper"] = df["sma20"]+2*close.rolling(20).std()
    df["bb_lower"] = df["sma20"]-2*close.rolling(20).std()
    df["bb_width"] = (df["bb_upper"]-df["bb_lower"])/df["bb_mid"]
    df["bb_pct"] = (close-df["bb_lower"])/(df["bb_upper"]-df["bb_lower"])
    tr = pd.concat([high-low,(high-close.shift()).abs(),(low-close.shift()).abs()],axis=1).max(axis=1)
    df["atr14"] = tr.ewm(com=13,adjust=False).mean(); df["atr_pct"] = df["atr14"]/close*100
    df["obv"] = (np.sign(close.diff())*vol).fillna(0).cumsum()
    df["vol_sma30"] = vol.rolling(30).mean(); df["vol_ratio"] = vol/df["vol_sma30"]
    df["above_200"] = (df["sma50"]>df["sma200"]).astype(int)
    cross = df["above_200"].diff().replace(0,np.nan).dropna()
    last_cross = None
    if not cross.empty:
        last_cross = {"type": "GOLDEN_CROSS" if cross.iloc[-1]==1 else "DEATH_CROSS",
                      "date": str(cross.index[-1].date()), "bars_ago": len(df)-df.index.get_loc(cross.index[-1])-1}
    latest = df.iloc[-1]; prev = df.iloc[-2] if len(df)>=2 else df.iloc[-1]
    def sf(v,d=4):
        try: return round(float(v),d) if not (v!=v) else None
        except: return None
    tech_result = {
        "latest_date": str(df.index[-1].date()), "current_price": sf(latest["close"]),
        "sma20": sf(latest["sma20"]), "sma50": sf(latest["sma50"]), "sma200": sf(latest["sma200"]),
        "ema12": sf(latest["ema12"]), "ema26": sf(latest["ema26"]),
        "macd": sf(latest["macd"]), "macd_signal": sf(latest["macd_signal"]),
        "macd_hist": sf(latest["macd_hist"]), "macd_hist_prev": sf(prev["macd_hist"]),
        "rsi14": sf(latest["rsi14"],2), "bb_upper": sf(latest["bb_upper"]), "bb_mid": sf(latest["bb_mid"]),
        "bb_lower": sf(latest["bb_lower"]), "bb_width": sf(latest["bb_width"]), "bb_pct": sf(latest["bb_pct"]),
        "atr14": sf(latest["atr14"]), "atr_pct": sf(latest["atr_pct"]),
        "obv_trend": "UP" if float(latest["obv"])>float(df["obv"].iloc[-10]) else "DOWN",
        "volume_today": int(latest["volume"]), "volume_sma30": sf(latest["vol_sma30"],0),
        "volume_ratio": sf(latest["vol_ratio"],2), "last_cross": last_cross,
        "support_20d": sf(low.rolling(20).min().iloc[-1]), "support_50d": sf(low.rolling(50).min().iloc[-1]),
        "resistance_20d": sf(high.rolling(20).max().iloc[-1]), "resistance_50d": sf(high.rolling(50).max().iloc[-1]),
        "pct_from_52w_high": sf((float(latest["close"])-float(high.max()))/float(high.max())*100,2),
        "pct_from_52w_low": sf((float(latest["close"])-float(low.min()))/float(low.min())*100,2),
    }
    print(json.dumps(tech_result, indent=2))
except Exception as e:
    print(f"BLOCK E FAILED: {e}")
    import traceback; traceback.print_exc()

print("\n" + "="*60 + "\nFETCH COMPLETE")
