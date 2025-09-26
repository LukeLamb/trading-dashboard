"""
Data Quality Dashboard Components for Trading Dashboard.

This module provides Streamlit components for data quality monitoring,
visualization, and management interfaces.
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.dashboard.components.data_quality import (
    DataQualityManager, QualityGrade, AlertSeverity, DataSourceQuality, QualityAlert
)


class QualityDashboard:
    """Main dashboard class for data quality monitoring."""

    def __init__(self):
        """Initialize quality dashboard."""
        # Initialize quality manager in session state
        if 'quality_manager' not in st.session_state:
            st.session_state.quality_manager = DataQualityManager()

        self.quality_manager = st.session_state.quality_manager

    def render_quality_overview(self):
        """Render the main quality overview dashboard."""
        st.markdown("## 📊 Data Quality Overview")

        # Quality metrics row
        self._render_quality_metrics()

        st.markdown("---")

        # Main quality visualization
        col1, col2 = st.columns([2, 1])

        with col1:
            # Quality overview chart
            st.markdown("### 📈 Source Quality Scores")
            quality_chart = self.quality_manager.create_quality_overview_chart()
            st.plotly_chart(quality_chart, use_container_width=True)

        with col2:
            # Quality distribution
            self._render_quality_distribution()

        st.markdown("---")

        # Quality comparison matrix
        st.markdown("### 🔍 Quality Comparison Matrix")
        comparison_chart = self.quality_manager.create_quality_comparison_matrix()
        st.plotly_chart(comparison_chart, use_container_width=True)

    def _render_quality_metrics(self):
        """Render key quality metrics."""
        col1, col2, col3, col4, col5 = st.columns(5)

        # Overall quality score
        overall_score = self.quality_manager.get_overall_quality_score()
        overall_grade = self.quality_manager._score_to_grade(overall_score)

        with col1:
            st.metric(
                "Overall Quality",
                f"{overall_grade.value} ({overall_score:.1f})",
                help="Weighted average quality across all sources"
            )

        # Active sources
        active_sources = len(self.quality_manager.source_qualities)
        with col2:
            st.metric(
                "Active Sources",
                str(active_sources),
                help="Number of active data sources"
            )

        # Active alerts
        active_alerts = len(self.quality_manager.active_alerts)
        with col3:
            alert_color = "🔴" if active_alerts > 0 else "🟢"
            st.metric(
                "Active Alerts",
                f"{alert_color} {active_alerts}",
                help="Number of unresolved quality alerts"
            )

        # Best performing source
        best_source = max(self.quality_manager.source_qualities.values(),
                         key=lambda x: x.score, default=None)
        with col4:
            if best_source:
                st.metric(
                    "Best Source",
                    best_source.source_name,
                    f"{best_source.grade.value} ({best_source.score:.1f})",
                    help="Highest quality data source"
                )

        # Worst performing source
        worst_source = min(self.quality_manager.source_qualities.values(),
                          key=lambda x: x.score, default=None)
        with col5:
            if worst_source:
                st.metric(
                    "Needs Attention",
                    worst_source.source_name,
                    f"{worst_source.grade.value} ({worst_source.score:.1f})",
                    delta_color="inverse",
                    help="Lowest quality data source"
                )

    def _render_quality_distribution(self):
        """Render quality grade distribution."""
        st.markdown("### 📊 Grade Distribution")

        distribution = self.quality_manager.get_quality_distribution()

        # Create pie chart data
        labels = []
        values = []
        colors = []

        for grade_str, count in distribution.items():
            if count > 0:
                grade = QualityGrade(grade_str)
                labels.append(f"{grade_str} ({count})")
                values.append(count)
                colors.append(grade.color)

        if values:
            # Create simple pie chart visualization
            total = sum(values)
            for i, (label, value, color) in enumerate(zip(labels, values, colors)):
                percentage = (value / total) * 100
                st.markdown(
                    f"<div style='display: flex; align-items: center; margin: 8px 0;'>"
                    f"<div style='width: 16px; height: 16px; background-color: {color}; "
                    f"border-radius: 2px; margin-right: 8px;'></div>"
                    f"<span style='font-size: 14px;'>{label}: {percentage:.1f}%</span>"
                    f"</div>",
                    unsafe_allow_html=True
                )
        else:
            st.info("No quality data available")

    def render_source_details(self):
        """Render detailed view for individual sources."""
        st.markdown("## 🔍 Source Quality Details")

        if not self.quality_manager.source_qualities:
            st.warning("No data sources configured")
            return

        # Source selection
        source_names = {q.source_name: q.source_id
                       for q in self.quality_manager.source_qualities.values()}

        selected_source_name = st.selectbox(
            "Select Data Source",
            options=list(source_names.keys()),
            help="Choose a data source to view detailed quality metrics"
        )

        if not selected_source_name:
            return

        source_id = source_names[selected_source_name]
        quality = self.quality_manager.source_qualities[source_id]

        # Source quality overview
        self._render_source_overview(quality)

        st.markdown("---")

        # Quality trend chart
        col1, col2 = st.columns([3, 1])

        with col1:
            st.markdown("### 📈 Quality Trend")
            trend_period = st.selectbox("Time Period", [7, 14, 30], index=0)
            trend_chart = self.quality_manager.create_quality_trend_chart(
                source_id, days=trend_period
            )
            st.plotly_chart(trend_chart, use_container_width=True)

        with col2:
            # Detailed metrics
            self._render_detailed_metrics(quality)

    def _render_source_overview(self, quality: DataSourceQuality):
        """Render overview for a single source."""
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            # Quality grade with color
            grade_color = quality.grade.color
            st.markdown(
                f"<div style='text-align: center; padding: 20px; "
                f"background-color: {grade_color}; color: white; border-radius: 10px;'>"
                f"<h2 style='margin: 0; color: white;'>{quality.grade.value}</h2>"
                f"<p style='margin: 0; color: white;'>Quality Grade</p>"
                f"</div>",
                unsafe_allow_html=True
            )

        with col2:
            st.metric(
                "Quality Score",
                f"{quality.score:.1f}",
                help="Overall quality score (0-100)"
            )

        with col3:
            st.metric(
                "Response Time",
                f"{quality.response_time:.0f}ms",
                help="Average API response time"
            )

        with col4:
            st.metric(
                "Uptime",
                f"{quality.uptime_percentage:.1f}%",
                help="Source availability percentage"
            )

    def _render_detailed_metrics(self, quality: DataSourceQuality):
        """Render detailed metrics for a source."""
        st.markdown("### 📊 Detailed Metrics")

        metrics_data = [
            ("Success Rate", f"{quality.success_rate:.1f}%", quality.success_rate),
            ("Data Completeness", f"{quality.data_completeness:.1f}%", quality.data_completeness),
            ("Data Accuracy", f"{quality.data_accuracy:.1f}%", quality.data_accuracy),
            ("Reliability", f"{quality.reliability_score:.1f}%", quality.reliability_score)
        ]

        for name, value, score in metrics_data:
            # Create a simple progress bar visualization
            color = "#10B981" if score >= 95 else "#F59E0B" if score >= 80 else "#EF4444"

            st.markdown(
                f"<div style='margin: 12px 0;'>"
                f"<div style='display: flex; justify-content: space-between; margin-bottom: 4px;'>"
                f"<span style='font-weight: 500;'>{name}</span>"
                f"<span style='font-weight: 500;'>{value}</span>"
                f"</div>"
                f"<div style='background-color: #E5E7EB; border-radius: 4px; height: 8px;'>"
                f"<div style='background-color: {color}; height: 8px; border-radius: 4px; "
                f"width: {score}%; transition: width 0.3s ease;'></div>"
                f"</div>"
                f"</div>",
                unsafe_allow_html=True
            )

        # Last updated
        time_ago = datetime.now() - quality.last_updated
        if time_ago.total_seconds() < 60:
            last_updated = "Just now"
        elif time_ago.total_seconds() < 3600:
            last_updated = f"{int(time_ago.total_seconds() / 60)} minutes ago"
        else:
            last_updated = f"{int(time_ago.total_seconds() / 3600)} hours ago"

        st.caption(f"Last updated: {last_updated}")

    def render_quality_alerts(self):
        """Render quality alerts dashboard."""
        st.markdown("## 🚨 Quality Alerts")

        # Alert summary
        self._render_alert_summary()

        st.markdown("---")

        # Alert timeline
        st.markdown("### 📅 Alert Timeline")
        timeline_period = st.selectbox("Timeline Period", [1, 7, 14, 30], index=1, key="alert_timeline")
        alert_timeline = self.quality_manager.create_alert_timeline(days=timeline_period)
        st.plotly_chart(alert_timeline, use_container_width=True)

        st.markdown("---")

        # Active alerts
        col1, col2 = st.columns([2, 1])

        with col1:
            self._render_active_alerts()

        with col2:
            self._render_quality_recommendations()

    def _render_alert_summary(self):
        """Render alert summary metrics."""
        col1, col2, col3, col4 = st.columns(4)

        # Count alerts by severity
        severity_counts = {severity: 0 for severity in AlertSeverity}
        for alert in self.quality_manager.active_alerts.values():
            severity_counts[alert.severity] += 1

        with col1:
            critical_count = severity_counts[AlertSeverity.CRITICAL]
            color = "🔴" if critical_count > 0 else "🟢"
            st.metric(
                "Critical Alerts",
                f"{color} {critical_count}",
                help="Critical quality issues requiring immediate attention"
            )

        with col2:
            high_count = severity_counts[AlertSeverity.HIGH]
            color = "🟠" if high_count > 0 else "🟢"
            st.metric(
                "High Priority",
                f"{color} {high_count}",
                help="High priority quality issues"
            )

        with col3:
            medium_count = severity_counts[AlertSeverity.MEDIUM] + severity_counts[AlertSeverity.LOW]
            st.metric(
                "Medium/Low",
                f"🟡 {medium_count}",
                help="Medium and low priority alerts"
            )

        with col4:
            resolved_today = len([a for a in self.quality_manager.resolved_alerts
                                if a.resolution_time and
                                (datetime.now() - a.resolution_time).days == 0])
            st.metric(
                "Resolved Today",
                f"✅ {resolved_today}",
                help="Alerts resolved in the last 24 hours"
            )

    def _render_active_alerts(self):
        """Render list of active alerts."""
        st.markdown("### 🔔 Active Alerts")

        if not self.quality_manager.active_alerts:
            st.success("🎉 No active alerts! All data sources are performing well.")
            return

        # Sort alerts by severity and timestamp
        severity_order = {
            AlertSeverity.CRITICAL: 0,
            AlertSeverity.HIGH: 1,
            AlertSeverity.MEDIUM: 2,
            AlertSeverity.LOW: 3,
            AlertSeverity.INFO: 4
        }

        sorted_alerts = sorted(
            self.quality_manager.active_alerts.values(),
            key=lambda x: (severity_order[x.severity], x.timestamp),
            reverse=True
        )

        for alert in sorted_alerts:
            self._render_alert_card(alert)

    def _render_alert_card(self, alert: QualityAlert):
        """Render individual alert card."""
        # Severity styling
        severity_styles = {
            AlertSeverity.CRITICAL: {"color": "#DC2626", "bg": "#FEE2E2"},
            AlertSeverity.HIGH: {"color": "#EA580C", "bg": "#FED7AA"},
            AlertSeverity.MEDIUM: {"color": "#D97706", "bg": "#FEF3C7"},
            AlertSeverity.LOW: {"color": "#65A30D", "bg": "#DCFCE7"},
            AlertSeverity.INFO: {"color": "#2563EB", "bg": "#DBEAFE"}
        }

        style = severity_styles[alert.severity]
        time_ago = datetime.now() - alert.timestamp

        if time_ago.total_seconds() < 3600:
            time_str = f"{int(time_ago.total_seconds() / 60)} minutes ago"
        else:
            time_str = f"{int(time_ago.total_seconds() / 3600)} hours ago"

        # Get source name
        source_name = "Unknown Source"
        if alert.source_id in self.quality_manager.source_qualities:
            source_name = self.quality_manager.source_qualities[alert.source_id].source_name

        with st.container():
            st.markdown(
                f"<div style='border: 1px solid {style['color']}; border-radius: 8px; "
                f"padding: 16px; margin: 8px 0; background-color: {style['bg']};'>"
                f"<div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;'>"
                f"<span style='font-weight: bold; color: {style['color']};'>"
                f"{alert.severity.value.upper()} - {alert.title}"
                f"</span>"
                f"<span style='color: #6B7280; font-size: 12px;'>{time_str}</span>"
                f"</div>"
                f"<div style='margin-bottom: 8px; color: #374151;'>{alert.message}</div>"
                f"<div style='color: #6B7280; font-size: 12px;'>Source: {source_name}</div>"
                f"</div>",
                unsafe_allow_html=True
            )

            # Resolve button
            if st.button(f"Resolve Alert", key=f"resolve_{alert.alert_id}"):
                self.quality_manager.resolve_alert(
                    alert.alert_id,
                    f"Manually resolved by user at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                )
                st.success(f"Alert '{alert.title}' has been resolved")
                st.rerun()

    def _render_quality_recommendations(self):
        """Render quality improvement recommendations."""
        st.markdown("### 💡 Recommendations")

        recommendations = self.quality_manager.get_quality_recommendations()

        if not recommendations:
            st.info("No recommendations at this time. All sources are performing well!")
            return

        for i, rec in enumerate(recommendations[:5]):  # Show top 5
            # Recommendation styling
            rec_styles = {
                'high': {"color": "#DC2626", "icon": "🔴"},
                'medium': {"color": "#F59E0B", "icon": "🟡"},
                'low': {"color": "#10B981", "icon": "🟢"}
            }

            style = rec_styles.get(rec['severity'], {"color": "#6B7280", "icon": "ℹ️"})

            with st.expander(f"{style['icon']} {rec['title']}"):
                st.markdown(f"**Source:** {rec['source']}")
                st.markdown(f"**Issue:** {rec['message']}")

                # Action suggestions based on type
                if rec['action'] == 'investigate_source':
                    st.markdown("**Suggested Actions:**")
                    st.markdown("- Check source API status and documentation")
                    st.markdown("- Verify network connectivity and firewall settings")
                    st.markdown("- Review error logs for specific failure patterns")
                    st.markdown("- Consider temporary failover to backup source")

                elif rec['action'] == 'optimize_performance':
                    st.markdown("**Suggested Actions:**")
                    st.markdown("- Implement response caching with appropriate TTL")
                    st.markdown("- Use connection pooling and keep-alive")
                    st.markdown("- Consider CDN or geographically closer endpoints")
                    st.markdown("- Optimize request parameters and data filtering")

                elif rec['action'] == 'add_backup_source':
                    st.markdown("**Suggested Actions:**")
                    st.markdown("- Configure secondary data source for redundancy")
                    st.markdown("- Implement data quality comparison between sources")
                    st.markdown("- Set up automatic failover procedures")
                    st.markdown("- Monitor data consistency across sources")

    def render_quality_settings(self):
        """Render quality monitoring settings."""
        st.markdown("## ⚙️ Quality Settings")

        # Threshold configuration
        st.markdown("### 🎯 Quality Thresholds")

        col1, col2 = st.columns(2)

        with col1:
            critical_threshold = st.slider(
                "Critical Score Threshold",
                min_value=0.0,
                max_value=100.0,
                value=self.quality_manager.thresholds['critical_score'],
                step=5.0,
                help="Quality scores below this threshold trigger critical alerts"
            )

            warning_threshold = st.slider(
                "Warning Score Threshold",
                min_value=critical_threshold,
                max_value=100.0,
                value=self.quality_manager.thresholds['warning_score'],
                step=5.0,
                help="Quality scores below this threshold trigger warning alerts"
            )

        with col2:
            response_threshold = st.slider(
                "Response Time Threshold (ms)",
                min_value=100.0,
                max_value=5000.0,
                value=self.quality_manager.thresholds['response_time_threshold'],
                step=100.0,
                help="Response times above this threshold trigger alerts"
            )

            completeness_threshold = st.slider(
                "Data Completeness Threshold (%)",
                min_value=50.0,
                max_value=100.0,
                value=self.quality_manager.thresholds['completeness_threshold'] * 100,
                step=1.0,
                help="Data completeness below this threshold triggers alerts"
            ) / 100

        # Update thresholds
        if st.button("Update Thresholds"):
            self.quality_manager.thresholds.update({
                'critical_score': critical_threshold,
                'warning_score': warning_threshold,
                'response_time_threshold': response_threshold,
                'completeness_threshold': completeness_threshold
            })
            st.success("Quality thresholds updated successfully!")

        st.markdown("---")

        # Data source management
        st.markdown("### 📊 Data Source Management")

        if self.quality_manager.source_qualities:
            st.markdown("**Currently Monitored Sources:**")

            for source_id, quality in self.quality_manager.source_qualities.items():
                col1, col2, col3 = st.columns([2, 1, 1])

                with col1:
                    st.markdown(f"**{quality.source_name}** ({quality.source_id})")

                with col2:
                    grade_color = quality.grade.color
                    st.markdown(
                        f"<span style='color: {grade_color}; font-weight: bold;'>"
                        f"{quality.grade.value} ({quality.score:.1f})"
                        f"</span>",
                        unsafe_allow_html=True
                    )

                with col3:
                    st.caption(f"Updated {(datetime.now() - quality.last_updated).seconds // 60}m ago")

        else:
            st.info("No data sources currently configured for quality monitoring.")


def render_data_quality_dashboard():
    """Main function to render the data quality dashboard."""
    dashboard = QualityDashboard()

    # Quality dashboard tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Overview",
        "🔍 Source Details",
        "🚨 Alerts",
        "⚙️ Settings"
    ])

    with tab1:
        dashboard.render_quality_overview()

    with tab2:
        dashboard.render_source_details()

    with tab3:
        dashboard.render_quality_alerts()

    with tab4:
        dashboard.render_quality_settings()