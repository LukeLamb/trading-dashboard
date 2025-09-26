"""
Orchestrator module for managing trading agents and system coordination.

This module provides:
- Agent lifecycle management (start/stop/restart)
- Health monitoring and auto-recovery
- Process management and cleanup
- Configuration-based agent orchestration
"""

from .agent_manager import AgentManager, AgentInfo, AgentStatus, ResourceMetrics, get_agent_manager
from .dependency_manager import DependencyManager, AgentDependency, StartupPolicy, RestartPolicy, StartupSequence

__all__ = [
    'AgentManager', 'AgentInfo', 'AgentStatus', 'ResourceMetrics', 'get_agent_manager',
    'DependencyManager', 'AgentDependency', 'StartupPolicy', 'RestartPolicy', 'StartupSequence'
]