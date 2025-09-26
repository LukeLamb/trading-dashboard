"""
Metrics Dashboard Interface for Trading Dashboard.

This module provides the user interface for system metrics monitoring,
business metrics tracking, and customizable dashboard layouts.
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.dashboard.components.metrics import SystemMetricsManager, MetricType, AlertLevel


class MetricsDashboard:
    """Main dashboard class for system and business metrics."""

    def __init__(self):
        """Initialize metrics dashboard."""
        # Initialize metrics manager in session state
        if 'metrics_manager' not in st.session_state:
            st.session_state.metrics_manager = SystemMetricsManager()

        self.metrics_manager = st.session_state.metrics_manager

        # Dashboard layouts
        self.available_layouts = {
            'default': {
                'name': 'Default Layout',
                'description': 'Standard system and business metrics overview',
                'widgets': ['system_overview', 'performance_charts', 'business_metrics']
            },
            'system_focus': {
                'name': 'System Focus',
                'description': 'Detailed system performance monitoring',
                'widgets': ['system_overview', 'cpu_memory_chart', 'network_chart', 'system_alerts']
            },
            'business_focus': {
                'name': 'Business Focus',
                'description': 'Trading and portfolio performance metrics',
                'widgets': ['business_overview', 'portfolio_chart', 'pnl_chart', 'risk_metrics']
            },
            'executive': {
                'name': 'Executive Summary',
                'description': 'High-level KPIs and summary metrics',
                'widgets': ['kpi_summary', 'portfolio_chart', 'system_health']
            }
        }

    def render_metrics_overview(self):
        """Render the main metrics overview dashboard."""
        st.markdown("## 📊 System Metrics Dashboard")

        # Layout selection
        layout_col, refresh_col = st.columns([3, 1])

        with layout_col:
            selected_layout = st.selectbox(
                "Dashboard Layout",
                options=list(self.available_layouts.keys()),
                format_func=lambda x: self.available_layouts[x]['name'],
                help="Choose dashboard layout and widget arrangement"
            )

        with refresh_col:
            if st.button("🔄 Refresh Metrics", help="Update all metrics with latest data"):
                st.session_state.metrics_manager = SystemMetricsManager()
                st.rerun()

        st.markdown("---")

        # Render selected layout
        self._render_layout(selected_layout)

    def _render_layout(self, layout_key: str):
        """Render specific dashboard layout."""
        layout = self.available_layouts[layout_key]
        widgets = layout['widgets']

        for widget in widgets:
            if widget == 'system_overview':
                self._render_system_overview()
            elif widget == 'performance_charts':
                self._render_performance_charts()
            elif widget == 'business_metrics':
                self._render_business_metrics()
            elif widget == 'cpu_memory_chart':
                self._render_cpu_memory_chart()
            elif widget == 'network_chart':
                self._render_network_chart()
            elif widget == 'system_alerts':
                self._render_system_alerts()
            elif widget == 'business_overview':
                self._render_business_overview()
            elif widget == 'portfolio_chart':
                self._render_portfolio_chart()
            elif widget == 'pnl_chart':
                self._render_pnl_chart()
            elif widget == 'risk_metrics':
                self._render_risk_metrics()
            elif widget == 'kpi_summary':
                self._render_kpi_summary()
            elif widget == 'system_health':
                self._render_system_health()

    def _render_system_overview(self):
        """Render system performance overview."""
        st.markdown("### 🖥️ System Performance")

        latest_system = self.metrics_manager.get_latest_system_metrics()

        if not latest_system:
            st.warning("No system metrics available")
            return

        col1, col2, col3, col4 = st.columns(4)

        # CPU Usage
        if "CPU Usage" in latest_system:
            cpu_metric = latest_system["CPU Usage"]
            cpu_color = self._get_alert_color(cpu_metric.alert_level)
            with col1:
                st.metric(
                    "CPU Usage",
                    f"{cpu_metric.value:.1f}%",
                    help=f"Current CPU utilization | Alert: {cpu_metric.alert_level.value.title()}"
                )
                st.markdown(f"<div style='height: 5px; background-color: {cpu_color}; border-radius: 2px;'></div>",
                           unsafe_allow_html=True)

        # Memory Usage
        if "Memory Usage" in latest_system:
            memory_metric = latest_system["Memory Usage"]
            memory_color = self._get_alert_color(memory_metric.alert_level)
            with col2:
                st.metric(
                    "Memory Usage",
                    f"{memory_metric.value:.1f}%",
                    help=f"Current memory utilization | Alert: {memory_metric.alert_level.value.title()}"
                )
                st.markdown(f"<div style='height: 5px; background-color: {memory_color}; border-radius: 2px;'></div>",
                           unsafe_allow_html=True)

        # Disk Usage
        if "Disk Usage" in latest_system:
            disk_metric = latest_system["Disk Usage"]
            disk_color = self._get_alert_color(disk_metric.alert_level)
            with col3:
                st.metric(
                    "Disk Usage",
                    f"{disk_metric.value:.1f}%",
                    help=f"Current disk utilization | Alert: {disk_metric.alert_level.value.title()}"
                )
                st.markdown(f"<div style='height: 5px; background-color: {disk_color}; border-radius: 2px;'></div>",
                           unsafe_allow_html=True)

        # System Health Score
        health_score, health_status = self.metrics_manager.get_system_health_score()
        health_color = self._get_health_color(health_score)
        with col4:
            st.metric(
                "System Health",
                f"{health_score:.0f}/100",
                help=f"Overall system health score | Status: {health_status}"
            )
            st.markdown(f"<div style='height: 5px; background-color: {health_color}; border-radius: 2px;'></div>",
                       unsafe_allow_html=True)

        # System details
        with st.expander("📋 System Details"):
            detail_col1, detail_col2 = st.columns(2)

            with detail_col1:
                if "CPU Cores" in latest_system:
                    st.markdown(f"**CPU Cores:** {latest_system['CPU Cores'].value:.0f}")
                if "Memory Total" in latest_system:
                    st.markdown(f"**Total Memory:** {latest_system['Memory Total'].value:.1f} GB")
                if "Disk Total" in latest_system:
                    st.markdown(f"**Total Disk:** {latest_system['Disk Total'].value:.1f} GB")

            with detail_col2:
                if "CPU Frequency" in latest_system:
                    st.markdown(f"**CPU Frequency:** {latest_system['CPU Frequency'].value:.0f} MHz")
                if "Memory Available" in latest_system:
                    st.markdown(f"**Available Memory:** {latest_system['Memory Available'].value:.1f} GB")
                if "Disk Free" in latest_system:
                    st.markdown(f"**Free Disk:** {latest_system['Disk Free'].value:.1f} GB")

    def _render_performance_charts(self):
        """Render performance charts."""
        st.markdown("### 📈 Performance Charts")

        chart_col1, chart_col2 = st.columns(2)

        with chart_col1:
            # CPU and Memory chart
            cpu_memory_chart = self.metrics_manager.create_cpu_memory_chart(hours=24)
            st.plotly_chart(cpu_memory_chart, use_container_width=True)

        with chart_col2:
            # Network activity chart
            network_chart = self.metrics_manager.create_network_chart(hours=24)
            st.plotly_chart(network_chart, use_container_width=True)

    def _render_business_metrics(self):
        """Render business metrics overview."""
        st.markdown("### 💰 Business Performance")

        latest_business = self.metrics_manager.get_latest_business_metrics()

        if not latest_business:
            st.warning("No business metrics available")
            return

        col1, col2, col3, col4 = st.columns(4)

        # Portfolio Value
        if "Portfolio Value" in latest_business:
            portfolio = latest_business["Portfolio Value"]
            change_indicator = ""
            if portfolio.change_percent_24h is not None:
                change_indicator = f"{portfolio.change_percent_24h:+.2f}%"

            with col1:
                st.metric(
                    "Portfolio Value",
                    f"${portfolio.value:,.2f}",
                    change_indicator,
                    help="Total portfolio value with 24h change"
                )

        # Daily P&L
        if "Daily P&L" in latest_business:
            pnl = latest_business["Daily P&L"]
            pnl_color = "#10B981" if pnl.value >= 0 else "#EF4444"
            with col2:
                st.metric(
                    "Daily P&L",
                    f"${pnl.value:,.2f}",
                    help="Today's profit and loss"
                )
                st.markdown(f"<div style='height: 5px; background-color: {pnl_color}; border-radius: 2px;'></div>",
                           unsafe_allow_html=True)

        # Risk Exposure
        if "Risk Exposure" in latest_business:
            risk = latest_business["Risk Exposure"]
            with col3:
                st.metric(
                    "Risk Exposure",
                    f"${risk.value:,.0f}",
                    help="Current risk exposure across all positions"
                )

        # Sharpe Ratio
        if "Sharpe Ratio" in latest_business:
            sharpe = latest_business["Sharpe Ratio"]
            sharpe_color = "#10B981" if sharpe.value > 1.5 else "#F59E0B" if sharpe.value > 1.0 else "#EF4444"
            with col4:
                st.metric(
                    "Sharpe Ratio",
                    f"{sharpe.value:.2f}",
                    help="Risk-adjusted return metric"
                )
                st.markdown(f"<div style='height: 5px; background-color: {sharpe_color}; border-radius: 2px;'></div>",
                           unsafe_allow_html=True)

    def _render_cpu_memory_chart(self):
        """Render detailed CPU and memory chart."""
        st.markdown("### 🖥️ CPU & Memory Usage")

        time_range = st.selectbox("Time Range", [6, 12, 24, 48], index=2, help="Hours of data to display")
        cpu_memory_chart = self.metrics_manager.create_cpu_memory_chart(hours=time_range)
        st.plotly_chart(cpu_memory_chart, use_container_width=True)

    def _render_network_chart(self):
        """Render network activity chart."""
        st.markdown("### 🌐 Network Activity")

        time_range = st.selectbox("Network Time Range", [6, 12, 24, 48], index=2, key="network_time")
        network_chart = self.metrics_manager.create_network_chart(hours=time_range)
        st.plotly_chart(network_chart, use_container_width=True)

    def _render_system_alerts(self):
        """Render system alerts and warnings."""
        st.markdown("### 🚨 System Alerts")

        latest_system = self.metrics_manager.get_latest_system_metrics()
        alerts = []

        for name, metric in latest_system.items():
            if metric.alert_level in [AlertLevel.WARNING, AlertLevel.CRITICAL]:
                alerts.append({
                    'metric': name,
                    'value': metric.value,
                    'unit': metric.unit,
                    'level': metric.alert_level,
                    'timestamp': metric.timestamp
                })

        if not alerts:
            st.success("🎉 No active system alerts. All metrics are within normal ranges.")
        else:
            for alert in alerts:
                alert_color = "#F59E0B" if alert['level'] == AlertLevel.WARNING else "#EF4444"
                alert_icon = "⚠️" if alert['level'] == AlertLevel.WARNING else "🔴"

                st.markdown(
                    f"<div style='padding: 12px; border-left: 4px solid {alert_color}; "
                    f"background-color: rgba(251, 191, 36, 0.1); margin: 8px 0; border-radius: 4px;'>"
                    f"<strong>{alert_icon} {alert['level'].value.title()}: {alert['metric']}</strong><br>"
                    f"Current value: {alert['value']:.1f}{alert['unit']}<br>"
                    f"<small>Last updated: {alert['timestamp'].strftime('%H:%M:%S')}</small>"
                    f"</div>",
                    unsafe_allow_html=True
                )

    def _render_business_overview(self):
        """Render detailed business metrics overview."""
        st.markdown("### 💼 Business Overview")

        latest_business = self.metrics_manager.get_latest_business_metrics()

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Portfolio Metrics**")
            if "Portfolio Value" in latest_business:
                portfolio = latest_business["Portfolio Value"]
                st.markdown(f"💰 **Portfolio Value:** ${portfolio.value:,.2f}")
                if portfolio.change_24h:
                    change_color = "green" if portfolio.change_24h >= 0 else "red"
                    st.markdown(f"📈 **24h Change:** <span style='color: {change_color};'>${portfolio.change_24h:,.2f} ({portfolio.change_percent_24h:+.2f}%)</span>",
                               unsafe_allow_html=True)

            if "Total Return" in latest_business:
                total_return = latest_business["Total Return"]
                st.markdown(f"📊 **Total Return:** ${total_return.value:,.2f}")

        with col2:
            st.markdown("**Trading Metrics**")
            if "Active Positions" in latest_business:
                positions = latest_business["Active Positions"]
                st.markdown(f"🎯 **Active Positions:** {positions.value:.0f}")

            if "Win Rate" in latest_business:
                win_rate = latest_business["Win Rate"]
                st.markdown(f"🏆 **Win Rate:** {win_rate.value:.1f}%")

            if "Average Trade" in latest_business:
                avg_trade = latest_business["Average Trade"]
                st.markdown(f"💹 **Average Trade:** ${avg_trade.value:.2f}")

    def _render_portfolio_chart(self):
        """Render portfolio performance chart."""
        st.markdown("### 📈 Portfolio Performance")

        time_range = st.selectbox("Portfolio Time Range", [7, 14, 30, 60], index=2, key="portfolio_time")
        portfolio_chart = self.metrics_manager.create_portfolio_chart(days=time_range)
        st.plotly_chart(portfolio_chart, use_container_width=True)

    def _render_pnl_chart(self):
        """Render P&L chart."""
        st.markdown("### 💰 Daily P&L")

        time_range = st.selectbox("P&L Time Range", [7, 14, 30, 60], index=2, key="pnl_time")
        pnl_chart = self.metrics_manager.create_pnl_chart(days=time_range)
        st.plotly_chart(pnl_chart, use_container_width=True)

    def _render_risk_metrics(self):
        """Render risk management metrics."""
        st.markdown("### ⚠️ Risk Management")

        latest_business = self.metrics_manager.get_latest_business_metrics()

        col1, col2, col3 = st.columns(3)

        with col1:
            if "Risk Exposure" in latest_business:
                risk = latest_business["Risk Exposure"]
                st.metric(
                    "Risk Exposure",
                    f"${risk.value:,.0f}",
                    help="Total risk exposure across all positions"
                )

        with col2:
            if "Max Drawdown" in latest_business:
                drawdown = latest_business["Max Drawdown"]
                st.metric(
                    "Max Drawdown",
                    f"${drawdown.value:,.2f}",
                    help="Maximum portfolio drawdown"
                )

        with col3:
            if "Sharpe Ratio" in latest_business:
                sharpe = latest_business["Sharpe Ratio"]
                st.metric(
                    "Sharpe Ratio",
                    f"{sharpe.value:.2f}",
                    help="Risk-adjusted return metric"
                )

        # Risk assessment
        with st.expander("📊 Risk Assessment"):
            if "Risk Exposure" in latest_business and "Portfolio Value" in latest_business:
                risk_exposure = latest_business["Risk Exposure"].value
                portfolio_value = latest_business["Portfolio Value"].value
                risk_percentage = (risk_exposure / portfolio_value) * 100

                st.markdown(f"**Risk-to-Portfolio Ratio:** {risk_percentage:.1f}%")

                if risk_percentage > 50:
                    st.warning("⚠️ High risk exposure relative to portfolio size")
                elif risk_percentage > 30:
                    st.info("ℹ️ Moderate risk exposure")
                else:
                    st.success("✅ Conservative risk exposure")

    def _render_kpi_summary(self):
        """Render executive KPI summary."""
        st.markdown("### 📋 Key Performance Indicators")

        # Create KPI grid
        kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)

        latest_business = self.metrics_manager.get_latest_business_metrics()
        latest_system = self.metrics_manager.get_latest_system_metrics()

        with kpi_col1:
            if "Portfolio Value" in latest_business:
                portfolio = latest_business["Portfolio Value"]
                change_indicator = ""
                if portfolio.change_percent_24h:
                    change_indicator = f"{portfolio.change_percent_24h:+.2f}%"
                st.metric("Portfolio", f"${portfolio.value/1000:.0f}K", change_indicator)

        with kpi_col2:
            if "Daily P&L" in latest_business:
                pnl = latest_business["Daily P&L"]
                pnl_indicator = f"${pnl.value:,.0f}"
                st.metric("Today's P&L", pnl_indicator)

        with kpi_col3:
            if "Win Rate" in latest_business:
                win_rate = latest_business["Win Rate"]
                st.metric("Win Rate", f"{win_rate.value:.1f}%")

        with kpi_col4:
            health_score, _ = self.metrics_manager.get_system_health_score()
            st.metric("System Health", f"{health_score:.0f}/100")

    def _render_system_health(self):
        """Render system health summary."""
        st.markdown("### 🏥 System Health")

        health_score, health_status = self.metrics_manager.get_system_health_score()
        health_color = self._get_health_color(health_score)

        # Health score gauge (simplified)
        col1, col2 = st.columns([1, 2])

        with col1:
            st.markdown(
                f"<div style='text-align: center; padding: 20px; "
                f"background-color: {health_color}; color: white; border-radius: 10px;'>"
                f"<h2 style='margin: 0; color: white;'>{health_score:.0f}/100</h2>"
                f"<p style='margin: 0; color: white;'>Health Score</p>"
                f"</div>",
                unsafe_allow_html=True
            )

        with col2:
            st.markdown("**System Status:**")
            st.markdown(health_status)

            # Recent alerts count
            latest_system = self.metrics_manager.get_latest_system_metrics()
            alert_count = sum(1 for m in latest_system.values()
                            if m.alert_level in [AlertLevel.WARNING, AlertLevel.CRITICAL])

            if alert_count > 0:
                st.warning(f"⚠️ {alert_count} active system alerts")
            else:
                st.success("✅ No active alerts")

    def _get_alert_color(self, alert_level: AlertLevel) -> str:
        """Get color for alert level."""
        color_map = {
            AlertLevel.NORMAL: "#10B981",
            AlertLevel.WARNING: "#F59E0B",
            AlertLevel.CRITICAL: "#EF4444",
            AlertLevel.EMERGENCY: "#DC2626"
        }
        return color_map.get(alert_level, "#6B7280")

    def _get_health_color(self, health_score: float) -> str:
        """Get color for health score."""
        if health_score >= 90:
            return "#10B981"  # Green
        elif health_score >= 75:
            return "#F59E0B"  # Yellow
        elif health_score >= 60:
            return "#F97316"  # Orange
        else:
            return "#EF4444"  # Red

    def render_layout_customizer(self):
        """Render dashboard layout customization interface."""
        st.markdown("### ⚙️ Dashboard Layout Customization")

        # Layout management
        st.markdown("#### 📋 Available Layouts")

        for layout_key, layout_info in self.available_layouts.items():
            with st.expander(f"📐 {layout_info['name']}"):
                st.markdown(f"**Description:** {layout_info['description']}")
                st.markdown(f"**Widgets:** {', '.join(layout_info['widgets'])}")

                if st.button(f"Use {layout_info['name']}", key=f"use_{layout_key}"):
                    st.session_state.selected_layout = layout_key
                    st.success(f"Layout changed to {layout_info['name']}")

        # Widget configuration
        st.markdown("#### 🧩 Widget Configuration")

        all_widgets = [
            'system_overview', 'performance_charts', 'business_metrics',
            'cpu_memory_chart', 'network_chart', 'system_alerts',
            'business_overview', 'portfolio_chart', 'pnl_chart',
            'risk_metrics', 'kpi_summary', 'system_health'
        ]

        selected_widgets = st.multiselect(
            "Select Widgets for Custom Layout",
            all_widgets,
            default=['system_overview', 'performance_charts', 'business_metrics'],
            help="Choose which widgets to display in your custom layout"
        )

        if st.button("💾 Save Custom Layout"):
            # Save custom layout to session state
            if 'custom_layouts' not in st.session_state:
                st.session_state.custom_layouts = {}

            layout_name = st.text_input("Layout Name", value="My Custom Layout")
            if layout_name and selected_widgets:
                st.session_state.custom_layouts[layout_name] = {
                    'name': layout_name,
                    'description': 'User-defined custom layout',
                    'widgets': selected_widgets
                }
                st.success(f"Custom layout '{layout_name}' saved!")


def render_metrics_dashboard():
    """Main function to render the metrics dashboard."""
    dashboard = MetricsDashboard()

    # Metrics dashboard tabs
    tab1, tab2, tab3 = st.tabs([
        "📊 Metrics Overview",
        "📈 Performance Details",
        "⚙️ Layout Settings"
    ])

    with tab1:
        dashboard.render_metrics_overview()

    with tab2:
        st.markdown("## 📈 Detailed Performance Analysis")

        detail_col1, detail_col2 = st.columns(2)

        with detail_col1:
            dashboard._render_cpu_memory_chart()
            dashboard._render_system_alerts()

        with detail_col2:
            dashboard._render_portfolio_chart()
            dashboard._render_pnl_chart()

    with tab3:
        dashboard.render_layout_customizer()