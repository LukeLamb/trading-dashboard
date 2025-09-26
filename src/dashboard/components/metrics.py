"""
System Metrics Dashboard for Trading Dashboard.

This module provides comprehensive system performance monitoring, business metrics tracking,
and customizable dashboard layouts for financial and technical metrics visualization.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import psutil
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import threading
import time
import json
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils.logging import get_logger


class MetricType(Enum):
    """Types of metrics that can be tracked."""
    SYSTEM = "system"
    BUSINESS = "business"
    NETWORK = "network"
    AGENT = "agent"


class AlertLevel(Enum):
    """Alert levels for metric thresholds."""
    NORMAL = "normal"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


@dataclass
class SystemMetric:
    """System performance metric."""
    name: str
    value: float
    unit: str
    timestamp: datetime
    category: MetricType
    alert_level: AlertLevel = AlertLevel.NORMAL
    threshold_warning: Optional[float] = None
    threshold_critical: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'name': self.name,
            'value': self.value,
            'unit': self.unit,
            'timestamp': self.timestamp.isoformat(),
            'category': self.category.value,
            'alert_level': self.alert_level.value,
            'threshold_warning': self.threshold_warning,
            'threshold_critical': self.threshold_critical
        }


@dataclass
class BusinessMetric:
    """Business performance metric."""
    name: str
    value: float
    currency: str
    timestamp: datetime
    change_24h: Optional[float] = None
    change_percent_24h: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'name': self.name,
            'value': self.value,
            'currency': self.currency,
            'timestamp': self.timestamp.isoformat(),
            'change_24h': self.change_24h,
            'change_percent_24h': self.change_percent_24h
        }


@dataclass
class DashboardLayout:
    """Dashboard layout configuration."""
    layout_id: str
    name: str
    description: str
    widgets: List[Dict[str, Any]]
    grid_config: Dict[str, Any]
    created_at: datetime
    is_default: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'layout_id': self.layout_id,
            'name': self.name,
            'description': self.description,
            'widgets': self.widgets,
            'grid_config': self.grid_config,
            'created_at': self.created_at.isoformat(),
            'is_default': self.is_default
        }


class SystemMetricsManager:
    """Manages system performance metrics collection and visualization."""

    def __init__(self):
        """Initialize system metrics manager."""
        self.logger = get_logger(__name__)

        # Metrics storage
        self.system_metrics: Dict[str, List[SystemMetric]] = {}
        self.business_metrics: Dict[str, List[BusinessMetric]] = {}

        # Monitoring configuration
        self.monitoring_active = False
        self.collection_interval = 5  # seconds
        self.max_history_points = 1000

        # Thresholds
        self.system_thresholds = {
            'cpu_usage': {'warning': 70.0, 'critical': 85.0},
            'memory_usage': {'warning': 75.0, 'critical': 90.0},
            'disk_usage': {'warning': 80.0, 'critical': 95.0},
            'network_latency': {'warning': 100.0, 'critical': 500.0}  # ms
        }

        # Initialize with current system state
        self._initialize_system_metrics()
        self._initialize_business_metrics()

    def _initialize_system_metrics(self):
        """Initialize system metrics with current values."""
        current_time = datetime.now()

        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        cpu_freq = psutil.cpu_freq()

        self._add_system_metric("CPU Usage", cpu_percent, "%", current_time, MetricType.SYSTEM,
                               threshold_warning=70.0, threshold_critical=85.0)
        self._add_system_metric("CPU Cores", cpu_count, "cores", current_time, MetricType.SYSTEM)

        if cpu_freq:
            self._add_system_metric("CPU Frequency", cpu_freq.current, "MHz", current_time, MetricType.SYSTEM)

        # Memory metrics
        memory = psutil.virtual_memory()
        self._add_system_metric("Memory Usage", memory.percent, "%", current_time, MetricType.SYSTEM,
                               threshold_warning=75.0, threshold_critical=90.0)
        self._add_system_metric("Memory Total", memory.total / (1024**3), "GB", current_time, MetricType.SYSTEM)
        self._add_system_metric("Memory Available", memory.available / (1024**3), "GB", current_time, MetricType.SYSTEM)

        # Disk metrics
        disk = psutil.disk_usage('/')
        disk_percent = (disk.used / disk.total) * 100
        self._add_system_metric("Disk Usage", disk_percent, "%", current_time, MetricType.SYSTEM,
                               threshold_warning=80.0, threshold_critical=95.0)
        self._add_system_metric("Disk Total", disk.total / (1024**3), "GB", current_time, MetricType.SYSTEM)
        self._add_system_metric("Disk Free", disk.free / (1024**3), "GB", current_time, MetricType.SYSTEM)

        # Network metrics
        network = psutil.net_io_counters()
        self._add_system_metric("Network Bytes Sent", network.bytes_sent / (1024**2), "MB", current_time, MetricType.NETWORK)
        self._add_system_metric("Network Bytes Received", network.bytes_recv / (1024**2), "MB", current_time, MetricType.NETWORK)

        # Generate historical data for demonstration
        self._generate_historical_system_data()

    def _initialize_business_metrics(self):
        """Initialize business metrics with mock data."""
        current_time = datetime.now()

        # Portfolio metrics
        self._add_business_metric("Portfolio Value", 125750.50, "USD", current_time, 2450.75, 1.99)
        self._add_business_metric("Daily P&L", 1825.30, "USD", current_time, 845.20, 0.68)
        self._add_business_metric("Total Return", 25750.50, "USD", current_time, 1205.80, 4.91)

        # Risk metrics
        self._add_business_metric("Risk Exposure", 45250.00, "USD", current_time, -1200.50, -2.58)
        self._add_business_metric("Max Drawdown", -3250.75, "USD", current_time, -125.30, 4.01)
        self._add_business_metric("Sharpe Ratio", 1.85, "ratio", current_time, 0.12, 6.95)

        # Trading metrics
        self._add_business_metric("Active Positions", 12, "positions", current_time, 3, 33.33)
        self._add_business_metric("Win Rate", 68.5, "%", current_time, 2.3, 3.47)
        self._add_business_metric("Average Trade", 245.80, "USD", current_time, 15.60, 6.78)

        # Generate historical business data
        self._generate_historical_business_data()

    def _add_system_metric(self, name: str, value: float, unit: str, timestamp: datetime,
                          category: MetricType, threshold_warning: Optional[float] = None,
                          threshold_critical: Optional[float] = None):
        """Add a system metric."""
        # Determine alert level
        alert_level = AlertLevel.NORMAL
        if threshold_critical and value >= threshold_critical:
            alert_level = AlertLevel.CRITICAL
        elif threshold_warning and value >= threshold_warning:
            alert_level = AlertLevel.WARNING

        metric = SystemMetric(
            name=name,
            value=value,
            unit=unit,
            timestamp=timestamp,
            category=category,
            alert_level=alert_level,
            threshold_warning=threshold_warning,
            threshold_critical=threshold_critical
        )

        if name not in self.system_metrics:
            self.system_metrics[name] = []

        self.system_metrics[name].append(metric)

        # Maintain history limit
        if len(self.system_metrics[name]) > self.max_history_points:
            self.system_metrics[name] = self.system_metrics[name][-self.max_history_points:]

    def _add_business_metric(self, name: str, value: float, currency: str, timestamp: datetime,
                           change_24h: Optional[float] = None, change_percent_24h: Optional[float] = None):
        """Add a business metric."""
        metric = BusinessMetric(
            name=name,
            value=value,
            currency=currency,
            timestamp=timestamp,
            change_24h=change_24h,
            change_percent_24h=change_percent_24h
        )

        if name not in self.business_metrics:
            self.business_metrics[name] = []

        self.business_metrics[name].append(metric)

        # Maintain history limit
        if len(self.business_metrics[name]) > self.max_history_points:
            self.business_metrics[name] = self.business_metrics[name][-self.max_history_points:]

    def _generate_historical_system_data(self):
        """Generate historical system data for demonstration."""
        # Generate last 24 hours of data (every 5 minutes)
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=24)

        current_time = start_time
        while current_time < end_time:
            # CPU with realistic variation
            base_cpu = 25.0
            cpu_variation = np.random.normal(0, 5) + np.sin(current_time.hour / 24 * 2 * np.pi) * 10
            cpu_usage = max(5, min(95, base_cpu + cpu_variation))

            # Memory with gradual increase pattern
            base_memory = 45.0
            memory_trend = (current_time - start_time).total_seconds() / (24 * 3600) * 5  # Slight upward trend
            memory_variation = np.random.normal(0, 3)
            memory_usage = max(20, min(90, base_memory + memory_trend + memory_variation))

            # Disk usage (relatively stable)
            disk_usage = 62.5 + np.random.normal(0, 1)

            # Network activity (higher during business hours)
            hour = current_time.hour
            if 9 <= hour <= 17:  # Business hours
                network_multiplier = 1.5
            else:
                network_multiplier = 0.5

            network_sent = np.random.exponential(50) * network_multiplier
            network_recv = np.random.exponential(75) * network_multiplier

            # Add metrics
            self._add_system_metric("CPU Usage", cpu_usage, "%", current_time, MetricType.SYSTEM,
                                   threshold_warning=70.0, threshold_critical=85.0)
            self._add_system_metric("Memory Usage", memory_usage, "%", current_time, MetricType.SYSTEM,
                                   threshold_warning=75.0, threshold_critical=90.0)
            self._add_system_metric("Disk Usage", disk_usage, "%", current_time, MetricType.SYSTEM,
                                   threshold_warning=80.0, threshold_critical=95.0)
            self._add_system_metric("Network Bytes Sent", network_sent, "MB", current_time, MetricType.NETWORK)
            self._add_system_metric("Network Bytes Received", network_recv, "MB", current_time, MetricType.NETWORK)

            current_time += timedelta(minutes=5)

    def _generate_historical_business_data(self):
        """Generate historical business data for demonstration."""
        # Generate last 30 days of daily business metrics
        end_time = datetime.now()
        start_time = end_time - timedelta(days=30)

        base_portfolio = 100000.0
        current_time = start_time
        portfolio_value = base_portfolio

        while current_time < end_time:
            # Portfolio growth with market volatility
            daily_return = np.random.normal(0.0008, 0.02)  # ~0.08% daily return with 2% volatility
            portfolio_value *= (1 + daily_return)

            daily_pnl = portfolio_value - (portfolio_value / (1 + daily_return))

            # Risk metrics
            risk_exposure = portfolio_value * np.random.uniform(0.3, 0.5)  # 30-50% of portfolio
            max_drawdown = min(0, np.random.normal(-0.02, 0.01)) * portfolio_value
            sharpe_ratio = max(0.5, np.random.normal(1.8, 0.3))

            # Trading metrics
            active_positions = np.random.randint(8, 20)
            win_rate = np.random.normal(65, 8)  # ~65% win rate with variation
            avg_trade = daily_pnl / max(1, active_positions) if daily_pnl > 0 else np.random.normal(200, 50)

            # Calculate 24h changes (compared to yesterday if available)
            change_24h = None
            change_percent_24h = None
            if len(self.business_metrics.get("Portfolio Value", [])) > 0:
                yesterday_value = self.business_metrics["Portfolio Value"][-1].value
                change_24h = portfolio_value - yesterday_value
                change_percent_24h = (change_24h / yesterday_value) * 100 if yesterday_value > 0 else 0

            # Add business metrics
            self._add_business_metric("Portfolio Value", portfolio_value, "USD", current_time, change_24h, change_percent_24h)
            self._add_business_metric("Daily P&L", daily_pnl, "USD", current_time)
            self._add_business_metric("Risk Exposure", risk_exposure, "USD", current_time)
            self._add_business_metric("Max Drawdown", max_drawdown, "USD", current_time)
            self._add_business_metric("Sharpe Ratio", sharpe_ratio, "ratio", current_time)
            self._add_business_metric("Active Positions", active_positions, "positions", current_time)
            self._add_business_metric("Win Rate", win_rate, "%", current_time)
            self._add_business_metric("Average Trade", avg_trade, "USD", current_time)

            current_time += timedelta(days=1)

    def get_latest_system_metrics(self) -> Dict[str, SystemMetric]:
        """Get the latest system metrics."""
        latest_metrics = {}
        for name, metrics_list in self.system_metrics.items():
            if metrics_list:
                latest_metrics[name] = metrics_list[-1]
        return latest_metrics

    def get_latest_business_metrics(self) -> Dict[str, BusinessMetric]:
        """Get the latest business metrics."""
        latest_metrics = {}
        for name, metrics_list in self.business_metrics.items():
            if metrics_list:
                latest_metrics[name] = metrics_list[-1]
        return latest_metrics

    def create_cpu_memory_chart(self, hours: int = 24) -> go.Figure:
        """Create CPU and memory usage chart."""
        if "CPU Usage" not in self.system_metrics or "Memory Usage" not in self.system_metrics:
            return go.Figure()

        # Filter data to last N hours
        cutoff_time = datetime.now() - timedelta(hours=hours)

        cpu_data = [m for m in self.system_metrics["CPU Usage"] if m.timestamp >= cutoff_time]
        memory_data = [m for m in self.system_metrics["Memory Usage"] if m.timestamp >= cutoff_time]

        if not cpu_data or not memory_data:
            return go.Figure()

        # Create subplot
        fig = make_subplots(specs=[[{"secondary_y": False}]])

        # CPU usage
        fig.add_trace(go.Scatter(
            x=[m.timestamp for m in cpu_data],
            y=[m.value for m in cpu_data],
            mode='lines',
            name='CPU Usage (%)',
            line=dict(color='#3B82F6', width=2),
            hovertemplate="<b>CPU Usage</b><br>%{x}<br>%{y:.1f}%<extra></extra>"
        ))

        # Memory usage
        fig.add_trace(go.Scatter(
            x=[m.timestamp for m in memory_data],
            y=[m.value for m in memory_data],
            mode='lines',
            name='Memory Usage (%)',
            line=dict(color='#10B981', width=2),
            hovertemplate="<b>Memory Usage</b><br>%{x}<br>%{y:.1f}%<extra></extra>"
        ))

        # Add threshold lines
        fig.add_hline(y=70, line_dash="dash", line_color="orange", opacity=0.7, annotation_text="CPU Warning (70%)")
        fig.add_hline(y=85, line_dash="dash", line_color="red", opacity=0.7, annotation_text="CPU Critical (85%)")

        fig.update_layout(
            title=f"System Performance (Last {hours} Hours)",
            xaxis_title="Time",
            yaxis_title="Usage (%)",
            hovermode='x unified',
            height=400,
            showlegend=True,
            plot_bgcolor='white',
            paper_bgcolor='white'
        )

        return fig

    def create_network_chart(self, hours: int = 24) -> go.Figure:
        """Create network activity chart."""
        if "Network Bytes Sent" not in self.system_metrics or "Network Bytes Received" not in self.system_metrics:
            return go.Figure()

        cutoff_time = datetime.now() - timedelta(hours=hours)

        sent_data = [m for m in self.system_metrics["Network Bytes Sent"] if m.timestamp >= cutoff_time]
        recv_data = [m for m in self.system_metrics["Network Bytes Received"] if m.timestamp >= cutoff_time]

        if not sent_data or not recv_data:
            return go.Figure()

        fig = go.Figure()

        # Network sent
        fig.add_trace(go.Scatter(
            x=[m.timestamp for m in sent_data],
            y=[m.value for m in sent_data],
            mode='lines',
            name='Bytes Sent (MB)',
            line=dict(color='#F59E0B', width=2),
            fill='tonexty',
            hovertemplate="<b>Sent</b><br>%{x}<br>%{y:.1f} MB<extra></extra>"
        ))

        # Network received
        fig.add_trace(go.Scatter(
            x=[m.timestamp for m in recv_data],
            y=[m.value for m in recv_data],
            mode='lines',
            name='Bytes Received (MB)',
            line=dict(color='#8B5CF6', width=2),
            fill='tozeroy',
            hovertemplate="<b>Received</b><br>%{x}<br>%{y:.1f} MB<extra></extra>"
        ))

        fig.update_layout(
            title=f"Network Activity (Last {hours} Hours)",
            xaxis_title="Time",
            yaxis_title="Data (MB)",
            hovermode='x unified',
            height=350,
            showlegend=True,
            plot_bgcolor='white',
            paper_bgcolor='white'
        )

        return fig

    def create_portfolio_chart(self, days: int = 30) -> go.Figure:
        """Create portfolio performance chart."""
        if "Portfolio Value" not in self.business_metrics:
            return go.Figure()

        cutoff_time = datetime.now() - timedelta(days=days)
        portfolio_data = [m for m in self.business_metrics["Portfolio Value"] if m.timestamp >= cutoff_time]

        if not portfolio_data:
            return go.Figure()

        # Calculate returns
        values = [m.value for m in portfolio_data]
        initial_value = values[0] if values else 1
        returns = [(v / initial_value - 1) * 100 for v in values]

        fig = go.Figure()

        # Portfolio value line
        fig.add_trace(go.Scatter(
            x=[m.timestamp for m in portfolio_data],
            y=values,
            mode='lines',
            name='Portfolio Value',
            line=dict(color='#10B981', width=3),
            hovertemplate="<b>Portfolio Value</b><br>%{x}<br>$%{y:,.2f}<extra></extra>"
        ))

        # Add baseline
        fig.add_hline(y=initial_value, line_dash="dash", line_color="gray", opacity=0.5,
                     annotation_text=f"Start: ${initial_value:,.2f}")

        fig.update_layout(
            title=f"Portfolio Performance (Last {days} Days)",
            xaxis_title="Date",
            yaxis_title="Portfolio Value ($)",
            hovermode='x unified',
            height=400,
            showlegend=True,
            plot_bgcolor='white',
            paper_bgcolor='white'
        )

        return fig

    def create_pnl_chart(self, days: int = 30) -> go.Figure:
        """Create P&L chart."""
        if "Daily P&L" not in self.business_metrics:
            return go.Figure()

        cutoff_time = datetime.now() - timedelta(days=days)
        pnl_data = [m for m in self.business_metrics["Daily P&L"] if m.timestamp >= cutoff_time]

        if not pnl_data:
            return go.Figure()

        # Separate positive and negative P&L for coloring
        timestamps = [m.timestamp for m in pnl_data]
        values = [m.value for m in pnl_data]
        colors = ['#10B981' if v >= 0 else '#EF4444' for v in values]

        fig = go.Figure()

        # P&L bars
        fig.add_trace(go.Bar(
            x=timestamps,
            y=values,
            name='Daily P&L',
            marker=dict(color=colors),
            hovertemplate="<b>Daily P&L</b><br>%{x}<br>$%{y:,.2f}<extra></extra>"
        ))

        # Add zero line
        fig.add_hline(y=0, line_color="black", line_width=1, opacity=0.5)

        fig.update_layout(
            title=f"Daily P&L (Last {days} Days)",
            xaxis_title="Date",
            yaxis_title="P&L ($)",
            height=350,
            showlegend=False,
            plot_bgcolor='white',
            paper_bgcolor='white'
        )

        return fig

    def get_system_health_score(self) -> Tuple[float, str]:
        """Calculate overall system health score."""
        latest_metrics = self.get_latest_system_metrics()

        if not latest_metrics:
            return 0.0, "No data available"

        health_components = []
        issues = []

        # CPU health (inverse of usage)
        if "CPU Usage" in latest_metrics:
            cpu_usage = latest_metrics["CPU Usage"].value
            cpu_health = max(0, 100 - cpu_usage)
            health_components.append(cpu_health * 0.3)  # 30% weight
            if cpu_usage > 85:
                issues.append(f"High CPU usage ({cpu_usage:.1f}%)")

        # Memory health (inverse of usage)
        if "Memory Usage" in latest_metrics:
            memory_usage = latest_metrics["Memory Usage"].value
            memory_health = max(0, 100 - memory_usage)
            health_components.append(memory_health * 0.3)  # 30% weight
            if memory_usage > 90:
                issues.append(f"High memory usage ({memory_usage:.1f}%)")

        # Disk health (inverse of usage)
        if "Disk Usage" in latest_metrics:
            disk_usage = latest_metrics["Disk Usage"].value
            disk_health = max(0, 100 - disk_usage)
            health_components.append(disk_health * 0.2)  # 20% weight
            if disk_usage > 95:
                issues.append(f"High disk usage ({disk_usage:.1f}%)")

        # Network health (simplified - assume good if within reasonable bounds)
        network_health = 85  # Default good network health
        health_components.append(network_health * 0.2)  # 20% weight

        overall_health = sum(health_components) if health_components else 0

        # Determine status message
        if overall_health >= 90:
            status = "Excellent - All systems running optimally"
        elif overall_health >= 75:
            status = "Good - System performance is acceptable"
        elif overall_health >= 60:
            status = "Fair - Some performance issues detected"
        elif overall_health >= 40:
            status = "Poor - Multiple performance issues"
        else:
            status = "Critical - Immediate attention required"

        if issues:
            status += f" | Issues: {', '.join(issues)}"

        return overall_health, status