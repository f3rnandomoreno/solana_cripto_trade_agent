"""Simple back-testing helper for the strategy."""

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List

from src.strategy.simple_strategy import generate_signal
from src.execution.portfolio import Portfolio


@dataclass
class BacktestResult:
    returns: float
    trades: int


def run_backtest(price_series: Iterable[float], starting_cash: float = 1000.0) -> BacktestResult:
    prices: List[float] = list(price_series)
    portfolio = Portfolio(quote_balance=starting_cash)
    trades = 0

    for i in range(50, len(prices)):
        window = prices[: i + 1]
        signal = generate_signal(window)
        price = prices[i]
        qty = 1  # fixed 1 SOL for demo
        if signal == "BUY" and portfolio.quote_balance >= price:
            portfolio.update_from_trade("BUY", qty, price)
            trades += 1
        elif signal == "SELL" and portfolio.base_balance >= qty:
            portfolio.update_from_trade("SELL", qty, price)
            trades += 1

    return BacktestResult(returns=portfolio.quote_balance - starting_cash, trades=trades)


def export_report(result: BacktestResult, path: Path) -> None:
    with path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["returns", "trades"])
        writer.writerow([result.returns, result.trades])
