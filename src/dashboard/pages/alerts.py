"""
Alerts Page

This module provides the main alerts page for the trading dashboard,
integrating alert management, notification configuration, and alert monitoring.
"""

import logging
from datetime import datetime
from typing import Dict, Any

import streamlit as st

from ..components.alert_dashboard import render_alert_dashboard
from ..components.alerts import get_alert_manager, DEFAULT_ALERT_RULES

# Configure logging
logger = logging.getLogger(__name__)


def show_alerts():
    """Display the main alerts page."""
    try:
        # Page header
        st.title("🚨 Alert Management System")
        st.markdown("""
        Configure and manage alerts for price movements, system health, data quality,
        and other important events in your trading dashboard.
        """)

        # Initialize alert manager if needed
        if 'alert_manager_initialized' not in st.session_state:
            _initialize_alert_system()

        # Check for demo mode
        demo_mode = st.session_state.get('alert_demo_mode', False)

        # Add demo mode toggle
        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            st.markdown("### Alert System Dashboard")

        with col2:
            if st.button("🔄 Refresh Data"):
                st.rerun()

        with col3:
            if st.button("🎮 Demo Mode" if not demo_mode else "🎮 Exit Demo"):
                st.session_state.alert_demo_mode = not demo_mode
                if st.session_state.alert_demo_mode:
                    _setup_demo_data()
                st.rerun()

        # Show demo indicator
        if demo_mode:
            st.info("🎮 **Demo Mode Active** - Using simulated alert data for demonstration")

        # Main alert dashboard
        render_alert_dashboard()

        # Quick actions section
        st.markdown("---")
        _render_quick_actions()

        # System integration status
        _render_integration_status()

    except Exception as e:
        st.error(f"Error loading alerts page: {str(e)}")
        logger.error(f"Alerts page error: {e}")

        # Show debug info if available
        if st.session_state.get('debug_mode', False):
            st.exception(e)


def _initialize_alert_system():
    """Initialize the alert management system."""
    try:
        # Get alert manager instance
        alert_manager = get_alert_manager()

        # Load default rules if no rules exist
        existing_rules = alert_manager.get_rules()
        if not existing_rules:
            st.info("Setting up default alert rules...")

            # Add default rules
            from ..components.alerts import AlertRule, AlertType, AlertSeverity, AlertCondition, ConditionOperator, NotificationChannel
            from uuid import uuid4

            for rule_config in DEFAULT_ALERT_RULES:
                try:
                    # Parse conditions
                    conditions = []
                    for cond_config in rule_config.get('conditions', []):
                        condition = AlertCondition(
                            field=cond_config['field'],
                            operator=ConditionOperator(cond_config['operator']),
                            value=cond_config['value']
                        )
                        conditions.append(condition)

                    # Parse notification channels
                    notification_channels = [
                        NotificationChannel(channel)
                        for channel in rule_config.get('notification_channels', ['console'])
                        if hasattr(NotificationChannel, channel.upper())
                    ]

                    # Create rule
                    rule = AlertRule(
                        id=str(uuid4()),
                        name=rule_config['name'],
                        description=rule_config['description'],
                        alert_type=AlertType(rule_config['alert_type']),
                        severity=AlertSeverity(rule_config['severity']),
                        conditions=conditions,
                        notification_channels=notification_channels,
                        cooldown_period=rule_config.get('cooldown_period', 300),
                        max_triggers_per_day=rule_config.get('max_triggers_per_day', 50)
                    )

                    # Add rule to manager
                    alert_manager.add_rule(rule)

                except Exception as e:
                    logger.error(f"Failed to create default rule {rule_config.get('name', 'unknown')}: {e}")

            st.success("Default alert rules have been configured!")

        # Start monitoring
        alert_manager.start_monitoring()

        st.session_state.alert_manager_initialized = True
        logger.info("Alert system initialized successfully")

    except Exception as e:
        st.error(f"Failed to initialize alert system: {str(e)}")
        logger.error(f"Alert system initialization error: {e}")


