"""
Chart Animation System for Real-time Trading Dashboard.

This module provides smooth animations and transitions for financial charts
when receiving real-time data updates.
"""

import plotly.graph_objects as go
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import asyncio
import streamlit as st

from src.dashboard.components.realtime_data import MarketDataPoint


@dataclass
class AnimationConfig:
    """Configuration for chart animations."""
    enabled: bool = True
    transition_duration: int = 750  # milliseconds
    easing: str = "cubic-in-out"  # plotly easing options
    update_mode: str = "smooth"  # 'smooth', 'instant', 'fade'
    auto_scroll: bool = True
    scroll_threshold: int = 100  # data points before scrolling
    max_visible_points: int = 500
    fade_duration: int = 300
    bounce_effect: bool = False


class ChartAnimationManager:
    """Manages animations for financial charts with real-time updates."""

    def __init__(self, config: Optional[AnimationConfig] = None):
        """Initialize animation manager."""
        self.config = config or AnimationConfig()
        self.chart_states: Dict[str, Dict[str, Any]] = {}
        self.animation_queue: List[Dict[str, Any]] = []
        self.is_animating = False

    def register_chart(self, chart_id: str, figure: go.Figure):
        """Register a chart for animation management."""
        self.chart_states[chart_id] = {
            'figure': figure,
            'last_update': datetime.now(),
            'data_points': 0,
            'scroll_position': 0,
            'pending_updates': []
        }

    def create_animated_candlestick(self, df: pd.DataFrame, title: str = "Live Price Chart") -> go.Figure:
        """Create an animated candlestick chart optimized for real-time updates."""
        fig = go.Figure()

        # Add candlestick trace with animation properties
        fig.add_trace(go.Candlestick(
            x=df.index,
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            name="OHLC",
            increasing_line_color='#00C853',
            decreasing_line_color='#FF1744',
            increasing_fillcolor='rgba(0, 200, 83, 0.7)',
            decreasing_fillcolor='rgba(255, 23, 68, 0.7)',
            line=dict(width=1),
            # Animation-ready configuration
            hovertemplate="<b>%{x}</b><br>" +
                         "Open: $%{open:.2f}<br>" +
                         "High: $%{high:.2f}<br>" +
                         "Low: $%{low:.2f}<br>" +
                         "Close: $%{close:.2f}<br>" +
                         "<extra></extra>"
        ))

        # Configure layout for smooth animations
        fig.update_layout(
            title=dict(
                text=title,
                x=0.5,
                font=dict(size=16, color='#2E3440')
            ),
            xaxis=dict(
                showgrid=True,
                gridcolor='rgba(128, 128, 128, 0.2)',
                showline=True,
                linecolor='#D8DEE9',
                rangeslider=dict(visible=False),
                # Animation properties
                autorange=True if self.config.auto_scroll else False,
                type='date'
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor='rgba(128, 128, 128, 0.2)',
                showline=True,
                linecolor='#D8DEE9',
                title="Price ($)",
                # Auto-scaling for new data
                autorange=True,
                fixedrange=False
            ),
            plot_bgcolor='white',
            paper_bgcolor='white',
            height=500,
            margin=dict(l=50, r=50, t=80, b=50),
            # Animation configuration
            transition=dict(
                duration=self.config.transition_duration,
                easing=self.config.easing
            ),
            # Enable smooth updates
            uirevision='constant'  # Preserves user interactions
        )

        return fig

    def create_animated_line_chart(self, df: pd.DataFrame, title: str = "Live Price Line") -> go.Figure:
        """Create an animated line chart for real-time price updates."""
        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=df.index,
            y=df['close'],
            mode='lines',
            name='Price',
            line=dict(
                color='#1976D2',
                width=2,
                # Smooth line rendering
                smoothing=1.3,
                shape='spline'
            ),
            # Animation-ready hover
            hovertemplate="<b>%{x}</b><br>Price: $%{y:.2f}<extra></extra>",
            # Enable streaming animation
            connectgaps=True
        ))

        # Add current price indicator (animated dot)
        if not df.empty:
            latest_time = df.index[-1]
            latest_price = df['close'].iloc[-1]

            fig.add_trace(go.Scatter(
                x=[latest_time],
                y=[latest_price],
                mode='markers',
                name='Current',
                marker=dict(
                    size=10,
                    color='#FF5722',
                    line=dict(color='white', width=2),
                    # Pulsing animation effect
                    symbol='circle'
                ),
                showlegend=False,
                hovertemplate="Current: $%{y:.2f}<extra></extra>"
            ))

        self._configure_animated_layout(fig, title)
        return fig

    def create_animated_volume_chart(self, df: pd.DataFrame, title: str = "Live Volume") -> go.Figure:
        """Create an animated volume chart."""
        fig = go.Figure()

        # Color volume bars based on price movement
        colors = []
        for i in range(len(df)):
            if i == 0:
                colors.append('#2196F3')  # First bar blue
            else:
                if df['close'].iloc[i] >= df['close'].iloc[i-1]:
                    colors.append('#4CAF50')  # Green for up
                else:
                    colors.append('#F44336')  # Red for down

        fig.add_trace(go.Bar(
            x=df.index,
            y=df['volume'],
            name='Volume',
            marker=dict(
                color=colors,
                opacity=0.7,
                line=dict(width=0.5, color='rgba(0,0,0,0.2)')
            ),
            hovertemplate="<b>%{x}</b><br>Volume: %{y:,.0f}<extra></extra>"
        ))

        fig.update_layout(
            title=title,
            xaxis=dict(title="Time"),
            yaxis=dict(title="Volume"),
            height=200,
            margin=dict(l=50, r=50, t=50, b=30),
            showlegend=False,
            transition=dict(
                duration=self.config.transition_duration,
                easing=self.config.easing
            )
        )

        return fig

    def _configure_animated_layout(self, fig: go.Figure, title: str):
        """Configure layout for smooth animations."""
        fig.update_layout(
            title=dict(text=title, x=0.5),
            xaxis=dict(
                showgrid=True,
                gridcolor='rgba(128, 128, 128, 0.2)',
                autorange=True if self.config.auto_scroll else False,
                type='date',
                # Smooth scrolling configuration
                rangeslider=dict(visible=False)
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor='rgba(128, 128, 128, 0.2)',
                autorange=True,
                title="Price ($)"
            ),
            height=400,
            margin=dict(l=50, r=50, t=50, b=50),
            plot_bgcolor='white',
            paper_bgcolor='white',
            transition=dict(
                duration=self.config.transition_duration,
                easing=self.config.easing
            ),
            uirevision='constant'
        )

    def update_chart_with_animation(self, chart_id: str, new_data: pd.DataFrame,
                                   animation_type: str = "append") -> go.Figure:
        """Update chart with smooth animations."""
        if chart_id not in self.chart_states:
            raise ValueError(f"Chart {chart_id} not registered")

        chart_state = self.chart_states[chart_id]
        figure = chart_state['figure']

        if animation_type == "append":
            return self._append_data_with_animation(figure, new_data, chart_state)
        elif animation_type == "update":
            return self._update_data_with_animation(figure, new_data, chart_state)
        elif animation_type == "replace":
            return self._replace_data_with_animation(figure, new_data, chart_state)
        else:
            raise ValueError(f"Unknown animation type: {animation_type}")

    def _append_data_with_animation(self, figure: go.Figure, new_data: pd.DataFrame,
                                   chart_state: Dict[str, Any]) -> go.Figure:
        """Append new data with smooth transition."""
        if new_data.empty:
            return figure

        # Get existing data
        existing_trace = figure.data[0]

        if hasattr(existing_trace, 'x') and len(existing_trace.x) > 0:
            # Combine existing and new data
            existing_df = pd.DataFrame({
                'open': existing_trace.open,
                'high': existing_trace.high,
                'low': existing_trace.low,
                'close': existing_trace.close
            }, index=existing_trace.x)

            # Append new data
            combined_df = pd.concat([existing_df, new_data]).drop_duplicates()
        else:
            combined_df = new_data

        # Apply data windowing for performance
        if len(combined_df) > self.config.max_visible_points:
            combined_df = combined_df.tail(self.config.max_visible_points)

        # Update the trace with animation
        if self.config.enabled:
            # Smooth transition
            figure.update_traces(
                x=combined_df.index,
                open=combined_df['open'],
                high=combined_df['high'],
                low=combined_df['low'],
                close=combined_df['close']
            )
        else:
            # Instant update
            figure.data = []
            figure.add_trace(go.Candlestick(
                x=combined_df.index,
                open=combined_df['open'],
                high=combined_df['high'],
                low=combined_df['low'],
                close=combined_df['close'],
                name="OHLC"
            ))

        # Update chart state
        chart_state['data_points'] = len(combined_df)
        chart_state['last_update'] = datetime.now()

        return figure

    def _update_data_with_animation(self, figure: go.Figure, new_data: pd.DataFrame,
                                   chart_state: Dict[str, Any]) -> go.Figure:
        """Update existing data points with animation."""
        # Implementation for updating existing points
        # This would involve morphing existing candlesticks
        return self._append_data_with_animation(figure, new_data, chart_state)

    def _replace_data_with_animation(self, figure: go.Figure, new_data: pd.DataFrame,
                                    chart_state: Dict[str, Any]) -> go.Figure:
        """Replace all data with fade transition."""
        if not self.config.enabled:
            # Instant replacement
            figure.data = []
            figure.add_trace(go.Candlestick(
                x=new_data.index,
                open=new_data['open'],
                high=new_data['high'],
                low=new_data['low'],
                close=new_data['close'],
                name="OHLC"
            ))
        else:
            # Fade transition (simulated by updating all data at once)
            figure.update_traces(
                x=new_data.index,
                open=new_data['open'],
                high=new_data['high'],
                low=new_data['low'],
                close=new_data['close']
            )

        chart_state['data_points'] = len(new_data)
        chart_state['last_update'] = datetime.now()

        return figure

    def create_price_alert_animation(self, price: float, threshold: float,
                                    chart_id: str, alert_type: str = "above") -> Dict[str, Any]:
        """Create animated price alert visualization."""
        alert_config = {
            'type': 'line',
            'x0': 0, 'x1': 1,
            'xref': 'paper',
            'y0': threshold, 'y1': threshold,
            'line': dict(
                color='red' if alert_type == 'above' else 'green',
                width=3,
                dash='dash'
            ),
            # Animation for alert line
            'opacity': 1,
            'label': dict(
                text=f"Alert: ${threshold:.2f}",
                textposition='end',
                font=dict(color='red' if alert_type == 'above' else 'green', size=12)
            )
        }

        # Add pulsing effect if price crosses threshold
        if (alert_type == 'above' and price > threshold) or \
           (alert_type == 'below' and price < threshold):
            alert_config['line']['color'] = '#FF5722'
            alert_config['opacity'] = 0.8

        return alert_config

    def create_trend_line_animation(self, df: pd.DataFrame, trend_type: str = "support") -> Dict[str, Any]:
        """Create animated trend line."""
        if len(df) < 2:
            return {}

        # Calculate trend line (simplified linear regression)
        x_numeric = np.arange(len(df))
        y_values = df['close'].values

        # Linear regression
        coeffs = np.polyfit(x_numeric, y_values, 1)
        trend_line = np.poly1d(coeffs)

        start_idx = df.index[0]
        end_idx = df.index[-1]
        start_price = trend_line(0)
        end_price = trend_line(len(df) - 1)

        color = '#4CAF50' if coeffs[0] > 0 else '#F44336'  # Green for uptrend, red for downtrend

        return {
            'type': 'line',
            'x0': start_idx, 'x1': end_idx,
            'y0': start_price, 'y1': end_price,
            'line': dict(
                color=color,
                width=2,
                dash='dot'
            ),
            'opacity': 0.7,
            'label': dict(
                text=f"{trend_type.title()} Line",
                textposition='end',
                font=dict(color=color, size=10)
            )
        }

    def add_volume_spike_animation(self, figure: go.Figure, df: pd.DataFrame,
                                  spike_threshold: float = 2.0) -> go.Figure:
        """Add animation for volume spikes."""
        if 'volume' not in df.columns:
            return figure

        # Calculate volume moving average
        volume_ma = df['volume'].rolling(window=20).mean()
        spike_indices = df[df['volume'] > volume_ma * spike_threshold].index

        # Add spike indicators
        for spike_time in spike_indices:
            spike_volume = df.loc[spike_time, 'volume']
            spike_price = df.loc[spike_time, 'close']

            # Add animated spike marker
            figure.add_trace(go.Scatter(
                x=[spike_time],
                y=[spike_price],
                mode='markers',
                marker=dict(
                    symbol='triangle-up',
                    size=15,
                    color='orange',
                    line=dict(color='darkorange', width=2)
                ),
                name='Volume Spike',
                showlegend=False,
                hovertemplate=f"Volume Spike<br>Time: %{{x}}<br>Price: $%{{y:.2f}}<br>Volume: {spike_volume:,.0f}<extra></extra>"
            ))

        return figure

    def get_animation_status(self) -> Dict[str, Any]:
        """Get current animation status and statistics."""
        return {
            'enabled': self.config.enabled,
            'active_charts': len(self.chart_states),
            'is_animating': self.is_animating,
            'queue_size': len(self.animation_queue),
            'config': {
                'transition_duration': self.config.transition_duration,
                'easing': self.config.easing,
                'auto_scroll': self.config.auto_scroll,
                'max_visible_points': self.config.max_visible_points
            },
            'chart_states': {
                chart_id: {
                    'data_points': state['data_points'],
                    'last_update': state['last_update'].isoformat(),
                    'pending_updates': len(state['pending_updates'])
                }
                for chart_id, state in self.chart_states.items()
            }
        }

    def update_animation_config(self, new_config: AnimationConfig):
        """Update animation configuration."""
        self.config = new_config

        # Update all existing charts with new config
        for chart_id, state in self.chart_states.items():
            figure = state['figure']
            figure.update_layout(
                transition=dict(
                    duration=self.config.transition_duration,
                    easing=self.config.easing
                )
            )

    def clear_chart_animations(self, chart_id: str):
        """Clear animations for a specific chart."""
        if chart_id in self.chart_states:
            del self.chart_states[chart_id]

    def clear_all_animations(self):
        """Clear all chart animations."""
        self.chart_states.clear()
        self.animation_queue.clear()
        self.is_animating = False


