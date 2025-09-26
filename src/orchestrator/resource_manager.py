"""
Resource Manager for Trading Dashboard

This module provides advanced resource monitoring, limits enforcement,
performance optimization, and resource allocation for agent processes.
"""

import asyncio
import time
import psutil
import os
from typing import Dict, List, Optional, Tuple, NamedTuple
from dataclasses import dataclass, field
from enum import Enum
import logging
from collections import defaultdict, deque

from .agent_manager import AgentManager, AgentStatus
from ..utils.logging import get_logger


class AlertLevel(Enum):
    """Resource alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class ResourceType(Enum):
    """Resource type enumeration."""
    CPU = "cpu"
    MEMORY = "memory"
    DISK_IO = "disk_io"
    NETWORK_IO = "network_io"
    PROCESS_COUNT = "process_count"


@dataclass
class ResourceThreshold:
    """Resource usage threshold configuration."""
    resource_type: ResourceType
    warning_level: float  # Percentage threshold for warning
    critical_level: float  # Percentage threshold for critical
    emergency_level: float  # Percentage threshold for emergency
    check_interval: int = 30  # Seconds between checks
    action_on_critical: str = "throttle"  # Action: throttle, restart, alert_only


@dataclass
class ResourceAlert:
    """Resource usage alert."""
    timestamp: float
    agent_name: str
    resource_type: ResourceType
    alert_level: AlertLevel
    current_value: float
    threshold_value: float
    message: str
    resolved: bool = False


@dataclass
class ProcessMetrics:
    """Extended process metrics for an agent."""
    cpu_percent: float = 0.0
    memory_mb: float = 0.0
    memory_percent: float = 0.0
    disk_read_mb: float = 0.0
    disk_write_mb: float = 0.0
    network_sent_mb: float = 0.0
    network_recv_mb: float = 0.0
    open_files: int = 0
    thread_count: int = 0
    priority: int = 0
    timestamp: float = field(default_factory=time.time)


class ResourceTrendAnalyzer:
    """Analyzes resource usage trends over time."""

    def __init__(self, history_size: int = 100):
        self.history_size = history_size
        self.metrics_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=history_size))

    def add_metrics(self, agent_name: str, metrics: ProcessMetrics):
        """Add metrics to trend analysis."""
        self.metrics_history[agent_name].append(metrics)

    def get_trend(self, agent_name: str, metric: str, window_minutes: int = 10) -> Optional[float]:
        """
        Calculate trend for a specific metric.

        Returns:
            Positive value for increasing trend, negative for decreasing, None if insufficient data
        """
        if agent_name not in self.metrics_history:
            return None

        history = list(self.metrics_history[agent_name])
        if len(history) < 2:
            return None

        # Filter to time window
        cutoff_time = time.time() - (window_minutes * 60)
        recent_metrics = [m for m in history if m.timestamp >= cutoff_time]

        if len(recent_metrics) < 2:
            return None

        # Calculate simple linear trend
        values = [getattr(m, metric, 0) for m in recent_metrics]
        if not values:
            return None

        # Simple trend calculation: (last - first) / time_span
        time_span = recent_metrics[-1].timestamp - recent_metrics[0].timestamp
        if time_span <= 0:
            return None

        value_change = values[-1] - values[0]
        return value_change / time_span  # Units per second

    def predict_resource_exhaustion(self, agent_name: str, metric: str, limit: float) -> Optional[float]:
        """
        Predict when a resource might be exhausted based on current trend.

        Returns:
            Seconds until exhaustion, or None if trend is not increasing
        """
        trend = self.get_trend(agent_name, metric, window_minutes=5)
        if not trend or trend <= 0:
            return None

        if agent_name not in self.metrics_history or not self.metrics_history[agent_name]:
            return None

        current_value = getattr(list(self.metrics_history[agent_name])[-1], metric, 0)
        remaining = limit - current_value

        if remaining <= 0:
            return 0  # Already exhausted

        return remaining / trend


class ResourceManager:
    """
    Manages agent resource monitoring, limits, and optimization.

    This class provides:
    - Advanced resource monitoring with alerts
    - Resource limit enforcement
    - Performance optimization recommendations
    - Resource allocation management
    """

    def __init__(self, agent_manager: AgentManager):
        """Initialize the Resource Manager."""
        self.logger = get_logger(self.__class__.__name__)
        self.agent_manager = agent_manager
        self.trend_analyzer = ResourceTrendAnalyzer()

        # Resource thresholds
        self.resource_thresholds: Dict[ResourceType, ResourceThreshold] = {}
        self.active_alerts: List[ResourceAlert] = []
        self.alert_history: deque = deque(maxlen=1000)

        # Monitoring state
        self._monitoring_active = False
        self._monitoring_task: Optional[asyncio.Task] = None

        # Performance data
        self.baseline_metrics: Dict[str, ProcessMetrics] = {}

        self._setup_default_thresholds()

    def _setup_default_thresholds(self):
        """Setup default resource thresholds."""
        try:
            # CPU thresholds
            self.resource_thresholds[ResourceType.CPU] = ResourceThreshold(
                resource_type=ResourceType.CPU,
                warning_level=70.0,
                critical_level=85.0,
                emergency_level=95.0,
                check_interval=10,
                action_on_critical="throttle"
            )

            # Memory thresholds
            self.resource_thresholds[ResourceType.MEMORY] = ResourceThreshold(
                resource_type=ResourceType.MEMORY,
                warning_level=75.0,
                critical_level=90.0,
                emergency_level=98.0,
                check_interval=10,
                action_on_critical="restart"
            )

            # Disk I/O thresholds (MB/s)
            self.resource_thresholds[ResourceType.DISK_IO] = ResourceThreshold(
                resource_type=ResourceType.DISK_IO,
                warning_level=50.0,
                critical_level=100.0,
                emergency_level=200.0,
                check_interval=30,
                action_on_critical="alert_only"
            )

            # Network I/O thresholds (MB/s)
            self.resource_thresholds[ResourceType.NETWORK_IO] = ResourceThreshold(
                resource_type=ResourceType.NETWORK_IO,
                warning_level=10.0,
                critical_level=50.0,
                emergency_level=100.0,
                check_interval=30,
                action_on_critical="alert_only"
            )

            self.logger.info(f"Configured {len(self.resource_thresholds)} resource thresholds")

        except Exception as e:
            self.logger.error(f"Failed to setup resource thresholds: {e}")

    async def collect_extended_metrics(self, agent_name: str) -> Optional[ProcessMetrics]:
        """
        Collect extended process metrics for an agent.

        Args:
            agent_name: Name of the agent

        Returns:
            ProcessMetrics object or None if collection failed
        """
        try:
            agent = self.agent_manager.agents.get(agent_name)
            if not agent or not agent.pid or agent.status != AgentStatus.RUNNING:
                return None

            process = psutil.Process(agent.pid)

            # Basic metrics
            cpu_percent = process.cpu_percent(interval=0.1)
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / (1024 * 1024)
            memory_percent = process.memory_percent()

            # I/O metrics
            try:
                io_counters = process.io_counters()
                disk_read_mb = io_counters.read_bytes / (1024 * 1024)
                disk_write_mb = io_counters.write_bytes / (1024 * 1024)
            except (psutil.AccessDenied, AttributeError):
                disk_read_mb = disk_write_mb = 0.0

            # Network metrics (system-wide approximation)
            try:
                net_io = psutil.net_io_counters()
                network_sent_mb = net_io.bytes_sent / (1024 * 1024)
                network_recv_mb = net_io.bytes_recv / (1024 * 1024)
            except AttributeError:
                network_sent_mb = network_recv_mb = 0.0

            # Process details
            try:
                open_files = len(process.open_files())
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                open_files = 0

            try:
                thread_count = process.num_threads()
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                thread_count = 0

            try:
                if hasattr(process, 'nice'):
                    priority = process.nice()
                else:
                    priority = 0
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                priority = 0

            metrics = ProcessMetrics(
                cpu_percent=cpu_percent,
                memory_mb=memory_mb,
                memory_percent=memory_percent,
                disk_read_mb=disk_read_mb,
                disk_write_mb=disk_write_mb,
                network_sent_mb=network_sent_mb,
                network_recv_mb=network_recv_mb,
                open_files=open_files,
                thread_count=thread_count,
                priority=priority
            )

            # Add to trend analysis
            self.trend_analyzer.add_metrics(agent_name, metrics)

            return metrics

        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
            self.logger.warning(f"Failed to collect metrics for {agent_name}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error collecting metrics for {agent_name}: {e}")
            return None

    async def check_resource_thresholds(self, agent_name: str, metrics: ProcessMetrics):
        """Check resource usage against thresholds and generate alerts."""
        try:
            checks = [
                (ResourceType.CPU, metrics.cpu_percent),
                (ResourceType.MEMORY, metrics.memory_percent),
                # Note: I/O metrics would need rate calculation for proper threshold checking
            ]

            for resource_type, current_value in checks:
                if resource_type not in self.resource_thresholds:
                    continue

                threshold = self.resource_thresholds[resource_type]
                alert_level = None
                threshold_value = 0

                if current_value >= threshold.emergency_level:
                    alert_level = AlertLevel.EMERGENCY
                    threshold_value = threshold.emergency_level
                elif current_value >= threshold.critical_level:
                    alert_level = AlertLevel.CRITICAL
                    threshold_value = threshold.critical_level
                elif current_value >= threshold.warning_level:
                    alert_level = AlertLevel.WARNING
                    threshold_value = threshold.warning_level

                if alert_level:
                    await self._create_alert(
                        agent_name, resource_type, alert_level,
                        current_value, threshold_value
                    )

                    # Take action if critical
                    if alert_level in [AlertLevel.CRITICAL, AlertLevel.EMERGENCY]:
                        await self._handle_critical_resource_usage(
                            agent_name, resource_type, threshold, current_value
                        )

        except Exception as e:
            self.logger.error(f"Error checking thresholds for {agent_name}: {e}")

    async def _create_alert(self, agent_name: str, resource_type: ResourceType,
                           alert_level: AlertLevel, current_value: float,
                           threshold_value: float):
        """Create and log a resource alert."""
        try:
            message = (
                f"{agent_name} {resource_type.value} usage {current_value:.1f}% "
                f"exceeds {alert_level.value} threshold {threshold_value:.1f}%"
            )

            alert = ResourceAlert(
                timestamp=time.time(),
                agent_name=agent_name,
                resource_type=resource_type,
                alert_level=alert_level,
                current_value=current_value,
                threshold_value=threshold_value,
                message=message
            )

            # Check if we already have an active alert for this resource
            existing = next(
                (a for a in self.active_alerts
                 if a.agent_name == agent_name and a.resource_type == resource_type and not a.resolved),
                None
            )

            if existing:
                # Update existing alert if severity changed
                if alert_level.value != existing.alert_level.value:
                    existing.resolved = True
                    self.active_alerts.append(alert)
            else:
                # New alert
                self.active_alerts.append(alert)

            # Add to history
            self.alert_history.append(alert)

            # Log the alert
            log_method = {
                AlertLevel.INFO: self.logger.info,
                AlertLevel.WARNING: self.logger.warning,
                AlertLevel.CRITICAL: self.logger.error,
                AlertLevel.EMERGENCY: self.logger.critical
            }.get(alert_level, self.logger.info)

            log_method(message)

        except Exception as e:
            self.logger.error(f"Error creating alert: {e}")

    async def _handle_critical_resource_usage(self, agent_name: str, resource_type: ResourceType,
                                            threshold: ResourceThreshold, current_value: float):
        """Handle critical resource usage based on configured action."""
        try:
            action = threshold.action_on_critical

            if action == "restart":
                self.logger.warning(f"Restarting {agent_name} due to critical {resource_type.value} usage")
                success = await self.agent_manager.restart_agent(agent_name)
                if success:
                    self.logger.info(f"Successfully restarted {agent_name}")
                else:
                    self.logger.error(f"Failed to restart {agent_name}")

            elif action == "throttle":
                await self._throttle_agent_process(agent_name, resource_type)

            # "alert_only" requires no action beyond the alert

        except Exception as e:
            self.logger.error(f"Error handling critical resource usage for {agent_name}: {e}")

    async def _throttle_agent_process(self, agent_name: str, resource_type: ResourceType):
        """Attempt to throttle an agent's resource usage."""
        try:
            agent = self.agent_manager.agents.get(agent_name)
            if not agent or not agent.pid:
                return

            process = psutil.Process(agent.pid)

            if resource_type == ResourceType.CPU:
                # Lower process priority
                try:
                    if hasattr(process, 'nice'):
                        current_nice = process.nice()
                        new_nice = min(current_nice + 5, 19)  # Lower priority
                        process.nice(new_nice)
                        self.logger.info(f"Throttled {agent_name} CPU priority: {current_nice} -> {new_nice}")
                except (psutil.AccessDenied, AttributeError):
                    self.logger.warning(f"Cannot throttle CPU for {agent_name}: Access denied")

        except Exception as e:
            self.logger.error(f"Error throttling {agent_name}: {e}")

    async def start_monitoring(self, interval: int = 15):
        """Start resource monitoring with specified interval."""
        if self._monitoring_active:
            self.logger.warning("Resource monitoring already active")
            return

        self._monitoring_active = True
        self._monitoring_task = asyncio.create_task(self._monitoring_loop(interval))
        self.logger.info(f"Started resource monitoring with {interval}s interval")

    async def stop_monitoring(self):
        """Stop resource monitoring."""
        self._monitoring_active = False
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        self.logger.info("Stopped resource monitoring")

    async def _monitoring_loop(self, interval: int):
        """Main resource monitoring loop."""
        try:
            while self._monitoring_active:
                # Collect metrics for all running agents
                for agent_name, agent in self.agent_manager.agents.items():
                    if agent.status == AgentStatus.RUNNING:
                        metrics = await self.collect_extended_metrics(agent_name)
                        if metrics:
                            await self.check_resource_thresholds(agent_name, metrics)

                # Clean up resolved alerts older than 1 hour
                cutoff_time = time.time() - 3600
                self.active_alerts = [
                    a for a in self.active_alerts
                    if not a.resolved or a.timestamp > cutoff_time
                ]

                await asyncio.sleep(interval)

        except asyncio.CancelledError:
            pass
        except Exception as e:
            self.logger.error(f"Resource monitoring loop error: {e}")

    def get_performance_recommendations(self, agent_name: str) -> List[str]:
        """Get performance optimization recommendations for an agent."""
        recommendations = []

        try:
            # Check if we have metrics for this agent
            if agent_name not in self.trend_analyzer.metrics_history:
                return ["Insufficient monitoring data for recommendations"]

            history = list(self.trend_analyzer.metrics_history[agent_name])
            if not history:
                return ["No metrics available for recommendations"]

            latest_metrics = history[-1]

            # CPU recommendations
            if latest_metrics.cpu_percent > 80:
                recommendations.append("High CPU usage detected - consider process optimization")

            cpu_trend = self.trend_analyzer.get_trend(agent_name, 'cpu_percent', window_minutes=10)
            if cpu_trend and cpu_trend > 1.0:  # Increasing by >1% per second
                recommendations.append("CPU usage trending upward - monitor for potential issues")

            # Memory recommendations
            if latest_metrics.memory_percent > 75:
                recommendations.append("High memory usage - consider memory optimization")

            memory_trend = self.trend_analyzer.get_trend(agent_name, 'memory_percent', window_minutes=10)
            if memory_trend and memory_trend > 0.5:  # Increasing by >0.5% per second
                exhaustion_time = self.trend_analyzer.predict_resource_exhaustion(
                    agent_name, 'memory_percent', 95.0
                )
                if exhaustion_time and exhaustion_time < 300:  # Less than 5 minutes
                    recommendations.append(f"Memory exhaustion predicted in {exhaustion_time:.0f}s - immediate action needed")

            # Thread recommendations
            if latest_metrics.thread_count > 50:
                recommendations.append("High thread count - review threading strategy")

            # File handle recommendations
            if latest_metrics.open_files > 100:
                recommendations.append("Many open files - ensure proper file handle cleanup")

            if not recommendations:
                recommendations.append("Agent performance appears optimal")

        except Exception as e:
            self.logger.error(f"Error generating recommendations for {agent_name}: {e}")
            recommendations.append("Error analyzing performance metrics")

        return recommendations

    def get_resource_summary(self) -> Dict[str, any]:
        """Get comprehensive resource usage summary."""
        try:
            summary = {
                "timestamp": time.time(),
                "active_alerts": len([a for a in self.active_alerts if not a.resolved]),
                "total_alerts_today": len([a for a in self.alert_history
                                          if a.timestamp > time.time() - 86400]),
                "agents": {},
                "system_totals": {
                    "total_cpu": 0.0,
                    "total_memory_mb": 0.0,
                    "running_agents": 0
                }
            }

            # Add per-agent metrics
            for agent_name in self.agent_manager.agents:
                if agent_name in self.trend_analyzer.metrics_history:
                    history = list(self.trend_analyzer.metrics_history[agent_name])
                    if history:
                        latest = history[-1]
                        summary["agents"][agent_name] = {
                            "cpu_percent": latest.cpu_percent,
                            "memory_mb": latest.memory_mb,
                            "memory_percent": latest.memory_percent,
                            "open_files": latest.open_files,
                            "thread_count": latest.thread_count,
                            "priority": latest.priority,
                            "active_alerts": len([a for a in self.active_alerts
                                                if a.agent_name == agent_name and not a.resolved])
                        }

                        # Add to system totals
                        if self.agent_manager.agents[agent_name].status == AgentStatus.RUNNING:
                            summary["system_totals"]["total_cpu"] += latest.cpu_percent
                            summary["system_totals"]["total_memory_mb"] += latest.memory_mb
                            summary["system_totals"]["running_agents"] += 1

            return summary

        except Exception as e:
            self.logger.error(f"Error generating resource summary: {e}")
            return {"error": str(e), "timestamp": time.time()}

    def get_active_alerts(self, agent_name: Optional[str] = None) -> List[ResourceAlert]:
        """Get active resource alerts, optionally filtered by agent."""
        active = [a for a in self.active_alerts if not a.resolved]

        if agent_name:
            active = [a for a in active if a.agent_name == agent_name]

        return active

    def resolve_alert(self, alert_id: int):
        """Mark an alert as resolved."""
        if 0 <= alert_id < len(self.active_alerts):
            self.active_alerts[alert_id].resolved = True
            self.logger.info(f"Resolved alert: {self.active_alerts[alert_id].message}")

    async def cleanup(self):
        """Clean up resource manager."""
        self.logger.info("Cleaning up Resource Manager...")
        await self.stop_monitoring()
        self.logger.info("Resource Manager cleanup complete")