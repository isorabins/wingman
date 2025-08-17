"""
Alert System for WingmanMatch
Proactive performance monitoring with email and Slack notifications
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Set
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass
from enum import Enum
import json
from src.config import Config
from src.email_templates import email_service
from src.observability.metrics_collector import metrics_collector

logger = logging.getLogger(__name__)

class AlertSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"

@dataclass
class AlertRule:
    """Alert rule configuration"""
    name: str
    metric_type: str
    metric_name: str
    threshold: float
    comparison: str  # '>', '<', '>=', '<='
    severity: AlertSeverity
    cooldown_minutes: int = 15
    enabled: bool = True

@dataclass
class Alert:
    """Alert instance"""
    rule_name: str
    severity: AlertSeverity
    message: str
    value: float
    threshold: float
    timestamp: datetime
    resolved: bool = False
    resolved_at: Optional[datetime] = None

class AlertSystem:
    """Proactive alert system with notification management"""
    
    def __init__(self):
        self.alert_rules: List[AlertRule] = []
        self.active_alerts: List[Alert] = []
        self.alert_history: List[Alert] = []
        self.last_check_time: Optional[datetime] = None
        self.alert_cooldowns: Dict[str, datetime] = {}
        self.notification_enabled = True
        
        # Initialize default alert rules
        self._setup_default_rules()
    
    def _setup_default_rules(self):
        """Setup default performance alert rules"""
        default_rules = [
            # Request performance alerts
            AlertRule(
                name="high_request_latency_p95",
                metric_type="request",
                metric_name="*",  # All endpoints
                threshold=2000,  # 2 seconds
                comparison=">=",
                severity=AlertSeverity.CRITICAL,
                cooldown_minutes=10
            ),
            AlertRule(
                name="moderate_request_latency_p95",
                metric_type="request", 
                metric_name="*",
                threshold=1000,  # 1 second
                comparison=">=",
                severity=AlertSeverity.WARNING,
                cooldown_minutes=15
            ),
            
            # Database performance alerts
            AlertRule(
                name="slow_database_queries",
                metric_type="database",
                metric_name="*",
                threshold=500,  # 500ms
                comparison=">=",
                severity=AlertSeverity.WARNING,
                cooldown_minutes=10
            ),
            AlertRule(
                name="critical_database_queries",
                metric_type="database",
                metric_name="*", 
                threshold=2000,  # 2 seconds
                comparison=">=",
                severity=AlertSeverity.CRITICAL,
                cooldown_minutes=5
            ),
            
            # Error rate alerts
            AlertRule(
                name="high_error_rate",
                metric_type="request",
                metric_name="error_rate",
                threshold=10,  # 10%
                comparison=">=",
                severity=AlertSeverity.CRITICAL,
                cooldown_minutes=5
            ),
            AlertRule(
                name="moderate_error_rate",
                metric_type="request",
                metric_name="error_rate",
                threshold=5,  # 5%
                comparison=">=",
                severity=AlertSeverity.WARNING,
                cooldown_minutes=10
            )
        ]
        
        self.alert_rules.extend(default_rules)
        logger.info(f"Initialized {len(default_rules)} default alert rules")
    
    async def check_alerts(self):
        """Check all alert rules against current metrics"""
        if not self.notification_enabled:
            return
        
        try:
            # Get recent metrics for evaluation
            summary = await metrics_collector.get_performance_summary(hours=1)
            self.last_check_time = datetime.now(timezone.utc)
            
            # Check each alert rule
            for rule in self.alert_rules:
                if not rule.enabled:
                    continue
                
                # Check cooldown
                if rule.name in self.alert_cooldowns:
                    cooldown_end = self.alert_cooldowns[rule.name]
                    if datetime.now(timezone.utc) < cooldown_end:
                        continue
                
                # Evaluate rule
                triggered_alerts = await self._evaluate_rule(rule, summary)
                
                for alert in triggered_alerts:
                    await self._handle_alert(alert, rule)
            
            # Check for resolved alerts
            await self._check_resolved_alerts(summary)
            
        except Exception as e:
            logger.error(f"Error during alert check: {e}")
    
    async def _evaluate_rule(self, rule: AlertRule, summary: Dict[str, Any]) -> List[Alert]:
        """Evaluate a single alert rule against metrics"""
        alerts = []
        
        if rule.metric_type not in summary.get("metric_types", {}):
            return alerts
        
        metrics = summary["metric_types"][rule.metric_type]["metrics"]
        
        # Check specific metric or all metrics (wildcard)
        metrics_to_check = {}
        if rule.metric_name == "*":
            metrics_to_check = metrics
        elif rule.metric_name in metrics:
            metrics_to_check[rule.metric_name] = metrics[rule.metric_name]
        
        for metric_name, metric_data in metrics_to_check.items():
            # Get value to compare (use P95 for latency metrics)
            if rule.metric_type == "request" and "percentiles" in metric_data:
                value = metric_data["percentiles"]["p95"]
            elif rule.metric_name == "error_rate":
                # Calculate error rate from metadata
                value = self._calculate_error_rate(metric_data)
            else:
                value = metric_data.get("avg", 0)
            
            # Evaluate threshold
            if self._compare_value(value, rule.threshold, rule.comparison):
                alert = Alert(
                    rule_name=rule.name,
                    severity=rule.severity,
                    message=self._generate_alert_message(rule, metric_name, value),
                    value=value,
                    threshold=rule.threshold,
                    timestamp=datetime.now(timezone.utc)
                )
                alerts.append(alert)
        
        return alerts
    
    def _compare_value(self, value: float, threshold: float, comparison: str) -> bool:
        """Compare value against threshold using specified comparison"""
        if comparison == ">":
            return value > threshold
        elif comparison == ">=":
            return value >= threshold
        elif comparison == "<":
            return value < threshold
        elif comparison == "<=":
            return value <= threshold
        return False
    
    def _calculate_error_rate(self, metric_data: Dict[str, Any]) -> float:
        """Calculate error rate from metric data"""
        # This would need to be implemented based on how error metrics are stored
        # For now, return 0 as placeholder
        return 0.0
    
    def _generate_alert_message(self, rule: AlertRule, metric_name: str, value: float) -> str:
        """Generate human-readable alert message"""
        severity_emoji = {
            AlertSeverity.INFO: "ℹ️",
            AlertSeverity.WARNING: "⚠️", 
            AlertSeverity.CRITICAL: "🚨"
        }
        
        emoji = severity_emoji.get(rule.severity, "")
        
        if rule.metric_type == "request":
            return f"{emoji} High response time detected: {metric_name} P95 latency is {value:.0f}ms (threshold: {rule.threshold}ms)"
        elif rule.metric_type == "database":
            return f"{emoji} Slow database queries detected: {metric_name} average time is {value:.0f}ms (threshold: {rule.threshold}ms)"
        else:
            return f"{emoji} Alert: {metric_name} value {value:.2f} exceeds threshold {rule.threshold}"
    
    async def _handle_alert(self, alert: Alert, rule: AlertRule):
        """Handle triggered alert with notifications"""
        # Add to active alerts
        self.active_alerts.append(alert)
        self.alert_history.append(alert)
        
        # Set cooldown
        cooldown_end = datetime.now(timezone.utc) + timedelta(minutes=rule.cooldown_minutes)
        self.alert_cooldowns[rule.name] = cooldown_end
        
        # Send notifications
        await self._send_notifications(alert)
        
        logger.warning(f"Alert triggered: {alert.message}")
    
    async def _send_notifications(self, alert: Alert):
        """Send alert notifications via email and Slack"""
        try:
            # Send email notification
            if email_service.enabled:
                await self._send_email_alert(alert)
            
            # Send Slack notification (if configured)
            slack_webhook = getattr(Config, 'SLACK_WEBHOOK_URL', None)
            if slack_webhook:
                await self._send_slack_alert(alert, slack_webhook)
                
        except Exception as e:
            logger.error(f"Failed to send alert notifications: {e}")
    
    async def _send_email_alert(self, alert: Alert):
        """Send email alert notification"""
        try:
            admin_email = getattr(Config, 'PERFORMANCE_ALERT_EMAIL', 'admin@wingmanmatch.com')
            
            subject = f"WingmanMatch Performance Alert - {alert.severity.value.upper()}"
            
            html_content = f"""
            <h2>Performance Alert</h2>
            <p><strong>Severity:</strong> {alert.severity.value.upper()}</p>
            <p><strong>Alert:</strong> {alert.message}</p>
            <p><strong>Value:</strong> {alert.value:.2f}</p>
            <p><strong>Threshold:</strong> {alert.threshold}</p>
            <p><strong>Time:</strong> {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
            
            <h3>Recommended Actions:</h3>
            <ul>
                <li>Check system performance metrics</li>
                <li>Review database query performance</li>
                <li>Monitor error rates and response times</li>
                <li>Scale resources if necessary</li>
            </ul>
            
            <p>This is an automated alert from WingmanMatch monitoring system.</p>
            """
            
            await email_service.send_email(
                to_email=admin_email,
                subject=subject,
                html_content=html_content
            )
            
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")
    
    async def _send_slack_alert(self, alert: Alert, webhook_url: str):
        """Send Slack alert notification"""
        try:
            import aiohttp
            
            color_map = {
                AlertSeverity.INFO: "good",
                AlertSeverity.WARNING: "warning", 
                AlertSeverity.CRITICAL: "danger"
            }
            
            payload = {
                "attachments": [{
                    "color": color_map.get(alert.severity, "warning"),
                    "title": f"WingmanMatch Performance Alert - {alert.severity.value.upper()}",
                    "text": alert.message,
                    "fields": [
                        {"title": "Value", "value": f"{alert.value:.2f}", "short": True},
                        {"title": "Threshold", "value": f"{alert.threshold}", "short": True},
                        {"title": "Time", "value": alert.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC'), "short": False}
                    ],
                    "footer": "WingmanMatch Monitoring",
                    "ts": int(alert.timestamp.timestamp())
                }]
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=payload) as response:
                    if response.status == 200:
                        logger.info("Slack alert sent successfully")
                    else:
                        logger.error(f"Failed to send Slack alert: {response.status}")
                        
        except Exception as e:
            logger.error(f"Failed to send Slack alert: {e}")
    
    async def _check_resolved_alerts(self, summary: Dict[str, Any]):
        """Check if any active alerts have been resolved"""
        resolved_alerts = []
        
        for alert in self.active_alerts:
            if alert.resolved:
                continue
            
            # Check if alert condition is no longer true
            # Implementation would depend on specific alert logic
            # For now, mark alerts as resolved after 1 hour
            if datetime.now(timezone.utc) - alert.timestamp > timedelta(hours=1):
                alert.resolved = True
                alert.resolved_at = datetime.now(timezone.utc)
                resolved_alerts.append(alert)
        
        # Remove resolved alerts from active list
        self.active_alerts = [a for a in self.active_alerts if not a.resolved]
        
        # Send resolution notifications
        for alert in resolved_alerts:
            await self._send_resolution_notification(alert)
    
    async def _send_resolution_notification(self, alert: Alert):
        """Send alert resolution notification"""
        try:
            if email_service.enabled:
                admin_email = getattr(Config, 'PERFORMANCE_ALERT_EMAIL', 'admin@wingmanmatch.com')
                
                subject = f"WingmanMatch Alert Resolved - {alert.rule_name}"
                html_content = f"""
                <h2>Alert Resolved</h2>
                <p>The following alert has been resolved:</p>
                <p><strong>Alert:</strong> {alert.message}</p>
                <p><strong>Resolved at:</strong> {alert.resolved_at.strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
                <p><strong>Duration:</strong> {(alert.resolved_at - alert.timestamp).total_seconds() / 60:.1f} minutes</p>
                """
                
                await email_service.send_email(
                    to_email=admin_email,
                    subject=subject,
                    html_content=html_content
                )
                
            logger.info(f"Alert resolved: {alert.rule_name}")
            
        except Exception as e:
            logger.error(f"Failed to send resolution notification: {e}")
    
    def add_alert_rule(self, rule: AlertRule):
        """Add custom alert rule"""
        self.alert_rules.append(rule)
        logger.info(f"Added alert rule: {rule.name}")
    
    def remove_alert_rule(self, rule_name: str):
        """Remove alert rule by name"""
        self.alert_rules = [r for r in self.alert_rules if r.name != rule_name]
        logger.info(f"Removed alert rule: {rule_name}")
    
    def get_active_alerts(self) -> List[Alert]:
        """Get currently active alerts"""
        return [a for a in self.active_alerts if not a.resolved]
    
    def get_alert_history(self, hours: int = 24) -> List[Alert]:
        """Get alert history for specified time window"""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        return [a for a in self.alert_history if a.timestamp > cutoff_time]
    
    def enable_notifications(self):
        """Enable alert notifications"""
        self.notification_enabled = True
        logger.info("Alert notifications enabled")
    
    def disable_notifications(self):
        """Disable alert notifications"""
        self.notification_enabled = False
        logger.info("Alert notifications disabled")

# Global alert system instance
alert_system = AlertSystem()

# Background task for continuous monitoring
async def start_alert_monitoring():
    """Start background alert monitoring"""
    logger.info("Starting alert monitoring background task")
    
    while True:
        try:
            await alert_system.check_alerts()
            # Check every 2 minutes
            await asyncio.sleep(120)
        except Exception as e:
            logger.error(f"Error in alert monitoring: {e}")
            await asyncio.sleep(60)  # Wait 1 minute before retrying

# Convenience functions
async def trigger_custom_alert(message: str, severity: AlertSeverity = AlertSeverity.WARNING):
    """Trigger a custom alert"""
    alert = Alert(
        rule_name="custom",
        severity=severity,
        message=message,
        value=0,
        threshold=0,
        timestamp=datetime.now(timezone.utc)
    )
    
    await alert_system._send_notifications(alert)
    alert_system.alert_history.append(alert)

def get_active_alerts():
    """Get active alerts"""
    return alert_system.get_active_alerts()

def get_alert_history(hours: int = 24):
    """Get alert history"""
    return alert_system.get_alert_history(hours)
