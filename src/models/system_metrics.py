"""
System Metrics Models for Trading Dashboard.

This module provides models for system performance monitoring, resource usage,
and operational metrics across the trading dashboard infrastructure.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from pydantic import BaseModel, Field, field_validator, model_validator
import psutil

from .api_responses import BaseResponse, ResponseStatus


class MetricType(str, Enum):
    """Types of metrics."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"
    RATE = "rate"


class AlertSeverity(str, Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ResourceType(str, Enum):
    """System resource types."""
    CPU = "cpu"
    MEMORY = "memory"
    DISK = "disk"
    NETWORK = "network"
    DATABASE = "database"
    CACHE = "cache"


# Base Metrics Models

class MetricValue(BaseModel):
    """Individual metric value with metadata."""
    name: str
    value: Union[int, float]
    metric_type: MetricType
    timestamp: datetime = Field(default_factory=datetime.now)
    tags: Dict[str, str] = Field(default_factory=dict)
    unit: Optional[str] = None
    description: Optional[str] = None

    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Metric name cannot be empty')
        return v.strip()

    @field_validator('value')
    @classmethod
    def validate_value(cls, v):
        if isinstance(v, (int, float)) and (v != v):  # Check for NaN
            raise ValueError('Metric value cannot be NaN')
        return v


class TimeSeries(BaseModel):
    """Time series data for metrics."""
    metric_name: str
    data_points: List[MetricValue] = Field(default_factory=list)
    start_time: datetime
    end_time: datetime
    interval_seconds: int = 60
    aggregation_method: str = "average"  # sum, average, min, max, count

    @field_validator('metric_name')
    @classmethod
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Metric name cannot be empty')
        return v.strip()

    @field_validator('interval_seconds')
    @classmethod
    def validate_interval(cls, v):
        if v <= 0:
            raise ValueError('Interval must be positive')
        return v

    @field_validator('aggregation_method')
    @classmethod
    def validate_aggregation(cls, v):
        valid_methods = ['sum', 'average', 'min', 'max', 'count']
        if v not in valid_methods:
            raise ValueError(f'Invalid aggregation method: {v}. Valid: {valid_methods}')
        return v

    @model_validator(mode='after')
    def validate_time_range(self):
        start_time = self.start_time
        end_time = self.end_time

        if start_time and end_time and start_time >= end_time:
            raise ValueError('Start time must be before end time')

        return self


# System Resource Models

class CPUMetrics(BaseModel):
    """CPU usage metrics."""
    usage_percent: float = Field(ge=0.0, le=100.0)
    load_average_1m: Optional[float] = None
    load_average_5m: Optional[float] = None
    load_average_15m: Optional[float] = None
    core_count: int = Field(default_factory=lambda: psutil.cpu_count())
    frequency_mhz: Optional[float] = None
    context_switches: Optional[int] = None
    interrupts: Optional[int] = None
    timestamp: datetime = Field(default_factory=datetime.now)

    @field_validator('usage_percent')
    @classmethod
    def validate_usage(cls, v):
        if v < 0 or v > 100:
            raise ValueError('CPU usage must be between 0 and 100')
        return v

    @field_validator('core_count')
    @classmethod
    def validate_cores(cls, v):
        if v <= 0:
            raise ValueError('Core count must be positive')
        return v

    @field_validator('load_average_1m', 'load_average_5m', 'load_average_15m')
    @classmethod
    def validate_load_averages(cls, v):
        if v is not None and v < 0:
            raise ValueError('Load average cannot be negative')
        return v


class MemoryMetrics(BaseModel):
    """Memory usage metrics."""
    total_mb: float
    available_mb: float
    used_mb: float
    usage_percent: float = Field(ge=0.0, le=100.0)
    cached_mb: Optional[float] = None
    buffered_mb: Optional[float] = None
    swap_total_mb: Optional[float] = None
    swap_used_mb: Optional[float] = None
    swap_usage_percent: Optional[float] = Field(None, ge=0.0, le=100.0)
    timestamp: datetime = Field(default_factory=datetime.now)

    @field_validator('total_mb', 'available_mb', 'used_mb')
    @classmethod
    def validate_memory_values(cls, v):
        if v < 0:
            raise ValueError('Memory values cannot be negative')
        return v

    @model_validator(mode='after')
    def validate_memory_consistency(self):
        total = self.total_mb or 0
        used = self.used_mb or 0
        available = self.available_mb or 0

        if total > 0 and used + available > total * 1.1:  # Allow 10% tolerance
            # Log warning but don't fail validation
            pass

        # Calculate usage percentage if not provided
        if total > 0:
            self.usage_percent = min(100.0, (used / total) * 100)

        return self


class DiskMetrics(BaseModel):
    """Disk usage metrics."""
    path: str
    total_gb: float
    used_gb: float
    available_gb: float
    usage_percent: float = Field(ge=0.0, le=100.0)
    inode_usage_percent: Optional[float] = Field(None, ge=0.0, le=100.0)
    read_bytes_per_sec: Optional[float] = None
    write_bytes_per_sec: Optional[float] = None
    read_ops_per_sec: Optional[float] = None
    write_ops_per_sec: Optional[float] = None
    timestamp: datetime = Field(default_factory=datetime.now)

    @field_validator('path')
    @classmethod
    def validate_path(cls, v):
        if not v or not v.strip():
            raise ValueError('Disk path cannot be empty')
        return v.strip()

    @field_validator('total_gb', 'used_gb', 'available_gb')
    @classmethod
    def validate_disk_values(cls, v):
        if v < 0:
            raise ValueError('Disk values cannot be negative')
        return v

    @model_validator(mode='after')
    def validate_disk_consistency(self):
        total = self.total_gb or 0
        used = self.used_gb or 0
        available = self.available_gb or 0

        if total > 0:
            # Calculate usage percentage
            self.usage_percent = min(100.0, (used / total) * 100)

            # Check consistency
            if abs((used + available) - total) > total * 0.1:  # 10% tolerance
                # Log warning but continue
                pass

        return self


class NetworkMetrics(BaseModel):
    """Network usage metrics."""
    interface: str
    bytes_sent: int = 0
    bytes_received: int = 0
    packets_sent: int = 0
    packets_received: int = 0
    errors_in: int = 0
    errors_out: int = 0
    drops_in: int = 0
    drops_out: int = 0
    bytes_sent_per_sec: Optional[float] = None
    bytes_received_per_sec: Optional[float] = None
    connections_active: Optional[int] = None
    connections_established: Optional[int] = None
    timestamp: datetime = Field(default_factory=datetime.now)

    @field_validator('interface')
    @classmethod
    def validate_interface(cls, v):
        if not v or not v.strip():
            raise ValueError('Network interface cannot be empty')
        return v.strip()

    @field_validator('bytes_sent', 'bytes_received', 'packets_sent', 'packets_received',
               'errors_in', 'errors_out', 'drops_in', 'drops_out')
    def validate_counters(cls, v):
        if v < 0:
            raise ValueError('Network counters cannot be negative')
        return v


# Application-Specific Metrics

class DatabaseMetrics(BaseModel):
    """Database performance metrics."""
    database_name: str
    connection_pool_size: int = 0
    active_connections: int = 0
    idle_connections: int = 0
    queries_per_second: float = 0.0
    slow_queries_count: int = 0
    average_query_time_ms: float = 0.0
    deadlocks_count: int = 0
    cache_hit_ratio: float = Field(default=0.0, ge=0.0, le=1.0)
    index_usage_ratio: float = Field(default=0.0, ge=0.0, le=1.0)
    database_size_mb: Optional[float] = None
    table_count: Optional[int] = None
    timestamp: datetime = Field(default_factory=datetime.now)

    @field_validator('database_name')
    @classmethod
    def validate_database_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Database name cannot be empty')
        return v.strip()

    @field_validator('connection_pool_size', 'active_connections', 'idle_connections',
               'slow_queries_count', 'deadlocks_count', 'table_count')
    def validate_counts(cls, v):
        if v is not None and v < 0:
            raise ValueError('Count values cannot be negative')
        return v

    @field_validator('queries_per_second', 'average_query_time_ms')
    @classmethod
    def validate_performance_metrics(cls, v):
        if v < 0:
            raise ValueError('Performance metrics cannot be negative')
        return v


class CacheMetrics(BaseModel):
    """Cache performance metrics."""
    cache_name: str
    hits: int = 0
    misses: int = 0
    hit_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    total_entries: int = 0
    memory_usage_mb: float = 0.0
    max_memory_mb: Optional[float] = None
    evictions: int = 0
    expirations: int = 0
    average_get_time_ms: float = 0.0
    average_set_time_ms: float = 0.0
    operations_per_second: float = 0.0
    timestamp: datetime = Field(default_factory=datetime.now)

    @field_validator('cache_name')
    @classmethod
    def validate_cache_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Cache name cannot be empty')
        return v.strip()

    @field_validator('hits', 'misses', 'total_entries', 'evictions', 'expirations')
    @classmethod
    def validate_counts(cls, v):
        if v < 0:
            raise ValueError('Count values cannot be negative')
        return v

    @field_validator('memory_usage_mb', 'average_get_time_ms', 'average_set_time_ms', 'operations_per_second')
    @classmethod
    def validate_performance_values(cls, v):
        if v < 0:
            raise ValueError('Performance values cannot be negative')
        return v

    @model_validator(mode='after')
    def calculate_hit_rate(self):
        hits = self.hits or 0
        misses = self.misses or 0
        total_requests = hits + misses

        if total_requests > 0:
            self.hit_rate = hits / total_requests

        return self


# API Performance Metrics

class APIEndpointMetrics(BaseModel):
    """API endpoint performance metrics."""
    endpoint_path: str
    method: str
    request_count: int = 0
    success_count: int = 0
    error_count: int = 0
    average_response_time_ms: float = 0.0
    min_response_time_ms: float = 0.0
    max_response_time_ms: float = 0.0
    p95_response_time_ms: float = 0.0
    p99_response_time_ms: float = 0.0
    requests_per_second: float = 0.0
    error_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    status_codes: Dict[int, int] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)

    @field_validator('endpoint_path')
    @classmethod
    def validate_endpoint(cls, v):
        if not v or not v.strip():
            raise ValueError('Endpoint path cannot be empty')
        return v.strip()

    @field_validator('method')
    @classmethod
    def validate_method(cls, v):
        valid_methods = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS']
        method = v.strip().upper()
        if method not in valid_methods:
            raise ValueError(f'Invalid HTTP method: {method}')
        return method

    @field_validator('request_count', 'success_count', 'error_count')
    @classmethod
    def validate_counts(cls, v):
        if v < 0:
            raise ValueError('Count values cannot be negative')
        return v

    @field_validator('average_response_time_ms', 'min_response_time_ms', 'max_response_time_ms',
               'p95_response_time_ms', 'p99_response_time_ms', 'requests_per_second')
    def validate_performance_metrics(cls, v):
        if v < 0:
            raise ValueError('Performance metrics cannot be negative')
        return v

    @model_validator(mode='after')
    def calculate_error_rate(self):
        total_requests = self.request_count or 0
        errors = self.error_count or 0

        if total_requests > 0:
            self.error_rate = errors / total_requests

        return self


