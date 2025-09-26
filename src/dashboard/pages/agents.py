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
from src.dashboard.components import (
    render_agent_status_section,
    render_agent_management_controls,
    render_agent_status_grid,
    render_bulk_operations,
    render_resource_monitoring
)
from src.orchestrator import get_agent_manager, AgentStatus


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
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🎮 Live Control", "🔍 Overview", "⚙️ Configuration", "📊 Legacy Status", "📈 Advanced Monitoring"
    ])

    with tab1:
        # Primary Live Agent Management Interface
        render_agent_management_controls()
        st.markdown("---")
        render_agent_status_section()

    with tab2:
        show_agent_overview(agent_configs)

    with tab3:
        show_agent_configuration(agent_configs)

    with tab4:
        show_agent_status(agent_configs)

    with tab5:
        # Advanced monitoring and analytics
        render_advanced_monitoring()

    st.markdown("---")

    # Quick Actions (Legacy - now available in Live Control tab)
    st.markdown("### ⚡ Legacy Quick Actions")
    st.info("🎮 **New!** Advanced agent controls are now available in the **Live Control** tab above with real-time status monitoring, dependency-aware operations, and resource management.")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("🔄 Refresh Status", use_container_width=True):
            st.success("✅ Status refreshed! Switch to Live Control tab for real-time updates.")

    with col2:
        if st.button("🚀 Start All (Legacy)", use_container_width=True):
            st.info("ℹ️ Use the advanced 'Start All' button in the Live Control tab for dependency-aware startup.")

    with col3:
        if st.button("⏹️ Stop All (Legacy)", use_container_width=True):
            st.info("ℹ️ Use the advanced 'Stop All' button in the Live Control tab for graceful shutdown.")

    with col4:
        if st.button("🔧 Configure", use_container_width=True):
            st.info("🚧 Dynamic configuration management will be available in Phase 3 Step 4.")


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


