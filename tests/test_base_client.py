"""
Test suite for BaseClient API functionality.

Tests the comprehensive base client including connection pooling,
retry logic, circuit breakers, and health monitoring.
"""

import pytest
import time
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import requests
from requests.exceptions import ConnectionError, Timeout, HTTPError

# Add project root to path
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.api_client.base_client import (
    BaseClient, CircuitBreaker, CircuitState, HealthStatus,
    RetryConfig, CircuitBreakerConfig, CircuitBreakerOpenError,
    RequestMetrics
)


class MockBaseClient(BaseClient):
    """Mock implementation of BaseClient for testing."""

    def health_check(self):
        """Test health check implementation."""
        try:
            response = self.get('/health')
            return {
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'response_code': response.status_code
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }


class TestCircuitBreaker:
    """Test cases for CircuitBreaker."""

    def test_circuit_breaker_initialization(self):
        """Test circuit breaker initialization."""
        config = CircuitBreakerConfig(failure_threshold=3, recovery_timeout=10)
        breaker = CircuitBreaker(config)

        assert breaker.state == CircuitState.CLOSED
        assert breaker.failure_count == 0
        assert breaker.success_count == 0

    def test_circuit_breaker_success(self):
        """Test circuit breaker with successful calls."""
        config = CircuitBreakerConfig(failure_threshold=3)
        breaker = CircuitBreaker(config)

        def success_func():
            return "success"

        result = breaker.call(success_func)
        assert result == "success"
        assert breaker.state == CircuitState.CLOSED
        assert breaker.failure_count == 0

    def test_circuit_breaker_failure_threshold(self):
        """Test circuit breaker opening after failures."""
        config = CircuitBreakerConfig(failure_threshold=2, recovery_timeout=1)
        breaker = CircuitBreaker(config)

        def failing_func():
            raise ConnectionError("Test failure")

        # First failure
        with pytest.raises(ConnectionError):
            breaker.call(failing_func)
        assert breaker.state == CircuitState.CLOSED

        # Second failure should open circuit
        with pytest.raises(ConnectionError):
            breaker.call(failing_func)
        assert breaker.state == CircuitState.OPEN

        # Third call should raise CircuitBreakerOpenError
        with pytest.raises(CircuitBreakerOpenError):
            breaker.call(failing_func)

    def test_circuit_breaker_half_open_recovery(self):
        """Test circuit breaker half-open recovery."""
        config = CircuitBreakerConfig(
            failure_threshold=1,
            recovery_timeout=0.1,  # Short timeout for testing
            success_threshold=2
        )
        breaker = CircuitBreaker(config)

        def failing_func():
            raise ConnectionError("Test failure")

        def success_func():
            return "success"

        # Open circuit with failure
        with pytest.raises(ConnectionError):
            breaker.call(failing_func)
        assert breaker.state == CircuitState.OPEN

        # Wait for recovery timeout
        time.sleep(0.2)

        # Next call should move to half-open
        result = breaker.call(success_func)
        assert result == "success"
        assert breaker.state == CircuitState.HALF_OPEN

        # Another success should close circuit
        result = breaker.call(success_func)
        assert result == "success"
        assert breaker.state == CircuitState.CLOSED


class TestRequestMetrics:
    """Test cases for RequestMetrics."""

    def test_metrics_initialization(self):
        """Test metrics initialization."""
        metrics = RequestMetrics()
        assert metrics.total_requests == 0
        assert metrics.successful_requests == 0
        assert metrics.failed_requests == 0
        assert metrics.average_response_time == 0.0


