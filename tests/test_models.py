"""
Comprehensive Tests for Trading Dashboard Models.

This module tests all Pydantic models for validation, serialization,
and business logic consistency across the trading dashboard.
"""

import pytest
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Dict, Any
import json

from src.models import (
    # Base Response Models
    BaseResponse, ErrorResponse, ResponseStatus, AgentType, HealthStatus,
    QualityGrade, DataSourceStatus, AgentHealthMetrics, AgentHealthCheck,
    SystemHealthResponse, PriceData, HistoricalDataPoint, ValidationResult,

    # Agent Status Models
    ProcessStatus, CircuitBreakerState, MarketDataAgentStatus,
    ComprehensiveAgentStatus, SystemStatus, AgentControlRequest,

    # Market Data Models
    MarketType, DataSource, TradingSymbol, MarketQuote, OHLCVBar, MarketDataRequest,
    DataQualityMetrics, MarketSentiment,

    # System Metrics Models
    MetricType, CPUMetrics, MemoryMetrics, SystemMetrics, MetricAlert,
    APIEndpointMetrics,
)


class TestBaseResponseModels:
    """Test base response models."""

    def test_base_response_creation(self):
        """Test basic response model creation."""
        response = BaseResponse()

        assert response.status == ResponseStatus.SUCCESS
        assert isinstance(response.timestamp, datetime)
        assert response.request_id is None
        assert response.agent_id is None

    def test_base_response_with_data(self):
        """Test response with custom data."""
        response = BaseResponse(
            status=ResponseStatus.ERROR,
            request_id="test-123",
            agent_id="market_data_001"
        )

        assert response.status == ResponseStatus.ERROR
        assert response.request_id == "test-123"
        assert response.agent_id == "market_data_001"

    def test_error_response_validation(self):
        """Test error response validation."""
        # Valid error response
        error = ErrorResponse(error_message="Connection failed")
        assert error.status == ResponseStatus.ERROR
        assert error.error_message == "Connection failed"

        # Empty error message should fail
        with pytest.raises(ValueError, match="Error message cannot be empty"):
            ErrorResponse(error_message="")

    def test_agent_health_metrics_validation(self):
        """Test agent health metrics validation."""
        metrics = AgentHealthMetrics(
            uptime_seconds=3600.5,
            cpu_usage_percent=75.2,
            memory_usage_mb=512.0,
            request_count_total=1000,
            error_count_total=5
        )

        assert metrics.uptime_seconds == 3600.5
        assert metrics.cpu_usage_percent == 75.2
        assert metrics.error_count_total == 5

        # Test negative values are corrected
        metrics_negative = AgentHealthMetrics(
            uptime_seconds=-100,
            cpu_usage_percent=-10
        )
        assert metrics_negative.uptime_seconds == 0.0
        assert metrics_negative.cpu_usage_percent == 0.0

    def test_agent_health_check_validation(self):
        """Test agent health check validation."""
        health = AgentHealthCheck(
            agent_type=AgentType.MARKET_DATA,
            agent_id="mda-001",
            status=HealthStatus.HEALTHY
        )

        assert health.agent_type == AgentType.MARKET_DATA
        assert health.agent_id == "mda-001"
        assert health.status == HealthStatus.HEALTHY

        # Empty agent ID should fail
        with pytest.raises(ValueError, match="Agent ID cannot be empty"):
            AgentHealthCheck(
                agent_type=AgentType.MARKET_DATA,
                agent_id="",
                status=HealthStatus.HEALTHY
            )


