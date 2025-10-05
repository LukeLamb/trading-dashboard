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
from src.dashboard.components.data_quality import DataQualityManager


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
        # Initialize quality manager for data quality display
        if 'chart_quality_manager' not in st.session_state:
            st.session_state.chart_quality_manager = DataQualityManager()

        quality_manager = st.session_state.chart_quality_manager
        overall_score = quality_manager.get_overall_quality_score()
        overall_grade = quality_manager._score_to_grade(overall_score)

        st.metric(
            "Data Quality",
            f"{overall_grade.value} ({overall_score:.1f})",
            help=f"Overall data quality across {len(quality_manager.source_qualities)} sources"
        )

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

    # Data quality indicators section
    with st.expander("🎯 Data Quality Indicators", expanded=False):
        _render_chart_quality_indicators(quality_manager)

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


def _render_chart_quality_indicators(quality_manager):
    """Render quality indicators for chart data sources."""
    st.markdown("### 📊 Current Data Source Quality")

    if not quality_manager.source_qualities:
        st.info("No quality data available")
        return

    # Quality overview metrics
    col1, col2, col3 = st.columns(3)

    with col1:
        # Best source
        best_source = max(quality_manager.source_qualities.values(), key=lambda x: x.score)
        st.markdown(f"**🥇 Best Source:** {best_source.source_name}")
        st.markdown(f"Grade: {best_source.grade.value} ({best_source.score:.1f})")

    with col2:
        # Active alerts
        alert_count = len(quality_manager.active_alerts)
        alert_color = "🔴" if alert_count > 0 else "🟢"
        st.markdown(f"**🚨 Active Alerts:** {alert_color} {alert_count}")

    with col3:
        # Quick action
        if st.button("📊 View Full Quality Dashboard"):
            st.session_state.current_page = 'quality'
            st.rerun()

    # Quality sources table
    st.markdown("### 📈 Source Performance")

    quality_data = []
    for quality in quality_manager.source_qualities.values():
        quality_data.append({
            "Source": quality.source_name,
            "Grade": quality.grade.value,
            "Score": f"{quality.score:.1f}",
            "Response Time": f"{quality.response_time:.0f}ms",
            "Uptime": f"{quality.uptime_percentage:.1f}%",
            "Last Updated": quality.last_updated.strftime("%H:%M:%S")
        })

    if quality_data:
        # Create a simple table display
        for i, data in enumerate(quality_data):
            with st.container():
                quality_obj = list(quality_manager.source_qualities.values())[i]
                grade_color = quality_obj.grade.color

                st.markdown(
                    f"<div style='display: flex; align-items: center; padding: 8px; margin: 4px 0; "
                    f"border: 1px solid #E5E7EB; border-radius: 6px; background-color: #F9FAFB;'>"
                    f"<div style='width: 24px; height: 24px; background-color: {grade_color}; "
                    f"border-radius: 4px; margin-right: 12px; display: flex; align-items: center; "
                    f"justify-content: center; color: white; font-weight: bold; font-size: 12px;'>"
                    f"{data['Grade']}"
                    f"</div>"
                    f"<div style='flex: 1;'>"
                    f"<div style='font-weight: 600;'>{data['Source']}</div>"
                    f"<div style='font-size: 12px; color: #6B7280;'>"
                    f"Score: {data['Score']} | Response: {data['Response Time']} | Uptime: {data['Uptime']}"
                    f"</div>"
                    f"</div>"
                    f"<div style='font-size: 11px; color: #9CA3AF;'>{data['Last Updated']}</div>"
                    f"</div>",
                    unsafe_allow_html=True
                )

    # Quality recommendations
    recommendations = quality_manager.get_quality_recommendations()
    if recommendations:
        st.markdown("### 💡 Quality Recommendations")
        for rec in recommendations[:3]:  # Show top 3
            severity_icons = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}
            icon = severity_icons.get(rec['severity'], 'ℹ️')

            st.markdown(f"{icon} **{rec['title']}**")
            st.caption(rec['message'])


if __name__ == "__main__" or True:
    show_charts()