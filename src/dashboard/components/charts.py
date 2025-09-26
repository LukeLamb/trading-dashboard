"""
Interactive Chart Components for Trading Dashboard

This module provides comprehensive financial data visualization components
including candlestick charts, technical indicators, and multi-symbol comparisons.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import math
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils.logging import get_logger


class TechnicalIndicators:
    """Technical analysis indicators for financial data."""

    @staticmethod
    def sma(prices: pd.Series, period: int) -> pd.Series:
        """Calculate Simple Moving Average."""
        return prices.rolling(window=period).mean()

    @staticmethod
    def ema(prices: pd.Series, period: int) -> pd.Series:
        """Calculate Exponential Moving Average."""
        return prices.ewm(span=period).mean()

    @staticmethod
    def rsi(prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate Relative Strength Index."""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    @staticmethod
    def macd(prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, pd.Series]:
        """Calculate MACD indicator."""
        ema_fast = TechnicalIndicators.ema(prices, fast)
        ema_slow = TechnicalIndicators.ema(prices, slow)
        macd = ema_fast - ema_slow
        signal_line = TechnicalIndicators.ema(macd, signal)
        histogram = macd - signal_line

        return {
            'macd': macd,
            'signal': signal_line,
            'histogram': histogram
        }

    @staticmethod
    def bollinger_bands(prices: pd.Series, period: int = 20, std_dev: int = 2) -> Dict[str, pd.Series]:
        """Calculate Bollinger Bands."""
        sma = TechnicalIndicators.sma(prices, period)
        std = prices.rolling(window=period).std()

        return {
            'middle': sma,
            'upper': sma + (std * std_dev),
            'lower': sma - (std * std_dev)
        }

    @staticmethod
    def stochastic(high: pd.Series, low: pd.Series, close: pd.Series, k_period: int = 14, d_period: int = 3) -> Dict[str, pd.Series]:
        """Calculate Stochastic Oscillator."""
        lowest_low = low.rolling(window=k_period).min()
        highest_high = high.rolling(window=k_period).max()
        k_percent = 100 * ((close - lowest_low) / (highest_high - lowest_low))
        d_percent = k_percent.rolling(window=d_period).mean()

        return {
            'k': k_percent,
            'd': d_percent
        }


