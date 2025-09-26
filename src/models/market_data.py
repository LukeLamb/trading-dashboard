"""
Market Data Models for Trading Dashboard.

This module provides specialized Pydantic models for market data operations,
extending the base models with trading-specific functionality and validation.
"""

from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple
from enum import Enum
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator, model_validator
import re

from .api_responses import BaseResponse, QualityGrade, ResponseStatus


class MarketType(str, Enum):
    """Types of financial markets."""
    EQUITY = "equity"
    FOREX = "forex"
    CRYPTO = "crypto"
    COMMODITY = "commodity"
    BOND = "bond"
    INDEX = "index"
    OPTION = "option"
    FUTURE = "future"


class PriceType(str, Enum):
    """Types of price data."""
    REAL_TIME = "real_time"
    DELAYED = "delayed"
    END_OF_DAY = "end_of_day"
    HISTORICAL = "historical"


class TradingSession(str, Enum):
    """Trading session indicators."""
    PRE_MARKET = "pre_market"
    REGULAR = "regular"
    AFTER_HOURS = "after_hours"
    CLOSED = "closed"


class DataSource(str, Enum):
    """Available data sources."""
    YFINANCE = "yfinance"
    ALPHA_VANTAGE = "alpha_vantage"
    IEX_CLOUD = "iex_cloud"
    POLYGON = "polygon"
    FINNHUB = "finnhub"
    TWELVE_DATA = "twelve_data"
    BLOOMBERG = "bloomberg"
    REUTERS = "reuters"


class TimeFrame(str, Enum):
    """Time frames for historical data."""
    ONE_MINUTE = "1m"
    FIVE_MINUTES = "5m"
    FIFTEEN_MINUTES = "15m"
    THIRTY_MINUTES = "30m"
    ONE_HOUR = "1h"
    FOUR_HOURS = "4h"
    ONE_DAY = "1d"
    ONE_WEEK = "1w"
    ONE_MONTH = "1M"


# Base Market Data Models

class TradingSymbol(BaseModel):
    """Trading symbol with metadata."""
    symbol: str
    name: Optional[str] = None
    market_type: Optional[MarketType] = None
    exchange: Optional[str] = None
    currency: Optional[str] = None
    country: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    is_active: bool = True

    @field_validator('symbol')
    @classmethod
    def validate_symbol(cls, v):
        if not v or not v.strip():
            raise ValueError('Symbol cannot be empty')

        # Clean and validate symbol format
        symbol = v.strip().upper()

        # Basic symbol validation (alphanumeric with some special chars)
        if not re.match(r'^[A-Z0-9._-]+$', symbol):
            raise ValueError('Symbol contains invalid characters')

        if len(symbol) > 12:  # Most symbols are under 12 characters
            raise ValueError('Symbol too long')

        return symbol

    @field_validator('currency')
    @classmethod
    def validate_currency(cls, v):
        if v is not None:
            currency = v.strip().upper()
            if len(currency) != 3:
                raise ValueError('Currency must be 3-character ISO code')
            return currency
        return v


class MarketQuote(BaseModel):
    """Real-time market quote."""
    symbol: str
    price: Decimal = Field(decimal_places=4)
    bid: Optional[Decimal] = Field(None, decimal_places=4)
    ask: Optional[Decimal] = Field(None, decimal_places=4)
    bid_size: Optional[int] = None
    ask_size: Optional[int] = None
    volume: Optional[int] = None
    timestamp: datetime
    price_type: PriceType = PriceType.REAL_TIME
    trading_session: TradingSession = TradingSession.REGULAR
    source: DataSource
    quality_score: int = Field(default=100, ge=0, le=100)
    quality_grade: QualityGrade = QualityGrade.A
    market_cap: Optional[Decimal] = None
    pe_ratio: Optional[Decimal] = None
    day_change: Optional[Decimal] = None
    day_change_percent: Optional[Decimal] = None
    day_high: Optional[Decimal] = None
    day_low: Optional[Decimal] = None
    day_open: Optional[Decimal] = None
    previous_close: Optional[Decimal] = None
    week_52_high: Optional[Decimal] = None
    week_52_low: Optional[Decimal] = None

    @field_validator('symbol')
    @classmethod
    def validate_symbol(cls, v):
        # Reuse validation logic from TradingSymbol
        if not v or not v.strip():
            raise ValueError('Symbol cannot be empty')

        symbol = v.strip().upper()
        if not re.match(r'^[A-Z0-9._-]+$', symbol):
            raise ValueError('Symbol contains invalid characters')

        if len(symbol) > 12:
            raise ValueError('Symbol too long')

        return symbol

    @field_validator('price')
    @classmethod
    def validate_price(cls, v):
        if v <= 0:
            raise ValueError('Price must be positive')
        return v

    @field_validator('volume', 'bid_size', 'ask_size')
    @classmethod
    def validate_sizes(cls, v):
        if v is not None and v < 0:
            raise ValueError('Volume and sizes cannot be negative')
        return v

    @model_validator(mode='after')
    def validate_bid_ask_spread(self):
        bid = self.bid
        ask = self.ask
        price = self.price

        if bid and ask:
            if bid >= ask:
                raise ValueError('Bid must be less than ask')

            # Price should be within bid-ask spread or close to it
            if price and (price < bid * Decimal('0.95') or price > ask * Decimal('1.05')):
                raise ValueError('Price significantly outside bid-ask spread')

        return self


