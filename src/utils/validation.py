"""
Validation utilities for Trading Dashboard.

This module provides comprehensive data validation, input sanitization,
and data type validation helpers for the trading dashboard system.
"""

import re
import ipaddress
from typing import Any, Dict, List, Optional, Union, Callable, Type
from urllib.parse import urlparse
from pathlib import Path
import json
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pydantic import BaseModel, ValidationError, validator


class ValidationError(Exception):
    """Custom validation error."""
    pass


class ValidationResult:
    """Result of validation operation."""

    def __init__(self, is_valid: bool, errors: Optional[List[str]] = None,
                 warnings: Optional[List[str]] = None, data: Any = None):
        """
        Initialize validation result.

        Args:
            is_valid: Whether validation passed
            errors: List of validation errors
            warnings: List of validation warnings
            data: Validated/cleaned data
        """
        self.is_valid = is_valid
        self.errors = errors or []
        self.warnings = warnings or []
        self.data = data

    def __bool__(self) -> bool:
        """Return True if validation passed."""
        return self.is_valid

    def add_error(self, error: str) -> None:
        """Add validation error."""
        self.errors.append(error)
        self.is_valid = False

    def add_warning(self, warning: str) -> None:
        """Add validation warning."""
        self.warnings.append(warning)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "is_valid": self.is_valid,
            "errors": self.errors,
            "warnings": self.warnings,
            "data": self.data
        }


