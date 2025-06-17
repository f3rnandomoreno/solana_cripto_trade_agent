import random

class MockPriceFeed:
    """Simple random walk price generator for offline testing."""

    def __init__(self, start_price: float = 100.0, volatility: float = 0.02):
        self.price = start_price
        self.volatility = volatility

    async def get_price(self) -> float:
        """Return next price tick."""
        change = random.uniform(-self.volatility, self.volatility)
        self.price *= 1 + change
        return round(self.price, 4)
