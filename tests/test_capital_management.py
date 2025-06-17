import pytest
import os
from src.execution.portfolio import Portfolio
from src.execution.capital_manager import TradingCapitalManager, CapitalStatus
from src.config import settings


def test_portfolio_capital_management():
    """Test portfolio capital management functionality."""
    
    print("\n🧪 TESTING CAPITAL MANAGEMENT")
    print("=" * 50)
    
    # Create portfolio with trading capital
    portfolio = Portfolio()
    
    print(f"Initial Portfolio Configuration:")
    print(f"  Trading Capital: {portfolio.trading_capital:.4f} SOL")
    print(f"  Quote Balance: {portfolio.quote_balance:.4f} SOL")
    print(f"  Max Position Size: {settings.max_position_size_pct}%")
    
    # Test capital calculations
    max_trade_size = portfolio.calculate_max_trade_size()
    available_capital = portfolio.get_available_capital()
    
    print(f"\nCapital Calculations:")
    print(f"  Max Trade Size: {max_trade_size:.4f} SOL")
    print(f"  Available Capital: {available_capital:.4f} SOL")
    
    # Test trade validation
    test_trade_sizes = [0.01, 0.05, 0.08, 0.1, 0.15]
    
    print(f"\nTrade Size Validation:")
    for trade_size in test_trade_sizes:
        validation = portfolio.validate_trade_size(trade_size)
        status = "✅" if validation["valid"] else "❌"
        print(f"  {trade_size:.3f} SOL: {status} {validation['reason']}")
    
    # Test position tracking
    print(f"\nTesting Position Tracking:")
    
    # Simulate a trade
    trade_size = 0.05
    price = 200.0
    
    print(f"  Before trade: {portfolio.as_dict()}")
    
    portfolio.update_from_trade("BUY", trade_size, price)
    
    print(f"  After BUY {trade_size} SOL @ ${price}: {portfolio.as_dict()}")
    
    # Test capital utilization
    utilization = portfolio.as_dict()["capital_utilization_pct"]
    expected_utilization = (trade_size / portfolio.trading_capital) * 100
    
    assert abs(utilization - expected_utilization) < 0.01, f"Capital utilization mismatch"
    
    print(f"✅ Capital management test passed!")


def test_trading_capital_configuration():
    """Test trading capital configuration from environment."""
    
    print(f"\n🔧 TESTING CAPITAL CONFIGURATION")
    print("=" * 50)
    
    print(f"Configuration from settings:")
    print(f"  TRADING_CAPITAL_SOL: {settings.trading_capital_sol}")
    print(f"  MAX_POSITION_SIZE_PCT: {settings.max_position_size_pct}")
    print(f"  RESERVE_BALANCE_SOL: {settings.reserve_balance_sol}")
    
    # Validate configuration makes sense
    assert settings.trading_capital_sol > 0, "Trading capital must be positive"
    assert settings.max_position_size_pct > 0 and settings.max_position_size_pct <= 100, "Position size must be 0-100%"
    assert settings.reserve_balance_sol >= 0, "Reserve balance must be non-negative"
    
    # Test that portfolio uses these settings
    portfolio = Portfolio()
    assert portfolio.trading_capital == settings.trading_capital_sol, "Portfolio should use configured trading capital"
    
    max_position_sol = portfolio.trading_capital * (settings.max_position_size_pct / 100.0)
    calculated_max = portfolio.calculate_max_trade_size()
    assert abs(calculated_max - max_position_sol) < 0.0001, "Max trade size calculation should match"
    
    print(f"✅ Configuration validation passed!")


def test_capital_safety_limits():
    """Test that capital management prevents over-allocation."""
    
    print(f"\n🛡️ TESTING SAFETY LIMITS")
    print("=" * 50)
    
    portfolio = Portfolio()
    
    # Try to make a trade larger than trading capital
    oversized_trade = portfolio.trading_capital + 0.01
    validation = portfolio.validate_trade_size(oversized_trade)
    
    print(f"Oversized trade validation:")
    print(f"  Trade size: {oversized_trade:.4f} SOL")
    print(f"  Valid: {validation['valid']}")
    print(f"  Reason: {validation['reason']}")
    
    assert not validation["valid"], "Oversized trades should be rejected"
    
    # Try to exceed max position size
    max_position_pct = settings.max_position_size_pct
    max_position_sol = portfolio.trading_capital * (max_position_pct / 100.0)
    oversized_position = max_position_sol + 0.001
    
    validation2 = portfolio.validate_trade_size(oversized_position)
    
    print(f"\nMax position size validation:")
    print(f"  Trade size: {oversized_position:.4f} SOL")
    print(f"  Max allowed: {max_position_sol:.4f} SOL")
    print(f"  Valid: {validation2['valid']}")
    print(f"  Reason: {validation2['reason']}")
    
    assert not validation2["valid"], "Trades exceeding max position should be rejected"
    
    print(f"✅ Safety limits test passed!")


def test_capital_management_with_real_config():
    """Test capital management with real configuration."""
    
    print(f"\n💼 TESTING WITH REAL CONFIG")
    print("=" * 50)
    
    # Show current configuration
    portfolio = Portfolio()
    capital_info = portfolio.as_dict()
    
    print(f"Current Configuration:")
    for key, value in capital_info.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.6f}")
        else:
            print(f"  {key}: {value}")
    
    # Calculate some realistic scenarios
    scenarios = [
        ("Conservative", 0.25),  # 25% of trading capital
        ("Moderate", 0.50),      # 50% of trading capital  
        ("Aggressive", 0.75),    # 75% of trading capital
    ]
    
    print(f"\nTrading Scenarios:")
    for name, pct in scenarios:
        trade_size = portfolio.trading_capital * pct
        validation = portfolio.validate_trade_size(trade_size)
        status = "✅" if validation["valid"] else "❌"
        print(f"  {name} ({pct*100}%): {trade_size:.4f} SOL {status}")
    
    print(f"✅ Real config test completed!")


if __name__ == "__main__":
    test_trading_capital_configuration()
    test_portfolio_capital_management()
    test_capital_safety_limits()
    test_capital_management_with_real_config()