"""
Unit tests for Resource Manager functionality.

This test suite covers resource monitoring, threshold management,
alert generation, and performance optimization features.
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.orchestrator.resource_manager import (
    ResourceManager, ResourceThreshold, ResourceAlert, ProcessMetrics,
    AlertLevel, ResourceType, ResourceTrendAnalyzer
)
from src.orchestrator.agent_manager import AgentManager, AgentStatus


class TestResourceManager:
    """Test suite for ResourceManager class."""

    @pytest.fixture
    def mock_agent_manager(self):
        """Mock agent manager for testing."""
        agent_manager = Mock(spec=AgentManager)
        agent_manager.agents = {
            "test_agent": Mock(
                pid=1234,
                status=AgentStatus.RUNNING,
                name="Test Agent"
            )
        }
        agent_manager.restart_agent = AsyncMock(return_value=True)
        return agent_manager

    @pytest.fixture
    def resource_manager(self, mock_agent_manager):
        """Create ResourceManager instance with mocked agent manager."""
        with patch('src.orchestrator.resource_manager.get_logger') as mock_logger:
            mock_logger.return_value = Mock()
            manager = ResourceManager(mock_agent_manager)
            return manager

    def test_resource_manager_initialization(self, resource_manager):
        """Test ResourceManager initializes correctly."""
        assert resource_manager is not None
        assert len(resource_manager.resource_thresholds) > 0
        assert ResourceType.CPU in resource_manager.resource_thresholds
        assert ResourceType.MEMORY in resource_manager.resource_thresholds
        assert not resource_manager._monitoring_active

    def test_default_thresholds_setup(self, resource_manager):
        """Test default resource thresholds are configured."""
        cpu_threshold = resource_manager.resource_thresholds[ResourceType.CPU]
        assert cpu_threshold.warning_level == 70.0
        assert cpu_threshold.critical_level == 85.0
        assert cpu_threshold.emergency_level == 95.0
        assert cpu_threshold.action_on_critical == "throttle"

        memory_threshold = resource_manager.resource_thresholds[ResourceType.MEMORY]
        assert memory_threshold.warning_level == 75.0
        assert memory_threshold.critical_level == 90.0
        assert memory_threshold.emergency_level == 98.0
        assert memory_threshold.action_on_critical == "restart"

    @pytest.mark.asyncio
    async def test_collect_extended_metrics_success(self, resource_manager):
        """Test successful extended metrics collection."""
        mock_process = Mock()
        mock_process.cpu_percent.return_value = 25.5
        mock_process.memory_info.return_value = Mock(rss=100 * 1024 * 1024)  # 100 MB
        mock_process.memory_percent.return_value = 15.0
        mock_process.io_counters.return_value = Mock(
            read_bytes=50 * 1024 * 1024,  # 50 MB
            write_bytes=30 * 1024 * 1024   # 30 MB
        )
        mock_process.open_files.return_value = []
        mock_process.num_threads.return_value = 5
        mock_process.nice.return_value = 0

        with patch('psutil.Process', return_value=mock_process):
            with patch('psutil.net_io_counters', return_value=Mock(
                bytes_sent=1024 * 1024, bytes_recv=2048 * 1024
            )):
                metrics = await resource_manager.collect_extended_metrics("test_agent")

        assert metrics is not None
        assert metrics.cpu_percent == 25.5
        assert metrics.memory_mb == 100.0
        assert metrics.memory_percent == 15.0
        assert metrics.disk_read_mb == 50.0
        assert metrics.disk_write_mb == 30.0
        assert metrics.open_files == 0
        assert metrics.thread_count == 5

    @pytest.mark.asyncio
    async def test_collect_extended_metrics_no_process(self, resource_manager):
        """Test metrics collection when agent has no process."""
        # Modify agent to have no PID
        resource_manager.agent_manager.agents["test_agent"].pid = None

        metrics = await resource_manager.collect_extended_metrics("test_agent")
        assert metrics is None

    @pytest.mark.asyncio
    async def test_check_resource_thresholds_warning(self, resource_manager):
        """Test resource threshold checking generates warning alert."""
        metrics = ProcessMetrics(
            cpu_percent=75.0,  # Above warning threshold (70%)
            memory_percent=60.0  # Below warning threshold
        )

        # Mock the alert creation method
        resource_manager._create_alert = AsyncMock()

        await resource_manager.check_resource_thresholds("test_agent", metrics)

        # Should create one alert for CPU
        resource_manager._create_alert.assert_called_once()
        args = resource_manager._create_alert.call_args[0]
        assert args[0] == "test_agent"  # agent_name
        assert args[1] == ResourceType.CPU  # resource_type
        assert args[2] == AlertLevel.WARNING  # alert_level

    @pytest.mark.asyncio
    async def test_check_resource_thresholds_critical(self, resource_manager):
        """Test critical threshold triggers action."""
        metrics = ProcessMetrics(
            cpu_percent=90.0,  # Above critical threshold (85%)
            memory_percent=95.0  # Above critical threshold (90%)
        )

        resource_manager._create_alert = AsyncMock()
        resource_manager._handle_critical_resource_usage = AsyncMock()

        await resource_manager.check_resource_thresholds("test_agent", metrics)

        # Should handle critical usage for both CPU and memory
        assert resource_manager._handle_critical_resource_usage.call_count == 2

    @pytest.mark.asyncio
    async def test_handle_critical_resource_usage_restart(self, resource_manager):
        """Test critical resource usage triggers restart action."""
        threshold = ResourceThreshold(
            resource_type=ResourceType.MEMORY,
            warning_level=75.0,
            critical_level=90.0,
            emergency_level=98.0,
            action_on_critical="restart"
        )

        await resource_manager._handle_critical_resource_usage(
            "test_agent", ResourceType.MEMORY, threshold, 95.0
        )

        # Should call restart_agent
        resource_manager.agent_manager.restart_agent.assert_called_once_with("test_agent")

    @pytest.mark.asyncio
    async def test_handle_critical_resource_usage_throttle(self, resource_manager):
        """Test critical resource usage triggers throttle action."""
        threshold = ResourceThreshold(
            resource_type=ResourceType.CPU,
            warning_level=70.0,
            critical_level=85.0,
            emergency_level=95.0,
            action_on_critical="throttle"
        )

        resource_manager._throttle_agent_process = AsyncMock()

        await resource_manager._handle_critical_resource_usage(
            "test_agent", ResourceType.CPU, threshold, 90.0
        )

        # Should call throttle
        resource_manager._throttle_agent_process.assert_called_once_with(
            "test_agent", ResourceType.CPU
        )

    @pytest.mark.asyncio
    async def test_throttle_agent_process(self, resource_manager):
        """Test agent process throttling."""
        mock_process = Mock()
        mock_process.nice.return_value = 0

        with patch('psutil.Process', return_value=mock_process):
            await resource_manager._throttle_agent_process("test_agent", ResourceType.CPU)

        # Should set process priority
        mock_process.nice.assert_called_with(5)  # Lowered priority

    @pytest.mark.asyncio
    async def test_create_alert(self, resource_manager):
        """Test alert creation."""
        await resource_manager._create_alert(
            "test_agent", ResourceType.CPU, AlertLevel.WARNING, 75.0, 70.0
        )

        assert len(resource_manager.active_alerts) == 1
        alert = resource_manager.active_alerts[0]
        assert alert.agent_name == "test_agent"
        assert alert.resource_type == ResourceType.CPU
        assert alert.alert_level == AlertLevel.WARNING
        assert alert.current_value == 75.0
        assert alert.threshold_value == 70.0
        assert not alert.resolved

        # Should also be in history
        assert len(resource_manager.alert_history) == 1

    @pytest.mark.asyncio
    async def test_monitoring_lifecycle(self, resource_manager):
        """Test monitoring start and stop."""
        # Mock the monitoring loop to avoid actual monitoring
        with patch.object(resource_manager, '_monitoring_loop', new_callable=AsyncMock):
            # Start monitoring
            await resource_manager.start_monitoring(interval=1)
            assert resource_manager._monitoring_active is True
            assert resource_manager._monitoring_task is not None

            # Stop monitoring
            await resource_manager.stop_monitoring()
            assert resource_manager._monitoring_active is False

    def test_get_performance_recommendations_insufficient_data(self, resource_manager):
        """Test performance recommendations with no data."""
        recommendations = resource_manager.get_performance_recommendations("unknown_agent")
        assert len(recommendations) == 1
        assert "Insufficient monitoring data" in recommendations[0]

    def test_get_performance_recommendations_high_cpu(self, resource_manager):
        """Test performance recommendations for high CPU usage."""
        # Add metrics with high CPU usage
        metrics = ProcessMetrics(cpu_percent=85.0, memory_percent=50.0, thread_count=10)
        resource_manager.trend_analyzer.add_metrics("test_agent", metrics)

        recommendations = resource_manager.get_performance_recommendations("test_agent")
        assert any("High CPU usage" in rec for rec in recommendations)

    def test_get_performance_recommendations_high_memory(self, resource_manager):
        """Test performance recommendations for high memory usage."""
        # Add metrics with high memory usage
        metrics = ProcessMetrics(cpu_percent=50.0, memory_percent=80.0, open_files=150)
        resource_manager.trend_analyzer.add_metrics("test_agent", metrics)

        recommendations = resource_manager.get_performance_recommendations("test_agent")
        assert any("High memory usage" in rec for rec in recommendations)
        assert any("Many open files" in rec for rec in recommendations)

    def test_get_resource_summary(self, resource_manager):
        """Test resource summary generation."""
        # Add some metrics and alerts
        metrics = ProcessMetrics(cpu_percent=60.0, memory_mb=200.0, memory_percent=40.0)
        resource_manager.trend_analyzer.add_metrics("test_agent", metrics)

        alert = ResourceAlert(
            timestamp=time.time(),
            agent_name="test_agent",
            resource_type=ResourceType.CPU,
            alert_level=AlertLevel.WARNING,
            current_value=75.0,
            threshold_value=70.0,
            message="Test alert"
        )
        resource_manager.active_alerts.append(alert)

        summary = resource_manager.get_resource_summary()

        assert "timestamp" in summary
        assert summary["active_alerts"] == 1
        assert "test_agent" in summary["agents"]
        assert summary["agents"]["test_agent"]["cpu_percent"] == 60.0
        assert summary["agents"]["test_agent"]["active_alerts"] == 1
        assert summary["system_totals"]["running_agents"] == 1

    def test_get_active_alerts(self, resource_manager):
        """Test active alerts retrieval."""
        alert1 = ResourceAlert(
            timestamp=time.time(),
            agent_name="agent1",
            resource_type=ResourceType.CPU,
            alert_level=AlertLevel.WARNING,
            current_value=75.0,
            threshold_value=70.0,
            message="Agent1 alert"
        )

        alert2 = ResourceAlert(
            timestamp=time.time(),
            agent_name="agent2",
            resource_type=ResourceType.MEMORY,
            alert_level=AlertLevel.CRITICAL,
            current_value=95.0,
            threshold_value=90.0,
            message="Agent2 alert",
            resolved=True  # Resolved alert
        )

        resource_manager.active_alerts.extend([alert1, alert2])

        # Get all active alerts
        active = resource_manager.get_active_alerts()
        assert len(active) == 1  # Only unresolved
        assert active[0].agent_name == "agent1"

        # Get alerts for specific agent
        agent1_alerts = resource_manager.get_active_alerts("agent1")
        assert len(agent1_alerts) == 1
        assert agent1_alerts[0].agent_name == "agent1"

    def test_resolve_alert(self, resource_manager):
        """Test alert resolution."""
        alert = ResourceAlert(
            timestamp=time.time(),
            agent_name="test_agent",
            resource_type=ResourceType.CPU,
            alert_level=AlertLevel.WARNING,
            current_value=75.0,
            threshold_value=70.0,
            message="Test alert"
        )
        resource_manager.active_alerts.append(alert)

        # Resolve the alert
        resource_manager.resolve_alert(0)
        assert resource_manager.active_alerts[0].resolved is True

    @pytest.mark.asyncio
    async def test_cleanup(self, resource_manager):
        """Test resource manager cleanup."""
        # Start monitoring first
        with patch.object(resource_manager, '_monitoring_loop', new_callable=AsyncMock):
            await resource_manager.start_monitoring()
            assert resource_manager._monitoring_active is True

            # Cleanup should stop monitoring
            await resource_manager.cleanup()
            assert resource_manager._monitoring_active is False


class TestResourceTrendAnalyzer:
    """Test suite for ResourceTrendAnalyzer."""

    @pytest.fixture
    def trend_analyzer(self):
        """Create ResourceTrendAnalyzer instance."""
        return ResourceTrendAnalyzer(history_size=10)

    def test_add_metrics(self, trend_analyzer):
        """Test adding metrics to trend analyzer."""
        metrics = ProcessMetrics(cpu_percent=50.0, memory_percent=60.0)
        trend_analyzer.add_metrics("test_agent", metrics)

        assert "test_agent" in trend_analyzer.metrics_history
        assert len(trend_analyzer.metrics_history["test_agent"]) == 1

    def test_get_trend_insufficient_data(self, trend_analyzer):
        """Test trend calculation with insufficient data."""
        # Add only one data point
        metrics = ProcessMetrics(cpu_percent=50.0)
        trend_analyzer.add_metrics("test_agent", metrics)

        trend = trend_analyzer.get_trend("test_agent", "cpu_percent", window_minutes=10)
        assert trend is None

    def test_get_trend_calculation(self, trend_analyzer):
        """Test trend calculation with multiple data points."""
        # Add metrics with increasing CPU usage
        base_time = time.time()
        for i, cpu_val in enumerate([50.0, 60.0, 70.0]):
            metrics = ProcessMetrics(cpu_percent=cpu_val)
            metrics.timestamp = base_time + (i * 60)  # 1 minute apart
            trend_analyzer.add_metrics("test_agent", metrics)

        trend = trend_analyzer.get_trend("test_agent", "cpu_percent", window_minutes=10)
        assert trend is not None
        assert trend > 0  # Should be positive (increasing)

    def test_predict_resource_exhaustion(self, trend_analyzer):
        """Test resource exhaustion prediction."""
        base_time = time.time()
        # Add metrics showing increasing memory usage
        for i, mem_val in enumerate([70.0, 80.0, 90.0]):
            metrics = ProcessMetrics(memory_percent=mem_val)
            metrics.timestamp = base_time + (i * 60)  # 1 minute apart
            trend_analyzer.add_metrics("test_agent", metrics)

        exhaustion_time = trend_analyzer.predict_resource_exhaustion(
            "test_agent", "memory_percent", 100.0
        )
        assert exhaustion_time is not None
        assert exhaustion_time > 0


class TestResourceThreshold:
    """Test ResourceThreshold data structure."""

    def test_resource_threshold_creation(self):
        """Test ResourceThreshold creation."""
        threshold = ResourceThreshold(
            resource_type=ResourceType.CPU,
            warning_level=70.0,
            critical_level=85.0,
            emergency_level=95.0,
            check_interval=30,
            action_on_critical="throttle"
        )

        assert threshold.resource_type == ResourceType.CPU
        assert threshold.warning_level == 70.0
        assert threshold.critical_level == 85.0
        assert threshold.emergency_level == 95.0
        assert threshold.check_interval == 30
        assert threshold.action_on_critical == "throttle"


class TestProcessMetrics:
    """Test ProcessMetrics data structure."""

    def test_process_metrics_creation(self):
        """Test ProcessMetrics creation with defaults."""
        metrics = ProcessMetrics()

        assert metrics.cpu_percent == 0.0
        assert metrics.memory_mb == 0.0
        assert metrics.memory_percent == 0.0
        assert metrics.disk_read_mb == 0.0
        assert metrics.disk_write_mb == 0.0
        assert metrics.open_files == 0
        assert metrics.thread_count == 0
        assert metrics.timestamp > 0

    def test_process_metrics_custom_values(self):
        """Test ProcessMetrics with custom values."""
        timestamp = time.time()
        metrics = ProcessMetrics(
            cpu_percent=75.5,
            memory_mb=512.0,
            memory_percent=25.0,
            disk_read_mb=100.0,
            disk_write_mb=50.0,
            network_sent_mb=10.0,
            network_recv_mb=20.0,
            open_files=25,
            thread_count=8,
            priority=5,
            timestamp=timestamp
        )

        assert metrics.cpu_percent == 75.5
        assert metrics.memory_mb == 512.0
        assert metrics.memory_percent == 25.0
        assert metrics.disk_read_mb == 100.0
        assert metrics.disk_write_mb == 50.0
        assert metrics.network_sent_mb == 10.0
        assert metrics.network_recv_mb == 20.0
        assert metrics.open_files == 25
        assert metrics.thread_count == 8
        assert metrics.priority == 5
        assert metrics.timestamp == timestamp


if __name__ == "__main__":
    pytest.main([__file__])