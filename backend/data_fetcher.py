# backend/data_fetcher.py
# The ONLY module that talks to yfinance. Everything else receives clean
# DataFrames from here — no other file should import yfinance directly.

import yfinance as yf
import pandas as pd


def fetch_history(ticker: str, period: str = "6mo", interval: str = "1d") -> pd.DataFrame:
    """
    Fetch historical OHLCV data for one ticker.
    interval: '1d' (daily), '1wk' (weekly), '1mo' (monthly)
    period: how far back, e.g. '6mo', '1y', '2y'
    Returns an empty DataFrame (not an error) if the ticker/data is unavailable —
    callers should check df.empty before using the result.
    """
    try:
        df = yf.Ticker(ticker).history(period=period, interval=interval)
        if df.empty:
            print(f"[warn] no data returned for {ticker} ({interval})")
        return df
    except Exception as e:
        print(f"[error] failed to fetch {ticker}: {e}")
        return pd.DataFrame()


def fetch_multi_timeframe(ticker: str) -> dict:
    """
    Fetches Monthly, Weekly, and Daily history for one ticker in one call —
    this is what the multi-timeframe alignment check (Step 3) needs.
    """
    return {
        "monthly": fetch_history(ticker, period="2y", interval="1mo"),
        "weekly": fetch_history(ticker, period="1y", interval="1wk"),
        "daily": fetch_history(ticker, period="6mo", interval="1d"),
    }


def fetch_latest_close_and_change(ticker: str) -> dict | None:
    """
    Returns the latest close price and % change vs previous close —
    used for ranking indices/sectors by daily performance (Step 2).
    """
    df = fetch_history(ticker, period="5d", interval="1d")
    if df.empty or len(df) < 2:
        return None
    latest = df["Close"].iloc[-1]
    previous = df["Close"].iloc[-2]
    pct_change = ((latest - previous) / previous) * 100
    return {"ticker": ticker, "latest_close": latest, "pct_change": pct_change}


def rank_by_performance(ticker_map: dict, top_n: int = 3, ascending: bool = False) -> list[dict]:
    """
    ticker_map: {"Display Name": "YAHOO_SYMBOL"}
    ascending=True -> biggest losers first (for bearish bias)
    ascending=False -> biggest gainers first (for bullish bias)
    """
    results = []
    for name, symbol in ticker_map.items():
        data = fetch_latest_close_and_change(symbol)
        if data:
            data["name"] = name
            results.append(data)

    results.sort(key=lambda x: x["pct_change"], reverse=not ascending)
    return results[:top_n]
