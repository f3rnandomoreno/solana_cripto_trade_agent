import aiohttp
from typing import Optional, Dict
from ..config import settings
from .simulation_client import simulator


API_URL = "https://quote-api.jup.ag/v6/quote"

async def request_quote(
    input_mint: str,
    output_mint: str,
    amount: int,
    slippage_bps: int = 50,
) -> Optional[Dict]:
    """Fetch a swap quote from the Jupiter aggregator.

    Returns the JSON response with route information or ``None`` if the
    request fails (for example due to missing network access).
    """
    params = {
        "inputMint": input_mint,
        "outputMint": output_mint,
        "amount": amount,
        "slippageBps": slippage_bps,
    }
    headers = {}
    if settings.jupiter_api_key:
        headers["apikey"] = settings.jupiter_api_key
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(API_URL, params=params, headers=headers) as resp:
                if resp.status != 200:
                    return None
                return await resp.json()
    except Exception:
        # Network access might not be available in some environments.
        return None


async def execute_swap(quote: Dict) -> bool:
    """Placeholder to sign and send the transaction built from a quote."""
    # The real implementation would use the Jupiter SDK and solana-py to
    # build and send the transaction. This is left as a stub for now.
    return False


async def execute_trade(side: str, amount_sol: float, price: float) -> bool:
    """Execute a BUY or SELL trade either simulated or on-chain."""
    if settings.simulation_mode and simulator:
        result = simulator.simulate_trade(side.upper(), amount_sol, price)
        return result.get("success", False)

    amount_lamports = int(amount_sol * 1_000_000_000)
    if side.upper() == "BUY":
        input_mint = settings.quote_mint
        output_mint = settings.base_mint
    else:
        input_mint = settings.base_mint
        output_mint = settings.quote_mint

    quote = await request_quote(
        input_mint=input_mint,
        output_mint=output_mint,
        amount=amount_lamports,
        slippage_bps=settings.slippage_bps,
    )
    if not quote:
        return False
    return await execute_swap(quote)
