"""
Real-time Data Manager for Trading Dashboard.

This module provides real-time data streaming capabilities for financial charts
including WebSocket connections, HTTP polling fallback, and smooth data updates.
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import threading
from queue import Queue
import pandas as pd

# Mock WebSocket client for demonstration
class MockWebSocketClient:
    """Mock WebSocket client for demonstration purposes."""

    def __init__(self, uri: str):
        self.uri = uri
        self.connected = False
        self.callbacks = []

    async def connect(self):
        """Connect to WebSocket (mock implementation)."""
        await asyncio.sleep(0.1)  # Simulate connection time
        self.connected = True

    async def disconnect(self):
        """Disconnect from WebSocket."""
        self.connected = False

    def add_callback(self, callback: Callable):
        """Add callback for incoming messages."""
        self.callbacks.append(callback)

    async def send_message(self, message: dict):
        """Send message through WebSocket."""
        if not self.connected:
            raise ConnectionError("WebSocket not connected")
        # Mock implementation - in real version would send to server
        pass


class ConnectionStatus(Enum):
    """Connection status enumeration."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    ERROR = "error"


class UpdateMode(Enum):
    """Data update mode enumeration."""
    WEBSOCKET = "websocket"
    POLLING = "polling"
    HYBRID = "hybrid"


@dataclass
class StreamConfig:
    """Configuration for real-time data streaming."""
    symbols: List[str] = field(default_factory=lambda: ["AAPL", "GOOGL", "MSFT"])
    update_interval: float = 1.0  # seconds
    max_data_points: int = 1000
    enable_animations: bool = True
    websocket_url: Optional[str] = None
    polling_url: Optional[str] = None
    mode: UpdateMode = UpdateMode.HYBRID
    reconnect_attempts: int = 5
    reconnect_delay: float = 5.0
    buffer_size: int = 100


@dataclass
class MarketDataPoint:
    """Single market data point."""
    symbol: str
    timestamp: datetime
    price: float
    volume: int
    change: float
    change_percent: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'symbol': self.symbol,
            'timestamp': self.timestamp.isoformat(),
            'price': self.price,
            'volume': self.volume,
            'change': self.change,
            'change_percent': self.change_percent
        }


@dataclass
class ConnectionMetrics:
    """Connection performance metrics."""
    connected_since: Optional[datetime] = None
    total_messages: int = 0
    messages_per_second: float = 0.0
    last_message_time: Optional[datetime] = None
    error_count: int = 0
    reconnect_count: int = 0
    average_latency: float = 0.0

    def update_message_stats(self, message_time: datetime):
        """Update message statistics."""
        self.total_messages += 1
        self.last_message_time = message_time

        if self.connected_since:
            duration = (message_time - self.connected_since).total_seconds()
            if duration > 0:
                self.messages_per_second = self.total_messages / duration