class TradingCharts:
    """Professional trading chart components with technical analysis."""

    def __init__(self):
        self.logger = get_logger(__name__)
        self.default_colors = {
            'up': '#26a69a',
            'down': '#ef5350',
            'volume': '#1f77b4',
            'sma': '#ff7f0e',
            'ema': '#2ca02c',
            'bollinger': '#d62728',
            'rsi': '#9467bd',
            'macd': '#8c564b'
        }

    def create_candlestick_chart(
        self,
        df: pd.DataFrame,
        title: str = "Price Chart",
        volume: bool = True,
        height: int = 600,
        indicators: Optional[List[str]] = None
    ) -> go.Figure:
        """
        Create a comprehensive candlestick chart with optional indicators.

        Args:
            df: DataFrame with OHLCV data (columns: open, high, low, close, volume, timestamp)
            title: Chart title
            volume: Whether to include volume subplot
            height: Chart height in pixels
            indicators: List of indicators to include ['sma_20', 'ema_50', 'bollinger', 'rsi', 'macd']
        """
        try:
            # Validate required columns
            required_cols = ['open', 'high', 'low', 'close', 'timestamp']
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                raise ValueError(f"Missing required columns: {missing_cols}")

            # Sort by timestamp
            df = df.sort_values('timestamp')

            # Create subplots
            subplot_count = 1
            if volume:
                subplot_count += 1
            if indicators:
                if 'rsi' in indicators:
                    subplot_count += 1
                if 'macd' in indicators:
                    subplot_count += 1

            # Calculate subplot heights
            row_heights = []
            if subplot_count == 1:
                row_heights = [1]
            elif subplot_count == 2:
                row_heights = [0.7, 0.3]
            elif subplot_count == 3:
                row_heights = [0.6, 0.2, 0.2]
            elif subplot_count == 4:
                row_heights = [0.5, 0.2, 0.15, 0.15]

            fig = make_subplots(
                rows=subplot_count,
                cols=1,
                shared_xaxes=True,
                vertical_spacing=0.05,
                row_heights=row_heights,
                subplot_titles=[title] + [''] * (subplot_count - 1)
            )

            # Main candlestick chart
            fig.add_trace(
                go.Candlestick(
                    x=df['timestamp'],
                    open=df['open'],
                    high=df['high'],
                    low=df['low'],
                    close=df['close'],
                    name='OHLC',
                    increasing_line_color=self.default_colors['up'],
                    decreasing_line_color=self.default_colors['down']
                ),
                row=1, col=1
            )

            current_row = 1

            # Add technical indicators to main chart
            if indicators:
                if 'sma_20' in indicators:
                    sma_20 = TechnicalIndicators.sma(df['close'], 20)
                    fig.add_trace(
                        go.Scatter(
                            x=df['timestamp'],
                            y=sma_20,
                            mode='lines',
                            name='SMA 20',
                            line=dict(color=self.default_colors['sma'], width=1)
                        ),
                        row=1, col=1
                    )

                if 'sma_50' in indicators:
                    sma_50 = TechnicalIndicators.sma(df['close'], 50)
                    fig.add_trace(
                        go.Scatter(
                            x=df['timestamp'],
                            y=sma_50,
                            mode='lines',
                            name='SMA 50',
                            line=dict(color=self.default_colors['sma'], width=1, dash='dash')
                        ),
                        row=1, col=1
                    )

                if 'ema_20' in indicators:
                    ema_20 = TechnicalIndicators.ema(df['close'], 20)
                    fig.add_trace(
                        go.Scatter(
                            x=df['timestamp'],
                            y=ema_20,
                            mode='lines',
                            name='EMA 20',
                            line=dict(color=self.default_colors['ema'], width=1)
                        ),
                        row=1, col=1
                    )

                if 'ema_50' in indicators:
                    ema_50 = TechnicalIndicators.ema(df['close'], 50)
                    fig.add_trace(
                        go.Scatter(
                            x=df['timestamp'],
                            y=ema_50,
                            mode='lines',
                            name='EMA 50',
                            line=dict(color=self.default_colors['ema'], width=1, dash='dash')
                        ),
                        row=1, col=1
                    )

                if 'bollinger' in indicators:
                    bb = TechnicalIndicators.bollinger_bands(df['close'])
                    fig.add_trace(
                        go.Scatter(
                            x=df['timestamp'],
                            y=bb['upper'],
                            mode='lines',
                            name='BB Upper',
                            line=dict(color=self.default_colors['bollinger'], width=1),
                            showlegend=False
                        ),
                        row=1, col=1
                    )
                    fig.add_trace(
                        go.Scatter(
                            x=df['timestamp'],
                            y=bb['lower'],
                            mode='lines',
                            name='BB Lower',
                            line=dict(color=self.default_colors['bollinger'], width=1),
                            fill='tonexty',
                            fillcolor=f"rgba{tuple(list(px.colors.hex_to_rgb(self.default_colors['bollinger'])) + [0.1])}",
                            showlegend=False
                        ),
                        row=1, col=1
                    )
                    fig.add_trace(
                        go.Scatter(
                            x=df['timestamp'],
                            y=bb['middle'],
                            mode='lines',
                            name='BB Middle',
                            line=dict(color=self.default_colors['bollinger'], width=1, dash='dot')
                        ),
                        row=1, col=1
                    )

            # Volume subplot
            if volume and 'volume' in df.columns:
                current_row += 1
                colors = ['red' if df.iloc[i]['close'] < df.iloc[i]['open'] else 'green'
                         for i in range(len(df))]

                fig.add_trace(
                    go.Bar(
                        x=df['timestamp'],
                        y=df['volume'],
                        name='Volume',
                        marker_color=colors,
                        opacity=0.7
                    ),
                    row=current_row, col=1
                )

            # RSI subplot
            if indicators and 'rsi' in indicators:
                current_row += 1
                rsi = TechnicalIndicators.rsi(df['close'])
                fig.add_trace(
                    go.Scatter(
                        x=df['timestamp'],
                        y=rsi,
                        mode='lines',
                        name='RSI',
                        line=dict(color=self.default_colors['rsi'], width=2)
                    ),
                    row=current_row, col=1
                )

                # Add RSI overbought/oversold lines
                fig.add_hline(y=70, line_dash="dash", line_color="red", opacity=0.7, row=current_row, col=1)
                fig.add_hline(y=30, line_dash="dash", line_color="green", opacity=0.7, row=current_row, col=1)
                fig.add_hline(y=50, line_dash="dot", line_color="gray", opacity=0.5, row=current_row, col=1)

            # MACD subplot
            if indicators and 'macd' in indicators:
                current_row += 1
                macd_data = TechnicalIndicators.macd(df['close'])

                fig.add_trace(
                    go.Scatter(
                        x=df['timestamp'],
                        y=macd_data['macd'],
                        mode='lines',
                        name='MACD',
                        line=dict(color=self.default_colors['macd'], width=2)
                    ),
                    row=current_row, col=1
                )

                fig.add_trace(
                    go.Scatter(
                        x=df['timestamp'],
                        y=macd_data['signal'],
                        mode='lines',
                        name='Signal',
                        line=dict(color='orange', width=1)
                    ),
                    row=current_row, col=1
                )

                # MACD histogram
                colors = ['green' if val >= 0 else 'red' for val in macd_data['histogram']]
                fig.add_trace(
                    go.Bar(
                        x=df['timestamp'],
                        y=macd_data['histogram'],
                        name='Histogram',
                        marker_color=colors,
                        opacity=0.6
                    ),
                    row=current_row, col=1
                )

            # Update layout
            fig.update_layout(
                height=height,
                showlegend=True,
                xaxis_rangeslider_visible=False,
                hovermode='x unified',
                template='plotly_white'
            )

            # Update x-axes
            fig.update_xaxes(
                type='date',
                showgrid=True,
                gridwidth=1,
                gridcolor='lightgray'
            )

            # Update y-axes
            fig.update_yaxes(
                showgrid=True,
                gridwidth=1,
                gridcolor='lightgray'
            )

            return fig

        except Exception as e:
            self.logger.error(f"Error creating candlestick chart: {e}")
            raise

    def create_line_comparison_chart(
        self,
        data_dict: Dict[str, pd.DataFrame],
        title: str = "Price Comparison",
        normalize: bool = True,
        height: int = 500
    ) -> go.Figure:
        """
        Create multi-symbol price comparison chart.

        Args:
            data_dict: Dict of {symbol: DataFrame} with price data
            title: Chart title
            normalize: Whether to normalize prices to percentage change
            height: Chart height in pixels
        """
        try:
            fig = go.Figure()

            colors = px.colors.qualitative.Set3
            color_idx = 0

            for symbol, df in data_dict.items():
                if 'close' not in df.columns or 'timestamp' not in df.columns:
                    continue

                df = df.sort_values('timestamp')
                prices = df['close']

                if normalize:
                    # Normalize to percentage change from first value
                    first_price = prices.iloc[0]
                    prices = ((prices - first_price) / first_price) * 100

                fig.add_trace(
                    go.Scatter(
                        x=df['timestamp'],
                        y=prices,
                        mode='lines',
                        name=symbol,
                        line=dict(
                            color=colors[color_idx % len(colors)],
                            width=2
                        ),
                        hovertemplate=f'<b>{symbol}</b><br>' +
                                    'Date: %{x}<br>' +
                                    ('Change: %{y:.2f}%' if normalize else 'Price: %{y:.2f}') +
                                    '<extra></extra>'
                    )
                )
                color_idx += 1

            # Update layout
            y_title = "Percentage Change (%)" if normalize else "Price"
            fig.update_layout(
                title=title,
                xaxis_title="Date",
                yaxis_title=y_title,
                height=height,
                hovermode='x unified',
                template='plotly_white',
                showlegend=True
            )

            # Add zero line if normalized
            if normalize:
                fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.7)

            fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
            fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')

            return fig

        except Exception as e:
            self.logger.error(f"Error creating line comparison chart: {e}")
            raise

    def create_volume_profile_chart(
        self,
        df: pd.DataFrame,
        title: str = "Volume Profile",
        height: int = 600
    ) -> go.Figure:
        """Create volume profile chart showing price levels with most trading activity."""
        try:
            # Calculate volume profile
            price_bins = 50
            min_price = df['low'].min()
            max_price = df['high'].max()
            price_range = np.linspace(min_price, max_price, price_bins)

            volume_profile = np.zeros(len(price_range) - 1)

            for i, row in df.iterrows():
                # Find which price bins this candle touches
                start_bin = np.searchsorted(price_range, row['low'])
                end_bin = np.searchsorted(price_range, row['high'])

                # Distribute volume across touched bins
                bins_touched = max(1, end_bin - start_bin)
                volume_per_bin = row['volume'] / bins_touched

                for bin_idx in range(start_bin, min(end_bin, len(volume_profile))):
                    volume_profile[bin_idx] += volume_per_bin

            # Create subplots
            fig = make_subplots(
                rows=1, cols=2,
                column_widths=[0.8, 0.2],
                shared_yaxes=True,
                horizontal_spacing=0.02
            )

            # Main candlestick chart
            fig.add_trace(
                go.Candlestick(
                    x=df['timestamp'],
                    open=df['open'],
                    high=df['high'],
                    low=df['low'],
                    close=df['close'],
                    name='OHLC',
                    increasing_line_color=self.default_colors['up'],
                    decreasing_line_color=self.default_colors['down']
                ),
                row=1, col=1
            )

            # Volume profile
            profile_y = (price_range[:-1] + price_range[1:]) / 2
            fig.add_trace(
                go.Bar(
                    y=profile_y,
                    x=volume_profile,
                    orientation='h',
                    name='Volume Profile',
                    marker_color='rgba(0, 100, 200, 0.6)',
                    showlegend=False
                ),
                row=1, col=2
            )

            fig.update_layout(
                title=title,
                height=height,
                xaxis_rangeslider_visible=False,
                template='plotly_white'
            )

            return fig

        except Exception as e:
            self.logger.error(f"Error creating volume profile chart: {e}")
            raise

    def create_heatmap_correlation(
        self,
        data_dict: Dict[str, pd.DataFrame],
        title: str = "Price Correlation Heatmap",
        height: int = 500
    ) -> go.Figure:
        """Create correlation heatmap for multiple symbols."""
        try:
            # Prepare data for correlation
            correlation_data = {}

            for symbol, df in data_dict.items():
                if 'close' not in df.columns:
                    continue
                df = df.sort_values('timestamp')
                correlation_data[symbol] = df['close'].pct_change().dropna()

            # Create DataFrame and calculate correlation
            corr_df = pd.DataFrame(correlation_data)
            correlation_matrix = corr_df.corr()

            # Create heatmap
            fig = go.Figure(
                data=go.Heatmap(
                    z=correlation_matrix.values,
                    x=correlation_matrix.columns,
                    y=correlation_matrix.columns,
                    colorscale='RdBu',
                    zmid=0,
                    text=correlation_matrix.round(3).values,
                    texttemplate='%{text}',
                    textfont={"size": 10},
                    hovertemplate='<b>%{x} vs %{y}</b><br>' +
                                'Correlation: %{z:.3f}<extra></extra>'
                )
            )

            fig.update_layout(
                title=title,
                height=height,
                template='plotly_white'
            )

            return fig

        except Exception as e:
            self.logger.error(f"Error creating correlation heatmap: {e}")
            raise

    def generate_sample_data(
        self,
        symbol: str = "SAMPLE",
        days: int = 100,
        start_price: float = 100.0,
        volatility: float = 0.02
    ) -> pd.DataFrame:
        """Generate sample OHLCV data for testing."""
        try:
            dates = pd.date_range(
                end=datetime.now(),
                periods=days,
                freq='D'
            )

            np.random.seed(42)  # For reproducible results

            data = []
            current_price = start_price

            for date in dates:
                # Generate price movement
                change = np.random.normal(0, volatility)
                current_price *= (1 + change)

                # Generate OHLC
                daily_volatility = volatility * 0.5
                intraday_range = current_price * daily_volatility

                high = current_price + np.random.uniform(0, intraday_range)
                low = current_price - np.random.uniform(0, intraday_range)
                open_price = current_price + np.random.uniform(-intraday_range/2, intraday_range/2)
                close = current_price

                # Ensure OHLC relationship is valid
                high = max(high, open_price, close)
                low = min(low, open_price, close)

                # Generate volume
                volume = np.random.randint(10000, 100000)

                data.append({
                    'timestamp': date,
                    'open': round(open_price, 2),
                    'high': round(high, 2),
                    'low': round(low, 2),
                    'close': round(close, 2),
                    'volume': volume,
                    'symbol': symbol
                })

            return pd.DataFrame(data)

        except Exception as e:
            self.logger.error(f"Error generating sample data: {e}")
            raise


