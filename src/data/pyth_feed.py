from typing import Optional
from pythclient.hermes import HermesClient

# Pyth price feed ID for SOL/USD on mainnet
SOL_FEED_ID = "J83mCTdkBStKF7yD1ewtg7d6cgt1YG11E9cujiFFJmD9"  # default feed id

async def fetch_pyth_sol_price() -> Optional[float]:
    """Fetch SOL/USD price from Pyth using Hermes HTTP endpoint."""
    client = HermesClient([SOL_FEED_ID])
    try:
        prices = await client.get_all_prices(version=2)
        feed = prices.get(SOL_FEED_ID)
        if not feed:
            return None
        price = feed["price"].price * (10 ** feed["price"].expo)
        return float(price)
    except Exception:
        return None
