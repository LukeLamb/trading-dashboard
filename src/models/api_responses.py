"""
API Response Models for Trading Dashboard.

This module provides Pydantic models for standardizing API responses across
all agent communications, ensuring type safety and validation.
"""

from datetime import datetime, date
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from pydantic import BaseModel, Field, field_validator, model_validator
import logging

logger = logging.getLogger(__name__)


class ResponseStatus(str, Enum):
    """Standard response status values."""
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    PENDING = "pending"


class AgentType(str, Enum):
    """Types of agents in the trading system."""
    MARKET_DATA = "market_data"
    PATTERN_RECOGNITION = "pattern_recognition"
    RISK_MANAGEMENT = "risk_management"
    ADVISOR = "advisor"
    BACKTEST = "backtest"


class HealthStatus(str, Enum):
    """Health status values."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class QualityGrade(str, Enum):
    """Data quality grades."""
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    F = "F"


class DataSourceStatus(str, Enum):
    """Data source status values."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    MAINTENANCE = "maintenance"


# Base Response Models

class BaseResponse(BaseModel):
    """Base response model for all API responses."""
    status: ResponseStatus = ResponseStatus.SUCCESS
    timestamp: datetime = Field(default_factory=datetime.now)
    request_id: Optional[str] = None
    agent_id: Optional[str] = None

    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ErrorResponse(BaseResponse):
    """Error response model."""
    status: ResponseStatus = ResponseStatus.ERROR
    error_code: Optional[str] = None
    error_message: str
    error_details: Optional[Dict[str, Any]] = None

    @field_validator('error_message')
    @classmethod
    def error_message_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Error message cannot be empty')
        return v.strip()


# Agent Status Models

class AgentHealthMetrics(BaseModel):
    """Metrics for agent health monitoring."""
    uptime_seconds: float = 0.0
    cpu_usage_percent: float = 0.0
    memory_usage_mb: float = 0.0
    request_count_total: int = 0
    request_count_last_hour: int = 0
    error_count_total: int = 0
    error_count_last_hour: int = 0
    average_response_time_ms: float = 0.0

    @field_validator('uptime_seconds', 'cpu_usage_percent', 'memory_usage_mb', 'average_response_time_ms')
    @classmethod
    def non_negative_floats(cls, v):
        return max(0.0, v)

    @field_validator('request_count_total', 'request_count_last_hour', 'error_count_total', 'error_count_last_hour')
    @classmethod
    def non_negative_ints(cls, v):
        return max(0, v)


class AgentHealthCheck(BaseModel):
    """Health check response for individual agent."""
    agent_type: AgentType
    agent_id: str
    status: HealthStatus
    message: Optional[str] = None
    metrics: AgentHealthMetrics = Field(default_factory=AgentHealthMetrics)
    last_successful_call: Optional[datetime] = None
    version: Optional[str] = None

    @field_validator('agent_id')
    @classmethod
    def agent_id_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Agent ID cannot be empty')
        return v.strip()


class SystemHealthResponse(BaseResponse):
    """System-wide health check response."""
    overall_status: HealthStatus
    agents: List[AgentHealthCheck] = Field(default_factory=list)
    healthy_agents: int = 0
    total_agents: int = 0
    system_metrics: AgentHealthMetrics = Field(default_factory=AgentHealthMetrics)

    @model_validator(mode='after')
    def validate_agent_counts(self):
        agents = self.agents
        healthy_count = sum(1 for agent in agents if agent.status == HealthStatus.HEALTHY)
        self.healthy_agents = healthy_count
        self.total_agents = len(agents)
        return self


# Market Data Models

class LearningInsights(BaseModel):
    """AI learning insights from market data agent."""
    predicted_quality: Optional[float] = None
    source_reputation: Optional[float] = None
    market_context: Optional[Dict[str, Any]] = None
    anomaly_score: Optional[float] = None
    confidence_level: Optional[float] = None

    @field_validator('predicted_quality', 'source_reputation', 'anomaly_score', 'confidence_level')
    @classmethod
    def validate_scores(cls, v):
        if v is not None and (v < 0.0 or v > 1.0):
            raise ValueError('Score values must be between 0.0 and 1.0')
        return v


