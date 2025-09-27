"""
Test suite for Advanced Error Handling System.

This module provides comprehensive tests for error handling capabilities including:
- Error detection and classification
- Recovery strategies and execution
- System diagnostics and monitoring
- User-friendly error reporting
"""

import pytest
import asyncio
import json
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from src.utils.error_handling import (
    AdvancedErrorHandler,
    ErrorSeverity,
    ErrorCategory,
    RecoveryStrategy,
    RecoveryAction,
    ErrorState,
    get_error_handler,
    handle_errors
)
from src.utils.diagnostics import (
    SystemDiagnosticsManager,
    NetworkDiagnostics,
    ConfigurationDiagnostics,
    PerformanceDiagnostics,
    DiagnosticStatus,
    get_diagnostics_manager
)


class TestErrorHandling:
    """Test error handling functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.error_handler = AdvancedErrorHandler()
        
    def test_error_handler_initialization(self):
        """Test error handler initializes correctly."""
        assert self.error_handler is not None
        assert len(self.error_handler.error_history) == 0
        assert len(self.error_handler.error_counts) == 0
        assert len(self.error_handler._degraded_features) == 0
    
    @pytest.mark.asyncio
    async def test_handle_basic_error(self):
        """Test basic error handling."""
        test_error = ValueError("Test error message")
        
        error_instance = await self.error_handler.handle_error(test_error)
        
        assert error_instance.exception_type == "ValueError"
        assert error_instance.message == "Test error message"
        assert error_instance.severity in [ErrorSeverity.LOW, ErrorSeverity.MEDIUM]
        assert error_instance.category in [ErrorCategory.VALIDATION, ErrorCategory.SYSTEM]  # Allow both
        assert len(self.error_handler.error_history) == 1
    
    @pytest.mark.asyncio
    async def test_error_severity_classification(self):
        """Test error severity classification."""
        # Test critical error
        critical_error = SystemError("Critical system error")
        error_instance = await self.error_handler.handle_error(critical_error)
        assert error_instance.severity == ErrorSeverity.CRITICAL
        
        # Test high severity error
        high_error = ConnectionError("Connection failed")
        error_instance = await self.error_handler.handle_error(high_error)
        assert error_instance.severity == ErrorSeverity.HIGH
        
        # Test low severity error
        low_error = ValueError("Invalid value")
        error_instance = await self.error_handler.handle_error(low_error)
        assert error_instance.severity == ErrorSeverity.LOW
    
    @pytest.mark.asyncio
    async def test_error_category_classification(self):
        """Test error category classification."""
        # Test network error
        network_error = ConnectionError("Network connection failed")
        error_instance = await self.error_handler.handle_error(network_error)
        assert error_instance.category == ErrorCategory.NETWORK
        
        # Test configuration error
        config_error = KeyError("config setting not found")
        error_instance = await self.error_handler.handle_error(config_error)
        assert error_instance.category == ErrorCategory.CONFIGURATION
    
    def test_error_statistics(self):
        """Test error statistics generation."""
        # Add some mock errors to history
        now = datetime.now()
        for i in range(5):
            mock_error = Mock()
            mock_error.timestamp = now - timedelta(hours=i)
            mock_error.resolved = i < 3
            mock_error.recovery_attempts = 1 if i < 3 else 0
            mock_error.category = ErrorCategory.NETWORK
            mock_error.severity = ErrorSeverity.MEDIUM
            mock_error.exception_type = "ConnectionError"
            mock_error.message = f"Test error {i}"
            self.error_handler.error_history.append(mock_error)
        
        stats = self.error_handler.get_error_statistics()
        
        assert stats["total_errors"] == 5
        assert stats["resolved_errors"] == 3
        assert "error_by_category" in stats
        assert "error_by_severity" in stats
        assert "most_common_errors" in stats
    
    def test_degraded_mode_management(self):
        """Test degraded mode functionality."""
        feature_name = "test_feature"
        
        # Test enabling degraded mode
        self.error_handler.enable_degraded_mode(feature_name)
        assert self.error_handler.is_degraded(feature_name)
        assert feature_name in self.error_handler._degraded_features
        
        # Test disabling degraded mode
        self.error_handler.disable_degraded_mode(feature_name)
        assert not self.error_handler.is_degraded(feature_name)
        assert feature_name not in self.error_handler._degraded_features
    
    def test_error_history_cleanup(self):
        """Test error history cleanup."""
        # Add old errors
        old_time = datetime.now() - timedelta(days=2)
        for _ in range(3):
            mock_error = Mock()
            mock_error.timestamp = old_time
            self.error_handler.error_history.append(mock_error)
        
        # Add recent errors
        recent_time = datetime.now()
        for _ in range(2):
            mock_error = Mock()
            mock_error.timestamp = recent_time
            self.error_handler.error_history.append(mock_error)
        
        assert len(self.error_handler.error_history) == 5
        
        # Clean up errors older than 1 day
        self.error_handler.clear_error_history(hours=24)
        
        assert len(self.error_handler.error_history) == 2
    
    def test_global_error_handler(self):
        """Test global error handler singleton."""
        handler1 = get_error_handler()
        handler2 = get_error_handler()
        
        assert handler1 is handler2
        assert isinstance(handler1, AdvancedErrorHandler)


class TestErrorState:
    """Test error state persistence."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Use temporary file for testing
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        self.temp_file.close()
        self.error_state = ErrorState(self.temp_file.name)
    
    def teardown_method(self):
        """Clean up test fixtures."""
        Path(self.temp_file.name).unlink(missing_ok=True)
    
    def test_state_persistence(self):
        """Test state persistence."""
        # Set some values
        self.error_state.set("test_key", "test_value")
        self.error_state.set("counter", 42)
        
        # Create new instance to test loading
        new_state = ErrorState(self.temp_file.name)
        
        assert new_state.get("test_key") == "test_value"
        assert new_state.get("counter") == 42
        assert new_state.get("nonexistent", "default") == "default"
    
    def test_state_increment(self):
        """Test state increment functionality."""
        # Test increment from zero
        result = self.error_state.increment("counter")
        assert result == 1
        assert self.error_state.get("counter") == 1
        
        # Test increment existing value
        result = self.error_state.increment("counter", 5)
        assert result == 6
        assert self.error_state.get("counter") == 6
    
    def test_state_clear(self):
        """Test state clearing."""
        # Set some values
        self.error_state.set("key1", "value1")
        self.error_state.set("key2", "value2")
        
        # Clear specific key
        self.error_state.clear("key1")
        assert self.error_state.get("key1") is None
        assert self.error_state.get("key2") == "value2"
        
        # Clear all
        self.error_state.clear()
        assert self.error_state.get("key2") is None


