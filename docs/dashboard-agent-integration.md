# Trading Dashboard - Auto-Start Market Data Agent Integration

## Overview

This document outlines how to enhance the Trading Dashboard to automatically start and manage the Market Data Agent, eliminating the need for users to manually start multiple processes.

## Current Architecture Issues

**Current State:**

- User must manually start Market Data Agent: `cd market_data_agent && python run_api.py`
- User must manually start Trading Dashboard: `cd trading-dashboard && python run_dashboard.py`
- No automatic dependency management
- No health monitoring between services
- Poor user experience with multiple terminal windows

**Desired State:**

- Single command: `python run_dashboard.py`
- Dashboard automatically starts Market Data Agent
- Health monitoring and auto-recovery
- Graceful shutdown of all services
- Real-time agent status in dashboard UI

## Implementation Plan

### Phase 1: Agent Manager Core

Create `src/orchestrator/agent_manager.py` with the following capabilities:

#### AgentManager Class Structure

```python
class AgentManager:
    def __init__(self, config_path: str = None)
    async def start_agent(self, agent_name: str, wait_for_health: bool = True) -> bool
    async def stop_agent(self, agent_name: str, timeout: int = 10) -> bool
    async def start_all_enabled_agents(self) -> Dict[str, bool]
    async def stop_all_agents(self) -> Dict[str, bool]
    async def get_agent_status(self, agent_name: str) -> Optional[AgentInfo]
    async def restart_agent(self, agent_name: str) -> bool
    async def start_monitoring(self, interval: int = 30)
    async def _check_agent_health(self, agent_name: str) -> bool
```

#### AgentInfo Data Structure

```python
@dataclass
class AgentInfo:
    name: str
    path: Path                    # Path to agent directory
    url: str                     # Agent API URL
    port: int                    # Agent port
    status: AgentStatus          # Current status
    process: Optional[subprocess.Popen] = None
    pid: Optional[int] = None
    start_command: List[str] = None
    health_endpoint: str = "/health"
    last_health_check: Optional[float] = None
    error_message: Optional[str] = None
```

#### Agent Status Enumeration

```python
class AgentStatus(Enum):
    STOPPED = "stopped"
    STARTING = "starting" 
    RUNNING = "running"
    ERROR = "error"
    STOPPING = "stopping"
```

### Phase 2: Configuration Enhancement

Update `config/environments/development.yaml` to include auto-start options:

```yaml
agents:
  market_data:
    url: "http://localhost:8000"
    timeout: 5
    health_check_interval: 10
    enabled: true
    auto_start: true              # NEW: Auto-start this agent
    start_command: ["python", "run_api.py"]  # NEW: Start command
    working_directory: "../market_data_agent"  # NEW: Relative path
    startup_timeout: 30           # NEW: Max time to wait for startup
    
  pattern_recognition:
    url: "http://localhost:8001"
    enabled: false
    auto_start: false
    
  risk_management:
    url: "http://localhost:8002"
    enabled: false
    auto_start: false
```

### Phase 3: Enhanced Dashboard Startup

Create `src/dashboard/enhanced_main.py` or modify existing `main.py`:

```python
import streamlit as st
import asyncio
from src.orchestrator.agent_manager import get_agent_manager

# Initialize agent manager in session state
if 'agent_manager' not in st.session_state:
    st.session_state.agent_manager = get_agent_manager()
    
    # Auto-start enabled agents on first load
    with st.spinner("Starting required services..."):
        results = asyncio.run(
            st.session_state.agent_manager.start_all_enabled_agents()
        )
        
        # Display startup results
        for agent_name, success in results.items():
            if success:
                st.success(f"✅ {agent_name} started successfully")
            else:
                st.error(f"❌ Failed to start {agent_name}")
```

### Phase 4: Agent Status Dashboard

Add agent monitoring section to the dashboard:

```python
def render_agent_status():
    st.subheader("🤖 Agent Status")
    
    agent_manager = st.session_state.agent_manager
    agents = asyncio.run(agent_manager.get_all_agent_status())
    
    for agent_name, agent_info in agents.items():
        col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
        
        with col1:
            st.write(f"**{agent_info.name}**")
            
        with col2:
            status_color = {
                "running": "🟢",
                "starting": "🟡", 
                "stopped": "🔴",
                "error": "🔴"
            }
            st.write(f"{status_color.get(agent_info.status.value, '⚪')} {agent_info.status.value.title()}")
            
        with col3:
            if st.button(f"Restart", key=f"restart_{agent_name}"):
                with st.spinner(f"Restarting {agent_info.name}..."):
                    success = asyncio.run(agent_manager.restart_agent(agent_name))
                    if success:
                        st.success("Restarted!")
                    else:
                        st.error("Restart failed")
                        
        with col4:
            if agent_info.error_message:
                st.error(f"Error: {agent_info.error_message}")
            elif agent_info.last_health_check:
                last_check = time.time() - agent_info.last_health_check
                st.write(f"Last check: {last_check:.1f}s ago")
```

