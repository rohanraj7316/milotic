"""Technical analysis indicator wrappers around pandas-ta."""


import pandas as pd


def compute_rsi(closes: list[float], length: int = 14) -> float | None:
    """Return the most recent RSI value for a closing-price series."""
    if len(closes) < length + 1:
        return None
    s = pd.Series(closes)
    result = s.ta.rsi(length=length)
    return float(result.iloc[-1]) if result is not None else None


def compute_macd(
    closes: list[float], fast: int = 12, slow: int = 26, signal: int = 9
) -> dict[str, float | None]:
    """Return MACD line, signal line, and histogram for a closing-price series."""
    s = pd.Series(closes)
    result = s.ta.macd(fast=fast, slow=slow, signal=signal)
    if result is None or result.empty:
        return {"macd": None, "signal": None, "histogram": None}
    row = result.iloc[-1]
    keys = result.columns.tolist()
    return {
        "macd": float(row[keys[0]]) if not pd.isna(row[keys[0]]) else None,
        "signal": float(row[keys[2]]) if not pd.isna(row[keys[2]]) else None,
        "histogram": float(row[keys[1]]) if not pd.isna(row[keys[1]]) else None,
    }


def compute_sma(closes: list[float], length: int = 20) -> float | None:
    """Return the most recent SMA value."""
    if len(closes) < length:
        return None
    s = pd.Series(closes)
    result = s.ta.sma(length=length)
    return float(result.iloc[-1]) if result is not None else None
