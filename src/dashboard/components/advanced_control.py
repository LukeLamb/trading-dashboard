"""
Advanced Agent Control Components for Trading Dashboard

This module provides advanced Streamlit components for comprehensive agent management,
including real-time status monitoring, bulk operations, and resource management.
"""

import streamlit as st
import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.orchestrator import get_agent_manager, AgentStatus, ResourceMetrics
from src.orchestrator.dependency_manager import DependencyManager, RestartPolicy
from src.orchestrator.resource_manager import ResourceManager, AlertLevel


def render_agent_status_grid():
    """Render advanced agent status grid with visual indicators and metrics."""
    agent_manager = get_agent_manager()

    st.markdown("### 🔍 Agent Status Grid")

    if not agent_manager.agents:
        st.info("No agents configured. Check your configuration files.")
        return

    # Create grid layout
    num_agents = len(agent_manager.agents)
    cols_per_row = min(3, num_agents)

    for i in range(0, num_agents, cols_per_row):
        agent_batch = list(agent_manager.agents.items())[i:i+cols_per_row]
        cols = st.columns(len(agent_batch))

        for col, (agent_name, agent_info) in zip(cols, agent_batch):
            with col:
                render_agent_status_card(agent_name, agent_info)


def render_agent_status_card(agent_name: str, agent_info):
    """Render individual agent status card with metrics and controls."""
    agent_manager = get_agent_manager()

    # Get current status and metrics
    status = agent_manager.get_agent_status(agent_name)
    metrics = agent_manager.get_resource_metrics(agent_name)
    health_score = agent_manager.get_health_score(agent_name)

    # Status indicator and colors
    status_colors = {
        AgentStatus.RUNNING: ("🟢", "#28a745", "success"),
        AgentStatus.STOPPED: ("🔴", "#dc3545", "error"),
        AgentStatus.STARTING: ("🟡", "#ffc107", "warning"),
        AgentStatus.STOPPING: ("🟠", "#fd7e14", "warning"),
        AgentStatus.ERROR: ("❌", "#dc3545", "error")
    }

    icon, color, status_type = status_colors.get(status, ("❓", "#6c757d", "info"))

    # Create card container
    with st.container():
        st.markdown(f"""
        <div style="
            border: 2px solid {color};
            border-radius: 10px;
            padding: 15px;
            margin: 10px 0;
            background: linear-gradient(135deg, {color}20, {color}05);
        ">
        """, unsafe_allow_html=True)

        # Agent header
        st.markdown(f"### {icon} {agent_info.name}")
        st.markdown(f"**Status:** {status.value.title()}")

        # Health score with progress bar
        if health_score is not None:
            st.markdown("**Health Score:**")
            st.progress(health_score / 100, text=f"{health_score:.1f}%")

        # Resource metrics
        if metrics and status == AgentStatus.RUNNING:
            st.markdown("**Resources:**")
            col1, col2 = st.columns(2)

            with col1:
                st.metric("CPU", f"{metrics.cpu_percent:.1f}%")
                st.metric("Memory", f"{metrics.memory_mb:.0f} MB")

            with col2:
                uptime_str = _format_uptime(metrics.uptime_seconds)
                st.metric("Uptime", uptime_str)
                st.metric("Restarts", metrics.restart_count)

        # Process information
        if agent_info.pid and status == AgentStatus.RUNNING:
            st.markdown(f"**PID:** {agent_info.pid}")
            st.markdown(f"**Port:** {agent_info.port}")

        # Individual controls
        render_individual_agent_controls(agent_name)

        st.markdown("</div>", unsafe_allow_html=True)


def render_individual_agent_controls(agent_name: str):
    """Render individual agent control buttons."""
    agent_manager = get_agent_manager()
    status = agent_manager.get_agent_status(agent_name)

    col1, col2, col3 = st.columns(3)

    with col1:
        if status == AgentStatus.STOPPED:
            if st.button("🚀 Start", key=f"start_{agent_name}", use_container_width=True):
                with st.spinner(f"Starting {agent_name}..."):
                    result = asyncio.run(agent_manager.start_agent(agent_name))
                    if result:
                        st.success(f"✅ {agent_name} started successfully!")
                        st.rerun()
                    else:
                        st.error(f"❌ Failed to start {agent_name}")
        else:
            st.button("🚀 Start", disabled=True, use_container_width=True)

    with col2:
        if status == AgentStatus.RUNNING:
            if st.button("⏹️ Stop", key=f"stop_{agent_name}", use_container_width=True):
                with st.spinner(f"Stopping {agent_name}..."):
                    result = asyncio.run(agent_manager.stop_agent(agent_name))
                    if result:
                        st.success(f"✅ {agent_name} stopped successfully!")
                        st.rerun()
                    else:
                        st.error(f"❌ Failed to stop {agent_name}")
        else:
            st.button("⏹️ Stop", disabled=True, use_container_width=True)

    with col3:
        if status in [AgentStatus.RUNNING, AgentStatus.ERROR]:
            if st.button("🔄 Restart", key=f"restart_{agent_name}", use_container_width=True):
                with st.spinner(f"Restarting {agent_name}..."):
                    result = asyncio.run(agent_manager.restart_agent(agent_name))
                    if result:
                        st.success(f"✅ {agent_name} restarted successfully!")
                        st.rerun()
                    else:
                        st.error(f"❌ Failed to restart {agent_name}")
        else:
            st.button("🔄 Restart", disabled=True, use_container_width=True)