class DataValidator:
    """
    Comprehensive data validation utility.

    Provides methods for validating various types of data commonly used
    in trading applications including URLs, numbers, dates, etc.
    """

    # Common regex patterns
    PATTERNS = {
        "email": re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'),
        "phone": re.compile(r'^\+?[\d\s\-\(\)]{10,}$'),
        "symbol": re.compile(r'^[A-Z]{1,10}$'),  # Trading symbol
        "currency": re.compile(r'^[A-Z]{3}$'),   # Currency code
        "percentage": re.compile(r'^\d+(\.\d+)?%$'),
    }

    @staticmethod
    def validate_url(url: str, schemes: Optional[List[str]] = None) -> ValidationResult:
        """
        Validate URL format and scheme.

        Args:
            url: URL to validate
            schemes: Allowed schemes (default: ['http', 'https'])

        Returns:
            ValidationResult with validation status
        """
        if schemes is None:
            schemes = ['http', 'https']

        result = ValidationResult(True, data=url)

        if not isinstance(url, str):
            result.add_error("URL must be a string")
            return result

        if not url.strip():
            result.add_error("URL cannot be empty")
            return result

        try:
            parsed = urlparse(url)

            if not parsed.scheme:
                result.add_error("URL must include a scheme (http/https)")
            elif parsed.scheme.lower() not in [s.lower() for s in schemes]:
                result.add_error(f"URL scheme must be one of: {', '.join(schemes)}")

            if not parsed.netloc:
                result.add_error("URL must include a hostname")

            # Clean and normalize URL
            if result.is_valid:
                cleaned_url = f"{parsed.scheme}://{parsed.netloc}"
                if parsed.path and parsed.path != '/':
                    cleaned_url += parsed.path
                if parsed.query:
                    cleaned_url += f"?{parsed.query}"
                result.data = cleaned_url

        except Exception as e:
            result.add_error(f"Invalid URL format: {str(e)}")

        return result

    @staticmethod
    def validate_port(port: Union[int, str]) -> ValidationResult:
        """
        Validate network port number.

        Args:
            port: Port number to validate

        Returns:
            ValidationResult with validation status
        """
        result = ValidationResult(True)

        try:
            port_int = int(port)
            if port_int < 1 or port_int > 65535:
                result.add_error("Port must be between 1 and 65535")
            else:
                result.data = port_int
        except (ValueError, TypeError):
            result.add_error("Port must be a valid integer")

        return result

    @staticmethod
    def validate_ip_address(ip: str, allow_private: bool = True) -> ValidationResult:
        """
        Validate IP address format.

        Args:
            ip: IP address to validate
            allow_private: Whether to allow private IP addresses

        Returns:
            ValidationResult with validation status
        """
        result = ValidationResult(True, data=ip)

        if not isinstance(ip, str):
            result.add_error("IP address must be a string")
            return result

        try:
            ip_obj = ipaddress.ip_address(ip)

            if not allow_private and ip_obj.is_private:
                result.add_warning("IP address is private")

            result.data = str(ip_obj)

        except ipaddress.AddressValueError as e:
            result.add_error(f"Invalid IP address format: {str(e)}")

        return result

    @staticmethod
    def validate_number(value: Any, min_value: Optional[Union[int, float]] = None,
                       max_value: Optional[Union[int, float]] = None,
                       allow_negative: bool = True,
                       decimal_places: Optional[int] = None) -> ValidationResult:
        """
        Validate numeric value with optional constraints.

        Args:
            value: Value to validate
            min_value: Minimum allowed value
            max_value: Maximum allowed value
            allow_negative: Whether to allow negative values
            decimal_places: Maximum decimal places allowed

        Returns:
            ValidationResult with validation status
        """
        result = ValidationResult(True)

        try:
            # Convert to appropriate numeric type
            if isinstance(value, str):
                if '.' in value or 'e' in value.lower():
                    num_value = float(value)
                else:
                    num_value = int(value)
            elif isinstance(value, (int, float, Decimal)):
                num_value = float(value) if isinstance(value, (float, Decimal)) else value
            else:
                result.add_error("Value must be a number")
                return result

            # Validate constraints
            if not allow_negative and num_value < 0:
                result.add_error("Negative values not allowed")

            if min_value is not None and num_value < min_value:
                result.add_error(f"Value must be >= {min_value}")

            if max_value is not None and num_value > max_value:
                result.add_error(f"Value must be <= {max_value}")

            # Validate decimal places
            if decimal_places is not None and isinstance(num_value, float):
                str_value = f"{num_value:.10f}".rstrip('0')
                if '.' in str_value:
                    actual_decimals = len(str_value.split('.')[1])
                    if actual_decimals > decimal_places:
                        result.add_error(f"Maximum {decimal_places} decimal places allowed")

            if result.is_valid:
                result.data = num_value

        except (ValueError, TypeError, InvalidOperation) as e:
            result.add_error(f"Invalid number format: {str(e)}")

        return result

    @staticmethod
    def validate_string(value: Any, min_length: Optional[int] = None,
                       max_length: Optional[int] = None,
                       pattern: Optional[str] = None,
                       allowed_chars: Optional[str] = None,
                       strip_whitespace: bool = True) -> ValidationResult:
        """
        Validate string value with optional constraints.

        Args:
            value: Value to validate
            min_length: Minimum string length
            max_length: Maximum string length
            pattern: Regex pattern to match
            allowed_chars: String of allowed characters
            strip_whitespace: Whether to strip whitespace

        Returns:
            ValidationResult with validation status
        """
        result = ValidationResult(True)

        if not isinstance(value, str):
            result.add_error("Value must be a string")
            return result

        # Clean string
        cleaned = value.strip() if strip_whitespace else value
        result.data = cleaned

        # Validate length
        if min_length is not None and len(cleaned) < min_length:
            result.add_error(f"String must be at least {min_length} characters")

        if max_length is not None and len(cleaned) > max_length:
            result.add_error(f"String must be no more than {max_length} characters")

        # Validate pattern
        if pattern and not re.match(pattern, cleaned):
            result.add_error("String does not match required pattern")

        # Validate allowed characters
        if allowed_chars:
            invalid_chars = set(cleaned) - set(allowed_chars)
            if invalid_chars:
                result.add_error(f"Contains invalid characters: {', '.join(invalid_chars)}")

        return result

    @staticmethod
    def validate_email(email: str) -> ValidationResult:
        """Validate email address format."""
        return DataValidator.validate_string(
            email,
            min_length=5,
            max_length=254,
            pattern=DataValidator.PATTERNS["email"].pattern
        )

    @staticmethod
    def validate_trading_symbol(symbol: str) -> ValidationResult:
        """Validate trading symbol format."""
        # Convert to uppercase first for validation
        upper_symbol = symbol.upper() if isinstance(symbol, str) else symbol

        result = DataValidator.validate_string(
            upper_symbol,
            min_length=1,
            max_length=10,
            pattern=DataValidator.PATTERNS["symbol"].pattern
        )

        return result

    @staticmethod
    def validate_currency_code(code: str) -> ValidationResult:
        """Validate currency code format (ISO 4217)."""
        result = DataValidator.validate_string(
            code,
            min_length=3,
            max_length=3,
            pattern=DataValidator.PATTERNS["currency"].pattern
        )

        if result.is_valid:
            result.data = result.data.upper()

        return result

    @staticmethod
    def validate_datetime(value: Any, format_string: Optional[str] = None) -> ValidationResult:
        """
        Validate datetime value.

        Args:
            value: Value to validate (string, datetime, or timestamp)
            format_string: Expected datetime format string

        Returns:
            ValidationResult with validation status
        """
        result = ValidationResult(True)

        try:
            if isinstance(value, datetime):
                result.data = value
            elif isinstance(value, str):
                if format_string:
                    result.data = datetime.strptime(value, format_string)
                else:
                    # Try common formats
                    formats = [
                        "%Y-%m-%d %H:%M:%S",
                        "%Y-%m-%d",
                        "%Y-%m-%dT%H:%M:%S",
                        "%Y-%m-%dT%H:%M:%SZ"
                    ]
                    parsed = None
                    for fmt in formats:
                        try:
                            parsed = datetime.strptime(value, fmt)
                            break
                        except ValueError:
                            continue

                    if parsed:
                        result.data = parsed
                    else:
                        result.add_error("Unable to parse datetime string")
            elif isinstance(value, (int, float)):
                result.data = datetime.fromtimestamp(value)
            else:
                result.add_error("Datetime must be string, datetime object, or timestamp")

        except (ValueError, TypeError, OverflowError) as e:
            result.add_error(f"Invalid datetime: {str(e)}")

        return result

    @staticmethod
    def validate_json(value: str) -> ValidationResult:
        """
        Validate JSON string.

        Args:
            value: JSON string to validate

        Returns:
            ValidationResult with parsed JSON data
        """
        result = ValidationResult(True)

        if not isinstance(value, str):
            result.add_error("JSON must be a string")
            return result

        try:
            result.data = json.loads(value)
        except json.JSONDecodeError as e:
            result.add_error(f"Invalid JSON format: {str(e)}")

        return result

    @staticmethod
    def validate_file_path(path: Union[str, Path], must_exist: bool = False,
                          must_be_file: bool = False, must_be_dir: bool = False) -> ValidationResult:
        """
        Validate file path.

        Args:
            path: File path to validate
            must_exist: Whether path must exist
            must_be_file: Whether path must be a file
            must_be_dir: Whether path must be a directory

        Returns:
            ValidationResult with validation status
        """
        result = ValidationResult(True)

        try:
            path_obj = Path(path)
            result.data = path_obj

            if must_exist and not path_obj.exists():
                result.add_error("Path does not exist")

            if must_be_file and path_obj.exists() and not path_obj.is_file():
                result.add_error("Path is not a file")

            if must_be_dir and path_obj.exists() and not path_obj.is_dir():
                result.add_error("Path is not a directory")

        except (TypeError, ValueError) as e:
            result.add_error(f"Invalid path: {str(e)}")

        return result


