"""
Alert and Notification System

This module provides comprehensive alert management and notification capabilities
for the trading dashboard, including configurable alert rules, multiple notification
channels, and alert history management.
"""

import asyncio
import json
import logging
import smtplib
import threading
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Union
from uuid import uuid4

import requests
from pydantic import BaseModel, Field, field_validator

# Configure logging
logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels."""
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class AlertType(Enum):
    """Types of alerts."""
    PRICE_ALERT = "price_alert"
    INDICATOR_ALERT = "indicator_alert"
    SYSTEM_HEALTH = "system_health"
    DATA_QUALITY = "data_quality"
    PERFORMANCE = "performance"
    CUSTOM = "custom"


class AlertStatus(Enum):
    """Alert status states."""
    ACTIVE = "active"
    TRIGGERED = "triggered"
    ACKNOWLEDGED = "acknowledged"
    SNOOZED = "snoozed"
    RESOLVED = "resolved"
    DISABLED = "disabled"


class NotificationChannel(Enum):
    """Available notification channels."""
    EMAIL = "email"
    BROWSER = "browser"
    SYSTEM_TRAY = "system_tray"
    WEBHOOK = "webhook"
    SMS = "sms"
    CONSOLE = "console"


class ConditionOperator(Enum):
    """Operators for alert conditions."""
    GREATER_THAN = ">"
    LESS_THAN = "<"
    GREATER_EQUAL = ">="
    LESS_EQUAL = "<="
    EQUAL = "=="
    NOT_EQUAL = "!="
    CROSSES_ABOVE = "crosses_above"
    CROSSES_BELOW = "crosses_below"
    PERCENTAGE_CHANGE = "percentage_change"


@dataclass
class AlertCondition:
    """Defines a condition that triggers an alert."""
    field: str
    operator: ConditionOperator
    value: Union[float, int, str]
    comparison_field: Optional[str] = None
    timeframe: Optional[str] = None  # e.g., "5m", "1h", "1d"

    def evaluate(self, data: Dict[str, Any], historical_data: Optional[List[Dict]] = None) -> bool:
        """Evaluate if the condition is met."""
        try:
            current_value = self._get_field_value(data, self.field)
            if current_value is None:
                return False

            target_value = self.value
            if self.comparison_field:
                target_value = self._get_field_value(data, self.comparison_field)
                if target_value is None:
                    return False

            return self._apply_operator(current_value, target_value, historical_data)

        except Exception as e:
            logger.error(f"Error evaluating condition: {e}")
            return False

    def _get_field_value(self, data: Dict[str, Any], field: str) -> Optional[Union[float, int, str]]:
        """Extract field value from nested data structure."""
        keys = field.split('.')
        value = data
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        return value

    def _apply_operator(self, current: Union[float, int, str], target: Union[float, int, str],
                       historical: Optional[List[Dict]] = None) -> bool:
        """Apply the operator to compare values."""
        if self.operator == ConditionOperator.GREATER_THAN:
            return float(current) > float(target)
        elif self.operator == ConditionOperator.LESS_THAN:
            return float(current) < float(target)
        elif self.operator == ConditionOperator.GREATER_EQUAL:
            return float(current) >= float(target)
        elif self.operator == ConditionOperator.LESS_EQUAL:
            return float(current) <= float(target)
        elif self.operator == ConditionOperator.EQUAL:
            return current == target
        elif self.operator == ConditionOperator.NOT_EQUAL:
            return current != target
        elif self.operator == ConditionOperator.CROSSES_ABOVE:
            return self._check_crosses_above(current, target, historical)
        elif self.operator == ConditionOperator.CROSSES_BELOW:
            return self._check_crosses_below(current, target, historical)
        elif self.operator == ConditionOperator.PERCENTAGE_CHANGE:
            return self._check_percentage_change(current, target, historical)
        else:
            return False

    def _check_crosses_above(self, current: float, target: float, historical: Optional[List[Dict]]) -> bool:
        """Check if value crossed above target."""
        if not historical or len(historical) < 2:
            return False

        previous_value = self._get_field_value(historical[-1], self.field)
        if previous_value is None:
            return False

        return float(previous_value) <= float(target) and float(current) > float(target)

    def _check_crosses_below(self, current: float, target: float, historical: Optional[List[Dict]]) -> bool:
        """Check if value crossed below target."""
        if not historical or len(historical) < 2:
            return False

        previous_value = self._get_field_value(historical[-1], self.field)
        if previous_value is None:
            return False

        return float(previous_value) >= float(target) and float(current) < float(target)

    def _check_percentage_change(self, current: float, threshold: float, historical: Optional[List[Dict]]) -> bool:
        """Check if percentage change exceeds threshold."""
        if not historical:
            return False

        previous_value = self._get_field_value(historical[-1], self.field)
        if previous_value is None or float(previous_value) == 0:
            return False

        change_percent = abs((float(current) - float(previous_value)) / float(previous_value)) * 100
        return change_percent >= float(threshold)


@dataclass
class AlertRule:
    """Defines an alert rule with conditions and actions."""
    id: str
    name: str
    description: str
    alert_type: AlertType
    severity: AlertSeverity
    conditions: List[AlertCondition]
    enabled: bool = True
    notification_channels: List[NotificationChannel] = field(default_factory=list)
    cooldown_period: int = 300  # seconds
    max_triggers_per_day: int = 50
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        self.updated_at = datetime.now()

    def evaluate(self, data: Dict[str, Any], historical_data: Optional[List[Dict]] = None) -> bool:
        """Evaluate if all conditions are met."""
        if not self.enabled:
            return False

        try:
            # All conditions must be true for alert to trigger
            for condition in self.conditions:
                if not condition.evaluate(data, historical_data):
                    return False
            return True

        except Exception as e:
            logger.error(f"Error evaluating alert rule {self.id}: {e}")
            return False


@dataclass
class AlertInstance:
    """Represents a triggered alert instance."""
    id: str
    rule_id: str
    rule_name: str
    alert_type: AlertType
    severity: AlertSeverity
    message: str
    data: Dict[str, Any]
    status: AlertStatus
    triggered_at: datetime
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    snoozed_until: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    resolution_notes: Optional[str] = None
    notification_history: List[Dict[str, Any]] = field(default_factory=list)

    def acknowledge(self, user: Optional[str] = None, notes: Optional[str] = None):
        """Acknowledge the alert."""
        self.status = AlertStatus.ACKNOWLEDGED
        self.acknowledged_at = datetime.now()
        self.acknowledged_by = user
        if notes:
            self.resolution_notes = notes

    def resolve(self, user: Optional[str] = None, notes: Optional[str] = None):
        """Resolve the alert."""
        self.status = AlertStatus.RESOLVED
        self.resolved_at = datetime.now()
        self.acknowledged_by = user
        if notes:
            self.resolution_notes = notes

    def snooze(self, duration_minutes: int = 60):
        """Snooze the alert for specified duration."""
        self.status = AlertStatus.SNOOZED
        self.snoozed_until = datetime.now() + timedelta(minutes=duration_minutes)

    def is_snoozed(self) -> bool:
        """Check if alert is currently snoozed."""
        if self.status != AlertStatus.SNOOZED:
            return False
        if self.snoozed_until and datetime.now() >= self.snoozed_until:
            self.status = AlertStatus.TRIGGERED
            return False
        return True


class NotificationService:
    """Base class for notification services."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.enabled = config.get('enabled', False)

    async def send_notification(self, alert: AlertInstance) -> bool:
        """Send notification for alert. Must be implemented by subclasses."""
        raise NotImplementedError

    def format_message(self, alert: AlertInstance) -> str:
        """Format alert message for this notification channel."""
        return f"[{alert.severity.value.upper()}] {alert.rule_name}: {alert.message}"


