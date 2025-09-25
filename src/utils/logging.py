"""
Logging utilities for Trading Dashboard.

This module provides comprehensive logging capabilities including structured output,
file rotation, multiple handlers, and integration with the configuration system.
"""

import logging
import logging.handlers
import json
import sys
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Union
import traceback

# Import configuration management
from .config import get_config_manager


class StructuredFormatter(logging.Formatter):
    """
    Custom formatter that outputs structured JSON logs.

    Provides both human-readable and machine-parseable log output
    with structured fields for better log analysis.
    """

    def __init__(self, include_extra: bool = True):
        """
        Initialize structured formatter.

        Args:
            include_extra: Whether to include extra fields in log output
        """
        super().__init__()
        self.include_extra = include_extra

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as structured JSON.

        Args:
            record: Log record to format

        Returns:
            Formatted log message as JSON string
        """
        # Base log structure
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }

        # Add process and thread info
        log_entry["process_id"] = record.process
        log_entry["thread_id"] = record.thread

        # Add exception information if present
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": traceback.format_exception(*record.exc_info)
            }

        # Add extra fields if enabled
        if self.include_extra:
            for key, value in record.__dict__.items():
                if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                              'filename', 'module', 'exc_info', 'exc_text', 'stack_info',
                              'lineno', 'funcName', 'created', 'msecs', 'relativeCreated',
                              'thread', 'threadName', 'processName', 'process', 'message']:
                    log_entry[f"extra_{key}"] = value

        return json.dumps(log_entry, default=str, ensure_ascii=False)


class ColoredFormatter(logging.Formatter):
    """
    Custom formatter that adds colors to console output.

    Provides colored output for different log levels to improve readability
    in terminal/console environments.
    """

    # Color codes for different log levels
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m'   # Magenta
    }

    RESET = '\033[0m'  # Reset color

    def __init__(self, use_colors: bool = True):
        """
        Initialize colored formatter.

        Args:
            use_colors: Whether to use colors in output
        """
        super().__init__()
        self.use_colors = use_colors and sys.stderr.isatty()

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record with colors.

        Args:
            record: Log record to format

        Returns:
            Formatted log message with color codes
        """
        # Format the basic message
        formatted = super().format(record)

        if self.use_colors:
            color = self.COLORS.get(record.levelname, '')
            if color:
                # Add color to level name
                formatted = formatted.replace(
                    record.levelname,
                    f"{color}{record.levelname}{self.RESET}"
                )

        return formatted


