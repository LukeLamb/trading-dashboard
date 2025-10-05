"""
Error Handling and Diagnostics Dashboard Components.

This module provides Streamlit components for displaying error handling status,
diagnostic results, and system health information.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import asyncio

from src.utils.error_handling import (
    get_error_handler,
    ErrorSeverity,
    ErrorCategory,
    RecoveryStrategy,
)
from src.utils.diagnostics import get_diagnostics_manager, DiagnosticStatus


def render_error_dashboard():
    """Render comprehensive error handling dashboard."""
    st.header("🚨 Error Handling & System Diagnostics")

    # Create tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs(
        ["📊 Error Overview", "🔍 Diagnostics", "⚡ Live Monitoring", "🛠️ Debug Tools"]
    )

    with tab1:
        render_error_overview()

    with tab2:
        render_system_diagnostics()

    with tab3:
        render_live_monitoring()

    with tab4:
        render_debug_tools()


def render_error_overview():
    """Render error overview dashboard."""
    error_handler = get_error_handler()

    # Get error statistics
    stats = error_handler.get_error_statistics()

    # Top level metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Total Errors",
            stats["total_errors"],
            delta=f"+{stats['recent_errors_24h']} (24h)",
        )

    with col2:
        recovery_rate = stats.get("recovery_success_rate", 0)
        st.metric(
            "Recovery Rate",
            f"{recovery_rate:.1f}%",
            delta="Good" if recovery_rate > 70 else "Poor",
        )

    with col3:
        resolved_errors = stats.get("resolved_errors", 0)
        st.metric(
            "Resolved Errors",
            resolved_errors,
            delta=f"{resolved_errors - (stats['total_errors'] - resolved_errors)} net",
        )

    with col4:
        degraded_features = len(stats.get("degraded_features", []))
        st.metric(
            "Degraded Features",
            degraded_features,
            delta="⚠️" if degraded_features > 0 else "✅",
        )

    # Error trends over time
    if stats["total_errors"] > 0:
        st.subheader("📈 Error Trends")

        # Create mock time series data for demonstration
        dates = pd.date_range(
            start=datetime.now() - timedelta(days=7), end=datetime.now(), freq="H"
        )

        # Generate sample error data
        import random

        error_counts = [random.randint(0, 5) for _ in dates]

        fig = px.line(
            x=dates,
            y=error_counts,
            title="Error Count Over Time (Last 7 Days)",
            labels={"x": "Time", "y": "Error Count"},
        )
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)

    # Error breakdown by category
    if stats.get("error_by_category"):
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("🏷️ Errors by Category")
            categories = list(stats["error_by_category"].keys())
            counts = list(stats["error_by_category"].values())

            fig = px.pie(
                values=counts, names=categories, title="Error Distribution by Category"
            )
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("⚠️ Errors by Severity")
            if stats.get("error_by_severity"):
                severities = list(stats["error_by_severity"].keys())
                severity_counts = list(stats["error_by_severity"].values())

                # Color mapping for severity
                colors = {
                    "low": "#90EE90",
                    "medium": "#FFD700",
                    "high": "#FFA500",
                    "critical": "#FF6347",
                    "emergency": "#DC143C",
                }

                fig = go.Figure(
                    data=[
                        go.Bar(
                            x=severities,
                            y=severity_counts,
                            marker_color=[
                                colors.get(s.lower(), "#999999") for s in severities
                            ],
                        )
                    ]
                )
                fig.update_layout(
                    title="Error Count by Severity", height=300, showlegend=False
                )
                st.plotly_chart(fig, use_container_width=True)

    # Most common errors
    if stats.get("most_common_errors"):
        st.subheader("🔝 Most Common Errors")

        error_df = pd.DataFrame(stats["most_common_errors"])
        st.dataframe(error_df, use_container_width=True, hide_index=True)

    # Degraded features
    if stats.get("degraded_features"):
        st.subheader("⚠️ Degraded Features")
        st.warning("The following features are currently in degraded mode:")
        for feature in stats["degraded_features"]:
            st.write(f"• {feature}")

        if st.button("🔄 Attempt Recovery"):
            with st.spinner("Attempting to recover degraded features..."):
                for feature in stats["degraded_features"]:
                    error_handler.disable_degraded_mode(feature)
            st.success("Recovery attempt completed. Check system status.")
            st.rerun()


def render_system_diagnostics():
    """Render system diagnostics dashboard."""
    diagnostics_manager = get_diagnostics_manager()

    st.subheader("🔍 System Diagnostics")

    col1, col2 = st.columns([2, 1])

    with col1:
        if st.button("🚀 Run Full Diagnostics", type="primary"):
            with st.spinner("Running comprehensive system diagnostics..."):
                try:
                    # Run diagnostics (note: we removed async, so this is now synchronous)
                    results = diagnostics_manager.run_full_diagnostics()
                    st.session_state["diagnostic_results"] = results
                    st.success(
                        f"Diagnostics completed! Status: {results['overall_status']}"
                    )
                except Exception as e:
                    st.error(f"Diagnostic run failed: {str(e)}")

    with col2:
        if st.button("🗑️ Clear History"):
            diagnostics_manager.clear_diagnostics_history()
            st.success("Diagnostic history cleared.")

    # Display results if available
    if "diagnostic_results" in st.session_state:
        results = st.session_state["diagnostic_results"]

        # Overall status
        status_color = {"HEALTHY": "🟢", "WARNING": "🟡", "CRITICAL": "🔴"}.get(
            results["overall_status"], "⚪"
        )

        st.markdown(f"### {status_color} Overall Status: {results['overall_status']}")

        # Summary metrics
        summary = results["summary"]
        col1, col2, col3, col4, col5, col6 = st.columns(6)

        with col1:
            st.metric("Total Tests", summary["total_tests"])
        with col2:
            st.metric("Passed", summary["passed"], delta="✅")
        with col3:
            st.metric(
                "Failed",
                summary["failed"],
                delta="❌" if summary["failed"] > 0 else None,
            )
        with col4:
            st.metric(
                "Warnings",
                summary["warnings"],
                delta="⚠️" if summary["warnings"] > 0 else None,
            )
        with col5:
            st.metric(
                "Errors",
                summary["errors"],
                delta="💥" if summary["errors"] > 0 else None,
            )
        with col6:
            st.metric("Skipped", summary["skipped"])

        # Test results details
        st.subheader("📋 Test Results")

        test_results = []
        for result in results["results"]:
            test_results.append(
                {
                    "Test Name": result["name"],
                    "Category": result["category"],
                    "Status": result["status"].upper(),
                    "Message": (
                        result["message"][:100] + "..."
                        if len(result["message"]) > 100
                        else result["message"]
                    ),
                    "Execution Time (ms)": f"{result['execution_time']*1000:.1f}",
                }
            )

        df = pd.DataFrame(test_results)

        # Color code the status column
        def color_status(val):
            if val == "PASS":
                return "background-color: #90EE90"
            elif val == "FAIL":
                return "background-color: #FFB6C1"
            elif val == "WARNING":
                return "background-color: #FFE4B5"
            elif val == "ERROR":
                return "background-color: #FFA07A"
            else:  # SKIP
                return "background-color: #D3D3D3"

        styled_df = df.style.applymap(color_status, subset=["Status"])
        st.dataframe(styled_df, use_container_width=True, hide_index=True)

        # System information
        if "system_info" in results:
            with st.expander("🖥️ System Information"):
                sys_info = results["system_info"]

                col1, col2 = st.columns(2)

                with col1:
                    st.write("**Platform Information:**")
                    st.write(f"• Platform: {sys_info['platform']}")
                    st.write(f"• Architecture: {sys_info['architecture']}")
                    st.write(f"• Python Version: {sys_info['python_version']}")
                    st.write(f"• CPU Count: {sys_info['cpu_count']}")

                with col2:
                    st.write("**Resource Information:**")
                    st.write(f"• Total Memory: {sys_info['memory_total']}")
                    st.write(f"• Available Memory: {sys_info['memory_available']}")
                    if sys_info["disk_space"]:
                        st.write(
                            f"• Disk Total: {sys_info['disk_space'].get('total', 'N/A')}"
                        )
                        st.write(
                            f"• Disk Free: {sys_info['disk_space'].get('free', 'N/A')}"
                        )

        # Recommendations
        if results.get("recommendations"):
            st.subheader("💡 Recommendations")
            for i, rec in enumerate(results["recommendations"], 1):
                st.write(f"{i}. {rec}")


def render_live_monitoring():
    """Render live system monitoring dashboard."""
    st.subheader("⚡ Live System Monitoring")

    # Auto-refresh toggle
    auto_refresh = st.checkbox("🔄 Auto-refresh (10s)", value=False)

    if auto_refresh:
        # Add auto-refresh placeholder
        placeholder = st.empty()

        # This would need to be implemented with actual real-time data
        with placeholder.container():
            st.info("Live monitoring would display real-time system metrics here.")

            # Mock real-time data
            import time
            import random

            # CPU and Memory gauges
            col1, col2 = st.columns(2)

            with col1:
                cpu_usage = random.uniform(10, 90)
                fig_cpu = go.Figure(
                    go.Indicator(
                        mode="gauge+number+delta",
                        value=cpu_usage,
                        domain={"x": [0, 1], "y": [0, 1]},
                        title={"text": "CPU Usage (%)"},
                        delta={"reference": 50},
                        gauge={
                            "axis": {"range": [None, 100]},
                            "bar": {"color": "darkblue"},
                            "steps": [
                                {"range": [0, 50], "color": "lightgray"},
                                {"range": [50, 80], "color": "gray"},
                            ],
                            "threshold": {
                                "line": {"color": "red", "width": 4},
                                "thickness": 0.75,
                                "value": 90,
                            },
                        },
                    )
                )
                fig_cpu.update_layout(height=300)
                st.plotly_chart(fig_cpu, use_container_width=True)

            with col2:
                memory_usage = random.uniform(20, 85)
                fig_mem = go.Figure(
                    go.Indicator(
                        mode="gauge+number+delta",
                        value=memory_usage,
                        domain={"x": [0, 1], "y": [0, 1]},
                        title={"text": "Memory Usage (%)"},
                        delta={"reference": 60},
                        gauge={
                            "axis": {"range": [None, 100]},
                            "bar": {"color": "darkgreen"},
                            "steps": [
                                {"range": [0, 60], "color": "lightgray"},
                                {"range": [60, 85], "color": "gray"},
                            ],
                            "threshold": {
                                "line": {"color": "red", "width": 4},
                                "thickness": 0.75,
                                "value": 90,
                            },
                        },
                    )
                )
                fig_mem.update_layout(height=300)
                st.plotly_chart(fig_mem, use_container_width=True)

        time.sleep(10)  # Wait 10 seconds
        st.rerun()  # Refresh the page

    else:
        st.info("Enable auto-refresh to see live system metrics.")

        # Static system information
        st.subheader("📊 Current System Status")

        try:
            import psutil

            # Current metrics
            col1, col2, col3 = st.columns(3)

            with col1:
                cpu_percent = psutil.cpu_percent(interval=1)
                st.metric("CPU Usage", f"{cpu_percent:.1f}%")

            with col2:
                memory = psutil.virtual_memory()
                st.metric("Memory Usage", f"{memory.percent:.1f}%")

            with col3:
                disk = psutil.disk_usage(".")
                disk_percent = (disk.used / disk.total) * 100
                st.metric("Disk Usage", f"{disk_percent:.1f}%")

        except ImportError:
            st.warning(
                "Install psutil for live system monitoring: `pip install psutil`"
            )


def render_debug_tools():
    """Render debugging tools and utilities."""
    st.subheader("🛠️ Debug Tools")

    # Debug mode toggle
    if "debug_mode" not in st.session_state:
        st.session_state.debug_mode = False

    col1, col2 = st.columns([3, 1])

    with col1:
        st.session_state.debug_mode = st.checkbox(
            "🐛 Enable Debug Mode", value=st.session_state.debug_mode
        )

    with col2:
        if st.button("🗑️ Clear Error History"):
            error_handler = get_error_handler()
            error_handler.clear_error_history()
            st.success("Error history cleared.")

    if st.session_state.debug_mode:
        st.info(
            "Debug mode is enabled. Additional information will be shown throughout the application."
        )

        # Configuration inspector
        with st.expander("⚙️ Configuration Inspector"):
            from ..utils.config import get_config_manager

            config_manager = get_config_manager()

            # Show configuration
            st.write("**Dashboard Configuration:**")
            dashboard_config = config_manager.get_dashboard_config()
            st.json(
                {
                    "title": dashboard_config.title,
                    "port": dashboard_config.port,
                    "host": dashboard_config.host,
                    "debug": dashboard_config.debug,
                    "refresh_interval": dashboard_config.refresh_interval,
                }
            )

            st.write("**Logging Configuration:**")
            logging_config = config_manager.get_logging_config()
            st.json(
                {
                    "level": logging_config.level,
                    "file_path": logging_config.file_path,
                    "console_output": logging_config.console_output,
                    "max_file_size": logging_config.max_file_size,
                    "backup_count": logging_config.backup_count,
                }
            )

        # Error simulation for testing
        with st.expander("🧪 Error Simulation (For Testing)"):
            st.warning("This section is for testing error handling. Use with caution!")

            error_type = st.selectbox(
                "Error Type",
                [
                    "ValueError",
                    "ConnectionError",
                    "KeyError",
                    "TypeError",
                    "RuntimeError",
                ],
            )

            error_message = st.text_input(
                "Error Message", value="Test error for debugging purposes"
            )

            if st.button("🔥 Simulate Error"):
                try:
                    if error_type == "ValueError":
                        raise ValueError(error_message)
                    elif error_type == "ConnectionError":
                        raise ConnectionError(error_message)
                    elif error_type == "KeyError":
                        raise KeyError(error_message)
                    elif error_type == "TypeError":
                        raise TypeError(error_message)
                    elif error_type == "RuntimeError":
                        raise RuntimeError(error_message)
                except Exception as e:
                    # Handle the error through our system
                    error_handler = get_error_handler()
                    asyncio.run(error_handler.handle_error(e))
                    st.error(f"Simulated error handled: {str(e)}")

        # Recent logs viewer
        with st.expander("📄 Recent Logs"):
            import os
            from pathlib import Path

            log_file = Path("logs/dashboard.log")
            if log_file.exists():
                try:
                    with open(log_file, "r", encoding="utf-8") as f:
                        lines = f.readlines()
                        # Show last 50 lines
                        recent_lines = lines[-50:] if len(lines) > 50 else lines

                    st.text_area(
                        "Recent Log Entries",
                        value="".join(recent_lines),
                        height=300,
                        disabled=True,
                    )
                except Exception as e:
                    st.error(f"Could not read log file: {e}")
            else:
                st.info("No log file found.")

    else:
        st.info("Enable debug mode to access advanced debugging tools.")


def render_error_status_indicator():
    """Render a small error status indicator for the main dashboard."""
    error_handler = get_error_handler()
    stats = error_handler.get_error_statistics()

    # Determine overall status
    recent_errors = stats.get("recent_errors_24h", 0)
    degraded_features = len(stats.get("degraded_features", []))
    recovery_rate = stats.get("recovery_success_rate", 100)

    if degraded_features > 0 or recent_errors > 10:
        status_color = "🔴"
        status_text = "Critical"
    elif recent_errors > 5 or recovery_rate < 80:
        status_color = "🟡"
        status_text = "Warning"
    else:
        status_color = "🟢"
        status_text = "Healthy"

    _, col2, _ = st.columns([1, 2, 1])

    with col2:
        st.markdown(
            f"""
            <div style="
                padding: 10px;
                border-radius: 5px;
                background-color: #f0f0f0;
                text-align: center;
                margin: 10px 0;
            ">
                {status_color} <strong>System Health: {status_text}</strong><br>
                <small>{recent_errors} errors (24h) | {degraded_features} degraded features</small>
            </div>
            """,
            unsafe_allow_html=True,
        )

    return status_text != "Healthy"  # Return True if there are issues