class OHLCVBar(BaseModel):
    """OHLCV (Open, High, Low, Close, Volume) bar data."""
    symbol: str
    timestamp: datetime
    timeframe: TimeFrame
    open: Decimal = Field(decimal_places=4)
    high: Decimal = Field(decimal_places=4)
    low: Decimal = Field(decimal_places=4)
    close: Decimal = Field(decimal_places=4)
    volume: int = 0
    adjusted_close: Optional[Decimal] = Field(None, decimal_places=4)
    dividend_amount: Optional[Decimal] = Field(None, decimal_places=4)
    split_coefficient: Optional[Decimal] = Field(None, decimal_places=2)
    source: DataSource
    quality_score: int = Field(default=100, ge=0, le=100)
    quality_grade: QualityGrade = QualityGrade.A

    @field_validator('symbol')
    @classmethod
    def validate_symbol(cls, v):
        # Reuse validation logic from TradingSymbol
        if not v or not v.strip():
            raise ValueError('Symbol cannot be empty')

        symbol = v.strip().upper()
        if not re.match(r'^[A-Z0-9._-]+$', symbol):
            raise ValueError('Symbol contains invalid characters')

        if len(symbol) > 12:
            raise ValueError('Symbol too long')

        return symbol

    @field_validator('open', 'high', 'low', 'close')
    @classmethod
    def validate_prices(cls, v):
        if v <= 0:
            raise ValueError('Prices must be positive')
        return v

    @field_validator('volume')
    @classmethod
    def validate_volume(cls, v):
        if v < 0:
            raise ValueError('Volume cannot be negative')
        return v

    @model_validator(mode='after')
    def validate_ohlc_relationships(self):
        open_price = self.open
        high = self.high
        low = self.low
        close = self.close

        if all(v is not None for v in [open_price, high, low, close]):
            # High should be the highest price
            if high < max(open_price, close):
                raise ValueError('High must be >= max(open, close)')

            # Low should be the lowest price
            if low > min(open_price, close):
                raise ValueError('Low must be <= min(open, close)')

            # Basic sanity check: high >= low
            if high < low:
                raise ValueError('High must be >= low')

        return self


class MarketDataRequest(BaseModel):
    """Request model for market data."""
    symbols: List[str]
    fields: List[str] = Field(default_factory=lambda: ['price', 'volume'])
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    timeframe: TimeFrame = TimeFrame.ONE_DAY
    limit: Optional[int] = Field(None, gt=0, le=10000)
    source_preference: List[DataSource] = Field(default_factory=list)
    quality_threshold: int = Field(default=70, ge=0, le=100)
    cache_ttl_seconds: int = Field(default=60, ge=0, le=3600)

    @field_validator('symbols')
    @classmethod
    def validate_symbols(cls, v):
        if not v:
            raise ValueError('At least one symbol is required')

        validated_symbols = []
        for symbol in v:
            # Reuse validation logic from TradingSymbol
            if not symbol or not symbol.strip():
                raise ValueError('Symbol cannot be empty')
            clean_symbol = symbol.strip().upper()
            if not re.match(r'^[A-Z0-9._-]+$', clean_symbol):
                raise ValueError('Symbol contains invalid characters')
            if len(clean_symbol) > 12:
                raise ValueError('Symbol too long')
            validated_symbols.append(clean_symbol)

        # Remove duplicates while preserving order
        return list(dict.fromkeys(validated_symbols))

    @field_validator('fields')
    @classmethod
    def validate_fields(cls, v):
        if not v:
            raise ValueError('At least one field is required')

        valid_fields = [
            'price', 'volume', 'bid', 'ask', 'open', 'high', 'low', 'close',
            'market_cap', 'pe_ratio', 'dividend_yield', 'beta'
        ]

        for field in v:
            if field not in valid_fields:
                raise ValueError(f'Invalid field: {field}. Valid fields: {valid_fields}')

        return v

    @model_validator(mode='after')
    def validate_date_range(self):
        start_date = self.start_date
        end_date = self.end_date

        if start_date and end_date:
            if start_date > end_date:
                raise ValueError('Start date must be before end date')

            if start_date > date.today():
                raise ValueError('Start date cannot be in the future')

            # Reasonable date range limit (10 years)
            if (date.today() - start_date).days > 3650:
                raise ValueError('Date range too large (max 10 years)')

        return self


