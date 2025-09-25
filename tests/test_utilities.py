"""
Test suite for core utilities.

Tests logging system, validation utilities, and data formatting helpers.
"""

import pytest
import tempfile
import os
import json
import logging
from datetime import datetime
from pathlib import Path
from decimal import Decimal

# Add project root to path
import sys
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.logging import (
    TradingDashboardLogger, StructuredFormatter, ColoredFormatter,
    get_logger, configure_logging
)
from src.utils.validation import (
    DataValidator, ConfigurationValidator, ValidationResult,
    sanitize_input, validate_model
)
from src.utils.formatting import (
    DataFormatter, CurrencyFormat, NumberFormat,
    format_currency, format_percentage, format_number
)


class TestLoggingSystem:
    """Test cases for logging system."""

    def test_structured_formatter(self):
        """Test structured JSON formatter."""
        formatter = StructuredFormatter()

        # Create test log record
        logger = logging.getLogger("test")
        record = logger.makeRecord(
            name="test",
            level=logging.INFO,
            fn="test.py",
            lno=10,
            msg="Test message",
            args=(),
            exc_info=None
        )

        formatted = formatter.format(record)

        # Parse JSON output
        log_data = json.loads(formatted)

        assert log_data["level"] == "INFO"
        assert log_data["message"] == "Test message"
        assert log_data["logger"] == "test"
        assert "timestamp" in log_data

    def test_colored_formatter(self):
        """Test colored console formatter."""
        formatter = ColoredFormatter(use_colors=False)  # Disable colors for testing

        logger = logging.getLogger("test")
        record = logger.makeRecord(
            name="test",
            level=logging.ERROR,
            fn="test.py",
            lno=10,
            msg="Error message",
            args=(),
            exc_info=None
        )

        formatted = formatter.format(record)
        assert "Error message" in formatted

    def test_trading_dashboard_logger(self):
        """Test main logger class."""
        with tempfile.TemporaryDirectory() as temp_dir:
            logger = TradingDashboardLogger("test_logger")

            # Test configuration without config system
            logger.configured = False
            logger.configure()

            assert logger.configured
            assert logger.logger.name == "test_logger"

    def test_get_logger_function(self):
        """Test global logger function."""
        logger = get_logger("test_function")

        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_function"


class TestValidationSystem:
    """Test cases for validation system."""

    def test_validation_result(self):
        """Test ValidationResult class."""
        # Test valid result
        result = ValidationResult(True, data="test_data")
        assert result.is_valid
        assert bool(result) is True
        assert result.data == "test_data"

        # Test invalid result
        result = ValidationResult(False, errors=["Error 1"])
        assert not result.is_valid
        assert bool(result) is False
        assert "Error 1" in result.errors

    def test_url_validation(self):
        """Test URL validation."""
        # Valid URLs
        result = DataValidator.validate_url("https://example.com")
        assert result.is_valid

        result = DataValidator.validate_url("http://localhost:8000")
        assert result.is_valid

        # Invalid URLs
        result = DataValidator.validate_url("not-a-url")
        assert not result.is_valid

        result = DataValidator.validate_url("")
        assert not result.is_valid

    def test_port_validation(self):
        """Test port validation."""
        # Valid ports
        result = DataValidator.validate_port(8080)
        assert result.is_valid
        assert result.data == 8080

        result = DataValidator.validate_port("3000")
        assert result.is_valid
        assert result.data == 3000

        # Invalid ports
        result = DataValidator.validate_port(0)
        assert not result.is_valid

        result = DataValidator.validate_port(70000)
        assert not result.is_valid

    def test_number_validation(self):
        """Test number validation."""
        # Valid numbers
        result = DataValidator.validate_number(42)
        assert result.is_valid
        assert result.data == 42

        result = DataValidator.validate_number("3.14", decimal_places=2)
        assert result.is_valid

        # Invalid numbers
        result = DataValidator.validate_number("not-a-number")
        assert not result.is_valid

        result = DataValidator.validate_number(-5, allow_negative=False)
        assert not result.is_valid

    def test_string_validation(self):
        """Test string validation."""
        # Valid strings
        result = DataValidator.validate_string("test", min_length=1, max_length=10)
        assert result.is_valid
        assert result.data == "test"

        # Invalid strings
        result = DataValidator.validate_string("", min_length=1)
        assert not result.is_valid

        result = DataValidator.validate_string("too long string", max_length=5)
        assert not result.is_valid

    def test_email_validation(self):
        """Test email validation."""
        # Valid emails
        result = DataValidator.validate_email("user@example.com")
        assert result.is_valid

        # Invalid emails
        result = DataValidator.validate_email("invalid-email")
        assert not result.is_valid

    def test_trading_symbol_validation(self):
        """Test trading symbol validation."""
        # Valid symbols
        result = DataValidator.validate_trading_symbol("AAPL")
        assert result.is_valid
        assert result.data == "AAPL"

        result = DataValidator.validate_trading_symbol("btc")
        assert result.is_valid
        assert result.data == "BTC"

        # Invalid symbols
        result = DataValidator.validate_trading_symbol("TOOLONGSTRING")
        assert not result.is_valid

    def test_datetime_validation(self):
        """Test datetime validation."""
        # Valid datetimes
        result = DataValidator.validate_datetime("2023-01-01 12:00:00")
        assert result.is_valid
        assert isinstance(result.data, datetime)

        result = DataValidator.validate_datetime(datetime.now())
        assert result.is_valid

        # Invalid datetime
        result = DataValidator.validate_datetime("invalid-date")
        assert not result.is_valid

    def test_json_validation(self):
        """Test JSON validation."""
        # Valid JSON
        result = DataValidator.validate_json('{"key": "value"}')
        assert result.is_valid
        assert result.data == {"key": "value"}

        # Invalid JSON
        result = DataValidator.validate_json('invalid json')
        assert not result.is_valid

    def test_configuration_validation(self):
        """Test configuration validation."""
        # Valid agent config
        config = {
            'name': 'Test Agent',
            'url': 'http://localhost:8000',
            'timeout': 10,
            'enabled': True
        }
        result = ConfigurationValidator.validate_agent_config(config)
        assert result.is_valid

        # Invalid agent config
        invalid_config = {
            'name': '',
            'url': 'invalid-url',
            'timeout': -1
        }
        result = ConfigurationValidator.validate_agent_config(invalid_config)
        assert not result.is_valid

    def test_input_sanitization(self):
        """Test input sanitization."""
        # Clean input
        result = sanitize_input("clean input")
        assert result == "clean input"

        # Malicious input
        result = sanitize_input("<script>alert('xss')</script>")
        assert "<script>" not in result
        assert "alert('xss')" not in result

        # Long input
        result = sanitize_input("a" * 1000, max_length=10)
        assert len(result) == 10


