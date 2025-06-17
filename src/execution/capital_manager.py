"""
Trading capital management to control investment amounts and risk.
"""

from dataclasses import dataclass
from typing import Dict, Optional
from solders.keypair import Keypair
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Confirmed
from src.config import settings


@dataclass
class CapitalStatus:
    """Status of trading capital allocation."""
    total_wallet_balance: float
    trading_capital: float
    available_for_trading: float
    current_position_value: float
    reserve_balance: float
    position_size_pct: float
    can_trade: bool
    reason: str = ""


class TradingCapitalManager:
    """
    Manages trading capital allocation and position sizing.
    Ensures the bot only trades with allocated capital, not entire wallet.
    """
    
    def __init__(self, keypair: Keypair, rpc_client: AsyncClient):
        self.keypair = keypair
        self.client = rpc_client
        self.trading_capital = settings.trading_capital_sol
        self.max_position_size_pct = settings.max_position_size_pct
        self.reserve_balance = settings.reserve_balance_sol
        
    async def get_capital_status(self, current_sol_position: float = 0.0, current_price: float = 0.0) -> CapitalStatus:
        """
        Get current capital allocation status.
        
        Args:
            current_sol_position: Current SOL position held by trading strategy
            current_price: Current SOL price in USD
        """
        try:
            # Get actual wallet balance
            response = await self.client.get_balance(self.keypair.pubkey(), commitment=Confirmed)
            total_balance = response.value / 1e9  # Convert lamports to SOL
            
            # Calculate current position value in SOL equivalent
            current_position_value = current_sol_position
            
            # Available capital for new positions
            used_capital = current_position_value
            available_capital = max(0, self.trading_capital - used_capital)
            
            # Check if we can trade
            can_trade = True
            reason = "Ready to trade"
            
            # Safety checks
            if total_balance < self.reserve_balance:
                can_trade = False
                reason = f"Insufficient balance for fees (need {self.reserve_balance} SOL)"
            elif available_capital <= 0:
                can_trade = False
                reason = "Trading capital fully allocated"
            elif total_balance < (self.trading_capital + self.reserve_balance):
                can_trade = False
                reason = f"Insufficient wallet balance (need {self.trading_capital + self.reserve_balance} SOL total)"
            
            # Calculate position size percentage
            position_size_pct = (used_capital / self.trading_capital * 100) if self.trading_capital > 0 else 0
            
            return CapitalStatus(
                total_wallet_balance=total_balance,
                trading_capital=self.trading_capital,
                available_for_trading=available_capital,
                current_position_value=current_position_value,
                reserve_balance=self.reserve_balance,
                position_size_pct=position_size_pct,
                can_trade=can_trade,
                reason=reason
            )
            
        except Exception as e:
            return CapitalStatus(
                total_wallet_balance=0.0,
                trading_capital=self.trading_capital,
                available_for_trading=0.0,
                current_position_value=0.0,
                reserve_balance=self.reserve_balance,
                position_size_pct=0.0,
                can_trade=False,
                reason=f"Error checking balance: {e}"
            )
    
    def calculate_position_size(self, signal_strength: float = 1.0) -> float:
        """
        Calculate position size based on available capital and signal strength.
        
        Args:
            signal_strength: Strength of trading signal (0.0 to 1.0)
            
        Returns:
            Position size in SOL
        """
        # Base position size as percentage of trading capital
        base_position_pct = min(self.max_position_size_pct, 100.0) / 100.0
        
        # Adjust by signal strength
        adjusted_position_pct = base_position_pct * max(0.0, min(1.0, signal_strength))
        
        # Calculate position size in SOL
        position_size = self.trading_capital * adjusted_position_pct
        
        return position_size
    
    def validate_trade_size(self, trade_size_sol: float, current_position: float = 0.0) -> Dict[str, any]:
        """
        Validate if a trade size is within capital limits.
        
        Args:
            trade_size_sol: Proposed trade size in SOL
            current_position: Current SOL position
            
        Returns:
            Dict with validation result
        """
        # Calculate what position would be after trade
        new_position = abs(current_position + trade_size_sol)
        
        # Check against trading capital
        if new_position > self.trading_capital:
            return {
                "valid": False,
                "reason": f"Trade would exceed trading capital ({new_position:.4f} > {self.trading_capital:.4f} SOL)",
                "max_allowed": self.trading_capital - abs(current_position),
                "suggested_size": max(0, self.trading_capital - abs(current_position))
            }
        
        # Check against max position size
        max_allowed = self.trading_capital * (self.max_position_size_pct / 100.0)
        if new_position > max_allowed:
            return {
                "valid": False,
                "reason": f"Trade would exceed max position size ({new_position:.4f} > {max_allowed:.4f} SOL)",
                "max_allowed": max_allowed - abs(current_position),
                "suggested_size": max(0, max_allowed - abs(current_position))
            }
        
        return {
            "valid": True,
            "reason": "Trade size is valid",
            "max_allowed": max_allowed,
            "suggested_size": trade_size_sol
        }
    
    def get_capital_summary(self) -> Dict[str, float]:
        """Get summary of capital configuration."""
        return {
            "trading_capital_sol": self.trading_capital,
            "max_position_size_pct": self.max_position_size_pct,
            "max_position_size_sol": self.trading_capital * (self.max_position_size_pct / 100.0),
            "reserve_balance_sol": self.reserve_balance,
            "min_wallet_balance_needed": self.trading_capital + self.reserve_balance
        }