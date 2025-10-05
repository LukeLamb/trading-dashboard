# Manual Testing Guide - Phase 2 Step 2: Market Data Agent Integration

## Overview

This guide provides manual testing and debugging instructions for the completed Market Data Agent Integration (Phase 2 Step 2).

## ✅ Step Completed: Market Data Agent Integration

**Features Implemented:**

- MarketDataClient extending BaseClient with specialized functionality
- Health check with comprehensive MarketDataHealth model
- Price retrieval methods with caching and validation
- Historical data retrieval with configurable timeframes
- Source status monitoring with detailed metrics
- Real-time polling system with callback support
- Advanced caching with TTL and force refresh
- Comprehensive test suite with 27 test cases

## Prerequisites

1. **Python Environment**: Ensure virtual environment is activated

   ```bash
   cd C:\Users\infob\Desktop\trading-dashboard
   venv\Scripts\activate
   ```

2. **Dependencies**: All dependencies should be installed from requirements.txt

3. **Project Structure**: Verify the following files exist:
   - `src/api_client/market_data.py` (MarketDataClient implementation)
   - `tests/test_market_data_client.py` (Comprehensive test suite)

## Manual Testing Commands

### 1. Run All Market Data Client Tests

```bash
# Full test suite (27 tests)
python -m pytest tests/test_market_data_client.py -v

# Expected output: 27 passed in ~45s
```

### 2. Run Specific Test Categories

```bash
# Test client initialization
python -m pytest tests/test_market_data_client.py::TestMarketDataClientInitialization -v

# Test health check functionality
python -m pytest tests/test_market_data_client.py::TestHealthCheck -v

# Test price retrieval
python -m pytest tests/test_market_data_client.py::TestPriceRetrieval -v

# Test historical data
python -m pytest tests/test_market_data_client.py::TestHistoricalData -v

# Test real-time polling
python -m pytest tests/test_market_data_client.py::TestRealTimePolling -v

# Test cache management
python -m pytest tests/test_market_data_client.py::TestCacheManagement -v
```

### 3. Verify Base Client Compatibility

```bash
# Ensure base client tests still pass (22 tests)
python -m pytest tests/test_base_client.py -v

# Expected output: 22 passed in ~0.4s
```

### 4. Test Integration with Dashboard

```bash
# Verify dashboard imports work correctly
python -c "
import sys
sys.path.append('.')
try:
    from src.dashboard.main import configure_page, get_config_manager
    from src.api_client.market_data import MarketDataClient
    print('✅ MarketDataClient import successful')

    # Test client creation
    client = MarketDataClient('http://localhost:8000')
    print('✅ MarketDataClient initialization successful')

    print('✅ All integrations working correctly')
except Exception as e:
    print(f'❌ Integration error: {e}')
"
```

## Interactive Testing (Python REPL)

For manual interactive testing:

```bash
python -c "
import asyncio
from src.api_client.market_data import MarketDataClient

# Create client
client = MarketDataClient('http://localhost:8000', timeout=5)
print('Client created:', client)

# Test methods (these will fail gracefully if no actual server)
async def test_client():
    # Test health check
    health = await client.health_check()
    print('Health check result:', health)

    # Test price retrieval (will return None if no server)
    price = await client.get_current_price('BTCUSD')
    print('Price result:', price)

# Run async test
asyncio.run(test_client())
"
```

## Debugging Commands

### 1. Check Imports and Dependencies

```bash
# Verify all imports work
python -c "
from src.api_client.market_data import (
    MarketDataClient, PriceData, SourceStatus, MarketDataHealth
)
from src.api_client.base_client import BaseClient, HealthStatus
print('✅ All imports successful')
"
```

### 2. Validate Configuration

```bash
# Check configuration loading
python -c "
from src.utils.config import ConfigurationManager
config_manager = ConfigurationManager()
agent_config = config_manager.get_agent_config('market_data')
print('Market Data Agent config:', agent_config)
"
```

### 3. Test Circuit Breaker Integration

```bash
# Test circuit breaker functionality
python -c "
import asyncio
from src.api_client.market_data import MarketDataClient

async def test_circuit_breaker():
    # Create client with short timeout for testing
    client = MarketDataClient('http://invalid-url:9999', timeout=1)

    # These should fail and trigger circuit breaker
    for i in range(3):
        try:
            result = await client.health_check()
            print(f'Attempt {i+1}: {result}')
        except Exception as e:
            print(f'Attempt {i+1}: Failed as expected - {type(e).__name__}')

asyncio.run(test_circuit_breaker())
"
```

### 4. Memory and Performance Check

```bash
# Basic memory usage test
python -c "
import psutil
import gc
from src.api_client.market_data import MarketDataClient

process = psutil.Process()
initial_memory = process.memory_info().rss / 1024 / 1024

# Create multiple clients
clients = [MarketDataClient(f'http://localhost:800{i}') for i in range(10)]
print(f'Created {len(clients)} clients')

current_memory = process.memory_info().rss / 1024 / 1024
print(f'Memory usage: {initial_memory:.1f}MB -> {current_memory:.1f}MB')

# Cleanup
del clients
gc.collect()

final_memory = process.memory_info().rss / 1024 / 1024
print(f'After cleanup: {final_memory:.1f}MB')
"
```

