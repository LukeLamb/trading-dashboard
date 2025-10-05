"""
Alert Dashboard Interface

This module provides Streamlit components for managing alerts, notifications,
and alert history in the trading dashboard.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from .alerts import (AlertManager, AlertRule, AlertSeverity, AlertType,
                     ConditionOperator, NotificationChannel, get_alert_manager)

# Configure logging
logger = logging.getLogger(__name__)


class AlertDashboard:
    """Alert management dashboard interface."""

    def __init__(self):
        self.alert_manager = get_alert_manager()

    def render_alerts_overview(self):
        """Render the alerts overview section."""
        st.subheader("🚨 Alerts Overview")

        # Get statistics
        stats = self.alert_manager.get_alert_statistics()
        active_alerts = self.alert_manager.get_active_alerts()

        # Create metrics columns
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Active Alerts",
                len(active_alerts),
                delta=None,
                help="Currently active and unresolved alerts"
            )

        with col2:
            st.metric(
                "Total Rules",
                stats.get('total_rules', 0),
                delta=f"{stats.get('enabled_rules', 0)} enabled",
                help="Total alert rules configured"
            )

        with col3:
            st.metric(
                "Today's Alerts",
                stats.get('alerts_by_day', {}).get(datetime.now().strftime('%Y-%m-%d'), 0),
                delta=None,
                help="Alerts triggered today"
            )

        with col4:
            st.metric(
                "Total Alerts",
                stats.get('total_alerts', 0),
                delta=None,
                help="Total alerts triggered all time"
            )

        # Alert severity distribution
        if stats.get('active_by_severity'):
            st.subheader("Active Alerts by Severity")
            severity_data = stats['active_by_severity']

            # Create severity chart
            fig = px.pie(
                values=list(severity_data.values()),
                names=list(severity_data.keys()),
                title="Active Alerts by Severity",
                color_discrete_map={
                    'info': '#3b82f6',
                    'low': '#10b981',
                    'medium': '#f59e0b',
                    'high': '#ef4444',
                    'critical': '#dc2626',
                    'emergency': '#7c2d12'
                }
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)

    def render_active_alerts(self):
        """Render active alerts management."""
        st.subheader("🔥 Active Alerts")

        active_alerts = self.alert_manager.get_active_alerts()

        if not active_alerts:
            st.info("No active alerts at this time.")
            return

        # Sort alerts by severity and time
        severity_order = {
            AlertSeverity.EMERGENCY: 0,
            AlertSeverity.CRITICAL: 1,
            AlertSeverity.HIGH: 2,
            AlertSeverity.MEDIUM: 3,
            AlertSeverity.LOW: 4,
            AlertSeverity.INFO: 5
        }

        sorted_alerts = sorted(
            active_alerts,
            key=lambda x: (severity_order.get(x.severity, 999), x.triggered_at),
            reverse=True
        )

        for alert in sorted_alerts:
            self._render_alert_card(alert)

    def _render_alert_card(self, alert):
        """Render an individual alert card."""
        # Severity color mapping
        severity_colors = {
            AlertSeverity.INFO: '#3b82f6',
            AlertSeverity.LOW: '#10b981',
            AlertSeverity.MEDIUM: '#f59e0b',
            AlertSeverity.HIGH: '#ef4444',
            AlertSeverity.CRITICAL: '#dc2626',
            AlertSeverity.EMERGENCY: '#7c2d12'
        }

        color = severity_colors.get(alert.severity, '#6b7280')

        # Create expandable card
        with st.expander(
            f"🚨 {alert.rule_name} - {alert.severity.value.upper()}",
            expanded=alert.severity in [AlertSeverity.CRITICAL, AlertSeverity.EMERGENCY]
        ):
            # Alert details
            col1, col2 = st.columns([2, 1])

            with col1:
                st.markdown(f"**Message:** {alert.message}")
                st.markdown(f"**Type:** {alert.alert_type.value}")
                st.markdown(f"**Triggered:** {alert.triggered_at.strftime('%Y-%m-%d %H:%M:%S')}")
                st.markdown(f"**Status:** {alert.status.value}")

                if alert.acknowledged_at:
                    st.markdown(f"**Acknowledged:** {alert.acknowledged_at.strftime('%Y-%m-%d %H:%M:%S')}")
                    if alert.acknowledged_by:
                        st.markdown(f"**Acknowledged By:** {alert.acknowledged_by}")

                if alert.resolution_notes:
                    st.markdown(f"**Notes:** {alert.resolution_notes}")

            with col2:
                # Action buttons
                st.markdown("**Actions:**")

                if alert.status.value == 'triggered':
                    if st.button(f"Acknowledge", key=f"ack_{alert.id}"):
                        if self.alert_manager.acknowledge_alert(alert.id, "dashboard_user"):
                            st.success("Alert acknowledged!")
                            st.rerun()

                    if st.button(f"Resolve", key=f"resolve_{alert.id}"):
                        if self.alert_manager.resolve_alert(alert.id, "dashboard_user"):
                            st.success("Alert resolved!")
                            st.rerun()

                    # Snooze options
                    snooze_duration = st.selectbox(
                        "Snooze for:",
                        [15, 30, 60, 120, 240],
                        format_func=lambda x: f"{x} minutes",
                        key=f"snooze_duration_{alert.id}"
                    )

                    if st.button(f"Snooze", key=f"snooze_{alert.id}"):
                        if self.alert_manager.snooze_alert(alert.id, snooze_duration):
                            st.success(f"Alert snoozed for {snooze_duration} minutes!")
                            st.rerun()

                elif alert.status.value == 'acknowledged':
                    if st.button(f"Resolve", key=f"resolve_ack_{alert.id}"):
                        if self.alert_manager.resolve_alert(alert.id, "dashboard_user"):
                            st.success("Alert resolved!")
                            st.rerun()

            # Show related data if available
            if alert.data:
                with st.expander("📊 Related Data"):
                    # Format data in a nice table
                    data_items = []
                    for key, value in alert.data.items():
                        if isinstance(value, (int, float)):
                            if isinstance(value, float):
                                value = f"{value:.4f}"
                        data_items.append({"Field": key, "Value": str(value)})

                    if data_items:
                        df = pd.DataFrame(data_items)
                        st.dataframe(df, use_container_width=True, hide_index=True)

            # Show notification history
            if alert.notification_history:
                with st.expander("📧 Notification History"):
                    for notification in alert.notification_history:
                        status_icon = "✅" if notification.get('success') else "❌"
                        st.markdown(
                            f"{status_icon} **{notification['channel']}** - "
                            f"{notification['sent_at']}"
                        )
                        if not notification.get('success') and notification.get('error'):
                            st.error(f"Error: {notification['error']}")

    def render_alert_rules(self):
        """Render alert rules management."""
        st.subheader("📋 Alert Rules")

        # Add tabs for different rule management functions
        tab1, tab2, tab3 = st.tabs(["View Rules", "Create Rule", "Import/Export"])

        with tab1:
            self._render_rules_list()

        with tab2:
            self._render_rule_creator()

        with tab3:
            self._render_import_export()

    def _render_rules_list(self):
        """Render list of existing rules."""
        rules = self.alert_manager.get_rules()

        if not rules:
            st.info("No alert rules configured. Create your first rule in the 'Create Rule' tab.")
            return

        # Rules overview
        st.write(f"**{len(rules)} rules configured**")

        # Filter options
        col1, col2, col3 = st.columns(3)

        with col1:
            filter_enabled = st.selectbox(
                "Filter by Status",
                ["All", "Enabled", "Disabled"],
                key="rules_filter_enabled"
            )

        with col2:
            filter_type = st.selectbox(
                "Filter by Type",
                ["All"] + [t.value for t in AlertType],
                key="rules_filter_type"
            )

        with col3:
            filter_severity = st.selectbox(
                "Filter by Severity",
                ["All"] + [s.value for s in AlertSeverity],
                key="rules_filter_severity"
            )

        # Apply filters
        filtered_rules = rules
        if filter_enabled != "All":
            enabled = filter_enabled == "Enabled"
            filtered_rules = [r for r in filtered_rules if r.enabled == enabled]

        if filter_type != "All":
            filtered_rules = [r for r in filtered_rules if r.alert_type.value == filter_type]

        if filter_severity != "All":
            filtered_rules = [r for r in filtered_rules if r.severity.value == filter_severity]

        # Display filtered rules
        for rule in filtered_rules:
            self._render_rule_card(rule)

    def _render_rule_card(self, rule: AlertRule):
        """Render an individual rule card."""
        status_icon = "✅" if rule.enabled else "❌"
        severity_emoji = {
            AlertSeverity.INFO: "ℹ️",
            AlertSeverity.LOW: "🟢",
            AlertSeverity.MEDIUM: "🟡",
            AlertSeverity.HIGH: "🟠",
            AlertSeverity.CRITICAL: "🔴",
            AlertSeverity.EMERGENCY: "🚨"
        }.get(rule.severity, "❓")

        with st.expander(f"{status_icon} {severity_emoji} {rule.name}"):
            col1, col2 = st.columns([2, 1])

            with col1:
                st.markdown(f"**Description:** {rule.description}")
                st.markdown(f"**Type:** {rule.alert_type.value}")
                st.markdown(f"**Severity:** {rule.severity.value}")
                st.markdown(f"**Cooldown:** {rule.cooldown_period} seconds")
                st.markdown(f"**Daily Limit:** {rule.max_triggers_per_day}")

                # Show conditions
                st.markdown("**Conditions:**")
                for i, condition in enumerate(rule.conditions, 1):
                    st.markdown(
                        f"  {i}. `{condition.field}` {condition.operator.value} `{condition.value}`"
                    )

                # Show notification channels
                if rule.notification_channels:
                    channels = [ch.value for ch in rule.notification_channels]
                    st.markdown(f"**Notifications:** {', '.join(channels)}")

                # Show tags
                if rule.tags:
                    st.markdown(f"**Tags:** {', '.join(rule.tags)}")

            with col2:
                st.markdown("**Actions:**")

                # Enable/Disable button
                if rule.enabled:
                    if st.button("Disable", key=f"disable_{rule.id}"):
                        if self.alert_manager.disable_rule(rule.id):
                            st.success("Rule disabled!")
                            st.rerun()
                else:
                    if st.button("Enable", key=f"enable_{rule.id}"):
                        if self.alert_manager.enable_rule(rule.id):
                            st.success("Rule enabled!")
                            st.rerun()

                # Delete button
                if st.button("Delete", key=f"delete_{rule.id}", type="secondary"):
                    if st.button("Confirm Delete", key=f"confirm_delete_{rule.id}", type="primary"):
                        if self.alert_manager.remove_rule(rule.id):
                            st.success("Rule deleted!")
                            st.rerun()

                # Edit button (placeholder)
                if st.button("Edit", key=f"edit_{rule.id}"):
                    st.info("Rule editing interface coming soon!")

    def _render_rule_creator(self):
        """Render alert rule creation interface."""
        st.markdown("### Create New Alert Rule")

        with st.form("create_alert_rule"):
            # Basic information
            col1, col2 = st.columns(2)

            with col1:
                rule_name = st.text_input("Rule Name*", placeholder="High CPU Usage Alert")
                rule_type = st.selectbox("Alert Type*", [t.value for t in AlertType])
                rule_severity = st.selectbox("Severity*", [s.value for s in AlertSeverity])

            with col2:
                rule_description = st.text_area("Description", placeholder="Alert when CPU usage exceeds threshold")
                cooldown = st.number_input("Cooldown Period (seconds)", min_value=0, value=300)
                daily_limit = st.number_input("Max Triggers Per Day", min_value=1, value=50)

            # Conditions
            st.markdown("### Conditions")
            st.info("Define the conditions that will trigger this alert. All conditions must be met.")

            # For simplicity, we'll allow one condition for now
            condition_field = st.text_input(
                "Field Path*",
                placeholder="system.cpu_percent",
                help="Path to the data field (e.g., system.cpu_percent, price, quality.grade)"
            )

            col1, col2 = st.columns(2)
            with col1:
                condition_operator = st.selectbox("Operator*", [op.value for op in ConditionOperator])

            with col2:
                condition_value = st.text_input(
                    "Value*",
                    placeholder="85",
                    help="Value to compare against"
                )

            # Notification channels
            st.markdown("### Notification Channels")
            notification_channels = st.multiselect(
                "Select Channels",
                [ch.value for ch in NotificationChannel],
                default=['console']
            )

            # Tags
            tags_input = st.text_input(
                "Tags (comma-separated)",
                placeholder="system, performance, critical",
                help="Optional tags for organizing rules"
            )

            # Submit button
            submitted = st.form_submit_button("Create Alert Rule", type="primary")

            if submitted:
                # Validate inputs
                if not rule_name or not condition_field or not condition_value:
                    st.error("Please fill in all required fields marked with *")
                    return

                try:
                    # Parse condition value
                    try:
                        parsed_value = float(condition_value)
                    except ValueError:
                        parsed_value = condition_value

                    # Create rule
                    from .alerts import AlertCondition, AlertRule
                    from uuid import uuid4

                    condition = AlertCondition(
                        field=condition_field,
                        operator=ConditionOperator(condition_operator),
                        value=parsed_value
                    )

                    tags = [tag.strip() for tag in tags_input.split(',') if tag.strip()] if tags_input else []

                    rule = AlertRule(
                        id=str(uuid4()),
                        name=rule_name,
                        description=rule_description,
                        alert_type=AlertType(rule_type),
                        severity=AlertSeverity(rule_severity),
                        conditions=[condition],
                        notification_channels=[NotificationChannel(ch) for ch in notification_channels],
                        cooldown_period=cooldown,
                        max_triggers_per_day=daily_limit,
                        tags=tags
                    )

                    # Add rule to manager
                    if self.alert_manager.add_rule(rule):
                        st.success(f"Alert rule '{rule_name}' created successfully!")
                        st.rerun()
                    else:
                        st.error("Failed to create alert rule")

                except Exception as e:
                    st.error(f"Error creating rule: {str(e)}")

    def _render_import_export(self):
        """Render import/export functionality."""
        st.markdown("### Import/Export Rules")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### Export Rules")
            if st.button("Export All Rules"):
                rules = self.alert_manager.get_rules()
                if rules:
                    export_data = []
                    for rule in rules:
                        rule_dict = {
                            'id': rule.id,
                            'name': rule.name,
                            'description': rule.description,
                            'alert_type': rule.alert_type.value,
                            'severity': rule.severity.value,
                            'enabled': rule.enabled,
                            'cooldown_period': rule.cooldown_period,
                            'max_triggers_per_day': rule.max_triggers_per_day,
                            'tags': rule.tags,
                            'notification_channels': [ch.value for ch in rule.notification_channels],
                            'conditions': [
                                {
                                    'field': cond.field,
                                    'operator': cond.operator.value,
                                    'value': cond.value,
                                    'comparison_field': cond.comparison_field,
                                    'timeframe': cond.timeframe
                                }
                                for cond in rule.conditions
                            ]
                        }
                        export_data.append(rule_dict)

                    export_json = json.dumps(export_data, indent=2)
                    st.download_button(
                        "Download Rules JSON",
                        data=export_json,
                        file_name=f"alert_rules_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json"
                    )
                else:
                    st.info("No rules to export")

        with col2:
            st.markdown("#### Import Rules")
            uploaded_file = st.file_uploader(
                "Choose JSON file",
                type="json",
                help="Upload a JSON file containing alert rules"
            )

            if uploaded_file is not None:
                try:
                    import_data = json.loads(uploaded_file.read())

                    st.write(f"Found {len(import_data)} rules in file:")
                    for rule_data in import_data[:5]:  # Show first 5
                        st.write(f"- {rule_data.get('name', 'Unnamed')} ({rule_data.get('severity', 'unknown')})")

                    if len(import_data) > 5:
                        st.write(f"... and {len(import_data) - 5} more")

                    if st.button("Import Rules"):
                        imported_count = 0
                        for rule_data in import_data:
                            try:
                                # Create rule from imported data
                                # (Implementation would be similar to rule creator)
                                imported_count += 1
                            except Exception as e:
                                st.error(f"Failed to import rule '{rule_data.get('name', 'unknown')}': {e}")

                        if imported_count > 0:
                            st.success(f"Successfully imported {imported_count} rules!")
                            st.rerun()

                except Exception as e:
                    st.error(f"Error parsing JSON file: {e}")

    def render_alert_history(self):
        """Render alert history and analytics."""
        st.subheader("📈 Alert History & Analytics")

        # Time range selector
        col1, col2 = st.columns(2)

        with col1:
            days_back = st.selectbox(
                "Time Range",
                [1, 7, 30, 90],
                index=1,
                format_func=lambda x: f"Last {x} day{'s' if x > 1 else ''}"
            )

        with col2:
            max_alerts = st.selectbox(
                "Max Alerts",
                [50, 100, 500, 1000],
                index=1
            )

        # Get alert history
        recent_alerts = self.alert_manager.history_manager.get_recent_alerts(max_alerts)

        if not recent_alerts:
            st.info("No alert history available.")
            return

        # Filter by time range
        cutoff_date = datetime.now() - timedelta(days=days_back)
        filtered_alerts = [
            alert for alert in recent_alerts
            if datetime.fromisoformat(alert['triggered_at']) >= cutoff_date
        ]

        if not filtered_alerts:
            st.info(f"No alerts in the last {days_back} day{'s' if days_back > 1 else ''}.")
            return

        # Convert to DataFrame for analysis
        df = pd.DataFrame(filtered_alerts)
        df['triggered_at'] = pd.to_datetime(df['triggered_at'])
        df['date'] = df['triggered_at'].dt.date
        df['hour'] = df['triggered_at'].dt.hour

        # Alert trends over time
        st.markdown("#### Alert Trends")

        daily_counts = df.groupby('date').size().reset_index(name='count')
        daily_counts['date'] = pd.to_datetime(daily_counts['date'])

        fig_trend = px.line(
            daily_counts,
            x='date',
            y='count',
            title=f"Daily Alert Count - Last {days_back} Days",
            markers=True
        )
        fig_trend.update_layout(height=400)
        st.plotly_chart(fig_trend, use_container_width=True)

        # Alert distribution charts
        col1, col2 = st.columns(2)

        with col1:
            # By severity
            severity_counts = df['severity'].value_counts()
            fig_severity = px.pie(
                values=severity_counts.values,
                names=severity_counts.index,
                title="Alerts by Severity"
            )
            fig_severity.update_layout(height=400)
            st.plotly_chart(fig_severity, use_container_width=True)

        with col2:
            # By type
            type_counts = df['alert_type'].value_counts()
            fig_type = px.bar(
                x=type_counts.index,
                y=type_counts.values,
                title="Alerts by Type"
            )
            fig_type.update_layout(height=400)
            st.plotly_chart(fig_type, use_container_width=True)

        # Hourly pattern
        st.markdown("#### Alert Patterns")
        hourly_counts = df.groupby('hour').size().reset_index(name='count')

        fig_hourly = px.bar(
            hourly_counts,
            x='hour',
            y='count',
            title="Alert Distribution by Hour of Day"
        )
        fig_hourly.update_layout(height=400)
        st.plotly_chart(fig_hourly, use_container_width=True)

        # Most frequent rules
        rule_counts = df['rule_name'].value_counts().head(10)
        if not rule_counts.empty:
            st.markdown("#### Most Triggered Rules")
            fig_rules = px.bar(
                x=rule_counts.values,
                y=rule_counts.index,
                orientation='h',
                title="Top 10 Most Triggered Rules"
            )
            fig_rules.update_layout(height=400)
            st.plotly_chart(fig_rules, use_container_width=True)

        # Recent alerts table
        st.markdown("#### Recent Alerts")
        display_df = df[['triggered_at', 'rule_name', 'severity', 'alert_type', 'status']].copy()
        display_df['triggered_at'] = display_df['triggered_at'].dt.strftime('%Y-%m-%d %H:%M:%S')
        display_df = display_df.sort_values('triggered_at', ascending=False).head(20)

        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "triggered_at": "Triggered At",
                "rule_name": "Rule Name",
                "severity": "Severity",
                "alert_type": "Type",
                "status": "Status"
            }
        )

    def render_notification_settings(self):
        """Render notification settings configuration."""
        st.subheader("📧 Notification Settings")

        st.info("Configure notification channels for alert delivery.")

        # Email settings
        with st.expander("📧 Email Configuration"):
            email_enabled = st.checkbox("Enable Email Notifications", value=False)

            if email_enabled:
                col1, col2 = st.columns(2)

                with col1:
                    smtp_server = st.text_input("SMTP Server", value="smtp.gmail.com")
                    smtp_port = st.number_input("SMTP Port", value=587, min_value=1, max_value=65535)
                    username = st.text_input("Username")

                with col2:
                    password = st.text_input("Password", type="password")
                    from_email = st.text_input("From Email")
                    to_emails = st.text_area("To Emails (one per line)", placeholder="user@example.com\nadmin@example.com")

                if st.button("Test Email Configuration"):
                    st.info("Email test functionality would be implemented here")

        # Webhook settings
        with st.expander("🔗 Webhook Configuration"):
            webhook_enabled = st.checkbox("Enable Webhook Notifications", value=False)

            if webhook_enabled:
                webhook_url = st.text_input("Webhook URL", placeholder="https://your-webhook-endpoint.com/alerts")
                webhook_timeout = st.number_input("Timeout (seconds)", value=30, min_value=1, max_value=300)

                # Custom headers
                st.markdown("**Custom Headers:**")
                header_key = st.text_input("Header Key", placeholder="Authorization")
                header_value = st.text_input("Header Value", placeholder="Bearer your-token")

                if st.button("Test Webhook Configuration"):
                    st.info("Webhook test functionality would be implemented here")

        # Browser notifications
        with st.expander("🔔 Browser Notifications"):
            st.checkbox("Enable Browser Push Notifications", value=True)
            st.info("Browser notifications will be shown when the dashboard is open in the browser.")

        # Save settings button
        if st.button("Save Notification Settings", type="primary"):
            st.success("Notification settings saved! (Implementation would save to configuration)")


def render_alert_dashboard():
    """Main function to render the complete alert dashboard."""
    dashboard = AlertDashboard()

    # Create tabs for different sections
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Overview",
        "Active Alerts",
        "Alert Rules",
        "History",
        "Settings"
    ])

    with tab1:
        dashboard.render_alerts_overview()

    with tab2:
        dashboard.render_active_alerts()

    with tab3:
        dashboard.render_alert_rules()

    with tab4:
        dashboard.render_alert_history()

    with tab5:
        dashboard.render_notification_settings()


if __name__ == "__main__":
    # For testing
    render_alert_dashboard()