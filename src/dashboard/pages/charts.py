"""
Trading Charts page for Trading Dashboard.

This page provides interactive financial data visualization including
candlestick charts, technical indicators, and multi-symbol comparisons.
"""

import streamlit as st
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.dashboard.components import render_trading_charts
from src.dashboard.components.realtime_charts import render_real_time_charts


def show_charts():
    """Display the trading charts page."""
    st.markdown("## 📈 Trading Charts & Analysis")

    st.markdown("""
    Professional financial data visualization with interactive charts, technical indicators,
    and multi-symbol analysis tools. Perfect for market analysis and trading decisions.
    """)

    # Quick stats/info section
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Chart Types", "4", help="Available chart types")

    with col2:
        st.metric("Technical Indicators", "7", help="Available technical indicators")

    with col3:
        st.metric("Real-time Updates", "✅ Available", help="Live data streaming - Phase 4 Step 2 Complete")

    with col4:
        st.metric("Data Quality", "A+", help="Simulated high-quality market data")

    st.markdown("---")

    # Chart type selection
    chart_mode = st.selectbox(
        "Chart Mode",
        ["Real-time Streaming", "Historical Analysis"],
        help="Choose between live data streaming or historical chart analysis"
    )

    if chart_mode == "Real-time Streaming":
        # Real-time charts with live data streaming
        render_real_time_charts()
    else:
        # Historical analysis charts
        render_trading_charts()

    st.markdown("---")

    # Feature information
    st.markdown("### 🎯 Features")

    feature_col1, feature_col2 = st.columns(2)

    with feature_col1:
        st.markdown("""
        **Chart Types:**
        - 🕯️ **Candlestick Charts** with OHLCV data
        - 📊 **Multi-Symbol Comparison** with normalization
        - 📊 **Volume Profile** analysis
        - 🔥 **Correlation Heatmaps** for portfolio analysis

        **Technical Indicators:**
        - 📈 **Moving Averages** (SMA, EMA)
        - 📊 **Bollinger Bands** with configurable periods
        - ⚡ **RSI** (Relative Strength Index)
        - 📈 **MACD** with signal line and histogram
        """)

    with feature_col2:
        st.markdown("""
        **Interactive Features:**
        - 🔍 **Zoom and Pan** controls
        - 📊 **Hover Data** with detailed information
        - 🎨 **Customizable** chart appearance
        - 📱 **Responsive** design for all devices

        **Coming Soon (Phase 4 Step 2):**
        - 🔄 **Real-time Data** streaming
        - ⚡ **Live Updates** with configurable intervals
        - 🔔 **Price Alerts** and notifications
        - 💾 **Chart Layouts** save/load functionality
        """)

    # Usage guide
    with st.expander("📖 How to Use Trading Charts"):
        st.markdown("""
        ### Getting Started:

        1. **Select Chart Type**: Choose from candlestick, comparison, volume profile, or correlation analysis
        2. **Configure Settings**: Adjust time period, symbols, and visual options
        3. **Add Indicators**: Enable technical indicators like moving averages, RSI, and MACD
        4. **Analyze Data**: Use interactive features to zoom, pan, and explore price movements

        ### Chart Types Explained:

        - **Candlestick Charts**: Show OHLC (Open, High, Low, Close) price data with optional volume and technical indicators
        - **Price Comparison**: Compare multiple symbols on the same chart with percentage normalization
        - **Volume Profile**: Analyze trading activity at different price levels
        - **Correlation Heatmap**: Visualize relationships between different assets

        ### Technical Indicators:

        - **SMA/EMA**: Moving averages help identify trends
        - **Bollinger Bands**: Show volatility and potential support/resistance levels
        - **RSI**: Momentum oscillator indicating overbought/oversold conditions (0-100 scale)
        - **MACD**: Trend-following momentum indicator with signal line crossovers
        """)

    # Sample data note
    st.info("""
    📝 **Note**: Currently displaying simulated market data for demonstration purposes.
    Real market data integration will be available in Phase 4 Step 2 with live streaming capabilities.
    """)

    # Performance tips
    with st.expander("⚡ Performance Tips"):
        st.markdown("""
        ### Optimizing Chart Performance:

        - **Data Period**: Use shorter periods (30-100 days) for faster rendering
        - **Indicators**: Enable only needed indicators to improve performance
        - **Chart Height**: Adjust height based on your screen size and preferences
        - **Browser**: Use modern browsers (Chrome, Firefox, Edge) for best performance

        ### Best Practices:

        - Start with basic candlestick charts before adding multiple indicators
        - Use correlation analysis to understand portfolio relationships
        - Combine multiple timeframes for comprehensive analysis
        - Save chart configurations using browser bookmarks (full save/load coming soon)
        """)


if __name__ == "__main__":
    show_charts()