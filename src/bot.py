import asyncio
from typing import List

from src.data.mock_feed import MockPriceFeed
from src.strategy.simple_strategy import generate_signal
from src.execution.portfolio import Portfolio
from src.utils.logger import setup_logger, log_trade


class TradingBot:
    """Orchestrates price feed, strategy and portfolio."""

    def __init__(self, starting_cash: float = 1000.0):
        self.feed = MockPriceFeed()
        self.portfolio = Portfolio(quote_balance=starting_cash)
        self.logger = setup_logger()
        self.prices: List[float] = []

    async def step(self) -> None:
        price = await self.feed.get_price()
        self.prices.append(price)
        self.logger.info(f"Price: {price} USD")
        signal = generate_signal(self.prices)

        if signal == "BUY" and self.portfolio.quote_balance >= price:
            self.portfolio.update_from_trade("BUY", 1, price)
            log_trade({"side": "BUY", "price": price})
            self.logger.info(f"Executed BUY @ {price}")
        elif signal == "SELL" and self.portfolio.base_balance >= 1:
            self.portfolio.update_from_trade("SELL", 1, price)
            log_trade({"side": "SELL", "price": price})
            self.logger.info(f"Executed SELL @ {price}")
        else:
            self.logger.info("No trade executed")

        self.logger.info(f"Balances: {self.portfolio.as_dict()}")

    async def run(self, steps: int = 50, interval: float = 1.0) -> None:
        for _ in range(steps):
            await self.step()
            await asyncio.sleep(interval)