def _setup_demo_data():
    """Setup demo data for demonstration purposes."""
    try:
        alert_manager = get_alert_manager()

        # Create some demo alerts
        from ..components.alerts import AlertInstance, AlertType, AlertSeverity, AlertStatus
        from uuid import uuid4
        from datetime import timedelta

        demo_alerts = [
            {
                'rule_name': 'High CPU Usage',
                'alert_type': AlertType.SYSTEM_HEALTH,
                'severity': AlertSeverity.HIGH,
                'message': 'CPU usage has exceeded 85% for 5 minutes',
                'data': {'cpu_percent': 89.2, 'system_load': 2.8},
                'minutes_ago': 15
            },
            {
                'rule_name': 'Data Quality Drop',
                'alert_type': AlertType.DATA_QUALITY,
                'severity': AlertSeverity.MEDIUM,
                'message': 'Market data quality grade has dropped to C+',
                'data': {'quality_grade': 'C+', 'quality_score': 72, 'source': 'Yahoo Finance'},
                'minutes_ago': 45
            },
            {
                'rule_name': 'Price Alert - AAPL',
                'alert_type': AlertType.PRICE_ALERT,
                'severity': AlertSeverity.INFO,
                'message': 'AAPL price crossed above $150.00',
                'data': {'symbol': 'AAPL', 'price': 150.25, 'previous_price': 149.85},
                'minutes_ago': 120
            }
        ]

        for alert_data in demo_alerts:
            alert_id = str(uuid4())
            triggered_time = datetime.now() - timedelta(minutes=alert_data['minutes_ago'])

            alert = AlertInstance(
                id=alert_id,
                rule_id=str(uuid4()),
                rule_name=alert_data['rule_name'],
                alert_type=alert_data['alert_type'],
                severity=alert_data['severity'],
                message=alert_data['message'],
                data=alert_data['data'],
                status=AlertStatus.TRIGGERED,
                triggered_at=triggered_time
            )

            # Add to active alerts
            alert_manager.active_alerts[alert_id] = alert

            # Add to history
            alert_manager.history_manager.add_alert(alert)

        st.success("Demo alert data has been created!")

    except Exception as e:
        st.error(f"Failed to setup demo data: {str(e)}")
        logger.error(f"Demo data setup error: {e}")


def _render_quick_actions():
    """Render quick action buttons."""
    st.subheader("🚀 Quick Actions")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("🆘 Test Emergency Alert", use_container_width=True):
            _trigger_test_alert("emergency")

    with col2:
        if st.button("⚡ Test System Alert", use_container_width=True):
            _trigger_test_alert("system")

    with col3:
        if st.button("📊 Test Data Quality Alert", use_container_width=True):
            _trigger_test_alert("data_quality")

    with col4:
        if st.button("🧹 Cleanup Old Alerts", use_container_width=True):
            _cleanup_old_alerts()


def _trigger_test_alert(alert_type: str):
    """Trigger a test alert."""
    try:
        alert_manager = get_alert_manager()

        from ..components.alerts import AlertInstance, AlertType, AlertSeverity, AlertStatus
        from uuid import uuid4

        # Define test alert parameters
        test_alerts = {
            'emergency': {
                'rule_name': 'Test Emergency Alert',
                'alert_type': AlertType.SYSTEM_HEALTH,
                'severity': AlertSeverity.EMERGENCY,
                'message': 'This is a test emergency alert to verify the system',
                'data': {'test': True, 'alert_type': 'emergency'}
            },
            'system': {
                'rule_name': 'Test System Alert',
                'alert_type': AlertType.SYSTEM_HEALTH,
                'severity': AlertSeverity.MEDIUM,
                'message': 'This is a test system health alert',
                'data': {'test': True, 'alert_type': 'system', 'cpu_percent': 75.0}
            },
            'data_quality': {
                'rule_name': 'Test Data Quality Alert',
                'alert_type': AlertType.DATA_QUALITY,
                'severity': AlertSeverity.HIGH,
                'message': 'This is a test data quality alert',
                'data': {'test': True, 'alert_type': 'data_quality', 'quality_grade': 'D'}
            }
        }

        alert_config = test_alerts.get(alert_type)
        if not alert_config:
            st.error("Unknown alert type")
            return

        # Create test alert
        alert_id = str(uuid4())
        alert = AlertInstance(
            id=alert_id,
            rule_id=str(uuid4()),
            rule_name=alert_config['rule_name'],
            alert_type=alert_config['alert_type'],
            severity=alert_config['severity'],
            message=alert_config['message'],
            data=alert_config['data'],
            status=AlertStatus.TRIGGERED,
            triggered_at=datetime.now()
        )

        # Add to active alerts
        alert_manager.active_alerts[alert_id] = alert

        # Add to history
        alert_manager.history_manager.add_alert(alert)

        st.success(f"Test {alert_type} alert triggered successfully!")
        st.rerun()

    except Exception as e:
        st.error(f"Failed to trigger test alert: {str(e)}")
        logger.error(f"Test alert error: {e}")