class ConfigurationValidator:
    """Specialized validator for configuration data."""

    @staticmethod
    def validate_agent_config(config: Dict[str, Any]) -> ValidationResult:
        """
        Validate agent configuration.

        Args:
            config: Agent configuration dictionary

        Returns:
            ValidationResult with validation status
        """
        result = ValidationResult(True, data=config.copy())

        # Required fields
        required_fields = ['name', 'url', 'timeout', 'enabled']
        for field in required_fields:
            if field not in config:
                result.add_error(f"Missing required field: {field}")

        if not result.is_valid:
            return result

        # Validate individual fields
        name_result = DataValidator.validate_string(config['name'], min_length=1, max_length=100)
        if not name_result:
            result.add_error(f"Invalid name: {', '.join(name_result.errors)}")

        url_result = DataValidator.validate_url(config['url'])
        if not url_result:
            result.add_error(f"Invalid URL: {', '.join(url_result.errors)}")

        timeout_result = DataValidator.validate_number(config['timeout'], min_value=1, max_value=300)
        if not timeout_result:
            result.add_error(f"Invalid timeout: {', '.join(timeout_result.errors)}")

        if not isinstance(config['enabled'], bool):
            result.add_error("Enabled field must be boolean")

        return result

    @staticmethod
    def validate_dashboard_config(config: Dict[str, Any]) -> ValidationResult:
        """
        Validate dashboard configuration.

        Args:
            config: Dashboard configuration dictionary

        Returns:
            ValidationResult with validation status
        """
        result = ValidationResult(True, data=config.copy())

        # Validate port
        if 'port' in config:
            port_result = DataValidator.validate_port(config['port'])
            if not port_result:
                result.add_error(f"Invalid port: {', '.join(port_result.errors)}")

        # Validate refresh interval
        if 'refresh_interval' in config:
            interval_result = DataValidator.validate_number(
                config['refresh_interval'], min_value=1, max_value=300
            )
            if not interval_result:
                result.add_error(f"Invalid refresh interval: {', '.join(interval_result.errors)}")

        return result


def sanitize_input(value: str, max_length: Optional[int] = None) -> str:
    """
    Sanitize user input by removing potentially harmful content.

    Args:
        value: Input string to sanitize
        max_length: Maximum allowed length

    Returns:
        Sanitized string
    """
    if not isinstance(value, str):
        return ""

    # Remove potentially harmful characters
    sanitized = re.sub(r'[<>"\'\x00-\x1f\x7f-\x9f]', '', value)

    # Strip whitespace
    sanitized = sanitized.strip()

    # Limit length
    if max_length and len(sanitized) > max_length:
        sanitized = sanitized[:max_length]

    return sanitized


def validate_model(model_class: Type[BaseModel], data: Dict[str, Any]) -> ValidationResult:
    """
    Validate data against Pydantic model.

    Args:
        model_class: Pydantic model class
        data: Data to validate

    Returns:
        ValidationResult with validation status
    """
    result = ValidationResult(True)

    try:
        validated_model = model_class(**data)
        result.data = validated_model
    except ValidationError as e:
        for error in e.errors():
            field = '.'.join(str(loc) for loc in error['loc'])
            result.add_error(f"{field}: {error['msg']}")

    return result