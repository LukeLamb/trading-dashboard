"""
Real-time Charts Integration for Trading Dashboard.

This module integrates real-time data streaming, animations, and performance
optimization with the existing chart components and Market Data Agent.
"""

import streamlit as st
import asyncio
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import time
import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.dashboard.components.realtime_data import (
    RealTimeDataManager, StreamConfig, UpdateMode, ConnectionStatus
)
from src.dashboard.components.chart_animations import (
    ChartAnimationManager, AnimationConfig, RealTimeChartRenderer
)
from src.dashboard.components.performance_optimizer import (
    PerformanceOptimizer, PerformanceConfig, TimeframeResolution
)
from src.dashboard.components.charts import TradingCharts, TechnicalIndicators
from src.clients.market_data_client import MarketDataClient
from src.orchestrator import get_agent_manager


class RealTimeChartsManager:
    """Manages real-time chart updates with Market Data Agent integration."""

    def __init__(self):
        """Initialize real-time charts manager."""
        self.logger = logging.getLogger(__name__)

        # Initialize components
        self.stream_config = StreamConfig(
            symbols=["AAPL", "GOOGL", "MSFT", "TSLA", "AMZN"],
            update_interval=2.0,  # 2 second updates
            max_data_points=1000,
            enable_animations=True
        )

        self.animation_config = AnimationConfig(
            enabled=True,
            transition_duration=500,
            auto_scroll=True,
            max_visible_points=500
        )

        self.performance_config = PerformanceConfig(
            max_memory_mb=256,
            max_data_points=5000,
            window_size=1000,
            background_processing=True
        )

        # Initialize managers
        self.data_manager = RealTimeDataManager(self.stream_config)
        self.animation_manager = ChartAnimationManager(self.animation_config)
        self.performance_optimizer = PerformanceOptimizer(self.performance_config)
        self.chart_renderer = RealTimeChartRenderer(self.animation_manager)

        # Market Data Client
        self.market_data_client = None
        self.agent_manager = None

        # State management
        self.is_streaming = False
        self.current_symbols = ["AAPL", "GOOGL", "MSFT"]
        self.chart_history = {}

        self.logger.info("RealTimeChartsManager initialized")

    def initialize_market_data_connection(self) -> bool:
        """Initialize connection to Market Data Agent."""
        try:
            # Get agent manager from session state
            if 'agent_manager' in st.session_state:
                self.agent_manager = st.session_state.agent_manager

                # Check if Market Data Agent is running
                agent_status = asyncio.run(
                    self.agent_manager.get_agent_status("market_data")
                )

                if agent_status and agent_status.get('status') == 'running':
                    # Initialize Market Data Client
                    self.market_data_client = MarketDataClient()

                    # Test connection
                    health = asyncio.run(self.market_data_client.health_check())
                    if health and health.is_healthy:
                        self.logger.info("Market Data Agent connection established")
                        return True
                    else:
                        self.logger.warning("Market Data Agent health check failed")
                else:
                    self.logger.warning("Market Data Agent not running")

        except Exception as e:
            self.logger.error(f"Failed to initialize Market Data connection: {e}")

        return False

    async def start_real_time_streaming(self, symbols: List[str]) -> bool:
        """Start real-time data streaming."""
        if self.is_streaming:
            return True

        try:
            # Update symbols
            self.current_symbols = symbols
            self.stream_config.symbols = symbols

            # Create performance windows for each symbol
            for symbol in symbols:
                window_id = self.performance_optimizer.create_data_window(
                    symbol, TimeframeResolution.MINUTE, 1000
                )

            # Set up data callbacks
            self.data_manager.add_data_callback(self._handle_new_data)
            self.data_manager.add_status_callback(self._handle_status_change)

            # Start streaming
            success = await self.data_manager.start_streaming()
            if success:
                self.is_streaming = True
                self.logger.info(f"Real-time streaming started for {len(symbols)} symbols")
                return True
            else:
                self.logger.error("Failed to start real-time streaming")
                return False

        except Exception as e:
            self.logger.error(f"Error starting streaming: {e}")
            return False

    async def stop_real_time_streaming(self):
        """Stop real-time data streaming."""
        if not self.is_streaming:
            return

        try:
            await self.data_manager.stop_streaming()
            self.is_streaming = False
            self.logger.info("Real-time streaming stopped")

        except Exception as e:
            self.logger.error(f"Error stopping streaming: {e}")

    def _handle_new_data(self, data: Dict[str, Any]):
        """Handle new real-time data."""
        try:
            for symbol, data_point in data.items():
                # Add to performance optimizer
                window_id = f"{symbol}_{TimeframeResolution.MINUTE.value}"
                self.performance_optimizer.add_data_point(window_id, data_point)

                # Update chart history
                if symbol not in self.chart_history:
                    self.chart_history[symbol] = []

                self.chart_history[symbol].append(data_point)

                # Maintain history limit
                if len(self.chart_history[symbol]) > 1000:
                    self.chart_history[symbol] = self.chart_history[symbol][-1000:]

        except Exception as e:
            self.logger.error(f"Error handling new data: {e}")

    def _handle_status_change(self, status: ConnectionStatus):
        """Handle connection status changes."""
        self.logger.info(f"Connection status changed to: {status}")

        # Update UI status indicator if available
        if hasattr(st.session_state, 'streaming_status'):
            st.session_state.streaming_status = status.value

    def render_real_time_dashboard(self):
        """Render the main real-time dashboard."""
        st.markdown("## 🔴 Live Trading Dashboard")

        # Control panel
        self._render_control_panel()

        # Status indicators
        self._render_status_indicators()

        # Main charts
        if self.is_streaming or self.chart_history:
            self._render_live_charts()
        else:
            self._render_demo_charts()

        # Performance metrics
        self._render_performance_metrics()

    def _render_control_panel(self):
        """Render the streaming control panel."""
        with st.container():
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                # Start/Stop streaming
                if not self.is_streaming:
                    if st.button("▶️ Start Live Streaming", type="primary"):
                        # Check Market Data Agent connection
                        if not self.market_data_client:
                            if self.initialize_market_data_connection():
                                st.success("✅ Connected to Market Data Agent")
                            else:
                                st.warning("⚠️ Using mock data - Market Data Agent unavailable")

                        # Start streaming
                        success = asyncio.run(
                            self.start_real_time_streaming(self.current_symbols)
                        )
                        if success:
                            st.success("🔴 Live streaming started!")
                            st.rerun()
                        else:
                            st.error("❌ Failed to start streaming")
                else:
                    if st.button("⏹️ Stop Streaming", type="secondary"):
                        asyncio.run(self.stop_real_time_streaming())
                        st.success("⏹️ Streaming stopped")
                        st.rerun()

            with col2:
                # Symbol selection
                available_symbols = ["AAPL", "GOOGL", "MSFT", "TSLA", "AMZN", "NVDA", "META"]
                selected_symbols = st.multiselect(
                    "Select Symbols",
                    available_symbols,
                    default=self.current_symbols,
                    help="Choose symbols to stream"
                )

                if selected_symbols != self.current_symbols:
                    self.current_symbols = selected_symbols
                    if self.is_streaming:
                        st.info("🔄 Restart streaming to apply symbol changes")

            with col3:
                # Update interval
                update_interval = st.selectbox(
                    "Update Interval",
                    [0.5, 1.0, 2.0, 5.0],
                    index=2,
                    help="Seconds between updates"
                )

                if update_interval != self.stream_config.update_interval:
                    self.stream_config.update_interval = update_interval
                    self.data_manager.update_config(self.stream_config)

            with col4:
                # Animation toggle
                enable_animations = st.checkbox(
                    "Enable Animations",
                    value=self.animation_config.enabled,
                    help="Smooth chart transitions"
                )

                if enable_animations != self.animation_config.enabled:
                    self.animation_config.enabled = enable_animations
                    self.animation_manager.update_animation_config(self.animation_config)

    def _render_status_indicators(self):
        """Render connection and performance status."""
        col1, col2, col3, col4, col5 = st.columns(5)

        # Connection status
        with col1:
            if self.is_streaming:
                status_color = "🟢" if self.data_manager.status == ConnectionStatus.CONNECTED else "🟡"
                st.metric("Connection", f"{status_color} {self.data_manager.status.value.title()}")
            else:
                st.metric("Connection", "🔴 Stopped")

        # Data points
        with col2:
            total_points = sum(len(history) for history in self.chart_history.values())
            st.metric("Data Points", f"{total_points:,}")

        # Active symbols
        with col3:
            st.metric("Active Symbols", len(self.current_symbols))

        # Update rate
        with col4:
            if hasattr(self.data_manager, 'metrics'):
                rate = f"{self.data_manager.metrics.messages_per_second:.1f}/s"
            else:
                rate = "0.0/s"
            st.metric("Update Rate", rate)

        # Memory usage
        with col5:
            perf_stats = self.performance_optimizer.get_performance_stats()
            memory_pct = perf_stats['memory_usage_percent']
            memory_color = "🟢" if memory_pct < 70 else "🟡" if memory_pct < 90 else "🔴"
            st.metric("Memory", f"{memory_color} {memory_pct:.1f}%")

    def _render_live_charts(self):
        """Render live charts with real-time data."""
        st.markdown("### 📈 Live Charts")

        # Chart type selection
        chart_type = st.selectbox(
            "Chart Type",
            ["Candlestick", "Line", "Multi-Symbol Comparison", "Volume Analysis"],
            help="Select chart visualization type"
        )

        if chart_type == "Candlestick":
            self._render_live_candlestick_charts()
        elif chart_type == "Line":
            self._render_live_line_charts()
        elif chart_type == "Multi-Symbol Comparison":
            self._render_live_comparison_charts()
        elif chart_type == "Volume Analysis":
            self._render_live_volume_charts()

    def _render_live_candlestick_charts(self):
        """Render live candlestick charts."""
        for i, symbol in enumerate(self.current_symbols):
            if symbol in self.chart_history and self.chart_history[symbol]:
                with st.container():
                    col1, col2 = st.columns([3, 1])

                    with col1:
                        # Get optimized data
                        data_points = self.performance_optimizer.get_optimized_data(
                            f"{symbol}_{TimeframeResolution.MINUTE.value}",
                            max_points=500
                        )

                        if not data_points:
                            data_points = self.chart_history[symbol][-500:]

                        if data_points:
                            # Render live chart
                            figure = self.chart_renderer.render_live_candlestick(
                                symbol, data_points, chart_height=400
                            )
                            st.plotly_chart(figure, use_container_width=True, key=f"live_candle_{symbol}_{i}")

                    with col2:
                        # Current price and stats
                        if data_points:
                            latest_point = data_points[-1]
                            st.metric(
                                f"{symbol} Price",
                                f"${latest_point.price:.2f}",
                                f"{latest_point.change_percent:+.2f}%",
                                delta_color="normal"
                            )

                            st.metric(
                                "Volume",
                                f"{latest_point.volume:,}",
                                help="Current volume"
                            )

                            st.metric(
                                "Last Update",
                                latest_point.timestamp.strftime("%H:%M:%S"),
                                help="Time of last update"
                            )

            else:
                st.info(f"No data available for {symbol}")

    def _render_live_line_charts(self):
        """Render live line charts."""
        for symbol in self.current_symbols:
            if symbol in self.chart_history and self.chart_history[symbol]:
                data_points = self.chart_history[symbol][-500:]

                figure = self.chart_renderer.render_live_line_chart(
                    symbol, data_points, chart_height=300
                )
                st.plotly_chart(figure, use_container_width=True, key=f"live_line_{symbol}")

    def _render_live_comparison_charts(self):
        """Render multi-symbol comparison charts."""
        if len(self.current_symbols) < 2:
            st.warning("Select at least 2 symbols for comparison")
            return

        # Combine data from all symbols
        comparison_data = {}
        for symbol in self.current_symbols:
            if symbol in self.chart_history and self.chart_history[symbol]:
                comparison_data[symbol] = self.chart_history[symbol][-200:]

        if comparison_data:
            # Create normalized comparison chart
            trading_charts = TradingCharts()
            comparison_df = self._create_comparison_dataframe(comparison_data)

            if not comparison_df.empty:
                figure = trading_charts.create_price_comparison_chart(
                    comparison_df, "Live Price Comparison"
                )
                st.plotly_chart(figure, use_container_width=True)

    def _render_live_volume_charts(self):
        """Render live volume charts."""
        for symbol in self.current_symbols:
            if symbol in self.chart_history and self.chart_history[symbol]:
                data_points = self.chart_history[symbol][-200:]

                figure = self.chart_renderer.render_live_volume(
                    symbol, data_points, chart_height=250
                )
                st.plotly_chart(figure, use_container_width=True, key=f"live_volume_{symbol}")

    def _render_demo_charts(self):
        """Render demo charts when streaming is not active."""
        st.info("🎬 Live streaming is not active. Showing demo charts with simulated data.")

        # Use existing TradingCharts for demo
        trading_charts = TradingCharts()
        demo_data = trading_charts.generate_sample_data(
            symbols=self.current_symbols,
            days=30
        )

        # Render demo candlestick chart
        for symbol in self.current_symbols:
            if symbol in demo_data:
                symbol_data = demo_data[symbol]
                figure = trading_charts.create_candlestick_chart(
                    symbol_data, f"{symbol} - Demo Data", volume=True
                )
                st.plotly_chart(figure, use_container_width=True, key=f"demo_{symbol}")

    def _render_performance_metrics(self):
        """Render performance monitoring dashboard."""
        with st.expander("📊 Performance Metrics", expanded=False):
            perf_stats = self.performance_optimizer.get_performance_stats()

            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown("**Memory Usage**")
                st.metric(
                    "Current Memory",
                    f"{perf_stats['current_memory_mb']:.1f} MB",
                    f"{perf_stats['memory_usage_percent']:.1f}%"
                )

                st.metric(
                    "Cache Hit Rate",
                    f"{perf_stats['cache_hit_rate']:.1%}",
                    help="Percentage of data served from cache"
                )

            with col2:
                st.markdown("**Processing Stats**")
                st.metric(
                    "Operations",
                    f"{perf_stats['total_operations']:,}",
                    help="Total data processing operations"
                )

                st.metric(
                    "Avg Processing Time",
                    f"{perf_stats['average_processing_time_ms']:.2f} ms",
                    help="Average time per operation"
                )

            with col3:
                st.markdown("**Data Management**")
                st.metric(
                    "Active Windows",
                    perf_stats['active_windows'],
                    help="Number of active data windows"
                )

                st.metric(
                    "Total Data Points",
                    f"{perf_stats['total_data_points']:,}",
                    help="Total data points in memory"
                )

    def _create_comparison_dataframe(self, comparison_data: Dict[str, List]) -> pd.DataFrame:
        """Create DataFrame for multi-symbol comparison."""
        try:
            all_data = []

            for symbol, data_points in comparison_data.items():
                for point in data_points:
                    all_data.append({
                        'timestamp': point.timestamp,
                        'symbol': symbol,
                        'price': point.price,
                        'volume': point.volume
                    })

            if all_data:
                df = pd.DataFrame(all_data)
                df_pivot = df.pivot_table(
                    index='timestamp',
                    columns='symbol',
                    values='price',
                    aggfunc='last'
                ).fillna(method='ffill').fillna(method='bfill')

                return df_pivot
            else:
                return pd.DataFrame()

        except Exception as e:
            self.logger.error(f"Error creating comparison DataFrame: {e}")
            return pd.DataFrame()

    def get_streaming_status(self) -> Dict[str, Any]:
        """Get current streaming status."""
        return {
            'is_streaming': self.is_streaming,
            'connection_status': self.data_manager.status.value if hasattr(self.data_manager, 'status') else 'unknown',
            'active_symbols': len(self.current_symbols),
            'symbols': self.current_symbols,
            'update_interval': self.stream_config.update_interval,
            'animations_enabled': self.animation_config.enabled,
            'total_data_points': sum(len(history) for history in self.chart_history.values()),
            'performance_stats': self.performance_optimizer.get_performance_stats()
        }


def render_real_time_charts():
    """Main function to render real-time charts interface."""
    # Initialize real-time charts manager in session state
    if 'realtime_charts_manager' not in st.session_state:
        st.session_state.realtime_charts_manager = RealTimeChartsManager()

    manager = st.session_state.realtime_charts_manager

    # Render the dashboard
    manager.render_real_time_dashboard()

    # Auto-refresh for live updates
    if manager.is_streaming:
        time.sleep(0.5)  # Brief delay
        st.rerun()