class MarketDataResponse(BaseResponse):
    """Response model for market data requests."""
    symbols_requested: List[str]
    symbols_returned: List[str]
    data_points: int = 0
    quotes: List[MarketQuote] = Field(default_factory=list)
    historical_data: Dict[str, List[OHLCVBar]] = Field(default_factory=dict)
    quality_summary: Dict[str, Any] = Field(default_factory=dict)
    source_breakdown: Dict[DataSource, int] = Field(default_factory=dict)
    cache_info: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode='after')
    def validate_response_data(self):
        quotes = self.quotes
        historical_data = self.historical_data

        total_points = len(quotes)
        for symbol_data in historical_data.values():
            total_points += len(symbol_data)

        self.data_points = total_points

        # Extract returned symbols
        returned_symbols = set()
        for quote in quotes:
            returned_symbols.add(quote.symbol)
        for symbol in historical_data.keys():
            returned_symbols.add(symbol)

        self.symbols_returned = list(returned_symbols)

        return self


# Data Quality Models

class DataQualityMetrics(BaseModel):
    """Data quality metrics for market data."""
    symbol: str
    source: DataSource
    completeness: float = Field(ge=0.0, le=1.0)  # % of expected data points
    accuracy: float = Field(ge=0.0, le=1.0)      # % of accurate data points
    timeliness: float = Field(ge=0.0, le=1.0)    # % of timely updates
    consistency: float = Field(ge=0.0, le=1.0)   # % consistent with other sources
    validity: float = Field(ge=0.0, le=1.0)      # % of valid data format
    freshness: float = Field(ge=0.0, le=1.0)     # Age-based freshness score
    overall_score: float = Field(default=0.0, ge=0.0, le=100.0)
    overall_grade: QualityGrade = QualityGrade.F
    issues_detected: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    assessment_timestamp: datetime = Field(default_factory=datetime.now)

    @field_validator('symbol')
    @classmethod
    def validate_symbol(cls, v):
        # Reuse validation logic from TradingSymbol
        if not v or not v.strip():
            raise ValueError('Symbol cannot be empty')

        symbol = v.strip().upper()
        if not re.match(r'^[A-Z0-9._-]+$', symbol):
            raise ValueError('Symbol contains invalid characters')

        if len(symbol) > 12:
            raise ValueError('Symbol too long')

        return symbol

    @model_validator(mode='after')
    def calculate_overall_score(self):
        # Calculate weighted average of quality dimensions
        weights = {
            'completeness': 0.25,
            'accuracy': 0.30,
            'timeliness': 0.20,
            'consistency': 0.15,
            'validity': 0.10
        }

        total_score = 0.0
        for dimension, weight in weights.items():
            dimension_score = getattr(self, dimension, 0.0)
            total_score += dimension_score * weight

        # Convert to 0-100 scale
        overall_score = total_score * 100
        self.overall_score = overall_score

        # Determine grade
        if overall_score >= 90:
            grade = QualityGrade.A
        elif overall_score >= 80:
            grade = QualityGrade.B
        elif overall_score >= 70:
            grade = QualityGrade.C
        elif overall_score >= 60:
            grade = QualityGrade.D
        else:
            grade = QualityGrade.F

        self.overall_grade = grade

        return self


class DataSourceHealth(BaseModel):
    """Health status for a data source."""
    source: DataSource
    is_operational: bool = False
    response_time_ms: float = 0.0
    success_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    rate_limit_remaining: Optional[int] = None
    rate_limit_reset_time: Optional[datetime] = None
    last_successful_call: Optional[datetime] = None
    last_error: Optional[str] = None
    error_count_today: int = 0
    total_requests_today: int = 0
    average_quality_score: float = Field(default=0.0, ge=0.0, le=100.0)
    supported_markets: List[MarketType] = Field(default_factory=list)
    symbols_available: int = 0

    @field_validator('response_time_ms')
    @classmethod
    def validate_response_time(cls, v):
        return max(0.0, v)

    @field_validator('error_count_today', 'total_requests_today', 'symbols_available')
    @classmethod
    def validate_counts(cls, v):
        return max(0, v)


# Market Context Models