class TestMarketDataModels:
    """Test market data models."""

    def test_trading_symbol_validation(self):
        """Test trading symbol validation."""
        # Valid symbols
        symbol1 = TradingSymbol(symbol="AAPL")
        assert symbol1.symbol == "AAPL"

        symbol2 = TradingSymbol(symbol="btc-usd", market_type=MarketType.CRYPTO)
        assert symbol2.symbol == "BTC-USD"  # Should be uppercased

        # Invalid symbols should fail
        with pytest.raises(ValueError, match="Symbol contains invalid characters"):
            TradingSymbol(symbol="AAPL@")

        with pytest.raises(ValueError, match="Symbol cannot be empty"):
            TradingSymbol(symbol="")

    def test_market_quote_validation(self):
        """Test market quote validation."""
        # Valid quote
        quote = MarketQuote(
            symbol="AAPL",
            price=Decimal("150.25"),
            bid=Decimal("150.20"),
            ask=Decimal("150.30"),
            volume=1000000,
            timestamp=datetime.now(),
            source="yfinance"
        )

        assert quote.symbol == "AAPL"
        assert quote.price == Decimal("150.25")
        assert quote.volume == 1000000

        # Invalid price should fail
        with pytest.raises(ValueError, match="Price must be positive"):
            MarketQuote(
                symbol="AAPL",
                price=Decimal("-10.0"),
                timestamp=datetime.now(),
                source=DataSource.YFINANCE
            )

        # Invalid bid-ask spread should fail
        with pytest.raises(ValueError, match="Bid must be less than ask"):
            MarketQuote(
                symbol="AAPL",
                price=Decimal("150.00"),
                bid=Decimal("150.30"),
                ask=Decimal("150.20"),
                timestamp=datetime.now(),
                source=DataSource.YFINANCE
            )

    def test_ohlcv_bar_validation(self):
        """Test OHLCV bar validation."""
        # Valid OHLCV bar
        bar = OHLCVBar(
            symbol="AAPL",
            timestamp=datetime.now(),
            timeframe="1d",
            open=Decimal("149.50"),
            high=Decimal("151.00"),
            low=Decimal("149.00"),
            close=Decimal("150.75"),
            volume=2500000,
            source="yfinance"
        )

        assert bar.symbol == "AAPL"
        assert bar.high == Decimal("151.00")
        assert bar.volume == 2500000

        # Invalid OHLC relationship should fail
        with pytest.raises(ValueError, match="High must be >= max\\(open, close\\)"):
            OHLCVBar(
                symbol="AAPL",
                timestamp=datetime.now(),
                timeframe="1d",
                open=Decimal("150.00"),
                high=Decimal("149.00"),  # High less than open
                low=Decimal("148.00"),
                close=Decimal("150.50"),
                volume=1000000,
                source=DataSource.YFINANCE
            )

    def test_market_data_request_validation(self):
        """Test market data request validation."""
        # Valid request
        request = MarketDataRequest(
            symbols=["AAPL", "GOOGL", "MSFT"],
            fields=["price", "volume"],
            start_date=date(2023, 1, 1),
            end_date=date(2023, 12, 31),
            timeframe="1d"
        )

        assert len(request.symbols) == 3
        assert "AAPL" in request.symbols
        assert request.timeframe == "1d"

        # Empty symbols should fail
        with pytest.raises(ValueError, match="At least one symbol is required"):
            MarketDataRequest(symbols=[])

        # Invalid date range should fail
        with pytest.raises(ValueError, match="Start date must be before end date"):
            MarketDataRequest(
                symbols=["AAPL"],
                start_date=date(2023, 12, 31),
                end_date=date(2023, 1, 1)
            )

    def test_data_quality_metrics_calculation(self):
        """Test data quality metrics calculation."""
        # Create metrics with individual scores
        metrics = DataQualityMetrics(
            symbol="AAPL",
            source=DataSource.YFINANCE,
            completeness=0.95,
            accuracy=0.98,
            timeliness=0.90,
            consistency=0.85,
            validity=1.00,
            freshness=0.92
        )

        # Overall score should be calculated automatically
        expected_score = (0.95 * 0.25 + 0.98 * 0.30 + 0.90 * 0.20 + 0.85 * 0.15 + 1.00 * 0.10) * 100
        assert abs(metrics.overall_score - expected_score) < 0.01

        # Grade should be assigned based on score
        assert metrics.overall_grade in [QualityGrade.A, QualityGrade.B, QualityGrade.C]

    def test_market_sentiment_validation(self):
        """Test market sentiment validation."""
        sentiment = MarketSentiment(
            symbol="AAPL",
            sentiment_score=0.75,
            volatility_index=15.2,
            volume_trend=0.3,
            price_momentum=0.6
        )

        assert sentiment.symbol == "AAPL"
        assert sentiment.sentiment_score == 0.75
        assert -1.0 <= sentiment.price_momentum <= 1.0

        # Invalid sentiment score should fail
        with pytest.raises(ValueError):
            MarketSentiment(
                symbol="AAPL",
                sentiment_score=2.0  # Outside valid range
            )


