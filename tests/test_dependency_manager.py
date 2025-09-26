"""
Unit tests for Dependency Manager functionality.

This test suite covers agent dependency resolution, startup sequencing,
restart policies, and orchestration logic.
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.orchestrator.dependency_manager import (
    DependencyManager, AgentDependency, StartupPolicy, RestartPolicy, StartupSequence
)
from src.orchestrator.agent_manager import AgentManager, AgentStatus


class TestDependencyManager:
    """Test suite for DependencyManager class."""

    @pytest.fixture
    def mock_agent_manager(self):
        """Mock agent manager for testing."""
        agent_manager = Mock(spec=AgentManager)
        agent_manager.start_agent = AsyncMock(return_value=True)
        agent_manager.restart_agent = AsyncMock(return_value=True)
        return agent_manager

    @pytest.fixture
    def dependency_manager(self, mock_agent_manager):
        """Create DependencyManager instance with mocked agent manager."""
        with patch('src.orchestrator.dependency_manager.get_logger') as mock_logger:
            mock_logger.return_value = Mock()
            manager = DependencyManager(mock_agent_manager)
            return manager

    def test_dependency_manager_initialization(self, dependency_manager):
        """Test DependencyManager initializes correctly."""
        assert dependency_manager is not None
        assert len(dependency_manager.dependencies) > 0
        assert "market_data" in dependency_manager.dependencies
        assert dependency_manager.startup_policy == StartupPolicy.DEPENDENCY_BASED

    def test_default_dependencies_setup(self, dependency_manager):
        """Test default agent dependencies are set up correctly."""
        deps = dependency_manager.get_all_dependencies()

        # Market Data Agent - no dependencies
        market_data = deps["market_data"]
        assert market_data.agent_name == "market_data"
        assert len(market_data.depends_on) == 0
        assert market_data.required is True
        assert market_data.priority == 100

        # Pattern Recognition - depends on Market Data
        pattern = deps["pattern_recognition"]
        assert "market_data" in pattern.depends_on
        assert pattern.priority < market_data.priority

        # Risk Management - depends on Market Data and Pattern Recognition
        risk = deps["risk_management"]
        assert "market_data" in risk.depends_on
        assert "pattern_recognition" in risk.depends_on
        assert risk.priority == 90

    def test_add_dependency_success(self, dependency_manager):
        """Test successful dependency addition."""
        new_dep = AgentDependency(
            agent_name="test_agent",
            depends_on=["market_data"],
            required=False,
            priority=50
        )

        result = dependency_manager.add_dependency(new_dep)
        assert result is True
        assert "test_agent" in dependency_manager.get_all_dependencies()

    def test_add_dependency_circular_detection(self, dependency_manager):
        """Test circular dependency detection."""
        # Try to create a circular dependency
        circular_dep = AgentDependency(
            agent_name="market_data",  # Already exists
            depends_on=["advisor"],  # Creates cycle: market_data -> advisor -> market_data
            required=False
        )

        result = dependency_manager.add_dependency(circular_dep)
        assert result is False

    def test_create_startup_sequence_simple(self, dependency_manager):
        """Test startup sequence creation for simple dependencies."""
        # Test with just market_data and pattern_recognition
        sequence = dependency_manager.create_startup_sequence(["market_data", "pattern_recognition"])

        assert isinstance(sequence, StartupSequence)
        assert sequence.total_agents == 2
        assert len(sequence.sequence) == 2  # Two groups

        # Market data should be first (no dependencies)
        assert "market_data" in sequence.sequence[0]
        # Pattern recognition should be second (depends on market_data)
        assert "pattern_recognition" in sequence.sequence[1]

    def test_create_startup_sequence_complex(self, dependency_manager):
        """Test startup sequence with complex dependencies."""
        all_agents = ["market_data", "pattern_recognition", "risk_management", "advisor"]
        sequence = dependency_manager.create_startup_sequence(all_agents)

        assert sequence.total_agents == 4

        # Find positions of agents in sequence
        positions = {}
        for i, group in enumerate(sequence.sequence):
            for agent in group:
                positions[agent] = i

        # Verify dependency order
        assert positions["market_data"] < positions["pattern_recognition"]
        assert positions["market_data"] < positions["risk_management"]
        assert positions["pattern_recognition"] < positions["risk_management"]
        assert positions["risk_management"] < positions["advisor"]

    def test_topological_sort_priority_ordering(self, dependency_manager):
        """Test that agents with same dependency level are ordered by priority."""
        # Add two agents that depend on market_data with different priorities
        high_priority = AgentDependency(
            agent_name="high_priority_agent",
            depends_on=["market_data"],
            priority=95
        )
        low_priority = AgentDependency(
            agent_name="low_priority_agent",
            depends_on=["market_data"],
            priority=85
        )

        dependency_manager.add_dependency(high_priority)
        dependency_manager.add_dependency(low_priority)

        sequence = dependency_manager.create_startup_sequence(
            ["market_data", "high_priority_agent", "low_priority_agent"]
        )

        # Find the group containing both agents
        for group in sequence.sequence:
            if "high_priority_agent" in group and "low_priority_agent" in group:
                high_idx = group.index("high_priority_agent")
                low_idx = group.index("low_priority_agent")
                assert high_idx < low_idx  # Higher priority comes first

    @pytest.mark.asyncio
    async def test_start_agents_with_dependencies_success(self, dependency_manager, mock_agent_manager):
        """Test successful startup with dependencies."""
        # Mock all agents as successful starts
        mock_agent_manager.start_agent.return_value = True

        results = await dependency_manager.start_agents_with_dependencies(["market_data", "pattern_recognition"])

        assert len(results) == 2
        assert all(results.values())  # All should be successful
        assert mock_agent_manager.start_agent.call_count == 2

    @pytest.mark.asyncio
    async def test_start_agents_required_failure_stops_sequence(self, dependency_manager, mock_agent_manager):
        """Test that required agent failure stops startup sequence."""
        # Mock market_data (required) to fail
        def mock_start_agent(agent_name, **kwargs):
            if agent_name == "market_data":
                return False
            return True

        mock_agent_manager.start_agent.side_effect = mock_start_agent

        results = await dependency_manager.start_agents_with_dependencies(
            ["market_data", "pattern_recognition", "risk_management"]
        )

        # Should only try to start market_data, then stop due to failure
        assert results["market_data"] is False
        assert len(results) == 1  # Should stop after required agent fails

    @pytest.mark.asyncio
    async def test_handle_agent_failure_immediate_restart(self, dependency_manager, mock_agent_manager):
        """Test immediate restart policy."""
        # Set market_data to immediate restart
        dependency_manager.dependencies["market_data"].restart_policy = RestartPolicy.IMMEDIATE

        result = await dependency_manager.handle_agent_failure("market_data")

        assert result is True
        mock_agent_manager.restart_agent.assert_called_once_with("market_data")

    @pytest.mark.asyncio
    async def test_handle_agent_failure_max_attempts_exceeded(self, dependency_manager, mock_agent_manager):
        """Test max restart attempts limit."""
        # Set restart attempts to max
        dependency_manager.restart_attempts["market_data"] = 5
        dependency_manager.dependencies["market_data"].max_restart_attempts = 3

        result = await dependency_manager.handle_agent_failure("market_data")

        assert result is False
        mock_agent_manager.restart_agent.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_agent_failure_manual_policy(self, dependency_manager, mock_agent_manager):
        """Test manual restart policy."""
        dependency_manager.dependencies["backtest"].restart_policy = RestartPolicy.MANUAL

        result = await dependency_manager.handle_agent_failure("backtest")

        assert result is False
        mock_agent_manager.restart_agent.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_agent_failure_exponential_backoff(self, dependency_manager, mock_agent_manager):
        """Test exponential backoff restart policy."""
        # Set exponential backoff policy
        dependency_manager.dependencies["market_data"].restart_policy = RestartPolicy.EXPONENTIAL_BACKOFF
        dependency_manager.dependencies["market_data"].restart_delay = 2
        dependency_manager.restart_attempts["market_data"] = 2  # Third attempt

        start_time = time.time()

        # Mock sleep to avoid actual waiting
        with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
            result = await dependency_manager.handle_agent_failure("market_data")

        # Should calculate delay as 2 * (2^2) = 8 seconds
        mock_sleep.assert_called_once_with(8)
        assert result is True

    def test_calculate_restart_delay_policies(self, dependency_manager):
        """Test restart delay calculations for different policies."""
        agent_name = "test_agent"

        # Immediate policy
        config = AgentDependency(agent_name, restart_policy=RestartPolicy.IMMEDIATE)
        delay = dependency_manager._calculate_restart_delay(agent_name, config)
        assert delay == 0

        # Delayed policy
        config = AgentDependency(agent_name, restart_policy=RestartPolicy.DELAYED, restart_delay=10)
        delay = dependency_manager._calculate_restart_delay(agent_name, config)
        assert delay == 10

        # Exponential backoff
        config = AgentDependency(agent_name, restart_policy=RestartPolicy.EXPONENTIAL_BACKOFF, restart_delay=5)
        dependency_manager.restart_attempts[agent_name] = 3
        delay = dependency_manager._calculate_restart_delay(agent_name, config)
        assert delay == 5 * (2 ** 3)  # 40 seconds

    def test_get_dependency_info(self, dependency_manager):
        """Test getting dependency information."""
        info = dependency_manager.get_dependency_info("market_data")
        assert info is not None
        assert info.agent_name == "market_data"

        # Non-existent agent
        info = dependency_manager.get_dependency_info("nonexistent")
        assert info is None

    def test_get_restart_statistics(self, dependency_manager):
        """Test restart statistics retrieval."""
        # Set some restart attempts
        dependency_manager.restart_attempts["market_data"] = 2
        dependency_manager.last_restart_time["market_data"] = time.time()

        stats = dependency_manager.get_restart_statistics()

        assert "market_data" in stats
        assert stats["market_data"]["restart_attempts"] == 2
        assert stats["market_data"]["max_attempts"] == 5
        assert stats["market_data"]["last_restart"] > 0

    def test_reset_restart_statistics(self, dependency_manager):
        """Test restart statistics reset."""
        # Set some restart attempts
        dependency_manager.restart_attempts["market_data"] = 3
        dependency_manager.last_restart_time["market_data"] = time.time()

        # Reset specific agent
        dependency_manager.reset_restart_statistics("market_data")
        assert dependency_manager.restart_attempts["market_data"] == 0
        assert "market_data" not in dependency_manager.last_restart_time

        # Set again and reset all
        dependency_manager.restart_attempts["market_data"] = 2
        dependency_manager.restart_attempts["pattern_recognition"] = 1

        dependency_manager.reset_restart_statistics()
        assert len(dependency_manager.restart_attempts) == 0
        assert len(dependency_manager.last_restart_time) == 0

    def test_estimate_startup_time(self, dependency_manager):
        """Test startup time estimation."""
        sequence = dependency_manager.create_startup_sequence(["market_data", "pattern_recognition"])

        # Should be sum of timeouts for sequential groups
        expected_time = 30 + 45  # market_data timeout + pattern_recognition timeout
        assert sequence.estimated_time == expected_time


class TestAgentDependency:
    """Test AgentDependency data structure."""

    def test_agent_dependency_creation(self):
        """Test AgentDependency creation with defaults."""
        dep = AgentDependency("test_agent")

        assert dep.agent_name == "test_agent"
        assert dep.depends_on == []
        assert dep.required is True
        assert dep.timeout == 30
        assert dep.priority == 0
        assert dep.restart_policy == RestartPolicy.DELAYED
        assert dep.max_restart_attempts == 3
        assert dep.restart_delay == 5

    def test_agent_dependency_custom_values(self):
        """Test AgentDependency with custom values."""
        dep = AgentDependency(
            agent_name="custom_agent",
            depends_on=["dep1", "dep2"],
            required=False,
            timeout=60,
            priority=100,
            restart_policy=RestartPolicy.EXPONENTIAL_BACKOFF,
            max_restart_attempts=5,
            restart_delay=10
        )

        assert dep.agent_name == "custom_agent"
        assert dep.depends_on == ["dep1", "dep2"]
        assert dep.required is False
        assert dep.timeout == 60
        assert dep.priority == 100
        assert dep.restart_policy == RestartPolicy.EXPONENTIAL_BACKOFF
        assert dep.max_restart_attempts == 5
        assert dep.restart_delay == 10


if __name__ == "__main__":
    pytest.main([__file__])