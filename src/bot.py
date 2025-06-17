import asyncio
from typing import List, Optional

from src.data.mock_feed import MockPriceFeed
from src.data.aggregated_feed import AggregatedPriceFeed
from src.strategy.simple_strategy import generate_signal
from src.execution.portfolio import Portfolio
from src.execution.jupiter_client import request_quote
from src.utils.logger import setup_logger, log_trade
from src.strategy.risk import exceed_max_drawdown


class TradingBot:
    """Orchestrates price feed, strategy and portfolio."""

    def __init__(self, starting_cash: float = None, use_mock: bool = False):
        self.feed = MockPriceFeed() if use_mock else AggregatedPriceFeed()
        
        # Use configured trading capital instead of arbitrary starting_cash
        if starting_cash is None:
            from src.config import settings
            starting_cash = settings.trading_capital_sol
        
        self.portfolio = Portfolio()  # Will auto-initialize with trading capital
        self.logger = setup_logger()
        self.prices: List[float] = []
        
        # Log trading capital configuration
        self.logger.info(f"Trading Capital Configuration:")
        self.logger.info(f"  Trading Capital: {self.portfolio.trading_capital:.4f} SOL")
        self.logger.info(f"  Max Position: {settings.max_position_size_pct}% = {self.portfolio.calculate_max_trade_size():.4f} SOL")
        self.logger.info(f"  Reserve Balance: {settings.reserve_balance_sol:.4f} SOL")

    async def step(self) -> None:
        price = await self.feed.get_price()
        if price is None:
            self.logger.warning("Price feed unavailable")
            return
        self.prices.append(price)
        self.logger.info(f"Price: {price} USD")

        # Check risk limits before generating new signal
        if exceed_max_drawdown(self.portfolio, price) and self.portfolio.base_balance > 0:
            self.logger.warning("Max drawdown exceeded - liquidating position")
            self.portfolio.update_from_trade("SELL", self.portfolio.base_balance, price)
            log_trade({"side": "STOP_SELL", "price": price})
            self.logger.info(f"Balances: {self.portfolio.as_dict()}")
            return

        signal = generate_signal(self.prices)

        if signal == "BUY":
            # Calculate position size based on available capital
            max_trade_size = self.portfolio.calculate_max_trade_size()
            available_capital = self.portfolio.get_available_capital()
            
            # Calculate actual trade size (in SOL terms, using price to convert)
            trade_size_sol = min(max_trade_size, available_capital)
            
            # Validate trade size
            validation = self.portfolio.validate_trade_size(trade_size_sol)
            
            if validation["valid"] and trade_size_sol > 0 and self.portfolio.quote_balance >= trade_size_sol * price:
                self.portfolio.update_from_trade("BUY", trade_size_sol, price)
                log_trade({"side": "BUY", "price": price, "quantity": trade_size_sol})
                
                # Request quote for actual trade amount
                amount_lamports = int(trade_size_sol * 1_000_000_000)  # Convert SOL to lamports
                quote = await request_quote(
                    input_mint="So11111111111111111111111111111111111111112",
                    output_mint="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
                    amount=amount_lamports,
                )
                if quote:
                    self.logger.info(f"Quote outAmount: {quote.get('data')[0]['outAmount']}")
                
                self.logger.info(f"Executed BUY {trade_size_sol:.4f} SOL @ ${price}")
            else:
                reason = validation.get("reason", "Insufficient capital")
                self.logger.info(f"BUY signal but cannot trade: {reason}")
                
        elif signal == "SELL" and self.portfolio.base_balance > 0:
            # Sell current position (or part of it)
            trade_size_sol = self.portfolio.base_balance
            
            self.portfolio.update_from_trade("SELL", trade_size_sol, price)
            log_trade({"side": "SELL", "price": price, "quantity": trade_size_sol})
            
            # Request quote for actual trade amount
            amount_lamports = int(trade_size_sol * 1_000_000_000)  # Convert SOL to lamports
            quote = await request_quote(
                input_mint="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
                output_mint="So11111111111111111111111111111111111111112",
                amount=amount_lamports,
            )
            if quote:
                self.logger.info(f"Quote outAmount: {quote.get('data')[0]['outAmount']}")
            
            self.logger.info(f"Executed SELL {trade_size_sol:.4f} SOL @ ${price}")
        else:
            self.logger.info("No trade executed")

        self.logger.info(f"Balances: {self.portfolio.as_dict()}")

    async def run(self, steps: int = 50, interval: float = 1.0) -> None:
        for _ in range(steps):
            await self.step()
            await asyncio.sleep(interval)
