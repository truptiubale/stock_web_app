# backend/screener.py
# Implements Steps 1-4 of the screening pipeline described in the docs.
# This is the ONLY module that should be called from the frontend for
# "what should I look at today" — it orchestrates data_fetcher + indicators.

import pandas as pd
from backend import data_fetcher, indicators
import config


def get_global_bias() -> str:
    """
    Step 1: check global benchmarks. Returns 'bullish' or 'bearish'
    based on whether more benchmarks closed up or down.
    """
    up, down = 0, 0
    for name, symbol in config.GLOBAL_BENCHMARKS.items():
        data = data_fetcher.fetch_latest_close_and_change(symbol)
        if data is None:
            continue
        if data["pct_change"] >= 0:
            up += 1
        else:
            down += 1
    return "bullish" if up >= down else "bearish"


def rank_indian_indices(bias: str) -> list[dict]:
    """Step 2: rank sector + thematic indices by performance, direction depends on bias."""
    ascending = bias == "bearish"  # bearish -> want biggest losers first
    all_indices = {**config.SECTOR_INDICES, **config.THEMATIC_INDICES}
    return data_fetcher.rank_by_performance(all_indices, top_n=3, ascending=ascending)


def check_timeframe_alignment(ticker: str, bias: str) -> bool:
    """
    Step 3: Monthly and Weekly trend must agree with EACH OTHER (and with the
    bias) — this is the real, established trend. Daily is deliberately NOT
    required to agree: a daily move opposite Monthly/Weekly is treated as a
    pullback/mean-reversion moment, not a disqualifying signal (that's what
    the daily RSI 40/60 trigger in Step 4 is for). Only Monthly-vs-Weekly
    disagreement fails this check.
    'Agree' = price above its own 20-period SMA on that timeframe (bullish)
    or below it (bearish).
    """
    data = data_fetcher.fetch_multi_timeframe(ticker)

    monthly_df, weekly_df = data["monthly"], data["weekly"]
    if monthly_df.empty or len(monthly_df) < 20 or weekly_df.empty or len(weekly_df) < 20:
        return False  # not enough data to judge -> fail safe

    monthly_df = indicators.add_moving_average(monthly_df, period=20)
    weekly_df = indicators.add_moving_average(weekly_df, period=20)

    monthly_last = monthly_df.iloc[-1]
    weekly_last = weekly_df.iloc[-1]

    monthly_above_sma = monthly_last["Close"] > monthly_last["SMA_20"]
    weekly_above_sma = weekly_last["Close"] > weekly_last["SMA_20"]

    # Monthly and Weekly must match each other first
    if monthly_above_sma != weekly_above_sma:
        return False

    # And that shared direction must match the day's bias
    if bias == "bullish" and not monthly_above_sma:
        return False
    if bias == "bearish" and monthly_above_sma:
        return False

    return True  # Daily is intentionally not checked here


def validate_with_indicators(ticker: str) -> dict:
    """
    Step 4: pulls daily data, runs full indicator set, returns a summary dict
    with RSI, Bollinger status, and volume confirmation for the verdict table.
    """
    df = data_fetcher.fetch_history(ticker, period="6mo", interval="1d")
    if df.empty or len(df) < config.BB_PERIOD:
        return {"ticker": ticker, "verdict": "insufficient_data"}

    df = indicators.add_all_indicators(df)
    last = df.iloc[-1]

    bb_status = indicators.classify_bollinger_status(last, period=config.BB_PERIOD)
    rsi_value = last.get(f"RSI_{config.RSI_PERIOD}")
    volume_confirmed = bool(last.get("Volume_Confirmed", False))

    return {
        "ticker": ticker,
        "rsi": round(rsi_value, 2) if pd.notna(rsi_value) else None,
        "bollinger_status": bb_status,
        "volume_confirmed": volume_confirmed,
    }


def run_daily_screen() -> pd.DataFrame:
    """
    Runs the full pipeline end-to-end and returns the daily summary table
    described in the docs: index name, global bias, indicator readings, verdict.
    """
    bias = get_global_bias()
    print(f"Global sentiment bias: {bias}")

    ranked = rank_indian_indices(bias)
    if not ranked:
        print("[warn] no ranked indices returned — check network/tickers")
        return pd.DataFrame()

    rows = []
    for candidate in ranked:
        ticker = candidate["ticker"]
        aligned = check_timeframe_alignment(ticker, bias)
        indicator_summary = validate_with_indicators(ticker)

        verdict = "insufficient_data"
        if indicator_summary.get("rsi") is not None:
            if aligned and indicator_summary["volume_confirmed"]:
                verdict = "validated_trending_sector"
            elif aligned:
                verdict = "trend_aligned_low_conviction"  # timeframes agree, volume doesn't confirm
            else:
                verdict = "rejected_timeframe_conflict"

        rows.append({
            "name": candidate["name"],
            "ticker": ticker,
            "pct_change": round(candidate["pct_change"], 2),
            "global_bias": bias,
            "timeframe_aligned": aligned,
            "rsi": indicator_summary.get("rsi"),
            "bollinger_status": indicator_summary.get("bollinger_status"),
            "volume_confirmed": indicator_summary.get("volume_confirmed"),
            "verdict": verdict,
        })

    return pd.DataFrame(rows)


if __name__ == "__main__":
    result = run_daily_screen()
    if not result.empty:
        print(result.to_string(index=False))
    else:
        print("No results — check your internet connection and ticker symbols in config.py")