class TestAgentStatusModels:
    """Test agent status models."""

    def test_market_data_agent_status(self):
        """Test market data agent status model."""
        status = MarketDataAgentStatus(
            agent_id="mda-001",
            name="Market Data Agent",
            status=HealthStatus.HEALTHY,
            data_points_collected_today=15000,
            data_quality_average=92.5,
            symbols_monitored=50
        )

        assert status.agent_type == AgentType.MARKET_DATA
        assert status.data_points_collected_today == 15000
        assert status.data_quality_average == 92.5

        # Negative values should be corrected
        status_negative = MarketDataAgentStatus(
            agent_id="mda-002",
            name="Test Agent",
            data_points_collected_today=-100
        )
        assert status_negative.data_points_collected_today == 0

    def test_agent_control_request_validation(self):
        """Test agent control request validation."""
        # Valid request
        request = AgentControlRequest(
            agent_id="mda-001",
            action="restart",
            timeout_seconds=60
        )

        assert request.agent_id == "mda-001"
        assert request.action == "restart"
        assert request.timeout_seconds == 60

        # Invalid action should fail
        with pytest.raises(ValueError, match="Invalid action"):
            AgentControlRequest(
                agent_id="mda-001",
                action="invalid_action"
            )

        # Empty agent ID should fail
        with pytest.raises(ValueError, match="Agent ID cannot be empty"):
            AgentControlRequest(
                agent_id="",
                action="start"
            )

    def test_system_status_calculation(self):
        """Test system status calculation."""
        # Create system status with some agents
        from src.models.agent_status import AgentStatusBase

        agent1 = AgentStatusBase(
            agent_type=AgentType.MARKET_DATA,
            agent_id="mda-001",
            name="Market Data Agent",
            status=HealthStatus.HEALTHY
        )

        agent2 = AgentStatusBase(
            agent_type=AgentType.RISK_MANAGEMENT,
            agent_id="rma-001",
            name="Risk Management Agent",
            status=HealthStatus.DEGRADED
        )

        # Create comprehensive agent status objects
        comp_status1 = ComprehensiveAgentStatus(
            basic_info=agent1,
            process_info={},
            connection_info={
                "url": "http://localhost:8000",
                "is_connected": True
            },
            health_metrics={}
        )

        comp_status2 = ComprehensiveAgentStatus(
            basic_info=agent2,
            process_info={},
            connection_info={
                "url": "http://localhost:8002",
                "is_connected": True
            },
            health_metrics={}
        )

        system_status = SystemStatus(
            agents=[comp_status1, comp_status2]
        )

        assert system_status.total_agents == 2
        assert system_status.healthy_agents == 1
        assert system_status.degraded_agents == 1
        assert system_status.overall_health == HealthStatus.DEGRADED  # Due to one degraded agent


class TestSystemMetricsModels:
    """Test system metrics models."""

    def test_cpu_metrics_validation(self):
        """Test CPU metrics validation."""
        cpu = CPUMetrics(
            usage_percent=75.5,
            load_average_1m=1.2,
            core_count=8
        )

        assert cpu.usage_percent == 75.5
        assert cpu.load_average_1m == 1.2
        assert cpu.core_count == 8

        # Invalid usage percentage should fail
        with pytest.raises(Exception):  # Pydantic ValidationError
            CPUMetrics(usage_percent=150.0)

    def test_memory_metrics_consistency(self):
        """Test memory metrics consistency validation."""
        memory = MemoryMetrics(
            total_mb=8192.0,
            available_mb=2048.0,
            used_mb=6144.0,
            usage_percent=75.0
        )

        assert memory.total_mb == 8192.0
        assert memory.usage_percent == (6144.0 / 8192.0) * 100

        # Negative values should fail
        with pytest.raises(Exception):  # Pydantic ValidationError
            MemoryMetrics(
                total_mb=-1000.0,
                available_mb=1000.0,
                used_mb=500.0,
                usage_percent=50.0
            )

    def test_api_endpoint_metrics(self):
        """Test API endpoint metrics."""
        api_metrics = APIEndpointMetrics(
            endpoint_path="/api/v1/price/AAPL",
            method="GET",
            request_count=1000,
            success_count=950,
            error_count=50,
            average_response_time_ms=125.5
        )

        assert api_metrics.endpoint_path == "/api/v1/price/AAPL"
        assert api_metrics.method == "GET"
        assert api_metrics.error_rate == 0.05  # 50/1000

        # Invalid HTTP method should fail
        with pytest.raises(ValueError, match="Invalid HTTP method"):
            APIEndpointMetrics(
                endpoint_path="/test",
                method="INVALID"
            )

    def test_metric_alert(self):
        """Test metric alert model."""
        alert = MetricAlert(
            metric_name="cpu_usage_percent",
            current_value=85.0,
            threshold_value=80.0,
            threshold_operator="gt",
            severity="warning",
            message="CPU usage is high"
        )

        assert alert.metric_name == "cpu_usage_percent"
        assert alert.current_value == 85.0
        assert alert.is_active is True

        # Test resolve functionality
        alert.resolve()
        assert alert.is_active is False
        assert alert.resolved_at is not None

        # Invalid threshold operator should fail
        with pytest.raises(ValueError, match="Invalid threshold operator"):
            MetricAlert(
                metric_name="test_metric",
                current_value=100,
                threshold_value=50,
                threshold_operator="invalid",
                severity="error",
                message="Test alert"
            )


