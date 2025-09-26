"""
Unit tests for Agent Manager functionality.

This test suite covers agent lifecycle management, health monitoring,
process control, and configuration handling.
"""

import pytest
import asyncio
import subprocess
import sys
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.orchestrator.agent_manager import AgentManager, AgentInfo, AgentStatus


class TestAgentManager:
    """Test suite for AgentManager class."""

    @pytest.fixture
    def mock_config_manager(self):
        """Mock configuration manager for testing."""
        config_manager = Mock()
        market_data_config = Mock()
        market_data_config.url = "http://localhost:8000"
        market_data_config.enabled = True

        config_manager.get_all_agent_configs.return_value = {
            "market_data": market_data_config
        }
        return config_manager

    @pytest.fixture
    def agent_manager(self, mock_config_manager):
        """Create AgentManager instance with mocked config."""
        with patch('src.orchestrator.agent_manager.get_config_manager', return_value=mock_config_manager):
            with patch('src.orchestrator.agent_manager.get_logger') as mock_logger:
                mock_logger.return_value = Mock()
                manager = AgentManager()
                return manager

    def test_agent_manager_initialization(self, agent_manager):
        """Test AgentManager initializes correctly."""
        assert agent_manager is not None
        assert len(agent_manager.agents) > 0
        assert "market_data" in agent_manager.agents
        assert not agent_manager._monitoring_active

    def test_agent_info_structure(self, agent_manager):
        """Test AgentInfo data structure."""
        market_data_agent = agent_manager.agents["market_data"]

        assert isinstance(market_data_agent, AgentInfo)
        assert market_data_agent.name == "Market Data Agent"
        assert market_data_agent.url == "http://localhost:8000"
        assert market_data_agent.port == 8000
        assert market_data_agent.status == AgentStatus.STOPPED
        assert market_data_agent.process is None
        assert market_data_agent.pid is None

    @pytest.mark.asyncio
    async def test_start_agent_success(self, agent_manager):
        """Test successful agent startup."""
        # Mock subprocess.Popen
        mock_process = Mock()
        mock_process.pid = 12345
        mock_process.poll.return_value = None

        with patch('subprocess.Popen', return_value=mock_process):
            with patch.object(agent_manager, '_wait_for_health', return_value=True):
                result = await agent_manager.start_agent("market_data")

        assert result is True
        agent = agent_manager.agents["market_data"]
        assert agent.status == AgentStatus.RUNNING
        assert agent.process == mock_process
        assert agent.pid == 12345

    @pytest.mark.asyncio
    async def test_start_agent_directory_not_found(self, agent_manager):
        """Test agent startup failure when directory doesn't exist."""
        # Make the agent path point to a non-existent directory
        agent_manager.agents["market_data"].path = Path("/non/existent/path")

        result = await agent_manager.start_agent("market_data")

        assert result is False
        agent = agent_manager.agents["market_data"]
        assert agent.status == AgentStatus.ERROR
        assert "Agent directory not found" in agent.error_message

    @pytest.mark.asyncio
    async def test_start_agent_already_running(self, agent_manager):
        """Test starting agent that's already running."""
        # Set agent as already running
        agent_manager.agents["market_data"].status = AgentStatus.RUNNING

        with patch.object(agent_manager, '_check_agent_health', return_value=True):
            result = await agent_manager.start_agent("market_data")

        assert result is True

    @pytest.mark.asyncio
    async def test_stop_agent_success(self, agent_manager):
        """Test successful agent shutdown."""
        # Setup running agent
        mock_process = Mock()
        mock_process.poll.return_value = None

        agent = agent_manager.agents["market_data"]
        agent.status = AgentStatus.RUNNING
        agent.process = mock_process
        agent.pid = 12345

        result = await agent_manager.stop_agent("market_data")

        assert result is True
        assert agent.status == AgentStatus.STOPPED
        assert agent.process is None
        assert agent.pid is None
        mock_process.terminate.assert_called_once()

    @pytest.mark.asyncio
    async def test_stop_agent_already_stopped(self, agent_manager):
        """Test stopping agent that's already stopped."""
        result = await agent_manager.stop_agent("market_data")
        assert result is True

    @pytest.mark.asyncio
    async def test_restart_agent(self, agent_manager):
        """Test agent restart functionality."""
        with patch.object(agent_manager, 'stop_agent', return_value=True) as mock_stop:
            with patch.object(agent_manager, 'start_agent', return_value=True) as mock_start:
                result = await agent_manager.restart_agent("market_data")

        assert result is True
        mock_stop.assert_called_once_with("market_data")
        mock_start.assert_called_once_with("market_data")

    @pytest.mark.asyncio
    async def test_get_agent_status(self, agent_manager):
        """Test getting agent status."""
        result = await agent_manager.get_agent_status("market_data")

        assert result is not None
        assert isinstance(result, AgentInfo)
        assert result.name == "Market Data Agent"

    @pytest.mark.asyncio
    async def test_get_all_agent_status(self, agent_manager):
        """Test getting all agent statuses."""
        result = await agent_manager.get_all_agent_status()

        assert isinstance(result, dict)
        assert "market_data" in result
        assert isinstance(result["market_data"], AgentInfo)

    @pytest.mark.asyncio
    async def test_start_all_enabled_agents(self, agent_manager):
        """Test starting all enabled agents."""
        with patch.object(agent_manager, 'start_agent', return_value=True) as mock_start:
            results = await agent_manager.start_all_enabled_agents()

        assert isinstance(results, dict)
        assert "market_data" in results
        mock_start.assert_called()

    @pytest.mark.asyncio
    async def test_stop_all_agents(self, agent_manager):
        """Test stopping all agents."""
        # Set up a running agent
        agent_manager.agents["market_data"].status = AgentStatus.RUNNING

        with patch.object(agent_manager, 'stop_agent', return_value=True) as mock_stop:
            results = await agent_manager.stop_all_agents()

        assert isinstance(results, dict)
        assert "market_data" in results
        mock_stop.assert_called_with("market_data")

    @pytest.mark.asyncio
    async def test_health_check_success(self, agent_manager):
        """Test successful health check."""
        mock_response = Mock()
        mock_response.status_code = 200

        with patch('requests.get', return_value=mock_response):
            result = await agent_manager._check_agent_health("market_data")

        assert result is True
        agent = agent_manager.agents["market_data"]
        assert agent.last_health_check is not None

    @pytest.mark.asyncio
    async def test_health_check_failure(self, agent_manager):
        """Test health check failure."""
        with patch('requests.get', side_effect=ConnectionError("Connection failed")):
            result = await agent_manager._check_agent_health("market_data")

        assert result is False

    @pytest.mark.asyncio
    async def test_wait_for_health_success(self, agent_manager):
        """Test waiting for agent health success."""
        with patch.object(agent_manager, '_check_agent_health', return_value=True):
            result = await agent_manager._wait_for_health("market_data", timeout=5)

        assert result is True

    @pytest.mark.asyncio
    async def test_wait_for_health_timeout(self, agent_manager):
        """Test waiting for agent health timeout."""
        with patch.object(agent_manager, '_check_agent_health', return_value=False):
            result = await agent_manager._wait_for_health("market_data", timeout=1)

        assert result is False

    @pytest.mark.asyncio
    async def test_monitoring_lifecycle(self, agent_manager):
        """Test monitoring start and stop."""
        # Start monitoring
        await agent_manager.start_monitoring(interval=1)
        assert agent_manager._monitoring_active is True
        assert agent_manager._monitoring_task is not None

        # Stop monitoring
        await agent_manager.stop_monitoring()
        assert agent_manager._monitoring_active is False

    @pytest.mark.asyncio
    async def test_cleanup(self, agent_manager):
        """Test agent manager cleanup."""
        # Start monitoring
        await agent_manager.start_monitoring()

        # Set up a running agent
        agent_manager.agents["market_data"].status = AgentStatus.RUNNING

        with patch.object(agent_manager, 'stop_all_agents', return_value={"market_data": True}) as mock_stop:
            await agent_manager.cleanup()

        mock_stop.assert_called_once()
        assert not agent_manager._monitoring_active

    @pytest.mark.asyncio
    async def test_unknown_agent_operations(self, agent_manager):
        """Test operations on unknown agents."""
        result1 = await agent_manager.start_agent("unknown_agent")
        result2 = await agent_manager.stop_agent("unknown_agent")
        result3 = await agent_manager.get_agent_status("unknown_agent")

        assert result1 is False
        assert result2 is False
        assert result3 is None


class TestAgentManagerIntegration:
    """Integration tests for AgentManager with real configuration."""

    def test_agent_manager_singleton(self):
        """Test that get_agent_manager returns singleton instance."""
        from src.orchestrator.agent_manager import get_agent_manager

        with patch('src.orchestrator.agent_manager.get_config_manager'):
            with patch('src.orchestrator.agent_manager.get_logger'):
                manager1 = get_agent_manager()
                manager2 = get_agent_manager()

                assert manager1 is manager2


if __name__ == "__main__":
    pytest.main([__file__])