"""
Agent management page for Trading Dashboard.

This page provides detailed information about all trading agents,
their configurations, and basic management capabilities.
"""

import streamlit as st
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils.config import get_config_manager


def show_agents():
    """Display the agent management page."""
    st.markdown("## 🤖 Agent Management")

    # Get configuration
    config_manager = get_config_manager()
    agent_configs = config_manager.get_all_agent_configs()
    environment = config_manager.get_environment()

    if not agent_configs:
        st.error("No agent configurations found. Please check your configuration files.")
        return

    # Summary metrics
    enabled_agents = [name for name, config in agent_configs.items() if config.enabled]
    disabled_agents = [name for name, config in agent_configs.items() if not config.enabled]

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total Agents", len(agent_configs))

    with col2:
        st.metric("Enabled Agents", len(enabled_agents), delta=len(enabled_agents))

    with col3:
        st.metric("Disabled Agents", len(disabled_agents), delta=len(disabled_agents))

    st.markdown("---")

    # Agent Details Section
    st.markdown("### 📋 Agent Details")

    # Tabs for different views
    tab1, tab2, tab3 = st.tabs(["🔍 Overview", "⚙️ Configuration", "📊 Status"])

    with tab1:
        show_agent_overview(agent_configs)

    with tab2:
        show_agent_configuration(agent_configs)

    with tab3:
        show_agent_status(agent_configs)

    st.markdown("---")

    # Agent Management Actions
    st.markdown("### ⚡ Quick Actions")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("🔄 Refresh Status", use_container_width=True):
            st.success("Status refreshed! (Health checking will be implemented in Phase 2)")

    with col2:
        if st.button("🚀 Start All", use_container_width=True):
            st.warning("Agent orchestration will be implemented in Phase 2")

    with col3:
        if st.button("⏹️ Stop All", use_container_width=True):
            st.warning("Agent orchestration will be implemented in Phase 2")

    with col4:
        if st.button("🔧 Configure", use_container_width=True):
            st.info("Agent configuration management will be enhanced in Phase 2")


def show_agent_overview(agent_configs):
    """Show agent overview information."""
    st.markdown("#### 🎯 Agent Overview")

    for agent_name, agent_config in agent_configs.items():
        with st.expander(f"{'🟢' if agent_config.enabled else '🔴'} {agent_config.name}"):
            col1, col2 = st.columns(2)

            with col1:
                st.markdown(f"""
                **Basic Information:**
                - **Name:** {agent_config.name}
                - **Status:** {'Enabled' if agent_config.enabled else 'Disabled'}
                - **URL:** `{agent_config.url}`
                - **Timeout:** {agent_config.timeout} seconds
                """)

            with col2:
                st.markdown(f"""
                **Configuration:**
                - **Health Check Interval:** {agent_config.health_check_interval}s
                - **Max Retries:** {agent_config.max_retries}
                - **Agent Key:** `{agent_name}`
                """)

            # Agent-specific information
            if agent_name == "market_data":
                st.markdown("""
                **Purpose:** Collects and processes real-time market data from multiple sources.
                **Key Features:** Data quality scoring, source reliability tracking, real-time price feeds.
                **Status:** Primary agent - Ready for integration
                """)
            elif agent_name == "pattern_recognition":
                st.markdown("""
                **Purpose:** Analyzes market patterns and identifies trading opportunities.
                **Key Features:** Technical analysis, pattern matching, signal generation.
                **Status:** Future implementation - Phase 2
                """)
            elif agent_name == "risk_management":
                st.markdown("""
                **Purpose:** Monitors and manages trading risk across all positions.
                **Key Features:** Position sizing, risk metrics, stop-loss management.
                **Status:** Future implementation - Phase 2
                """)
            elif agent_name == "advisor":
                st.markdown("""
                **Purpose:** Provides trading recommendations and strategy optimization.
                **Key Features:** Portfolio analysis, strategy recommendations, performance insights.
                **Status:** Future implementation - Phase 3
                """)
            elif agent_name == "backtest":
                st.markdown("""
                **Purpose:** Tests trading strategies against historical data.
                **Key Features:** Historical simulation, performance metrics, strategy validation.
                **Status:** Future implementation - Phase 3
                """)


def show_agent_configuration(agent_configs):
    """Show detailed agent configuration."""
    st.markdown("#### ⚙️ Agent Configuration Details")

    # Create a table of configurations
    config_data = []
    for agent_name, agent_config in agent_configs.items():
        config_data.append({
            "Agent": agent_config.name,
            "Key": agent_name,
            "URL": agent_config.url,
            "Enabled": "✅" if agent_config.enabled else "❌",
            "Timeout": f"{agent_config.timeout}s",
            "Health Check": f"{agent_config.health_check_interval}s",
            "Max Retries": agent_config.max_retries
        })

    st.dataframe(config_data, use_container_width=True)

    # Configuration source information
    st.markdown("---")
    st.markdown("#### 📁 Configuration Sources")

    config_manager = get_config_manager()
    environment = config_manager.get_environment()

    st.markdown(f"""
    **Active Configuration Files:**
    - **Main Config:** `config/dashboard.yaml`
    - **Environment Override:** `config/environments/{environment}.yaml`
    - **Environment Variables:** Loaded from `.env` file (if present)

    **Configuration Priority:**
    1. Environment variables (highest priority)
    2. Environment-specific YAML files
    3. Main dashboard.yaml (lowest priority)
    """)


def show_agent_status(agent_configs):
    """Show agent status and health information."""
    st.markdown("#### 📊 Agent Status & Health")

    st.markdown("""
    <div class="alert alert-info">
        <h4>🚧 Health Monitoring Coming in Phase 2</h4>
        <p>Real-time agent health monitoring, API connectivity testing, and performance metrics will be implemented in Phase 2: Agent Communication Framework.</p>
    </div>
    """, unsafe_allow_html=True)

    # Mock status data for demonstration
    for agent_name, agent_config in agent_configs.items():
        with st.container():
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                status_icon = "🟢" if agent_config.enabled else "🔴"
                status_text = "Ready" if agent_config.enabled else "Disabled"
                st.metric(f"{status_icon} {agent_config.name}", status_text)

            with col2:
                # Mock response time
                if agent_config.enabled:
                    st.metric("Response Time", "N/A", delta="Health check pending")
                else:
                    st.metric("Response Time", "Disabled", delta="Not monitored")

            with col3:
                # Mock uptime
                if agent_config.enabled:
                    st.metric("Uptime", "N/A", delta="Not started")
                else:
                    st.metric("Uptime", "0%", delta="Disabled")

            with col4:
                # Mock last check
                st.metric("Last Check", "Never", delta="Pending Phase 2")

        st.markdown("---")

    # Future features preview
    st.markdown("#### 🔮 Planned Features (Phase 2+)")

    feature_cols = st.columns(3)

    with feature_cols[0]:
        st.markdown("""
        **Health Monitoring:**
        - Real-time connectivity testing
        - API endpoint validation
        - Response time tracking
        - Uptime monitoring
        """)

    with feature_cols[1]:
        st.markdown("""
        **Agent Control:**
        - Start/stop individual agents
        - Bulk operations
        - Configuration updates
        - Restart procedures
        """)

    with feature_cols[2]:
        st.markdown("""
        **Performance Metrics:**
        - Resource usage tracking
        - Request/response rates
        - Error rate monitoring
        - Performance analytics
        """)