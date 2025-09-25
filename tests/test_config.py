"""
Test suite for configuration management system.

Tests configuration loading, validation, environment overrides,
and error handling.
"""

import pytest
import os
import tempfile
import yaml
from pathlib import Path
from unittest.mock import patch, mock_open

from src.utils.config import ConfigurationManager, DashboardConfig, AgentConfig, LoggingConfig


class TestConfigurationManager:
    """Test cases for ConfigurationManager."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create temporary config directory
        self.temp_dir = tempfile.mkdtemp()
        self.config_dir = Path(self.temp_dir)
        self.env_dir = self.config_dir / "environments"
        self.env_dir.mkdir(exist_ok=True)

        # Sample configuration data
        self.sample_config = {
            "dashboard": {
                "title": "Test Dashboard",
                "port": 3000,
                "debug": False,
                "refresh_interval": 5
            },
            "agents": {
                "market_data": {
                    "name": "Market Data Agent",
                    "url": "http://localhost:8000",
                    "timeout": 10,
                    "enabled": True
                }
            },
            "logging": {
                "level": "INFO",
                "console_output": True
            }
        }

        # Create main config file
        with open(self.config_dir / "dashboard.yaml", 'w') as f:
            yaml.dump(self.sample_config, f)

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_basic_config_loading(self):
        """Test basic configuration loading."""
        config_manager = ConfigurationManager(config_dir=str(self.config_dir), environment="development")

        # Test dashboard config
        dashboard_config = config_manager.get_dashboard_config()
        assert dashboard_config.title == "Test Dashboard"
        assert dashboard_config.port == 3000
        assert dashboard_config.debug is False

        # Test agent config
        agent_config = config_manager.get_agent_config("market_data")
        assert agent_config is not None
        assert agent_config.name == "Market Data Agent"
        assert agent_config.url == "http://localhost:8000"
        assert agent_config.enabled is True

    def test_environment_override(self):
        """Test environment-specific configuration overrides."""
        # Create development environment config
        dev_config = {
            "dashboard": {
                "debug": True,
                "refresh_interval": 2
            },
            "agents": {
                "market_data": {
                    "timeout": 5
                }
            }
        }

        with open(self.env_dir / "development.yaml", 'w') as f:
            yaml.dump(dev_config, f)

        config_manager = ConfigurationManager(config_dir=str(self.config_dir), environment="development")

        # Test that overrides were applied
        dashboard_config = config_manager.get_dashboard_config()
        assert dashboard_config.debug is True  # Overridden
        assert dashboard_config.refresh_interval == 2  # Overridden
        assert dashboard_config.title == "Test Dashboard"  # Not overridden

        agent_config = config_manager.get_agent_config("market_data")
        assert agent_config.timeout == 5  # Overridden

    @patch.dict(os.environ, {
        "DASHBOARD_PORT": "8080",
        "DASHBOARD_DEBUG": "true",
        "MARKET_DATA_URL": "http://remote:9000"
    })
    def test_environment_variable_override(self):
        """Test environment variable overrides."""
        config_manager = ConfigurationManager(config_dir=str(self.config_dir), environment="development")

        # Test environment variable overrides
        dashboard_config = config_manager.get_dashboard_config()
        assert dashboard_config.port == 8080  # From env var
        assert dashboard_config.debug is True  # From env var

        agent_config = config_manager.get_agent_config("market_data")
        assert agent_config.url == "http://remote:9000"  # From env var

    def test_environment_detection(self):
        """Test automatic environment detection."""
        with patch.dict(os.environ, {"TRADING_DASHBOARD_ENV": "production"}):
            config_manager = ConfigurationManager(config_dir=str(self.config_dir))
            assert config_manager.get_environment() == "production"

        with patch.dict(os.environ, {}, clear=True):
            config_manager = ConfigurationManager(config_dir=str(self.config_dir))
            assert config_manager.get_environment() == "development"

    def test_config_validation(self):
        """Test configuration validation."""
        config_manager = ConfigurationManager(config_dir=str(self.config_dir), environment="development")

        # Valid configuration should pass
        assert config_manager.validate_configuration() is True

        # Test invalid port
        config_manager.config["dashboard"]["port"] = -1
        assert config_manager.validate_configuration() is False

        # Test invalid logging level
        config_manager.config["logging"]["level"] = "INVALID"
        assert config_manager.validate_configuration() is False

    def test_get_config_value_dot_notation(self):
        """Test getting configuration values with dot notation."""
        config_manager = ConfigurationManager(config_dir=str(self.config_dir), environment="development")

        assert config_manager.get_config_value("dashboard.title") == "Test Dashboard"
        assert config_manager.get_config_value("agents.market_data.url") == "http://localhost:8000"
        assert config_manager.get_config_value("nonexistent.key", "default") == "default"

    def test_missing_agent_config(self):
        """Test handling of missing agent configuration."""
        config_manager = ConfigurationManager(config_dir=str(self.config_dir), environment="development")

        agent_config = config_manager.get_agent_config("nonexistent_agent")
        assert agent_config is None

    def test_logging_config(self):
        """Test logging configuration."""
        config_manager = ConfigurationManager(config_dir=str(self.config_dir), environment="development")

        logging_config = config_manager.get_logging_config()
        assert logging_config.level == "INFO"
        assert logging_config.console_output is True

    def test_all_agent_configs(self):
        """Test getting all agent configurations."""
        config_manager = ConfigurationManager(config_dir=str(self.config_dir), environment="development")

        all_configs = config_manager.get_all_agent_configs()
        assert "market_data" in all_configs
        assert isinstance(all_configs["market_data"], AgentConfig)

    def test_missing_config_file_handling(self):
        """Test handling of missing configuration files."""
        empty_dir = tempfile.mkdtemp()

        try:
            # Should handle missing config gracefully (not raise exception)
            config_manager = ConfigurationManager(config_dir=empty_dir, environment="development")

            # Should have empty config
            assert config_manager.config == {}

            # Should still provide defaults for dashboard config
            dashboard_config = config_manager.get_dashboard_config()
            assert dashboard_config.title == "Trading Dashboard"  # Default value

        finally:
            import shutil
            shutil.rmtree(empty_dir, ignore_errors=True)


def test_dataclass_creation():
    """Test dataclass creation and defaults."""
    # Test DashboardConfig
    dashboard_config = DashboardConfig(
        title="Test",
        subtitle="Test Sub",
        port=3000,
        host="localhost",
        debug=False,
        refresh_interval=5
    )

    assert dashboard_config.title == "Test"
    assert dashboard_config.port == 3000

    # Test AgentConfig
    agent_config = AgentConfig(
        name="Test Agent",
        url="http://localhost:8000",
        timeout=10,
        health_check_interval=30,
        max_retries=3,
        enabled=True
    )

    assert agent_config.name == "Test Agent"
    assert agent_config.enabled is True

    # Test LoggingConfig
    logging_config = LoggingConfig(
        level="INFO",
        format="%(message)s",
        file_path="test.log",
        max_file_size="10MB",
        backup_count=5,
        console_output=True
    )

    assert logging_config.level == "INFO"
    assert logging_config.console_output is True


if __name__ == "__main__":
    pytest.main([__file__])