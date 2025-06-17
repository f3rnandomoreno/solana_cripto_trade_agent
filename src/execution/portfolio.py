from dataclasses import dataclass
from typing import Dict, Optional
from src.config import settings


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
        
        # Initialize with configured trading capital (not entire wallet)
        self.quote_balance = self.trading_capital
        self.peak_value = self.trading_capital

    def update_from_trade(self, side: str, quantity: float, price: float, fee: float = 0.0) -> None:
        """Update balances after executing a trade."""
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
        return {
            self.base_symbol: self.base_balance,
            self.quote_symbol: self.quote_balance,
            "trading_capital": self.trading_capital,
            "position_value_sol": self.get_position_value_sol(),
            "available_capital": self.get_available_capital(),
            "capital_utilization_pct": (self.get_position_value_sol() / self.trading_capital * 100) if self.trading_capital > 0 else 0
        }