# Alert Models

class MetricAlert(BaseModel):
    """Alert for metric threshold violations."""
    metric_name: str
    current_value: Union[int, float]
    threshold_value: Union[int, float]
    threshold_operator: str  # gt, lt, gte, lte, eq, ne
    severity: AlertSeverity
    message: str
    triggered_at: datetime = Field(default_factory=datetime.now)
    resolved_at: Optional[datetime] = None
    is_active: bool = True
    tags: Dict[str, str] = Field(default_factory=dict)
    escalation_level: int = Field(default=1, ge=1, le=5)
    notification_sent: bool = False

    @field_validator('metric_name')
    @classmethod
    def validate_metric_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Metric name cannot be empty')
        return v.strip()

    @field_validator('threshold_operator')
    @classmethod
    def validate_operator(cls, v):
        valid_operators = ['gt', 'lt', 'gte', 'lte', 'eq', 'ne']
        if v not in valid_operators:
            raise ValueError(f'Invalid threshold operator: {v}. Valid: {valid_operators}')
        return v

    @field_validator('message')
    @classmethod
    def validate_message(cls, v):
        if not v or not v.strip():
            raise ValueError('Alert message cannot be empty')
        return v.strip()

    def resolve(self):
        """Mark the alert as resolved."""
        self.is_active = False
        self.resolved_at = datetime.now()


