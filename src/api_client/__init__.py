"""
API Client package for Trading Dashboard.

This package provides robust HTTP client functionality for communicating
with trading agents and external APIs. Features include connection pooling,
retry logic, circuit breakers, and comprehensive error handling.
"""

from .base_client import BaseClient

__all__ = [
    'BaseClient'
]

__version__ = '1.0.0'