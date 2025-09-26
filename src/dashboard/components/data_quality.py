"""
Data Quality Integration for Trading Dashboard.

This module provides comprehensive data quality monitoring, visualization,
and alerting capabilities integrated with the Market Data Agent.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging
import asyncio
import json
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils.logging import get_logger


class QualityGrade(Enum):
    """Data quality grade enumeration (A-F scale)."""
    A_PLUS = "A+"
    A = "A"
    A_MINUS = "A-"
    B_PLUS = "B+"
    B = "B"
    B_MINUS = "B-"
    C_PLUS = "C+"
    C = "C"
    C_MINUS = "C-"
    D = "D"
    F = "F"
    UNKNOWN = "N/A"

    @property
    def score(self) -> float:
        """Convert grade to numerical score (0-100)."""
        grade_map = {
            "A+": 100, "A": 95, "A-": 90,
            "B+": 87, "B": 83, "B-": 80,
            "C+": 77, "C": 73, "C-": 70,
            "D": 65, "F": 0, "N/A": 0
        }
        return grade_map.get(self.value, 0)

    @property
    def color(self) -> str:
        """Get color for grade visualization."""
        if self.score >= 90:
            return "#10B981"  # Green
        elif self.score >= 80:
            return "#F59E0B"  # Yellow
        elif self.score >= 70:
            return "#F97316"  # Orange
        elif self.score >= 60:
            return "#EF4444"  # Red
        else:
            return "#6B7280"  # Gray


class AlertSeverity(Enum):
    """Quality alert severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class DataSourceQuality:
    """Quality information for a single data source."""
    source_id: str
    source_name: str
    grade: QualityGrade
    score: float
    last_updated: datetime
    response_time: float
    error_count: int
    success_rate: float
    data_completeness: float
    data_accuracy: float
    reliability_score: float
    uptime_percentage: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'source_id': self.source_id,
            'source_name': self.source_name,
            'grade': self.grade.value,
            'score': self.score,
            'last_updated': self.last_updated.isoformat(),
            'response_time': self.response_time,
            'error_count': self.error_count,
            'success_rate': self.success_rate,
            'data_completeness': self.data_completeness,
            'data_accuracy': self.data_accuracy,
            'reliability_score': self.reliability_score,
            'uptime_percentage': self.uptime_percentage
        }


@dataclass
class QualityAlert:
    """Data quality alert."""
    alert_id: str
    source_id: str
    severity: AlertSeverity
    title: str
    message: str
    timestamp: datetime
    resolved: bool = False
    resolution_time: Optional[datetime] = None
    resolution_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'alert_id': self.alert_id,
            'source_id': self.source_id,
            'severity': self.severity.value,
            'title': self.title,
            'message': self.message,
            'timestamp': self.timestamp.isoformat(),
            'resolved': self.resolved,
            'resolution_time': self.resolution_time.isoformat() if self.resolution_time else None,
            'resolution_message': self.resolution_message
        }


@dataclass
class QualityTrend:
    """Quality trend data over time."""
    source_id: str
    timestamps: List[datetime]
    scores: List[float]
    grades: List[QualityGrade]
    response_times: List[float]
    error_rates: List[float]


