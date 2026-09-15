# backend/indicators.py
# Pure math functions. Take a DataFrame with OHLCV columns, return the DataFrame
# with new indicator columns added. No data fetching, no printing, no I/O here —
# keeps this module trivially testable and reusable across timeframes.

import pandas as pd
import numpy as np


def add_moving_average(df: pd.DataFrame, period: int = 20, column: str = "Close") -> pd.DataFrame:
    """Adds a simple moving average column, e.g. 'SMA_20'."""
    df[f"SMA_{period}"] = df[column].rolling(window=period).mean()
    return df


def add_daily_return(df: pd.DataFrame, column: str = "Close") -> pd.DataFrame:
    """Adds day-over-day percentage return."""
    df["Daily_Return"] = df[column].pct_change() * 100
    return df


def add_volatility(df: pd.DataFrame, period: int = 20) -> pd.DataFrame:
    """Rolling standard deviation of daily returns — a simple volatility measure."""
    if "Daily_Return" not in df.columns:
        df = add_daily_return(df)
    df[f"Volatility_{period}"] = df["Daily_Return"].rolling(window=period).std()
    return df


def add_rsi(df: pd.DataFrame, period: int = 14, column: str = "Close") -> pd.DataFrame:
    """
    Relative Strength Index. Measures momentum: >60 generally means strong
    upward momentum, <40 generally means strong downward momentum (using the
    40/60 bands from the screening spec, rather than the textbook 30/70).
    """
    delta = df[column].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()

    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    df[f"RSI_{period}"] = rsi
    return df


def add_bollinger_bands(df: pd.DataFrame, period: int = 20, std_dev: int = 2, column: str = "Close") -> pd.DataFrame:
    """
    Adds upper/lower Bollinger Bands and the middle SMA.
    Band squeeze = bands very close together (low volatility, breakout may be coming).
    Band walking = price hugging the upper or lower band (strong trend continuation).
    """
    mid = df[column].rolling(window=period).mean()
    std = df[column].rolling(window=period).std()

    df[f"BB_Mid_{period}"] = mid
    df[f"BB_Upper_{period}"] = mid + (std_dev * std)
    df[f"BB_Lower_{period}"] = mid - (std_dev * std)
    df[f"BB_Width_{period}"] = df[f"BB_Upper_{period}"] - df[f"BB_Lower_{period}"]
    return df


def add_volume_confirmation(df: pd.DataFrame, period: int = 20, volume_col: str = "Volume") -> pd.DataFrame:
    """
    Flags whether today's volume exceeds its own 20-period average —
    the 'is this move backed by real conviction' check.
    """
    df[f"Volume_SMA_{period}"] = df[volume_col].rolling(window=period).mean()
    df["Volume_Confirmed"] = df[volume_col] > df[f"Volume_SMA_{period}"]
    return df


def classify_bollinger_status(row, period: int = 20) -> str:
    """Given a row that already has BB columns, label its current BB behaviour."""
    price = row["Close"]
    upper = row[f"BB_Upper_{period}"]
    lower = row[f"BB_Lower_{period}"]
    mid = row[f"BB_Mid_{period}"]
    width = row[f"BB_Width_{period}"]

    if pd.isna(upper) or pd.isna(lower):
        return "insufficient_data"

    # squeeze: width unusually small relative to price
    if width / price < 0.04:
        return "squeeze"
    if price >= upper * 0.98:
        return "walking_upper_band" if price > mid else "rejecting_upper_band"
    if price <= lower * 1.02:
        return "walking_lower_band" if price < mid else "rejecting_lower_band"
    return "neutral"


def add_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Convenience: run every indicator in one call, in the right order."""
    df = add_daily_return(df)
    df = add_moving_average(df, period=20)
    df = add_volatility(df, period=20)
    df = add_rsi(df, period=14)
    df = add_bollinger_bands(df, period=20, std_dev=2)
    df = add_volume_confirmation(df, period=20)
    return df