class TradingDashboardLogger:
    """
    Main logging class for Trading Dashboard.

    Provides centralized logging configuration with support for multiple handlers,
    structured output, file rotation, and integration with configuration system.
    """

    def __init__(self, name: str = "trading_dashboard"):
        """
        Initialize trading dashboard logger.

        Args:
            name: Logger name
        """
        self.name = name
        self.logger = logging.getLogger(name)
        self.handlers: Dict[str, logging.Handler] = {}
        self.configured = False

    def configure(self, force_reconfigure: bool = False) -> None:
        """
        Configure logger based on configuration system.

        Args:
            force_reconfigure: Whether to force reconfiguration even if already configured
        """
        if self.configured and not force_reconfigure:
            return

        try:
            # Get configuration
            config_manager = get_config_manager()
            logging_config = config_manager.get_logging_config()

            # Clear existing handlers if reconfiguring
            if force_reconfigure:
                self.logger.handlers.clear()
                self.handlers.clear()

            # Set log level
            level = getattr(logging, logging_config.level.upper(), logging.INFO)
            self.logger.setLevel(level)

            # Create logs directory if it doesn't exist
            log_file_path = Path(logging_config.file_path)
            log_file_path.parent.mkdir(parents=True, exist_ok=True)

            # Configure file handler with rotation
            self._configure_file_handler(logging_config)

            # Configure console handler if enabled
            if logging_config.console_output:
                self._configure_console_handler()

            # Configure structured JSON handler
            self._configure_json_handler(logging_config)

            self.configured = True
            self.logger.info("Logging system configured successfully",
                           extra={"log_level": logging_config.level,
                                 "file_path": logging_config.file_path,
                                 "console_output": logging_config.console_output})

        except Exception as e:
            # Fallback to basic configuration if config fails
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            self.logger.error(f"Failed to configure logging: {e}")

    def _configure_file_handler(self, config) -> None:
        """Configure rotating file handler."""
        try:
            # Parse max file size
            max_bytes = self._parse_file_size(config.max_file_size)

            # Create rotating file handler
            file_handler = logging.handlers.RotatingFileHandler(
                filename=config.file_path,
                maxBytes=max_bytes,
                backupCount=config.backup_count,
                encoding='utf-8'
            )

            # Set formatter
            file_formatter = logging.Formatter(
                fmt=config.format,
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(file_formatter)

            self.logger.addHandler(file_handler)
            self.handlers['file'] = file_handler

        except Exception as e:
            self.logger.error(f"Failed to configure file handler: {e}")

    def _configure_console_handler(self) -> None:
        """Configure console handler with colors."""
        try:
            console_handler = logging.StreamHandler(sys.stdout)

            # Use colored formatter for console
            console_formatter = ColoredFormatter()
            console_formatter._style._fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            console_handler.setFormatter(console_formatter)

            self.logger.addHandler(console_handler)
            self.handlers['console'] = console_handler

        except Exception as e:
            self.logger.error(f"Failed to configure console handler: {e}")

    def _configure_json_handler(self, config) -> None:
        """Configure structured JSON handler."""
        try:
            # Create JSON log file path
            json_log_path = Path(config.file_path).with_suffix('.json')

            json_handler = logging.handlers.RotatingFileHandler(
                filename=str(json_log_path),
                maxBytes=self._parse_file_size(config.max_file_size),
                backupCount=config.backup_count,
                encoding='utf-8'
            )

            # Use structured formatter
            json_formatter = StructuredFormatter()
            json_handler.setFormatter(json_formatter)

            self.logger.addHandler(json_handler)
            self.handlers['json'] = json_handler

        except Exception as e:
            self.logger.error(f"Failed to configure JSON handler: {e}")

    def _parse_file_size(self, size_str: str) -> int:
        """
        Parse file size string to bytes.

        Args:
            size_str: Size string like "10MB", "1GB", etc.

        Returns:
            Size in bytes
        """
        size_str = size_str.upper()

        if size_str.endswith('GB'):
            return int(float(size_str[:-2]) * 1024 * 1024 * 1024)
        elif size_str.endswith('MB'):
            return int(float(size_str[:-2]) * 1024 * 1024)
        elif size_str.endswith('KB'):
            return int(float(size_str[:-2]) * 1024)
        elif size_str.endswith('B'):
            return int(size_str[:-1])
        else:
            # Default to MB if no unit specified
            return int(float(size_str) * 1024 * 1024)

    def get_logger(self) -> logging.Logger:
        """
        Get configured logger instance.

        Returns:
            Configured logger instance
        """
        if not self.configured:
            self.configure()
        return self.logger

    def log_system_event(self, event_type: str, message: str,
                        level: str = "INFO", **kwargs) -> None:
        """
        Log system event with structured data.

        Args:
            event_type: Type of event (e.g., "agent_start", "config_change")
            message: Event message
            level: Log level
            **kwargs: Additional event data
        """
        extra_data = {
            "event_type": event_type,
            "event_data": kwargs
        }

        log_level = getattr(logging, level.upper(), logging.INFO)
        self.logger.log(log_level, message, extra=extra_data)

    def log_agent_event(self, agent_name: str, event: str,
                       status: str, **kwargs) -> None:
        """
        Log agent-specific event.

        Args:
            agent_name: Name of the agent
            event: Event description
            status: Event status (success, error, warning)
            **kwargs: Additional event data
        """
        self.log_system_event(
            event_type="agent_event",
            message=f"Agent {agent_name}: {event}",
            level="INFO" if status == "success" else "WARNING" if status == "warning" else "ERROR",
            agent_name=agent_name,
            event=event,
            status=status,
            **kwargs
        )

    def log_performance_metric(self, metric_name: str, value: Union[int, float],
                             unit: str = "", **kwargs) -> None:
        """
        Log performance metric.

        Args:
            metric_name: Name of the metric
            value: Metric value
            unit: Unit of measurement
            **kwargs: Additional metric data
        """
        self.log_system_event(
            event_type="performance_metric",
            message=f"Metric {metric_name}: {value} {unit}",
            metric_name=metric_name,
            value=value,
            unit=unit,
            **kwargs
        )


# Global logger instance
_global_logger: Optional[TradingDashboardLogger] = None


def get_logger(name: str = "trading_dashboard") -> logging.Logger:
    """
    Get configured logger instance.

    Args:
        name: Logger name

    Returns:
        Configured logger instance
    """
    global _global_logger

    if _global_logger is None or _global_logger.name != name:
        _global_logger = TradingDashboardLogger(name)
        _global_logger.configure()

    return _global_logger.get_logger()


def configure_logging(force_reconfigure: bool = False) -> None:
    """
    Configure global logging system.

    Args:
        force_reconfigure: Whether to force reconfiguration
    """
    global _global_logger

    if _global_logger is None:
        _global_logger = TradingDashboardLogger()

    _global_logger.configure(force_reconfigure=force_reconfigure)


def log_system_startup() -> None:
    """Log system startup event."""
    logger = get_logger()
    logger.info("Trading Dashboard starting up", extra={
        "event_type": "system_startup",
        "python_version": sys.version,
        "platform": sys.platform
    })