import asyncio
from rich import print
from src.data.jupiter_quote import fetch_sol_price

async def main():
    price = await fetch_sol_price()
    if price is not None:
        print(f"SOL price: {price} USD")
    else:
        print("Failed to fetch price")

if __name__ == "__main__":
    asyncio.run(main())
