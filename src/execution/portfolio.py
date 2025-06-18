from dataclasses import dataclass
from typing import Dict, Optional
from src.config import settings
from .simulation_client import simulator


@dataclass
class Portfolio:
    """Trading portfolio tracker with capital management."""

    base_symbol: str = "SOL"
    quote_symbol: str = "USDC"
    base_balance: float = 0.0
    quote_balance: float = 0.0
    peak_value: float = 0.0  # highest USD value observed
    
    # Capital management
    trading_capital: float = 0.0
    allocated_capital: float = 0.0
    
    def __post_init__(self) -> None:
        """Initialize portfolio with trading capital configuration."""
        # Set trading capital from config
        self.trading_capital = settings.trading_capital_sol

        # Initialize balances only if not provided
        if self.quote_balance == 0.0:
            self.quote_balance = self.trading_capital
        if self.peak_value == 0.0:
            self.peak_value = self.quote_balance

    def update_from_trade(self, side: str, quantity: float, price: float, fee: float = 0.0) -> None:
        """Update balances after executing a trade."""
        if settings.simulation_mode and simulator:
            # En modo simulación, usar el simulador
            result = simulator.simulate_trade(side, quantity, price)
            if result["success"]:
                # Actualizar balance local desde simulador
                self.quote_balance = result["new_balance_sol"]
                if result.get("position"):
                    self.base_balance = result["position"]["amount_sol"]
                else:
                    self.base_balance = 0.0
            return
        
        # Modo real - actualizar balances normalmente
        if side.upper() == "BUY":
            self.base_balance += quantity
            self.quote_balance -= quantity * price + fee
        elif side.upper() == "SELL":
            self.base_balance -= quantity
            self.quote_balance += quantity * price - fee

    @property
    def value_usd(self) -> float:
        """Return portfolio value in USD based on quote balance only."""
        return self.quote_balance

    def total_value(self, price: float) -> float:
        """Return portfolio value including base asset priced in USD."""
        return self.quote_balance + self.base_balance * price

    def get_position_value_sol(self) -> float:
        """Get current position value in SOL terms."""
        return self.base_balance
    
    def get_available_capital(self) -> float:
        """Get available capital for new positions."""
        used_capital = self.get_position_value_sol()
        return max(0, self.trading_capital - used_capital)
    
    def calculate_max_trade_size(self, max_position_pct: float = None) -> float:
        """Calculate maximum trade size based on capital limits."""
        if max_position_pct is None:
            max_position_pct = settings.max_position_size_pct
        
        max_position_sol = self.trading_capital * (max_position_pct / 100.0)
        current_position = abs(self.base_balance)
        
        return max(0, max_position_sol - current_position)
    
    def validate_trade_size(self, trade_size_sol: float) -> Dict[str, any]:
        """Validate if trade size is within capital limits."""
        current_position = abs(self.base_balance)
        new_position = current_position + abs(trade_size_sol)
        
        if new_position > self.trading_capital:
            return {
                "valid": False,
                "reason": f"Exceeds trading capital ({new_position:.4f} > {self.trading_capital:.4f} SOL)",
                "max_allowed": self.trading_capital - current_position
            }
        
        max_position = self.trading_capital * (settings.max_position_size_pct / 100.0)
        if new_position > max_position:
            return {
                "valid": False,
                "reason": f"Exceeds max position size ({new_position:.4f} > {max_position:.4f} SOL)",
                "max_allowed": max_position - current_position
            }
        
        return {"valid": True, "reason": "Trade size valid"}

    def as_dict(self) -> Dict[str, float]:
        base_dict = {
            self.base_symbol: self.base_balance,
            self.quote_symbol: self.quote_balance,
            "trading_capital": self.trading_capital,
            "position_value_sol": self.get_position_value_sol(),
            "available_capital": self.get_available_capital(),
            "capital_utilization_pct": (self.get_position_value_sol() / self.trading_capital * 100) if self.trading_capital > 0 else 0
        }
        
        # Agregar información de simulación si está activa
        if settings.simulation_mode and simulator:
            sim_status = simulator.get_portfolio_status()
            base_dict.update({
                "simulation_mode": True,
                "realized_pnl": sim_status["realized_pnl"],
                "unrealized_pnl": sim_status["unrealized_pnl"],
                "total_pnl": sim_status["total_pnl"],
                "total_return_pct": sim_status["total_return_pct"],
                "total_trades": sim_status["total_trades"],
                "total_fees_paid": sim_status["total_fees_paid"]
            })
        else:
            base_dict["simulation_mode"] = False
            
        return base_dict
