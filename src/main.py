import asyncio
from rich import print

from src.data.jupiter_quote import fetch_sol_price
from src.data.pyth_feed import fetch_pyth_sol_price
from src.strategy.simple_strategy import generate_signal


async def gather_prices(count: int = 10, interval: float = 1.0):
    """Fetch SOL prices multiple times and return the list."""
    prices = []
    for _ in range(count):
        price = await fetch_sol_price()
        if price is not None:
            prices.append(price)
            print(f"[cyan]Jupiter price:[/] {price} USD")
        else:
            print("[red]Failed to fetch Jupiter price[/]")
        await asyncio.sleep(interval)
    return prices


async def main():
    prices = await gather_prices()
    pyth_price = await fetch_pyth_sol_price()
    if pyth_price is not None:
        print(f"[green]Latest Pyth price:[/] {pyth_price} USD")
    signal = generate_signal(prices)
    print(f"[bold yellow]Generated signal:[/] {signal}")


if __name__ == "__main__":
    asyncio.run(main())
