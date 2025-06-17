import aiohttp
from typing import Optional

JUPITER_PRICE_URL = "https://price.jup.ag/v4/price?ids=SOL"

async def fetch_sol_price() -> Optional[float]:
    async with aiohttp.ClientSession() as session:
        async with session.get(JUPITER_PRICE_URL) as resp:
            if resp.status != 200:
                return None
            data = await resp.json()
            try:
                return data["data"]["SOL"]["price"]
            except Exception:
                return None
