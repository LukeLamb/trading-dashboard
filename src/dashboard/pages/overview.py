"""
Overview page for Trading Dashboard.

This page provides a comprehensive overview of the trading system status,
including agent health, system metrics, and key information.
"""

import streamlit as st
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils.config import get_config_manager
from src.dashboard.components.alerts import get_alert_manager
from src.dashboard.components.error_dashboard import render_error_status_indicator


def show_overview():
    """Display the main overview page."""
    st.markdown("## 🏠 System Overview")

    # Show error status indicator
    try:
        has_issues = render_error_status_indicator()
        if has_issues:
            st.info(
                "💡 Check the Error Handling page for detailed diagnostics and troubleshooting."
            )
    except Exception:
        pass  # Silently handle any errors in error status display

    # Get configuration
    config_manager = get_config_manager()
    dashboard_config = config_manager.get_dashboard_config()
    agent_configs = config_manager.get_all_agent_configs()
    environment = config_manager.get_environment()

    # Create metrics row
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        enabled_agents = sum(1 for config in agent_configs.values() if config.enabled)
        total_agents = len(agent_configs)
        st.metric(
            label="🤖 Active Agents",
            value=f"{enabled_agents}/{total_agents}",
            delta="1 enabled" if enabled_agents > 0 else "All disabled",
        )

    with col2:
        st.metric(
            label="🌍 Environment",
            value=environment.title(),
            delta="Development" if environment == "development" else None,
        )

    with col3:
        st.metric(
            label="⚡ Refresh Rate",
            value=f"{dashboard_config.refresh_interval}s",
            delta=(
                "Auto-refresh" if dashboard_config.refresh_interval <= 5 else "Manual"
            ),
        )

    with col4:
        # Alert status
        try:
            alert_manager = get_alert_manager()
            active_alerts = alert_manager.get_active_alerts()
            alert_count = len(active_alerts)

            # Check for high severity alerts
            critical_alerts = sum(
                1
                for alert in active_alerts
                if alert.severity.value in ["critical", "emergency"]
            )

            if critical_alerts > 0:
                delta = f"{critical_alerts} critical"
                delta_color = "inverse"
            elif alert_count > 0:
                delta = f"{alert_count} active"
                delta_color = "normal"
            else:
                delta = "All clear"
                delta_color = "normal"

            st.metric(label="🚨 Alerts", value=str(alert_count), delta=delta)
        except Exception:
            st.metric(label="🚨 Alerts", value="N/A", delta="Not configured")

    st.markdown("---")

    # Active Alerts Section (if any)
    try:
        alert_manager = get_alert_manager()
        active_alerts = alert_manager.get_active_alerts()

        if active_alerts:
            st.markdown("### 🚨 Active Alerts")

            # Show only critical/emergency alerts in overview
            high_priority_alerts = [
                alert
                for alert in active_alerts
                if alert.severity.value in ["critical", "emergency", "high"]
            ]

            if high_priority_alerts:
                for alert in high_priority_alerts[:3]:  # Show max 3 alerts
                    severity_emoji = {
                        "emergency": "🚨",
                        "critical": "🔴",
                        "high": "🟠",
                    }.get(alert.severity.value, "⚠️")

                    st.warning(
                        f"{severity_emoji} **{alert.rule_name}**: {alert.message} "
                        f"({alert.triggered_at.strftime('%H:%M:%S')})"
                    )

                if len(active_alerts) > 3:
                    st.info(
                        f"+ {len(active_alerts) - 3} more alerts. Visit the Alerts page for details."
                    )

                # Quick link to alerts page
                if st.button("🚨 Go to Alerts Page", type="secondary"):
                    st.session_state.current_page = "alerts"
                    st.rerun()
            else:
                st.info(
                    f"{len(active_alerts)} low-priority alerts active. Visit the Alerts page for details."
                )

    except Exception as e:
        # Don't show error in overview, just skip alerts section
        pass

    st.markdown("---")

    # Agent Status Section
    st.markdown("### 🤖 Agent Status")

    if not agent_configs:
        st.warning("No agent configurations found.")
        return

    # Create columns for agent status
    cols = st.columns(min(len(agent_configs), 3))

    for idx, (agent_name, agent_config) in enumerate(agent_configs.items()):
        col_idx = idx % 3
        with cols[col_idx]:
            status_color = "🟢" if agent_config.enabled else "🔴"
            status_text = "Enabled" if agent_config.enabled else "Disabled"

            st.markdown(
                f"""
            <div class="metric-card">
                <h4>{status_color} {agent_config.name}</h4>
                <p><strong>Status:</strong> {status_text}</p>
                <p><strong>URL:</strong> <code>{agent_config.url}</code></p>
                <p><strong>Timeout:</strong> {agent_config.timeout}s</p>
            </div>
            """,
                unsafe_allow_html=True,
            )

    st.markdown("---")

    # System Information Section
    st.markdown("### ℹ️ System Information")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 📋 Configuration")
        st.markdown(
            f"""
        - **Dashboard Title:** {dashboard_config.title}
        - **Environment:** {environment}
        - **Debug Mode:** {'On' if dashboard_config.debug else 'Off'}
        - **Host:** {dashboard_config.host}
        - **Port:** {dashboard_config.port}
        """
        )

    with col2:
        st.markdown("#### 🔧 System Status")

        # Configuration validation
        is_config_valid = config_manager.validate_configuration()
        config_status = "✅ Valid" if is_config_valid else "❌ Invalid"

        # Agent count
        agent_summary = (
            f"{enabled_agents} enabled, {total_agents - enabled_agents} disabled"
        )

        st.markdown(
            f"""
        - **Configuration:** {config_status}
        - **Total Agents:** {total_agents}
        - **Agent Summary:** {agent_summary}
        - **Last Updated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        """
        )

    st.markdown("---")

    # Development Status Section
    st.markdown("### 🚧 Development Status")

    phases = [
        (
            "Phase 1: Foundation Setup",
            "🟢",
            "In Progress",
            [
                ("Step 1: Project Structure", "✅", "Completed"),
                ("Step 2: Configuration System", "✅", "Completed"),
                ("Step 3: Basic Streamlit App", "🔄", "In Progress"),
                ("Step 4: Core Utilities", "⏳", "Pending"),
            ],
        ),
        (
            "Phase 2: Agent Communication",
            "⏳",
            "Planned",
            [
                ("API Client Framework", "⏳", "Planned"),
                ("Health Monitoring", "⏳", "Planned"),
                ("Agent Orchestration", "⏳", "Planned"),
            ],
        ),
        (
            "Phase 3: Real-time Visualization",
            "⏳",
            "Future",
            [
                ("Interactive Charts", "⏳", "Future"),
                ("System Metrics", "⏳", "Future"),
                ("Data Quality Monitoring", "⏳", "Future"),
            ],
        ),
    ]

    for phase_name, phase_status, phase_desc, steps in phases:
        with st.expander(f"{phase_status} {phase_name} - {phase_desc}"):
            for step_name, step_status, step_desc in steps:
                st.markdown(f"{step_status} **{step_name}**: {step_desc}")

    # Quick Actions Section
    st.markdown("---")
    st.markdown("### ⚡ Quick Actions")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.experimental_rerun()

    with col2:
        if st.button("⚙️ View Config", use_container_width=True):
            st.session_state.current_page = "settings"
            st.experimental_rerun()

    with col3:
        if st.button("🤖 Manage Agents", use_container_width=True):
            st.session_state.current_page = "agents"
            st.experimental_rerun()

    with col4:
        if st.button("📊 View Analytics", use_container_width=True):
            st.session_state.current_page = "analytics"
            st.experimental_rerun()

    # Recent Activity (Placeholder)
    st.markdown("---")
    st.markdown("### 📝 Recent Activity")

    st.markdown(
        """
    <div class="alert alert-info">
        <p>📋 <strong>Activity log will be implemented in Phase 2</strong></p>
        <p>This section will show recent system events, agent status changes, and user actions.</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

# Execute page content
if __name__ == '__main__' or True:
    show_overview()