def render_bulk_operations():
    """Render bulk operation controls with dependency management."""
    agent_manager = get_agent_manager()
    dependency_manager = agent_manager.dependency_manager

    st.markdown("### ⚡ Bulk Operations")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("🚀 Start All", use_container_width=True, type="primary"):
            with st.spinner("Starting agents in dependency order..."):
                startup_sequence = dependency_manager.create_startup_sequence()
                success_count = 0

                progress_bar = st.progress(0, text="Preparing startup sequence...")

                for i, group in enumerate(startup_sequence):
                    # Update progress
                    progress = (i + 1) / len(startup_sequence)
                    progress_bar.progress(progress, text=f"Starting group {i+1}/{len(startup_sequence)}")

                    # Start agents in this dependency group in parallel
                    tasks = []
                    for agent_name in group:
                        if agent_manager.get_agent_status(agent_name) == AgentStatus.STOPPED:
                            tasks.append(agent_manager.start_agent(agent_name))

                    if tasks:
                        results = asyncio.run(_run_parallel_tasks(tasks))
                        success_count += sum(1 for result in results if result)

                        # Brief pause between groups
                        time.sleep(1)

                st.success(f"✅ Startup complete! {success_count} agents started successfully.")
                st.rerun()

    with col2:
        if st.button("⏹️ Stop All", use_container_width=True):
            with st.spinner("Stopping all agents..."):
                running_agents = [name for name, info in agent_manager.agents.items()
                                if agent_manager.get_agent_status(name) == AgentStatus.RUNNING]

                if running_agents:
                    # Stop in reverse dependency order
                    shutdown_sequence = list(reversed(dependency_manager.create_startup_sequence()))
                    success_count = 0

                    progress_bar = st.progress(0, text="Shutting down agents...")

                    for i, group in enumerate(shutdown_sequence):
                        # Update progress
                        progress = (i + 1) / len(shutdown_sequence)
                        progress_bar.progress(progress, text=f"Stopping group {i+1}/{len(shutdown_sequence)}")

                        # Stop agents in this group
                        tasks = []
                        for agent_name in group:
                            if agent_name in running_agents:
                                tasks.append(agent_manager.stop_agent(agent_name))

                        if tasks:
                            results = asyncio.run(_run_parallel_tasks(tasks))
                            success_count += sum(1 for result in results if result)

                    st.success(f"✅ Shutdown complete! {success_count} agents stopped successfully.")
                else:
                    st.info("ℹ️ No agents are currently running.")
                st.rerun()

    with col3:
        if st.button("🔄 Restart All", use_container_width=True):
            with st.spinner("Restarting all agents..."):
                # First stop all running agents
                running_agents = [name for name, info in agent_manager.agents.items()
                                if agent_manager.get_agent_status(name) == AgentStatus.RUNNING]

                if running_agents:
                    # Stop all first
                    stop_tasks = [agent_manager.stop_agent(name) for name in running_agents]
                    asyncio.run(_run_parallel_tasks(stop_tasks))
                    time.sleep(2)  # Brief pause

                # Then start all in dependency order
                startup_sequence = dependency_manager.create_startup_sequence()
                success_count = 0

                for group in startup_sequence:
                    tasks = [agent_manager.start_agent(name) for name in group]
                    results = asyncio.run(_run_parallel_tasks(tasks))
                    success_count += sum(1 for result in results if result)
                    time.sleep(1)

                st.success(f"✅ Restart complete! {success_count} agents restarted successfully.")
                st.rerun()

    with col4:
        if st.button("🚨 Emergency Stop", use_container_width=True, type="secondary"):
            if st.session_state.get('confirm_emergency_stop', False):
                with st.spinner("Emergency shutdown in progress..."):
                    # Force stop all agents immediately
                    tasks = []
                    for agent_name, agent_info in agent_manager.agents.items():
                        if agent_info.pid:
                            tasks.append(agent_manager.stop_agent(agent_name, force=True))

                    if tasks:
                        asyncio.run(_run_parallel_tasks(tasks))

                    st.warning("⚠️ Emergency stop completed. All agents forcefully terminated.")
                    st.session_state['confirm_emergency_stop'] = False
                    st.rerun()
            else:
                st.session_state['confirm_emergency_stop'] = True
                st.warning("⚠️ Click again to confirm emergency stop!")


