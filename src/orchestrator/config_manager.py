"""
Dynamic Configuration Manager for Trading Dashboard

This module provides dynamic configuration management with real-time updates,
validation, backup/restore, and agent-specific configuration handling.
"""

import os
import yaml
import json
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable, Union
from dataclasses import dataclass, asdict, field
from datetime import datetime
from enum import Enum
import asyncio
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import logging

from ..utils.logging import get_logger
from ..utils.config import get_config_manager


class ConfigChangeType(Enum):
    """Types of configuration changes."""
    CREATED = "created"
    MODIFIED = "modified"
    DELETED = "deleted"
    RELOADED = "reloaded"
    VALIDATED = "validated"
    RESTORED = "restored"


@dataclass
class ConfigChange:
    """Configuration change tracking."""
    timestamp: float
    change_type: ConfigChangeType
    config_section: str
    old_value: Any = None
    new_value: Any = None
    user: Optional[str] = None
    message: Optional[str] = None


@dataclass
class ConfigTemplate:
    """Configuration template definition."""
    name: str
    description: str
    template_data: Dict[str, Any]
    variables: Dict[str, str] = field(default_factory=dict)
    required_fields: List[str] = field(default_factory=list)


@dataclass
class ConfigVersion:
    """Configuration version tracking."""
    version: str
    timestamp: float
    config_data: Dict[str, Any]
    changes: List[str] = field(default_factory=list)
    author: Optional[str] = None


class ConfigFileWatcher(FileSystemEventHandler):
    """File system watcher for configuration changes."""

    def __init__(self, config_manager: 'DynamicConfigManager'):
        self.config_manager = config_manager
        self.logger = get_logger(__name__)

    def on_modified(self, event):
        """Handle file modification events."""
        if not event.is_directory and event.src_path.endswith(('.yaml', '.yml')):
            self.logger.info(f"Configuration file modified: {event.src_path}")
            # Debounce file changes (avoid multiple rapid events)
            asyncio.create_task(self.config_manager._handle_file_change(event.src_path))


