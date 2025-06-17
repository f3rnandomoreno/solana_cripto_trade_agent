from typing import List, Tuple
import pandas as pd


def ema(prices: List[float], span: int) -> float:
    """Calculate exponential moving average for the given span."""
    series = pd.Series(prices)
    return series.ewm(span=span, adjust=False).mean().iloc[-1]


def rsi(prices: List[float], window: int = 14) -> float:
    """Calculate Relative Strength Index (RSI)."""
    series = pd.Series(prices)
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.rolling(window=window).mean()
    avg_loss = loss.rolling(window=window).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.iloc[-1]


def bollinger_bands(prices: List[float], window: int = 20, num_std: float = 2) -> Tuple[float, float]:
    """Return upper and lower Bollinger Bands."""
    series = pd.Series(prices)
    sma = series.rolling(window=window).mean()
    std = series.rolling(window=window).std()
    upper = sma + num_std * std
    lower = sma - num_std * std
    return upper.iloc[-1], lower.iloc[-1]