### Phase 5: Enhanced Run Script

Create `enhanced_run_dashboard.py` or modify existing `run_dashboard.py`:

```python
#!/usr/bin/env python3
"""Enhanced Trading Dashboard Launcher with Agent Management"""

import subprocess
import sys
import os
import atexit
import signal
from pathlib import Path

# Global reference for cleanup
agent_manager_process = None

def cleanup_agents():
    """Cleanup function to stop all agents on exit"""
    if agent_manager_process:
        print("\n🧹 Stopping all agents...")
        # This would call the agent manager's cleanup method
        # Implementation depends on how you structure the cleanup

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print(f"\n📡 Received signal {signum}, shutting down...")
    cleanup_agents()
    sys.exit(0)

def main():
    """Launch the Enhanced Trading Dashboard"""
    print("🚀 Starting Enhanced Trading Dashboard...")
    print("📋 Auto-starting enabled agents...")
    print("=" * 50)
    
    # Register cleanup handlers
    atexit.register(cleanup_agents)
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Continue with existing dashboard startup logic...
    # But now agents will be started automatically by the dashboard
```

## Implementation Details

### Agent Process Management

```python
# Starting an agent
def start_agent_process(agent_info: AgentInfo) -> subprocess.Popen:
    return subprocess.Popen(
        agent_info.start_command,
        cwd=agent_info.path,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0
    )

# Health checking
async def check_agent_health(agent_url: str, health_endpoint: str) -> bool:
    try:
        response = requests.get(f"{agent_url}{health_endpoint}", timeout=5)
        return response.status_code == 200
    except:
        return False
```

### Error Handling and Recovery

```python
# Auto-restart failed agents
async def monitor_agents():
    while monitoring_active:
        for agent_name, agent_info in agents.items():
            if agent_info.status == AgentStatus.RUNNING:
                if not await check_agent_health(agent_info.url, agent_info.health_endpoint):
                    logger.warning(f"Agent {agent_name} unhealthy, restarting...")
                    await restart_agent(agent_name)
        await asyncio.sleep(30)  # Check every 30 seconds
```

### Graceful Shutdown

```python
async def shutdown_all_agents():
    """Gracefully shutdown all agents"""
    for agent_name, agent_info in agents.items():
        if agent_info.process:
            # Try graceful shutdown first
            agent_info.process.terminate()
            try:
                agent_info.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                # Force kill if needed
                agent_info.process.kill()
```

## File Structure

```bash
trading-dashboard/
├── src/
│   ├── orchestrator/
│   │   ├── __init__.py
│   │   └── agent_manager.py          # NEW: Core agent management
│   ├── dashboard/
│   │   ├── main.py                   # MODIFY: Add agent management
│   │   └── components/
│   │       └── agent_status.py       # NEW: Agent status UI
│   └── utils/
│       └── process_utils.py          # NEW: Process management utilities
├── config/
│   └── environments/
│       └── development.yaml          # MODIFY: Add auto-start config
└── enhanced_run_dashboard.py         # NEW: Enhanced launcher
```

## Benefits

1. **Improved User Experience**: Single command startup
2. **Automatic Dependency Management**: Dashboard ensures all required services are running
3. **Health Monitoring**: Real-time status monitoring with auto-recovery
4. **Production Ready**: Proper process management and error handling
5. **Graceful Shutdown**: Clean shutdown of all services
6. **Development Friendly**: Easy to disable auto-start for debugging individual agents

## Migration Strategy

1. **Phase 1**: Implement `AgentManager` class without UI integration
2. **Phase 2**: Add configuration support for auto-start options
3. **Phase 3**: Create enhanced dashboard with agent status UI
4. **Phase 4**: Update run script with automatic agent management
5. **Phase 5**: Add monitoring and auto-recovery features

## Testing Approach

```python
# Unit tests for AgentManager
async def test_start_agent():
    manager = AgentManager()
    result = await manager.start_agent("market_data")
    assert result == True
    
async def test_agent_health_check():
    manager = AgentManager()
    await manager.start_agent("market_data")
    health = await manager._check_agent_health("market_data")
    assert health == True
    
async def test_graceful_shutdown():
    manager = AgentManager() 
    await manager.start_all_enabled_agents()
    results = await manager.stop_all_agents()
    assert all(results.values())
```

## Configuration Examples

### Development Environment

```yaml
# Focus on market data only
agents:
  market_data:
    auto_start: true
    enabled: true
  pattern_recognition:
    auto_start: false
    enabled: false
```

### Production Environment

```yaml
# All agents enabled
agents:
  market_data:
    auto_start: true
    enabled: true
    startup_timeout: 60
  pattern_recognition:
    auto_start: true
    enabled: true
  risk_management:
    auto_start: true
    enabled: true
```

This implementation will transform the user experience from managing multiple processes manually to a single, integrated system that handles all dependencies automatically.