class EmailNotificationService(NotificationService):
    """Email notification service."""

    async def send_notification(self, alert: AlertInstance) -> bool:
        """Send email notification."""
        if not self.enabled:
            return False

        try:
            smtp_server = self.config.get('smtp_server', 'localhost')
            smtp_port = self.config.get('smtp_port', 587)
            username = self.config.get('username', '')
            password = self.config.get('password', '')
            from_email = self.config.get('from_email', username)
            to_emails = self.config.get('to_emails', [])

            if not to_emails:
                logger.warning("No recipient emails configured")
                return False

            # Create message
            msg = MIMEMultipart()
            msg['From'] = from_email
            msg['To'] = ', '.join(to_emails)
            msg['Subject'] = f"Trading Alert: {alert.rule_name}"

            # Format email body
            body = self._format_email_body(alert)
            msg.attach(MIMEText(body, 'html'))

            # Send email
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                if username and password:
                    server.starttls()
                    server.login(username, password)

                server.send_message(msg)

            logger.info(f"Email notification sent for alert {alert.id}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")
            return False

    def _format_email_body(self, alert: AlertInstance) -> str:
        """Format HTML email body."""
        severity_colors = {
            AlertSeverity.INFO: '#3b82f6',
            AlertSeverity.LOW: '#10b981',
            AlertSeverity.MEDIUM: '#f59e0b',
            AlertSeverity.HIGH: '#ef4444',
            AlertSeverity.CRITICAL: '#dc2626',
            AlertSeverity.EMERGENCY: '#7c2d12'
        }

        color = severity_colors.get(alert.severity, '#6b7280')

        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; margin: 0; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto;">
                <div style="background-color: {color}; color: white; padding: 20px; border-radius: 8px 8px 0 0;">
                    <h2 style="margin: 0;">Trading Alert</h2>
                    <p style="margin: 5px 0 0 0; opacity: 0.9;">{alert.severity.value.upper()} - {alert.rule_name}</p>
                </div>
                <div style="background-color: #f9fafb; padding: 20px; border-radius: 0 0 8px 8px; border: 1px solid #e5e7eb;">
                    <h3 style="margin-top: 0; color: #374151;">Alert Details</h3>
                    <p><strong>Message:</strong> {alert.message}</p>
                    <p><strong>Type:</strong> {alert.alert_type.value}</p>
                    <p><strong>Triggered:</strong> {alert.triggered_at.strftime('%Y-%m-%d %H:%M:%S')}</p>
                    <p><strong>Alert ID:</strong> {alert.id}</p>

                    {self._format_data_section(alert.data)}
                </div>
            </div>
        </body>
        </html>
        """

    def _format_data_section(self, data: Dict[str, Any]) -> str:
        """Format alert data for email."""
        if not data:
            return ""

        items = []
        for key, value in data.items():
            if isinstance(value, (int, float)):
                if isinstance(value, float):
                    value = f"{value:.4f}"
                items.append(f"<li><strong>{key}:</strong> {value}</li>")
            elif isinstance(value, str):
                items.append(f"<li><strong>{key}:</strong> {value}</li>")

        if items:
            return f"""
            <h4 style="color: #374151; margin-bottom: 10px;">Related Data</h4>
            <ul style="margin: 0; padding-left: 20px;">
                {''.join(items)}
            </ul>
            """
        return ""


class BrowserNotificationService(NotificationService):
    """Browser push notification service."""

    async def send_notification(self, alert: AlertInstance) -> bool:
        """Send browser notification (placeholder for JavaScript integration)."""
        if not self.enabled:
            return False

        # This would be implemented with JavaScript on the frontend
        logger.info(f"Browser notification queued for alert {alert.id}")
        return True


class WebhookNotificationService(NotificationService):
    """Webhook notification service."""

    async def send_notification(self, alert: AlertInstance) -> bool:
        """Send webhook notification."""
        if not self.enabled:
            return False

        try:
            webhook_url = self.config.get('webhook_url')
            if not webhook_url:
                logger.warning("No webhook URL configured")
                return False

            payload = {
                'alert_id': alert.id,
                'rule_name': alert.rule_name,
                'severity': alert.severity.value,
                'message': alert.message,
                'type': alert.alert_type.value,
                'triggered_at': alert.triggered_at.isoformat(),
                'data': alert.data
            }

            headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'TradingDashboard-AlertSystem/1.0'
            }

            # Add custom headers if configured
            custom_headers = self.config.get('headers', {})
            headers.update(custom_headers)

            response = requests.post(
                webhook_url,
                json=payload,
                headers=headers,
                timeout=self.config.get('timeout', 30)
            )

            response.raise_for_status()
            logger.info(f"Webhook notification sent for alert {alert.id}")
            return True

        except Exception as e:
            logger.error(f"Failed to send webhook notification: {e}")
            return False


class ConsoleNotificationService(NotificationService):
    """Console/log notification service."""

    async def send_notification(self, alert: AlertInstance) -> bool:
        """Send console notification."""
        if not self.enabled:
            return False

        message = self.format_message(alert)

        # Log with appropriate level based on severity
        if alert.severity in [AlertSeverity.CRITICAL, AlertSeverity.EMERGENCY]:
            logger.critical(message)
        elif alert.severity == AlertSeverity.HIGH:
            logger.error(message)
        elif alert.severity == AlertSeverity.MEDIUM:
            logger.warning(message)
        else:
            logger.info(message)

        return True


class AlertHistoryManager:
    """Manages alert history and statistics."""

    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = Path(storage_path) if storage_path else Path("data/alerts")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.history_file = self.storage_path / "alert_history.json"
        self.stats_file = self.storage_path / "alert_stats.json"

        self._load_history()
        self._load_stats()

    def _load_history(self):
        """Load alert history from storage."""
        self.history: List[Dict[str, Any]] = []

        try:
            if self.history_file.exists():
                with open(self.history_file, 'r') as f:
                    data = json.load(f)
                    self.history = data.get('alerts', [])
        except Exception as e:
            logger.error(f"Failed to load alert history: {e}")

    def _load_stats(self):
        """Load alert statistics from storage."""
        self.stats: Dict[str, Any] = {
            'total_alerts': 0,
            'alerts_by_severity': {},
            'alerts_by_type': {},
            'alerts_by_day': {},
            'response_times': [],
            'most_frequent_rules': {}
        }

        try:
            if self.stats_file.exists():
                with open(self.stats_file, 'r') as f:
                    self.stats.update(json.load(f))
        except Exception as e:
            logger.error(f"Failed to load alert stats: {e}")

    def add_alert(self, alert: AlertInstance):
        """Add alert to history and update statistics."""
        alert_data = {
            'id': alert.id,
            'rule_id': alert.rule_id,
            'rule_name': alert.rule_name,
            'alert_type': alert.alert_type.value,
            'severity': alert.severity.value,
            'message': alert.message,
            'triggered_at': alert.triggered_at.isoformat(),
            'acknowledged_at': alert.acknowledged_at.isoformat() if alert.acknowledged_at else None,
            'resolved_at': alert.resolved_at.isoformat() if alert.resolved_at else None,
            'status': alert.status.value,
            'data': alert.data
        }

        self.history.append(alert_data)
        self._update_stats(alert)
        self._save_history()
        self._save_stats()

    def _update_stats(self, alert: AlertInstance):
        """Update alert statistics."""
        self.stats['total_alerts'] += 1

        # Update by severity
        severity_key = alert.severity.value
        self.stats['alerts_by_severity'][severity_key] = self.stats['alerts_by_severity'].get(severity_key, 0) + 1

        # Update by type
        type_key = alert.alert_type.value
        self.stats['alerts_by_type'][type_key] = self.stats['alerts_by_type'].get(type_key, 0) + 1

        # Update by day
        day_key = alert.triggered_at.strftime('%Y-%m-%d')
        self.stats['alerts_by_day'][day_key] = self.stats['alerts_by_day'].get(day_key, 0) + 1

        # Update rule frequency
        rule_key = alert.rule_name
        self.stats['most_frequent_rules'][rule_key] = self.stats['most_frequent_rules'].get(rule_key, 0) + 1

    def _save_history(self):
        """Save alert history to storage."""
        try:
            # Keep only last 10000 alerts to prevent file from growing too large
            if len(self.history) > 10000:
                self.history = self.history[-10000:]

            with open(self.history_file, 'w') as f:
                json.dump({'alerts': self.history}, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save alert history: {e}")

    def _save_stats(self):
        """Save alert statistics to storage."""
        try:
            with open(self.stats_file, 'w') as f:
                json.dump(self.stats, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save alert stats: {e}")

    def get_recent_alerts(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent alerts."""
        return self.history[-limit:] if len(self.history) > limit else self.history

    def get_alerts_by_rule(self, rule_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get alerts for specific rule."""
        rule_alerts = [alert for alert in self.history if alert.get('rule_id') == rule_id]
        return rule_alerts[-limit:] if len(rule_alerts) > limit else rule_alerts

    def get_statistics(self) -> Dict[str, Any]:
        """Get alert statistics."""
        return self.stats.copy()


class AlertManager:
    """Main alert management system."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.rules: Dict[str, AlertRule] = {}
        self.active_alerts: Dict[str, AlertInstance] = {}
        self.notification_services: Dict[NotificationChannel, NotificationService] = {}
        self.history_manager = AlertHistoryManager(self.config.get('storage_path'))
        self.rule_triggers: Dict[str, List[datetime]] = {}  # Track rule trigger times
        self.running = False
        self.monitor_thread: Optional[threading.Thread] = None

        self._setup_notification_services()
        self._load_rules()

    def _setup_notification_services(self):
        """Initialize notification services."""
        notification_config = self.config.get('notifications', {})

        # Email service
        if notification_config.get('email', {}).get('enabled', False):
            self.notification_services[NotificationChannel.EMAIL] = EmailNotificationService(
                notification_config['email']
            )

        # Browser service
        if notification_config.get('browser', {}).get('enabled', False):
            self.notification_services[NotificationChannel.BROWSER] = BrowserNotificationService(
                notification_config['browser']
            )

        # Webhook service
        if notification_config.get('webhook', {}).get('enabled', False):
            self.notification_services[NotificationChannel.WEBHOOK] = WebhookNotificationService(
                notification_config['webhook']
            )

        # Console service (always enabled)
        self.notification_services[NotificationChannel.CONSOLE] = ConsoleNotificationService(
            {'enabled': True}
        )

    def _load_rules(self):
        """Load alert rules from configuration."""
        rules_config = self.config.get('rules', [])

        for rule_config in rules_config:
            try:
                rule = self._parse_rule_config(rule_config)
                self.rules[rule.id] = rule
            except Exception as e:
                logger.error(f"Failed to load rule: {e}")

    def _parse_rule_config(self, config: Dict[str, Any]) -> AlertRule:
        """Parse rule configuration into AlertRule object."""
        conditions = []
        for cond_config in config.get('conditions', []):
            condition = AlertCondition(
                field=cond_config['field'],
                operator=ConditionOperator(cond_config['operator']),
                value=cond_config['value'],
                comparison_field=cond_config.get('comparison_field'),
                timeframe=cond_config.get('timeframe')
            )
            conditions.append(condition)

        notification_channels = [
            NotificationChannel(channel)
            for channel in config.get('notification_channels', ['console'])
        ]

        return AlertRule(
            id=config.get('id', str(uuid4())),
            name=config['name'],
            description=config.get('description', ''),
            alert_type=AlertType(config.get('alert_type', 'custom')),
            severity=AlertSeverity(config.get('severity', 'medium')),
            conditions=conditions,
            enabled=config.get('enabled', True),
            notification_channels=notification_channels,
            cooldown_period=config.get('cooldown_period', 300),
            max_triggers_per_day=config.get('max_triggers_per_day', 50),
            tags=config.get('tags', []),
            metadata=config.get('metadata', {})
        )

    def add_rule(self, rule: AlertRule) -> bool:
        """Add or update an alert rule."""
        try:
            self.rules[rule.id] = rule
            logger.info(f"Added/updated alert rule: {rule.name}")
            return True
        except Exception as e:
            logger.error(f"Failed to add rule: {e}")
            return False

    def remove_rule(self, rule_id: str) -> bool:
        """Remove an alert rule."""
        try:
            if rule_id in self.rules:
                del self.rules[rule_id]
                logger.info(f"Removed alert rule: {rule_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to remove rule: {e}")
            return False

    def enable_rule(self, rule_id: str) -> bool:
        """Enable an alert rule."""
        if rule_id in self.rules:
            self.rules[rule_id].enabled = True
            logger.info(f"Enabled alert rule: {rule_id}")
            return True
        return False

    def disable_rule(self, rule_id: str) -> bool:
        """Disable an alert rule."""
        if rule_id in self.rules:
            self.rules[rule_id].enabled = False
            logger.info(f"Disabled alert rule: {rule_id}")
            return True
        return False

    def check_alerts(self, data: Dict[str, Any], historical_data: Optional[List[Dict]] = None):
        """Check all rules against current data."""
        for rule in self.rules.values():
            if not rule.enabled:
                continue

            # Check cooldown period
            if not self._check_cooldown(rule.id):
                continue

            # Check daily trigger limit
            if not self._check_daily_limit(rule.id):
                continue

            # Evaluate rule conditions
            if rule.evaluate(data, historical_data):
                self._trigger_alert(rule, data)

    def _check_cooldown(self, rule_id: str) -> bool:
        """Check if rule is in cooldown period."""
        if rule_id not in self.rule_triggers:
            return True

        rule = self.rules[rule_id]
        last_trigger = max(self.rule_triggers[rule_id]) if self.rule_triggers[rule_id] else None

        if last_trigger:
            time_since_last = (datetime.now() - last_trigger).total_seconds()
            return time_since_last >= rule.cooldown_period

        return True

    def _check_daily_limit(self, rule_id: str) -> bool:
        """Check if rule has exceeded daily trigger limit."""
        if rule_id not in self.rule_triggers:
            return True

        rule = self.rules[rule_id]
        today = datetime.now().date()

        todays_triggers = [
            trigger for trigger in self.rule_triggers[rule_id]
            if trigger.date() == today
        ]

        return len(todays_triggers) < rule.max_triggers_per_day

    def _trigger_alert(self, rule: AlertRule, data: Dict[str, Any]):
        """Trigger an alert for the given rule."""
        alert_id = str(uuid4())

        # Create alert instance
        alert = AlertInstance(
            id=alert_id,
            rule_id=rule.id,
            rule_name=rule.name,
            alert_type=rule.alert_type,
            severity=rule.severity,
            message=self._generate_alert_message(rule, data),
            data=data.copy(),
            status=AlertStatus.TRIGGERED,
            triggered_at=datetime.now()
        )

        # Store alert
        self.active_alerts[alert_id] = alert
        self.history_manager.add_alert(alert)

        # Track trigger time
        if rule.id not in self.rule_triggers:
            self.rule_triggers[rule.id] = []
        self.rule_triggers[rule.id].append(datetime.now())

        # Send notifications
        try:
            loop = asyncio.get_running_loop()
            asyncio.create_task(self._send_notifications(alert, rule.notification_channels))
        except RuntimeError:
            # No event loop running, use thread executor
            asyncio.run(self._send_notifications(alert, rule.notification_channels))

        logger.info(f"Alert triggered: {rule.name} [{alert.severity.value}]")

    def _generate_alert_message(self, rule: AlertRule, data: Dict[str, Any]) -> str:
        """Generate human-readable alert message."""
        if rule.alert_type == AlertType.PRICE_ALERT:
            symbol = data.get('symbol', 'Unknown')
            price = data.get('price', 'Unknown')
            return f"Price alert for {symbol}: {price}"
        elif rule.alert_type == AlertType.SYSTEM_HEALTH:
            return f"System health alert: {rule.description}"
        elif rule.alert_type == AlertType.DATA_QUALITY:
            return f"Data quality alert: {rule.description}"
        else:
            return rule.description or f"Alert triggered: {rule.name}"

    async def _send_notifications(self, alert: AlertInstance, channels: List[NotificationChannel]):
        """Send notifications through specified channels."""
        for channel in channels:
            if channel in self.notification_services:
                try:
                    success = await self.notification_services[channel].send_notification(alert)
                    alert.notification_history.append({
                        'channel': channel.value,
                        'sent_at': datetime.now().isoformat(),
                        'success': success
                    })
                except Exception as e:
                    logger.error(f"Failed to send notification via {channel.value}: {e}")
                    alert.notification_history.append({
                        'channel': channel.value,
                        'sent_at': datetime.now().isoformat(),
                        'success': False,
                        'error': str(e)
                    })

    def acknowledge_alert(self, alert_id: str, user: Optional[str] = None, notes: Optional[str] = None) -> bool:
        """Acknowledge an alert."""
        if alert_id in self.active_alerts:
            self.active_alerts[alert_id].acknowledge(user, notes)
            logger.info(f"Alert acknowledged: {alert_id}")
            return True
        return False

    def resolve_alert(self, alert_id: str, user: Optional[str] = None, notes: Optional[str] = None) -> bool:
        """Resolve an alert."""
        if alert_id in self.active_alerts:
            self.active_alerts[alert_id].resolve(user, notes)
            logger.info(f"Alert resolved: {alert_id}")
            return True
        return False

    def snooze_alert(self, alert_id: str, duration_minutes: int = 60) -> bool:
        """Snooze an alert."""
        if alert_id in self.active_alerts:
            self.active_alerts[alert_id].snooze(duration_minutes)
            logger.info(f"Alert snoozed: {alert_id} for {duration_minutes} minutes")
            return True
        return False

    def get_active_alerts(self) -> List[AlertInstance]:
        """Get all active alerts."""
        return [
            alert for alert in self.active_alerts.values()
            if alert.status in [AlertStatus.TRIGGERED, AlertStatus.ACKNOWLEDGED]
            and not alert.is_snoozed()
        ]

    def get_alert_statistics(self) -> Dict[str, Any]:
        """Get alert statistics."""
        stats = self.history_manager.get_statistics()

        # Add current active alert counts
        active_by_severity = {}
        for alert in self.get_active_alerts():
            severity = alert.severity.value
            active_by_severity[severity] = active_by_severity.get(severity, 0) + 1

        stats['active_alerts'] = len(self.get_active_alerts())
        stats['active_by_severity'] = active_by_severity
        stats['total_rules'] = len(self.rules)
        stats['enabled_rules'] = len([r for r in self.rules.values() if r.enabled])

        return stats

    def get_rules(self) -> List[AlertRule]:
        """Get all alert rules."""
        return list(self.rules.values())

    def get_rule(self, rule_id: str) -> Optional[AlertRule]:
        """Get specific alert rule."""
        return self.rules.get(rule_id)

    def start_monitoring(self):
        """Start the alert monitoring system."""
        if self.running:
            return

        self.running = True
        logger.info("Alert monitoring started")

    def stop_monitoring(self):
        """Stop the alert monitoring system."""
        self.running = False
        logger.info("Alert monitoring stopped")

    def cleanup_old_alerts(self, days: int = 30):
        """Clean up old resolved alerts."""
        cutoff_date = datetime.now() - timedelta(days=days)

        # Remove old active alerts that are resolved
        to_remove = []
        for alert_id, alert in self.active_alerts.items():
            if (alert.status == AlertStatus.RESOLVED and
                alert.resolved_at and alert.resolved_at < cutoff_date):
                to_remove.append(alert_id)

        for alert_id in to_remove:
            del self.active_alerts[alert_id]

        # Clean up old trigger history
        cutoff_time = datetime.now() - timedelta(days=days)
        for rule_id in self.rule_triggers:
            self.rule_triggers[rule_id] = [
                trigger for trigger in self.rule_triggers[rule_id]
                if trigger >= cutoff_time
            ]

        logger.info(f"Cleaned up {len(to_remove)} old alerts")


# Singleton instance
_alert_manager: Optional[AlertManager] = None


def get_alert_manager(config: Optional[Dict[str, Any]] = None) -> AlertManager:
    """Get or create the global AlertManager instance."""
    global _alert_manager
    if _alert_manager is None:
        _alert_manager = AlertManager(config)
    return _alert_manager


# Default alert rule templates
DEFAULT_ALERT_RULES = [
    {
        'name': 'High CPU Usage',
        'description': 'Alert when CPU usage exceeds 85%',
        'alert_type': 'system_health',
        'severity': 'high',
        'conditions': [
            {
                'field': 'system.cpu_percent',
                'operator': '>',
                'value': 85
            }
        ],
        'notification_channels': ['console', 'email'],
        'cooldown_period': 600,
        'max_triggers_per_day': 10
    },
    {
        'name': 'Low Memory Warning',
        'description': 'Alert when available memory is below 20%',
        'alert_type': 'system_health',
        'severity': 'medium',
        'conditions': [
            {
                'field': 'system.memory_percent',
                'operator': '>',
                'value': 80
            }
        ],
        'notification_channels': ['console'],
        'cooldown_period': 300,
        'max_triggers_per_day': 20
    },
    {
        'name': 'Data Quality Drop',
        'description': 'Alert when data quality grade drops below B',
        'alert_type': 'data_quality',
        'severity': 'medium',
        'conditions': [
            {
                'field': 'quality.overall_grade_numeric',
                'operator': '<',
                'value': 80
            }
        ],
        'notification_channels': ['console', 'webhook'],
        'cooldown_period': 900,
        'max_triggers_per_day': 5
    }
]