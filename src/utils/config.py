"""
Configuration management utilities for Trading Dashboard.

This module provides comprehensive configuration loading and management
with support for YAML files, environment variables, and multi-environment
configurations.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)


@dataclass
class DashboardConfig:
    """Dashboard configuration dataclass."""
    title: str
    subtitle: str
    port: int
    host: str
    debug: bool
    refresh_interval: int


@dataclass
class AgentConfig:
    """Agent configuration dataclass."""
    name: str
    url: str
    timeout: int
    health_check_interval: int
    max_retries: int
    enabled: bool


@dataclass
class LoggingConfig:
    """Logging configuration dataclass."""
    level: str
    format: str
    file_path: str
    max_file_size: str
    backup_count: int
    console_output: bool


class ConfigurationManager:
    """
    Manages configuration loading and validation for the Trading Dashboard.

    Supports:
    - YAML configuration files
    - Environment-specific overrides
    - Environment variable substitution
    - Configuration validation
    """

    def __init__(self, config_dir: Optional[str] = None, environment: Optional[str] = None):
        """
        Initialize configuration manager.

        Args:
            config_dir: Path to configuration directory
            environment: Environment name (development, staging, production)
        """
        self.config_dir = Path(config_dir) if config_dir else self._get_default_config_dir()
        self.environment = environment or self._detect_environment()
        self.config: Dict[str, Any] = {}

        # Load environment variables
        load_dotenv()

        # Load configurations
        self._load_configurations()

    def _get_default_config_dir(self) -> Path:
        """Get default configuration directory."""
        # Assume config dir is relative to project root
        project_root = Path(__file__).parent.parent.parent
        return project_root / "config"

    def _detect_environment(self) -> str:
        """Detect current environment from environment variables."""
        env = os.getenv("TRADING_DASHBOARD_ENV", "development").lower()
        valid_envs = ["development", "staging", "production"]

        if env not in valid_envs:
            logger.warning(f"Unknown environment '{env}', defaulting to 'development'")
            return "development"

        return env

    def _load_configurations(self) -> None:
        """Load all configuration files."""
        try:
            # Load main configuration
            main_config_path = self.config_dir / "dashboard.yaml"
            if main_config_path.exists():
                with open(main_config_path, 'r', encoding='utf-8') as f:
                    self.config = yaml.safe_load(f)
                logger.info(f"Loaded main configuration from {main_config_path}")
            else:
                logger.error(f"Main configuration file not found: {main_config_path}")
                self.config = {}

            # Load environment-specific overrides
            env_config_path = self.config_dir / "environments" / f"{self.environment}.yaml"
            if env_config_path.exists():
                with open(env_config_path, 'r', encoding='utf-8') as f:
                    env_config = yaml.safe_load(f)
                    self._merge_configs(self.config, env_config)
                logger.info(f"Loaded environment configuration from {env_config_path}")

            # Apply environment variable overrides
            self._apply_env_overrides()

        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            raise

    def _merge_configs(self, base_config: Dict[str, Any], override_config: Dict[str, Any]) -> None:
        """
        Recursively merge configuration dictionaries.

        Args:
            base_config: Base configuration dictionary
            override_config: Override configuration dictionary
        """
        for key, value in override_config.items():
            if key in base_config and isinstance(base_config[key], dict) and isinstance(value, dict):
                self._merge_configs(base_config[key], value)
            else:
                base_config[key] = value

    def _apply_env_overrides(self) -> None:
        """Apply environment variable overrides."""
        # Dashboard port
        if os.getenv("DASHBOARD_PORT"):
            self.config.setdefault("dashboard", {})["port"] = int(os.getenv("DASHBOARD_PORT"))

        # Dashboard debug mode
        if os.getenv("DASHBOARD_DEBUG"):
            self.config.setdefault("dashboard", {})["debug"] = os.getenv("DASHBOARD_DEBUG").lower() == "true"

        # Agent URLs
        for agent_name in ["market_data", "pattern_recognition", "risk_management", "advisor", "backtest"]:
            env_var = f"{agent_name.upper()}_URL"
            if os.getenv(env_var):
                self.config.setdefault("agents", {}).setdefault(agent_name, {})["url"] = os.getenv(env_var)

    def get_dashboard_config(self) -> DashboardConfig:
        """Get dashboard configuration."""
        dashboard_config = self.config.get("dashboard", {})

        return DashboardConfig(
            title=dashboard_config.get("title", "Trading Dashboard"),
            subtitle=dashboard_config.get("subtitle", "Central Control for Autonomous Trading System"),
            port=dashboard_config.get("port", 3000),
            host=dashboard_config.get("host", "localhost"),
            debug=dashboard_config.get("debug", False),
            refresh_interval=dashboard_config.get("refresh_interval", 5)
        )

    def get_agent_config(self, agent_name: str) -> Optional[AgentConfig]:
        """Get configuration for a specific agent."""
        agents_config = self.config.get("agents", {})
        agent_config = agents_config.get(agent_name)

        if not agent_config:
            logger.warning(f"No configuration found for agent: {agent_name}")
            return None

        return AgentConfig(
            name=agent_config.get("name", agent_name.replace("_", " ").title()),
            url=agent_config.get("url", f"http://localhost:8000"),
            timeout=agent_config.get("timeout", 10),
            health_check_interval=agent_config.get("health_check_interval", 30),
            max_retries=agent_config.get("max_retries", 3),
            enabled=agent_config.get("enabled", False)
        )

    def get_all_agent_configs(self) -> Dict[str, AgentConfig]:
        """Get all agent configurations."""
        agents_config = self.config.get("agents", {})
        result = {}

        for agent_name in agents_config.keys():
            agent_config = self.get_agent_config(agent_name)
            if agent_config:
                result[agent_name] = agent_config

        return result

    def get_logging_config(self) -> LoggingConfig:
        """Get logging configuration."""
        logging_config = self.config.get("logging", {})

        return LoggingConfig(
            level=logging_config.get("level", "INFO"),
            format=logging_config.get("format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"),
            file_path=logging_config.get("file_path", "logs/dashboard.log"),
            max_file_size=logging_config.get("max_file_size", "10MB"),
            backup_count=logging_config.get("backup_count", 5),
            console_output=logging_config.get("console_output", True)
        )

    def get_config_value(self, key_path: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation.

        Args:
            key_path: Configuration key path (e.g., "dashboard.port")
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        keys = key_path.split(".")
        value = self.config

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default

        return value

    def validate_configuration(self) -> bool:
        """
        Validate configuration completeness and correctness.

        Returns:
            True if configuration is valid, False otherwise
        """
        try:
            # Validate dashboard config
            dashboard_config = self.get_dashboard_config()
            if dashboard_config.port <= 0 or dashboard_config.port > 65535:
                logger.error(f"Invalid dashboard port: {dashboard_config.port}")
                return False

            # Validate agent configs
            agent_configs = self.get_all_agent_configs()
            for agent_name, agent_config in agent_configs.items():
                if not agent_config.url:
                    logger.error(f"Missing URL for agent: {agent_name}")
                    return False

                if agent_config.timeout <= 0:
                    logger.error(f"Invalid timeout for agent {agent_name}: {agent_config.timeout}")
                    return False

            # Validate logging config
            logging_config = self.get_logging_config()
            valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
            if logging_config.level not in valid_levels:
                logger.error(f"Invalid logging level: {logging_config.level}")
                return False

            logger.info("Configuration validation passed")
            return True

        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            return False

    def reload_configuration(self) -> None:
        """Reload configuration from files."""
        logger.info("Reloading configuration...")
        self._load_configurations()

    def get_environment(self) -> str:
        """Get current environment."""
        return self.environment


# Global configuration manager instance
config_manager: Optional[ConfigurationManager] = None


def get_config_manager() -> ConfigurationManager:
    """Get global configuration manager instance."""
    global config_manager

    if config_manager is None:
        config_manager = ConfigurationManager()

    return config_manager


def reload_config() -> None:
    """Reload global configuration."""
    global config_manager

    if config_manager is not None:
        config_manager.reload_configuration()