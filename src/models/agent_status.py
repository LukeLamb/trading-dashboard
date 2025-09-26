"""
Agent Status Models for Trading Dashboard.

This module provides specialized models for different agent types and their
status reporting, extending the base models with agent-specific functionality.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from pydantic import BaseModel, Field, field_validator, model_validator

from .api_responses import (
    BaseResponse, AgentType, HealthStatus, QualityGrade,
    AgentHealthCheck, AgentHealthMetrics
)


class ProcessStatus(str, Enum):
    """Process status for agent lifecycle management."""
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    FAILED = "failed"
    RESTARTING = "restarting"


class CircuitBreakerState(str, Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Circuit breaker activated
    HALF_OPEN = "half_open"  # Testing if service recovered


# Base Agent Status Models

class AgentStatusBase(BaseModel):
    """Base model for agent status information."""
    agent_type: AgentType
    agent_id: str
    name: str
    version: str = "1.0.0"
    status: HealthStatus = HealthStatus.UNKNOWN
    last_updated: datetime = Field(default_factory=datetime.now)

    @field_validator('agent_id', 'name')
    @classmethod
    def not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Field cannot be empty')
        return v.strip()

    class Config:
        use_enum_values = True


class ProcessInfo(BaseModel):
    """Process information for agent monitoring."""
    process_id: Optional[int] = None
    process_status: ProcessStatus = ProcessStatus.STOPPED
    start_time: Optional[datetime] = None
    uptime: Optional[timedelta] = None
    restart_count: int = 0
    last_restart: Optional[datetime] = None
    command_line: Optional[str] = None
    working_directory: Optional[str] = None
    environment_variables: Dict[str, str] = Field(default_factory=dict)

    @field_validator('restart_count')
    @classmethod
    def restart_count_non_negative(cls, v):
        return max(0, v)

    @model_validator(mode='after')
    def calculate_uptime(self):
        start_time = self.start_time
        if start_time:
            self.uptime = datetime.now() - start_time
        return self


class CircuitBreakerStatus(BaseModel):
    """Circuit breaker status information."""
    state: CircuitBreakerState = CircuitBreakerState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: Optional[datetime] = None
    last_success_time: Optional[datetime] = None
    failure_threshold: int = 5
    recovery_timeout: int = 300  # seconds
    half_open_max_calls: int = 3
    next_attempt_time: Optional[datetime] = None

    @field_validator('failure_count', 'success_count', 'failure_threshold', 'recovery_timeout', 'half_open_max_calls')
    @classmethod
    def non_negative_values(cls, v):
        return max(0, v)


class ConnectionInfo(BaseModel):
    """Connection information for agent communication."""
    url: str
    is_connected: bool = False
    connection_established: Optional[datetime] = None
    last_successful_request: Optional[datetime] = None
    last_failed_request: Optional[datetime] = None
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    average_response_time_ms: float = 0.0
    timeout_seconds: int = 30
    retry_count: int = 3
    circuit_breaker: CircuitBreakerStatus = Field(default_factory=CircuitBreakerStatus)

    @field_validator('url')
    @classmethod
    def validate_url(cls, v):
        if not v or not v.strip():
            raise ValueError('URL cannot be empty')
        url = v.strip()
        if not (url.startswith('http://') or url.startswith('https://')):
            raise ValueError('URL must start with http:// or https://')
        return url

    @field_validator('total_requests', 'successful_requests', 'failed_requests', 'timeout_seconds', 'retry_count')
    @classmethod
    def non_negative_values(cls, v):
        return max(0, v)

    @field_validator('average_response_time_ms')
    @classmethod
    def non_negative_float(cls, v):
        return max(0.0, v)

    @model_validator(mode='after')
    def validate_request_consistency(self):
        total = self.total_requests
        successful = self.successful_requests
        failed = self.failed_requests

        if successful + failed > total:
            # Adjust total to match
            self.total_requests = successful + failed

        return self


# Agent-Specific Status Models

class MarketDataAgentStatus(AgentStatusBase):
    """Status model specific to Market Data Agent."""
    agent_type: AgentType = AgentType.MARKET_DATA
    data_sources: Dict[str, Any] = Field(default_factory=dict)
    active_symbols: List[str] = Field(default_factory=list)
    data_points_collected_today: int = 0
    last_data_update: Optional[datetime] = None
    data_quality_average: float = Field(default=0.0, ge=0.0, le=100.0)
    rate_limit_status: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    cache_hit_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    symbols_monitored: int = 0

    @field_validator('data_points_collected_today', 'symbols_monitored')
    @classmethod
    def non_negative_counts(cls, v):
        return max(0, v)


class PatternRecognitionAgentStatus(AgentStatusBase):
    """Status model for Pattern Recognition Agent."""
    agent_type: AgentType = AgentType.PATTERN_RECOGNITION
    patterns_detected_today: int = 0
    active_patterns: List[str] = Field(default_factory=list)
    model_accuracy: float = Field(default=0.0, ge=0.0, le=1.0)
    last_pattern_detection: Optional[datetime] = None
    processing_queue_size: int = 0
    models_loaded: int = 0
    confidence_threshold: float = Field(default=0.7, ge=0.0, le=1.0)

    @field_validator('patterns_detected_today', 'processing_queue_size', 'models_loaded')
    @classmethod
    def non_negative_counts(cls, v):
        return max(0, v)


class RiskManagementAgentStatus(AgentStatusBase):
    """Status model for Risk Management Agent."""
    agent_type: AgentType = AgentType.RISK_MANAGEMENT
    risk_assessments_today: int = 0
    active_alerts: int = 0
    risk_score_average: float = Field(default=0.0, ge=0.0, le=10.0)
    last_risk_assessment: Optional[datetime] = None
    portfolio_exposure: float = Field(default=0.0, ge=0.0)
    var_calculation_time: Optional[datetime] = None
    stress_test_results: Dict[str, float] = Field(default_factory=dict)

    @field_validator('risk_assessments_today', 'active_alerts')
    @classmethod
    def non_negative_counts(cls, v):
        return max(0, v)


class AdvisorAgentStatus(AgentStatusBase):
    """Status model for Advisor Agent."""
    agent_type: AgentType = AgentType.ADVISOR
    recommendations_today: int = 0
    active_strategies: List[str] = Field(default_factory=list)
    portfolio_value: float = Field(default=0.0, ge=0.0)
    last_recommendation: Optional[datetime] = None
    strategy_performance: Dict[str, float] = Field(default_factory=dict)
    model_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    backtesting_results: Dict[str, Any] = Field(default_factory=dict)

    @field_validator('recommendations_today')
    @classmethod
    def non_negative_counts(cls, v):
        return max(0, v)


class BacktestAgentStatus(AgentStatusBase):
    """Status model for Backtest Agent."""
    agent_type: AgentType = AgentType.BACKTEST
    backtests_completed_today: int = 0
    running_backtests: int = 0
    queued_backtests: int = 0
    last_backtest_completion: Optional[datetime] = None
    average_backtest_duration: float = 0.0  # minutes
    historical_data_range: Dict[str, str] = Field(default_factory=dict)
    compute_resources_used: float = Field(default=0.0, ge=0.0, le=100.0)

    @field_validator('backtests_completed_today', 'running_backtests', 'queued_backtests')
    @classmethod
    def non_negative_counts(cls, v):
        return max(0, v)

    @field_validator('average_backtest_duration')
    @classmethod
    def non_negative_duration(cls, v):
        return max(0.0, v)


# Comprehensive Agent Status Model

class ComprehensiveAgentStatus(BaseModel):
    """Comprehensive status information for any agent."""
    basic_info: AgentStatusBase
    process_info: ProcessInfo
    connection_info: ConnectionInfo
    health_metrics: AgentHealthMetrics
    specific_status: Optional[Union[
        MarketDataAgentStatus,
        PatternRecognitionAgentStatus,
        RiskManagementAgentStatus,
        AdvisorAgentStatus,
        BacktestAgentStatus
    ]] = None
    dependencies: List[str] = Field(default_factory=list)
    configuration: Dict[str, Any] = Field(default_factory=dict)
    logs_summary: Dict[str, int] = Field(default_factory=dict)  # log_level -> count
    alerts: List[Dict[str, Any]] = Field(default_factory=list)
    performance_trends: Dict[str, List[float]] = Field(default_factory=dict)

    @model_validator(mode='after')
    def ensure_agent_type_consistency(self):
        basic_info = self.basic_info
        specific_status = self.specific_status

        if basic_info and specific_status:
            if basic_info.agent_type != specific_status.agent_type:
                raise ValueError('Agent type mismatch between basic_info and specific_status')

        return self


# System-wide Status Models

class SystemStatus(BaseResponse):
    """System-wide status aggregation."""
    agents: List[ComprehensiveAgentStatus] = Field(default_factory=list)
    overall_health: HealthStatus = HealthStatus.UNKNOWN
    total_agents: int = 0
    healthy_agents: int = 0
    degraded_agents: int = 0
    unhealthy_agents: int = 0
    system_uptime: Optional[timedelta] = None
    system_load: float = Field(default=0.0, ge=0.0)
    memory_usage_percent: float = Field(default=0.0, ge=0.0, le=100.0)
    disk_usage_percent: float = Field(default=0.0, ge=0.0, le=100.0)
    network_status: Dict[str, Any] = Field(default_factory=dict)
    active_connections: int = 0
    total_requests_today: int = 0
    error_rate_today: float = Field(default=0.0, ge=0.0, le=1.0)

    @field_validator('total_agents', 'healthy_agents', 'degraded_agents', 'unhealthy_agents', 'active_connections', 'total_requests_today')
    @classmethod
    def non_negative_counts(cls, v):
        return max(0, v)

    @model_validator(mode='after')
    def calculate_system_health(self):
        agents = self.agents

        healthy_count = sum(1 for agent in agents if agent.basic_info.status == HealthStatus.HEALTHY)
        degraded_count = sum(1 for agent in agents if agent.basic_info.status == HealthStatus.DEGRADED)
        unhealthy_count = sum(1 for agent in agents if agent.basic_info.status == HealthStatus.UNHEALTHY)

        self.total_agents = len(agents)
        self.healthy_agents = healthy_count
        self.degraded_agents = degraded_count
        self.unhealthy_agents = unhealthy_count

        # Determine overall health
        if len(agents) == 0:
            overall_health = HealthStatus.UNKNOWN
        elif unhealthy_count > 0:
            overall_health = HealthStatus.UNHEALTHY
        elif degraded_count > 0:
            overall_health = HealthStatus.DEGRADED
        elif healthy_count > 0:
            overall_health = HealthStatus.HEALTHY
        else:
            overall_health = HealthStatus.UNKNOWN

        self.overall_health = overall_health
        return self


# Agent Control Models

class AgentControlRequest(BaseModel):
    """Request model for agent control operations."""
    agent_id: str
    action: str  # start, stop, restart, reload_config
    parameters: Dict[str, Any] = Field(default_factory=dict)
    timeout_seconds: int = Field(default=60, ge=1, le=300)
    force: bool = False

    @field_validator('agent_id')
    @classmethod
    def agent_id_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Agent ID cannot be empty')
        return v.strip()

    @field_validator('action')
    @classmethod
    def validate_action(cls, v):
        valid_actions = ['start', 'stop', 'restart', 'reload_config', 'health_check']
        if v not in valid_actions:
            raise ValueError(f'Invalid action. Must be one of: {valid_actions}')
        return v


class AgentControlResponse(BaseResponse):
    """Response model for agent control operations."""
    agent_id: str
    action: str
    success: bool
    message: str
    previous_status: HealthStatus
    current_status: HealthStatus
    execution_time_seconds: float = 0.0

    @field_validator('execution_time_seconds')
    @classmethod
    def non_negative_time(cls, v):
        return max(0.0, v)


# Configuration Models

class AgentConfigurationUpdate(BaseModel):
    """Model for updating agent configuration."""
    agent_id: str
    configuration_changes: Dict[str, Any]
    restart_required: bool = False
    backup_current_config: bool = True
    validate_before_apply: bool = True

    @field_validator('agent_id')
    @classmethod
    def agent_id_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Agent ID cannot be empty')
        return v.strip()

    @field_validator('configuration_changes')
    @classmethod
    def config_changes_not_empty(cls, v):
        if not v:
            raise ValueError('Configuration changes cannot be empty')
        return v