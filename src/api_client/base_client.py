"""
Base API Client for Trading Dashboard.

This module provides a robust, feature-rich base class for API communication
with comprehensive error handling, retry logic, circuit breakers, and monitoring.
"""

import asyncio
import time
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Union, Callable, List
from enum import Enum
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import json

import requests
from requests.adapters import HTTPAdapter
from requests.exceptions import (
    RequestException, ConnectionError, Timeout, HTTPError,
    TooManyRedirects, InvalidURL, ChunkedEncodingError
)
from urllib3.util.retry import Retry

# Import our utilities
from ..utils.logging import get_logger
from ..utils.validation import DataValidator
from ..utils.formatting import DataFormatter


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Circuit breaker activated
    HALF_OPEN = "half_open"  # Testing if service recovered


class HealthStatus(Enum):
    """Agent health status."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""
    failure_threshold: int = 5          # Failures before opening circuit
    recovery_timeout: int = 30          # Seconds before trying half-open
    success_threshold: int = 3          # Successes to close circuit in half-open
    monitoring_window: int = 300        # Seconds for failure rate monitoring


@dataclass
class RetryConfig:
    """Configuration for retry logic."""
    max_attempts: int = 3
    backoff_factor: float = 1.0
    backoff_max: float = 30.0
    retry_on_status: List[int] = field(default_factory=lambda: [500, 502, 503, 504])
    retry_on_exceptions: tuple = (ConnectionError, Timeout, ChunkedEncodingError)


@dataclass
class RequestMetrics:
    """Metrics for API requests."""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    average_response_time: float = 0.0
    last_request_time: Optional[datetime] = None
    last_success_time: Optional[datetime] = None
    last_failure_time: Optional[datetime] = None
    consecutive_failures: int = 0
    consecutive_successes: int = 0


class CircuitBreaker:
    """
    Circuit breaker implementation for preventing cascading failures.

    Monitors request success/failure rates and opens the circuit when
    too many failures occur, preventing further requests until recovery.
    """

    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.failure_times: List[datetime] = []

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection."""
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
            else:
                raise CircuitBreakerOpenError(
                    f"Circuit breaker is OPEN. Last failure: {self.last_failure_time}"
                )

        try:
            result = func(*args, **kwargs)
            self._record_success()
            return result
        except Exception as e:
            self._record_failure()
            raise e

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        if not self.last_failure_time:
            return True
        return (datetime.now() - self.last_failure_time).total_seconds() >= self.config.recovery_timeout

    def _record_success(self):
        """Record successful request."""
        self.failure_count = 0
        self.success_count += 1

        if self.state == CircuitState.HALF_OPEN:
            if self.success_count >= self.config.success_threshold:
                self.state = CircuitState.CLOSED
                self.success_count = 0

    def _record_failure(self):
        """Record failed request."""
        now = datetime.now()
        self.failure_count += 1
        self.success_count = 0
        self.last_failure_time = now
        self.failure_times.append(now)

        # Clean old failure times outside monitoring window
        cutoff_time = now - timedelta(seconds=self.config.monitoring_window)
        self.failure_times = [ft for ft in self.failure_times if ft > cutoff_time]

        # Check if we should open the circuit
        if (self.state == CircuitState.CLOSED and
            len(self.failure_times) >= self.config.failure_threshold):
            self.state = CircuitState.OPEN
        elif self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.OPEN


class CircuitBreakerOpenError(Exception):
    """Exception raised when circuit breaker is open."""
    pass


