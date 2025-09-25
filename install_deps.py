#!/usr/bin/env python3
"""
Dependency installer for Trading Dashboard.

This script installs all required dependencies in the virtual environment
and verifies the installation.
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description):
    """Run a command and return success status."""
    print(f"Running: {description}")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        if e.stdout:
            print(f"STDOUT: {e.stdout}")
        if e.stderr:
            print(f"STDERR: {e.stderr}")
        return False

def main():
    """Install dependencies and verify installation."""
    print("Trading Dashboard - Dependency Installation")
    print("=" * 50)

    # Get current directory
    project_dir = Path(__file__).parent
    venv_dir = project_dir / "venv"

    # Check if we're in a virtual environment
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("[OK] Virtual environment is active")
        venv_python = sys.executable
        venv_pip = sys.executable.replace("python.exe", "Scripts\\pip.exe")
    else:
        print("[INFO] Virtual environment is not active")

        # Try to use virtual environment directly
        if sys.platform == "win32":
            venv_python = str(venv_dir / "Scripts" / "python.exe")
            venv_pip = str(venv_dir / "Scripts" / "pip.exe")
        else:
            venv_python = str(venv_dir / "bin" / "python")
            venv_pip = str(venv_dir / "bin" / "pip")

        if not os.path.exists(venv_python):
            print(f"[ERROR] Virtual environment not found at {venv_python}")
            print("Please create virtual environment first:")
            print("  python -m venv venv")
            return False

        print(f"[OK] Using virtual environment: {venv_python}")

    # Install dependencies
    requirements_file = project_dir / "requirements.txt"
    install_cmd = f'"{venv_python}" -m pip install -r "{requirements_file}"'

    print("\nInstalling dependencies...")
    if not run_command(install_cmd, "Installing requirements"):
        return False

    # Verify installation
    print("\nVerifying installation...")

    test_imports = [
        "import yaml; print('[OK] PyYAML installed')",
        "import pytest; print('[OK] pytest installed')",
        "import streamlit; print('[OK] Streamlit installed')",
        "import pandas; print('[OK] Pandas installed')",
        "import plotly; print('[OK] Plotly installed')",
        "import pydantic; print('[OK] Pydantic installed')",
    ]

    all_good = True
    for test_import in test_imports:
        verify_cmd = f'"{venv_python}" -c "{test_import}"'
        if not run_command(verify_cmd, "Verifying import"):
            all_good = False

    print("\n" + "=" * 50)
    if all_good:
        print("[SUCCESS] All dependencies installed successfully!")
        print("\nNext steps:")
        print("1. Activate virtual environment:")
        if sys.platform == "win32":
            print("   venv\\Scripts\\activate.bat")
        else:
            print("   source venv/bin/activate")
        print("2. Test configuration system:")
        print("   python test_config_standalone.py")
        return True
    else:
        print("[ERROR] Some dependencies failed to install")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)