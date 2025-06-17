"""Basic risk management utilities."""

from src.execution.portfolio import Portfolio
from src.config import settings


def exceed_max_drawdown(portfolio: Portfolio, current_price: float) -> bool:
    """Return ``True`` if the portfolio drawdown exceeds ``settings.max_drawdown_pct``.

    The portfolio tracks the peak total value (USD) seen so far. When the
    difference between this peak and the current value is larger than the
    configured percentage, the function returns ``True``.
    """
    current_value = portfolio.total_value(current_price)
    if current_value > portfolio.peak_value:
        portfolio.peak_value = current_value
        return False

    drawdown = (portfolio.peak_value - current_value) / portfolio.peak_value * 100
    return drawdown >= settings.max_drawdown_pct