class PriceData(BaseModel):
    """Current price data model."""
    symbol: str
    price: float
    timestamp: datetime
    volume: Optional[int] = None
    bid: Optional[float] = None
    ask: Optional[float] = None
    source: str
    quality_score: int = Field(default=100, ge=0, le=100)
    quality_grade: Optional[QualityGrade] = None
    change_24h: Optional[float] = None
    change_percent_24h: Optional[float] = None
    cached: bool = False
    learning_insights: Optional[LearningInsights] = None

    @field_validator('symbol')
    @classmethod
    def symbol_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Symbol cannot be empty')
        return v.strip().upper()

    @field_validator('price')
    @classmethod
    def price_positive(cls, v):
        if v <= 0:
            raise ValueError('Price must be positive')
        return v

    @field_validator('volume')
    @classmethod
    def volume_non_negative(cls, v):
        if v is not None and v < 0:
            raise ValueError('Volume cannot be negative')
        return v

    @field_validator('source')
    @classmethod
    def source_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Source cannot be empty')
        return v.strip()


class HistoricalDataPoint(BaseModel):
    """Historical price data point."""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    adjusted_close: Optional[float] = None
    source: str
    quality_score: int = Field(default=100, ge=0, le=100)

    @field_validator('open', 'high', 'low', 'close')
    @classmethod
    def prices_positive(cls, v):
        if v <= 0:
            raise ValueError('Prices must be positive')
        return v

    @field_validator('volume')
    @classmethod
    def volume_non_negative(cls, v):
        if v < 0:
            raise ValueError('Volume cannot be negative')
        return v

    @model_validator(mode='after')
    def validate_ohlc(self):
        open_price = self.open
        high = self.high
        low = self.low
        close = self.close

        if all(v is not None for v in [open_price, high, low, close]):
            if high < max(open_price, close) or low > min(open_price, close):
                raise ValueError('Invalid OHLC: high must be >= max(open, close) and low must be <= min(open, close)')

        return self


class HistoricalDataResponse(BaseResponse):
    """Historical data response model."""
    symbol: str
    start_date: date
    end_date: date
    interval: str
    data_points: int = 0
    data: List[HistoricalDataPoint] = Field(default_factory=list)

    @field_validator('symbol')
    @classmethod
    def symbol_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Symbol cannot be empty')
        return v.strip().upper()

    @field_validator('interval')
    @classmethod
    def validate_interval(cls, v):
        valid_intervals = ['1m', '5m', '15m', '30m', '1h', '4h', '1d', '1wk', '1mo']
        if v not in valid_intervals:
            raise ValueError(f'Invalid interval. Must be one of: {valid_intervals}')
        return v

    @model_validator(mode='after')
    def validate_data_points(self):
        self.data_points = len(self.data)
        return self


class DataSourceMetrics(BaseModel):
    """Metrics for a data source."""
    name: str
    status: DataSourceStatus
    last_update: datetime
    quality_grade: QualityGrade = QualityGrade.F
    error_count: int = 0
    response_time_ms: Optional[float] = None
    reliability: float = Field(default=0.0, ge=0.0, le=1.0)
    is_available: bool = False
    rate_limit_remaining: Optional[int] = None
    priority: int = Field(default=3, ge=1, le=3)

    @field_validator('name')
    @classmethod
    def name_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Source name cannot be empty')
        return v.strip()

    @field_validator('error_count')
    @classmethod
    def error_count_non_negative(cls, v):
        return max(0, v)

    @field_validator('response_time_ms')
    @classmethod
    def response_time_non_negative(cls, v):
        if v is not None:
            return max(0.0, v)
        return v


class SourcesStatusResponse(BaseResponse):
    """Data sources status response."""
    sources: Dict[str, DataSourceMetrics] = Field(default_factory=dict)
    total_sources: int = 0
    healthy_sources: int = 0

    @model_validator(mode='after')
    def validate_source_counts(self):
        sources = self.sources
        healthy_count = sum(1 for source in sources.values()
                          if source.status == DataSourceStatus.ACTIVE)
        self.total_sources = len(sources)
        self.healthy_sources = healthy_count
        return self


# Agent Communication Models

class AgentRequest(BaseModel):
    """Base model for agent requests."""
    request_id: str
    agent_type: AgentType
    timestamp: datetime = Field(default_factory=datetime.now)
    timeout: int = Field(default=30, ge=1, le=300)
    priority: int = Field(default=1, ge=1, le=5)

    @field_validator('request_id')
    @classmethod
    def request_id_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Request ID cannot be empty')
        return v.strip()


class AgentResponse(BaseResponse):
    """Base response from agents."""
    data: Optional[Dict[str, Any]] = None
    processing_time_ms: float = 0.0

    @field_validator('processing_time_ms')
    @classmethod
    def processing_time_non_negative(cls, v):
        return max(0.0, v)


# Configuration Models