# Comprehensive System Metrics

class SystemMetrics(BaseModel):
    """Comprehensive system metrics snapshot."""
    timestamp: datetime = Field(default_factory=datetime.now)
    uptime_seconds: float = 0.0
    cpu: CPUMetrics = Field(default_factory=CPUMetrics)
    memory: MemoryMetrics
    disk: List[DiskMetrics] = Field(default_factory=list)
    network: List[NetworkMetrics] = Field(default_factory=list)
    database: Optional[DatabaseMetrics] = None
    cache: List[CacheMetrics] = Field(default_factory=list)
    api_endpoints: List[APIEndpointMetrics] = Field(default_factory=list)
    active_alerts: List[MetricAlert] = Field(default_factory=list)

    @field_validator('uptime_seconds')
    @classmethod
    def validate_uptime(cls, v):
        if v < 0:
            raise ValueError('Uptime cannot be negative')
        return v


class SystemMetricsResponse(BaseResponse):
    """Response model for system metrics."""
    metrics: SystemMetrics
    collection_duration_ms: float = 0.0
    next_collection_time: Optional[datetime] = None

    @field_validator('collection_duration_ms')
    @classmethod
    def validate_duration(cls, v):
        if v < 0:
            raise ValueError('Collection duration cannot be negative')
        return v