def _cleanup_old_alerts():
    """Cleanup old resolved alerts."""
    try:
        alert_manager = get_alert_manager()

        # Get current counts
        active_before = len(alert_manager.active_alerts)

        # Cleanup old alerts (30 days)
        alert_manager.cleanup_old_alerts(days=30)

        # Get counts after cleanup
        active_after = len(alert_manager.active_alerts)

        cleaned_count = active_before - active_after

        if cleaned_count > 0:
            st.success(f"Cleaned up {cleaned_count} old alerts!")
        else:
            st.info("No old alerts to clean up.")

        st.rerun()

    except Exception as e:
        st.error(f"Failed to cleanup alerts: {str(e)}")
        logger.error(f"Alert cleanup error: {e}")


def _render_integration_status():
    """Render system integration status."""
    st.subheader("🔗 System Integration Status")

    col1, col2, col3 = st.columns(3)

    with col1:
        # Alert Manager Status
        st.markdown("#### Alert Manager")
        try:
            alert_manager = get_alert_manager()
            if alert_manager.running:
                st.success("✅ Active")
                st.write(f"Rules: {len(alert_manager.get_rules())}")
                st.write(f"Active Alerts: {len(alert_manager.get_active_alerts())}")
            else:
                st.warning("⚠️ Inactive")
        except Exception as e:
            st.error("❌ Error")
            st.write(f"Error: {str(e)}")

    with col2:
        # Market Data Integration
        st.markdown("#### Market Data Agent")
        try:
            # Check if market data agent is available
            from src.orchestrator import get_agent_manager
            agent_manager = get_agent_manager()
            market_agent_status = agent_manager.get_agent_status('market_data')

            if market_agent_status and market_agent_status.get('status') == 'running':
                st.success("✅ Connected")
                st.write("Price alerts available")
            else:
                st.warning("⚠️ Disconnected")
                st.write("Price alerts unavailable")
        except Exception:
            st.info("ℹ️ Not configured")
            st.write("Market data integration pending")

    with col3:
        # Notification Services
        st.markdown("#### Notification Services")
        try:
            alert_manager = get_alert_manager()
            services = alert_manager.notification_services

            enabled_services = []
            for channel, service in services.items():
                if service.enabled:
                    enabled_services.append(channel.value)

            if enabled_services:
                st.success(f"✅ {len(enabled_services)} Active")
                st.write(f"Channels: {', '.join(enabled_services)}")
            else:
                st.warning("⚠️ Console Only")
                st.write("Configure email/webhook for external notifications")

        except Exception:
            st.error("❌ Configuration Error")

    # Integration tips
    with st.expander("💡 Integration Tips"):
        st.markdown("""
        **Optimize your alert system:**

        1. **Configure Email Notifications:**
           - Set up SMTP settings in the Settings tab
           - Test email delivery before relying on alerts
           - Use app-specific passwords for Gmail

        2. **Set Up Webhooks:**
           - Configure webhook endpoints for external integrations
           - Test webhook delivery and response handling
           - Consider security (HTTPS, authentication tokens)

        3. **Market Data Integration:**
           - Ensure Market Data Agent is running for price alerts
           - Configure data quality thresholds appropriately
           - Test alert conditions with real market data

        4. **Performance Optimization:**
           - Adjust cooldown periods to prevent alert spam
           - Set appropriate daily trigger limits
           - Regularly clean up old resolved alerts
        """)


if __name__ == "__main__" or True:
    # For testing
    show_alerts()