class BaseClient(ABC):
    """
    Abstract base class for API clients with comprehensive features.

    Provides:
    - Connection pooling via requests.Session
    - Configurable retry logic with exponential backoff
    - Circuit breaker pattern for fault tolerance
    - Request/response logging and metrics
    - Timeout handling
    - Health monitoring
    - Request validation and sanitization
    """

    def __init__(self,
                 base_url: str,
                 timeout: float = 30.0,
                 retry_config: Optional[RetryConfig] = None,
                 circuit_config: Optional[CircuitBreakerConfig] = None,
                 headers: Optional[Dict[str, str]] = None,
                 verify_ssl: bool = True):
        """
        Initialize base client.

        Args:
            base_url: Base URL for the API
            timeout: Default timeout for requests
            retry_config: Retry configuration
            circuit_config: Circuit breaker configuration
            headers: Default headers for requests
            verify_ssl: Whether to verify SSL certificates
        """
        self.logger = get_logger(f"{self.__class__.__name__}")

        # Validate base URL
        url_validation = DataValidator.validate_url(base_url)
        if not url_validation.is_valid:
            raise ValueError(f"Invalid base URL: {url_validation.errors}")

        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self.retry_config = retry_config or RetryConfig()
        self.circuit_config = circuit_config or CircuitBreakerConfig()

        # Initialize components
        self.session = self._create_session()
        self.circuit_breaker = CircuitBreaker(self.circuit_config)
        self.metrics = RequestMetrics()
        self.default_headers = headers or {}

        # Health status
        self.health_status = HealthStatus.UNKNOWN
        self.last_health_check = None

        self.logger.info(f"Initialized {self.__class__.__name__} for {base_url}")

    def _create_session(self) -> requests.Session:
        """Create configured requests session with connection pooling."""
        session = requests.Session()

        # Configure retry strategy
        retry_strategy = Retry(
            total=self.retry_config.max_attempts,
            status_forcelist=self.retry_config.retry_on_status,
            backoff_factor=self.retry_config.backoff_factor,
            raise_on_status=False
        )

        # Create adapter with retry strategy
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=10,  # Number of connection pools
            pool_maxsize=20,      # Max connections per pool
            pool_block=False      # Don't block if pool is full
        )

        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    def _make_request(self,
                     method: str,
                     endpoint: str,
                     data: Optional[Dict[str, Any]] = None,
                     params: Optional[Dict[str, str]] = None,
                     headers: Optional[Dict[str, str]] = None,
                     timeout: Optional[float] = None,
                     **kwargs) -> requests.Response:
        """
        Make HTTP request with circuit breaker protection.

        Args:
            method: HTTP method
            endpoint: API endpoint (relative to base_url)
            data: Request body data
            params: Query parameters
            headers: Request headers
            timeout: Request timeout
            **kwargs: Additional request arguments

        Returns:
            Response object

        Raises:
            CircuitBreakerOpenError: If circuit breaker is open
            RequestException: For various request failures
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        request_headers = {**self.default_headers}
        if headers:
            request_headers.update(headers)

        request_timeout = timeout or self.timeout

        # Log request details
        self.logger.debug(f"Making {method} request to {url}",
                         extra={"endpoint": endpoint, "timeout": request_timeout})

        start_time = time.time()

        def _execute_request():
            return self.session.request(
                method=method.upper(),
                url=url,
                json=data,
                params=params,
                headers=request_headers,
                timeout=request_timeout,
                verify=self.verify_ssl,
                **kwargs
            )

        try:
            # Execute request with circuit breaker protection
            response = self.circuit_breaker.call(_execute_request)
            response_time = time.time() - start_time

            # Log response
            self.logger.debug(f"Request completed in {response_time:.3f}s",
                            extra={
                                "status_code": response.status_code,
                                "response_time": response_time,
                                "url": url
                            })

            # Check for HTTP errors
            if response.status_code >= 400:
                error_msg = f"HTTP {response.status_code} error for {method} {url}"
                if response.status_code >= 500:
                    # Server error - might recover, record as failure
                    self._update_metrics(False, response_time)
                    self.logger.error(error_msg, extra={"response_body": response.text[:500]})
                else:
                    # Client error - likely permanent, don't count as circuit breaker failure
                    self._update_metrics(False, response_time)
                    self.logger.warning(error_msg, extra={"response_body": response.text[:500]})

                response.raise_for_status()

            # If we get here, request was successful
            self._update_metrics(True, response_time)
            return response

        except self.retry_config.retry_on_exceptions as e:
            response_time = time.time() - start_time
            self._update_metrics(False, response_time)
            self.logger.error(f"Request failed: {str(e)}",
                            extra={"exception_type": type(e).__name__, "url": url})
            raise
        except CircuitBreakerOpenError:
            self.logger.warning(f"Circuit breaker is OPEN for {self.__class__.__name__}")
            raise
        except HTTPError as e:
            # HTTPError was already handled and metrics updated above
            # Just re-raise without double-counting
            raise
        except Exception as e:
            response_time = time.time() - start_time
            self._update_metrics(False, response_time)
            self.logger.error(f"Unexpected error during request: {str(e)}",
                            extra={"exception_type": type(e).__name__, "url": url})
            raise

    def _update_metrics(self, success: bool, response_time: float):
        """Update request metrics."""
        now = datetime.now()
        self.metrics.total_requests += 1
        self.metrics.last_request_time = now

        if success:
            self.metrics.successful_requests += 1
            self.metrics.last_success_time = now
            self.metrics.consecutive_failures = 0
            self.metrics.consecutive_successes += 1
        else:
            self.metrics.failed_requests += 1
            self.metrics.last_failure_time = now
            self.metrics.consecutive_successes = 0
            self.metrics.consecutive_failures += 1

        # Update rolling average response time
        if self.metrics.total_requests == 1:
            self.metrics.average_response_time = response_time
        else:
            # Exponential moving average
            alpha = 0.1
            self.metrics.average_response_time = (
                alpha * response_time +
                (1 - alpha) * self.metrics.average_response_time
            )

    def get(self, endpoint: str, params: Optional[Dict[str, str]] = None,
            headers: Optional[Dict[str, str]] = None, **kwargs) -> requests.Response:
        """Make GET request."""
        return self._make_request("GET", endpoint, params=params, headers=headers, **kwargs)

    def post(self, endpoint: str, data: Optional[Dict[str, Any]] = None,
             headers: Optional[Dict[str, str]] = None, **kwargs) -> requests.Response:
        """Make POST request."""
        return self._make_request("POST", endpoint, data=data, headers=headers, **kwargs)

    def put(self, endpoint: str, data: Optional[Dict[str, Any]] = None,
            headers: Optional[Dict[str, str]] = None, **kwargs) -> requests.Response:
        """Make PUT request."""
        return self._make_request("PUT", endpoint, data=data, headers=headers, **kwargs)

    def delete(self, endpoint: str, headers: Optional[Dict[str, str]] = None,
               **kwargs) -> requests.Response:
        """Make DELETE request."""
        return self._make_request("DELETE", endpoint, headers=headers, **kwargs)

    def patch(self, endpoint: str, data: Optional[Dict[str, Any]] = None,
              headers: Optional[Dict[str, str]] = None, **kwargs) -> requests.Response:
        """Make PATCH request."""
        return self._make_request("PATCH", endpoint, data=data, headers=headers, **kwargs)

    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on the service.

        Returns:
            Health status information
        """
        pass

    def get_health_status(self) -> HealthStatus:
        """Get current health status."""
        return self.health_status

    def get_metrics(self) -> Dict[str, Any]:
        """Get current client metrics."""
        success_rate = 0.0
        if self.metrics.total_requests > 0:
            success_rate = (self.metrics.successful_requests / self.metrics.total_requests) * 100

        return {
            "total_requests": self.metrics.total_requests,
            "successful_requests": self.metrics.successful_requests,
            "failed_requests": self.metrics.failed_requests,
            "success_rate": round(success_rate, 2),
            "average_response_time": round(self.metrics.average_response_time, 3),
            "consecutive_failures": self.metrics.consecutive_failures,
            "consecutive_successes": self.metrics.consecutive_successes,
            "last_request_time": self.metrics.last_request_time.isoformat() if self.metrics.last_request_time else None,
            "last_success_time": self.metrics.last_success_time.isoformat() if self.metrics.last_success_time else None,
            "last_failure_time": self.metrics.last_failure_time.isoformat() if self.metrics.last_failure_time else None,
            "circuit_breaker_state": self.circuit_breaker.state.value,
            "health_status": self.health_status.value,
            "base_url": self.base_url
        }

    def reset_circuit_breaker(self):
        """Manually reset circuit breaker (for testing/admin purposes)."""
        self.circuit_breaker.state = CircuitState.CLOSED
        self.circuit_breaker.failure_count = 0
        self.circuit_breaker.success_count = 0
        self.logger.info("Circuit breaker manually reset")

    def close(self):
        """Close the session and clean up resources."""
        if hasattr(self, 'session'):
            self.session.close()
        self.logger.info(f"Closed {self.__class__.__name__} session")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    def __repr__(self):
        """String representation."""
        return (f"{self.__class__.__name__}(base_url='{self.base_url}', "
                f"health_status='{self.health_status.value}', "
                f"circuit_state='{self.circuit_breaker.state.value}')")