class TestErrorDecorator:
    """Test error handling decorator."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.error_handler = get_error_handler()
        # Clear any existing errors
        self.error_handler.error_history.clear()
    
    def test_sync_decorator_success(self):
        """Test decorator on successful sync function."""
        @handle_errors()
        def test_function():
            return "success"
        
        result = test_function()
        assert result == "success"
        assert len(self.error_handler.error_history) == 0
    
    def test_sync_decorator_error(self):
        """Test decorator on sync function with error."""
        @handle_errors(silent=True)
        def test_function():
            raise ValueError("Test error")
        
        result = test_function()
        assert result is None
        assert len(self.error_handler.error_history) == 1
    
    @pytest.mark.asyncio
    async def test_async_decorator_success(self):
        """Test decorator on successful async function."""
        @handle_errors()
        async def test_function():
            await asyncio.sleep(0.01)
            return "async_success"
        
        result = await test_function()
        assert result == "async_success"
        assert len(self.error_handler.error_history) == 0
    
    @pytest.mark.asyncio
    async def test_async_decorator_error(self):
        """Test decorator on async function with error."""
        @handle_errors(silent=True)
        async def test_function():
            raise ConnectionError("Async test error")
        
        result = await test_function()
        assert result is None
        assert len(self.error_handler.error_history) == 1


class TestSystemDiagnostics:
    """Test system diagnostics functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.diagnostics = SystemDiagnosticsManager()
        self.network_diag = NetworkDiagnostics()
        self.config_diag = ConfigurationDiagnostics()
        self.perf_diag = PerformanceDiagnostics()
    
    def test_diagnostics_manager_initialization(self):
        """Test diagnostics manager initializes correctly."""
        assert self.diagnostics is not None
        assert len(self.diagnostics.test_history) == 0
    
    def test_internet_connectivity(self):
        """Test internet connectivity diagnostic."""
        result = self.network_diag.test_internet_connectivity()
        
        assert result is not None
        assert result.test_id == "network_internet"
        assert result.name == "Internet Connectivity"
        assert result.category.value == "network"
        assert result.status in [DiagnosticStatus.PASS, DiagnosticStatus.FAIL, DiagnosticStatus.WARNING]
    
    def test_port_connectivity(self):
        """Test port connectivity diagnostic."""
        # Test connection to a port that should fail
        result = self.network_diag.test_port_connectivity("localhost", 99999, timeout=1)
        
        assert result is not None
        assert "network_port_localhost_99999" in result.test_id
        assert result.category.value == "network"
        assert result.status in [DiagnosticStatus.PASS, DiagnosticStatus.FAIL, DiagnosticStatus.ERROR]
    
    def test_configuration_validation(self):
        """Test configuration validation diagnostic."""
        result = self.config_diag.validate_configuration_files()
        
        assert result is not None
        assert result.test_id == "config_validation"
        assert result.category.value == "configuration"
        assert result.status in [DiagnosticStatus.PASS, DiagnosticStatus.WARNING, DiagnosticStatus.ERROR]
    
    def test_file_permissions(self):
        """Test file permissions diagnostic."""
        result = self.config_diag.test_file_permissions()
        
        assert result is not None
        assert result.test_id == "file_permissions"
        assert result.category.value == "system"
    
    @patch('src.utils.diagnostics.HAS_PSUTIL', True)
    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_usage')
    def test_system_resources(self, mock_disk, mock_memory, mock_cpu):
        """Test system resources diagnostic."""
        # Mock psutil responses
        mock_cpu.return_value = 50.0
        
        mock_memory_obj = Mock()
        mock_memory_obj.percent = 60.0
        mock_memory_obj.available = 4 * 1024**3  # 4GB
        mock_memory.return_value = mock_memory_obj
        
        mock_disk_obj = Mock()
        mock_disk_obj.used = 50 * 1024**3  # 50GB
        mock_disk_obj.total = 100 * 1024**3  # 100GB
        mock_disk_obj.free = 50 * 1024**3  # 50GB
        mock_disk.return_value = mock_disk_obj
        
        result = self.perf_diag.check_system_resources()
        
        assert result is not None
        assert result.test_id == "system_resources"
        assert result.category.value == "performance"
        assert result.status in [DiagnosticStatus.PASS, DiagnosticStatus.WARNING, DiagnosticStatus.FAIL]
    
    def test_performance_benchmark(self):
        """Test performance benchmark."""
        result = self.perf_diag.performance_benchmark()
        
        assert result is not None
        assert result.test_id == "performance_benchmark"
        assert result.category.value == "performance"
        assert "cpu_time_ms" in result.details
        assert "memory_time_ms" in result.details
        assert "io_time_ms" in result.details
    
    def test_full_diagnostics(self):
        """Test full diagnostic run."""
        results = self.diagnostics.run_full_diagnostics()
        
        assert results is not None
        assert "overall_status" in results
        assert "summary" in results
        assert "results" in results
        assert "system_info" in results
        assert "recommendations" in results
        
        # Verify summary structure
        summary = results["summary"]
        assert "total_tests" in summary
        assert "passed" in summary
        assert "failed" in summary
        
        # Verify we have some test results
        assert len(results["results"]) > 0
    
    def test_diagnostics_history(self):
        """Test diagnostics history management."""
        # Run diagnostics to create history
        self.diagnostics.run_full_diagnostics()
        
        history = self.diagnostics.get_diagnostics_history()
        assert len(history) > 0
        
        # Clear history
        self.diagnostics.clear_diagnostics_history()
        history = self.diagnostics.get_diagnostics_history()
        assert len(history) == 0
    
    def test_global_diagnostics_manager(self):
        """Test global diagnostics manager singleton."""
        manager1 = get_diagnostics_manager()
        manager2 = get_diagnostics_manager()
        
        assert manager1 is manager2
        assert isinstance(manager1, SystemDiagnosticsManager)