def render_trading_charts():
    """Main trading charts interface for Streamlit."""
    st.markdown("### 📈 Trading Charts")

    charts = TradingCharts()

    # Chart type selection
    chart_type = st.selectbox(
        "Select Chart Type",
        ["Candlestick Chart", "Price Comparison", "Volume Profile", "Correlation Heatmap"]
    )

    if chart_type == "Candlestick Chart":
        st.markdown("#### 🕯️ Candlestick Chart with Technical Indicators")

        col1, col2 = st.columns([1, 2])

        with col1:
            # Chart configuration
            symbol = st.text_input("Symbol", value="SAMPLE", help="Enter trading symbol")
            days = st.slider("Data Period (days)", 30, 365, 100)
            chart_height = st.slider("Chart Height", 400, 800, 600)

            # Technical indicators
            st.markdown("**Technical Indicators:**")
            show_volume = st.checkbox("Volume", value=True)

            indicators = []
            if st.checkbox("SMA 20"):
                indicators.append("sma_20")
            if st.checkbox("SMA 50"):
                indicators.append("sma_50")
            if st.checkbox("EMA 20"):
                indicators.append("ema_20")
            if st.checkbox("EMA 50"):
                indicators.append("ema_50")
            if st.checkbox("Bollinger Bands"):
                indicators.append("bollinger")
            if st.checkbox("RSI"):
                indicators.append("rsi")
            if st.checkbox("MACD"):
                indicators.append("macd")

        with col2:
            # Generate and display chart
            try:
                # Generate sample data
                df = charts.generate_sample_data(symbol=symbol, days=days)

                # Create chart
                fig = charts.create_candlestick_chart(
                    df=df,
                    title=f"{symbol} Price Chart",
                    volume=show_volume,
                    height=chart_height,
                    indicators=indicators if indicators else None
                )

                st.plotly_chart(fig, use_container_width=True)

                # Display recent data
                st.markdown("**Recent Price Data:**")
                st.dataframe(df.tail(5)[['timestamp', 'open', 'high', 'low', 'close', 'volume']])

            except Exception as e:
                st.error(f"Error creating chart: {e}")

    elif chart_type == "Price Comparison":
        st.markdown("#### 📊 Multi-Symbol Price Comparison")

        col1, col2 = st.columns([1, 2])

        with col1:
            # Configuration
            symbols_input = st.text_area(
                "Symbols (one per line)",
                value="AAPL\nGOOGL\nMSFT\nTSLA",
                help="Enter symbols to compare, one per line"
            )
            days = st.slider("Data Period (days)", 30, 365, 100, key="comparison_days")
            normalize = st.checkbox("Normalize to % Change", value=True)
            chart_height = st.slider("Chart Height", 400, 800, 500, key="comparison_height")

        with col2:
            try:
                symbols = [s.strip() for s in symbols_input.split('\n') if s.strip()]

                if symbols:
                    # Generate data for each symbol
                    data_dict = {}
                    for i, symbol in enumerate(symbols):
                        df = charts.generate_sample_data(
                            symbol=symbol,
                            days=days,
                            start_price=100 + i * 20,  # Different starting prices
                            volatility=0.015 + i * 0.005  # Different volatilities
                        )
                        data_dict[symbol] = df

                    # Create comparison chart
                    fig = charts.create_line_comparison_chart(
                        data_dict=data_dict,
                        title="Price Comparison",
                        normalize=normalize,
                        height=chart_height
                    )

                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("Please enter at least one symbol")

            except Exception as e:
                st.error(f"Error creating comparison chart: {e}")

    elif chart_type == "Volume Profile":
        st.markdown("#### 📊 Volume Profile Analysis")

        try:
            # Generate sample data
            df = charts.generate_sample_data(days=100)

            # Create volume profile chart
            fig = charts.create_volume_profile_chart(
                df=df,
                title="Volume Profile",
                height=600
            )

            st.plotly_chart(fig, use_container_width=True)

            st.info("Volume profile shows price levels where the most trading activity occurred.")

        except Exception as e:
            st.error(f"Error creating volume profile: {e}")

    elif chart_type == "Correlation Heatmap":
        st.markdown("#### 🔥 Price Correlation Analysis")

        try:
            # Generate sample data for multiple symbols
            symbols = ["AAPL", "GOOGL", "MSFT", "TSLA", "AMZN"]
            data_dict = {}

            for i, symbol in enumerate(symbols):
                df = charts.generate_sample_data(
                    symbol=symbol,
                    days=100,
                    start_price=100 + i * 15,
                    volatility=0.015 + i * 0.003
                )
                data_dict[symbol] = df

            # Create correlation heatmap
            fig = charts.create_heatmap_correlation(
                data_dict=data_dict,
                title="Daily Returns Correlation Matrix",
                height=500
            )

            st.plotly_chart(fig, use_container_width=True)

            st.info("Correlation values range from -1 to 1. Values closer to 1 indicate strong positive correlation.")

        except Exception as e:
            st.error(f"Error creating correlation heatmap: {e}")