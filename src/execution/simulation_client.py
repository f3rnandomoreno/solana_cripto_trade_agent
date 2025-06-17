"""
Simulador de trading que no ejecuta transacciones reales.
Simula operaciones y tracking de P&L sin tocar la blockchain.
"""

import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import json
from ..config import settings


@dataclass
class SimulatedTrade:
    """Representa una operación simulada"""
    timestamp: float
    side: str  # "BUY" or "SELL"
    amount_sol: float
    price: float
    value_usd: float
    fees_sol: float = 0.0
    slippage_pct: float = 0.0
    

@dataclass
class SimulatedPosition:
    """Representa una posición simulada"""
    entry_timestamp: float
    entry_price: float
    amount_sol: float
    current_price: float = 0.0
    unrealized_pnl: float = 0.0
    
    def update_price(self, new_price: float):
        """Actualiza precio actual y P&L no realizado"""
        self.current_price = new_price
        self.unrealized_pnl = (new_price - self.entry_price) * self.amount_sol


class TradingSimulator:
    """
    Simulador de trading que NO ejecuta transacciones reales.
    Simula todas las operaciones con datos virtuales.
    """
    
    def __init__(self, initial_balance: float = None):
        self.initial_balance = initial_balance or settings.simulation_initial_balance
        self.sol_balance = self.initial_balance
        self.usd_balance = 0.0
        
        self.trades: List[SimulatedTrade] = []
        self.position: Optional[SimulatedPosition] = None
        
        self.total_fees_paid = 0.0
        self.realized_pnl = 0.0
        self.start_time = time.time()
        
        from src.utils.logger import setup_logger
        logger = setup_logger()
        logger.info(f"🎮 MODO SIMULACIÓN ACTIVADO")
        logger.info(f"💰 Balance inicial: {self.initial_balance:.4f} SOL")
        logger.warning(f"⚠️  NO SE EJECUTARÁN TRANSACCIONES REALES")
        
    def simulate_trade(self, side: str, amount_sol: float, price: float) -> Dict:
        """
        Simula una operación de trading SIN ejecutar transacciones reales.
        
        Args:
            side: "BUY" o "SELL"
            amount_sol: Cantidad en SOL
            price: Precio por SOL en USD
            
        Returns:
            Dict con resultado de la simulación
        """
        
        if not settings.simulation_mode:
            raise Exception("⚠️ NO SE PUEDE SIMULAR - Modo simulación desactivado")
            
        # Simular fees (0.25% típico)
        fee_rate = 0.0025
        fees_sol = amount_sol * fee_rate
        
        # Simular slippage (random entre 0.1% - 0.5%)
        import random
        slippage_pct = random.uniform(0.1, 0.5)
        
        if side == "BUY":
            return self._simulate_buy(amount_sol, price, fees_sol, slippage_pct)
        elif side == "SELL":
            return self._simulate_sell(amount_sol, price, fees_sol, slippage_pct)
        else:
            raise ValueError(f"Lado inválido: {side}")
    
    def _simulate_buy(self, amount_sol: float, price: float, fees_sol: float, slippage_pct: float) -> Dict:
        """Simula una compra"""
        
        # Verificar balance suficiente
        total_cost = amount_sol + fees_sol
        if self.sol_balance < total_cost:
            return {
                "success": False,
                "error": f"Balance insuficiente. Necesario: {total_cost:.4f} SOL, Disponible: {self.sol_balance:.4f} SOL",
                "simulation": True
            }
        
        # Aplicar slippage al precio (peor precio en compra)
        actual_price = price * (1 + slippage_pct / 100)
        value_usd = amount_sol * actual_price
        
        # Actualizar balances virtuales
        self.sol_balance -= total_cost
        self.usd_balance += value_usd
        self.total_fees_paid += fees_sol
        
        # Crear trade simulado
        trade = SimulatedTrade(
            timestamp=time.time(),
            side="BUY",
            amount_sol=amount_sol,
            price=actual_price,
            value_usd=value_usd,
            fees_sol=fees_sol,
            slippage_pct=slippage_pct
        )
        self.trades.append(trade)
        
        # Crear/actualizar posición
        if self.position is None:
            self.position = SimulatedPosition(
                entry_timestamp=trade.timestamp,
                entry_price=actual_price,
                amount_sol=amount_sol,
                current_price=actual_price
            )
        else:
            # Promedio ponderado si ya hay posición
            total_amount = self.position.amount_sol + amount_sol
            avg_price = ((self.position.entry_price * self.position.amount_sol) + 
                        (actual_price * amount_sol)) / total_amount
            
            self.position.amount_sol = total_amount
            self.position.entry_price = avg_price
            self.position.current_price = actual_price
        
        return {
            "success": True,
            "simulation": True,
            "trade": asdict(trade),
            "new_balance_sol": self.sol_balance,
            "new_balance_usd": self.usd_balance,
            "position": asdict(self.position) if self.position else None
        }
    
    def _simulate_sell(self, amount_sol: float, price: float, fees_sol: float, slippage_pct: float) -> Dict:
        """Simula una venta"""
        
        # Verificar que tengamos posición
        if self.position is None or self.position.amount_sol < amount_sol:
            available = self.position.amount_sol if self.position else 0.0
            return {
                "success": False,
                "error": f"Posición insuficiente. Necesario: {amount_sol:.4f} SOL, Disponible: {available:.4f} SOL",
                "simulation": True
            }
        
        # Aplicar slippage al precio (peor precio en venta)
        actual_price = price * (1 - slippage_pct / 100)
        value_usd = amount_sol * actual_price
        
        # Calcular P&L realizado
        cost_basis = self.position.entry_price * amount_sol
        pnl = value_usd - cost_basis
        self.realized_pnl += pnl
        
        # Actualizar balances virtuales
        self.sol_balance += (amount_sol - fees_sol)  # Recibimos SOL menos fees
        self.usd_balance -= value_usd  # Perdemos el valor USD
        self.total_fees_paid += fees_sol
        
        # Crear trade simulado
        trade = SimulatedTrade(
            timestamp=time.time(),
            side="SELL",
            amount_sol=amount_sol,
            price=actual_price,
            value_usd=value_usd,
            fees_sol=fees_sol,
            slippage_pct=slippage_pct
        )
        self.trades.append(trade)
        
        # Actualizar posición
        self.position.amount_sol -= amount_sol
        if self.position.amount_sol <= 0.0001:  # Posición cerrada
            self.position = None
        
        return {
            "success": True,
            "simulation": True,
            "trade": asdict(trade),
            "realized_pnl": pnl,
            "new_balance_sol": self.sol_balance,
            "new_balance_usd": self.usd_balance,
            "position": asdict(self.position) if self.position else None
        }
    
    def update_current_price(self, price: float):
        """Actualiza precio actual para P&L no realizado"""
        if self.position:
            self.position.update_price(price)
    
    def get_portfolio_status(self) -> Dict:
        """Obtiene status actual del portfolio simulado"""
        
        total_value_sol = self.sol_balance
        if self.position and self.position.current_price > 0:
            total_value_sol += self.position.amount_sol
        
        unrealized_pnl = self.position.unrealized_pnl if self.position else 0.0
        total_pnl = self.realized_pnl + unrealized_pnl
        total_return_pct = (total_pnl / (self.initial_balance * (self.position.entry_price if self.position else 1))) * 100
        
        return {
            "simulation_mode": True,
            "initial_balance": self.initial_balance,
            "sol_balance": self.sol_balance,
            "usd_balance": self.usd_balance,
            "position": asdict(self.position) if self.position else None,
            "total_value_sol": total_value_sol,
            "realized_pnl": self.realized_pnl,
            "unrealized_pnl": unrealized_pnl,
            "total_pnl": total_pnl,
            "total_return_pct": total_return_pct,
            "total_fees_paid": self.total_fees_paid,
            "total_trades": len(self.trades),
            "runtime_hours": (time.time() - self.start_time) / 3600
        }
    
    def get_trade_history(self) -> List[Dict]:
        """Obtiene historial de trades simulados"""
        return [asdict(trade) for trade in self.trades]
    
    def export_simulation_log(self, filename: str = None) -> str:
        """Exporta log detallado de la simulación"""
        
        if filename is None:
            filename = f"simulation_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        log_data = {
            "simulation_summary": self.get_portfolio_status(),
            "trade_history": self.get_trade_history(),
            "settings": {
                "initial_balance": self.initial_balance,
                "simulation_mode": settings.simulation_mode
            }
        }
        
        with open(filename, 'w') as f:
            json.dump(log_data, f, indent=2)
        
        return filename


# Instancia global del simulador
simulator = TradingSimulator() if settings.simulation_mode else None