class TestModelSerialization:
    """Test model serialization and deserialization."""

    def test_json_serialization(self):
        """Test JSON serialization of models."""
        # Create a complex model
        quote = MarketQuote(
            symbol="AAPL",
            price=Decimal("150.25"),
            timestamp=datetime.now(),
            source="yfinance",
            quality_score=95
        )

        # Test JSON serialization
        json_data = quote.json()
        assert isinstance(json_data, str)

        # Test deserialization
        parsed_data = json.loads(json_data)
        assert parsed_data["symbol"] == "AAPL"
        assert parsed_data["quality_score"] == 95

    def test_dict_conversion(self):
        """Test dict conversion of models."""
        error = ErrorResponse(
            error_message="Test error",
            error_code="E001"
        )

        # Test dict conversion
        error_dict = error.dict()
        assert error_dict["error_message"] == "Test error"
        assert error_dict["error_code"] == "E001"
        assert error_dict["status"] == ResponseStatus.ERROR

    def test_model_copy(self):
        """Test model copying and updating."""
        original = PriceData(
            symbol="AAPL",
            price=150.25,
            timestamp=datetime.now(),
            source="yfinance"
        )

        # Test copy with updates
        updated = original.copy(update={"price": 151.50, "quality_score": 98})

        assert original.price == 150.25
        assert updated.price == 151.50
        assert updated.quality_score == 98
        assert updated.symbol == "AAPL"  # Unchanged


class TestValidationResult:
    """Test validation result model."""

    def test_validation_result_consistency(self):
        """Test validation result consistency checks."""
        # Valid result with no issues
        result = ValidationResult(
            is_valid=True,
            validation_score=0.95,
            issues=[],
            warnings=["Minor formatting issue"]
        )

        assert result.is_valid is True
        assert result.validation_score == 0.95

        # Result with issues should be marked invalid
        result_with_issues = ValidationResult(
            is_valid=True,  # This will be overridden
            validation_score=0.8,
            issues=["Critical validation error"]
        )

        assert result_with_issues.is_valid is False  # Should be corrected


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_string_validation(self):
        """Test validation of empty strings."""
        # Test various models with empty strings
        with pytest.raises(ValueError):
            TradingSymbol(symbol="")

        with pytest.raises(ValueError):
            ErrorResponse(error_message="")

        with pytest.raises(ValueError):
            AgentControlRequest(agent_id="", action="start")

    def test_extreme_values(self):
        """Test handling of extreme values."""
        # Very large numbers
        metrics = AgentHealthMetrics(
            request_count_total=999999999999,
            uptime_seconds=31536000.0  # 1 year in seconds
        )

        assert metrics.request_count_total == 999999999999
        assert metrics.uptime_seconds == 31536000.0

        # Very small positive numbers
        quote = MarketQuote(
            symbol="PENNY",
            price=Decimal("0.0001"),
            timestamp=datetime.now(),
            source=DataSource.YFINANCE
        )

        assert quote.price == Decimal("0.0001")

    def test_unicode_handling(self):
        """Test handling of unicode characters."""
        # Test with unicode in descriptions and messages
        error = ErrorResponse(
            error_message="Connection failed: 连接失败",
            error_details={"reason": "网络错误"}
        )

        assert "连接失败" in error.error_message
        assert error.error_details["reason"] == "网络错误"

    def test_timezone_handling(self):
        """Test timezone handling in datetime fields."""
        from datetime import timezone

        # Test with timezone-aware datetime
        now_utc = datetime.now(timezone.utc)

        quote = MarketQuote(
            symbol="AAPL",
            price=Decimal("150.00"),
            timestamp=now_utc,
            source=DataSource.YFINANCE
        )

        assert quote.timestamp.tzinfo is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])