class TestBaseClientImplementation:
    """Test cases for BaseClient implementation."""

    def setup_method(self):
        """Set up method called before each test."""
        pass  # We'll create fresh clients in each test

    def test_client_initialization(self):
        """Test client initialization."""
        client = MockBaseClient("https://api.example.com", timeout=10.0)

        assert client.base_url == "https://api.example.com"
        assert client.timeout == 10.0
        assert client.health_status == HealthStatus.UNKNOWN
        assert client.circuit_breaker.state == CircuitState.CLOSED
        assert isinstance(client.metrics, RequestMetrics)

    def test_client_initialization_invalid_url(self):
        """Test client initialization with invalid URL."""
        with pytest.raises(ValueError, match="Invalid base URL"):
            MockBaseClient("not-a-url")

    def test_client_base_url_normalization(self):
        """Test base URL normalization."""
        client = MockBaseClient("https://api.example.com/")
        assert client.base_url == "https://api.example.com"

    @patch('requests.Session.request')
    def test_successful_get_request(self, mock_request):
        """Test successful GET request."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "test"}
        mock_request.return_value = mock_response

        client = MockBaseClient("https://api.example.com")

        response = client.get('/test')

        assert response.status_code == 200
        assert client.metrics.total_requests == 1
        assert client.metrics.successful_requests == 1
        assert client.metrics.failed_requests == 0

        mock_request.assert_called_once()

    @patch('requests.Session.request')
    def test_successful_post_request(self, mock_request):
        """Test successful POST request."""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_request.return_value = mock_response

        client = MockBaseClient("https://api.example.com")

        response = client.post('/create', data={"name": "test"})

        assert response.status_code == 201
        assert client.metrics.successful_requests == 1

    @patch('requests.Session.request')
    def test_http_error_handling(self, mock_request):
        """Test HTTP error handling."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_response.raise_for_status.side_effect = HTTPError("Server Error")
        mock_request.return_value = mock_response

        client = MockBaseClient("https://api.example.com")

        with pytest.raises(HTTPError):
            client.get('/error')

        assert client.metrics.failed_requests == 1

    @patch('requests.Session.request')
    def test_connection_error_handling(self, mock_request):
        """Test connection error handling."""
        mock_request.side_effect = ConnectionError("Connection failed")

        client = MockBaseClient("https://api.example.com")

        with pytest.raises(ConnectionError):
            client.get('/unreachable')

        assert client.metrics.failed_requests == 1

    @patch('requests.Session.request')
    def test_timeout_handling(self, mock_request):
        """Test timeout handling."""
        mock_request.side_effect = Timeout("Request timeout")

        client = MockBaseClient("https://api.example.com")

        with pytest.raises(Timeout):
            client.get('/slow')

        assert client.metrics.failed_requests == 1

    @patch('requests.Session.request')
    def test_circuit_breaker_integration(self, mock_request):
        """Test circuit breaker integration with client."""
        mock_request.side_effect = ConnectionError("Connection failed")

        # Configure low failure threshold for testing
        circuit_config = CircuitBreakerConfig(failure_threshold=2, recovery_timeout=0.1)
        client = MockBaseClient("https://api.example.com", circuit_config=circuit_config)

        # First failure
        with pytest.raises(ConnectionError):
            client.get('/test')
        assert client.circuit_breaker.state == CircuitState.CLOSED

        # Second failure should open circuit
        with pytest.raises(ConnectionError):
            client.get('/test')
        assert client.circuit_breaker.state == CircuitState.OPEN

        # Third call should raise CircuitBreakerOpenError
        with pytest.raises(CircuitBreakerOpenError):
            client.get('/test')

    def test_metrics_reporting(self):
        """Test metrics reporting."""
        client = MockBaseClient("https://api.example.com")

        metrics = client.get_metrics()

        assert "total_requests" in metrics
        assert "successful_requests" in metrics
        assert "failed_requests" in metrics
        assert "success_rate" in metrics
        assert "average_response_time" in metrics
        assert "circuit_breaker_state" in metrics
        assert "health_status" in metrics
        assert "base_url" in metrics

        assert metrics["base_url"] == "https://api.example.com"
        assert metrics["health_status"] == "unknown"

    @patch('requests.Session.request')
    def test_custom_headers(self, mock_request):
        """Test custom headers handling."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_request.return_value = mock_response

        client = MockBaseClient(
            "https://api.example.com",
            headers={"Authorization": "Bearer token"}
        )

        client.get('/test', headers={"Custom-Header": "value"})

        # Check that both default and custom headers were used
        call_kwargs = mock_request.call_args[1]
        assert "Authorization" in call_kwargs["headers"]
        assert "Custom-Header" in call_kwargs["headers"]
        assert call_kwargs["headers"]["Authorization"] == "Bearer token"
        assert call_kwargs["headers"]["Custom-Header"] == "value"

    def test_context_manager(self):
        """Test client as context manager."""
        with MockBaseClient("https://api.example.com") as client:
            assert isinstance(client, MockBaseClient)
            assert hasattr(client, 'session')

        # Session should be closed after context exit
        # Note: We can't easily test if session is actually closed
        # without accessing private attributes

    def test_client_representation(self):
        """Test string representation of client."""
        client = MockBaseClient("https://api.example.com")
        repr_str = repr(client)

        assert "MockBaseClient" in repr_str
        assert "https://api.example.com" in repr_str
        assert "health_status='unknown'" in repr_str
        assert "circuit_state='closed'" in repr_str

    @patch('requests.Session.request')
    def test_retry_configuration(self, mock_request):
        """Test retry configuration."""
        retry_config = RetryConfig(max_attempts=2, backoff_factor=0.1)
        client = MockBaseClient("https://api.example.com", retry_config=retry_config)

        assert client.retry_config.max_attempts == 2
        assert client.retry_config.backoff_factor == 0.1

    def test_circuit_breaker_manual_reset(self):
        """Test manual circuit breaker reset."""
        client = MockBaseClient("https://api.example.com")

        # Force circuit breaker to open state
        client.circuit_breaker.state = CircuitState.OPEN
        client.circuit_breaker.failure_count = 5

        # Reset circuit breaker
        client.reset_circuit_breaker()

        assert client.circuit_breaker.state == CircuitState.CLOSED
        assert client.circuit_breaker.failure_count == 0

    @patch('requests.Session.request')
    def test_health_check_implementation(self, mock_request):
        """Test health check implementation."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_request.return_value = mock_response

        client = MockBaseClient("https://api.example.com")
        health_result = client.health_check()

        assert "status" in health_result
        assert "timestamp" in health_result
        assert health_result["status"] == "healthy"

    @patch('requests.Session.request')
    def test_all_http_methods(self, mock_request):
        """Test all HTTP methods."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_request.return_value = mock_response

        client = MockBaseClient("https://api.example.com")

        # Test all methods
        client.get('/test')
        client.post('/test', data={"key": "value"})
        client.put('/test', data={"key": "value"})
        client.patch('/test', data={"key": "value"})
        client.delete('/test')

        assert mock_request.call_count == 5
        assert client.metrics.total_requests == 5
        assert client.metrics.successful_requests == 5


# Helper function to run all tests
def run_base_client_tests():
    """Run all base client tests."""
    pytest.main([__file__, "-v"])


if __name__ == "__main__":
    run_base_client_tests()