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
from src.dashboard.pages import overview, agents

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
            'Get Help': 'https://github.com/user/trading-dashboard',
            'Report a bug': "https://github.com/user/trading-dashboard/issues",
            'About': f"""
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
            """
        }
    )


def load_custom_css():
    """Load custom CSS for professional styling."""
    st.markdown("""
    <style>
    /* Main container styling */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }

    /* Header styling */
    .dashboard-header {
        background: linear-gradient(90deg, #1f2937 0%, #374151 100%);
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
    }

    .dashboard-header h1 {
        color: white !important;
        margin-bottom: 0.5rem;
    }

    .dashboard-header p {
        color: #d1d5db;
        margin-bottom: 0;
    }

    /* Status indicators */
    .status-indicator {
        display: inline-block;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        margin-right: 8px;
    }

    .status-healthy {
        background-color: #10b981;
    }

    .status-warning {
        background-color: #f59e0b;
    }

    .status-error {
        background-color: #ef4444;
    }

    .status-disabled {
        background-color: #6b7280;
    }

    /* Card styling */
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border: 1px solid #e5e7eb;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        margin-bottom: 1rem;
    }

    /* Sidebar styling */
    .sidebar .sidebar-content {
        background-color: #f9fafb;
    }

    /* Navigation styling */
    .nav-link {
        display: block;
        padding: 0.75rem 1rem;
        margin: 0.25rem 0;
        background: #f3f4f6;
        border-radius: 0.375rem;
        text-decoration: none;
        color: #374151;
        transition: all 0.2s;
    }

    .nav-link:hover {
        background: #e5e7eb;
        color: #111827;
    }

    .nav-link.active {
        background: #3b82f6;
        color: white;
    }

    /* Alert styling */
    .alert {
        padding: 1rem;
        border-radius: 0.375rem;
        margin: 1rem 0;
    }

    .alert-info {
        background-color: #dbeafe;
        border: 1px solid #93c5fd;
        color: #1e40af;
    }

    .alert-warning {
        background-color: #fef3c7;
        border: 1px solid #fbbf24;
        color: #92400e;
    }

    .alert-error {
        background-color: #fee2e2;
        border: 1px solid #fca5a5;
        color: #dc2626;
    }

    /* Footer styling */
    .dashboard-footer {
        text-align: center;
        color: #6b7280;
        font-size: 0.875rem;
        padding: 2rem 0 1rem 0;
        border-top: 1px solid #e5e7eb;
        margin-top: 3rem;
    }

    /* Hide Streamlit default elements */
    #MainMenu {visibility: hidden;}
    .stDeployButton {display: none;}
    footer {visibility: hidden;}
    .stApp > header {visibility: hidden;}

    /* Custom button styling */
    .stButton > button {
        background-color: #3b82f6;
        color: white;
        border: none;
        border-radius: 0.375rem;
        padding: 0.5rem 1rem;
        font-weight: 500;
        transition: all 0.2s;
    }

    .stButton > button:hover {
        background-color: #2563eb;
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
    }
    </style>
    """, unsafe_allow_html=True)


def render_header():
    """Render the main dashboard header."""
    config_manager = get_config_manager()
    dashboard_config = config_manager.get_dashboard_config()
    environment = config_manager.get_environment()

    st.markdown(f"""
    <div class="dashboard-header">
        <h1>{dashboard_config.title}</h1>
        <p>{dashboard_config.subtitle}</p>
        <p><strong>Environment:</strong> {environment.title()} | <strong>Auto-refresh:</strong> {dashboard_config.refresh_interval}s</p>
    </div>
    """, unsafe_allow_html=True)


def render_navigation():
    """Render the navigation sidebar."""
    st.sidebar.title("📊 Navigation")

    # Navigation pages
    pages = {
        "🏠 Overview": "overview",
        "🤖 Agents": "agents",
        "📈 Trading": "trading",
        "📊 Analytics": "analytics",
        "⚙️ Settings": "settings"
    }

    # Get current page from session state
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'overview'

    # Create navigation buttons
    for page_name, page_key in pages.items():
        if st.sidebar.button(page_name, key=f"nav_{page_key}", use_container_width=True):
            st.session_state.current_page = page_key

    # Add divider
    st.sidebar.markdown("---")

    # System status section
    st.sidebar.subheader("🔍 System Status")

    # Quick status indicators
    config_manager = get_config_manager()
    agent_configs = config_manager.get_all_agent_configs()

    enabled_agents = sum(1 for config in agent_configs.values() if config.enabled)
    total_agents = len(agent_configs)

    st.sidebar.markdown(f"""
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
    """, unsafe_allow_html=True)


def render_page_content():
    """Render the main page content based on current selection."""
    current_page = st.session_state.get('current_page', 'overview')

    try:
        if current_page == 'overview':
            overview.show_overview()
        elif current_page == 'agents':
            agents.show_agents()
        elif current_page == 'trading':
            render_placeholder_page("Trading Interface", "🔄",
                "Real-time trading interface will be implemented in Phase 2")
        elif current_page == 'analytics':
            render_placeholder_page("Analytics Dashboard", "📈",
                "Performance analytics and metrics will be implemented in Phase 3")
        elif current_page == 'settings':
            render_placeholder_page("Settings", "⚙️",
                "Configuration settings interface will be implemented in Phase 2")
        else:
            overview.show_overview()

    except Exception as e:
        st.error(f"Error loading page '{current_page}': {str(e)}")
        logger.error(f"Page loading error: {e}")


def render_placeholder_page(title: str, icon: str, description: str):
    """Render a placeholder page for future implementation."""
    st.markdown(f"""
    <div class="alert alert-info">
        <h3>{icon} {title}</h3>
        <p>{description}</p>
        <p><strong>Status:</strong> Planned for future phases</p>
    </div>
    """, unsafe_allow_html=True)


def render_footer():
    """Render the dashboard footer."""
    config_manager = get_config_manager()
    environment = config_manager.get_environment()

    st.markdown(f"""
    <div class="dashboard-footer">
        <p>Trading Dashboard v1.0.0 | Environment: {environment.title()} |
        Built with Streamlit | 🤖 Generated with Claude Code</p>
    </div>
    """, unsafe_allow_html=True)


def initialize_agent_manager():
    """Initialize the Agent Manager and auto-start enabled agents."""
    if 'agent_manager' not in st.session_state:
        with st.spinner("Initializing Agent Manager..."):
            try:
                st.session_state.agent_manager = get_agent_manager()
                logger.info("Agent Manager initialized successfully")

                # Auto-start enabled agents on first load
                with st.spinner("Starting required services..."):
                    results = asyncio.run(
                        st.session_state.agent_manager.start_all_enabled_agents(wait_for_health=False)
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

        # Render header
        render_header()

        # Create two-column layout
        with st.container():
            # Render navigation sidebar
            render_navigation()

            # Render main content
            render_page_content()

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