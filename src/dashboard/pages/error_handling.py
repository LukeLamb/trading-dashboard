"""
Error Handling Dashboard Page.

This module provides a dedicated page for error handling and system diagnostics
in the Trading Dashboard application.
"""

import streamlit as st
from ..components.error_dashboard import render_error_dashboard


def show():
    """Show the error handling dashboard page."""
    try:
        render_error_dashboard()
    except Exception as e:
        st.error(f"Error loading error dashboard: {str(e)}")
        st.exception(e)


if __name__ == "__main__":
    show()
