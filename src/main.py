import asyncio
from rich import print

from src.data.jupiter_quote import fetch_sol_price
from src.data.pyth_feed import fetch_pyth_sol_price

async def main():
    jup_price = await fetch_sol_price()
    pyth_price = await fetch_pyth_sol_price()

    if jup_price is not None:
        print(f"[green]Jupiter price:[/] {jup_price} USD")
    else:
        print("[red]Failed to fetch Jupiter price[/]")

    if pyth_price is not None:
        print(f"[green]Pyth price:[/] {pyth_price} USD")
    else:
        print("[red]Failed to fetch Pyth price[/]")

if __name__ == "__main__":
    asyncio.run(main())
