import pytest
from src.execution.portfolio import Portfolio
from src.strategy.risk import exceed_max_drawdown


@pytest.mark.asyncio
async def test_exceed_max_drawdown_triggers():
    portfolio = Portfolio(quote_balance=1000.0)
    # simulate holding 10 SOL purchased at 100 USD
    portfolio.base_balance = 10
    portfolio.quote_balance = 0.0

    assert exceed_max_drawdown(portfolio, 80.0)  # 20% drop from peak 1000


@pytest.mark.asyncio
async def test_exceed_max_drawdown_updates_peak():
    portfolio = Portfolio(quote_balance=1000.0)
    portfolio.base_balance = 10
    portfolio.quote_balance = 0.0

    # price rises -> new peak
    assert not exceed_max_drawdown(portfolio, 120.0)
    assert portfolio.peak_value == pytest.approx(1200.0)

    # small drop from new peak (5%) should not trigger
    assert not exceed_max_drawdown(portfolio, 114.0)

