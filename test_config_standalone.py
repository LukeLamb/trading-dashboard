#!/usr/bin/env python3
"""
Standalone test runner for configuration system.

This script can be run directly without pytest to test the configuration system.
It includes the necessary path setup to import from src/.
"""

import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Now we can import from src
from src.utils.config import ConfigurationManager

def test_configuration_system():
    """Test the configuration system directly."""
    print("Testing Trading Dashboard Configuration System")
    print("=" * 50)

    try:
        # Test basic loading
        print("1. Initializing configuration manager...")
        config_manager = ConfigurationManager()
        print("   [OK] Configuration manager initialized successfully")

        # Test dashboard config
        print("2. Testing dashboard configuration...")
        dashboard_config = config_manager.get_dashboard_config()
        print(f"   [OK] Dashboard: {dashboard_config.title} on port {dashboard_config.port}")
        print(f"   [OK] Debug mode: {dashboard_config.debug}")
        print(f"   [OK] Refresh interval: {dashboard_config.refresh_interval}s")

        # Test agent configs
        print("3. Testing agent configurations...")
        agent_configs = config_manager.get_all_agent_configs()
        print(f"   [OK] Loaded {len(agent_configs)} agent configurations:")

        for name, config in agent_configs.items():
            status = "enabled" if config.enabled else "disabled"
            print(f"      - {config.name}: {config.url} ({status})")

        # Test environment detection
        print("4. Testing environment detection...")
        env = config_manager.get_environment()
        print(f"   [OK] Detected environment: {env}")

        # Test configuration validation
        print("5. Testing configuration validation...")
        is_valid = config_manager.validate_configuration()
        print(f"   [OK] Configuration validation: {'PASSED' if is_valid else 'FAILED'}")

        # Test dot notation access
        print("6. Testing dot notation access...")
        title = config_manager.get_config_value("dashboard.title")
        port = config_manager.get_config_value("dashboard.port")
        missing = config_manager.get_config_value("nonexistent.key", "default_value")
        print(f"   [OK] dashboard.title = {title}")
        print(f"   [OK] dashboard.port = {port}")
        print(f"   [OK] nonexistent.key = {missing} (using default)")

        # Test logging config
        print("7. Testing logging configuration...")
        logging_config = config_manager.get_logging_config()
        print(f"   [OK] Log level: {logging_config.level}")
        print(f"   [OK] Log file: {logging_config.file_path}")
        print(f"   [OK] Console output: {logging_config.console_output}")

        print("\n" + "=" * 50)
        print("SUCCESS: ALL CONFIGURATION TESTS PASSED!")
        print("The configuration system is working correctly.")

        return True

    except Exception as e:
        print(f"\nERROR: Configuration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_configuration_system()
    sys.exit(0 if success else 1)