class AgentConfiguration(BaseModel):
    """Agent configuration model."""
    agent_type: AgentType
    name: str
    url: str
    timeout: int = Field(default=30, ge=1, le=300)
    health_check_interval: int = Field(default=60, ge=10, le=3600)
    max_retries: int = Field(default=3, ge=0, le=10)
    enabled: bool = True

    @field_validator('name')
    @classmethod
    def name_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Agent name cannot be empty')
        return v.strip()

    @field_validator('url')
    @classmethod
    def validate_url(cls, v):
        if not v or not v.strip():
            raise ValueError('Agent URL cannot be empty')
        url = v.strip()
        if not (url.startswith('http://') or url.startswith('https://')):
            raise ValueError('Agent URL must start with http:// or https://')
        return url


# Validation Models

class ValidationResult(BaseModel):
    """Validation result for data or requests."""
    is_valid: bool
    validation_score: float = Field(ge=0.0, le=1.0)
    issues: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)

    @model_validator(mode='after')
    def validate_score_consistency(self):
        is_valid = self.is_valid
        score = self.validation_score
        issues = self.issues

        # If there are issues, validation should be False
        if issues and is_valid:
            self.is_valid = False

        # Score should reflect validity
        if not is_valid and score > 0.7:
            logger.warning(f"Validation score {score} seems high for invalid result")

        return self


# Performance Models

class PerformanceMetrics(BaseModel):
    """Performance metrics for operations."""
    operation_name: str
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    average_response_time_ms: float = 0.0
    min_response_time_ms: float = 0.0
    max_response_time_ms: float = 0.0
    requests_per_second: float = 0.0
    error_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    cache_hit_rate: float = Field(default=0.0, ge=0.0, le=1.0)

    @field_validator('operation_name')
    @classmethod
    def operation_name_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Operation name cannot be empty')
        return v.strip()

    @field_validator('total_requests', 'successful_requests', 'failed_requests')
    @classmethod
    def counts_non_negative(cls, v):
        return max(0, v)

    @field_validator('average_response_time_ms', 'min_response_time_ms', 'max_response_time_ms', 'requests_per_second')
    @classmethod
    def times_non_negative(cls, v):
        return max(0.0, v)

    @model_validator(mode='after')
    def validate_request_consistency(self):
        total = self.total_requests
        successful = self.successful_requests
        failed = self.failed_requests

        # Ensure counts are consistent
        if successful + failed > total:
            logger.warning("Request counts inconsistent: successful + failed > total")

        # Calculate error rate
        if total > 0:
            self.error_rate = failed / total

        return self


# Symbol Validation Models

class SymbolValidation(BaseModel):
    """Symbol validation response."""
    symbol: str
    is_valid: bool
    valid_sources: List[str] = Field(default_factory=list)
    validation_results: Dict[str, bool] = Field(default_factory=dict)
    total_sources_checked: int = 0

    @field_validator('symbol')
    @classmethod
    def symbol_format(cls, v):
        if not v or not v.strip():
            raise ValueError('Symbol cannot be empty')
        return v.strip().upper()

    @model_validator(mode='after')
    def validate_symbol_consistency(self):
        results = self.validation_results
        valid_sources = self.valid_sources

        # Ensure valid sources match validation results
        expected_valid = [source for source, is_valid in results.items() if is_valid]
        if set(valid_sources) != set(expected_valid):
            logger.warning("Valid sources list doesn't match validation results")

        self.total_sources_checked = len(results)
        self.is_valid = len(valid_sources) > 0

        return self


# Quality Assessment Models

class QualityAssessment(BaseModel):
    """Data quality assessment result."""
    symbol: str
    source: str
    overall_grade: QualityGrade
    overall_score: float = Field(ge=0.0, le=100.0)
    dimension_scores: Dict[str, float] = Field(default_factory=dict)
    total_issues: int = 0
    critical_issues: int = 0
    high_issues: int = 0
    medium_issues: int = 0
    low_issues: int = 0
    priority_recommendations: List[str] = Field(default_factory=list)
    improvement_suggestions: List[str] = Field(default_factory=list)
    confidence_level: float = Field(default=0.0, ge=0.0, le=1.0)
    assessment_period: tuple = Field(default_factory=lambda: (datetime.now(), datetime.now()))
    data_points_analyzed: int = 0

    @field_validator('symbol')
    @classmethod
    def symbol_format(cls, v):
        return v.strip().upper()

    @field_validator('source')
    @classmethod
    def source_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Source cannot be empty')
        return v.strip()

    @model_validator(mode='after')
    def validate_quality_consistency(self):
        score = self.overall_score
        grade = self.overall_grade

        # Grade should match score ranges
        if grade == QualityGrade.A and score < 90:
            logger.warning(f"Grade A with score {score} < 90")
        elif grade == QualityGrade.F and score > 60:
            logger.warning(f"Grade F with score {score} > 60")

        return self