"""
Advanced Error Handling System for Trading Dashboard.

This module provides comprehensive error handling capabilities including:
- Centralized error management
- Automatic error recovery strategies
- Graceful degradation modes
- Error state persistence
- User-friendly error reporting
- Contextual error information
- Error severity classification
- Resolution guidance
"""

import json
import traceback
import sys
import os
import time
import asyncio
import functools
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Callable, Type
from dataclasses import dataclass, asdict
from enum import Enum
import logging

from .logging import get_logger
from .config import get_config_manager


class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class ErrorCategory(Enum):
    """Error category types."""
    SYSTEM = "system"
    NETWORK = "network"
    CONFIGURATION = "configuration"
    DATA = "data"
    AUTHENTICATION = "authentication"
    AGENT = "agent"
    UI = "ui"
    DATABASE = "database"
    EXTERNAL_API = "external_api"
    VALIDATION = "validation"


class RecoveryStrategy(Enum):
    """Error recovery strategy types."""
    RETRY = "retry"
    FALLBACK = "fallback"
    SKIP = "skip"
    RESTART = "restart"
    DEGRADE = "degrade"
    MANUAL = "manual"
    IGNORE = "ignore"


@dataclass
class ErrorContext:
    """Error context information."""
    function_name: str
    module_name: str
    file_path: str
    line_number: int
    arguments: Dict[str, Any]
    local_variables: Dict[str, Any]
    stack_trace: List[str]
    timestamp: datetime
    thread_id: int
    process_id: int


@dataclass
class RecoveryAction:
    """Recovery action definition."""
    strategy: RecoveryStrategy
    max_attempts: int
    delay_seconds: float
    backoff_multiplier: float
    fallback_function: Optional[Callable] = None
    success_condition: Optional[Callable] = None
    failure_threshold: Optional[int] = None


@dataclass
class ErrorInstance:
    """Individual error instance."""
    error_id: str
    timestamp: datetime
    severity: ErrorSeverity
    category: ErrorCategory
    exception_type: str
    message: str
    context: ErrorContext
    recovery_action: Optional[RecoveryAction]
    recovery_attempts: int
    resolved: bool
    resolution_timestamp: Optional[datetime]
    resolution_method: Optional[str]
    user_impact: str
    system_state: Dict[str, Any]


@dataclass
class ErrorPattern:
    """Error pattern for pattern-based recovery."""
    pattern_id: str
    exception_types: List[str]
    message_patterns: List[str]
    categories: List[ErrorCategory]
    frequency_threshold: int
    time_window_minutes: int
    recovery_action: RecoveryAction