class MarketSession(BaseModel):
    """Market session information."""
    market: str
    session_type: TradingSession
    is_open: bool
    next_open: Optional[datetime] = None
    next_close: Optional[datetime] = None
    timezone: str = "UTC"
    current_time: datetime = Field(default_factory=datetime.now)

    @field_validator('market')
    @classmethod
    def validate_market(cls, v):
        if not v or not v.strip():
            raise ValueError('Market cannot be empty')
        return v.strip().upper()


class MarketSentiment(BaseModel):
    """Market sentiment indicators."""
    symbol: str
    sentiment_score: float = Field(ge=-1.0, le=1.0)  # -1 (very bearish) to 1 (very bullish)
    volatility_index: float = Field(ge=0.0)
    volume_trend: float = Field(ge=-1.0, le=1.0)  # -1 (decreasing) to 1 (increasing)
    price_momentum: float = Field(ge=-1.0, le=1.0)  # -1 (bearish) to 1 (bullish)
    social_media_buzz: float = Field(default=0.0, ge=0.0, le=1.0)
    news_sentiment: float = Field(default=0.0, ge=-1.0, le=1.0)
    analyst_ratings: Dict[str, int] = Field(default_factory=dict)  # rating -> count
    confidence_level: float = Field(default=0.0, ge=0.0, le=1.0)
    timestamp: datetime = Field(default_factory=datetime.now)

    @field_validator('symbol')
    @classmethod
    def validate_symbol(cls, v):
        # Reuse validation logic from TradingSymbol
        if not v or not v.strip():
            raise ValueError('Symbol cannot be empty')

        symbol = v.strip().upper()
        if not re.match(r'^[A-Z0-9._-]+$', symbol):
            raise ValueError('Symbol contains invalid characters')

        if len(symbol) > 12:
            raise ValueError('Symbol too long')

        return symbol


class MarketContext(BaseModel):
    """Comprehensive market context."""
    timestamp: datetime = Field(default_factory=datetime.now)
    market_sessions: Dict[str, MarketSession] = Field(default_factory=dict)
    sentiment_indicators: Dict[str, MarketSentiment] = Field(default_factory=dict)
    economic_indicators: Dict[str, float] = Field(default_factory=dict)
    volatility_environment: str = "normal"  # low, normal, high, extreme
    market_regime: str = "normal"  # bull, bear, sideways, volatile
    risk_appetite: float = Field(default=0.0, ge=0.0, le=1.0)

    @field_validator('volatility_environment')
    @classmethod
    def validate_volatility(cls, v):
        valid_levels = ['low', 'normal', 'high', 'extreme']
        if v not in valid_levels:
            raise ValueError(f'Invalid volatility environment: {v}. Valid: {valid_levels}')
        return v

    @field_validator('market_regime')
    @classmethod
    def validate_regime(cls, v):
        valid_regimes = ['bull', 'bear', 'sideways', 'volatile']
        if v not in valid_regimes:
            raise ValueError(f'Invalid market regime: {v}. Valid: {valid_regimes}')
        return v


# Aggregated Response Models

class MarketOverview(BaseResponse):
    """Market overview with key metrics."""
    major_indices: Dict[str, MarketQuote] = Field(default_factory=dict)
    top_movers: Dict[str, List[MarketQuote]] = Field(default_factory=dict)  # gainers, losers, most_active
    market_summary: Dict[str, Any] = Field(default_factory=dict)
    sector_performance: Dict[str, float] = Field(default_factory=dict)
    market_context: MarketContext = Field(default_factory=MarketContext)
    data_sources_status: Dict[DataSource, DataSourceHealth] = Field(default_factory=dict)
    quality_overview: Dict[str, float] = Field(default_factory=dict)


class SymbolAnalysis(BaseResponse):
    """Comprehensive analysis for a single symbol."""
    symbol: str
    current_quote: Optional[MarketQuote] = None
    historical_data: List[OHLCVBar] = Field(default_factory=list)
    technical_indicators: Dict[str, float] = Field(default_factory=dict)
    fundamental_data: Dict[str, Any] = Field(default_factory=dict)
    quality_metrics: Optional[DataQualityMetrics] = None
    sentiment: Optional[MarketSentiment] = None
    peer_comparison: Dict[str, Any] = Field(default_factory=dict)
    recommendations: List[str] = Field(default_factory=list)

    @field_validator('symbol')
    @classmethod
    def validate_symbol(cls, v):
        # Reuse validation logic from TradingSymbol
        if not v or not v.strip():
            raise ValueError('Symbol cannot be empty')

        symbol = v.strip().upper()
        if not re.match(r'^[A-Z0-9._-]+$', symbol):
            raise ValueError('Symbol contains invalid characters')

        if len(symbol) > 12:
            raise ValueError('Symbol too long')

        return symbol