class DataQualityManager:
    """Manages data quality monitoring and visualization."""

    def __init__(self):
        """Initialize data quality manager."""
        self.logger = get_logger(__name__)

        # Quality data storage
        self.source_qualities: Dict[str, DataSourceQuality] = {}
        self.quality_history: Dict[str, QualityTrend] = {}
        self.active_alerts: Dict[str, QualityAlert] = {}
        self.resolved_alerts: List[QualityAlert] = []

        # Quality thresholds
        self.thresholds = {
            'critical_score': 60.0,
            'warning_score': 80.0,
            'response_time_threshold': 1000.0,  # milliseconds
            'error_rate_threshold': 0.05,  # 5%
            'completeness_threshold': 0.95  # 95%
        }

        # Mock data sources for demonstration
        self._initialize_mock_sources()

    def _initialize_mock_sources(self):
        """Initialize mock data sources for demonstration."""
        mock_sources = [
            {
                'id': 'bloomberg',
                'name': 'Bloomberg Terminal',
                'grade': QualityGrade.A,
                'response_time': 45.2,
                'error_count': 2,
                'success_rate': 99.8,
                'completeness': 99.9,
                'accuracy': 99.7,
                'reliability': 99.5,
                'uptime': 99.9
            },
            {
                'id': 'yahoo_finance',
                'name': 'Yahoo Finance',
                'grade': QualityGrade.B_PLUS,
                'response_time': 120.5,
                'error_count': 15,
                'success_rate': 96.2,
                'completeness': 94.5,
                'accuracy': 97.8,
                'reliability': 95.1,
                'uptime': 98.5
            },
            {
                'id': 'alpha_vantage',
                'name': 'Alpha Vantage',
                'grade': QualityGrade.B,
                'response_time': 200.1,
                'error_count': 8,
                'success_rate': 94.8,
                'completeness': 92.3,
                'accuracy': 96.5,
                'reliability': 93.8,
                'uptime': 97.2
            },
            {
                'id': 'iex_cloud',
                'name': 'IEX Cloud',
                'grade': QualityGrade.A_MINUS,
                'response_time': 85.7,
                'error_count': 5,
                'success_rate': 98.5,
                'completeness': 96.8,
                'accuracy': 98.9,
                'reliability': 97.4,
                'uptime': 99.1
            },
            {
                'id': 'finnhub',
                'name': 'Finnhub',
                'grade': QualityGrade.C_PLUS,
                'response_time': 450.3,
                'error_count': 25,
                'success_rate': 89.2,
                'completeness': 88.5,
                'accuracy': 91.2,
                'reliability': 87.6,
                'uptime': 94.8
            }
        ]

        # Create DataSourceQuality objects
        for source_data in mock_sources:
            quality = DataSourceQuality(
                source_id=source_data['id'],
                source_name=source_data['name'],
                grade=source_data['grade'],
                score=source_data['grade'].score,
                last_updated=datetime.now(),
                response_time=source_data['response_time'],
                error_count=source_data['error_count'],
                success_rate=source_data['success_rate'],
                data_completeness=source_data['completeness'],
                data_accuracy=source_data['accuracy'],
                reliability_score=source_data['reliability'],
                uptime_percentage=source_data['uptime']
            )

            self.source_qualities[source_data['id']] = quality

            # Generate historical data
            self._generate_quality_history(source_data['id'], quality)

        # Generate some sample alerts
        self._generate_sample_alerts()

    def _generate_quality_history(self, source_id: str, quality: DataSourceQuality):
        """Generate historical quality data for demonstration."""
        # Generate 30 days of historical data
        timestamps = []
        scores = []
        grades = []
        response_times = []
        error_rates = []

        base_time = datetime.now() - timedelta(days=30)
        base_score = quality.score
        base_response_time = quality.response_time

        for i in range(30 * 24):  # Hourly data for 30 days
            timestamp = base_time + timedelta(hours=i)

            # Add some realistic variation
            score_variation = np.random.normal(0, 2.5)  # ±2.5 point variation
            score = max(0, min(100, base_score + score_variation))

            response_variation = np.random.normal(0, base_response_time * 0.1)
            response_time = max(10, base_response_time + response_variation)

            error_rate = max(0, min(1, (100 - score) / 100 * 0.1))

            # Convert score to grade
            if score >= 95:
                grade = QualityGrade.A
            elif score >= 90:
                grade = QualityGrade.A_MINUS
            elif score >= 87:
                grade = QualityGrade.B_PLUS
            elif score >= 83:
                grade = QualityGrade.B
            elif score >= 80:
                grade = QualityGrade.B_MINUS
            elif score >= 77:
                grade = QualityGrade.C_PLUS
            elif score >= 73:
                grade = QualityGrade.C
            elif score >= 70:
                grade = QualityGrade.C_MINUS
            elif score >= 65:
                grade = QualityGrade.D
            else:
                grade = QualityGrade.F

            timestamps.append(timestamp)
            scores.append(score)
            grades.append(grade)
            response_times.append(response_time)
            error_rates.append(error_rate)

        self.quality_history[source_id] = QualityTrend(
            source_id=source_id,
            timestamps=timestamps,
            scores=scores,
            grades=grades,
            response_times=response_times,
            error_rates=error_rates
        )

    def _generate_sample_alerts(self):
        """Generate sample quality alerts."""
        alerts = [
            {
                'id': 'alert_001',
                'source_id': 'finnhub',
                'severity': AlertSeverity.HIGH,
                'title': 'High Response Time Detected',
                'message': 'Response time exceeded 400ms threshold (450ms)',
                'timestamp': datetime.now() - timedelta(hours=2)
            },
            {
                'id': 'alert_002',
                'source_id': 'yahoo_finance',
                'severity': AlertSeverity.MEDIUM,
                'title': 'Data Completeness Below Threshold',
                'message': 'Data completeness dropped to 94.5% (below 95% threshold)',
                'timestamp': datetime.now() - timedelta(hours=6)
            },
            {
                'id': 'alert_003',
                'source_id': 'alpha_vantage',
                'severity': AlertSeverity.LOW,
                'title': 'Temporary Grade Drop',
                'message': 'Quality grade dropped from B+ to B',
                'timestamp': datetime.now() - timedelta(hours=12),
                'resolved': True,
                'resolution_time': datetime.now() - timedelta(hours=8),
                'resolution_message': 'Quality restored to normal levels'
            }
        ]

        for alert_data in alerts:
            alert = QualityAlert(
                alert_id=alert_data['id'],
                source_id=alert_data['source_id'],
                severity=alert_data['severity'],
                title=alert_data['title'],
                message=alert_data['message'],
                timestamp=alert_data['timestamp'],
                resolved=alert_data.get('resolved', False),
                resolution_time=alert_data.get('resolution_time'),
                resolution_message=alert_data.get('resolution_message')
            )

            if alert.resolved:
                self.resolved_alerts.append(alert)
            else:
                self.active_alerts[alert.alert_id] = alert

    def get_overall_quality_score(self) -> float:
        """Calculate overall system quality score."""
        if not self.source_qualities:
            return 0.0

        # Weighted average based on source reliability
        total_weight = 0
        weighted_sum = 0

        for quality in self.source_qualities.values():
            weight = quality.reliability_score / 100
            weighted_sum += quality.score * weight
            total_weight += weight

        return weighted_sum / total_weight if total_weight > 0 else 0.0

    def get_quality_distribution(self) -> Dict[str, int]:
        """Get distribution of quality grades."""
        distribution = {}
        for grade in QualityGrade:
            if grade != QualityGrade.UNKNOWN:
                distribution[grade.value] = 0

        for quality in self.source_qualities.values():
            distribution[quality.grade.value] += 1

        return distribution

    def create_quality_overview_chart(self) -> go.Figure:
        """Create quality overview chart showing all sources."""
        if not self.source_qualities:
            return go.Figure()

        # Prepare data
        sources = []
        scores = []
        grades = []
        colors = []

        for quality in self.source_qualities.values():
            sources.append(quality.source_name)
            scores.append(quality.score)
            grades.append(quality.grade.value)
            colors.append(quality.grade.color)

        # Create horizontal bar chart
        fig = go.Figure(data=[
            go.Bar(
                y=sources,
                x=scores,
                orientation='h',
                marker=dict(color=colors),
                text=[f"{grade} ({score:.1f})" for grade, score in zip(grades, scores)],
                textposition='inside',
                textfont=dict(color='white', size=12),
                hovertemplate="<b>%{y}</b><br>Score: %{x:.1f}<br>Grade: %{text}<extra></extra>"
            )
        ])

        fig.update_layout(
            title=dict(
                text="Data Source Quality Overview",
                x=0.5,
                font=dict(size=16)
            ),
            xaxis=dict(
                title="Quality Score",
                range=[0, 100],
                showgrid=True,
                gridcolor='rgba(128, 128, 128, 0.2)'
            ),
            yaxis=dict(
                title="Data Sources",
                showgrid=False
            ),
            plot_bgcolor='white',
            paper_bgcolor='white',
            height=400,
            margin=dict(l=150, r=50, t=60, b=50)
        )

        return fig

    def create_quality_trend_chart(self, source_id: str, days: int = 7) -> go.Figure:
        """Create quality trend chart for a specific source."""
        if source_id not in self.quality_history:
            return go.Figure()

        trend = self.quality_history[source_id]

        # Filter to last N days
        cutoff_time = datetime.now() - timedelta(days=days)
        filtered_data = [(t, s, g) for t, s, g in zip(trend.timestamps, trend.scores, trend.grades)
                        if t >= cutoff_time]

        if not filtered_data:
            return go.Figure()

        timestamps, scores, grades = zip(*filtered_data)

        # Create line chart
        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=timestamps,
            y=scores,
            mode='lines+markers',
            name='Quality Score',
            line=dict(color='#3B82F6', width=2),
            marker=dict(size=4),
            hovertemplate="<b>%{x}</b><br>Score: %{y:.1f}<extra></extra>"
        ))

        # Add grade zones
        grade_zones = [
            (95, 100, 'A Grade', '#10B981', 0.1),
            (90, 95, 'A- Grade', '#34D399', 0.1),
            (80, 90, 'B Grade', '#F59E0B', 0.1),
            (70, 80, 'C Grade', '#F97316', 0.1),
            (0, 70, 'D/F Grade', '#EF4444', 0.1)
        ]

        for y0, y1, name, color, opacity in grade_zones:
            fig.add_shape(
                type="rect",
                x0=timestamps[0], x1=timestamps[-1],
                y0=y0, y1=y1,
                fillcolor=color,
                opacity=opacity,
                layer="below",
                line_width=0
            )

        source_name = self.source_qualities.get(source_id, {}).source_name if source_id in self.source_qualities else source_id

        fig.update_layout(
            title=dict(
                text=f"Quality Trend - {source_name} (Last {days} Days)",
                x=0.5,
                font=dict(size=16)
            ),
            xaxis=dict(
                title="Time",
                showgrid=True,
                gridcolor='rgba(128, 128, 128, 0.2)'
            ),
            yaxis=dict(
                title="Quality Score",
                range=[0, 100],
                showgrid=True,
                gridcolor='rgba(128, 128, 128, 0.2)'
            ),
            plot_bgcolor='white',
            paper_bgcolor='white',
            height=400,
            margin=dict(l=50, r=50, t=60, b=50),
            showlegend=False
        )

        return fig

    def create_quality_comparison_matrix(self) -> go.Figure:
        """Create quality comparison matrix heatmap."""
        if not self.source_qualities:
            return go.Figure()

        sources = list(self.source_qualities.keys())
        source_names = [self.source_qualities[sid].source_name for sid in sources]

        # Create comparison matrix
        metrics = ['Score', 'Response Time', 'Completeness', 'Accuracy', 'Reliability']
        matrix = []

        for metric in metrics:
            row = []
            for source_id in sources:
                quality = self.source_qualities[source_id]

                if metric == 'Score':
                    value = quality.score
                elif metric == 'Response Time':
                    value = 100 - min(100, quality.response_time / 10)  # Normalize response time
                elif metric == 'Completeness':
                    value = quality.data_completeness
                elif metric == 'Accuracy':
                    value = quality.data_accuracy
                elif metric == 'Reliability':
                    value = quality.reliability_score
                else:
                    value = 0

                row.append(value)
            matrix.append(row)

        # Create heatmap
        fig = go.Figure(data=go.Heatmap(
            z=matrix,
            x=source_names,
            y=metrics,
            colorscale='RdYlGn',
            colorbar=dict(title="Score"),
            hovertemplate="<b>%{y}</b><br>%{x}<br>Score: %{z:.1f}<extra></extra>",
            showscale=True
        ))

        fig.update_layout(
            title=dict(
                text="Data Quality Comparison Matrix",
                x=0.5,
                font=dict(size=16)
            ),
            xaxis=dict(title="Data Sources", side='bottom'),
            yaxis=dict(title="Quality Metrics"),
            plot_bgcolor='white',
            paper_bgcolor='white',
            height=400,
            margin=dict(l=100, r=100, t=60, b=100)
        )

        return fig

    def create_alert_timeline(self, days: int = 7) -> go.Figure:
        """Create alert timeline chart."""
        # Combine active and resolved alerts
        all_alerts = list(self.active_alerts.values()) + self.resolved_alerts

        # Filter to last N days
        cutoff_time = datetime.now() - timedelta(days=days)
        recent_alerts = [alert for alert in all_alerts if alert.timestamp >= cutoff_time]

        if not recent_alerts:
            # Create empty chart
            fig = go.Figure()
            fig.update_layout(
                title="No alerts in the selected time period",
                xaxis=dict(title="Time"),
                yaxis=dict(title="Alerts"),
                height=300
            )
            return fig

        # Prepare data
        timestamps = []
        severities = []
        titles = []
        resolved_status = []
        colors = []

        severity_colors = {
            AlertSeverity.CRITICAL: '#DC2626',
            AlertSeverity.HIGH: '#EA580C',
            AlertSeverity.MEDIUM: '#D97706',
            AlertSeverity.LOW: '#65A30D',
            AlertSeverity.INFO: '#2563EB'
        }

        for alert in recent_alerts:
            timestamps.append(alert.timestamp)
            severities.append(alert.severity.value.title())
            titles.append(alert.title)
            resolved_status.append("Resolved" if alert.resolved else "Active")
            colors.append(severity_colors[alert.severity])

        # Create scatter plot
        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=timestamps,
            y=severities,
            mode='markers',
            marker=dict(
                color=colors,
                size=12,
                opacity=0.7,
                line=dict(width=2, color='white')
            ),
            text=titles,
            hovertemplate="<b>%{text}</b><br>Severity: %{y}<br>Time: %{x}<extra></extra>",
            name="Alerts"
        ))

        fig.update_layout(
            title=dict(
                text=f"Quality Alerts Timeline (Last {days} Days)",
                x=0.5,
                font=dict(size=16)
            ),
            xaxis=dict(
                title="Time",
                showgrid=True,
                gridcolor='rgba(128, 128, 128, 0.2)'
            ),
            yaxis=dict(
                title="Severity Level",
                showgrid=True,
                gridcolor='rgba(128, 128, 128, 0.2)'
            ),
            plot_bgcolor='white',
            paper_bgcolor='white',
            height=350,
            margin=dict(l=80, r=50, t=60, b=50),
            showlegend=False
        )

        return fig

    def get_quality_recommendations(self) -> List[Dict[str, Any]]:
        """Get quality improvement recommendations."""
        recommendations = []

        for source_id, quality in self.source_qualities.items():
            if quality.score < self.thresholds['warning_score']:
                # Low quality source
                recommendations.append({
                    'type': 'quality',
                    'severity': 'high' if quality.score < self.thresholds['critical_score'] else 'medium',
                    'title': f"Improve {quality.source_name} Quality",
                    'message': f"Quality score ({quality.score:.1f}) is below threshold. Consider investigating data source issues.",
                    'source': quality.source_name,
                    'action': 'investigate_source'
                })

            if quality.response_time > self.thresholds['response_time_threshold']:
                # High response time
                recommendations.append({
                    'type': 'performance',
                    'severity': 'medium',
                    'title': f"Optimize {quality.source_name} Response Time",
                    'message': f"Response time ({quality.response_time:.0f}ms) exceeds threshold. Consider caching or alternative endpoints.",
                    'source': quality.source_name,
                    'action': 'optimize_performance'
                })

            if quality.data_completeness < self.thresholds['completeness_threshold']:
                # Data completeness issue
                recommendations.append({
                    'type': 'completeness',
                    'severity': 'high',
                    'title': f"Address {quality.source_name} Data Gaps",
                    'message': f"Data completeness ({quality.data_completeness:.1f}%) is below threshold. Consider secondary data sources.",
                    'source': quality.source_name,
                    'action': 'add_backup_source'
                })

        return recommendations

    def check_quality_thresholds(self) -> List[QualityAlert]:
        """Check quality thresholds and generate alerts if needed."""
        new_alerts = []

        for source_id, quality in self.source_qualities.items():
            # Check if we should create new alerts
            if quality.score < self.thresholds['critical_score']:
                alert_id = f"critical_quality_{source_id}_{int(datetime.now().timestamp())}"
                if alert_id not in self.active_alerts:
                    new_alert = QualityAlert(
                        alert_id=alert_id,
                        source_id=source_id,
                        severity=AlertSeverity.CRITICAL,
                        title=f"Critical Quality Drop - {quality.source_name}",
                        message=f"Quality score dropped to {quality.score:.1f} (below {self.thresholds['critical_score']:.1f} threshold)",
                        timestamp=datetime.now()
                    )
                    new_alerts.append(new_alert)
                    self.active_alerts[alert_id] = new_alert

        return new_alerts

    def resolve_alert(self, alert_id: str, resolution_message: str = ""):
        """Resolve an active alert."""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.resolved = True
            alert.resolution_time = datetime.now()
            alert.resolution_message = resolution_message

            # Move to resolved alerts
            self.resolved_alerts.append(alert)
            del self.active_alerts[alert_id]

    def get_source_quality(self, source_id: str) -> Optional[DataSourceQuality]:
        """Get quality information for a specific source."""
        return self.source_qualities.get(source_id)

    def update_source_quality(self, source_id: str, quality_data: Dict[str, Any]):
        """Update quality information for a source."""
        if source_id in self.source_qualities:
            quality = self.source_qualities[source_id]

            # Update fields if provided
            if 'score' in quality_data:
                quality.score = quality_data['score']
                quality.grade = self._score_to_grade(quality_data['score'])

            if 'response_time' in quality_data:
                quality.response_time = quality_data['response_time']

            if 'error_count' in quality_data:
                quality.error_count = quality_data['error_count']

            quality.last_updated = datetime.now()

            # Check for new alerts
            self.check_quality_thresholds()

    def _score_to_grade(self, score: float) -> QualityGrade:
        """Convert numerical score to quality grade."""
        if score >= 97:
            return QualityGrade.A_PLUS
        elif score >= 93:
            return QualityGrade.A
        elif score >= 90:
            return QualityGrade.A_MINUS
        elif score >= 87:
            return QualityGrade.B_PLUS
        elif score >= 83:
            return QualityGrade.B
        elif score >= 80:
            return QualityGrade.B_MINUS
        elif score >= 77:
            return QualityGrade.C_PLUS
        elif score >= 73:
            return QualityGrade.C
        elif score >= 70:
            return QualityGrade.C_MINUS
        elif score >= 65:
            return QualityGrade.D
        else:
            return QualityGrade.F