class ErrorState:
    """Error state manager for persistence."""
    
    def __init__(self, state_file: str = "logs/error_state.json"):
        self.state_file = Path(state_file)
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self._state: Dict[str, Any] = {}
        self._load_state()
    
    def _load_state(self) -> None:
        """Load error state from file."""
        try:
            if self.state_file.exists():
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    self._state = json.load(f)
        except Exception:
            self._state = {}
    
    def _save_state(self) -> None:
        """Save error state to file."""
        try:
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(self._state, f, default=str, indent=2)
        except Exception as e:
            logger = get_logger()
            logger.error(f"Failed to save error state: {e}")
    
    def set(self, key: str, value: Any) -> None:
        """Set error state value."""
        self._state[key] = value
        self._save_state()
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get error state value."""
        return self._state.get(key, default)
    
    def increment(self, key: str, amount: int = 1) -> int:
        """Increment error state counter."""
        current = self._state.get(key, 0)
        new_value = current + amount
        self.set(key, new_value)
        return new_value
    
    def clear(self, key: Optional[str] = None) -> None:
        """Clear error state."""
        if key:
            self._state.pop(key, None)
        else:
            self._state.clear()
        self._save_state()


class ErrorRecoveryManager:
    """Error recovery strategy manager."""
    
    def __init__(self):
        self.logger = get_logger()
        self.patterns: List[ErrorPattern] = []
        self.recovery_history: Dict[str, List[datetime]] = {}
        self._load_default_patterns()
    
    def _load_default_patterns(self) -> None:
        """Load default error patterns."""
        # Network connection errors
        self.add_pattern(ErrorPattern(
            pattern_id="network_connection",
            exception_types=["ConnectionError", "TimeoutError", "HTTPError"],
            message_patterns=["connection", "timeout", "network"],
            categories=[ErrorCategory.NETWORK],
            frequency_threshold=3,
            time_window_minutes=5,
            recovery_action=RecoveryAction(
                strategy=RecoveryStrategy.RETRY,
                max_attempts=3,
                delay_seconds=2.0,
                backoff_multiplier=2.0
            )
        ))
        
        # Configuration errors
        self.add_pattern(ErrorPattern(
            pattern_id="configuration_error",
            exception_types=["KeyError", "ValueError", "TypeError"],
            message_patterns=["config", "setting", "parameter"],
            categories=[ErrorCategory.CONFIGURATION],
            frequency_threshold=1,
            time_window_minutes=60,
            recovery_action=RecoveryAction(
                strategy=RecoveryStrategy.FALLBACK,
                max_attempts=1,
                delay_seconds=0.0,
                backoff_multiplier=1.0
            )
        ))
        
        # Agent communication errors
        self.add_pattern(ErrorPattern(
            pattern_id="agent_communication",
            exception_types=["ConnectionError", "HTTPError", "RequestException"],
            message_patterns=["agent", "endpoint", "service"],
            categories=[ErrorCategory.AGENT],
            frequency_threshold=2,
            time_window_minutes=10,
            recovery_action=RecoveryAction(
                strategy=RecoveryStrategy.DEGRADE,
                max_attempts=2,
                delay_seconds=5.0,
                backoff_multiplier=1.5
            )
        ))
    
    def add_pattern(self, pattern: ErrorPattern) -> None:
        """Add error pattern."""
        self.patterns.append(pattern)
    
    def find_matching_pattern(self, error: ErrorInstance) -> Optional[ErrorPattern]:
        """Find matching error pattern."""
        for pattern in self.patterns:
            # Check exception type
            if error.exception_type in pattern.exception_types:
                # Check message patterns
                if any(msg_pattern.lower() in error.message.lower() 
                      for msg_pattern in pattern.message_patterns):
                    # Check category
                    if error.category in pattern.categories:
                        return pattern
        return None
    
    async def execute_recovery(self, error: ErrorInstance, 
                             recovery_action: RecoveryAction) -> bool:
        """Execute recovery action."""
        attempt = 0
        delay = recovery_action.delay_seconds
        
        while attempt < recovery_action.max_attempts:
            try:
                attempt += 1
                
                if attempt > 1:
                    self.logger.info(f"Recovery attempt {attempt} for error {error.error_id}")
                    await asyncio.sleep(delay)
                    delay *= recovery_action.backoff_multiplier
                
                success = await self._perform_recovery_strategy(
                    error, recovery_action.strategy
                )
                
                if success:
                    self.logger.info(f"Recovery successful for error {error.error_id}")
                    return True
                    
            except Exception as e:
                self.logger.error(f"Recovery attempt {attempt} failed: {e}")
        
        self.logger.error(f"Recovery failed after {attempt} attempts for error {error.error_id}")
        return False
    
    async def _perform_recovery_strategy(self, error: ErrorInstance, 
                                       strategy: RecoveryStrategy) -> bool:
        """Perform specific recovery strategy."""
        if strategy == RecoveryStrategy.RETRY:
            # Simply return True to indicate retry should happen
            return True
            
        elif strategy == RecoveryStrategy.FALLBACK:
            # Execute fallback function if available
            if (error.recovery_action and 
                hasattr(error.recovery_action, 'fallback_function') and 
                error.recovery_action.fallback_function):
                try:
                    result = await error.recovery_action.fallback_function()
                    return result is not None
                except Exception:
                    return False
            return False
            
        elif strategy == RecoveryStrategy.DEGRADE:
            # Implement graceful degradation
            self.logger.warning(f"Graceful degradation activated for {error.category.value}")
            return True
            
        elif strategy == RecoveryStrategy.RESTART:
            # Log restart requirement
            self.logger.critical(f"System restart required for error {error.error_id}")
            return False
            
        elif strategy == RecoveryStrategy.SKIP:
            # Skip the operation
            self.logger.info(f"Skipping operation due to error {error.error_id}")
            return True
            
        elif strategy == RecoveryStrategy.MANUAL:
            # Requires manual intervention
            self.logger.error(f"Manual intervention required for error {error.error_id}")
            return False
            
        elif strategy == RecoveryStrategy.IGNORE:
            # Ignore the error
            self.logger.warning(f"Ignoring error {error.error_id}")
            return True
        
        return False


class ErrorReportGenerator:
    """Generate user-friendly error reports."""
    
    def __init__(self):
        self.logger = get_logger()
        self.error_templates = self._load_error_templates()
    
    def _load_error_templates(self) -> Dict[str, Dict[str, str]]:
        """Load error message templates."""
        return {
            "network": {
                "title": "Network Connection Problem",
                "description": "Unable to connect to the required service.",
                "user_action": "Please check your internet connection and try again.",
                "technical_action": "Verify network settings and firewall configuration."
            },
            "configuration": {
                "title": "Configuration Error",
                "description": "There's an issue with the system configuration.",
                "user_action": "Please check your settings or contact support.",
                "technical_action": "Review configuration files and validate settings."
            },
            "agent": {
                "title": "Agent Communication Error",
                "description": "Unable to communicate with the trading agent.",
                "user_action": "The system will try to recover automatically.",
                "technical_action": "Check agent status and restart if necessary."
            },
            "data": {
                "title": "Data Processing Error",
                "description": "There was an error processing the requested data.",
                "user_action": "Please try again or use different parameters.",
                "technical_action": "Validate data format and processing pipeline."
            },
            "authentication": {
                "title": "Authentication Problem",
                "description": "Unable to verify your credentials.",
                "user_action": "Please check your login information and try again.",
                "technical_action": "Verify authentication service and credentials."
            }
        }
    
    def generate_user_report(self, error: ErrorInstance) -> Dict[str, Any]:
        """Generate user-friendly error report."""
        template = self.error_templates.get(
            error.category.value,
            self.error_templates.get("configuration", {})
        )
        
        # Fallback template if none found
        if not template:
            template = {
                "title": "System Error",
                "description": "An unexpected error occurred.",
                "user_action": "Please try again or contact support."
            }
        
        return {
            "error_id": error.error_id,
            "timestamp": error.timestamp.isoformat(),
            "title": template.get("title", "System Error"),
            "description": template.get("description", "An error occurred."),
            "user_action": template.get("user_action", "Please try again."),
            "severity": error.severity.value,
            "category": error.category.value,
            "resolved": error.resolved,
            "recovery_in_progress": error.recovery_attempts > 0 and not error.resolved,
            "system_impact": self._assess_system_impact(error)
        }
    
    def generate_technical_report(self, error: ErrorInstance) -> Dict[str, Any]:
        """Generate technical error report."""
        return {
            "error_id": error.error_id,
            "timestamp": error.timestamp.isoformat(),
            "exception_type": error.exception_type,
            "message": error.message,
            "severity": error.severity.value,
            "category": error.category.value,
            "context": {
                "function": error.context.function_name,
                "module": error.context.module_name,
                "file": error.context.file_path,
                "line": error.context.line_number,
                "arguments": error.context.arguments,
                "stack_trace": error.context.stack_trace
            },
            "recovery": {
                "strategy": error.recovery_action.strategy.value if error.recovery_action else None,
                "attempts": error.recovery_attempts,
                "resolved": error.resolved
            },
            "system_state": error.system_state
        }
    
    def _assess_system_impact(self, error: ErrorInstance) -> str:
        """Assess system impact of error."""
        if error.severity in [ErrorSeverity.CRITICAL, ErrorSeverity.EMERGENCY]:
            return "High - System functionality may be impacted"
        elif error.severity == ErrorSeverity.HIGH:
            return "Medium - Some features may be temporarily unavailable"
        elif error.severity == ErrorSeverity.MEDIUM:
            return "Low - Minor impact on user experience"
        else:
            return "Minimal - No significant impact expected"


class AdvancedErrorHandler:
    """Central error handling system."""
    
    def __init__(self):
        self.logger = get_logger()
        self.state = ErrorState()
        self.recovery_manager = ErrorRecoveryManager()
        self.report_generator = ErrorReportGenerator()
        self.error_history: List[ErrorInstance] = []
        self.error_counts: Dict[str, int] = {}
        self._degraded_features: set = set()
    
    def _generate_error_id(self) -> str:
        """Generate unique error ID."""
        timestamp = int(time.time() * 1000)
        return f"ERR_{timestamp}_{len(self.error_history)}"
    
    def _extract_context(self, exc_info=None) -> ErrorContext:
        """Extract error context information."""
        if exc_info is None:
            exc_info = sys.exc_info()
        
        frame = sys._getframe(2)  # Go up 2 frames to get the original caller
        
        # Extract local variables (safely)
        local_vars = {}
        try:
            for key, value in frame.f_locals.items():
                try:
                    # Only include serializable values
                    json.dumps(value, default=str)
                    local_vars[key] = str(value)[:200]  # Limit size
                except (TypeError, ValueError):
                    local_vars[key] = f"<non-serializable: {type(value).__name__}>"
        except Exception:
            local_vars = {"error": "Failed to extract local variables"}
        
        # Extract arguments
        arguments = {}
        try:
            if 'args' in frame.f_locals:
                arguments['args'] = str(frame.f_locals['args'])[:200]
            if 'kwargs' in frame.f_locals:
                arguments['kwargs'] = str(frame.f_locals['kwargs'])[:200]
        except Exception:
            arguments = {"error": "Failed to extract arguments"}
        
        return ErrorContext(
            function_name=frame.f_code.co_name,
            module_name=frame.f_globals.get('__name__', 'unknown'),
            file_path=frame.f_code.co_filename,
            line_number=frame.f_lineno,
            arguments=arguments,
            local_variables=local_vars,
            stack_trace=traceback.format_exception(exc_info[0], exc_info[1], exc_info[2]) if exc_info[0] else [],
            timestamp=datetime.now(),
            thread_id=os.getpid(),
            process_id=os.getpid()
        )
    
    def _determine_severity(self, exception: Exception, 
                          category: ErrorCategory) -> ErrorSeverity:
        """Determine error severity."""
        critical_exceptions = [
            "SystemExit", "KeyboardInterrupt", "MemoryError",
            "SystemError", "ImportError"
        ]
        
        high_exceptions = [
            "ConnectionError", "TimeoutError", "AuthenticationError",
            "DatabaseError", "FileNotFoundError"
        ]
        
        exception_name = type(exception).__name__
        
        if exception_name in critical_exceptions:
            return ErrorSeverity.CRITICAL
        elif exception_name in high_exceptions:
            return ErrorSeverity.HIGH
        elif category in [ErrorCategory.SYSTEM, ErrorCategory.CONFIGURATION]:
            return ErrorSeverity.MEDIUM
        else:
            return ErrorSeverity.LOW
    
    def _determine_category(self, exception: Exception, 
                          context: ErrorContext) -> ErrorCategory:
        """Determine error category."""
        exception_name = type(exception).__name__
        message = str(exception).lower()
        module_name = context.module_name.lower()
        
        if "network" in message or "connection" in message:
            return ErrorCategory.NETWORK
        elif "config" in message or "setting" in message:
            return ErrorCategory.CONFIGURATION
        elif "auth" in message or "token" in message:
            return ErrorCategory.AUTHENTICATION
        elif "agent" in module_name or "agent" in message:
            return ErrorCategory.AGENT
        elif "data" in message or "parse" in message:
            return ErrorCategory.DATA
        elif "ui" in module_name or "dashboard" in module_name:
            return ErrorCategory.UI
        elif "database" in message or "db" in message:
            return ErrorCategory.DATABASE
        elif "api" in message or "http" in message:
            return ErrorCategory.EXTERNAL_API
        elif "validation" in message or "invalid" in message:
            return ErrorCategory.VALIDATION
        else:
            return ErrorCategory.SYSTEM
    
    async def handle_error(self, exception: Exception, 
                          custom_category: Optional[ErrorCategory] = None,
                          custom_severity: Optional[ErrorSeverity] = None,
                          recovery_action: Optional[RecoveryAction] = None) -> ErrorInstance:
        """Handle error with comprehensive processing."""
        try:
            # Extract context
            context = self._extract_context()
            
            # Determine category and severity
            category = custom_category or self._determine_category(exception, context)
            severity = custom_severity or self._determine_severity(exception, category)
            
            # Create error instance
            error = ErrorInstance(
                error_id=self._generate_error_id(),
                timestamp=datetime.now(),
                severity=severity,
                category=category,
                exception_type=type(exception).__name__,
                message=str(exception),
                context=context,
                recovery_action=recovery_action,
                recovery_attempts=0,
                resolved=False,
                resolution_timestamp=None,
                resolution_method=None,
                user_impact=self._assess_user_impact(severity, category),
                system_state=self._capture_system_state()
            )
            
            # Log error
            self.logger.error(
                f"Error handled: {error.error_id} - {error.message}",
                extra={
                    "error_id": error.error_id,
                    "category": category.value,
                    "severity": severity.value,
                    "exception_type": error.exception_type
                }
            )
            
            # Add to history
            self.error_history.append(error)
            self.error_counts[error.exception_type] = self.error_counts.get(error.exception_type, 0) + 1
            
            # Find and execute recovery if applicable
            if not recovery_action:
                pattern = self.recovery_manager.find_matching_pattern(error)
                if pattern:
                    error.recovery_action = pattern.recovery_action
            
            if error.recovery_action:
                error.recovery_attempts = 1
                success = await self.recovery_manager.execute_recovery(error, error.recovery_action)
                if success:
                    error.resolved = True
                    error.resolution_timestamp = datetime.now()
                    error.resolution_method = "automatic_recovery"
            
            # Update persistent state
            self.state.increment(f"error_count_{category.value}")
            self.state.increment(f"error_total")
            
            return error
            
        except Exception as handler_error:
            # Fallback logging if error handler fails
            self.logger.critical(f"Error handler failed: {handler_error}")
            raise handler_error
    
    def _assess_user_impact(self, severity: ErrorSeverity, 
                          category: ErrorCategory) -> str:
        """Assess user impact."""
        if severity == ErrorSeverity.CRITICAL:
            return "System may be unusable"
        elif severity == ErrorSeverity.HIGH:
            return "Significant feature impact"
        elif severity == ErrorSeverity.MEDIUM:
            return "Minor feature impact"
        else:
            return "Minimal impact"
    
    def _capture_system_state(self) -> Dict[str, Any]:
        """Capture current system state."""
        try:
            return {
                "timestamp": datetime.now().isoformat(),
                "degraded_features": list(self._degraded_features),
                "error_counts": dict(self.error_counts),
                "total_errors": len(self.error_history),
                "memory_usage": self._get_memory_usage(),
                "active_threads": self._get_thread_count()
            }
        except Exception:
            return {"error": "Failed to capture system state"}
    
    def _get_memory_usage(self) -> str:
        """Get memory usage information."""
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            return f"{memory_info.rss / 1024 / 1024:.1f} MB"
        except ImportError:
            return "N/A (psutil not available)"
        except Exception:
            return "N/A"
    
    def _get_thread_count(self) -> int:
        """Get active thread count."""
        try:
            import threading
            return threading.active_count()
        except Exception:
            return -1
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics."""
        now = datetime.now()
        recent_errors = [e for e in self.error_history 
                        if (now - e.timestamp) < timedelta(hours=24)]
        
        return {
            "total_errors": len(self.error_history),
            "recent_errors_24h": len(recent_errors),
            "resolved_errors": len([e for e in self.error_history if e.resolved]),
            "error_by_category": self._group_by_category(),
            "error_by_severity": self._group_by_severity(),
            "most_common_errors": self._get_most_common_errors(),
            "degraded_features": list(self._degraded_features),
            "recovery_success_rate": self._calculate_recovery_rate()
        }
    
    def _group_by_category(self) -> Dict[str, int]:
        """Group errors by category."""
        categories = {}
        for error in self.error_history:
            categories[error.category.value] = categories.get(error.category.value, 0) + 1
        return categories
    
    def _group_by_severity(self) -> Dict[str, int]:
        """Group errors by severity."""
        severities = {}
        for error in self.error_history:
            severities[error.severity.value] = severities.get(error.severity.value, 0) + 1
        return severities
    
    def _get_most_common_errors(self) -> List[Dict[str, Any]]:
        """Get most common error types."""
        error_types = {}
        for error in self.error_history:
            key = f"{error.exception_type}: {error.message[:50]}..."
            error_types[key] = error_types.get(key, 0) + 1
        
        return [{"error": k, "count": v} for k, v in 
                sorted(error_types.items(), key=lambda x: x[1], reverse=True)[:10]]
    
    def _calculate_recovery_rate(self) -> float:
        """Calculate recovery success rate."""
        attempted = len([e for e in self.error_history if e.recovery_attempts > 0])
        if attempted == 0:
            return 0.0
        resolved = len([e for e in self.error_history if e.resolved])
        return (resolved / attempted) * 100
    
    def enable_degraded_mode(self, feature: str) -> None:
        """Enable degraded mode for a feature."""
        self._degraded_features.add(feature)
        self.logger.warning(f"Feature '{feature}' entering degraded mode")
    
    def disable_degraded_mode(self, feature: str) -> None:
        """Disable degraded mode for a feature."""
        self._degraded_features.discard(feature)
        self.logger.info(f"Feature '{feature}' recovered from degraded mode")
    
    def is_degraded(self, feature: str) -> bool:
        """Check if feature is in degraded mode."""
        return feature in self._degraded_features
    
    def clear_error_history(self, hours: int = 24) -> None:
        """Clear old error history."""
        cutoff = datetime.now() - timedelta(hours=hours)
        self.error_history = [e for e in self.error_history if e.timestamp > cutoff]


