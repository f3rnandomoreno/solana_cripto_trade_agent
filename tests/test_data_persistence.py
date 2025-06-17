import pytest
import os
import tempfile
import sqlite3
import time
from src.data.data_manager import DataManager, PriceData, TradeData, PortfolioSnapshot
from src.utils.data_analytics import generate_trading_report, backup_database, print_quick_stats


def test_data_manager_initialization():
    """Test DataManager initialization and database creation."""
    
    print(f"\n💾 TESTING DATA MANAGER INITIALIZATION")
    print("=" * 50)
    
    # Create temporary database for testing
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
        temp_db_path = tmp_file.name
    
    try:
        # Initialize DataManager with custom path
        dm = DataManager(db_path=temp_db_path)
        
        print(f"Database created at: {temp_db_path}")
        print(f"Database exists: {os.path.exists(temp_db_path)}")
        
        # Verify database file was created
        assert os.path.exists(temp_db_path), "Database file should be created"
        
        # Verify tables were created
        with sqlite3.connect(temp_db_path) as conn:
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]
            
            expected_tables = ['price_data', 'trade_data', 'portfolio_snapshots']
            for table in expected_tables:
                assert table in tables, f"Table {table} should exist"
                print(f"✅ Table {table} created")
        
        print(f"✅ DataManager initialization test passed!")
        
    finally:
        # Clean up
        if os.path.exists(temp_db_path):
            os.unlink(temp_db_path)


def test_price_data_persistence():
    """Test saving and retrieving price data."""
    
    print(f"\n💰 TESTING PRICE DATA PERSISTENCE")
    print("=" * 50)
    
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
        temp_db_path = tmp_file.name
    
    try:
        dm = DataManager(db_path=temp_db_path)
        
        # Save test price data
        test_prices = [
            (200.50, "mock", 1000000, 50000000),
            (201.25, "aggregated", 1100000, 51000000),
            (199.80, "pyth", 950000, 49000000)
        ]
        
        for price, source, volume, market_cap in test_prices:
            success = dm.save_price_data(
                price=price,
                source=source,
                volume_24h=volume,
                market_cap=market_cap,
                metadata={"test": True}
            )
            assert success, f"Should save price {price} from {source}"
            print(f"💾 Saved: {price} USD from {source}")
        
        # Retrieve price history
        price_history = dm.get_price_history(hours=1)  # Last hour
        
        print(f"Retrieved {len(price_history)} price records")
        assert len(price_history) == 3, "Should retrieve all 3 price records"
        
        # Verify data integrity
        for i, record in enumerate(price_history):
            expected_price, expected_source, _, _ = test_prices[i]
            assert record["price"] == expected_price, f"Price should match"
            assert record["source"] == expected_source, f"Source should match"
            assert record["metadata"]["test"] == True, f"Metadata should be preserved"
            print(f"✅ Record {i+1}: {record['price']} USD from {record['source']}")
        
        print(f"✅ Price data persistence test passed!")
        
    finally:
        if os.path.exists(temp_db_path):
            os.unlink(temp_db_path)


def test_trade_data_persistence():
    """Test saving and retrieving trade data."""
    
    print(f"\n🔄 TESTING TRADE DATA PERSISTENCE")
    print("=" * 50)
    
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
        temp_db_path = tmp_file.name
    
    try:
        dm = DataManager(db_path=temp_db_path)
        
        # Save test trade data
        test_trades = [
            ("BUY", 0.5, 200.0, 100.0, 0.0025, True, 0.2),   # Simulation buy
            ("SELL", 0.3, 210.0, 63.0, 0.0015, True, 0.1),   # Simulation sell
            ("BUY", 0.1, 205.0, 20.5, 0.0005, False, 0.15)   # Real buy
        ]
        
        for side, amount, price, value, fees, simulation, slippage in test_trades:
            success = dm.save_trade_data(
                side=side,
                amount_sol=amount,
                price=price,
                value_usd=value,
                fees_sol=fees,
                simulation=simulation,
                slippage_pct=slippage,
                portfolio_value_before=100.0,
                portfolio_value_after=110.0,
                metadata={"test_trade": True}
            )
            assert success, f"Should save {side} trade"
            print(f"💾 Saved: {side} {amount} SOL @ ${price} ({'SIM' if simulation else 'REAL'})")
        
        # Retrieve all trades
        all_trades = dm.get_trade_history(hours=1)
        assert len(all_trades) == 3, "Should retrieve all 3 trades"
        print(f"Retrieved {len(all_trades)} total trades")
        
        # Retrieve only simulation trades
        sim_trades = dm.get_trade_history(simulation=True, hours=1)
        assert len(sim_trades) == 2, "Should retrieve 2 simulation trades"
        print(f"Retrieved {len(sim_trades)} simulation trades")
        
        # Retrieve only real trades
        real_trades = dm.get_trade_history(simulation=False, hours=1)
        assert len(real_trades) == 1, "Should retrieve 1 real trade"
        print(f"Retrieved {len(real_trades)} real trades")
        
        # Verify trade data
        for trade in all_trades:
            assert trade["side"] in ["BUY", "SELL"], "Valid trade side"
            assert trade["amount_sol"] > 0, "Positive amount"
            assert trade["price"] > 0, "Positive price"
            print(f"✅ Trade: {trade['side']} {trade['amount_sol']} SOL @ ${trade['price']}")
        
        print(f"✅ Trade data persistence test passed!")
        
    finally:
        if os.path.exists(temp_db_path):
            os.unlink(temp_db_path)


