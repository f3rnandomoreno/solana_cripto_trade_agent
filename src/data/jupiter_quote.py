import aiohttp
from typing import Optional

JUPITER_PRICE_URL = "https://api.jup.ag/price/v2?ids=So11111111111111111111111111111111111111112"

async def fetch_sol_price() -> Optional[float]:
    """Return the current SOL price reported by Jupiter.

    If the request fails (for instance due to missing network access) ``None``
    is returned instead of raising an exception.
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(JUPITER_PRICE_URL) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()
                return float(
                    data["data"]["So11111111111111111111111111111111111111112"]["price"]
                )
    except Exception:
        # Network might be unavailable in certain environments.
        return None
