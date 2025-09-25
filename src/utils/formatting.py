"""
Data formatting utilities for Trading Dashboard.

This module provides comprehensive data formatting capabilities for financial data,
timestamps, currencies, percentages, and other common trading data types.
"""

import re
from typing import Union, Optional, Dict, Any, List
from datetime import datetime, timezone, timedelta
from decimal import Decimal, ROUND_HALF_UP
import locale
from enum import Enum


class CurrencyFormat(Enum):
    """Currency formatting options."""
    SYMBOL_BEFORE = "symbol_before"    # $1,234.56
    SYMBOL_AFTER = "symbol_after"      # 1,234.56 USD
    CODE_BEFORE = "code_before"        # USD 1,234.56
    CODE_AFTER = "code_after"          # 1,234.56 USD


class NumberFormat(Enum):
    """Number formatting options."""
    STANDARD = "standard"              # 1,234.56
    SCIENTIFIC = "scientific"          # 1.23e+3
    COMPACT = "compact"                # 1.2K
    PERCENTAGE = "percentage"          # 12.34%


class DataFormatter:
    """
    Comprehensive data formatting utility for trading applications.

    Provides methods for formatting currencies, percentages, numbers,
    timestamps, and other financial data types.
    """

    # Currency symbols mapping
    CURRENCY_SYMBOLS = {
        'USD': '$', 'EUR': '€', 'GBP': '£', 'JPY': '¥',
        'CHF': '₣', 'CAD': 'C$', 'AUD': 'A$', 'CNY': '¥',
        'INR': '₹', 'KRW': '₩', 'BRL': 'R$', 'MXN': '$',
        'RUB': '₽', 'ZAR': 'R', 'SGD': 'S$', 'HKD': 'HK$',
        'BTC': '₿', 'ETH': 'Ξ'
    }

    # Number suffixes for compact formatting
    NUMBER_SUFFIXES = [
        (1_000_000_000_000, 'T'),  # Trillion
        (1_000_000_000, 'B'),      # Billion
        (1_000_000, 'M'),          # Million
        (1_000, 'K')               # Thousand
    ]

    def __init__(self, locale_name: Optional[str] = None):
        """
        Initialize data formatter.

        Args:
            locale_name: Locale name for number formatting (e.g., 'en_US', 'de_DE')
        """
        self.locale_name = locale_name
        if locale_name:
            try:
                locale.setlocale(locale.LC_ALL, locale_name)
            except locale.Error:
                # Fall back to default locale if specified locale is not available
                pass

    @staticmethod
    def format_currency(amount: Union[int, float, Decimal, str],
                       currency: str = 'USD',
                       format_type: CurrencyFormat = CurrencyFormat.SYMBOL_BEFORE,
                       decimal_places: int = 2,
                       show_sign: bool = False,
                       compact: bool = False) -> str:
        """
        Format monetary amount with currency.

        Args:
            amount: Amount to format
            currency: Currency code (e.g., 'USD', 'EUR')
            format_type: Currency format style
            decimal_places: Number of decimal places
            show_sign: Whether to show positive sign
            compact: Whether to use compact notation (1.2K, 1.3M, etc.)

        Returns:
            Formatted currency string
        """
        try:
            # Convert to Decimal for precise calculations
            if isinstance(amount, str):
                decimal_amount = Decimal(amount)
            else:
                decimal_amount = Decimal(str(amount))

            # Handle compact formatting
            if compact:
                formatted_number = DataFormatter._format_compact_number(float(decimal_amount))
            else:
                # Round to specified decimal places
                rounded_amount = decimal_amount.quantize(
                    Decimal('0.1') ** decimal_places,
                    rounding=ROUND_HALF_UP
                )
                formatted_number = f"{rounded_amount:,.{decimal_places}f}"

            # Add positive sign if requested
            if show_sign and decimal_amount > 0:
                formatted_number = f"+{formatted_number}"

            # Get currency symbol
            currency_symbol = DataFormatter.CURRENCY_SYMBOLS.get(currency.upper(), currency.upper())

            # Apply formatting based on format type
            if format_type == CurrencyFormat.SYMBOL_BEFORE:
                return f"{currency_symbol}{formatted_number}"
            elif format_type == CurrencyFormat.SYMBOL_AFTER:
                return f"{formatted_number} {currency_symbol}"
            elif format_type == CurrencyFormat.CODE_BEFORE:
                return f"{currency.upper()} {formatted_number}"
            else:  # CODE_AFTER
                return f"{formatted_number} {currency.upper()}"

        except (ValueError, TypeError, Decimal.InvalidOperation):
            return str(amount)  # Return original if formatting fails

    @staticmethod
    def format_percentage(value: Union[int, float, Decimal, str],
                         decimal_places: int = 2,
                         show_sign: bool = False,
                         multiply_by_100: bool = True) -> str:
        """
        Format value as percentage.

        Args:
            value: Value to format as percentage
            decimal_places: Number of decimal places
            show_sign: Whether to show positive sign
            multiply_by_100: Whether to multiply by 100 (0.5 -> 50%)

        Returns:
            Formatted percentage string
        """
        try:
            if isinstance(value, str):
                decimal_value = Decimal(value)
            else:
                decimal_value = Decimal(str(value))

            # Multiply by 100 if needed
            if multiply_by_100:
                decimal_value *= 100

            # Round to specified decimal places
            rounded_value = decimal_value.quantize(
                Decimal('0.1') ** decimal_places,
                rounding=ROUND_HALF_UP
            )

            # Format with commas for large numbers
            formatted_number = f"{rounded_value:,.{decimal_places}f}"

            # Add positive sign if requested
            if show_sign and decimal_value > 0:
                formatted_number = f"+{formatted_number}"

            return f"{formatted_number}%"

        except (ValueError, TypeError, Decimal.InvalidOperation):
            return f"{value}%"

    @staticmethod
    def format_number(value: Union[int, float, Decimal, str],
                     decimal_places: Optional[int] = None,
                     format_type: NumberFormat = NumberFormat.STANDARD,
                     show_sign: bool = False) -> str:
        """
        Format number with various formatting options.

        Args:
            value: Number to format
            decimal_places: Number of decimal places (None for auto)
            format_type: Number formatting style
            show_sign: Whether to show positive sign

        Returns:
            Formatted number string
        """
        try:
            if isinstance(value, str):
                float_value = float(value)
            else:
                float_value = float(value)

            # Handle different format types
            if format_type == NumberFormat.SCIENTIFIC:
                if decimal_places is not None:
                    formatted = f"{float_value:.{decimal_places}e}"
                else:
                    formatted = f"{float_value:e}"
            elif format_type == NumberFormat.COMPACT:
                formatted = DataFormatter._format_compact_number(float_value)
            elif format_type == NumberFormat.PERCENTAGE:
                return DataFormatter.format_percentage(float_value, decimal_places or 2, show_sign)
            else:  # STANDARD
                if decimal_places is not None:
                    formatted = f"{float_value:,.{decimal_places}f}"
                else:
                    # Auto-detect decimal places
                    if float_value.is_integer():
                        formatted = f"{int(float_value):,}"
                    else:
                        formatted = f"{float_value:,}"

            # Add positive sign if requested
            if show_sign and float_value > 0:
                formatted = f"+{formatted}"

            return formatted

        except (ValueError, TypeError):
            return str(value)

    @staticmethod
    def _format_compact_number(value: float) -> str:
        """Format number in compact notation (1.2K, 1.5M, etc.)."""
        abs_value = abs(value)
        sign = '-' if value < 0 else ''

        for threshold, suffix in DataFormatter.NUMBER_SUFFIXES:
            if abs_value >= threshold:
                compact_value = abs_value / threshold
                if compact_value >= 10:
                    return f"{sign}{compact_value:.1f}{suffix}"
                else:
                    return f"{sign}{compact_value:.2f}{suffix}"

        # For numbers less than 1000
        if abs_value >= 1:
            return f"{sign}{abs_value:.2f}"
        else:
            return f"{sign}{abs_value:.4f}"

    @staticmethod
    def format_timestamp(timestamp: Union[datetime, int, float, str],
                        format_string: str = "%Y-%m-%d %H:%M:%S",
                        timezone_info: Optional[timezone] = None,
                        relative: bool = False) -> str:
        """
        Format timestamp with various options.

        Args:
            timestamp: Timestamp to format
            format_string: Format string for datetime formatting
            timezone_info: Timezone for conversion
            relative: Whether to show relative time (e.g., "2 hours ago")

        Returns:
            Formatted timestamp string
        """
        try:
            # Convert to datetime object
            if isinstance(timestamp, datetime):
                dt = timestamp
            elif isinstance(timestamp, (int, float)):
                dt = datetime.fromtimestamp(timestamp)
            elif isinstance(timestamp, str):
                # Try to parse string timestamp
                try:
                    dt = datetime.fromisoformat(timestamp)
                except ValueError:
                    # Try parsing as timestamp
                    dt = datetime.fromtimestamp(float(timestamp))
            else:
                return str(timestamp)

            # Apply timezone if specified
            if timezone_info:
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                dt = dt.astimezone(timezone_info)

            # Return relative time if requested
            if relative:
                return DataFormatter._format_relative_time(dt)

            # Format using format string
            return dt.strftime(format_string)

        except (ValueError, TypeError, OSError):
            return str(timestamp)

    @staticmethod
    def _format_relative_time(dt: datetime) -> str:
        """Format datetime as relative time string."""
        now = datetime.now(dt.tzinfo) if dt.tzinfo else datetime.now()
        diff = now - dt
        total_seconds = abs(diff.total_seconds())

        if total_seconds < 60:
            return "just now"
        elif total_seconds < 3600:  # Less than 1 hour
            minutes = int(total_seconds // 60)
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        elif total_seconds < 86400:  # Less than 1 day
            hours = int(total_seconds // 3600)
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        elif total_seconds < 2592000:  # Less than 30 days
            days = int(total_seconds // 86400)
            return f"{days} day{'s' if days != 1 else ''} ago"
        elif total_seconds < 31536000:  # Less than 1 year
            months = int(total_seconds // 2592000)
            return f"{months} month{'s' if months != 1 else ''} ago"
        else:
            years = int(total_seconds // 31536000)
            return f"{years} year{'s' if years != 1 else ''} ago"

    @staticmethod
    def format_duration(seconds: Union[int, float]) -> str:
        """
        Format duration in seconds to human-readable string.

        Args:
            seconds: Duration in seconds

        Returns:
            Formatted duration string (e.g., "2h 30m 15s")
        """
        try:
            total_seconds = int(abs(seconds))

            if total_seconds < 60:
                return f"{total_seconds}s"

            parts = []

            # Days
            if total_seconds >= 86400:
                days = total_seconds // 86400
                parts.append(f"{days}d")
                total_seconds %= 86400

            # Hours
            if total_seconds >= 3600:
                hours = total_seconds // 3600
                parts.append(f"{hours}h")
                total_seconds %= 3600

            # Minutes
            if total_seconds >= 60:
                minutes = total_seconds // 60
                parts.append(f"{minutes}m")
                total_seconds %= 60

            # Seconds
            if total_seconds > 0:
                parts.append(f"{total_seconds}s")

            return " ".join(parts)

        except (ValueError, TypeError):
            return str(seconds)

    @staticmethod
    def format_file_size(size_bytes: Union[int, float]) -> str:
        """
        Format file size in bytes to human-readable string.

        Args:
            size_bytes: Size in bytes

        Returns:
            Formatted file size string (e.g., "1.5 MB")
        """
        try:
            size = abs(float(size_bytes))

            if size == 0:
                return "0 B"

            units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
            unit_index = 0

            while size >= 1024 and unit_index < len(units) - 1:
                size /= 1024
                unit_index += 1

            if unit_index == 0:  # Bytes
                return f"{int(size)} {units[unit_index]}"
            else:
                return f"{size:.1f} {units[unit_index]}"

        except (ValueError, TypeError):
            return str(size_bytes)

    @staticmethod
    def format_trading_symbol(symbol: str) -> str:
        """
        Format trading symbol consistently.

        Args:
            symbol: Trading symbol to format

        Returns:
            Formatted trading symbol (uppercase, cleaned)
        """
        if not isinstance(symbol, str):
            return str(symbol)

        # Clean and format symbol
        cleaned = re.sub(r'[^A-Za-z0-9]', '', symbol.strip())
        return cleaned.upper()

    @staticmethod
    def format_price(price: Union[int, float, Decimal, str],
                    currency: str = 'USD',
                    decimal_places: Optional[int] = None) -> str:
        """
        Format price with appropriate decimal places based on value.

        Args:
            price: Price value to format
            currency: Currency code
            decimal_places: Fixed decimal places (None for auto)

        Returns:
            Formatted price string
        """
        try:
            price_value = float(price)

            # Auto-detect decimal places if not specified
            if decimal_places is None:
                if abs(price_value) >= 100:
                    decimal_places = 2
                elif abs(price_value) >= 1:
                    decimal_places = 4
                else:
                    decimal_places = 6

            return DataFormatter.format_currency(
                price_value,
                currency=currency,
                decimal_places=decimal_places,
                format_type=CurrencyFormat.SYMBOL_BEFORE
            )

        except (ValueError, TypeError):
            return str(price)

    @staticmethod
    def format_volume(volume: Union[int, float]) -> str:
        """
        Format trading volume with appropriate scaling.

        Args:
            volume: Volume value to format

        Returns:
            Formatted volume string
        """
        try:
            volume_value = float(volume)
            return DataFormatter.format_number(
                volume_value,
                format_type=NumberFormat.COMPACT
            )
        except (ValueError, TypeError):
            return str(volume)

    @staticmethod
    def format_change(current: Union[int, float], previous: Union[int, float],
                     as_percentage: bool = True, show_sign: bool = True) -> str:
        """
        Format change between two values.

        Args:
            current: Current value
            previous: Previous value
            as_percentage: Whether to format as percentage
            show_sign: Whether to show positive sign

        Returns:
            Formatted change string
        """
        try:
            current_val = float(current)
            previous_val = float(previous)

            if previous_val == 0:
                return "N/A"

            if as_percentage:
                change = ((current_val - previous_val) / previous_val)
                return DataFormatter.format_percentage(
                    change, show_sign=show_sign, multiply_by_100=True
                )
            else:
                change = current_val - previous_val
                return DataFormatter.format_number(
                    change, show_sign=show_sign
                )

        except (ValueError, TypeError, ZeroDivisionError):
            return "N/A"


# Convenience functions for common formatting operations
def format_currency(amount: Union[int, float, str], currency: str = 'USD') -> str:
    """Quick currency formatting."""
    return DataFormatter.format_currency(amount, currency)


def format_percentage(value: Union[int, float, str], decimal_places: int = 2) -> str:
    """Quick percentage formatting."""
    return DataFormatter.format_percentage(value, decimal_places)


def format_number(value: Union[int, float, str], decimal_places: int = 2) -> str:
    """Quick number formatting."""
    return DataFormatter.format_number(value, decimal_places)


def format_timestamp(timestamp: Union[datetime, int, float, str]) -> str:
    """Quick timestamp formatting."""
    return DataFormatter.format_timestamp(timestamp)


def format_price(price: Union[int, float, str], currency: str = 'USD') -> str:
    """Quick price formatting."""
    return DataFormatter.format_price(price, currency)