def test_portfolio_snapshot_persistence():
    """Test saving and retrieving portfolio snapshots."""
    
    print(f"\n📈 TESTING PORTFOLIO SNAPSHOT PERSISTENCE")
    print("=" * 50)
    
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
        temp_db_path = tmp_file.name
    
    try:
        dm = DataManager(db_path=temp_db_path)
        
        # Save test portfolio snapshots
        test_snapshots = [
            (1.0, 0.0, 200.0, 0.0, 0.0, True),    # Initial state (simulation)
            (0.5, 100.0, 200.0, 0.0, 10.0, True), # After buy (simulation)  
            (0.0, 210.0, 210.0, 10.0, 0.0, True), # After sell (simulation)
            (0.8, 40.0, 200.0, 0.0, 5.0, False)   # Real trade
        ]
        
        for sol_bal, usd_bal, total_val, real_pnl, unreal_pnl, simulation in test_snapshots:
            success = dm.save_portfolio_snapshot(
                sol_balance=sol_bal,
                usd_balance=usd_bal,
                total_value_usd=total_val,
                realized_pnl=real_pnl,
                unrealized_pnl=unreal_pnl,
                simulation=simulation,
                metadata={"test_snapshot": True}
            )
            assert success, "Should save portfolio snapshot"
            print(f"💾 Snapshot: {sol_bal} SOL, {usd_bal} USD, Total: ${total_val} ({'SIM' if simulation else 'REAL'})")
            
            # Small delay to ensure different timestamps
            time.sleep(0.01)
        
        # Retrieve portfolio history
        portfolio_history = dm.get_portfolio_history(hours=1)
        assert len(portfolio_history) == 4, "Should retrieve all 4 snapshots"
        print(f"Retrieved {len(portfolio_history)} portfolio snapshots")
        
        # Retrieve only simulation snapshots
        sim_snapshots = dm.get_portfolio_history(simulation=True, hours=1)
        assert len(sim_snapshots) == 3, "Should retrieve 3 simulation snapshots"
        print(f"Retrieved {len(sim_snapshots)} simulation snapshots")
        
        # Verify data progression
        for i, snapshot in enumerate(portfolio_history):
            expected = test_snapshots[i]
            assert abs(snapshot["sol_balance"] - expected[0]) < 0.001, "SOL balance should match"
            assert abs(snapshot["total_value_usd"] - expected[2]) < 0.001, "Total value should match"
            print(f"✅ Snapshot {i+1}: {snapshot['sol_balance']} SOL, ${snapshot['total_value_usd']}")
        
        print(f"✅ Portfolio snapshot persistence test passed!")
        
    finally:
        if os.path.exists(temp_db_path):
            os.unlink(temp_db_path)


def test_statistics_and_export():
    """Test statistics generation and data export."""
    
    print(f"\n📊 TESTING STATISTICS AND EXPORT")
    print("=" * 50)
    
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
        temp_db_path = tmp_file.name
    
    try:
        dm = DataManager(db_path=temp_db_path)
        
        # Add some test data
        dm.save_price_data(200.0, "test", 1000000, 50000000)
        dm.save_trade_data("BUY", 0.5, 200.0, 100.0, 0.0025, True)
        dm.save_portfolio_snapshot(1.0, 0.0, 200.0, 0.0, 0.0, True)
        
        # Get statistics
        stats = dm.get_statistics()
        
        print(f"Statistics retrieved:")
        print(f"  Price records: {stats['price_data']['total_records']}")
        print(f"  Trade records: {sum(stats['trade_data'].values())}")
        print(f"  Portfolio snapshots: {stats['portfolio_snapshots']['total_records']}")
        print(f"  DB size: {stats['database']['file_size_mb']} MB")
        
        assert stats["price_data"]["total_records"] >= 1, "Should have price data"
        assert sum(stats["trade_data"].values()) >= 1, "Should have trade data"
        assert stats["portfolio_snapshots"]["total_records"] >= 1, "Should have portfolio data"
        assert stats["database"]["file_size_mb"] > 0, "Database should have size"
        
        # Test export
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as export_file:
            export_path = export_file.name
        
        try:
            success = dm.export_data(export_path)
            assert success, "Export should succeed"
            assert os.path.exists(export_path), "Export file should exist"
            
            # Verify export file has content
            file_size = os.path.getsize(export_path)
            assert file_size > 100, "Export file should have substantial content"
            print(f"✅ Export file created: {file_size} bytes")
            
        finally:
            if os.path.exists(export_path):
                os.unlink(export_path)
        
        print(f"✅ Statistics and export test passed!")
        
    finally:
        if os.path.exists(temp_db_path):
            os.unlink(temp_db_path)


