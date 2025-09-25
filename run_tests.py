#!/usr/bin/env python3
"""
Test runner script for Trading Dashboard.

This script properly sets up the Python path to allow imports
from the src directory, then runs the specified tests.

Usage:
    python run_tests.py                    # Run all tests
    python run_tests.py test_config        # Run specific test file
    python run_tests.py -v                 # Verbose output
"""

import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

if __name__ == "__main__":
    import pytest

    # Default to running all tests if no arguments provided
    args = sys.argv[1:] if len(sys.argv) > 1 else ["tests/"]

    # Run pytest with the provided arguments
    exit_code = pytest.main(args)
    sys.exit(exit_code)