class TestFormattingSystem:
    """Test cases for data formatting system."""

    def test_currency_formatting(self):
        """Test currency formatting."""
        # Basic formatting
        result = DataFormatter.format_currency(1234.56, 'USD')
        assert result == "$1,234.56"

        # Different formats
        result = DataFormatter.format_currency(
            1000, 'EUR', CurrencyFormat.CODE_AFTER
        )
        assert result == "1,000.00 EUR"

        # Compact formatting
        result = DataFormatter.format_currency(
            1500000, 'USD', compact=True
        )
        assert "1.50M" in result

    def test_percentage_formatting(self):
        """Test percentage formatting."""
        # Basic percentage
        result = DataFormatter.format_percentage(0.1234)
        assert result == "12.34%"

        # No multiplication
        result = DataFormatter.format_percentage(50, multiply_by_100=False)
        assert result == "50.00%"

        # With sign
        result = DataFormatter.format_percentage(0.05, show_sign=True)
        assert result == "+5.00%"

    def test_number_formatting(self):
        """Test number formatting."""
        # Standard formatting
        result = DataFormatter.format_number(1234567.89)
        assert result == "1,234,567.89"

        # Compact formatting
        result = DataFormatter.format_number(
            1500000, format_type=NumberFormat.COMPACT
        )
        assert result == "1.50M"

        # Scientific notation
        result = DataFormatter.format_number(
            1234.5, format_type=NumberFormat.SCIENTIFIC, decimal_places=2
        )
        assert "1.23e+03" in result or "1.23e+3" in result

    def test_timestamp_formatting(self):
        """Test timestamp formatting."""
        # Datetime object
        dt = datetime(2023, 1, 1, 12, 0, 0)
        result = DataFormatter.format_timestamp(dt)
        assert "2023-01-01" in result

        # Timestamp
        result = DataFormatter.format_timestamp(1672574400)  # 2023-01-01 12:00:00 UTC
        assert "2023" in result

        # Custom format
        result = DataFormatter.format_timestamp(dt, "%Y/%m/%d")
        assert result == "2023/01/01"

    def test_duration_formatting(self):
        """Test duration formatting."""
        # Seconds
        result = DataFormatter.format_duration(30)
        assert result == "30s"

        # Minutes and seconds
        result = DataFormatter.format_duration(90)
        assert result == "1m 30s"

        # Hours, minutes, seconds
        result = DataFormatter.format_duration(3661)
        assert result == "1h 1m 1s"

        # Days
        result = DataFormatter.format_duration(90000)
        assert "1d" in result

    def test_file_size_formatting(self):
        """Test file size formatting."""
        # Bytes
        result = DataFormatter.format_file_size(512)
        assert result == "512 B"

        # Kilobytes
        result = DataFormatter.format_file_size(1536)
        assert result == "1.5 KB"

        # Megabytes
        result = DataFormatter.format_file_size(2 * 1024 * 1024)
        assert result == "2.0 MB"

    def test_price_formatting(self):
        """Test price formatting."""
        # High price
        result = DataFormatter.format_price(150.50, 'USD')
        assert "$150.50" in result

        # Low price
        result = DataFormatter.format_price(0.001234, 'BTC')
        assert "0.001234" in result

    def test_volume_formatting(self):
        """Test volume formatting."""
        result = DataFormatter.format_volume(1500000)
        assert result == "1.50M"

    def test_change_formatting(self):
        """Test change formatting."""
        # Percentage change
        result = DataFormatter.format_change(110, 100, as_percentage=True)
        assert result == "+10.00%"

        # Absolute change
        result = DataFormatter.format_change(110, 100, as_percentage=False)
        assert "+10" in result

    def test_trading_symbol_formatting(self):
        """Test trading symbol formatting."""
        result = DataFormatter.format_trading_symbol("aapl")
        assert result == "AAPL"

        result = DataFormatter.format_trading_symbol("BTC-USD")
        assert result == "BTCUSD"

    def test_convenience_functions(self):
        """Test convenience formatting functions."""
        assert format_currency(100, 'USD') == "$100.00"
        assert format_percentage(0.5) == "50.00%"
        assert "100" in format_number(100)


# Helper function to run all tests
def run_all_tests():
    """Run all utility tests."""
    pytest.main([__file__, "-v"])


if __name__ == "__main__":
    run_all_tests()