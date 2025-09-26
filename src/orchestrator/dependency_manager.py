"""
Agent Dependency Manager for Trading Dashboard

This module manages agent dependencies, startup sequencing, and orchestration policies
to ensure agents start in the correct order and handle complex interdependencies.
"""

import asyncio
import time
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging
from collections import defaultdict, deque

from .agent_manager import AgentManager, AgentStatus
from ..utils.logging import get_logger


class StartupPolicy(Enum):
    """Startup policy enumeration."""
    PARALLEL = "parallel"  # Start all agents simultaneously
    SEQUENTIAL = "sequential"  # Start agents one by one
    DEPENDENCY_BASED = "dependency_based"  # Start based on dependencies


class RestartPolicy(Enum):
    """Restart policy enumeration."""
    IMMEDIATE = "immediate"  # Restart immediately on failure
    DELAYED = "delayed"  # Wait before restarting
    EXPONENTIAL_BACKOFF = "exponential_backoff"  # Exponential delay
    MANUAL = "manual"  # Manual restart only


@dataclass
class AgentDependency:
    """Agent dependency configuration."""
    agent_name: str
    depends_on: List[str] = field(default_factory=list)
    required: bool = True  # Whether dependency is required for startup
    timeout: int = 30  # Startup timeout in seconds
    priority: int = 0  # Higher priority agents start first
    restart_policy: RestartPolicy = RestartPolicy.DELAYED
    max_restart_attempts: int = 3
    restart_delay: int = 5  # Base delay in seconds


@dataclass
class StartupSequence:
    """Startup sequence plan."""
    sequence: List[List[str]]  # Groups of agents that can start in parallel
    total_agents: int
    estimated_time: int  # Estimated startup time in seconds


