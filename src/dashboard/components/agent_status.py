"""
Agent Status UI Components

This module provides Streamlit components for displaying and managing agent status,
including real-time status monitoring, restart controls, and health information.
"""

import streamlit as st
import asyncio
import time
from typing import Dict
from src.orchestrator import AgentInfo, AgentStatus


def render_agent_status_section():
    """Render the comprehensive agent status section."""
    st.subheader("🤖 Agent Status & Management")

    if 'agent_manager' not in st.session_state:
        st.warning("Agent Manager not initialized. Please refresh the page.")
        return

    agent_manager = st.session_state.agent_manager

    try:
        # Get current agent status
        agents = asyncio.run(agent_manager.get_all_agent_status())

        if not agents:
            st.info("No agents configured for management.")
            return

        # Create status overview cards
        render_status_overview(agents)

        # Detailed agent cards
        st.markdown("---")
        st.subheader("📊 Detailed Agent Information")

        for agent_name, agent_info in agents.items():
            render_agent_card(agent_name, agent_info, agent_manager)

    except Exception as e:
        st.error(f"Failed to load agent status: {e}")


def render_status_overview(agents: Dict[str, AgentInfo]):
    """Render agent status overview cards."""
    # Count agents by status
    status_counts = {
        AgentStatus.RUNNING: 0,
        AgentStatus.STOPPED: 0,
        AgentStatus.ERROR: 0,
        AgentStatus.STARTING: 0,
        AgentStatus.STOPPING: 0
    }

    for agent in agents.values():
        status_counts[agent.status] += 1

    # Create status overview columns
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="🟢 Running",
            value=status_counts[AgentStatus.RUNNING],
            delta=None
        )

    with col2:
        st.metric(
            label="🔴 Stopped",
            value=status_counts[AgentStatus.STOPPED],
            delta=None
        )

    with col3:
        st.metric(
            label="🟡 Starting/Stopping",
            value=status_counts[AgentStatus.STARTING] + status_counts[AgentStatus.STOPPING],
            delta=None
        )

    with col4:
        st.metric(
            label="❌ Errors",
            value=status_counts[AgentStatus.ERROR],
            delta=None
        )


def render_agent_card(agent_name: str, agent_info: AgentInfo, agent_manager):
    """Render a detailed card for a specific agent."""
    # Determine status color and icon
    status_config = get_status_config(agent_info.status)

    # Create expandable agent card
    with st.expander(f"{status_config['icon']} {agent_info.name}", expanded=agent_info.status == AgentStatus.ERROR):
        col1, col2 = st.columns([2, 1])

        with col1:
            # Agent information
            st.write(f"**Name:** {agent_info.name}")
            st.write(f"**Status:** {status_config['icon']} {agent_info.status.value.title()}")
            st.write(f"**URL:** {agent_info.url}")
            st.write(f"**Port:** {agent_info.port}")
            st.write(f"**Path:** {agent_info.path}")

            if agent_info.pid:
                st.write(f"**Process ID:** {agent_info.pid}")

            if agent_info.last_health_check:
                last_check = time.time() - agent_info.last_health_check
                st.write(f"**Last Health Check:** {last_check:.1f}s ago")

            # Error message if present
            if agent_info.error_message:
                st.error(f"**Error:** {agent_info.error_message}")

        with col2:
            # Control buttons
            render_agent_controls(agent_name, agent_info, agent_manager)