def render_advanced_monitoring():
    """Render advanced monitoring and analytics interface."""
    st.markdown("#### 📊 Advanced System Monitoring")

    agent_manager = get_agent_manager()

    # System overview
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("##### 🏗️ Architecture Status")
        total_agents = len(agent_manager.agents)
        running_count = sum(1 for name in agent_manager.agents
                          if agent_manager.get_agent_status(name) == AgentStatus.RUNNING)

        st.metric("Total Agents", total_agents)
        st.metric("Running Agents", running_count, delta=f"{running_count}/{total_agents}")

    with col2:
        st.markdown("##### 🔄 Dependency Graph")
        if hasattr(agent_manager, 'dependency_manager'):
            dep_count = len(agent_manager.dependency_manager.dependencies)
            st.metric("Dependencies Configured", dep_count)

            # Show startup sequence
            if dep_count > 0:
                sequence = agent_manager.dependency_manager.create_startup_sequence()
                st.markdown("**Startup Order:**")
                for i, group in enumerate(sequence):
                    st.markdown(f"**Group {i+1}:** {', '.join(group)}")
        else:
            st.info("Dependency manager not available")

    with col3:
        st.markdown("##### ⚡ Performance Metrics")
        if hasattr(agent_manager, 'resource_manager'):
            summary = agent_manager.resource_manager.get_resource_summary()
            total_cpu = summary.get('system_totals', {}).get('total_cpu_percent', 0)
            total_memory = summary.get('system_totals', {}).get('total_memory_mb', 0)

            st.metric("System CPU Usage", f"{total_cpu:.1f}%")
            st.metric("System Memory Usage", f"{total_memory:.0f} MB")
        else:
            st.info("Resource manager not available")

    st.markdown("---")

    # Agent health matrix
    st.markdown("##### 🏥 Agent Health Matrix")

    if agent_manager.agents:
        health_data = []
        for agent_name, agent_info in agent_manager.agents.items():
            status = agent_manager.get_agent_status(agent_name)
            health_score = agent_manager.get_health_score(agent_name)
            metrics = agent_manager.get_resource_metrics(agent_name)

            health_data.append({
                "Agent": agent_info.name,
                "Status": status.value.title(),
                "Health Score": f"{health_score:.1f}%" if health_score else "N/A",
                "CPU %": f"{metrics.cpu_percent:.1f}" if metrics else "N/A",
                "Memory MB": f"{metrics.memory_mb:.0f}" if metrics else "N/A",
                "Uptime": f"{metrics.uptime_seconds/3600:.1f}h" if metrics and metrics.uptime_seconds > 0 else "N/A",
                "Restarts": str(metrics.restart_count) if metrics else "0"
            })

        st.dataframe(health_data, use_container_width=True)

        # Resource usage charts
        if any(data["CPU %"] != "N/A" for data in health_data):
            st.markdown("##### 📈 Resource Usage Visualization")

            # Create simple bar chart data
            chart_data = []
            for data in health_data:
                if data["CPU %"] != "N/A":
                    chart_data.append({
                        "Agent": data["Agent"],
                        "CPU %": float(data["CPU %"]),
                        "Memory MB": float(data["Memory MB"]) if data["Memory MB"] != "N/A" else 0
                    })

            if chart_data:
                import pandas as pd
                df = pd.DataFrame(chart_data)

                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("**CPU Usage by Agent**")
                    st.bar_chart(df.set_index("Agent")["CPU %"])

                with col2:
                    st.markdown("**Memory Usage by Agent**")
                    st.bar_chart(df.set_index("Agent")["Memory MB"])

    else:
        st.info("No agents configured for monitoring")

    # Troubleshooting section
    st.markdown("---")
    st.markdown("##### 🔧 System Diagnostics")

    diag_col1, diag_col2 = st.columns(2)

    with diag_col1:
        st.markdown("**Health Checks:**")
        if st.button("Run All Health Checks", use_container_width=True):
            with st.spinner("Running health checks..."):
                results = {}
                for agent_name in agent_manager.agents:
                    try:
                        health_url = f"http://localhost:{agent_manager.agents[agent_name].port}/health"
                        import requests
                        response = requests.get(health_url, timeout=5)
                        results[agent_name] = "✅ Healthy" if response.status_code == 200 else f"❌ Error {response.status_code}"
                    except Exception as e:
                        results[agent_name] = f"❌ Connection failed: {str(e)[:50]}"

                for agent_name, result in results.items():
                    st.markdown(f"**{agent_name}:** {result}")

    with diag_col2:
        st.markdown("**System Information:**")
        import platform
        import psutil

        st.markdown(f"""
        **Platform:** {platform.system()} {platform.release()}
        **Python:** {platform.python_version()}
        **CPU Cores:** {psutil.cpu_count()}
        **Total Memory:** {psutil.virtual_memory().total / (1024**3):.1f} GB
        **Available Memory:** {psutil.virtual_memory().available / (1024**3):.1f} GB
        """)

    # Export system state
    st.markdown("---")
    if st.button("📥 Export System State", use_container_width=True):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        state_data = {
            "timestamp": timestamp,
            "agents": {},
            "system_metrics": {}
        }

        for agent_name, agent_info in agent_manager.agents.items():
            state_data["agents"][agent_name] = {
                "status": agent_manager.get_agent_status(agent_name).value,
                "health_score": agent_manager.get_health_score(agent_name),
                "metrics": agent_manager.get_resource_metrics(agent_name).__dict__ if agent_manager.get_resource_metrics(agent_name) else None
            }

        # Convert to JSON for display
        import json
        json_data = json.dumps(state_data, indent=2, default=str)
        st.download_button(
            label="💾 Download System State",
            data=json_data,
            file_name=f"system_state_{timestamp}.json",
            mime="application/json"
        )
        st.success("✅ System state exported successfully!")