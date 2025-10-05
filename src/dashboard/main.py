"""
Trading Dashboard - Main Streamlit Application

This is the main entry point for the Trading Dashboard web application.
It provides a comprehensive interface for managing and monitoring autonomous trading agents.
"""

import streamlit as st
import sys
from pathlib import Path
import logging

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import configuration management
from src.utils.config import get_config_manager

# Import pages and components
try:
    from .pages import (
        overview,
        agents,
        charts,
        alerts,
        quality,
        analytics,
        error_handling,
    )
    from .components.error_dashboard import render_error_status_indicator
except ImportError:
    # Fallback for direct execution
    from src.dashboard.pages import (
        overview,
        agents,
        charts,
        alerts,
        quality,
        analytics,
        error_handling,
    )
    from src.dashboard.components.error_dashboard import render_error_status_indicator

# Import agent management
from src.orchestrator import get_agent_manager
import asyncio

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def configure_page():
    """Configure Streamlit page settings and layout."""
    config_manager = get_config_manager()
    dashboard_config = config_manager.get_dashboard_config()

    st.set_page_config(
        page_title=dashboard_config.title,
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={
            "Get Help": "https://github.com/user/trading-dashboard",
            "Report a bug": "https://github.com/user/trading-dashboard/issues",
            "About": f"""
            # {dashboard_config.title}

            {dashboard_config.subtitle}

            **Environment:** {config_manager.get_environment().title()}
            **Version:** 1.0.0 (Phase 1: Foundation)

            This dashboard orchestrates multiple autonomous trading agents:
            - Market Data Agent
            - Pattern Recognition Agent
            - Risk Management Agent
            - Advisor Agent
            - Backtest Agent
            """,
        },
    )


def load_custom_css():
    """Load custom CSS for professional styling - matches LocalAI Finance website."""
    try:
        from .utils.theme_loader import load_custom_css as load_theme
        success = load_theme()
        if success:
            logger.info("✅ Custom theme loaded successfully")
        else:
            logger.warning("⚠️ Custom theme failed to load, using defaults")
    except ImportError:
        # Fallback for direct execution
        from src.dashboard.utils.theme_loader import load_custom_css as load_theme
        success = load_theme()
        if success:
            logger.info("✅ Custom theme loaded successfully")
        else:
            logger.warning("⚠️ Custom theme failed to load, using defaults")


def render_header():
    """Render the main dashboard header."""
    config_manager = get_config_manager()
    dashboard_config = config_manager.get_dashboard_config()
    environment = config_manager.get_environment()

    st.markdown(
        f"""
    <div class="dashboard-header">
        <h1>{dashboard_config.title}</h1>
        <p>{dashboard_config.subtitle}</p>
        <p><strong>Environment:</strong> {environment.title()} | <strong>Auto-refresh:</strong> {dashboard_config.refresh_interval}s</p>
    </div>
    """,
        unsafe_allow_html=True,
    )


def render_navigation():
    """Render the navigation sidebar with system status only."""
    # Add branding at top
    st.sidebar.markdown(
        """
        <div style="text-align: center; padding: 1rem 0;">
            <h2 class="gradient-text">LocalAI Finance</h2>
            <p style="color: var(--text-secondary); font-size: 0.875rem;">Trading Dashboard</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Add divider
    st.sidebar.markdown("---")

    # System status section
    st.sidebar.subheader("🔍 System Status")

    # Quick status indicators
    config_manager = get_config_manager()
    agent_configs = config_manager.get_all_agent_configs()

    enabled_agents = sum(1 for config in agent_configs.values() if config.enabled)
    total_agents = len(agent_configs)

    st.sidebar.markdown(
        f"""
    <div style="font-size: 0.9rem;">
        <div>
            <span class="status-indicator status-healthy"></span>
            <strong>Agents:</strong> {enabled_agents}/{total_agents} enabled
        </div>
        <div style="margin-top: 0.5rem;">
            <span class="status-indicator status-healthy"></span>
            <strong>Config:</strong> Valid
        </div>
        <div style="margin-top: 0.5rem;">
            <span class="status-indicator status-healthy"></span>
            <strong>Environment:</strong> {config_manager.get_environment().title()}
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )


def render_page_content():
    """Render the main page content - now handled by Streamlit's page router."""
    # Streamlit automatically handles page routing with the pages/ folder
    # This function is kept for compatibility but pages are now auto-routed
    pass


def render_placeholder_page(title: str, icon: str, description: str):
    """Render a placeholder page for future implementation."""
    st.markdown(
        f"""
    <div class="alert alert-info">
        <h3>{icon} {title}</h3>
        <p>{description}</p>
        <p><strong>Status:</strong> Planned for future phases</p>
    </div>
    """,
        unsafe_allow_html=True,
    )


def render_footer():
    """Render the dashboard footer."""
    config_manager = get_config_manager()
    environment = config_manager.get_environment()

    st.markdown(
        f"""
    <div class="dashboard-footer">
        <p>Trading Dashboard v1.0.0 | Environment: {environment.title()} |
        Built with Streamlit | 🤖 Generated with Claude Code</p>
    </div>
    """,
        unsafe_allow_html=True,
    )


def initialize_agent_manager():
    """Initialize the Agent Manager and auto-start enabled agents."""
    if "agent_manager" not in st.session_state:
        with st.spinner("Initializing Agent Manager..."):
            try:
                st.session_state.agent_manager = get_agent_manager()
                logger.info("Agent Manager initialized successfully")

                # Auto-start enabled agents on first load
                with st.spinner("Starting required services..."):
                    results = asyncio.run(
                        st.session_state.agent_manager.start_all_enabled_agents(
                            wait_for_health=False
                        )
                    )

                    # Display startup results in sidebar
                    successful_agents = []
                    failed_agents = []

                    for agent_name, success in results.items():
                        if success:
                            successful_agents.append(agent_name)
                        else:
                            failed_agents.append(agent_name)

                    if successful_agents:
                        st.success(f"✅ Started: {', '.join(successful_agents)}")
                    if failed_agents:
                        st.error(f"❌ Failed: {', '.join(failed_agents)}")

            except Exception as e:
                st.error(f"Failed to initialize Agent Manager: {e}")
                logger.error(f"Agent Manager initialization error: {e}")


def main():
    """Main application entry point."""
    try:
        # Configure page
        configure_page()

        # Initialize Agent Manager (only once)
        initialize_agent_manager()

        # Load custom styling
        load_custom_css()

        # Render sidebar navigation and status
        render_navigation()

        # Render header
        render_header()

        # Main content is now handled by Streamlit's page router
        # Each page in pages/ folder renders itself

        # Render footer
        render_footer()

    except Exception as e:
        st.error(f"Application error: {str(e)}")
        logger.error(f"Main application error: {e}")

        # Show debug info if in debug mode
        config_manager = get_config_manager()
        if config_manager.get_dashboard_config().debug:
            st.exception(e)


if __name__ == "__main__":
    main()