def render_agent_controls(agent_name: str, agent_info: AgentInfo, agent_manager):
    """Render control buttons for an agent."""
    st.write("**Controls:**")

    # Start button
    if agent_info.status in [AgentStatus.STOPPED, AgentStatus.ERROR]:
        if st.button(f"▶️ Start", key=f"start_{agent_name}", use_container_width=True):
            with st.spinner(f"Starting {agent_info.name}..."):
                try:
                    success = asyncio.run(agent_manager.start_agent(agent_name, wait_for_health=False))
                    if success:
                        st.success(f"Started {agent_info.name}")
                        st.rerun()
                    else:
                        st.error(f"Failed to start {agent_info.name}")
                except Exception as e:
                    st.error(f"Error starting {agent_info.name}: {e}")

    # Stop button
    if agent_info.status in [AgentStatus.RUNNING, AgentStatus.STARTING]:
        if st.button(f"⏹️ Stop", key=f"stop_{agent_name}", use_container_width=True):
            with st.spinner(f"Stopping {agent_info.name}..."):
                try:
                    success = asyncio.run(agent_manager.stop_agent(agent_name))
                    if success:
                        st.success(f"Stopped {agent_info.name}")
                        st.rerun()
                    else:
                        st.error(f"Failed to stop {agent_info.name}")
                except Exception as e:
                    st.error(f"Error stopping {agent_info.name}: {e}")

    # Restart button (always available except when stopping)
    if agent_info.status != AgentStatus.STOPPING:
        if st.button(f"🔄 Restart", key=f"restart_{agent_name}", use_container_width=True):
            with st.spinner(f"Restarting {agent_info.name}..."):
                try:
                    success = asyncio.run(agent_manager.restart_agent(agent_name))
                    if success:
                        st.success(f"Restarted {agent_info.name}")
                        st.rerun()
                    else:
                        st.error(f"Failed to restart {agent_info.name}")
                except Exception as e:
                    st.error(f"Error restarting {agent_info.name}: {e}")

    # Health check button
    if agent_info.status == AgentStatus.RUNNING:
        if st.button(f"🏥 Health Check", key=f"health_{agent_name}", use_container_width=True):
            with st.spinner(f"Checking {agent_info.name} health..."):
                try:
                    healthy = asyncio.run(agent_manager._check_agent_health(agent_name))
                    if healthy:
                        st.success(f"{agent_info.name} is healthy")
                    else:
                        st.error(f"{agent_info.name} is unhealthy")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error checking {agent_info.name} health: {e}")


def get_status_config(status: AgentStatus) -> dict:
    """Get status configuration (icon, color) for a given status."""
    status_configs = {
        AgentStatus.RUNNING: {"icon": "🟢", "color": "green"},
        AgentStatus.STOPPED: {"icon": "🔴", "color": "red"},
        AgentStatus.ERROR: {"icon": "❌", "color": "red"},
        AgentStatus.STARTING: {"icon": "🟡", "color": "orange"},
        AgentStatus.STOPPING: {"icon": "🟡", "color": "orange"}
    }

    return status_configs.get(status, {"icon": "⚪", "color": "gray"})


def render_agent_management_controls():
    """Render global agent management controls."""
    st.subheader("🎛️ Global Agent Management")

    if 'agent_manager' not in st.session_state:
        st.warning("Agent Manager not initialized.")
        return

    agent_manager = st.session_state.agent_manager

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("▶️ Start All Enabled", use_container_width=True):
            with st.spinner("Starting all enabled agents..."):
                try:
                    results = asyncio.run(agent_manager.start_all_enabled_agents(wait_for_health=False))
                    successful = sum(1 for success in results.values() if success)
                    total = len(results)
                    st.success(f"Started {successful}/{total} agents")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error starting agents: {e}")

    with col2:
        if st.button("⏹️ Stop All", use_container_width=True):
            with st.spinner("Stopping all agents..."):
                try:
                    results = asyncio.run(agent_manager.stop_all_agents())
                    successful = sum(1 for success in results.values() if success)
                    total = len(results)
                    st.success(f"Stopped {successful}/{total} agents")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error stopping agents: {e}")

    with col3:
        if st.button("🔄 Restart All", use_container_width=True):
            with st.spinner("Restarting all agents..."):
                try:
                    # Stop all first
                    await_results = asyncio.run(agent_manager.stop_all_agents())
                    # Wait a moment
                    time.sleep(2)
                    # Start all enabled
                    start_results = asyncio.run(agent_manager.start_all_enabled_agents(wait_for_health=False))
                    successful = sum(1 for success in start_results.values() if success)
                    total = len(start_results)
                    st.success(f"Restarted {successful}/{total} agents")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error restarting agents: {e}")