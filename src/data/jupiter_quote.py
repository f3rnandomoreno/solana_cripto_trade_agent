import aiohttp
from typing import Optional

JUPITER_PRICE_URL = "https://api.jup.ag/price/v2?ids=So11111111111111111111111111111111111111112"

async def fetch_sol_price() -> Optional[float]:
    async with aiohttp.ClientSession() as session:
        async with session.get(JUPITER_PRICE_URL) as resp:
            if resp.status != 200:
                return None
            data = await resp.json()
            try:
                return float(data["data"]["So11111111111111111111111111111111111111112"]["price"])
            except Exception:
                return None