class RealTimeDataManager:
    """Manages real-time data streaming for trading dashboard."""

    def __init__(self, config: Optional[StreamConfig] = None):
        """Initialize real-time data manager."""
        self.config = config or StreamConfig()
        self.logger = logging.getLogger(__name__)

        # Connection management
        self.status = ConnectionStatus.DISCONNECTED
        self.websocket_client: Optional[MockWebSocketClient] = None
        self.metrics = ConnectionMetrics()

        # Data management
        self.data_buffer: Queue = Queue(maxsize=self.config.buffer_size)
        self.current_data: Dict[str, MarketDataPoint] = {}
        self.historical_data: Dict[str, List[MarketDataPoint]] = {}

        # Callback management
        self.data_callbacks: List[Callable[[Dict[str, MarketDataPoint]], None]] = []
        self.status_callbacks: List[Callable[[ConnectionStatus], None]] = []

        # Threading and control
        self.streaming_task: Optional[asyncio.Task] = None
        self.polling_task: Optional[asyncio.Task] = None
        self.is_streaming = False
        self.stop_event = asyncio.Event()

        self.logger.info(f"RealTimeDataManager initialized with mode: {self.config.mode}")

    def add_data_callback(self, callback: Callable[[Dict[str, MarketDataPoint]], None]):
        """Add callback for data updates."""
        self.data_callbacks.append(callback)
        self.logger.debug(f"Added data callback: {callback.__name__}")

    def add_status_callback(self, callback: Callable[[ConnectionStatus], None]):
        """Add callback for status updates."""
        self.status_callbacks.append(callback)
        self.logger.debug(f"Added status callback: {callback.__name__}")

    def _update_status(self, new_status: ConnectionStatus):
        """Update connection status and notify callbacks."""
        if self.status != new_status:
            self.logger.info(f"Status changed: {self.status} -> {new_status}")
            self.status = new_status

            # Update metrics
            if new_status == ConnectionStatus.CONNECTED and not self.metrics.connected_since:
                self.metrics.connected_since = datetime.now()
            elif new_status == ConnectionStatus.DISCONNECTED:
                self.metrics.connected_since = None

            # Notify callbacks
            for callback in self.status_callbacks:
                try:
                    callback(new_status)
                except Exception as e:
                    self.logger.error(f"Status callback error: {e}")

    def _notify_data_callbacks(self, data: Dict[str, MarketDataPoint]):
        """Notify all data callbacks with new data."""
        for callback in self.data_callbacks:
            try:
                callback(data)
            except Exception as e:
                self.logger.error(f"Data callback error: {e}")

    async def start_streaming(self) -> bool:
        """Start real-time data streaming."""
        if self.is_streaming:
            self.logger.warning("Streaming already active")
            return True

        self.logger.info(f"Starting real-time streaming with mode: {self.config.mode}")
        self.is_streaming = True
        self.stop_event.clear()

        try:
            if self.config.mode in [UpdateMode.WEBSOCKET, UpdateMode.HYBRID]:
                await self._start_websocket_streaming()

            if self.config.mode in [UpdateMode.POLLING, UpdateMode.HYBRID]:
                await self._start_polling_streaming()

            return True

        except Exception as e:
            self.logger.error(f"Failed to start streaming: {e}")
            self.is_streaming = False
            self._update_status(ConnectionStatus.ERROR)
            return False

    async def stop_streaming(self):
        """Stop real-time data streaming."""
        if not self.is_streaming:
            return

        self.logger.info("Stopping real-time streaming")
        self.is_streaming = False
        self.stop_event.set()

        # Stop WebSocket connection
        if self.websocket_client:
            await self.websocket_client.disconnect()
            self.websocket_client = None

        # Cancel tasks
        if self.streaming_task and not self.streaming_task.done():
            self.streaming_task.cancel()
        if self.polling_task and not self.polling_task.done():
            self.polling_task.cancel()

        self._update_status(ConnectionStatus.DISCONNECTED)
        self.logger.info("Real-time streaming stopped")

    async def _start_websocket_streaming(self):
        """Start WebSocket streaming."""
        if not self.config.websocket_url:
            self.logger.warning("WebSocket URL not configured, using mock client")
            self.config.websocket_url = "ws://localhost:8765/market-data"

        try:
            self._update_status(ConnectionStatus.CONNECTING)
            self.websocket_client = MockWebSocketClient(self.config.websocket_url)

            await self.websocket_client.connect()
            self.websocket_client.add_callback(self._handle_websocket_message)

            self._update_status(ConnectionStatus.CONNECTED)
            self.logger.info("WebSocket connection established")

            # Start WebSocket message loop
            self.streaming_task = asyncio.create_task(self._websocket_message_loop())

        except Exception as e:
            self.logger.error(f"WebSocket connection failed: {e}")
            self._update_status(ConnectionStatus.ERROR)

            # Fall back to polling if hybrid mode
            if self.config.mode == UpdateMode.HYBRID:
                self.logger.info("Falling back to polling mode")
                await self._start_polling_streaming()

    async def _start_polling_streaming(self):
        """Start HTTP polling streaming."""
        self.logger.info("Starting HTTP polling mode")
        self.polling_task = asyncio.create_task(self._polling_loop())

    async def _websocket_message_loop(self):
        """WebSocket message processing loop."""
        while self.is_streaming and not self.stop_event.is_set():
            try:
                # Mock receiving WebSocket messages
                await asyncio.sleep(self.config.update_interval)

                # Generate mock data (in real implementation, this would be actual WebSocket data)
                mock_data = self._generate_mock_market_data()
                await self._handle_websocket_message(mock_data)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"WebSocket message loop error: {e}")
                self.metrics.error_count += 1

                # Attempt reconnection
                if self.metrics.error_count < self.config.reconnect_attempts:
                    await self._attempt_reconnection()
                else:
                    self._update_status(ConnectionStatus.ERROR)
                    break

    async def _polling_loop(self):
        """HTTP polling loop."""
        while self.is_streaming and not self.stop_event.is_set():
            try:
                # Generate mock data (in real implementation, this would be HTTP API call)
                mock_data = self._generate_mock_market_data()
                await self._process_market_data(mock_data)

                await asyncio.sleep(self.config.update_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Polling loop error: {e}")
                self.metrics.error_count += 1
                await asyncio.sleep(self.config.reconnect_delay)

    async def _handle_websocket_message(self, message: Dict[str, Any]):
        """Handle incoming WebSocket message."""
        try:
            await self._process_market_data(message)
            self.metrics.update_message_stats(datetime.now())

        except Exception as e:
            self.logger.error(f"Error processing WebSocket message: {e}")
            self.metrics.error_count += 1

    async def _process_market_data(self, data: Dict[str, Any]):
        """Process incoming market data."""
        try:
            # Convert raw data to MarketDataPoint objects
            processed_data = {}

            for symbol in self.config.symbols:
                if symbol in data:
                    point_data = data[symbol]
                    data_point = MarketDataPoint(
                        symbol=symbol,
                        timestamp=datetime.fromisoformat(point_data['timestamp']),
                        price=float(point_data['price']),
                        volume=int(point_data['volume']),
                        change=float(point_data['change']),
                        change_percent=float(point_data['change_percent'])
                    )

                    processed_data[symbol] = data_point
                    self.current_data[symbol] = data_point

                    # Add to historical data
                    if symbol not in self.historical_data:
                        self.historical_data[symbol] = []

                    self.historical_data[symbol].append(data_point)

                    # Maintain max data points limit
                    if len(self.historical_data[symbol]) > self.config.max_data_points:
                        self.historical_data[symbol] = self.historical_data[symbol][-self.config.max_data_points:]

            # Notify callbacks
            if processed_data:
                self._notify_data_callbacks(processed_data)

        except Exception as e:
            self.logger.error(f"Error processing market data: {e}")

    async def _attempt_reconnection(self):
        """Attempt to reconnect WebSocket."""
        self._update_status(ConnectionStatus.RECONNECTING)
        self.logger.info(f"Attempting reconnection (attempt {self.metrics.reconnect_count + 1})")

        await asyncio.sleep(self.config.reconnect_delay)

        try:
            if self.websocket_client:
                await self.websocket_client.disconnect()

            await self._start_websocket_streaming()
            self.metrics.reconnect_count += 1

        except Exception as e:
            self.logger.error(f"Reconnection failed: {e}")

    def _generate_mock_market_data(self) -> Dict[str, Any]:
        """Generate mock market data for testing."""
        import random

        data = {}
        current_time = datetime.now()

        for symbol in self.config.symbols:
            # Get last price or start with random base
            if symbol in self.current_data:
                last_price = self.current_data[symbol].price
            else:
                last_price = random.uniform(100, 300)

            # Generate realistic price movement
            change_percent = random.uniform(-2.0, 2.0)  # ±2% change
            change = last_price * (change_percent / 100)
            new_price = last_price + change
            new_price = max(0.01, new_price)  # Ensure positive price

            volume = random.randint(1000, 50000)

            data[symbol] = {
                'timestamp': current_time.isoformat(),
                'price': round(new_price, 2),
                'volume': volume,
                'change': round(change, 2),
                'change_percent': round(change_percent, 2)
            }

        return data

    def get_current_data(self) -> Dict[str, MarketDataPoint]:
        """Get current market data for all symbols."""
        return self.current_data.copy()

    def get_historical_data(self, symbol: str, limit: Optional[int] = None) -> List[MarketDataPoint]:
        """Get historical data for a specific symbol."""
        if symbol not in self.historical_data:
            return []

        data = self.historical_data[symbol]
        if limit:
            return data[-limit:]
        return data.copy()

    def get_connection_metrics(self) -> ConnectionMetrics:
        """Get connection performance metrics."""
        return self.metrics

    def update_config(self, new_config: StreamConfig):
        """Update streaming configuration."""
        self.logger.info("Updating streaming configuration")
        self.config = new_config

        # If streaming is active, restart with new config
        if self.is_streaming:
            self.logger.info("Restarting streaming with new configuration")
            asyncio.create_task(self._restart_streaming())

    async def _restart_streaming(self):
        """Restart streaming with updated configuration."""
        await self.stop_streaming()
        await asyncio.sleep(1)  # Brief pause
        await self.start_streaming()


class StreamingDataCache:
    """Cache for streaming data with TTL and size limits."""

    def __init__(self, max_size: int = 10000, ttl_seconds: int = 3600):
        """Initialize cache."""
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.timestamps: Dict[str, datetime] = {}
        self.logger = logging.getLogger(__name__)

    def put(self, key: str, data: Any):
        """Store data in cache."""
        current_time = datetime.now()

        # Clean expired entries
        self._cleanup_expired(current_time)

        # Remove oldest if at capacity
        if len(self.cache) >= self.max_size:
            self._remove_oldest()

        self.cache[key] = data
        self.timestamps[key] = current_time

    def get(self, key: str) -> Optional[Any]:
        """Retrieve data from cache."""
        if key not in self.cache:
            return None

        # Check if expired
        if self._is_expired(key):
            self._remove(key)
            return None

        return self.cache[key]

    def _is_expired(self, key: str) -> bool:
        """Check if cache entry is expired."""
        if key not in self.timestamps:
            return True

        age = (datetime.now() - self.timestamps[key]).total_seconds()
        return age > self.ttl_seconds

    def _cleanup_expired(self, current_time: datetime):
        """Remove expired cache entries."""
        expired_keys = []

        for key, timestamp in self.timestamps.items():
            if (current_time - timestamp).total_seconds() > self.ttl_seconds:
                expired_keys.append(key)

        for key in expired_keys:
            self._remove(key)

    def _remove_oldest(self):
        """Remove oldest cache entry."""
        if not self.timestamps:
            return

        oldest_key = min(self.timestamps.keys(), key=lambda k: self.timestamps[k])
        self._remove(oldest_key)

    def _remove(self, key: str):
        """Remove cache entry."""
        self.cache.pop(key, None)
        self.timestamps.pop(key, None)

    def clear(self):
        """Clear all cache entries."""
        self.cache.clear()
        self.timestamps.clear()

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            'size': len(self.cache),
            'max_size': self.max_size,
            'ttl_seconds': self.ttl_seconds,
            'oldest_entry': min(self.timestamps.values()) if self.timestamps else None
        }