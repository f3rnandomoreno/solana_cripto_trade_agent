import asyncio
from typing import List, Optional

from src.data.aggregated_feed import AggregatedPriceFeed
from src.data.data_manager import data_manager
from src.strategy.simple_strategy import generate_signal
from src.strategy.indicators import compute_indicators
from src.execution.portfolio import Portfolio
from src.execution.jupiter_client import execute_trade
from src.execution.simulation_client import simulator
from src.utils.logger import setup_logger, log_trade
from src.strategy.risk import exceed_max_drawdown
from src.config import settings


class TradingBot:
    """Orchestrates price feed, strategy and portfolio."""

    def __init__(self, starting_cash: float = None):
        # Siempre usar feeds reales - no se permite mock
        self.feed = AggregatedPriceFeed()
        
        # Use configured trading capital instead of arbitrary starting_cash
        if starting_cash is None:
            starting_cash = settings.trading_capital_sol
        
        self.portfolio = Portfolio()  # Will auto-initialize with trading capital
        self.logger = setup_logger()
        self.prices: List[float] = []
        
        # Log trading capital configuration
        if settings.simulation_mode:
            self.logger.info(f"🎮 MODO SIMULACIÓN ACTIVADO - NO SE EJECUTARÁN TRANSACCIONES REALES")
            self.logger.info(f"💰 Balance inicial simulado: {settings.simulation_initial_balance:.4f} SOL")
        else:
            self.logger.info(f"⚠️  MODO REAL - SE EJECUTARÁN TRANSACCIONES REALES")
        
        self.logger.info(f"Trading Capital Configuration:")
        self.logger.info(f"  Trading Capital: {self.portfolio.trading_capital:.4f} SOL")
        self.logger.info(f"  Max Position: {settings.max_position_size_pct}% = {self.portfolio.calculate_max_trade_size():.4f} SOL")
        self.logger.info(f"  Reserve Balance: {settings.reserve_balance_sol:.4f} SOL")

    async def step(self) -> None:
        price = await self.feed.get_price()
        if price is None:
            self.logger.warning("Price feed unavailable")
            return
        
        # Guardar precio en base de datos (siempre de fuente real)
        data_manager.save_price_data(price, "aggregated")

        self.prices.append(price)
        self.logger.info(f"Price: {price} USD")

        indicators = compute_indicators(self.prices)
        if indicators:
            self.logger.info(
                "Indicadores => EMA12:{ema12:.2f} EMA50:{ema50:.2f} SMA20:{sma20:.2f} RSI:{rsi:.2f} BB:[{lower_bb:.2f}, {upper_bb:.2f}]".format(**indicators)
            )

        # Actualizar precio actual en simulador
        if settings.simulation_mode and simulator:
            simulator.update_current_price(price)

        # Check risk limits before generating new signal
        if exceed_max_drawdown(self.portfolio, price) and self.portfolio.base_balance > 0:
            self.logger.warning("Max drawdown exceeded - liquidating position")
            self.portfolio.update_from_trade("SELL", self.portfolio.base_balance, price)
            log_trade({"side": "STOP_SELL", "price": price})
            self.logger.info(f"Balances: {self.portfolio.as_dict()}")
            return

        signal = generate_signal(self.prices)
        self.logger.info(f"Previsión de acción: {signal}")

        if signal == "BUY":
            # Calculate position size based on available capital
            max_trade_size = self.portfolio.calculate_max_trade_size()
            available_capital = self.portfolio.get_available_capital()
            
            # Calculate actual trade size (in SOL terms, using price to convert)
            trade_size_sol = min(max_trade_size, available_capital)
            
            # Validate trade size
            validation = self.portfolio.validate_trade_size(trade_size_sol)
            
            if validation["valid"] and trade_size_sol > 0 and self.portfolio.quote_balance >= trade_size_sol * price:
                # Capturar valor del portfolio antes del trade
                portfolio_before = self.portfolio.as_dict()
                portfolio_value_before = portfolio_before.get("trading_capital", 0)
                
                self.portfolio.update_from_trade("BUY", trade_size_sol, price)
                log_trade({"side": "BUY", "price": price, "quantity": trade_size_sol})
                
                # Capturar valor del portfolio después del trade
                portfolio_after = self.portfolio.as_dict()
                portfolio_value_after = portfolio_after.get("trading_capital", 0)
                
                # Guardar trade en base de datos
                data_manager.save_trade_data(
                    side="BUY",
                    amount_sol=trade_size_sol,
                    price=price,
                    value_usd=trade_size_sol * price,
                    fees_sol=0.0,  # Simplificado por ahora
                    simulation=settings.simulation_mode,
                    portfolio_value_before=portfolio_value_before,
                    portfolio_value_after=portfolio_value_after
                )
                
                if settings.simulation_mode:
                    self.logger.info(f"🎮 SIMULADO: BUY {trade_size_sol:.4f} SOL @ ${price}")
                else:
                    success = await execute_trade("BUY", trade_size_sol, price)
                    if success:
                        self.logger.info(f"⚠️  REAL: BUY {trade_size_sol:.4f} SOL @ ${price}")
                    else:
                        self.logger.warning("Real BUY failed")
            else:
                reason = validation.get("reason", "Insufficient capital")
                self.logger.info(f"BUY signal but cannot trade: {reason}")
                
        elif signal == "SELL" and self.portfolio.base_balance > 0:
            # Sell current position (or part of it)
            trade_size_sol = self.portfolio.base_balance
            
            # Capturar valor del portfolio antes del trade
            portfolio_before = self.portfolio.as_dict()
            portfolio_value_before = portfolio_before.get("trading_capital", 0)
            
            self.portfolio.update_from_trade("SELL", trade_size_sol, price)
            log_trade({"side": "SELL", "price": price, "quantity": trade_size_sol})
            
            # Capturar valor del portfolio después del trade
            portfolio_after = self.portfolio.as_dict()
            portfolio_value_after = portfolio_after.get("trading_capital", 0)
            
            # Guardar trade en base de datos
            data_manager.save_trade_data(
                side="SELL",
                amount_sol=trade_size_sol,
                price=price,
                value_usd=trade_size_sol * price,
                fees_sol=0.0,  # Simplificado por ahora
                simulation=settings.simulation_mode,
                portfolio_value_before=portfolio_value_before,
                portfolio_value_after=portfolio_value_after
            )
            
            if settings.simulation_mode:
                self.logger.info(f"🎮 SIMULADO: SELL {trade_size_sol:.4f} SOL @ ${price}")
            else:
                success = await execute_trade("SELL", trade_size_sol, price)
                if success:
                    self.logger.info(f"⚠️  REAL: SELL {trade_size_sol:.4f} SOL @ ${price}")
                else:
                    self.logger.warning("Real SELL failed")
        else:
            self.logger.info("No trade executed")

        # Guardar snapshot del portfolio
        portfolio_data = self.portfolio.as_dict()
        data_manager.save_portfolio_snapshot(
            sol_balance=portfolio_data.get("SOL", 0),
            usd_balance=portfolio_data.get("USDC", 0),
            total_value_usd=price * portfolio_data.get("SOL", 0) + portfolio_data.get("USDC", 0),
            realized_pnl=portfolio_data.get("realized_pnl", 0),
            unrealized_pnl=portfolio_data.get("unrealized_pnl", 0),
            simulation=settings.simulation_mode,
            metadata={"current_price": price}
        )
        
        self.logger.info(f"Balances: {portfolio_data}")
        self.logger.info(
            "Estado actual => SOL:{sol:.4f} USDC:{usdc:.2f} UnrealizedPnL:{upnl:.2f} RealizedPnL:{rpnl:.2f}".format(
                sol=portfolio_data.get("SOL", 0),
                usdc=portfolio_data.get("USDC", 0),
                upnl=portfolio_data.get("unrealized_pnl", 0),
                rpnl=portfolio_data.get("realized_pnl", 0),
            )
        )

    async def run(self, steps: int = 50, interval: float = 1.0) -> None:
        for _ in range(steps):
            await self.step()
            await asyncio.sleep(interval)
