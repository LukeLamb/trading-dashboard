#!/usr/bin/env python3
"""
Trading Dashboard Launcher

This script launches the Trading Dashboard Streamlit application
with proper path setup and configuration.
"""

import subprocess
import sys
import os
from pathlib import Path

def main():
    """Launch the Trading Dashboard."""
    print("🚀 Starting Trading Dashboard...")
    print("=" * 50)

    # Get project directory
    project_dir = Path(__file__).parent

    # Check if virtual environment exists
    if sys.platform == "win32":
        venv_python = project_dir / "venv" / "Scripts" / "python.exe"
        venv_streamlit = project_dir / "venv" / "Scripts" / "streamlit.exe"
    else:
        venv_python = project_dir / "bin" / "python"
        venv_streamlit = project_dir / "bin" / "streamlit"

    # Determine which python/streamlit to use
    if venv_python.exists():
        python_cmd = str(venv_python)
        if venv_streamlit.exists():
            streamlit_cmd = [str(venv_streamlit)]
        else:
            streamlit_cmd = [python_cmd, "-m", "streamlit"]
        print(f"✓ Using virtual environment: {venv_python}")
    else:
        python_cmd = sys.executable
        streamlit_cmd = [python_cmd, "-m", "streamlit"]
        print(f"⚠ Virtual environment not found, using system Python: {python_cmd}")

    # Dashboard entry point
    dashboard_script = project_dir / "src" / "dashboard" / "main.py"

    if not dashboard_script.exists():
        print(f"❌ Dashboard script not found: {dashboard_script}")
        return 1

    # Build command
    cmd = streamlit_cmd + [
        "run",
        str(dashboard_script),
        "--server.port=8501",
        "--server.headless=false",
        "--browser.serverAddress=localhost",
        "--server.enableXsrfProtection=false"
    ]

    print(f"📋 Command: {' '.join(cmd)}")
    print("🌐 Dashboard will be available at: http://localhost:8501")
    print("🔄 Auto-refresh is enabled")
    print("=" * 50)
    print("Press Ctrl+C to stop the dashboard")
    print()

    try:
        # Change to project directory
        os.chdir(project_dir)

        # Launch Streamlit
        result = subprocess.run(cmd, check=True)
        return result.returncode

    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start dashboard: {e}")
        return e.returncode
    except KeyboardInterrupt:
        print("\n👋 Dashboard stopped by user")
        return 0
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())