def test_data_analytics_integration():
    """Test integration with data analytics module."""
    
    print(f"\n🎯 TESTING DATA ANALYTICS INTEGRATION")
    print("=" * 50)
    
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
        temp_db_path = tmp_file.name
    
    try:
        dm = DataManager(db_path=temp_db_path)
        
        # Add comprehensive test data
        prices = [190.0, 195.0, 200.0, 205.0, 210.0]
        for i, price in enumerate(prices):
            dm.save_price_data(price, "test")
            time.sleep(0.01)  # Small delay for different timestamps
        
        # Add some trades
        dm.save_trade_data("BUY", 0.5, 200.0, 100.0, 0.0025, True)
        time.sleep(0.01)
        dm.save_trade_data("SELL", 0.3, 210.0, 63.0, 0.0015, True)
        
        # Add portfolio snapshots
        dm.save_portfolio_snapshot(1.0, 0.0, 200.0, 0.0, 0.0, True)
        time.sleep(0.01)
        dm.save_portfolio_snapshot(0.5, 100.0, 205.0, 0.0, 5.0, True)
        
        # Test analytics report generation
        # Pass the custom DataManager to generate_trading_report by temporarily replacing the global one
        from src.utils import data_analytics
        original_dm = data_analytics.data_manager
        data_analytics.data_manager = dm
        
        try:
            report = generate_trading_report(hours=1)
        finally:
            data_analytics.data_manager = original_dm
        
        print(f"Analytics report generated:")
        print(f"  Price data points: {report['raw_data']['price_count']}")
        print(f"  Trades analyzed: {report['raw_data']['trade_count']}")
        print(f"  Portfolio snapshots: {report['raw_data']['portfolio_snapshots']}")
        
        assert report["raw_data"]["price_count"] >= 5, "Should have price data"
        assert report["raw_data"]["trade_count"] >= 2, "Should have trade data"
        assert "price_analysis" in report, "Should have price analysis"
        assert "trading_analysis" in report, "Should have trading analysis"
        
        # Test price analysis
        price_analysis = report["price_analysis"]
        if "error" not in price_analysis:
            assert price_analysis["min_price"] == 190.0, "Min price should be correct"
            assert price_analysis["max_price"] == 210.0, "Max price should be correct"
            print(f"✅ Price analysis: {price_analysis['trend']} trend, {price_analysis['volatility_pct']:.2f}% volatility")
        
        print(f"✅ Data analytics integration test passed!")
        
    finally:
        if os.path.exists(temp_db_path):
            os.unlink(temp_db_path)


def test_cleanup_functionality():
    """Test data cleanup functionality."""
    
    print(f"\n🧹 TESTING DATA CLEANUP")
    print("=" * 50)
    
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
        temp_db_path = tmp_file.name
    
    try:
        dm = DataManager(db_path=temp_db_path)
        
        # Add current data
        dm.save_price_data(200.0, "current")
        dm.save_trade_data("BUY", 0.5, 200.0, 100.0, 0.0025, True)
        
        # Simulate old data by manually inserting with old timestamp
        old_timestamp = time.time() - (35 * 24 * 3600)  # 35 days ago
        
        with sqlite3.connect(temp_db_path) as conn:
            conn.execute("""
                INSERT INTO price_data (timestamp, price, source) 
                VALUES (?, ?, ?)
            """, (old_timestamp, 180.0, "old"))
            conn.commit()
        
        # Verify we have both old and new data
        stats_before = dm.get_statistics()
        price_count_before = stats_before["price_data"]["total_records"]
        print(f"Records before cleanup: {price_count_before}")
        
        assert price_count_before >= 2, "Should have both old and new records"
        
        # Cleanup old data (older than 30 days)
        success = dm.cleanup_old_data(days=30)
        assert success, "Cleanup should succeed"
        
        # Verify cleanup worked
        stats_after = dm.get_statistics()
        price_count_after = stats_after["price_data"]["total_records"]
        print(f"Records after cleanup: {price_count_after}")
        
        assert price_count_after < price_count_before, "Should have fewer records after cleanup"
        assert price_count_after >= 1, "Should still have recent records"
        
        print(f"✅ Data cleanup test passed!")
        
    finally:
        if os.path.exists(temp_db_path):
            os.unlink(temp_db_path)


if __name__ == "__main__":
    test_data_manager_initialization()
    test_price_data_persistence()
    test_trade_data_persistence()
    test_portfolio_snapshot_persistence()
    test_statistics_and_export()
    test_data_analytics_integration()
    test_cleanup_functionality()
    
    print(f"\n🎉 ALL DATA PERSISTENCE TESTS PASSED!")
    print("📊 El sistema de persistencia está funcionando correctamente")
    print("💾 Todos los datos de trading se guardan localmente de forma segura")