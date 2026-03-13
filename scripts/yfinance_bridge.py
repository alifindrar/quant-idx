import subprocess
import sys

# Auto-install yfinance if not present
try:
    import yfinance as yf
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "yfinance", "--quiet"])
    import yfinance as yf

import json


def get_usdidr_rate():
    """Fetch live USD/IDR exchange rate from yfinance. Returns float or None on failure."""
    try:
        rate = yf.Ticker("USDIDR=X").info.get("regularMarketPrice") or \
               yf.Ticker("USDIDR=X").fast_info.get("last_price")
        return float(rate) if rate else None
    except Exception:
        return None


def convert_if_usd(value, currency, usd_to_idr_rate, field_name):
    """
    If a numeric value came back in USD and we need IDR, multiply by the
    exchange rate and flag it as converted. Returns the (possibly converted)
    value and an updated note string.
    """
    if value in ("N/A", None) or not isinstance(value, (int, float)):
        return value, currency, None
    if currency == "USD" and usd_to_idr_rate:
        idr_value = round(value * usd_to_idr_rate, 2)
        note = (
            f"{field_name}: converted from USD {value:,.4f} "
            f"x {usd_to_idr_rate:,.0f} = IDR {idr_value:,.2f}"
        )
        return idr_value, "IDR (converted)", note
    return value, currency, None


def fetch_data(ticker_symbol):
    try:
        stock = yf.Ticker(ticker_symbol)
        info = stock.info

        # Grab the currency natively from Yahoo Finance
        native_currency = info.get("currency", "UNKNOWN")
        current_price = info.get("currentPrice", info.get("regularMarketPrice", "N/A"))
        ma50  = info.get("fiftyDayAverage", "N/A")
        ma200 = info.get("twoHundredDayAverage", "N/A")
        fwd_pe = info.get("forwardPE", "N/A")

        is_idx = ticker_symbol.upper().endswith(".JK")
        usd_rate = None
        conversions = []

        # ── Auto-conversion: if an IDX ticker returns USD values, convert to IDR ──
        if is_idx and native_currency == "USD":
            usd_rate = get_usdidr_rate()
            if usd_rate:
                current_price, _, note = convert_if_usd(current_price, native_currency, usd_rate, "current_price")
                if note: conversions.append(note)
                ma50, _, note = convert_if_usd(ma50, native_currency, usd_rate, "50_day_ma")
                if note: conversions.append(note)
                ma200, _, note = convert_if_usd(ma200, native_currency, usd_rate, "200_day_ma")
                if note: conversions.append(note)
                reported_currency = "IDR (converted from USD)"
            else:
                reported_currency = "USD (conversion failed -- USDIDR=X unavailable)"
        else:
            reported_currency = native_currency

        # Build the data dictionary
        data = {
            "ticker": ticker_symbol.upper(),
            "native_currency": native_currency,
            "reported_currency": reported_currency,
            "usd_to_idr_rate": usd_rate,
            "current_price": current_price,
            "50_day_ma": ma50,
            "200_day_ma": ma200,
            "forward_pe": fwd_pe,
        }

        if conversions:
            data["conversion_log"] = conversions

        # ── Currency verification gate (Rule 6, RULES.md) ─────────────────────
        if is_idx and native_currency not in ("IDR", "USD"):
            # Neither IDR nor USD — unexpected, escalate
            data["CURRENCY_WARNING"] = (
                f"TICKER ERROR -- unexpected currency '{native_currency}' "
                f"for IDX ticker {ticker_symbol.upper()}. "
                f"Verify ticker and re-run."
            )
        elif is_idx and native_currency == "USD" and not usd_rate:
            data["CURRENCY_WARNING"] = (
                f"CONVERSION FAILED -- ticker returned USD but USDIDR=X "
                f"rate could not be fetched. Values remain in USD."
            )

        # Print as JSON for the Agent to read
        print(json.dumps(data, indent=2))

    except Exception as e:
        print(json.dumps({"error": f"Failed to fetch data for {ticker_symbol}: {str(e)}"}))


if __name__ == "__main__":
    if len(sys.argv) > 1:
        fetch_data(sys.argv[1])
    else:
        print(json.dumps({"error": "No ticker provided."}))
