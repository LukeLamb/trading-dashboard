"""
Market Data Agent Client for Trading Dashboard.

This module provides a specialized client for communicating with the Market Data Agent,
handling price data retrieval, source status monitoring, and real-time data polling.
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass
import json

from .base_client import BaseClient, HealthStatus
from ..utils.logging import get_logger
from ..utils.validation import DataValidator
from ..utils.formatting import DataFormatter


@dataclass
class PriceData:
    """Price data model."""
    symbol: str
    price: float
    timestamp: datetime
    source: str
    quality_grade: str = "A"
    bid: Optional[float] = None
    ask: Optional[float] = None
    volume: Optional[int] = None
    change_24h: Optional[float] = None
    change_percent_24h: Optional[float] = None


@dataclass
class SourceStatus:
    """Data source status model."""
    name: str
    status: str
    last_update: datetime
    quality_grade: str
    error_count: int = 0
    response_time_ms: Optional[float] = None


@dataclass
class MarketDataHealth:
    """Market Data Agent health status."""
    status: HealthStatus
    uptime: timedelta
    active_sources: int
    total_sources: int
    avg_response_time: float
    data_points_per_minute: int
    overall_quality_grade: str
    errors_last_hour: int


class MarketDataClient(BaseClient):
    """
    Client for Market Data Agent communication.

    Provides methods for price retrieval, source monitoring, and real-time data polling
    with built-in caching, retry logic, and circuit breaker protection.
    """

    def __init__(self, base_url: str, timeout: int = 10, **kwargs):
        """
        Initialize Market Data Agent client.

        Args:
            base_url: Base URL of the Market Data Agent
            timeout: Request timeout in seconds
            **kwargs: Additional configuration passed to BaseClient
        """
        super().__init__(base_url=base_url, timeout=timeout, **kwargs)
        self.logger = get_logger(f"{self.__class__.__name__}")
        self.validator = DataValidator()
        self.formatter = DataFormatter()

        # Cache for price data to reduce API calls
        self._price_cache: Dict[str, PriceData] = {}
        self._cache_ttl = 5  # Cache TTL in seconds
        self._last_cache_update: Dict[str, datetime] = {}

        # Real-time polling configuration
        self._polling_active = False
        self._polling_interval = 1.0  # seconds
        self._polling_symbols: List[str] = []
        self._polling_callbacks: List[callable] = []

    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on Market Data Agent.

        Returns:
            Health status information
        """
        try:
            self.logger.debug("Performing health check on Market Data Agent")
            response = await self.get("/health")

            if response and isinstance(response, dict):
                # Parse health response
                health_data = MarketDataHealth(
                    status=HealthStatus(response.get("status", "unknown")),
                    uptime=timedelta(seconds=response.get("uptime_seconds", 0)),
                    active_sources=response.get("active_sources", 0),
                    total_sources=response.get("total_sources", 0),
                    avg_response_time=response.get("avg_response_time_ms", 0.0),
                    data_points_per_minute=response.get("data_points_per_minute", 0),
                    overall_quality_grade=response.get("overall_quality_grade", "F"),
                    errors_last_hour=response.get("errors_last_hour", 0)
                )

                self.logger.info(f"Market Data Agent health: {health_data.status.value}")
                return {
                    "healthy": health_data.status == HealthStatus.HEALTHY,
                    "status": health_data.status.value,
                    "details": health_data.__dict__
                }

            return {"healthy": False, "status": "unknown", "error": "Invalid health response"}

        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return {"healthy": False, "status": "error", "error": str(e)}

    async def get_current_price(self, symbol: str, force_refresh: bool = False) -> Optional[PriceData]:
        """
        Get current price for a symbol.

        Args:
            symbol: Trading symbol (e.g., 'BTCUSD', 'EURUSD')
            force_refresh: Skip cache and fetch fresh data

        Returns:
            PriceData object or None if failed
        """
        try:
            # Validate symbol
            if not self.validator.validate_trading_symbol(symbol):
                self.logger.warning(f"Invalid trading symbol: {symbol}")
                return None

            # Check cache first (unless force refresh)
            if not force_refresh and self._is_cache_valid(symbol):
                self.logger.debug(f"Returning cached price for {symbol}")
                return self._price_cache[symbol]

            self.logger.debug(f"Fetching current price for {symbol}")
            response = await self.get(f"/price/{symbol}")

            if response and isinstance(response, dict):
                price_data = PriceData(
                    symbol=response.get("symbol", symbol),
                    price=float(response.get("price", 0)),
                    timestamp=datetime.fromisoformat(response.get("timestamp", datetime.now().isoformat())),
                    source=response.get("source", "unknown"),
                    quality_grade=response.get("quality_grade", "F"),
                    bid=response.get("bid"),
                    ask=response.get("ask"),
                    volume=response.get("volume"),
                    change_24h=response.get("change_24h"),
                    change_percent_24h=response.get("change_percent_24h")
                )

                # Update cache
                self._price_cache[symbol] = price_data
                self._last_cache_update[symbol] = datetime.now()

                self.logger.info(f"Retrieved price for {symbol}: {self.formatter.format_currency(price_data.price)} (Grade: {price_data.quality_grade})")
                return price_data

            self.logger.warning(f"No price data available for {symbol}")
            return None

        except Exception as e:
            self.logger.error(f"Failed to get current price for {symbol}: {e}")
            return None

    async def get_historical_prices(self, symbol: str, timeframe: str = "1h",
                                  limit: int = 100) -> List[PriceData]:
        """
        Get historical price data for a symbol.

        Args:
            symbol: Trading symbol
            timeframe: Time frame (1m, 5m, 15m, 1h, 4h, 1d)
            limit: Number of data points to retrieve

        Returns:
            List of PriceData objects
        """
        try:
            if not self.validator.validate_trading_symbol(symbol):
                self.logger.warning(f"Invalid trading symbol: {symbol}")
                return []

            params = {
                "timeframe": timeframe,
                "limit": min(limit, 1000)  # Cap at 1000 for performance
            }

            self.logger.debug(f"Fetching historical data for {symbol} ({timeframe}, {limit} points)")
            response = await self.get(f"/historical/{symbol}", params=params)

            if response and isinstance(response, dict) and "data" in response:
                historical_data = []
                for item in response["data"]:
                    price_data = PriceData(
                        symbol=item.get("symbol", symbol),
                        price=float(item.get("price", 0)),
                        timestamp=datetime.fromisoformat(item.get("timestamp")),
                        source=item.get("source", "unknown"),
                        quality_grade=item.get("quality_grade", "F"),
                        bid=item.get("bid"),
                        ask=item.get("ask"),
                        volume=item.get("volume")
                    )
                    historical_data.append(price_data)

                self.logger.info(f"Retrieved {len(historical_data)} historical data points for {symbol}")
                return historical_data

            self.logger.warning(f"No historical data available for {symbol}")
            return []

        except Exception as e:
            self.logger.error(f"Failed to get historical prices for {symbol}: {e}")
            return []

    async def get_sources_status(self) -> List[SourceStatus]:
        """
        Get status of all data sources.

        Returns:
            List of SourceStatus objects
        """
        try:
            self.logger.debug("Fetching data sources status")
            response = await self.get("/sources")

            if response and isinstance(response, dict) and "sources" in response:
                sources = []
                for source_data in response["sources"]:
                    source_status = SourceStatus(
                        name=source_data.get("name", "unknown"),
                        status=source_data.get("status", "unknown"),
                        last_update=datetime.fromisoformat(source_data.get("last_update", datetime.now().isoformat())),
                        quality_grade=source_data.get("quality_grade", "F"),
                        error_count=source_data.get("error_count", 0),
                        response_time_ms=source_data.get("response_time_ms")
                    )
                    sources.append(source_status)

                self.logger.info(f"Retrieved status for {len(sources)} data sources")
                return sources

            self.logger.warning("No source status data available")
            return []

        except Exception as e:
            self.logger.error(f"Failed to get sources status: {e}")
            return []

    async def start_real_time_polling(self, symbols: List[str],
                                    callback: callable = None,
                                    interval: float = 1.0) -> bool:
        """
        Start real-time data polling for specified symbols.

        Args:
            symbols: List of symbols to poll
            callback: Optional callback function for price updates
            interval: Polling interval in seconds

        Returns:
            True if polling started successfully
        """
        try:
            if self._polling_active:
                self.logger.warning("Real-time polling already active")
                return False

            # Validate symbols
            valid_symbols = [s for s in symbols if self.validator.validate_trading_symbol(s)]
            if not valid_symbols:
                self.logger.error("No valid symbols provided for polling")
                return False

            self._polling_symbols = valid_symbols
            self._polling_interval = interval
            if callback:
                self._polling_callbacks.append(callback)

            self._polling_active = True

            # Start polling task
            asyncio.create_task(self._polling_loop())

            self.logger.info(f"Started real-time polling for {len(valid_symbols)} symbols (interval: {interval}s)")
            return True

        except Exception as e:
            self.logger.error(f"Failed to start real-time polling: {e}")
            return False

    async def stop_real_time_polling(self) -> bool:
        """
        Stop real-time data polling.

        Returns:
            True if polling stopped successfully
        """
        try:
            if not self._polling_active:
                self.logger.warning("Real-time polling not active")
                return False

            self._polling_active = False
            self._polling_symbols.clear()
            self._polling_callbacks.clear()

            self.logger.info("Stopped real-time polling")
            return True

        except Exception as e:
            self.logger.error(f"Failed to stop real-time polling: {e}")
            return False

    def add_polling_callback(self, callback: callable) -> bool:
        """
        Add callback for real-time price updates.

        Args:
            callback: Function to call with price updates

        Returns:
            True if callback added successfully
        """
        try:
            if callback not in self._polling_callbacks:
                self._polling_callbacks.append(callback)
                self.logger.debug("Added polling callback")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to add polling callback: {e}")
            return False

    def get_cached_prices(self) -> Dict[str, PriceData]:
        """
        Get all cached price data.

        Returns:
            Dictionary of cached prices
        """
        return self._price_cache.copy()

    def clear_cache(self) -> None:
        """Clear price cache."""
        self._price_cache.clear()
        self._last_cache_update.clear()
        self.logger.debug("Price cache cleared")

    # Private methods

    def _is_cache_valid(self, symbol: str) -> bool:
        """Check if cached data is still valid."""
        if symbol not in self._price_cache:
            return False

        if symbol not in self._last_cache_update:
            return False

        age = (datetime.now() - self._last_cache_update[symbol]).total_seconds()
        return age < self._cache_ttl

    async def _polling_loop(self) -> None:
        """Main polling loop for real-time data."""
        try:
            while self._polling_active:
                for symbol in self._polling_symbols:
                    if not self._polling_active:  # Check if stopped during loop
                        break

                    try:
                        price_data = await self.get_current_price(symbol, force_refresh=True)
                        if price_data:
                            # Call all registered callbacks
                            for callback in self._polling_callbacks:
                                try:
                                    await callback(price_data) if asyncio.iscoroutinefunction(callback) else callback(price_data)
                                except Exception as e:
                                    self.logger.error(f"Error in polling callback: {e}")

                    except Exception as e:
                        self.logger.error(f"Error polling {symbol}: {e}")

                # Wait before next polling cycle
                await asyncio.sleep(self._polling_interval)

        except Exception as e:
            self.logger.error(f"Polling loop error: {e}")
        finally:
            self._polling_active = False