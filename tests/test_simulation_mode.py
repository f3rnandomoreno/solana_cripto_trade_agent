import pytest
import os
from src.execution.simulation_client import TradingSimulator, SimulatedTrade, SimulatedPosition
from src.execution.portfolio import Portfolio
from src.config import settings


def test_simulation_mode_configuration():
    """Test simulation mode configuration from environment."""
    
    print(f"\n🔧 TESTING SIMULATION CONFIGURATION")
    print("=" * 50)
    
    print(f"Configuration from settings:")
    print(f"  SIMULATION_MODE: {settings.simulation_mode}")
    print(f"  SIMULATION_INITIAL_BALANCE: {settings.simulation_initial_balance}")
    
    # Verify simulation is enabled by default
    assert settings.simulation_mode == True, "Simulation mode should be enabled by default"
    assert settings.simulation_initial_balance > 0, "Initial balance should be positive"
    
    print(f"✅ Simulation configuration is valid!")


def test_trading_simulator_initialization():
    """Test trading simulator initialization."""
    
    print(f"\n🎮 TESTING SIMULATOR INITIALIZATION")
    print("=" * 50)
    
    # Create simulator with custom balance
    simulator = TradingSimulator(initial_balance=2.0)
    
    print(f"Simulator Configuration:")
    print(f"  Initial Balance: {simulator.initial_balance} SOL")
    print(f"  SOL Balance: {simulator.sol_balance} SOL")
    print(f"  USD Balance: {simulator.usd_balance} USD")
    print(f"  Total Trades: {len(simulator.trades)}")
    
    assert simulator.initial_balance == 2.0, "Initial balance should match"
    assert simulator.sol_balance == 2.0, "SOL balance should equal initial balance"
    assert simulator.usd_balance == 0.0, "USD balance should start at 0"
    assert len(simulator.trades) == 0, "Should start with no trades"
    assert simulator.position is None, "Should start with no position"
    
    print(f"✅ Simulator initialization test passed!")


def test_simulated_buy_operation():
    """Test simulated buy operation."""
    
    print(f"\n💸 TESTING SIMULATED BUY")
    print("=" * 50)
    
    simulator = TradingSimulator(initial_balance=1.0)
    
    # Test buy operation
    amount_sol = 0.5
    price = 200.0
    
    print(f"Before buy:")
    print(f"  SOL Balance: {simulator.sol_balance:.4f}")
    print(f"  USD Balance: {simulator.usd_balance:.4f}")
    
    result = simulator.simulate_trade("BUY", amount_sol, price)
    
    print(f"Buy result: {result['success']}")
    print(f"After buy:")
    print(f"  SOL Balance: {result['new_balance_sol']:.4f}")
    print(f"  USD Balance: {result['new_balance_usd']:.4f}")
    
    assert result["success"] == True, "Buy should succeed"
    assert result["simulation"] == True, "Should be marked as simulation"
    assert result["new_balance_sol"] < 1.0, "SOL balance should decrease (fees)"
    assert result["new_balance_usd"] > 0, "USD balance should increase"
    assert result["position"] is not None, "Should create position"
    
    # Verify trade was recorded
    assert len(simulator.trades) == 1, "Should have one trade"
    trade = simulator.trades[0]
    assert trade.side == "BUY", "Trade should be BUY"
    assert trade.amount_sol == amount_sol, "Trade amount should match"
    
    print(f"✅ Simulated buy test passed!")


def test_simulated_sell_operation():
    """Test simulated sell operation."""
    
    print(f"\n💰 TESTING SIMULATED SELL")
    print("=" * 50)
    
    simulator = TradingSimulator(initial_balance=1.0)
    
    # First buy to have position
    buy_result = simulator.simulate_trade("BUY", 0.5, 200.0)
    assert buy_result["success"], "Buy should succeed"
    
    print(f"After buy - Position: {buy_result['position']['amount_sol']:.4f} SOL")
    
    # Now sell
    sell_amount = 0.3
    sell_price = 220.0  # Higher price for profit
    
    sell_result = simulator.simulate_trade("SELL", sell_amount, sell_price)
    
    print(f"Sell result: {sell_result['success']}")
    print(f"Realized P&L: {sell_result.get('realized_pnl', 0):.4f} USD")
    
    assert sell_result["success"] == True, "Sell should succeed"
    assert sell_result["simulation"] == True, "Should be marked as simulation"
    assert sell_result.get("realized_pnl", 0) > 0, "Should have positive P&L (higher sell price)"
    
    # Verify position was reduced
    remaining_position = sell_result["position"]["amount_sol"] if sell_result["position"] else 0
    expected_remaining = 0.5 - sell_amount
    assert abs(remaining_position - expected_remaining) < 0.001, "Position should be reduced correctly"
    
    # Verify we have 2 trades now
    assert len(simulator.trades) == 2, "Should have two trades"
    
    print(f"✅ Simulated sell test passed!")