# Global error handler instance
_global_error_handler: Optional[AdvancedErrorHandler] = None


def get_error_handler() -> AdvancedErrorHandler:
    """Get global error handler instance."""
    global _global_error_handler
    if _global_error_handler is None:
        _global_error_handler = AdvancedErrorHandler()
    return _global_error_handler


def handle_errors(recovery_action: Optional[RecoveryAction] = None,
                 category: Optional[ErrorCategory] = None,
                 severity: Optional[ErrorSeverity] = None,
                 silent: bool = False):
    """
    Decorator for automatic error handling.
    
    Args:
        recovery_action: Custom recovery action
        category: Error category override
        severity: Error severity override
        silent: Whether to suppress re-raising the exception
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                handler = get_error_handler()
                error = await handler.handle_error(e, category, severity, recovery_action)
                
                if not silent and not error.resolved:
                    raise e
                
                return None
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                handler = get_error_handler()
                # Run async handler in sync context
                try:
                    loop = asyncio.get_event_loop()
                    error = loop.run_until_complete(
                        handler.handle_error(e, category, severity, recovery_action)
                    )
                except RuntimeError:
                    # No event loop, create one
                    error = asyncio.run(
                        handler.handle_error(e, category, severity, recovery_action)
                    )
                
                if not silent and not error.resolved:
                    raise e
                
                return None
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator