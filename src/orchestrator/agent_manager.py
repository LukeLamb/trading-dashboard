"""
Agent Manager for Trading Dashboard

This module manages the lifecycle of trading agents (starting, stopping, health monitoring).
It allows the dashboard to automatically start and manage dependent services like the Market Data Agent.
"""

import asyncio
import subprocess
import sys
import time
import requests
import psutil
from pathlib import Path
from typing import Dict, Optional, List, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging

from ..utils.logging import get_logger
from ..utils.config import get_config_manager


class AgentStatus(Enum):
    """Agent status enumeration."""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    ERROR = "error"
    STOPPING = "stopping"


@dataclass
class ResourceMetrics:
    """Agent resource usage metrics."""
    cpu_percent: float = 0.0
    memory_mb: float = 0.0
    memory_percent: float = 0.0
    uptime_seconds: float = 0.0
    restart_count: int = 0
    last_restart_time: Optional[float] = None


@dataclass
class AgentInfo:
    """Information about a managed agent."""
    name: str
    path: Path
    url: str
    port: int
    status: AgentStatus = AgentStatus.STOPPED
    process: Optional[subprocess.Popen] = None
    pid: Optional[int] = None
    start_command: List[str] = field(default_factory=list)
    health_endpoint: str = "/health"
    last_health_check: Optional[float] = None
    error_message: Optional[str] = None
    start_time: Optional[float] = None
    resource_metrics: ResourceMetrics = field(default_factory=ResourceMetrics)


