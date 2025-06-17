import argparse
import asyncio
from pathlib import Path

from src.bot import TradingBot
from src.utils.backtest import load_prices_csv, run_backtest


async def run_bot(args: argparse.Namespace) -> None:
    bot = TradingBot(use_mock=args.mock)
    await bot.run(steps=args.steps, interval=args.interval)


def run_backtest_cmd(args: argparse.Namespace) -> None:
    prices = load_prices_csv(Path(args.csv))
    result = run_backtest(prices)
    print(f"returns={result.returns:.2f} trades={result.trades}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Solana trading bot CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    trade = sub.add_parser("trade", help="Run trading bot")
    trade.add_argument("--steps", type=int, default=10)
    trade.add_argument("--interval", type=float, default=1.0)
    trade.add_argument("--mock", action="store_true")

    back = sub.add_parser("backtest", help="Run backtest from CSV")
    back.add_argument("csv")

    return parser.parse_args()


async def main() -> None:
    args = parse_args()
    if args.cmd == "trade":
        await run_bot(args)
    else:
        run_backtest_cmd(args)


if __name__ == "__main__":
    asyncio.run(main())