class DependencyManager:
    """
    Manages agent dependencies and orchestration policies.

    This class handles:
    - Agent dependency graph resolution
    - Startup sequencing based on dependencies
    - Restart policies and failure handling
    - Resource monitoring and allocation
    """

    def __init__(self, agent_manager: AgentManager):
        """Initialize the Dependency Manager."""
        self.logger = get_logger(self.__class__.__name__)
        self.agent_manager = agent_manager
        self.dependencies: Dict[str, AgentDependency] = {}
        self.startup_policy = StartupPolicy.DEPENDENCY_BASED
        self.restart_attempts: Dict[str, int] = defaultdict(int)
        self.last_restart_time: Dict[str, float] = {}
        self._setup_default_dependencies()

    def _setup_default_dependencies(self):
        """Setup default agent dependencies."""
        try:
            # Market Data Agent - no dependencies (foundation agent)
            self.dependencies["market_data"] = AgentDependency(
                agent_name="market_data",
                depends_on=[],
                required=True,
                timeout=30,
                priority=100,  # Highest priority
                restart_policy=RestartPolicy.IMMEDIATE,
                max_restart_attempts=5
            )

            # Pattern Recognition - depends on Market Data
            self.dependencies["pattern_recognition"] = AgentDependency(
                agent_name="pattern_recognition",
                depends_on=["market_data"],
                required=False,
                timeout=45,
                priority=80,
                restart_policy=RestartPolicy.DELAYED,
                max_restart_attempts=3,
                restart_delay=10
            )

            # Risk Management - depends on Market Data and Pattern Recognition
            self.dependencies["risk_management"] = AgentDependency(
                agent_name="risk_management",
                depends_on=["market_data", "pattern_recognition"],
                required=False,
                timeout=30,
                priority=90,  # High priority for risk
                restart_policy=RestartPolicy.EXPONENTIAL_BACKOFF,
                max_restart_attempts=3,
                restart_delay=5
            )

            # Advisor Agent - depends on all other agents
            self.dependencies["advisor"] = AgentDependency(
                agent_name="advisor",
                depends_on=["market_data", "pattern_recognition", "risk_management"],
                required=False,
                timeout=60,
                priority=60,
                restart_policy=RestartPolicy.DELAYED,
                max_restart_attempts=2,
                restart_delay=15
            )

            # Backtest Agent - depends on Market Data only
            self.dependencies["backtest"] = AgentDependency(
                agent_name="backtest",
                depends_on=["market_data"],
                required=False,
                timeout=30,
                priority=40,  # Lower priority
                restart_policy=RestartPolicy.MANUAL,
                max_restart_attempts=1
            )

            self.logger.info(f"Configured dependencies for {len(self.dependencies)} agents")

        except Exception as e:
            self.logger.error(f"Failed to setup default dependencies: {e}")

    def add_dependency(self, dependency: AgentDependency) -> bool:
        """
        Add or update agent dependency configuration.

        Args:
            dependency: Agent dependency configuration

        Returns:
            True if dependency was added successfully
        """
        try:
            # Validate dependency doesn't create cycles
            if self._has_circular_dependency(dependency.agent_name, dependency.depends_on):
                self.logger.error(f"Circular dependency detected for {dependency.agent_name}")
                return False

            self.dependencies[dependency.agent_name] = dependency
            self.logger.info(f"Added dependency configuration for {dependency.agent_name}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to add dependency for {dependency.agent_name}: {e}")
            return False

    def _has_circular_dependency(self, agent_name: str, dependencies: List[str]) -> bool:
        """Check for circular dependencies."""
        visited = set()

        def dfs(current_agent: str) -> bool:
            if current_agent == agent_name:
                return True
            if current_agent in visited:
                return False

            visited.add(current_agent)
            current_deps = self.dependencies.get(current_agent, AgentDependency(current_agent)).depends_on

            for dep in current_deps:
                if dfs(dep):
                    return True
            return False

        for dep in dependencies:
            visited.clear()
            if dfs(dep):
                return True

        return False

    def create_startup_sequence(self, agent_names: Optional[List[str]] = None) -> StartupSequence:
        """
        Create an optimal startup sequence based on dependencies.

        Args:
            agent_names: Specific agents to include (None for all)

        Returns:
            StartupSequence with ordered groups
        """
        try:
            # Get agents to include
            if agent_names is None:
                agent_names = list(self.dependencies.keys())

            # Store original count before topological sort modifies the list
            original_count = len(agent_names)

            # Topological sort to determine startup order
            sequence_groups = self._topological_sort(agent_names.copy())  # Pass a copy

            # Estimate total startup time
            estimated_time = self._estimate_startup_time(sequence_groups)

            return StartupSequence(
                sequence=sequence_groups,
                total_agents=original_count,
                estimated_time=estimated_time
            )

        except Exception as e:
            self.logger.error(f"Failed to create startup sequence: {e}")
            return StartupSequence(sequence=[[]], total_agents=0, estimated_time=0)

    def _topological_sort(self, agent_names: List[str]) -> List[List[str]]:
        """Perform topological sort with priority ordering."""
        # Build dependency graph
        graph = defaultdict(list)
        in_degree = defaultdict(int)

        # Initialize all agents
        for agent in agent_names:
            in_degree[agent] = 0

        # Build graph and calculate in-degrees
        for agent in agent_names:
            dep_config = self.dependencies.get(agent, AgentDependency(agent))
            for dependency in dep_config.depends_on:
                if dependency in agent_names:  # Only include if dependency is in our list
                    graph[dependency].append(agent)
                    in_degree[agent] += 1

        # Topological sort with priority
        sequence = []
        queue = []

        while True:
            # Find all agents with no dependencies
            ready_agents = []
            for agent in agent_names:
                if in_degree[agent] == 0:
                    ready_agents.append(agent)

            if not ready_agents:
                break

            # Sort by priority (higher priority first)
            ready_agents.sort(
                key=lambda a: self.dependencies.get(a, AgentDependency(a)).priority,
                reverse=True
            )

            # Add to sequence and remove from consideration
            if ready_agents:
                sequence.append(ready_agents)

                for agent in ready_agents:
                    agent_names.remove(agent)
                    in_degree[agent] = -1  # Mark as processed

                    # Reduce in-degree for dependent agents
                    for dependent in graph[agent]:
                        if in_degree[dependent] > 0:
                            in_degree[dependent] -= 1

        # Handle any remaining agents (shouldn't happen with valid dependencies)
        if agent_names:
            self.logger.warning(f"Remaining agents after topological sort: {agent_names}")
            sequence.append(agent_names)

        return sequence

    def _estimate_startup_time(self, sequence_groups: List[List[str]]) -> int:
        """Estimate total startup time for sequence."""
        total_time = 0

        for group in sequence_groups:
            # Time for this group is the maximum timeout of agents in the group
            group_time = 0
            for agent in group:
                dep_config = self.dependencies.get(agent, AgentDependency(agent))
                group_time = max(group_time, dep_config.timeout)
            total_time += group_time

        return total_time

    async def start_agents_with_dependencies(self, agent_names: Optional[List[str]] = None) -> Dict[str, bool]:
        """
        Start agents respecting their dependencies.

        Args:
            agent_names: Specific agents to start (None for all enabled)

        Returns:
            Dictionary mapping agent names to start success status
        """
        results = {}

        try:
            # Create startup sequence
            sequence = self.create_startup_sequence(agent_names)
            self.logger.info(f"Starting {sequence.total_agents} agents in {len(sequence.sequence)} groups")
            self.logger.info(f"Estimated startup time: {sequence.estimated_time} seconds")

            # Start agents group by group
            for i, group in enumerate(sequence.sequence):
                self.logger.info(f"Starting group {i + 1}/{len(sequence.sequence)}: {group}")

                # Start all agents in this group in parallel
                group_tasks = []
                for agent_name in group:
                    dep_config = self.dependencies.get(agent_name, AgentDependency(agent_name))
                    task = self._start_single_agent_with_config(agent_name, dep_config)
                    group_tasks.append(task)

                # Wait for all agents in this group
                group_results = await asyncio.gather(*group_tasks, return_exceptions=True)

                # Process results
                for agent_name, result in zip(group, group_results):
                    if isinstance(result, Exception):
                        self.logger.error(f"Exception starting {agent_name}: {result}")
                        results[agent_name] = False
                    else:
                        results[agent_name] = result

                # Check if any required agents failed
                failed_required = []
                for agent_name in group:
                    dep_config = self.dependencies.get(agent_name, AgentDependency(agent_name))
                    if dep_config.required and not results.get(agent_name, False):
                        failed_required.append(agent_name)

                if failed_required:
                    self.logger.error(f"Required agents failed to start: {failed_required}")
                    self.logger.error("Stopping startup sequence due to required agent failures")
                    break

            successful = sum(1 for success in results.values() if success)
            total = len(results)
            self.logger.info(f"Startup sequence completed: {successful}/{total} agents started successfully")

        except Exception as e:
            self.logger.error(f"Failed to start agents with dependencies: {e}")

        return results

    async def _start_single_agent_with_config(self, agent_name: str, config: AgentDependency) -> bool:
        """Start a single agent with its specific configuration."""
        try:
            success = await self.agent_manager.start_agent(
                agent_name,
                wait_for_health=True,
                timeout=config.timeout
            )

            if success:
                self.restart_attempts[agent_name] = 0  # Reset restart count on successful start
                self.logger.info(f"Successfully started {agent_name}")
            else:
                self.logger.error(f"Failed to start {agent_name}")

            return success

        except Exception as e:
            self.logger.error(f"Exception starting {agent_name}: {e}")
            return False

    async def handle_agent_failure(self, agent_name: str) -> bool:
        """
        Handle agent failure according to restart policy.

        Args:
            agent_name: Name of failed agent

        Returns:
            True if restart was attempted
        """
        try:
            dep_config = self.dependencies.get(agent_name, AgentDependency(agent_name))

            # Check restart attempts
            current_attempts = self.restart_attempts[agent_name]
            if current_attempts >= dep_config.max_restart_attempts:
                self.logger.error(f"Maximum restart attempts ({dep_config.max_restart_attempts}) reached for {agent_name}")
                return False

            # Apply restart policy
            if dep_config.restart_policy == RestartPolicy.MANUAL:
                self.logger.info(f"Agent {agent_name} set to manual restart - no automatic restart")
                return False

            # Calculate restart delay
            delay = self._calculate_restart_delay(agent_name, dep_config)

            if delay > 0:
                self.logger.info(f"Waiting {delay} seconds before restarting {agent_name}")
                await asyncio.sleep(delay)

            # Attempt restart
            self.logger.info(f"Attempting restart {current_attempts + 1}/{dep_config.max_restart_attempts} for {agent_name}")
            self.restart_attempts[agent_name] += 1
            self.last_restart_time[agent_name] = time.time()

            success = await self.agent_manager.restart_agent(agent_name)

            if success:
                self.logger.info(f"Successfully restarted {agent_name}")
                self.restart_attempts[agent_name] = 0  # Reset on success
            else:
                self.logger.error(f"Failed to restart {agent_name}")

            return success

        except Exception as e:
            self.logger.error(f"Failed to handle agent failure for {agent_name}: {e}")
            return False

    def _calculate_restart_delay(self, agent_name: str, config: AgentDependency) -> int:
        """Calculate restart delay based on policy."""
        if config.restart_policy == RestartPolicy.IMMEDIATE:
            return 0
        elif config.restart_policy == RestartPolicy.DELAYED:
            return config.restart_delay
        elif config.restart_policy == RestartPolicy.EXPONENTIAL_BACKOFF:
            attempts = self.restart_attempts[agent_name]
            return config.restart_delay * (2 ** attempts)
        else:
            return 0

    def get_dependency_info(self, agent_name: str) -> Optional[AgentDependency]:
        """Get dependency configuration for an agent."""
        return self.dependencies.get(agent_name)

    def get_all_dependencies(self) -> Dict[str, AgentDependency]:
        """Get all agent dependency configurations."""
        return self.dependencies.copy()

    def get_restart_statistics(self) -> Dict[str, Dict[str, int]]:
        """Get restart statistics for all agents."""
        stats = {}
        for agent_name in self.dependencies:
            stats[agent_name] = {
                "restart_attempts": self.restart_attempts[agent_name],
                "max_attempts": self.dependencies[agent_name].max_restart_attempts,
                "last_restart": int(self.last_restart_time.get(agent_name, 0))
            }
        return stats

    def reset_restart_statistics(self, agent_name: Optional[str] = None):
        """Reset restart statistics for agent(s)."""
        if agent_name:
            self.restart_attempts[agent_name] = 0
            if agent_name in self.last_restart_time:
                del self.last_restart_time[agent_name]
            self.logger.info(f"Reset restart statistics for {agent_name}")
        else:
            self.restart_attempts.clear()
            self.last_restart_time.clear()
            self.logger.info("Reset restart statistics for all agents")