class MetricsHistoryResponse(BaseResponse):
    """Response model for historical metrics."""
    metric_name: str
    time_series: TimeSeries
    summary_statistics: Dict[str, float] = Field(default_factory=dict)
    trend_analysis: Dict[str, Any] = Field(default_factory=dict)

    @field_validator('metric_name')
    @classmethod
    def validate_metric_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Metric name cannot be empty')
        return v.strip()


# Performance Benchmarks

class PerformanceBenchmark(BaseModel):
    """Performance benchmark results."""
    benchmark_name: str
    target_value: Union[int, float]
    actual_value: Union[int, float]
    unit: str
    passed: bool
    performance_ratio: float  # actual/target
    timestamp: datetime = Field(default_factory=datetime.now)
    details: Dict[str, Any] = Field(default_factory=dict)

    @field_validator('benchmark_name')
    @classmethod
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Benchmark name cannot be empty')
        return v.strip()

    @model_validator(mode='after')
    def calculate_performance_ratio(self):
        target = self.target_value
        actual = self.actual_value

        if target and target != 0:
            self.performance_ratio = actual / target
        else:
            self.performance_ratio = 0.0

        return self


class SystemHealthScore(BaseModel):
    """Overall system health score."""
    overall_score: float = Field(ge=0.0, le=100.0)
    component_scores: Dict[str, float] = Field(default_factory=dict)
    health_status: str  # excellent, good, fair, poor, critical
    recommendations: List[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.now)

    @field_validator('health_status')
    @classmethod
    def validate_health_status(cls, v):
        valid_statuses = ['excellent', 'good', 'fair', 'poor', 'critical']
        if v not in valid_statuses:
            raise ValueError(f'Invalid health status: {v}. Valid: {valid_statuses}')
        return v

    @model_validator(mode='after')
    def validate_component_scores(self):
        component_scores = self.component_scores or {}
        for component, score in component_scores.items():
            if score < 0 or score > 100:
                raise ValueError(f'Component score for {component} must be between 0 and 100')
        return self