class TestRecoveryStrategies:
    """Test error recovery strategies."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.error_handler = AdvancedErrorHandler()
        self.recovery_manager = self.error_handler.recovery_manager
    
    @pytest.mark.asyncio
    async def test_retry_strategy(self):
        """Test retry recovery strategy."""
        # Create mock error with retry action
        mock_error = Mock()
        mock_error.error_id = "test_retry"
        mock_error.recovery_action = RecoveryAction(
            strategy=RecoveryStrategy.RETRY,
            max_attempts=3,
            delay_seconds=0.01,
            backoff_multiplier=1.0
        )
        
        # Test successful retry
        result = await self.recovery_manager._perform_recovery_strategy(
            mock_error, RecoveryStrategy.RETRY
        )
        assert result is True
    
    @pytest.mark.asyncio
    async def test_skip_strategy(self):
        """Test skip recovery strategy."""
        mock_error = Mock()
        mock_error.error_id = "test_skip"
        
        result = await self.recovery_manager._perform_recovery_strategy(
            mock_error, RecoveryStrategy.SKIP
        )
        assert result is True
    
    @pytest.mark.asyncio
    async def test_degrade_strategy(self):
        """Test graceful degradation strategy."""
        mock_error = Mock()
        mock_error.error_id = "test_degrade"
        mock_error.category = ErrorCategory.NETWORK
        
        result = await self.recovery_manager._perform_recovery_strategy(
            mock_error, RecoveryStrategy.DEGRADE
        )
        assert result is True
    
    @pytest.mark.asyncio
    async def test_ignore_strategy(self):
        """Test ignore recovery strategy."""
        mock_error = Mock()
        mock_error.error_id = "test_ignore"
        
        result = await self.recovery_manager._perform_recovery_strategy(
            mock_error, RecoveryStrategy.IGNORE
        )
        assert result is True
    
    @pytest.mark.asyncio
    async def test_manual_strategy(self):
        """Test manual intervention strategy."""
        mock_error = Mock()
        mock_error.error_id = "test_manual"
        
        result = await self.recovery_manager._perform_recovery_strategy(
            mock_error, RecoveryStrategy.MANUAL
        )
        assert result is False  # Manual requires human intervention


if __name__ == "__main__":
    # Run specific test categories
    import subprocess
    import sys
    
    print("🧪 Running Advanced Error Handling Tests...")
    
    # Run with pytest
    result = subprocess.run([
        sys.executable, "-m", "pytest", __file__, "-v", "--tb=short"
    ], cwd=Path(__file__).parent.parent.parent)
    
    if result.returncode == 0:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed!")
        sys.exit(1)