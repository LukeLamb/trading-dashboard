# Claude Startup Chat

## Quick Startup Sequence

At the start of each new chat session, execute this startup sequence:

### 1. Configuration Loading

- Read `.claude/settings.local.json` - Claude Code settings with MCP server configs
- Read `settings.local.json` - Project-specific settings with bypass permissions
- Test dashboard imports using the pre-approved command in settings

### 2. MCP Server Initialization

- Read `.mcp.json` - Contains 5 MCP servers:
  - **memory**: Persistent project knowledge with custom path
  - **context7**: Library documentation lookup
  - **sequentialthinking**: Enhanced reasoning capabilities
  - **time**: Timezone and time utilities
  - **playwright**: Browser automation (if needed)

### 3. Project State Loading

- Read `memory.json` - Current project progress and implementation status
- Read all documentation in `docs/` folder for full context

### 4. Dashboard Verification

Execute this command to verify dashboard is ready:

```bash
"venv/Scripts/python.exe" -c "
import sys
sys.path.append('.')
from src.dashboard.main import configure_page, get_config_manager
config_manager = get_config_manager()
dashboard_config = config_manager.get_dashboard_config()
from src.dashboard.pages import overview, agents
print('[SUCCESS] All imports successful - dashboard ready to run')
"
```

## Current Project Status

**Phase 1**: ✅ Foundation Setup (4 steps completed)

- Project structure, configuration system, basic Streamlit app, core utilities

**Phase 2 Step 1**: ✅ Base API Client Development completed

- Enterprise-level BaseClient with circuit breaker, retry logic, comprehensive testing

**Next**: Phase 2 Step 2 - Market Data Agent Integration

## Project Architecture

```bash
Trading Dashboard (Central Hub)
├── Streamlit Dashboard (Port 8501)
├── Agent Orchestration System
├── Real-time Visualization
└── Configuration Management

Managed Trading Agents:
├── Market Data Agent (Port 8000)
├── Pattern Recognition (Port 8001)
├── Risk Management (Port 8002)
├── Advisor Agent (Port 8003)
└── Backtest Agent (Port 8004)
```

## Ready State Checklist

After startup sequence, confirm:

- [ ] All configuration files loaded successfully
- [ ] MCP servers configured (5 total)
- [ ] Dashboard imports working (no errors)
- [ ] Memory system shows current project state
- [ ] Documentation context loaded

**Expected Outcome**: "All imports successful - dashboard ready to run" message displayed.

Then provide project progress summary and await further instructions.