class RealTimeChartRenderer:
    """Renders real-time financial charts with smooth animations."""

    def __init__(self, animation_manager: ChartAnimationManager):
        """Initialize renderer with animation manager."""
        self.animation_manager = animation_manager
        self.active_charts: Dict[str, go.Figure] = {}

    def render_live_candlestick(self, symbol: str, data_points: List[MarketDataPoint],
                               chart_height: int = 500) -> go.Figure:
        """Render live candlestick chart with real-time updates."""
        # Convert data points to DataFrame
        df_data = []
        for point in data_points:
            # Simulate OHLC data from price points
            df_data.append({
                'timestamp': point.timestamp,
                'open': point.price * 0.999,  # Simulate open
                'high': point.price * 1.002,  # Simulate high
                'low': point.price * 0.998,   # Simulate low
                'close': point.price,
                'volume': point.volume
            })

        if not df_data:
            return go.Figure()

        df = pd.DataFrame(df_data)
        df.set_index('timestamp', inplace=True)

        # Create or update animated chart
        chart_id = f"live_{symbol}"

        if chart_id not in self.active_charts:
            # Create new animated chart
            figure = self.animation_manager.create_animated_candlestick(
                df, f"{symbol} - Live Price"
            )
            self.animation_manager.register_chart(chart_id, figure)
            self.active_charts[chart_id] = figure
        else:
            # Update existing chart with animation
            figure = self.animation_manager.update_chart_with_animation(
                chart_id, df, "append"
            )
            self.active_charts[chart_id] = figure

        # Adjust height
        figure.update_layout(height=chart_height)

        return figure

    def render_live_line_chart(self, symbol: str, data_points: List[MarketDataPoint],
                              chart_height: int = 400) -> go.Figure:
        """Render live line chart with smooth transitions."""
        df_data = []
        for point in data_points:
            df_data.append({
                'timestamp': point.timestamp,
                'close': point.price
            })

        if not df_data:
            return go.Figure()

        df = pd.DataFrame(df_data)
        df.set_index('timestamp', inplace=True)

        figure = self.animation_manager.create_animated_line_chart(
            df, f"{symbol} - Live Price Trend"
        )
        figure.update_layout(height=chart_height)

        return figure

    def render_live_volume(self, symbol: str, data_points: List[MarketDataPoint],
                          chart_height: int = 200) -> go.Figure:
        """Render live volume chart."""
        df_data = []
        for point in data_points:
            df_data.append({
                'timestamp': point.timestamp,
                'volume': point.volume,
                'close': point.price
            })

        if not df_data:
            return go.Figure()

        df = pd.DataFrame(df_data)
        df.set_index('timestamp', inplace=True)

        figure = self.animation_manager.create_animated_volume_chart(
            df, f"{symbol} - Live Volume"
        )
        figure.update_layout(height=chart_height)

        return figure