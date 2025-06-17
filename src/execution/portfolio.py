from dataclasses import dataclass
from typing import Dict


@dataclass
class Portfolio:
    """Simple in-memory portfolio tracker."""

    base_symbol: str = "SOL"
    quote_symbol: str = "USDC"
    base_balance: float = 0.0
    quote_balance: float = 0.0
    peak_value: float = 0.0  # highest USD value observed

    def __post_init__(self) -> None:
        """Initialize peak value based on starting quote balance."""
        self.peak_value = self.quote_balance

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

    def as_dict(self) -> Dict[str, float]:
        return {
            self.base_symbol: self.base_balance,
            self.quote_symbol: self.quote_balance,
        }
