import asyncio
from typing import Optional

from .jupiter_quote import fetch_sol_price
from .pyth_feed import fetch_pyth_sol_price


class AggregatedPriceFeed:
    """Retrieve SOL price using both Pyth and Jupiter as sources."""

    async def get_price(self) -> Optional[float]:
        """Return the average price from available feeds."""
        try:
            pyth_task = asyncio.create_task(fetch_pyth_sol_price())
            jupiter_task = asyncio.create_task(fetch_sol_price())
            pyth_price, jupiter_price = await asyncio.gather(pyth_task, jupiter_task)
        except Exception:
            return None

        if pyth_price and jupiter_price:
            return (pyth_price + jupiter_price) / 2
        return pyth_price or jupiter_price
