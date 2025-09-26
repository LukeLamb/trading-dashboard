"""
Performance Optimization System for Real-time Trading Dashboard.

This module provides data windowing, aggregation, and memory management
for efficient handling of large financial datasets.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import threading
import time
from collections import deque, defaultdict
import psutil
import gc
import weakref

from src.dashboard.components.realtime_data import MarketDataPoint


class TimeframeResolution(Enum):
    """Timeframe resolution options."""
    TICK = "tick"           # Raw tick data
    SECOND = "1s"           # 1-second bars
    MINUTE = "1m"           # 1-minute bars
    FIVE_MINUTES = "5m"     # 5-minute bars
    FIFTEEN_MINUTES = "15m" # 15-minute bars
    HOUR = "1h"             # 1-hour bars
    DAILY = "1d"            # Daily bars


class AggregationMethod(Enum):
    """Data aggregation methods."""
    OHLC = "ohlc"           # Open, High, Low, Close
    MEAN = "mean"           # Average values
    LAST = "last"           # Last value only
    MAX = "max"             # Maximum value
    MIN = "min"             # Minimum value
    SUM = "sum"             # Sum of values
    VWAP = "vwap"           # Volume Weighted Average Price


@dataclass
class PerformanceConfig:
    """Configuration for performance optimization."""
    max_memory_mb: int = 512
    max_data_points: int = 10000
    window_size: int = 1000
    aggregation_threshold: int = 5000
    cleanup_interval: int = 300  # seconds
    enable_compression: bool = True
    use_memory_mapping: bool = False
    cache_aggregated_data: bool = True
    background_processing: bool = True
    gc_threshold: int = 1000  # Number of operations before garbage collection


@dataclass
class DataWindow:
    """Sliding window for time-series data."""
    symbol: str
    timeframe: TimeframeResolution
    max_size: int
    data: deque = field(default_factory=deque)
    aggregated_data: Dict[str, deque] = field(default_factory=dict)
    last_aggregation: Optional[datetime] = None
    total_points_added: int = 0

    def __post_init__(self):
        """Initialize aggregated data containers."""
        for method in AggregationMethod:
            self.aggregated_data[method.value] = deque(maxlen=self.max_size)


class PerformanceOptimizer:
    """Optimizes performance for real-time financial data processing."""

    def __init__(self, config: Optional[PerformanceConfig] = None):
        """Initialize performance optimizer."""
        self.config = config or PerformanceConfig()
        self.data_windows: Dict[str, DataWindow] = {}
        self.aggregation_cache: Dict[str, Dict[str, Any]] = {}
        self.memory_monitor = MemoryMonitor(self.config.max_memory_mb)

        # Performance statistics
        self.stats = {
            'total_operations': 0,
            'aggregations_performed': 0,
            'memory_cleanups': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'processing_times': deque(maxlen=1000),
            'memory_usage_history': deque(maxlen=100)
        }

        # Background processing
        self.background_task: Optional[asyncio.Task] = None
        self.is_running = False
        self._lock = threading.Lock()

        # Start background monitoring if enabled
        if self.config.background_processing:
            asyncio.create_task(self.start_background_processing())

    async def start_background_processing(self):
        """Start background performance optimization tasks."""
        self.is_running = True
        self.background_task = asyncio.create_task(self._background_optimization_loop())

    async def stop_background_processing(self):
        """Stop background processing."""
        self.is_running = False
        if self.background_task and not self.background_task.done():
            self.background_task.cancel()

    async def _background_optimization_loop(self):
        """Background loop for continuous optimization."""
        while self.is_running:
            try:
                # Memory monitoring and cleanup
                await self._perform_memory_cleanup()

                # Garbage collection if needed
                if self.stats['total_operations'] % self.config.gc_threshold == 0:
                    gc.collect()

                # Update memory usage statistics
                current_memory = self.memory_monitor.get_current_usage()
                self.stats['memory_usage_history'].append({
                    'timestamp': datetime.now(),
                    'memory_mb': current_memory
                })

                # Sleep before next iteration
                await asyncio.sleep(self.config.cleanup_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Background optimization error: {e}")
                await asyncio.sleep(60)  # Wait before retrying

    def create_data_window(self, symbol: str, timeframe: TimeframeResolution,
                          max_size: Optional[int] = None) -> str:
        """Create a data window for a symbol and timeframe."""
        window_id = f"{symbol}_{timeframe.value}"
        max_size = max_size or self.config.window_size

        self.data_windows[window_id] = DataWindow(
            symbol=symbol,
            timeframe=timeframe,
            max_size=max_size
        )

        return window_id

    def add_data_point(self, window_id: str, data_point: MarketDataPoint) -> bool:
        """Add data point to window with optimization."""
        if window_id not in self.data_windows:
            return False

        start_time = time.time()

        with self._lock:
            window = self.data_windows[window_id]

            # Add to raw data window
            window.data.append(data_point)
            window.total_points_added += 1

            # Check if aggregation is needed
            if (len(window.data) >= self.config.aggregation_threshold and
                (window.last_aggregation is None or
                 (datetime.now() - window.last_aggregation).seconds >= 60)):

                self._perform_aggregation(window)
                window.last_aggregation = datetime.now()
                self.stats['aggregations_performed'] += 1

        # Update statistics
        processing_time = time.time() - start_time
        self.stats['processing_times'].append(processing_time)
        self.stats['total_operations'] += 1

        return True

    def _perform_aggregation(self, window: DataWindow):
        """Perform data aggregation for a window."""
        if len(window.data) == 0:
            return

        # Convert to DataFrame for efficient aggregation
        df_data = []
        for point in window.data:
            df_data.append({
                'timestamp': point.timestamp,
                'price': point.price,
                'volume': point.volume,
                'change': point.change,
                'change_percent': point.change_percent
            })

        df = pd.DataFrame(df_data)
        df.set_index('timestamp', inplace=True)

        # Perform different aggregations
        aggregations = self._calculate_aggregations(df)

        # Store aggregated data
        for method, data in aggregations.items():
            if method in window.aggregated_data:
                window.aggregated_data[method].extend(data)

        # Clear raw data if we have aggregated data
        if self.config.cache_aggregated_data:
            # Keep only recent raw data
            keep_raw = max(100, len(window.data) // 10)
            window.data = deque(list(window.data)[-keep_raw:], maxlen=window.max_size)

    def _calculate_aggregations(self, df: pd.DataFrame) -> Dict[str, List[MarketDataPoint]]:
        """Calculate various aggregations of the data."""
        aggregations = {}

        # OHLC aggregation (1-minute bars)
        if len(df) > 0:
            ohlc_bars = []
            resampled = df.resample('1T').agg({
                'price': ['first', 'max', 'min', 'last'],
                'volume': 'sum',
                'change': 'last',
                'change_percent': 'last'
            }).dropna()

            for timestamp, row in resampled.iterrows():
                ohlc_bars.append(MarketDataPoint(
                    symbol=df.index[0] if hasattr(df.index[0], 'symbol') else 'UNKNOWN',
                    timestamp=timestamp,
                    price=row[('price', 'last')],
                    volume=int(row[('volume', 'sum')]),
                    change=row[('change', 'last')],
                    change_percent=row[('change_percent', 'last')]
                ))

            aggregations['ohlc'] = ohlc_bars

        # Mean aggregation
        if len(df) > 0:
            mean_data = []
            mean_resampled = df.resample('1T').mean().dropna()

            for timestamp, row in mean_resampled.iterrows():
                mean_data.append(MarketDataPoint(
                    symbol='UNKNOWN',
                    timestamp=timestamp,
                    price=row['price'],
                    volume=int(row['volume']),
                    change=row['change'],
                    change_percent=row['change_percent']
                ))

            aggregations['mean'] = mean_data

        return aggregations

    def get_optimized_data(self, window_id: str, max_points: Optional[int] = None,
                          aggregation_method: Optional[AggregationMethod] = None) -> List[MarketDataPoint]:
        """Get optimized data from window."""
        if window_id not in self.data_windows:
            return []

        window = self.data_windows[window_id]
        max_points = max_points or self.config.max_data_points

        # Use aggregated data if available and beneficial
        if (aggregation_method and
            aggregation_method.value in window.aggregated_data and
            len(window.aggregated_data[aggregation_method.value]) > 0):

            data_source = list(window.aggregated_data[aggregation_method.value])
            self.stats['cache_hits'] += 1
        else:
            data_source = list(window.data)
            self.stats['cache_misses'] += 1

        # Apply data windowing
        if len(data_source) > max_points:
            # Use intelligent sampling
            return self._intelligent_sampling(data_source, max_points)
        else:
            return data_source

    def _intelligent_sampling(self, data: List[MarketDataPoint], target_size: int) -> List[MarketDataPoint]:
        """Intelligently sample data to reduce size while preserving important features."""
        if len(data) <= target_size:
            return data

        # Use pandas for efficient resampling
        df_data = []
        for point in data:
            df_data.append({
                'timestamp': point.timestamp,
                'price': point.price,
                'volume': point.volume,
                'change': point.change,
                'change_percent': point.change_percent,
                'symbol': point.symbol
            })

        df = pd.DataFrame(df_data)
        df.set_index('timestamp', inplace=True)

        # Calculate sampling interval
        total_duration = (df.index[-1] - df.index[0]).total_seconds()
        target_interval = max(1, total_duration / target_size)

        # Resample to target size
        resampled = df.resample(f'{int(target_interval)}s').agg({
            'price': 'last',
            'volume': 'sum',
            'change': 'last',
            'change_percent': 'last',
            'symbol': 'last'
        }).dropna()

        # Convert back to MarketDataPoint objects
        sampled_data = []
        for timestamp, row in resampled.iterrows():
            sampled_data.append(MarketDataPoint(
                symbol=row['symbol'],
                timestamp=timestamp,
                price=row['price'],
                volume=int(row['volume']),
                change=row['change'],
                change_percent=row['change_percent']
            ))

        return sampled_data

    async def _perform_memory_cleanup(self):
        """Perform memory cleanup operations."""
        current_memory = self.memory_monitor.get_current_usage()

        if current_memory > self.config.max_memory_mb * 0.8:  # 80% threshold
            with self._lock:
                # Clean up old data windows
                for window_id, window in list(self.data_windows.items()):
                    if len(window.data) > self.config.window_size:
                        # Reduce window size
                        keep_size = self.config.window_size // 2
                        window.data = deque(list(window.data)[-keep_size:], maxlen=window.max_size)

                # Clear old cache entries
                self._cleanup_cache()

                # Force garbage collection
                gc.collect()

                self.stats['memory_cleanups'] += 1

    def _cleanup_cache(self):
        """Clean up aggregation cache."""
        if len(self.aggregation_cache) > 100:  # Arbitrary limit
            # Keep only recent cache entries
            sorted_cache = sorted(self.aggregation_cache.items(),
                                key=lambda x: x[1].get('last_access', datetime.min))

            # Keep only the most recent 50 entries
            self.aggregation_cache = dict(sorted_cache[-50:])

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        current_memory = self.memory_monitor.get_current_usage()
        avg_processing_time = (np.mean(self.stats['processing_times'])
                              if self.stats['processing_times'] else 0)

        return {
            'current_memory_mb': current_memory,
            'max_memory_mb': self.config.max_memory_mb,
            'memory_usage_percent': (current_memory / self.config.max_memory_mb) * 100,
            'total_operations': self.stats['total_operations'],
            'aggregations_performed': self.stats['aggregations_performed'],
            'memory_cleanups': self.stats['memory_cleanups'],
            'cache_hit_rate': (self.stats['cache_hits'] /
                              (self.stats['cache_hits'] + self.stats['cache_misses'])
                              if (self.stats['cache_hits'] + self.stats['cache_misses']) > 0 else 0),
            'average_processing_time_ms': avg_processing_time * 1000,
            'active_windows': len(self.data_windows),
            'total_data_points': sum(len(w.data) for w in self.data_windows.values()),
            'background_processing': self.is_running
        }

    def optimize_for_timeframe(self, timeframe: TimeframeResolution) -> Dict[str, Any]:
        """Optimize configuration for specific timeframe."""
        optimization_settings = {}

        if timeframe == TimeframeResolution.TICK:
            optimization_settings = {
                'max_data_points': 1000,
                'window_size': 500,
                'aggregation_threshold': 1000,
                'cleanup_interval': 60
            }
        elif timeframe in [TimeframeResolution.SECOND, TimeframeResolution.MINUTE]:
            optimization_settings = {
                'max_data_points': 5000,
                'window_size': 2000,
                'aggregation_threshold': 3000,
                'cleanup_interval': 120
            }
        elif timeframe in [TimeframeResolution.FIVE_MINUTES, TimeframeResolution.FIFTEEN_MINUTES]:
            optimization_settings = {
                'max_data_points': 10000,
                'window_size': 5000,
                'aggregation_threshold': 7000,
                'cleanup_interval': 300
            }
        else:  # Hourly, Daily
            optimization_settings = {
                'max_data_points': 50000,
                'window_size': 20000,
                'aggregation_threshold': 30000,
                'cleanup_interval': 600
            }

        return optimization_settings

    def clear_window(self, window_id: str):
        """Clear specific data window."""
        if window_id in self.data_windows:
            with self._lock:
                del self.data_windows[window_id]

    def clear_all_windows(self):
        """Clear all data windows."""
        with self._lock:
            self.data_windows.clear()
            self.aggregation_cache.clear()
            gc.collect()


class MemoryMonitor:
    """Monitors memory usage for the application."""

    def __init__(self, max_memory_mb: int):
        """Initialize memory monitor."""
        self.max_memory_mb = max_memory_mb
        self.process = psutil.Process()
        self.memory_history = deque(maxlen=100)

    def get_current_usage(self) -> float:
        """Get current memory usage in MB."""
        try:
            memory_info = self.process.memory_info()
            memory_mb = memory_info.rss / (1024 * 1024)  # Convert to MB

            self.memory_history.append({
                'timestamp': datetime.now(),
                'memory_mb': memory_mb
            })

            return memory_mb
        except Exception:
            return 0.0

    def is_memory_critical(self) -> bool:
        """Check if memory usage is critical."""
        current_usage = self.get_current_usage()
        return current_usage > self.max_memory_mb * 0.9  # 90% threshold

    def get_memory_trend(self) -> Dict[str, float]:
        """Get memory usage trend."""
        if len(self.memory_history) < 2:
            return {'trend': 0.0, 'current': self.get_current_usage()}

        recent_data = list(self.memory_history)[-10:]  # Last 10 readings
        memory_values = [entry['memory_mb'] for entry in recent_data]

        # Simple linear trend calculation
        x = np.arange(len(memory_values))
        if len(memory_values) > 1:
            slope = np.polyfit(x, memory_values, 1)[0]
        else:
            slope = 0.0

        return {
            'trend': slope,  # MB per reading
            'current': memory_values[-1] if memory_values else 0.0,
            'average': np.mean(memory_values) if memory_values else 0.0,
            'peak': max(memory_values) if memory_values else 0.0
        }


class DataCompressor:
    """Compresses financial data for efficient storage."""

    @staticmethod
    def compress_price_data(data: List[MarketDataPoint]) -> Dict[str, Any]:
        """Compress price data using delta encoding and quantization."""
        if not data:
            return {}

        # Sort by timestamp
        sorted_data = sorted(data, key=lambda x: x.timestamp)

        # Delta encode prices and volumes
        base_price = sorted_data[0].price
        base_volume = sorted_data[0].volume
        base_timestamp = sorted_data[0].timestamp

        compressed = {
            'base_price': base_price,
            'base_volume': base_volume,
            'base_timestamp': base_timestamp.isoformat(),
            'symbol': sorted_data[0].symbol,
            'deltas': []
        }

        for i, point in enumerate(sorted_data):
            if i == 0:
                continue  # Skip first point as it's the base

            time_delta = (point.timestamp - base_timestamp).total_seconds()
            price_delta = point.price - base_price
            volume_delta = point.volume - base_volume

            compressed['deltas'].append({
                'time': int(time_delta),
                'price': round(price_delta, 4),
                'volume': volume_delta,
                'change': point.change,
                'change_percent': round(point.change_percent, 2)
            })

        return compressed

    @staticmethod
    def decompress_price_data(compressed: Dict[str, Any]) -> List[MarketDataPoint]:
        """Decompress price data."""
        if not compressed or 'deltas' not in compressed:
            return []

        base_timestamp = datetime.fromisoformat(compressed['base_timestamp'])
        base_price = compressed['base_price']
        base_volume = compressed['base_volume']
        symbol = compressed['symbol']

        # First point
        data = [MarketDataPoint(
            symbol=symbol,
            timestamp=base_timestamp,
            price=base_price,
            volume=base_volume,
            change=0.0,
            change_percent=0.0
        )]

        # Decompress deltas
        for delta in compressed['deltas']:
            timestamp = base_timestamp + timedelta(seconds=delta['time'])
            price = base_price + delta['price']
            volume = base_volume + delta['volume']

            data.append(MarketDataPoint(
                symbol=symbol,
                timestamp=timestamp,
                price=price,
                volume=volume,
                change=delta['change'],
                change_percent=delta['change_percent']
            ))

        return data