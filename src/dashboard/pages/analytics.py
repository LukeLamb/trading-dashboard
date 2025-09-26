"""
Analytics page for Trading Dashboard.

This page provides comprehensive system metrics monitoring, business analytics,
and performance tracking for the trading system.
"""

import streamlit as st
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.dashboard.components.metrics_dashboard import render_metrics_dashboard


def show_analytics():
    """Display the analytics and metrics page."""
    st.markdown("## 📊 Analytics & System Metrics")

    st.markdown("""
    Comprehensive system performance monitoring and business analytics dashboard.
    Track system health, monitor resource usage, and analyze trading performance.
    """)

    # Quick info section
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Monitoring", "Real-time", help="Live system and business metrics")

    with col2:
        st.metric("Metrics Types", "System + Business", help="Comprehensive performance tracking")

    with col3:
        st.metric("Layouts", "4 + Custom", help="Multiple dashboard layouts available")

    with col4:
        st.metric("Alerts", "Multi-level", help="Warning and critical alert system")

    st.markdown("---")

    # Main metrics dashboard
    render_metrics_dashboard()

    st.markdown("---")

    # Feature information
    st.markdown("### 🎯 Analytics Features")

    feature_col1, feature_col2 = st.columns(2)

    with feature_col1:
        st.markdown("""
        **System Metrics:**
        - 🖥️ **CPU & Memory Monitoring** with real-time usage tracking
        - 💾 **Disk Usage Analysis** with storage optimization insights
        - 🌐 **Network Activity Tracking** with bandwidth monitoring
        - 🏥 **System Health Scoring** with overall performance assessment

        **Performance Analytics:**
        - 📈 **Historical Trend Analysis** with configurable time ranges
        - 🚨 **Alert Management System** with threshold-based notifications
        - 📊 **Resource Optimization** recommendations and insights
        - ⚡ **Real-time Performance Gauges** with color-coded status indicators
        """)

    with feature_col2:
        st.markdown("""
        **Business Metrics:**
        - 💰 **Portfolio Performance Tracking** with real-time P&L
        - 📈 **Trading Analytics** with win rates and average trade analysis
        - ⚠️ **Risk Management Metrics** with exposure and drawdown tracking
        - 💹 **Performance KPIs** with Sharpe ratio and return analysis

        **Dashboard Customization:**
        - 🎨 **Multiple Layout Options** (Default, System Focus, Business Focus, Executive)
        - 🧩 **Custom Widget Configuration** with drag-and-drop functionality
        - 💾 **Layout Save/Load** with persistent user preferences
        - 📱 **Responsive Design** optimized for all screen sizes
        """)

    # Dashboard layouts guide
    with st.expander("📐 Dashboard Layouts Guide"):
        st.markdown("""
        ### Available Dashboard Layouts

        **🏠 Default Layout**
        - System overview with CPU, memory, disk, and health metrics
        - Performance charts showing CPU/memory usage and network activity
        - Business metrics with portfolio value, P&L, and risk exposure
        - Balanced view for general monitoring

        **🖥️ System Focus Layout**
        - Detailed system performance monitoring
        - Extended CPU and memory charts with configurable time ranges
        - Network activity analysis with bandwidth tracking
        - System alerts and warnings with actionable insights

        **💼 Business Focus Layout**
        - Trading and portfolio performance emphasis
        - Detailed portfolio performance charts with return analysis
        - P&L tracking with daily, weekly, and monthly views
        - Risk management metrics with exposure and drawdown analysis

        **👔 Executive Summary Layout**
        - High-level KPIs and summary metrics
        - Key performance indicators in executive-friendly format
        - Portfolio overview with simplified metrics
        - System health summary for operational awareness

        ### Custom Layout Creation

        1. **Widget Selection**: Choose from 12+ available widgets
        2. **Layout Configuration**: Arrange widgets in preferred order
        3. **Save & Load**: Persist custom layouts across sessions
        4. **Share Layouts**: Export/import layout configurations
        """)

    # Metrics explanation
    with st.expander("📊 Metrics Explanation"):
        st.markdown("""
        ### System Metrics Explained

        **CPU Usage (%)**
        - Current processor utilization across all cores
        - Warning threshold: 70%, Critical threshold: 85%
        - Includes frequency monitoring and core count tracking

        **Memory Usage (%)**
        - RAM utilization including used, available, and total memory
        - Warning threshold: 75%, Critical threshold: 90%
        - Memory leak detection and optimization recommendations

        **Disk Usage (%)**
        - Storage utilization across all mounted volumes
        - Warning threshold: 80%, Critical threshold: 95%
        - Free space monitoring and cleanup recommendations

        **Network Activity (MB)**
        - Bytes sent and received with bandwidth utilization
        - Traffic pattern analysis and peak usage identification
        - Network latency monitoring and connectivity assessment

        ### Business Metrics Explained

        **Portfolio Value ($)**
        - Total value of all positions and cash holdings
        - 24-hour change tracking with percentage calculations
        - Historical performance with trend analysis

        **Daily P&L ($)**
        - Profit and loss for current trading session
        - Cumulative and individual position P&L tracking
        - Win/loss ratio analysis and performance attribution

        **Risk Exposure ($)**
        - Total risk across all open positions
        - Value-at-Risk (VaR) calculations and stress testing
        - Risk-to-portfolio ratio monitoring

        **Sharpe Ratio**
        - Risk-adjusted return metric (return per unit of risk)
        - Benchmark comparison and historical analysis
        - Portfolio optimization recommendations
        """)

    # Alert system guide
    with st.expander("🚨 Alert System Guide"):
        st.markdown("""
        ### Alert Severity Levels

        **🟢 Normal**
        - All metrics within acceptable ranges
        - System operating optimally
        - No action required

        **🟡 Warning**
        - Metrics approaching threshold limits
        - Performance degradation possible
        - Monitor closely, prepare for action

        **🔴 Critical**
        - Metrics exceed safe operating thresholds
        - Immediate attention required
        - System performance significantly impacted

        **🆘 Emergency**
        - System failure imminent or occurred
        - Urgent intervention required
        - Trading operations may be affected

        ### Alert Response Guidelines

        1. **Acknowledge Alerts**: Review alert details and context
        2. **Assess Impact**: Determine effect on trading operations
        3. **Take Action**: Implement appropriate remediation steps
        4. **Monitor Progress**: Track metric improvements
        5. **Document Resolution**: Log actions taken for future reference

        ### Automated Responses

        - **Resource Scaling**: Automatic resource allocation adjustments
        - **Process Throttling**: Reduce system load during high usage
        - **Failover Activation**: Switch to backup systems when necessary
        - **Alert Escalation**: Notify administrators for critical issues
        """)

    # Performance optimization tips
    with st.expander("⚡ Performance Optimization"):
        st.markdown("""
        ### System Optimization Tips

        **CPU Optimization:**
        - Monitor process CPU usage and identify resource-heavy applications
        - Implement process priority management for critical trading systems
        - Use CPU affinity to dedicate cores to specific trading processes
        - Schedule maintenance tasks during off-peak hours

        **Memory Optimization:**
        - Monitor memory leaks in long-running trading applications
        - Implement garbage collection optimization for better performance
        - Use memory mapping for large datasets and historical data
        - Configure swap space appropriately for system stability

        **Network Optimization:**
        - Monitor market data feed latency and optimize connections
        - Implement connection pooling for API calls to reduce overhead
        - Use compression for large data transfers when appropriate
        - Configure quality-of-service (QoS) for critical trading traffic

        **Trading Performance:**
        - Optimize order execution algorithms for better fill rates
        - Monitor slippage and implement smart order routing
        - Use historical analysis to optimize position sizing
        - Implement risk controls to prevent excessive exposure

        ### Best Practices

        1. **Regular Monitoring**: Check metrics dashboard daily
        2. **Threshold Tuning**: Adjust alert thresholds based on usage patterns
        3. **Capacity Planning**: Plan for growth and peak usage scenarios
        4. **Performance Baselines**: Establish normal operating ranges
        5. **Continuous Improvement**: Regular system optimization and updates
        """)

    # Sample data note
    st.info("""
    📝 **Note**: Currently displaying simulated system and business metrics for demonstration.
    Live integration with actual system monitoring and trading data will provide real-time insights
    when connected to production trading infrastructure.
    """)


if __name__ == "__main__":
    show_analytics()