# Phase 2: Agent Communication Framework

**Objective:** Build robust API communication system for agent integration

## Phase 2 Implementation Todo List

### Step 1: Base API Client Development

- [ ] Create abstract base client with common functionality
  - [ ] Create `src/api_client/__init__.py`
  - [ ] Create `src/api_client/base_client.py`
  - [ ] Implement abstract BaseClient class
  - [ ] Add common HTTP methods (GET, POST, PUT, DELETE)
  - [ ] Add request/response logging
- [ ] Implement connection pooling and retry logic
  - [ ] Add requests.Session for connection pooling
  - [ ] Implement exponential backoff retry strategy
  - [ ] Add configurable retry attempts and delays
  - [ ] Handle connection timeouts gracefully
- [ ] Add timeout and circuit breaker patterns
  - [ ] Implement configurable request timeouts
  - [ ] Add circuit breaker for unhealthy agents
  - [ ] Create health state tracking
  - [ ] Add automatic circuit breaker recovery

### Step 2: Market Data Agent Integration

- [ ] Implement MarketDataClient with health checks
  - [ ] Create `src/api_client/market_data.py`
  - [ ] Extend BaseClient for Market Data Agent
  - [ ] Implement `/health` endpoint integration
  - [ ] Add agent-specific error handling
- [ ] Create methods for price retrieval and source status
  - [ ] Implement `get_current_price(symbol)` method
  - [ ] Implement `get_historical_prices()` method
  - [ ] Implement `get_sources_status()` method
  - [ ] Add data validation for responses
- [ ] Add real-time data polling capabilities
  - [ ] Implement polling mechanism with configurable intervals
  - [ ] Add data caching to reduce API calls
  - [ ] Implement data change detection
  - [ ] Add WebSocket support preparation

### Step 3: API Response Models

- [ ] Define Pydantic models for standardized responses
  - [ ] Create `src/models/__init__.py`
  - [ ] Create `src/models/agent_status.py`
  - [ ] Create `src/models/market_data.py`
  - [ ] Create `src/models/api_responses.py`
- [ ] Create agent status, health check, and data models
  - [ ] Define AgentStatus model with health states
  - [ ] Define HealthCheck model with metrics
  - [ ] Define MarketDataResponse model
  - [ ] Define ErrorResponse model
- [ ] Implement validation and error handling
  - [ ] Add field validation for all models
  - [ ] Implement custom validators for financial data
  - [ ] Add error response parsing
  - [ ] Create validation error messages

### Step 4: Health Monitoring System

- [ ] Build comprehensive health checker for all agents
  - [ ] Create `src/orchestrator/__init__.py`
  - [ ] Create `src/orchestrator/health_monitor.py`
  - [ ] Implement HealthMonitor class
  - [ ] Add multi-agent health checking
- [ ] Create status aggregation and reporting
  - [ ] Implement system-wide health status aggregation
  - [ ] Add health metrics collection
  - [ ] Create health status reporting functions
  - [ ] Add health history tracking
- [ ] Implement automated health checks with scheduling
  - [ ] Add APScheduler integration
  - [ ] Configure periodic health check jobs
  - [ ] Implement health check failure notifications
  - [ ] Add health check performance monitoring

## Testing Checklist

### Unit Tests

- [ ] BaseClient methods work correctly
- [ ] MarketDataClient connects to test endpoints
- [ ] Pydantic models validate data correctly
- [ ] Health monitoring functions properly
- [ ] Retry logic handles failures appropriately

### Integration Tests

- [ ] Successfully connect to Market Data Agent (if available)
- [ ] Health checks return proper status
- [ ] API communication handles network issues
- [ ] Data models parse real API responses
- [ ] Scheduled health checks execute correctly

### Performance Tests

- [ ] API response times are acceptable (<500ms)
- [ ] Connection pooling improves performance
- [ ] Circuit breaker prevents cascade failures
- [ ] Memory usage remains stable during polling
- [ ] Health checks don't impact system performance

## Success Criteria

✅ **Phase 2 Complete When:**

- [ ] Base API client framework is implemented
- [ ] Market Data Agent client is functional
- [ ] All API response models are defined and tested
- [ ] Health monitoring system is operational
- [ ] Retry and circuit breaker patterns work correctly
- [ ] Real-time data polling is implemented
- [ ] All code is tested and committed to repository

## Debugging Notes

### Common Issues and Solutions

- **Connection Issues:**
  - Verify agent URLs and ports in configuration
  - Check firewall settings and network connectivity
  - Validate SSL certificates for HTTPS endpoints

- **Timeout Problems:**
  - Adjust timeout values based on agent response times
  - Implement proper timeout handling in all methods
  - Consider async operations for better performance

- **Data Validation Errors:**
  - Check API response formats match expected models
  - Validate required fields are present in responses
  - Handle optional fields gracefully

- **Health Check Failures:**
  - Ensure health endpoints are implemented correctly
  - Check health check frequency doesn't overwhelm agents
  - Validate health status interpretation logic

## Implementation Notes

- Focus on Market Data Agent integration first
- Prepare framework for future agents (Pattern Recognition, Risk Management, etc.)
- Test with mock responses if actual agents aren't available
- Document all API endpoint requirements for future agent development