## Common Issues and Solutions

### Issue 1: Import Errors

```bash
# Solution: Check Python path and virtual environment
python -c "import sys; print('Python path:', sys.path)"
python -c "import sys; print('Python executable:', sys.executable)"
```

### Issue 2: Test Failures

```bash
# Run tests with more verbose output
python -m pytest tests/test_market_data_client.py -v -s --tb=long

# Run specific failing test
python -m pytest tests/test_market_data_client.py::TestClassName::test_method_name -v -s
```

### Issue 3: Async/Await Issues

```bash
# Test async functionality
python -c "
import asyncio
print('Asyncio version:', asyncio.__version__ if hasattr(asyncio, '__version__') else 'Built-in')

async def test_async():
    print('Async/await working correctly')
    return True

result = asyncio.run(test_async())
print('Async test result:', result)
"
```

## Expected Test Results

### Full Test Suite Output

```bash
============================= test session starts =============================
platform win32 -- Python 3.13.7, pytest-8.4.2, pluggy-1.6.0
collected 27 items

tests/test_market_data_client.py::TestMarketDataClientInitialization::test_client_initialization PASSED
tests/test_market_data_client.py::TestMarketDataClientInitialization::test_client_initialization_with_custom_cache_ttl PASSED
tests/test_market_data_client.py::TestHealthCheck::test_health_check_success PASSED
tests/test_market_data_client.py::TestHealthCheck::test_health_check_failure PASSED
tests/test_market_data_client.py::TestHealthCheck::test_health_check_invalid_response PASSED
tests/test_market_data_client.py::TestPriceRetrieval::test_get_current_price_success PASSED
tests/test_market_data_client.py::TestPriceRetrieval::test_get_current_price_invalid_symbol PASSED
tests/test_market_data_client.py::TestPriceRetrieval::test_get_current_price_api_error PASSED
tests/test_market_data_client.py::TestPriceRetrieval::test_get_current_price_caching PASSED
tests/test_market_data_client.py::TestPriceRetrieval::test_get_current_price_force_refresh PASSED
tests/test_market_data_client.py::TestHistoricalData::test_get_historical_prices_success PASSED
tests/test_market_data_client.py::TestHistoricalData::test_get_historical_prices_invalid_symbol PASSED
tests/test_market_data_client.py::TestHistoricalData::test_get_historical_prices_limit_cap PASSED
tests/test_market_data_client.py::TestSourcesStatus::test_get_sources_status_success PASSED
tests/test_market_data_client.py::TestSourcesStatus::test_get_sources_status_api_error PASSED
tests/test_market_data_client.py::TestRealTimePolling::test_start_real_time_polling_success PASSED
tests/test_market_data_client.py::TestRealTimePolling::test_start_real_time_polling_already_active PASSED
tests/test_market_data_client.py::TestRealTimePolling::test_start_real_time_polling_invalid_symbols PASSED
tests/test_market_data_client.py::TestRealTimePolling::test_stop_real_time_polling_success PASSED
tests/test_market_data_client.py::TestRealTimePolling::test_stop_real_time_polling_not_active PASSED
tests/test_market_data_client.py::TestRealTimePolling::test_add_polling_callback_success PASSED
tests/test_market_data_client.py::TestRealTimePolling::test_add_polling_callback_duplicate PASSED
tests/test_market_data_client.py::TestCacheManagement::test_get_cached_prices PASSED
tests/test_market_data_client.py::TestCacheManagement::test_clear_cache PASSED
tests/test_market_data_client.py::TestCacheManagement::test_cache_validity_check PASSED
tests/test_market_data_client.py::TestErrorHandling::test_polling_loop_error_handling PASSED
tests/test_market_data_client.py::TestErrorHandling::test_async_callback_handling PASSED

========================== 27 passed in 44.99s ===========================
```

## Success Criteria ✅

Phase 2 Step 2 is complete when:

- [x] All 27 MarketDataClient tests pass
- [x] All 22 BaseClient tests still pass (compatibility verified)
- [x] Dashboard integration imports work correctly
- [x] Circuit breaker and retry logic functional
- [x] Real-time polling system operational
- [x] Caching system working with TTL
- [x] Async/await support fully implemented
- [x] Memory usage is reasonable and stable
- [x] All code committed to git repository

## Next Steps

With Phase 2 Step 2 completed, proceed to:

- **Phase 2 Step 3**: API Response Models implementation
- **Phase 2 Step 4**: Health Monitoring System

---

**Status**: ✅ Phase 2 Step 2 Complete - Market Data Agent Integration successful with comprehensive testing and enterprise-level features.