def test_insufficient_balance_handling():
    """Test handling of insufficient balance scenarios."""
    
    print(f"\n⚠️  TESTING INSUFFICIENT BALANCE")
    print("=" * 50)
    
    simulator = TradingSimulator(initial_balance=0.1)  # Small balance
    
    # Try to buy more than we have
    oversized_amount = 1.0  # Much larger than 0.1 SOL balance
    price = 200.0
    
    result = simulator.simulate_trade("BUY", oversized_amount, price)
    
    print(f"Oversized buy result: {result['success']}")
    print(f"Error message: {result.get('error', 'N/A')}")
    
    assert result["success"] == False, "Oversized buy should fail"
    assert "Balance insuficiente" in result.get("error", ""), "Should have insufficient balance error"
    assert result["simulation"] == True, "Should still be marked as simulation"
    
    # Try to sell without position
    sell_result = simulator.simulate_trade("SELL", 0.1, price)
    
    print(f"Sell without position result: {sell_result['success']}")
    print(f"Error message: {sell_result.get('error', 'N/A')}")
    
    assert sell_result["success"] == False, "Sell without position should fail"
    assert "Posición insuficiente" in sell_result.get("error", ""), "Should have insufficient position error"
    
    print(f"✅ Insufficient balance handling test passed!")


def test_portfolio_simulation_integration():
    """Test portfolio integration with simulation mode."""
    
    print(f"\n🔗 TESTING PORTFOLIO SIMULATION INTEGRATION")
    print("=" * 50)
    
    # Ensure simulation mode is enabled
    original_sim_mode = settings.simulation_mode
    settings.simulation_mode = True
    
    try:
        portfolio = Portfolio()
        
        # Execute simulated trade through portfolio
        initial_balance = portfolio.quote_balance
        trade_amount = 0.05
        price = 200.0
        
        print(f"Before trade:")
        print(f"  Portfolio data: {portfolio.as_dict()}")
        
        portfolio.update_from_trade("BUY", trade_amount, price)
        
        print(f"After trade:")
        final_data = portfolio.as_dict()
        print(f"  Portfolio data: {final_data}")
        
        # Verify simulation mode is reflected
        assert final_data.get("simulation_mode") == True, "Portfolio should show simulation mode"
        assert "realized_pnl" in final_data, "Should have P&L tracking"
        assert "total_trades" in final_data, "Should have trade counting"
        
        print(f"✅ Portfolio simulation integration test passed!")
        
    finally:
        # Restore original setting
        settings.simulation_mode = original_sim_mode


def test_portfolio_status_and_export():
    """Test portfolio status reporting and export functionality."""
    
    print(f"\n📊 TESTING PORTFOLIO STATUS & EXPORT")
    print("=" * 50)
    
    simulator = TradingSimulator(initial_balance=1.0)
    
    # Execute some trades
    simulator.simulate_trade("BUY", 0.5, 200.0)
    simulator.update_current_price(220.0)  # Price increased
    simulator.simulate_trade("SELL", 0.2, 220.0)
    
    # Get portfolio status
    status = simulator.get_portfolio_status()
    
    print(f"Portfolio Status:")
    for key, value in status.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.4f}")
        else:
            print(f"  {key}: {value}")
    
    assert status["simulation_mode"] == True, "Should be in simulation mode"
    assert status["total_trades"] == 2, "Should have 2 trades"
    assert status["realized_pnl"] > 0, "Should have positive realized P&L"
    assert status["unrealized_pnl"] >= 0, "Should have non-negative unrealized P&L"
    
    # Test export functionality
    trade_history = simulator.get_trade_history()
    assert len(trade_history) == 2, "Should export 2 trades"
    
    # Test log export (without actually writing file)
    import tempfile
    import os
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        filename = f.name
    
    try:
        exported_file = simulator.export_simulation_log(filename)
        assert os.path.exists(exported_file), "Log file should be created"
        
        # Verify file contains expected data
        import json
        with open(exported_file, 'r') as f:
            log_data = json.load(f)
        
        assert "simulation_summary" in log_data, "Should have simulation summary"
        assert "trade_history" in log_data, "Should have trade history"
        assert len(log_data["trade_history"]) == 2, "Should have 2 trades in export"
        
        print(f"✅ Portfolio status and export test passed!")
        
    finally:
        # Clean up
        if os.path.exists(filename):
            os.unlink(filename)


if __name__ == "__main__":
    test_simulation_mode_configuration()
    test_trading_simulator_initialization()
    test_simulated_buy_operation()
    test_simulated_sell_operation()
    test_insufficient_balance_handling()
    test_portfolio_simulation_integration()
    test_portfolio_status_and_export()
    
    print(f"\n🎉 ALL SIMULATION TESTS PASSED!")