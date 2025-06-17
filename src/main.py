import asyncio
from src.bot import TradingBot


async def main():
    bot = TradingBot()
    await bot.run(steps=10, interval=1.0)


if __name__ == "__main__":
    asyncio.run(main())
