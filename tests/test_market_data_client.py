"""
Tests for Market Data Client.

Comprehensive test suite covering all MarketDataClient functionality including
price retrieval, source status, real-time polling, caching, and error handling.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
import json

from src.api_client.market_data import MarketDataClient, PriceData, SourceStatus, MarketDataHealth
from src.api_client.base_client import HealthStatus


@pytest.fixture
def mock_config():
    """Mock configuration for testing."""
    return {
        "base_url": "http://localhost:8000",
        "timeout": 10
    }


@pytest.fixture
def market_data_client(mock_config):
    """Create MarketDataClient instance for testing."""
    return MarketDataClient(**mock_config)


@pytest.fixture
def mock_price_response():
    """Mock price response data."""
    return {
        "symbol": "BTCUSD",
        "price": 45000.50,
        "timestamp": datetime.now().isoformat(),
        "source": "coinbase",
        "quality_grade": "A",
        "bid": 44999.00,
        "ask": 45001.00,
        "volume": 1250000,
        "change_24h": 1200.50,
        "change_percent_24h": 2.75
    }


@pytest.fixture
def mock_health_response():
    """Mock health check response data."""
    return {
        "status": "healthy",
        "uptime_seconds": 86400,
        "active_sources": 5,
        "total_sources": 6,
        "avg_response_time_ms": 120.5,
        "data_points_per_minute": 450,
        "overall_quality_grade": "A",
        "errors_last_hour": 2
    }


@pytest.fixture
def mock_sources_response():
    """Mock sources status response data."""
    return {
        "sources": [
            {
                "name": "coinbase",
                "status": "active",
                "last_update": datetime.now().isoformat(),
                "quality_grade": "A",
                "error_count": 0,
                "response_time_ms": 95.2
            },
            {
                "name": "binance",
                "status": "active",
                "last_update": datetime.now().isoformat(),
                "quality_grade": "B",
                "error_count": 1,
                "response_time_ms": 156.8
            }
        ]
    }


@pytest.fixture
def mock_historical_response():
    """Mock historical data response."""
    base_time = datetime.now()
    return {
        "data": [
            {
                "symbol": "BTCUSD",
                "price": 44800.00 + i * 50,
                "timestamp": (base_time - timedelta(hours=i)).isoformat(),
                "source": "coinbase",
                "quality_grade": "A",
                "volume": 1000000 + i * 10000
            }
            for i in range(24)
        ]
    }


class TestMarketDataClientInitialization:
    """Test MarketDataClient initialization."""

    def test_client_initialization(self, mock_config):
        """Test client initializes correctly."""
        client = MarketDataClient(**mock_config)

        assert hasattr(client, 'base_url')
        assert hasattr(client, 'timeout')
        assert client._cache_ttl == 5
        assert client._polling_active is False
        assert len(client._price_cache) == 0
        assert len(client._polling_callbacks) == 0

    def test_client_initialization_with_custom_cache_ttl(self):
        """Test client initialization with custom cache TTL."""
        client = MarketDataClient(
            base_url="http://localhost:8000",
            timeout=15
        )
        client._cache_ttl = 10

        assert client._cache_ttl == 10


class TestHealthCheck:
    """Test health check functionality."""

    @pytest.mark.asyncio
    async def test_health_check_success(self, market_data_client, mock_health_response):
        """Test successful health check."""
        with patch.object(market_data_client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_health_response

            result = await market_data_client.health_check()

            assert result["healthy"] is True
            assert result["status"] == "healthy"
            assert "details" in result
            assert result["details"]["active_sources"] == 5
            assert result["details"]["total_sources"] == 6

    @pytest.mark.asyncio
    async def test_health_check_failure(self, market_data_client):
        """Test health check failure."""
        with patch.object(market_data_client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = Exception("Connection error")

            result = await market_data_client.health_check()

            assert result["healthy"] is False
            assert result["status"] == "error"
            assert "Connection error" in result["error"]

    @pytest.mark.asyncio
    async def test_health_check_invalid_response(self, market_data_client):
        """Test health check with invalid response."""
        with patch.object(market_data_client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = "invalid response"

            result = await market_data_client.health_check()

            assert result["healthy"] is False
            assert result["status"] == "unknown"


class TestPriceRetrieval:
    """Test price data retrieval functionality."""

    @pytest.mark.asyncio
    async def test_get_current_price_success(self, market_data_client, mock_price_response):
        """Test successful current price retrieval."""
        with patch.object(market_data_client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_price_response

            result = await market_data_client.get_current_price("BTCUSD")

            assert isinstance(result, PriceData)
            assert result.symbol == "BTCUSD"
            assert result.price == 45000.50
            assert result.quality_grade == "A"
            assert result.bid == 44999.00
            assert result.ask == 45001.00

    @pytest.mark.asyncio
    async def test_get_current_price_invalid_symbol(self, market_data_client):
        """Test current price retrieval with invalid symbol."""
        result = await market_data_client.get_current_price("INVALID_SYMBOL!")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_current_price_api_error(self, market_data_client):
        """Test current price retrieval with API error."""
        with patch.object(market_data_client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = Exception("API error")

            result = await market_data_client.get_current_price("BTCUSD")

            assert result is None

    @pytest.mark.asyncio
    async def test_get_current_price_caching(self, market_data_client, mock_price_response):
        """Test price caching functionality."""
        with patch.object(market_data_client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_price_response

            # First call - should hit API
            result1 = await market_data_client.get_current_price("BTCUSD")
            assert mock_get.call_count == 1

            # Second call - should use cache
            result2 = await market_data_client.get_current_price("BTCUSD")
            assert mock_get.call_count == 1  # No additional API calls

            assert result1.price == result2.price

    @pytest.mark.asyncio
    async def test_get_current_price_force_refresh(self, market_data_client, mock_price_response):
        """Test price retrieval with force refresh."""
        with patch.object(market_data_client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_price_response

            # First call
            await market_data_client.get_current_price("BTCUSD")
            assert mock_get.call_count == 1

            # Second call with force refresh - should hit API again
            await market_data_client.get_current_price("BTCUSD", force_refresh=True)
            assert mock_get.call_count == 2


class TestHistoricalData:
    """Test historical data retrieval."""

    @pytest.mark.asyncio
    async def test_get_historical_prices_success(self, market_data_client, mock_historical_response):
        """Test successful historical data retrieval."""
        with patch.object(market_data_client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_historical_response

            result = await market_data_client.get_historical_prices("BTCUSD", "1h", 24)

            assert len(result) == 24
            assert all(isinstance(item, PriceData) for item in result)
            assert result[0].symbol == "BTCUSD"

    @pytest.mark.asyncio
    async def test_get_historical_prices_invalid_symbol(self, market_data_client):
        """Test historical data retrieval with invalid symbol."""
        result = await market_data_client.get_historical_prices("INVALID!")

        assert result == []

    @pytest.mark.asyncio
    async def test_get_historical_prices_limit_cap(self, market_data_client):
        """Test historical data limit is capped at 1000."""
        with patch.object(market_data_client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = {"data": []}

            await market_data_client.get_historical_prices("BTCUSD", "1h", 2000)

            # Check that the limit parameter was capped
            args, kwargs = mock_get.call_args
            assert kwargs["params"]["limit"] == 1000


class TestSourcesStatus:
    """Test data sources status functionality."""

    @pytest.mark.asyncio
    async def test_get_sources_status_success(self, market_data_client, mock_sources_response):
        """Test successful sources status retrieval."""
        with patch.object(market_data_client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_sources_response

            result = await market_data_client.get_sources_status()

            assert len(result) == 2
            assert all(isinstance(source, SourceStatus) for source in result)
            assert result[0].name == "coinbase"
            assert result[0].status == "active"
            assert result[0].quality_grade == "A"

    @pytest.mark.asyncio
    async def test_get_sources_status_api_error(self, market_data_client):
        """Test sources status retrieval with API error."""
        with patch.object(market_data_client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = Exception("API error")

            result = await market_data_client.get_sources_status()

            assert result == []


class TestRealTimePolling:
    """Test real-time data polling functionality."""

    @pytest.mark.asyncio
    async def test_start_real_time_polling_success(self, market_data_client):
        """Test successful start of real-time polling."""
        symbols = ["BTCUSD", "ETHUSD"]
        callback = Mock()

        result = await market_data_client.start_real_time_polling(symbols, callback, 0.1)

        assert result is True
        assert market_data_client._polling_active is True
        assert market_data_client._polling_symbols == symbols
        assert callback in market_data_client._polling_callbacks

    @pytest.mark.asyncio
    async def test_start_real_time_polling_already_active(self, market_data_client):
        """Test starting polling when already active."""
        market_data_client._polling_active = True

        result = await market_data_client.start_real_time_polling(["BTCUSD"])

        assert result is False

    @pytest.mark.asyncio
    async def test_start_real_time_polling_invalid_symbols(self, market_data_client):
        """Test starting polling with invalid symbols."""
        result = await market_data_client.start_real_time_polling(["INVALID!"])

        assert result is False

    @pytest.mark.asyncio
    async def test_stop_real_time_polling_success(self, market_data_client):
        """Test successful stop of real-time polling."""
        market_data_client._polling_active = True
        market_data_client._polling_symbols = ["BTCUSD"]

        result = await market_data_client.stop_real_time_polling()

        assert result is True
        assert market_data_client._polling_active is False
        assert len(market_data_client._polling_symbols) == 0
        assert len(market_data_client._polling_callbacks) == 0

    @pytest.mark.asyncio
    async def test_stop_real_time_polling_not_active(self, market_data_client):
        """Test stopping polling when not active."""
        result = await market_data_client.stop_real_time_polling()

        assert result is False

    def test_add_polling_callback_success(self, market_data_client):
        """Test adding polling callback."""
        callback = Mock()

        result = market_data_client.add_polling_callback(callback)

        assert result is True
        assert callback in market_data_client._polling_callbacks

    def test_add_polling_callback_duplicate(self, market_data_client):
        """Test adding duplicate polling callback."""
        callback = Mock()
        market_data_client._polling_callbacks.append(callback)

        result = market_data_client.add_polling_callback(callback)

        assert result is False


class TestCacheManagement:
    """Test price cache management functionality."""

    def test_get_cached_prices(self, market_data_client):
        """Test getting cached prices."""
        # Add some test data to cache
        test_price = PriceData(
            symbol="BTCUSD",
            price=45000.0,
            timestamp=datetime.now(),
            source="test"
        )
        market_data_client._price_cache["BTCUSD"] = test_price

        cached_prices = market_data_client.get_cached_prices()

        assert "BTCUSD" in cached_prices
        assert cached_prices["BTCUSD"].price == 45000.0

    def test_clear_cache(self, market_data_client):
        """Test clearing price cache."""
        # Add some test data
        market_data_client._price_cache["BTCUSD"] = Mock()
        market_data_client._last_cache_update["BTCUSD"] = datetime.now()

        market_data_client.clear_cache()

        assert len(market_data_client._price_cache) == 0
        assert len(market_data_client._last_cache_update) == 0

    def test_cache_validity_check(self, market_data_client):
        """Test cache validity checking."""
        symbol = "BTCUSD"

        # No cache data - should be invalid
        assert market_data_client._is_cache_valid(symbol) is False

        # Add cache data with recent timestamp - should be valid
        market_data_client._price_cache[symbol] = Mock()
        market_data_client._last_cache_update[symbol] = datetime.now()
        assert market_data_client._is_cache_valid(symbol) is True

        # Old timestamp - should be invalid
        market_data_client._last_cache_update[symbol] = datetime.now() - timedelta(seconds=10)
        assert market_data_client._is_cache_valid(symbol) is False


class TestErrorHandling:
    """Test error handling and edge cases."""

    @pytest.mark.asyncio
    async def test_polling_loop_error_handling(self, market_data_client, mock_price_response):
        """Test polling loop handles errors gracefully."""
        callback = Mock(side_effect=Exception("Callback error"))

        with patch.object(market_data_client, 'get_current_price') as mock_get_price:
            mock_get_price.return_value = PriceData(
                symbol="BTCUSD",
                price=45000.0,
                timestamp=datetime.now(),
                source="test"
            )

            # Start polling
            market_data_client._polling_active = True
            market_data_client._polling_symbols = ["BTCUSD"]
            market_data_client._polling_callbacks = [callback]
            market_data_client._polling_interval = 0.01

            # Run polling loop briefly
            polling_task = asyncio.create_task(market_data_client._polling_loop())
            await asyncio.sleep(0.05)  # Let it run briefly

            # Stop polling
            market_data_client._polling_active = False
            await polling_task

            # Verify callback was called despite errors
            assert callback.called

    @pytest.mark.asyncio
    async def test_async_callback_handling(self, market_data_client):
        """Test handling of async callbacks in polling."""
        async_callback = AsyncMock()
        sync_callback = Mock()

        price_data = PriceData(
            symbol="BTCUSD",
            price=45000.0,
            timestamp=datetime.now(),
            source="test"
        )

        market_data_client._polling_callbacks = [async_callback, sync_callback]

        # Simulate callback execution
        for callback in market_data_client._polling_callbacks:
            if asyncio.iscoroutinefunction(callback):
                await callback(price_data)
            else:
                callback(price_data)

        # Verify both callbacks were called
        async_callback.assert_called_once_with(price_data)
        sync_callback.assert_called_once_with(price_data)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])