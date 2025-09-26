"""
Basic Tests for Trading Dashboard Models.

Simple tests to verify basic model functionality without complex validations.
"""

import pytest
from datetime import datetime, date
from typing import Dict, Any

# Test basic imports first
def test_basic_imports():
    """Test that we can import basic models."""
    try:
        from src.models.api_responses import BaseResponse, ResponseStatus
        assert True
    except ImportError as e:
        pytest.fail(f"Failed to import basic models: {e}")

def test_base_response_creation():
    """Test basic response model creation."""
    from src.models.api_responses import BaseResponse, ResponseStatus

    response = BaseResponse()
    assert response.status == ResponseStatus.SUCCESS
    assert isinstance(response.timestamp, datetime)

def test_enum_values():
    """Test enum values are working."""
    from src.models.api_responses import ResponseStatus, AgentType, HealthStatus

    assert ResponseStatus.SUCCESS == "success"
    assert ResponseStatus.ERROR == "error"
    assert AgentType.MARKET_DATA == "market_data"
    assert HealthStatus.HEALTHY == "healthy"

if __name__ == "__main__":
    # Run the tests
    test_basic_imports()
    test_base_response_creation()
    test_enum_values()
    print("✅ Basic model tests passed!")