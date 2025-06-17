import asyncio
import pytest
from src.data.jupiter_quote import fetch_sol_price
from src.data.pyth_feed import fetch_pyth_sol_price
from src.data.aggregated_feed import AggregatedPriceFeed
from src.data.mock_feed import MockPriceFeed


class TestPriceFeedsIntegration:
    """Integration tests for price feed functionality with real services."""

    @pytest.mark.asyncio
    async def test_jupiter_price_feed_real(self):
        """Test Jupiter price feed with real API call."""
        print("\n=== Testing Jupiter Price Feed ===")
        price = await fetch_sol_price()
        print(f"Jupiter SOL price: ${price}")
        
        # Allow None if service is down, but validate structure if available
        if price is not None:
            assert isinstance(price, (int, float))
            assert price > 0
            assert price < 10000  # Reasonable upper bound for SOL price
        else:
            print("Jupiter API not available - this may be due to network issues")

    @pytest.mark.asyncio
    async def test_pyth_price_feed_real(self):
        """Test Pyth price feed with real API call."""
        print("\n=== Testing Pyth Price Feed ===")
        price = await fetch_pyth_sol_price()
        print(f"Pyth SOL price: ${price}")
        
        # Allow None if service is down, but validate structure if available
        assert price is not None, f"Pyth price is None"
        assert isinstance(price, (int, float)), f"Pyth price type: {type(price)}"
        assert price > 0, f"Pyth price is not positive: {price}"
        assert price < 10000, f"Pyth price is too high: {price}"

    @pytest.mark.asyncio
    async def test_aggregated_feed_real(self):
        """Test aggregated feed with real API calls."""
        print("\n=== Testing Aggregated Price Feed ===")
        feed = AggregatedPriceFeed()
        price = await feed.get_price()
        print(f"Aggregated SOL price: ${price}")
        
        # Allow None if both services are down
        if price is not None:
            assert isinstance(price, (int, float))
            assert price > 0
            assert price < 10000  # Reasonable upper bound for SOL price
        else:
            print("Both price feeds unavailable - this may be due to network issues")

    @pytest.mark.asyncio
    async def test_mock_feed_works(self):
        """Test mock feed generates realistic prices."""
        print("\n=== Testing Mock Price Feed ===")
        mock_feed = MockPriceFeed()
        prices = []
        for i in range(5):
            price = await mock_feed.get_price()
            prices.append(price)
            print(f"Mock price {i+1}: ${price}")
            assert isinstance(price, (int, float))
            assert 50 <= price <= 500  # Reasonable SOL price range
        
        # Check that prices vary (not all the same)
        assert len(set(prices)) > 1, "Mock feed should generate varying prices"

    @pytest.mark.asyncio
    async def test_price_feed_comparison(self):
        """Compare prices from different feeds."""
        print("\n=== Comparing Price Feeds ===")
        
        # Get prices from all sources
        jupiter_task = asyncio.create_task(fetch_sol_price())
        pyth_task = asyncio.create_task(fetch_pyth_sol_price())
        mock_feed = MockPriceFeed()
        mock_task = asyncio.create_task(mock_feed.get_price())
        
        jupiter_price, pyth_price, mock_price = await asyncio.gather(
            jupiter_task, pyth_task, mock_task
        )
        
        print(f"Jupiter: ${jupiter_price}")
        print(f"Pyth: ${pyth_price}")
        print(f"Mock: ${mock_price}")
        
        # Mock feed should always work
        assert mock_price is not None
        assert isinstance(mock_price, (int, float))
        
        # If both real feeds work, they should be reasonably close
        if jupiter_price is not None and pyth_price is not None:
            price_diff = abs(jupiter_price - pyth_price)
            max_allowed_diff = max(jupiter_price, pyth_price) * 0.05  # 5% tolerance
            assert price_diff <= max_allowed_diff, f"Price difference too large: {price_diff}"

    def test_price_feed_import_structure(self):
        """Test that all price feed modules can be imported correctly."""
        from src.data import jupiter_quote, pyth_feed, aggregated_feed, mock_feed
        
        # Verify key functions exist
        assert hasattr(jupiter_quote, 'fetch_sol_price')
        assert hasattr(pyth_feed, 'fetch_pyth_sol_price')
        assert hasattr(aggregated_feed, 'AggregatedPriceFeed')
        assert hasattr(mock_feed, 'MockPriceFeed')


async def run_tests():
    """Run all tests manually."""
    test_class = TestPriceFeedsIntegration()
    
    print("🧪 Running Price Feed Integration Tests\n")
    
    # Test imports first
    print("=== Testing Imports ===")
    test_class.test_price_feed_import_structure()
    print("✅ All imports successful\n")
    
    # Test each feed
    await test_class.test_jupiter_price_feed_real()
    await test_class.test_pyth_price_feed_real()
    await test_class.test_aggregated_feed_real()
    await test_class.test_mock_feed_works()
    await test_class.test_price_feed_comparison()
    
    print("\n🎉 All tests completed!")


if __name__ == "__main__":
    asyncio.run(run_tests())