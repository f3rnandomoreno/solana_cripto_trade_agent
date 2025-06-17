from typing import List
from .indicators import ema, rsi, bollinger_bands


def generate_signal(prices: List[float]) -> str:
    """Return BUY, SELL or HOLD based on simple indicator rules."""
    if len(prices) < 50:
        return "HOLD"

    last_price = prices[-1]
    ema12 = ema(prices, 12)
    ema50 = ema(prices, 50)
    rsi_val = rsi(prices, 14)
    upper_bb, lower_bb = bollinger_bands(prices)

    if rsi_val > 70 and last_price >= upper_bb:
        return "SELL"
    if rsi_val < 30 and last_price <= lower_bb:
        return "BUY"
    if ema12 > ema50 and rsi_val < 70:
        return "HOLD"
    return "HOLD"
