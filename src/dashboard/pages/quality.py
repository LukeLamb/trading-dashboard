"""
Data Quality page for Trading Dashboard.

This page provides comprehensive data quality monitoring and management
capabilities for all data sources in the trading system.
"""

import streamlit as st
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.dashboard.components.quality_dashboard import render_data_quality_dashboard


def show_quality():
    """Display the data quality monitoring page."""
    st.markdown("## 🎯 Data Quality Monitoring")

    st.markdown("""
    Comprehensive data quality monitoring and management system for all trading data sources.
    Monitor quality grades, track trends, manage alerts, and optimize data reliability.
    """)

    # Quick info section
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Quality Grades", "A-F Scale", help="A+ (100) to F (0) quality scoring")

    with col2:
        st.metric("Alert System", "Multi-Level", help="Critical, High, Medium, Low, Info alerts")

    with col3:
        st.metric("Trend Analysis", "Historical", help="Quality trends over time with predictions")

    with col4:
        st.metric("Auto Actions", "Smart Rules", help="Automatic responses to quality issues")

    st.markdown("---")

    # Main quality dashboard
    render_data_quality_dashboard()

    st.markdown("---")

    # Feature information
    st.markdown("### 🎯 Quality Features")

    feature_col1, feature_col2 = st.columns(2)

    with feature_col1:
        st.markdown("""
        **Quality Monitoring:**
        - 🎯 **A-F Quality Grades** with numerical scores
        - 📊 **Real-time Quality Metrics** from Market Data Agent
        - 📈 **Historical Trend Analysis** with predictions
        - 🔍 **Source Reliability Tracking** and comparison

        **Alert Management:**
        - 🚨 **Multi-level Alert System** (Critical to Info)
        - 📅 **Alert Timeline Visualization** with resolution tracking
        - 🔔 **Threshold-based Notifications** with customizable levels
        - ✅ **Manual and Automatic Resolution** with audit trail
        """)

    with feature_col2:
        st.markdown("""
        **Quality Actions:**
        - 🔄 **Automatic Source Switching** on quality drops
        - 💡 **Quality Improvement Recommendations** with actionable steps
        - 🎯 **Threshold Configuration** for custom quality standards
        - 📊 **Performance Optimization Suggestions** based on metrics

        **Integration Features:**
        - 🤖 **Market Data Agent Integration** for live quality data
        - 📈 **Chart Quality Indicators** showing data source reliability
        - 🔍 **Quality-aware Data Selection** for optimal trading decisions
        - 📊 **Quality-weighted Aggregation** for multi-source data
        """)

    # Quality scoring guide
    with st.expander("📖 Quality Scoring Guide"):
        st.markdown("""
        ### Understanding Quality Grades

        **Grade Scale (A-F):**
        - **A+ (97-100)**: Exceptional quality - Premium data sources with near-perfect reliability
        - **A (93-96)**: Excellent quality - High-reliability sources suitable for critical trading
        - **A- (90-92)**: Very good quality - Reliable sources with minor limitations
        - **B+ (87-89)**: Good quality - Acceptable for most trading applications
        - **B (83-86)**: Fair quality - Suitable with some limitations
        - **B- (80-82)**: Marginal quality - Requires monitoring and backup sources
        - **C+ (77-79)**: Poor quality - Use with caution, high error potential
        - **C (73-76)**: Very poor quality - Not recommended for trading decisions
        - **C- (70-72)**: Unreliable - Significant data issues present
        - **D (65-69)**: Critical issues - Immediate attention required
        - **F (0-64)**: Failing - Data source unusable

        ### Quality Metrics Explained

        **Key Components:**
        - **Response Time**: API latency and connection speed
        - **Data Completeness**: Percentage of expected data points received
        - **Data Accuracy**: Validation against reference sources
        - **Reliability Score**: Historical consistency and availability
        - **Uptime Percentage**: Service availability over time
        - **Error Rate**: Frequency of failed requests or corrupted data

        ### Alert Severity Levels

        - **Critical**: Immediate action required - trading operations may be affected
        - **High**: Urgent attention needed - quality degradation detected
        - **Medium**: Monitor closely - minor issues that may escalate
        - **Low**: Awareness only - informational quality changes
        - **Info**: General notifications - routine quality updates
        """)

    # Quality best practices
    with st.expander("✨ Quality Best Practices"):
        st.markdown("""
        ### Optimization Recommendations

        **Source Management:**
        1. **Diversify Data Sources**: Use multiple sources for critical data
        2. **Monitor Quality Trends**: Watch for gradual degradation patterns
        3. **Set Appropriate Thresholds**: Customize alerts for your trading strategy
        4. **Regular Quality Reviews**: Weekly assessment of source performance

        **Alert Response:**
        1. **Prioritize Critical Alerts**: Address failing sources immediately
        2. **Investigate Patterns**: Look for systematic issues vs. transient problems
        3. **Document Resolutions**: Track what fixes work for future reference
        4. **Test Backup Sources**: Ensure failover systems work correctly

        **Performance Optimization:**
        1. **Cache Strategic Data**: Reduce load on high-quality sources
        2. **Load Balance Requests**: Distribute across multiple endpoints
        3. **Implement Circuit Breakers**: Protect against cascading failures
        4. **Monitor Resource Usage**: Track API rate limits and quotas

        **Quality Integration:**
        1. **Weight by Quality**: Give higher-quality sources more influence
        2. **Quality-aware Routing**: Direct critical requests to best sources
        3. **Automatic Degradation**: Gracefully handle quality drops
        4. **Quality Reporting**: Include quality metrics in trading analytics
        """)

    # Sample data note
    st.info("""
    📝 **Note**: Currently displaying simulated quality data for demonstration purposes.
    Live quality integration with Market Data Agent will be available when the agent is running
    and configured with quality monitoring enabled.
    """)


if __name__ == "__main__" or True:
    show_quality()