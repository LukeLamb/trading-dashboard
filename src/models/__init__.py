"""
Trading Dashboard Models Package.

This package provides comprehensive Pydantic models for the trading dashboard,
ensuring type safety, validation, and standardized data structures across
all components and API communications.
"""

# Base Response Models
from .api_responses import (
    # Base Models
    BaseResponse,
    ErrorResponse,
    ResponseStatus,
    AgentType,
    HealthStatus,
    QualityGrade,
    DataSourceStatus,

    # Agent Health Models
    AgentHealthMetrics,
    AgentHealthCheck,
    SystemHealthResponse,

    # Market Data Models
    LearningInsights,
    PriceData,
    HistoricalDataPoint,
    HistoricalDataResponse,
    DataSourceMetrics,
    SourcesStatusResponse,

    # Communication Models
    AgentRequest,
    AgentResponse,
    AgentConfiguration,

    # Validation Models
    ValidationResult,
    PerformanceMetrics,
    SymbolValidation,
    QualityAssessment,
)

# Agent Status Models
from .agent_status import (
    # Status Enums
    ProcessStatus,
    CircuitBreakerState,

    # Base Status Models
    AgentStatusBase,
    ProcessInfo,
    CircuitBreakerStatus,
    ConnectionInfo,

    # Agent-Specific Status Models
    MarketDataAgentStatus,
    PatternRecognitionAgentStatus,
    RiskManagementAgentStatus,
    AdvisorAgentStatus,
    BacktestAgentStatus,

    # Comprehensive Status Models
    ComprehensiveAgentStatus,
    SystemStatus,

    # Control Models
    AgentControlRequest,
    AgentControlResponse,
    AgentConfigurationUpdate,
)

# Market Data Models
from .market_data import (
    # Market Data Enums
    MarketType,
    PriceType,
    TradingSession,
    DataSource,
    TimeFrame,

    # Core Market Data Models
    TradingSymbol,
    MarketQuote,
    OHLCVBar,
    MarketDataRequest,
    MarketDataResponse,

    # Quality and Health Models
    DataQualityMetrics,
    DataSourceHealth,

    # Market Context Models
    MarketSession,
    MarketSentiment,
    MarketContext,

    # Aggregated Models
    MarketOverview,
    SymbolAnalysis,
)

# System Metrics Models
from .system_metrics import (
    # Metrics Enums
    MetricType,
    AlertSeverity,
    ResourceType,

    # Base Metrics Models
    MetricValue,
    TimeSeries,

    # Resource Metrics Models
    CPUMetrics,
    MemoryMetrics,
    DiskMetrics,
    NetworkMetrics,

    # Application Metrics Models
    DatabaseMetrics,
    CacheMetrics,
    APIEndpointMetrics,

    # Alert Models
    MetricAlert,

    # Comprehensive Metrics Models
    SystemMetrics,
    SystemMetricsResponse,
    MetricsHistoryResponse,

    # Performance Models
    PerformanceBenchmark,
    SystemHealthScore,
)

# Export all models for easy importing
__all__ = [
    # Base Response Models
    "BaseResponse",
    "ErrorResponse",
    "ResponseStatus",
    "AgentType",
    "HealthStatus",
    "QualityGrade",
    "DataSourceStatus",

    # Agent Health Models
    "AgentHealthMetrics",
    "AgentHealthCheck",
    "SystemHealthResponse",

    # Market Data Base Models
    "LearningInsights",
    "PriceData",
    "HistoricalDataPoint",
    "HistoricalDataResponse",
    "DataSourceMetrics",
    "SourcesStatusResponse",

    # Communication Models
    "AgentRequest",
    "AgentResponse",
    "AgentConfiguration",

    # Validation Models
    "ValidationResult",
    "PerformanceMetrics",
    "SymbolValidation",
    "QualityAssessment",

    # Agent Status Models
    "ProcessStatus",
    "CircuitBreakerState",
    "AgentStatusBase",
    "ProcessInfo",
    "CircuitBreakerStatus",
    "ConnectionInfo",
    "MarketDataAgentStatus",
    "PatternRecognitionAgentStatus",
    "RiskManagementAgentStatus",
    "AdvisorAgentStatus",
    "BacktestAgentStatus",
    "ComprehensiveAgentStatus",
    "SystemStatus",
    "AgentControlRequest",
    "AgentControlResponse",
    "AgentConfigurationUpdate",

    # Market Data Models
    "MarketType",
    "PriceType",
    "TradingSession",
    "DataSource",
    "TimeFrame",
    "TradingSymbol",
    "MarketQuote",
    "OHLCVBar",
    "MarketDataRequest",
    "MarketDataResponse",
    "DataQualityMetrics",
    "DataSourceHealth",
    "MarketSession",
    "MarketSentiment",
    "MarketContext",
    "MarketOverview",
    "SymbolAnalysis",

    # System Metrics Models
    "MetricType",
    "AlertSeverity",
    "ResourceType",
    "MetricValue",
    "TimeSeries",
    "CPUMetrics",
    "MemoryMetrics",
    "DiskMetrics",
    "NetworkMetrics",
    "DatabaseMetrics",
    "CacheMetrics",
    "APIEndpointMetrics",
    "MetricAlert",
    "SystemMetrics",
    "SystemMetricsResponse",
    "MetricsHistoryResponse",
    "PerformanceBenchmark",
    "SystemHealthScore",
]