def render_resource_monitoring():
    """Render resource monitoring dashboard with alerts and recommendations."""
    agent_manager = get_agent_manager()

    if hasattr(agent_manager, 'resource_manager'):
        resource_manager = agent_manager.resource_manager

        st.markdown("### 📊 Resource Monitoring")

        # System resource summary
        summary = resource_manager.get_resource_summary()

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Active Alerts", summary.get('active_alerts', 0))

        with col2:
            st.metric("Running Agents", summary.get('system_totals', {}).get('running_agents', 0))

        with col3:
            total_cpu = summary.get('system_totals', {}).get('total_cpu_percent', 0)
            st.metric("Total CPU Usage", f"{total_cpu:.1f}%")

        with col4:
            total_memory = summary.get('system_totals', {}).get('total_memory_mb', 0)
            st.metric("Total Memory", f"{total_memory:.0f} MB")

        # Active alerts
        active_alerts = resource_manager.get_active_alerts()
        if active_alerts:
            st.markdown("#### 🚨 Active Alerts")

            for i, alert in enumerate(active_alerts[:5]):  # Show top 5 alerts
                alert_colors = {
                    AlertLevel.WARNING: "orange",
                    AlertLevel.CRITICAL: "red",
                    AlertLevel.EMERGENCY: "darkred"
                }
                color = alert_colors.get(alert.alert_level, "gray")

                st.markdown(f"""
                <div style="border-left: 4px solid {color}; padding-left: 10px; margin: 5px 0;">
                    <strong>{alert.alert_level.value.upper()}</strong> - {alert.agent_name}<br>
                    {alert.message}<br>
                    <small>Current: {alert.current_value:.1f}% | Threshold: {alert.threshold_value:.1f}%</small>
                </div>
                """, unsafe_allow_html=True)

        # Performance recommendations
        st.markdown("#### 💡 Performance Recommendations")

        recommendations_shown = False
        for agent_name in agent_manager.agents:
            recommendations = resource_manager.get_performance_recommendations(agent_name)
            if recommendations and len(recommendations) > 1:  # More than just "insufficient data"
                recommendations_shown = True
                with st.expander(f"📈 {agent_name} Recommendations"):
                    for rec in recommendations:
                        st.markdown(f"• {rec}")

        if not recommendations_shown:
            st.info("✅ No performance recommendations at this time. All agents operating within normal parameters.")


def render_agent_management_controls():
    """Main agent management control interface."""
    st.markdown("### 🎮 Agent Management Center")

    # Auto-refresh toggle
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        st.markdown("**Live Dashboard** - Real-time agent monitoring and control")

    with col2:
        auto_refresh = st.checkbox("Auto-refresh (10s)", value=st.session_state.get('auto_refresh', False))
        st.session_state['auto_refresh'] = auto_refresh

    with col3:
        if st.button("🔄 Refresh Now", use_container_width=True):
            st.rerun()

    # Auto-refresh logic
    if auto_refresh:
        time.sleep(0.1)  # Small delay to prevent immediate rerun
        if 'last_refresh' not in st.session_state or time.time() - st.session_state['last_refresh'] > 10:
            st.session_state['last_refresh'] = time.time()
            st.rerun()


def render_agent_status_section():
    """Render the main agent status section with all components."""
    # Status grid
    render_agent_status_grid()

    st.markdown("---")

    # Bulk operations
    render_bulk_operations()

    st.markdown("---")

    # Resource monitoring (if available)
    render_resource_monitoring()


# Helper functions

async def _run_parallel_tasks(tasks):
    """Run multiple async tasks in parallel."""
    if not tasks:
        return []
    return await asyncio.gather(*tasks, return_exceptions=True)


def _format_uptime(seconds: float) -> str:
    """Format uptime seconds into readable string."""
    if seconds < 60:
        return f"{seconds:.0f}s"
    elif seconds < 3600:
        return f"{seconds/60:.0f}m"
    elif seconds < 86400:
        hours = int(seconds / 3600)
        minutes = int((seconds % 3600) / 60)
        return f"{hours}h {minutes}m"
    else:
        days = int(seconds / 86400)
        hours = int((seconds % 86400) / 3600)
        return f"{days}d {hours}h"


def _get_status_color(status: AgentStatus) -> str:
    """Get color code for agent status."""
    colors = {
        AgentStatus.RUNNING: "#28a745",
        AgentStatus.STOPPED: "#dc3545",
        AgentStatus.STARTING: "#ffc107",
        AgentStatus.STOPPING: "#fd7e14",
        AgentStatus.ERROR: "#dc3545"
    }
    return colors.get(status, "#6c757d")