class DynamicConfigManager:
    """Dynamic configuration manager with real-time updates and validation."""

    def __init__(self, config_root: Optional[Path] = None):
        self.logger = get_logger(__name__)
        self.config_root = config_root or Path("config")
        self.backup_dir = self.config_root / "backups"
        self.templates_dir = self.config_root / "templates"

        # Configuration state
        self.current_config: Dict[str, Any] = {}
        self.config_history: List[ConfigChange] = []
        self.config_versions: List[ConfigVersion] = []
        self.templates: Dict[str, ConfigTemplate] = {}
        self.change_callbacks: List[Callable] = []

        # File watching
        self.observer: Optional[Observer] = None
        self.watcher: Optional[ConfigFileWatcher] = None

        # Thread safety
        self.config_lock = threading.RLock()

        # Initialize
        self._setup_directories()
        self._load_templates()
        self._create_initial_version()

    def _setup_directories(self):
        """Setup configuration directories."""
        self.config_root.mkdir(exist_ok=True)
        self.backup_dir.mkdir(exist_ok=True)
        self.templates_dir.mkdir(exist_ok=True)

        # Create default templates if they don't exist
        self._create_default_templates()

    def _create_default_templates(self):
        """Create default configuration templates."""
        agent_template = {
            "name": "{{agent_name}}",
            "url": "http://localhost:{{port}}/{{endpoint}}",
            "timeout": 30,
            "health_check_interval": 60,
            "max_retries": 3,
            "enabled": "{{enabled}}",
            "dependencies": "{{dependencies}}",
            "priority": "{{priority}}"
        }

        template_file = self.templates_dir / "agent_template.yaml"
        if not template_file.exists():
            with open(template_file, 'w') as f:
                yaml.dump({"agent_template": agent_template}, f)

    def _load_templates(self):
        """Load configuration templates."""
        for template_file in self.templates_dir.glob("*.yaml"):
            try:
                with open(template_file, 'r') as f:
                    template_data = yaml.safe_load(f)

                for template_name, template_config in template_data.items():
                    self.templates[template_name] = ConfigTemplate(
                        name=template_name,
                        description=template_config.get('description', f'Template for {template_name}'),
                        template_data=template_config,
                        variables=template_config.get('variables', {}),
                        required_fields=template_config.get('required_fields', [])
                    )

                self.logger.info(f"Loaded configuration templates from {template_file}")

            except Exception as e:
                self.logger.error(f"Failed to load template {template_file}: {e}")

    def _create_initial_version(self):
        """Create initial configuration version."""
        try:
            base_config_manager = get_config_manager()
            self.current_config = {
                "dashboard": asdict(base_config_manager.get_dashboard_config()),
                "agents": {name: asdict(config) for name, config in base_config_manager.get_all_agent_configs().items()},
                "logging": asdict(base_config_manager.get_logging_config())
            }

            # Create initial version
            version = ConfigVersion(
                version="1.0.0",
                timestamp=datetime.now().timestamp(),
                config_data=self.current_config.copy(),
                changes=["Initial configuration version"],
                author="System"
            )
            self.config_versions.append(version)

        except Exception as e:
            self.logger.error(f"Failed to create initial configuration version: {e}")
            self.current_config = {}

    async def start_watching(self):
        """Start watching configuration files for changes."""
        if self.observer is not None:
            return

        try:
            self.watcher = ConfigFileWatcher(self)
            self.observer = Observer()
            self.observer.schedule(self.watcher, str(self.config_root), recursive=True)
            self.observer.start()

            self.logger.info(f"Started watching configuration directory: {self.config_root}")

        except Exception as e:
            self.logger.error(f"Failed to start configuration watching: {e}")

    async def stop_watching(self):
        """Stop watching configuration files."""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.observer = None
            self.watcher = None

            self.logger.info("Stopped watching configuration files")

    async def _handle_file_change(self, file_path: str):
        """Handle configuration file changes."""
        # Debounce rapid changes
        await asyncio.sleep(0.5)

        try:
            await self.reload_configuration()

            change = ConfigChange(
                timestamp=datetime.now().timestamp(),
                change_type=ConfigChangeType.RELOADED,
                config_section="file_system",
                message=f"Configuration reloaded due to file change: {file_path}"
            )

            self.config_history.append(change)
            await self._notify_change_callbacks(change)

        except Exception as e:
            self.logger.error(f"Failed to handle configuration file change: {e}")

    async def reload_configuration(self) -> bool:
        """Reload configuration from files."""
        with self.config_lock:
            try:
                # Create backup of current config
                await self.create_backup(f"pre_reload_{datetime.now().strftime('%Y%m%d_%H%M%S')}")

                # Reload from base config manager
                base_config_manager = get_config_manager()
                base_config_manager.reload()

                new_config = {
                    "dashboard": asdict(base_config_manager.get_dashboard_config()),
                    "agents": {name: asdict(config) for name, config in base_config_manager.get_all_agent_configs().items()},
                    "logging": asdict(base_config_manager.get_logging_config())
                }

                # Validate new configuration
                validation_result = await self.validate_configuration(new_config)
                if not validation_result["valid"]:
                    self.logger.error(f"Configuration validation failed: {validation_result['errors']}")
                    return False

                # Update configuration
                old_config = self.current_config.copy()
                self.current_config = new_config

                # Create new version
                version = ConfigVersion(
                    version=self._generate_version(),
                    timestamp=datetime.now().timestamp(),
                    config_data=new_config.copy(),
                    changes=self._detect_changes(old_config, new_config),
                    author="System"
                )
                self.config_versions.append(version)

                self.logger.info("Configuration reloaded successfully")
                return True

            except Exception as e:
                self.logger.error(f"Failed to reload configuration: {e}")
                return False

    async def validate_configuration(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate configuration data."""
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": []
        }

        try:
            # Validate dashboard configuration
            if "dashboard" in config:
                dashboard_config = config["dashboard"]
                required_fields = ["title", "port", "host"]
                for field in required_fields:
                    if field not in dashboard_config:
                        validation_result["errors"].append(f"Missing required dashboard field: {field}")
                        validation_result["valid"] = False

            # Validate agent configurations
            if "agents" in config:
                for agent_name, agent_config in config["agents"].items():
                    required_fields = ["name", "url", "enabled"]
                    for field in required_fields:
                        if field not in agent_config:
                            validation_result["errors"].append(f"Missing required field '{field}' in agent '{agent_name}'")
                            validation_result["valid"] = False

                    # Validate URL format
                    if "url" in agent_config and not agent_config["url"].startswith(("http://", "https://")):
                        validation_result["warnings"].append(f"Agent '{agent_name}' URL should start with http:// or https://")

                    # Validate port numbers
                    if "url" in agent_config and "localhost:" in agent_config["url"]:
                        try:
                            port_part = agent_config["url"].split("localhost:")[1].split("/")[0]
                            port = int(port_part)
                            if port < 1024 or port > 65535:
                                validation_result["warnings"].append(f"Agent '{agent_name}' port {port} may be invalid")
                        except (ValueError, IndexError):
                            pass

            # Validate logging configuration
            if "logging" in config:
                logging_config = config["logging"]
                valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
                if "level" in logging_config and logging_config["level"] not in valid_levels:
                    validation_result["errors"].append(f"Invalid logging level: {logging_config['level']}")
                    validation_result["valid"] = False

            # Record validation
            change = ConfigChange(
                timestamp=datetime.now().timestamp(),
                change_type=ConfigChangeType.VALIDATED,
                config_section="validation",
                message=f"Configuration validation: {'passed' if validation_result['valid'] else 'failed'}"
            )
            self.config_history.append(change)

        except Exception as e:
            validation_result["valid"] = False
            validation_result["errors"].append(f"Validation error: {str(e)}")
            self.logger.error(f"Configuration validation failed: {e}")

        return validation_result

    async def update_agent_configuration(self, agent_name: str, config_updates: Dict[str, Any]) -> bool:
        """Update specific agent configuration."""
        with self.config_lock:
            try:
                if "agents" not in self.current_config:
                    self.current_config["agents"] = {}

                old_config = self.current_config["agents"].get(agent_name, {}).copy()

                # Update agent configuration
                if agent_name not in self.current_config["agents"]:
                    self.current_config["agents"][agent_name] = {}

                self.current_config["agents"][agent_name].update(config_updates)

                # Validate updated configuration
                validation_result = await self.validate_configuration(self.current_config)
                if not validation_result["valid"]:
                    # Rollback on validation failure
                    self.current_config["agents"][agent_name] = old_config
                    self.logger.error(f"Agent configuration update failed validation: {validation_result['errors']}")
                    return False

                # Record change
                change = ConfigChange(
                    timestamp=datetime.now().timestamp(),
                    change_type=ConfigChangeType.MODIFIED,
                    config_section=f"agents.{agent_name}",
                    old_value=old_config,
                    new_value=self.current_config["agents"][agent_name].copy(),
                    message=f"Updated configuration for agent {agent_name}"
                )

                self.config_history.append(change)
                await self._notify_change_callbacks(change)

                # Save to file
                await self.save_configuration()

                self.logger.info(f"Updated configuration for agent {agent_name}")
                return True

            except Exception as e:
                self.logger.error(f"Failed to update agent configuration: {e}")
                return False

    async def create_backup(self, backup_name: Optional[str] = None) -> str:
        """Create configuration backup."""
        if backup_name is None:
            backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        backup_path = self.backup_dir / f"{backup_name}.json"

        try:
            backup_data = {
                "timestamp": datetime.now().timestamp(),
                "version": self._get_current_version(),
                "config": self.current_config,
                "history": [asdict(change) for change in self.config_history[-10:]]  # Last 10 changes
            }

            with open(backup_path, 'w') as f:
                json.dump(backup_data, f, indent=2, default=str)

            self.logger.info(f"Configuration backup created: {backup_path}")
            return str(backup_path)

        except Exception as e:
            self.logger.error(f"Failed to create configuration backup: {e}")
            raise

    async def restore_backup(self, backup_path: str) -> bool:
        """Restore configuration from backup."""
        with self.config_lock:
            try:
                with open(backup_path, 'r') as f:
                    backup_data = json.load(f)

                # Validate backup data
                if "config" not in backup_data:
                    raise ValueError("Invalid backup file: missing config data")

                backup_config = backup_data["config"]
                validation_result = await self.validate_configuration(backup_config)

                if not validation_result["valid"]:
                    self.logger.error(f"Backup validation failed: {validation_result['errors']}")
                    return False

                # Create backup of current state before restore
                await self.create_backup("pre_restore")

                # Restore configuration
                old_config = self.current_config.copy()
                self.current_config = backup_config

                # Record restore
                change = ConfigChange(
                    timestamp=datetime.now().timestamp(),
                    change_type=ConfigChangeType.RESTORED,
                    config_section="system",
                    old_value=old_config,
                    new_value=backup_config,
                    message=f"Configuration restored from {backup_path}"
                )

                self.config_history.append(change)
                await self._notify_change_callbacks(change)

                # Save restored configuration
                await self.save_configuration()

                self.logger.info(f"Configuration restored from {backup_path}")
                return True

            except Exception as e:
                self.logger.error(f"Failed to restore configuration backup: {e}")
                return False

    async def save_configuration(self):
        """Save current configuration to files."""
        try:
            # Save main dashboard configuration
            dashboard_config_path = self.config_root / "dashboard.yaml"

            save_config = {
                "dashboard": self.current_config.get("dashboard", {}),
                "agents": self.current_config.get("agents", {}),
                "logging": self.current_config.get("logging", {})
            }

            with open(dashboard_config_path, 'w') as f:
                yaml.dump(save_config, f, default_flow_style=False, indent=2)

            self.logger.info(f"Configuration saved to {dashboard_config_path}")

        except Exception as e:
            self.logger.error(f"Failed to save configuration: {e}")
            raise

    def get_current_configuration(self) -> Dict[str, Any]:
        """Get current configuration."""
        with self.config_lock:
            return self.current_config.copy()

    def get_agent_configuration(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """Get configuration for specific agent."""
        with self.config_lock:
            return self.current_config.get("agents", {}).get(agent_name)

    def get_configuration_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get configuration change history."""
        return [asdict(change) for change in self.config_history[-limit:]]

    def get_available_templates(self) -> Dict[str, ConfigTemplate]:
        """Get available configuration templates."""
        return self.templates.copy()

    def get_configuration_versions(self) -> List[Dict[str, Any]]:
        """Get configuration version history."""
        return [asdict(version) for version in self.config_versions]

    def register_change_callback(self, callback: Callable):
        """Register callback for configuration changes."""
        self.change_callbacks.append(callback)

    def get_configuration_diff(self, version1: str, version2: str) -> Dict[str, Any]:
        """Get differences between two configuration versions."""
        v1_config = None
        v2_config = None

        for version in self.config_versions:
            if version.version == version1:
                v1_config = version.config_data
            if version.version == version2:
                v2_config = version.config_data

        if v1_config is None or v2_config is None:
            return {"error": "One or both versions not found"}

        return self._calculate_diff(v1_config, v2_config)

    async def _notify_change_callbacks(self, change: ConfigChange):
        """Notify registered callbacks of configuration changes."""
        for callback in self.change_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(change)
                else:
                    callback(change)
            except Exception as e:
                self.logger.error(f"Error in configuration change callback: {e}")

    def _generate_version(self) -> str:
        """Generate next version number."""
        if not self.config_versions:
            return "1.0.0"

        latest_version = self.config_versions[-1].version
        try:
            parts = latest_version.split(".")
            major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])
            return f"{major}.{minor}.{patch + 1}"
        except (ValueError, IndexError):
            return f"1.0.{len(self.config_versions)}"

    def _get_current_version(self) -> str:
        """Get current configuration version."""
        if self.config_versions:
            return self.config_versions[-1].version
        return "1.0.0"

    def _detect_changes(self, old_config: Dict[str, Any], new_config: Dict[str, Any]) -> List[str]:
        """Detect changes between configurations."""
        changes = []

        # Simple change detection (could be enhanced)
        for section in ["dashboard", "agents", "logging"]:
            if old_config.get(section) != new_config.get(section):
                changes.append(f"Modified {section} configuration")

        return changes if changes else ["Configuration updated"]

    def _calculate_diff(self, config1: Dict[str, Any], config2: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate differences between two configurations."""
        diff = {
            "added": {},
            "modified": {},
            "removed": {}
        }

        # Simple diff calculation (could be enhanced with deep diff)
        all_keys = set(config1.keys()) | set(config2.keys())

        for key in all_keys:
            if key not in config1:
                diff["added"][key] = config2[key]
            elif key not in config2:
                diff["removed"][key] = config1[key]
            elif config1[key] != config2[key]:
                diff["modified"][key] = {
                    "old": config1[key],
                    "new": config2[key]
                }

        return diff

    async def cleanup(self):
        """Cleanup configuration manager resources."""
        await self.stop_watching()
        self.logger.info("Configuration manager cleanup completed")


# Global configuration manager instance
_config_manager_instance: Optional[DynamicConfigManager] = None


def get_dynamic_config_manager() -> DynamicConfigManager:
    """Get global dynamic configuration manager instance."""
    global _config_manager_instance
    if _config_manager_instance is None:
        _config_manager_instance = DynamicConfigManager()
    return _config_manager_instance