class AgentManager:
    """
    Manages the lifecycle of trading agents.
    
    This class can start, stop, and monitor trading agents automatically,
    making it easy for the dashboard to manage its dependencies.
    """

    def __init__(self, config_path: str = None):
        """Initialize the Agent Manager."""
        self.logger = get_logger(self.__class__.__name__)
        self.config_manager = get_config_manager()
        self.config = self.config_manager
        self.agents: Dict[str, AgentInfo] = {}
        self._monitoring_task: Optional[asyncio.Task] = None
        self._monitoring_active = False
        self._setup_agents()

    def _setup_agents(self):
        """Setup agent configurations from config."""
        try:
            # Get the dashboard directory (parent of src)
            dashboard_dir = Path(__file__).parent.parent.parent
            
            # Market Data Agent setup
            agent_configs = self.config_manager.get_all_agent_configs()
            market_data_config = agent_configs.get("market_data")
            market_data_path = dashboard_dir.parent / "market_data_agent"
            
            if market_data_config:
                self.agents["market_data"] = AgentInfo(
                    name="Market Data Agent",
                    path=market_data_path,
                    url=market_data_config.url,
                    port=8000,  # Default port from market data config
                    start_command=[sys.executable, "run_api.py"],
                    health_endpoint="/health"
                )
            
            # Add other agents here as they become available
            # Example for future agents:
            # pattern_recognition_config = self.config.agents.pattern_recognition
            # self.agents["pattern_recognition"] = AgentInfo(...)
            
            self.logger.info(f"Configured {len(self.agents)} agents for management")
            
        except Exception as e:
            self.logger.error(f"Failed to setup agents: {e}")

    async def start_agent(self, agent_name: str, wait_for_health: bool = True, 
                         timeout: int = 30) -> bool:
        """
        Start a specific agent.
        
        Args:
            agent_name: Name of the agent to start
            wait_for_health: Whether to wait for the agent to be healthy
            timeout: Timeout in seconds for health check
            
        Returns:
            True if agent started successfully
        """
        if agent_name not in self.agents:
            self.logger.error(f"Unknown agent: {agent_name}")
            return False
            
        agent = self.agents[agent_name]
        
        try:
            # Check if already running
            if agent.status == AgentStatus.RUNNING:
                if await self._check_agent_health(agent_name):
                    self.logger.info(f"{agent.name} is already running")
                    return True
                else:
                    self.logger.warning(f"{agent.name} appears to be running but unhealthy, restarting")
                    await self.stop_agent(agent_name)
            
            # Check if agent directory exists
            if not agent.path.exists():
                agent.status = AgentStatus.ERROR
                agent.error_message = f"Agent directory not found: {agent.path}"
                self.logger.error(agent.error_message)
                return False
                
            # Check if start command exists
            start_script = agent.path / agent.start_command[-1]
            if not start_script.exists():
                agent.status = AgentStatus.ERROR
                agent.error_message = f"Start script not found: {start_script}"
                self.logger.error(agent.error_message)
                return False
            
            self.logger.info(f"Starting {agent.name}...")
            agent.status = AgentStatus.STARTING
            agent.error_message = None
            
            # Start the process
            process = subprocess.Popen(
                agent.start_command,
                cwd=agent.path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0
            )
            
            agent.process = process
            agent.pid = process.pid
            agent.start_time = time.time()
            agent.resource_metrics.restart_count += 1
            agent.resource_metrics.last_restart_time = agent.start_time
            
            self.logger.info(f"{agent.name} started with PID {agent.pid}")
            
            # Wait for the agent to be healthy if requested
            if wait_for_health:
                healthy = await self._wait_for_health(agent_name, timeout)
                if healthy:
                    agent.status = AgentStatus.RUNNING
                    self.logger.info(f"{agent.name} is running and healthy")
                    return True
                else:
                    agent.status = AgentStatus.ERROR
                    agent.error_message = f"Agent failed to become healthy within {timeout}s"
                    self.logger.error(agent.error_message)
                    await self.stop_agent(agent_name)
                    return False
            else:
                agent.status = AgentStatus.RUNNING
                return True
                
        except Exception as e:
            agent.status = AgentStatus.ERROR
            agent.error_message = str(e)
            self.logger.error(f"Failed to start {agent.name}: {e}")
            return False

    async def stop_agent(self, agent_name: str, timeout: int = 10) -> bool:
        """
        Stop a specific agent.
        
        Args:
            agent_name: Name of the agent to stop
            timeout: Timeout in seconds for graceful shutdown
            
        Returns:
            True if agent stopped successfully
        """
        if agent_name not in self.agents:
            self.logger.error(f"Unknown agent: {agent_name}")
            return False
            
        agent = self.agents[agent_name]
        
        try:
            if agent.status == AgentStatus.STOPPED:
                self.logger.info(f"{agent.name} is already stopped")
                return True
                
            self.logger.info(f"Stopping {agent.name}...")
            agent.status = AgentStatus.STOPPING
            
            if agent.process and agent.process.poll() is None:
                # Try graceful shutdown first
                if sys.platform == "win32":
                    agent.process.terminate()
                else:
                    agent.process.terminate()
                
                # Wait for graceful shutdown
                try:
                    agent.process.wait(timeout=timeout)
                    self.logger.info(f"{agent.name} stopped gracefully")
                except subprocess.TimeoutExpired:
                    # Force kill if graceful shutdown failed
                    self.logger.warning(f"{agent.name} didn't stop gracefully, force killing")
                    agent.process.kill()
                    agent.process.wait()
                    
            elif agent.pid:
                # Process handle lost but we have PID, try to kill by PID
                try:
                    if sys.platform == "win32":
                        subprocess.run(["taskkill", "/F", "/PID", str(agent.pid)], check=True)
                    else:
                        subprocess.run(["kill", "-9", str(agent.pid)], check=True)
                    self.logger.info(f"Killed {agent.name} by PID {agent.pid}")
                except subprocess.CalledProcessError:
                    self.logger.warning(f"Failed to kill {agent.name} by PID, may already be dead")
            
            # Clean up agent state
            agent.process = None
            agent.pid = None
            agent.status = AgentStatus.STOPPED
            agent.error_message = None
            agent.start_time = None
            
            self.logger.info(f"{agent.name} stopped")
            return True
            
        except Exception as e:
            agent.status = AgentStatus.ERROR
            agent.error_message = str(e)
            self.logger.error(f"Failed to stop {agent.name}: {e}")
            return False

    async def start_all_enabled_agents(self, wait_for_health: bool = True) -> Dict[str, bool]:
        """
        Start all enabled agents.
        
        Args:
            wait_for_health: Whether to wait for agents to be healthy
            
        Returns:
            Dictionary mapping agent names to start success status
        """
        results = {}
        
        for agent_name, agent in self.agents.items():
            # Check if agent is enabled in config
            try:
                agent_configs = self.config_manager.get_all_agent_configs()
                agent_config = agent_configs.get(agent_name)
                if agent_config and not agent_config.enabled:
                    self.logger.info(f"Skipping {agent.name} (disabled in config)")
                    results[agent_name] = True  # Consider skipped as success
                    continue
            except Exception:
                self.logger.warning(f"No config found for {agent_name}, assuming enabled")
            
            self.logger.info(f"Starting {agent.name}...")
            results[agent_name] = await self.start_agent(agent_name, wait_for_health)
        
        successful = sum(1 for success in results.values() if success)
        total = len(results)
        self.logger.info(f"Started {successful}/{total} agents successfully")
        
        return results

    async def stop_all_agents(self) -> Dict[str, bool]:
        """
        Stop all running agents.
        
        Returns:
            Dictionary mapping agent names to stop success status
        """
        results = {}
        
        for agent_name, agent in self.agents.items():
            if agent.status in [AgentStatus.RUNNING, AgentStatus.STARTING]:
                results[agent_name] = await self.stop_agent(agent_name)
            else:
                results[agent_name] = True  # Already stopped
        
        return results

    async def get_agent_status(self, agent_name: str) -> Optional[AgentInfo]:
        """
        Get status of a specific agent.
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            AgentInfo object or None if agent doesn't exist
        """
        return self.agents.get(agent_name)

    async def get_all_agent_status(self) -> Dict[str, AgentInfo]:
        """
        Get status of all agents.
        
        Returns:
            Dictionary mapping agent names to AgentInfo objects
        """
        return self.agents.copy()

    async def restart_agent(self, agent_name: str) -> bool:
        """
        Restart a specific agent.
        
        Args:
            agent_name: Name of the agent to restart
            
        Returns:
            True if agent restarted successfully
        """
        self.logger.info(f"Restarting {agent_name}...")
        
        # Stop first
        stop_success = await self.stop_agent(agent_name)
        if not stop_success:
            self.logger.error(f"Failed to stop {agent_name} for restart")
            return False
        
        # Wait a moment
        await asyncio.sleep(2)
        
        # Start again
        start_success = await self.start_agent(agent_name)
        return start_success

    async def start_monitoring(self, interval: int = 30):
        """
        Start monitoring all agents with periodic health checks.
        
        Args:
            interval: Health check interval in seconds
        """
        if self._monitoring_active:
            self.logger.warning("Monitoring already active")
            return
            
        self._monitoring_active = True
        self._monitoring_task = asyncio.create_task(self._monitoring_loop(interval))
        self.logger.info(f"Started agent monitoring with {interval}s interval")

    async def stop_monitoring(self):
        """Stop agent monitoring."""
        self._monitoring_active = False
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        self.logger.info("Stopped agent monitoring")

    # Private methods

    async def _check_agent_health(self, agent_name: str) -> bool:
        """Check if an agent is healthy."""
        if agent_name not in self.agents:
            return False
            
        agent = self.agents[agent_name]
        
        try:
            # Try to reach the health endpoint
            response = requests.get(
                f"{agent.url}{agent.health_endpoint}",
                timeout=5
            )
            
            healthy = response.status_code == 200
            agent.last_health_check = time.time()
            
            if healthy and agent.status == AgentStatus.ERROR:
                # Agent recovered
                agent.status = AgentStatus.RUNNING
                agent.error_message = None
                self.logger.info(f"{agent.name} recovered")
            elif not healthy and agent.status == AgentStatus.RUNNING:
                # Agent became unhealthy
                agent.status = AgentStatus.ERROR
                agent.error_message = f"Health check failed: HTTP {response.status_code}"
                self.logger.warning(f"{agent.name} became unhealthy")
            
            return healthy
            
        except Exception as e:
            agent.last_health_check = time.time()
            if agent.status == AgentStatus.RUNNING:
                agent.status = AgentStatus.ERROR
                agent.error_message = f"Health check failed: {e}"
                self.logger.warning(f"{agent.name} health check failed: {e}")
            return False

    async def _wait_for_health(self, agent_name: str, timeout: int) -> bool:
        """Wait for an agent to become healthy."""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if await self._check_agent_health(agent_name):
                return True
            await asyncio.sleep(1)
            
        return False

    async def _monitoring_loop(self, interval: int):
        """Main monitoring loop."""
        try:
            while self._monitoring_active:
                for agent_name, agent in self.agents.items():
                    if agent.status in [AgentStatus.RUNNING, AgentStatus.ERROR]:
                        await self._check_agent_health(agent_name)
                
                await asyncio.sleep(interval)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            self.logger.error(f"Monitoring loop error: {e}")

    async def cleanup(self):
        """Clean up resources and stop all agents."""
        self.logger.info("Cleaning up Agent Manager...")
        
        # Stop monitoring
        await self.stop_monitoring()
        
        # Stop all agents
        await self.stop_all_agents()
        
        self.logger.info("Agent Manager cleanup complete")

    async def update_resource_metrics(self, agent_name: str) -> bool:
        """
        Update resource metrics for a specific agent.

        Args:
            agent_name: Name of the agent to update

        Returns:
            True if metrics were updated successfully
        """
        if agent_name not in self.agents:
            return False

        agent = self.agents[agent_name]

        if not agent.pid or agent.status != AgentStatus.RUNNING:
            return False

        try:
            # Get process information
            process = psutil.Process(agent.pid)

            # CPU and memory usage
            agent.resource_metrics.cpu_percent = process.cpu_percent(interval=0.1)
            memory_info = process.memory_info()
            agent.resource_metrics.memory_mb = memory_info.rss / (1024 * 1024)  # Convert to MB
            agent.resource_metrics.memory_percent = process.memory_percent()

            # Uptime calculation
            if agent.start_time:
                agent.resource_metrics.uptime_seconds = time.time() - agent.start_time

            return True

        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
            self.logger.warning(f"Failed to get resource metrics for {agent.name}: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Error updating resource metrics for {agent.name}: {e}")
            return False

    async def update_all_resource_metrics(self) -> Dict[str, bool]:
        """
        Update resource metrics for all running agents.

        Returns:
            Dictionary mapping agent names to update success status
        """
        results = {}

        for agent_name, agent in self.agents.items():
            if agent.status == AgentStatus.RUNNING:
                results[agent_name] = await self.update_resource_metrics(agent_name)
            else:
                results[agent_name] = True  # No update needed for stopped agents

        return results

    def get_resource_summary(self) -> Dict[str, Dict]:
        """
        Get resource usage summary for all agents.

        Returns:
            Dictionary with agent resource summaries
        """
        summary = {}

        total_cpu = 0.0
        total_memory = 0.0
        running_agents = 0

        for agent_name, agent in self.agents.items():
            metrics = agent.resource_metrics

            agent_summary = {
                "status": agent.status.value,
                "cpu_percent": metrics.cpu_percent,
                "memory_mb": round(metrics.memory_mb, 2),
                "memory_percent": round(metrics.memory_percent, 2),
                "uptime_hours": round(metrics.uptime_seconds / 3600, 2) if metrics.uptime_seconds > 0 else 0,
                "restart_count": metrics.restart_count,
                "last_restart": metrics.last_restart_time
            }

            summary[agent_name] = agent_summary

            if agent.status == AgentStatus.RUNNING:
                total_cpu += metrics.cpu_percent
                total_memory += metrics.memory_mb
                running_agents += 1

        # Add system totals
        summary["_system_totals"] = {
            "running_agents": running_agents,
            "total_agents": len(self.agents),
            "total_cpu_percent": round(total_cpu, 2),
            "total_memory_mb": round(total_memory, 2)
        }

        return summary

    def get_health_score(self, agent_name: str) -> Optional[float]:
        """
        Calculate health score for an agent based on various metrics.

        Args:
            agent_name: Name of the agent

        Returns:
            Health score from 0.0 (unhealthy) to 1.0 (perfect health)
        """
        if agent_name not in self.agents:
            return None

        agent = self.agents[agent_name]

        if agent.status != AgentStatus.RUNNING:
            return 0.0

        score = 1.0

        # Penalize high restart count
        if agent.resource_metrics.restart_count > 0:
            restart_penalty = min(agent.resource_metrics.restart_count * 0.1, 0.3)
            score -= restart_penalty

        # Penalize high CPU usage
        if agent.resource_metrics.cpu_percent > 80:
            cpu_penalty = (agent.resource_metrics.cpu_percent - 80) / 100
            score -= cpu_penalty

        # Penalize high memory usage
        if agent.resource_metrics.memory_percent > 80:
            memory_penalty = (agent.resource_metrics.memory_percent - 80) / 100
            score -= memory_penalty

        # Bonus for long uptime
        if agent.resource_metrics.uptime_seconds > 3600:  # More than 1 hour
            uptime_bonus = min(0.1, agent.resource_metrics.uptime_seconds / 86400 * 0.1)  # Max 0.1 bonus
            score += uptime_bonus

        # Health check penalty
        if agent.last_health_check:
            time_since_check = time.time() - agent.last_health_check
            if time_since_check > 300:  # More than 5 minutes
                score -= 0.2
        else:
            score -= 0.1  # Never had a health check

        return max(0.0, min(1.0, score))

    def get_all_health_scores(self) -> Dict[str, float]:
        """Get health scores for all agents."""
        scores = {}
        for agent_name in self.agents:
            score = self.get_health_score(agent_name)
            if score is not None:
                scores[agent_name] = round(score, 3)
        return scores


# Singleton instance for global access
_agent_manager: Optional[AgentManager] = None


def get_agent_manager(config_path: str = None) -> AgentManager:
    """Get the global Agent Manager instance."""
    global _agent_manager
    if _agent_manager is None:
        _agent_manager = AgentManager(config_path)
    return _agent_manager
