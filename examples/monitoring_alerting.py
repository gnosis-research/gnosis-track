#!/usr/bin/env python3
"""
Monitoring and Alerting Examples for Gnosis-Track

This module demonstrates how to implement comprehensive monitoring
and alerting for your SeaweedFS-based logging infrastructure.
"""

import time
import json
import requests
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from gnosis_track.core.config_manager import ConfigManager
from gnosis_track.core.seaweed_client import SeaweedClient
from gnosis_track.core.bucket_manager import BucketManager
from gnosis_track.logging.log_streamer import LogStreamer


@dataclass
class AlertConfig:
    """Alert configuration."""
    name: str
    enabled: bool = True
    threshold: float = 0.0
    comparison: str = ">"  # >, <, >=, <=, ==, !=
    message: str = ""
    severity: str = "warning"  # info, warning, error, critical


@dataclass
class Alert:
    """Alert instance."""
    config: AlertConfig
    value: float
    timestamp: datetime
    message: str


class MonitoringSystem:
    """
    Comprehensive monitoring system for Gnosis-Track.
    
    Monitors system health, performance metrics, and log patterns
    to provide early warning of issues.
    """
    
    def __init__(self, config_path: str = None):
        """Initialize monitoring system."""
        self.config_manager = ConfigManager(config_path)
        self.config = self.config_manager.get_config()
        
        self.seaweed_client = SeaweedClient(self.config)
        self.bucket_manager = BucketManager(self.seaweed_client, self.config)
        
        self.bucket_name = self.config.get('logging', {}).get('bucket_name', 'validator-logs')
        self.log_streamer = LogStreamer(self.seaweed_client, self.bucket_name)
        
        # Alert configurations
        self.alert_configs = self._load_alert_configs()
        
        # Metrics history for trend analysis
        self.metrics_history: List[Dict[str, Any]] = []
        
    def _load_alert_configs(self) -> List[AlertConfig]:
        """Load alert configurations."""
        return [
            AlertConfig(
                name="high_error_rate",
                threshold=10.0,
                comparison=">=",
                message="High error rate detected: {value}% errors in last 5 minutes",
                severity="error"
            ),
            AlertConfig(
                name="storage_space_low",
                threshold=85.0,
                comparison=">=",
                message="Storage space critically low: {value}% used",
                severity="critical"
            ),
            AlertConfig(
                name="connection_failures",
                threshold=5.0,
                comparison=">=",
                message="Multiple connection failures: {value} failures detected",
                severity="warning"
            ),
            AlertConfig(
                name="memory_usage_high",
                threshold=90.0,
                comparison=">=",
                message="High memory usage: {value}% memory utilized",
                severity="warning"
            ),
            AlertConfig(
                name="slow_response_time",
                threshold=5000.0,  # 5 seconds in milliseconds
                comparison=">=",
                message="Slow response times: {value}ms average response time",
                severity="warning"
            ),
            AlertConfig(
                name="backup_failure",
                threshold=1.0,
                comparison=">=",
                message="Backup failures detected: {value} failed backups",
                severity="error"
            ),
            AlertConfig(
                name="validator_silence",
                threshold=300.0,  # 5 minutes in seconds
                comparison=">=",
                message="Validator silence: No logs from validator for {value} seconds",
                severity="warning"
            )
        ]
    
    def collect_metrics(self) -> Dict[str, Any]:
        """Collect comprehensive system metrics."""
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'system': self._collect_system_metrics(),
            'storage': self._collect_storage_metrics(),
            'logs': self._collect_log_metrics(),
            'performance': self._collect_performance_metrics(),
            'health': self._collect_health_metrics()
        }
        
        # Store metrics history
        self.metrics_history.append(metrics)
        
        # Keep only last 1000 entries
        if len(self.metrics_history) > 1000:
            self.metrics_history = self.metrics_history[-1000:]
        
        return metrics
    
    def _collect_system_metrics(self) -> Dict[str, Any]:
        """Collect system-level metrics."""
        import psutil
        
        return {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_usage': psutil.disk_usage('/').percent,
            'load_average': psutil.getloadavg()[0] if hasattr(psutil, 'getloadavg') else 0,
            'process_count': len(psutil.pids())
        }
    
    def _collect_storage_metrics(self) -> Dict[str, Any]:
        """Collect storage-related metrics."""
        try:
            # Get bucket statistics
            objects = self.seaweed_client.list_objects(self.bucket_name)
            
            total_objects = len(objects)
            total_size = sum(obj.get('Size', 0) for obj in objects)
            
            # Count validators
            validators = set()
            for obj in objects:
                parts = obj['Key'].split('/')
                if parts[0].startswith('validator_'):
                    validators.add(parts[0])
            
            return {
                'total_objects': total_objects,
                'total_size_bytes': total_size,
                'total_size_mb': total_size / (1024 * 1024),
                'total_validators': len(validators),
                'connection_healthy': True
            }
            
        except Exception as e:
            return {
                'total_objects': 0,
                'total_size_bytes': 0,
                'total_size_mb': 0,
                'total_validators': 0,
                'connection_healthy': False,
                'error': str(e)
            }
    
    def _collect_log_metrics(self) -> Dict[str, Any]:
        """Collect log-related metrics."""
        try:
            # Get recent log statistics
            cutoff_time = datetime.now() - timedelta(minutes=5)
            
            # This would analyze recent logs for patterns
            # For demo, return example metrics
            return {
                'logs_per_minute': 145,
                'error_rate_percent': 2.1,
                'warning_rate_percent': 8.5,
                'avg_log_size_bytes': 256,
                'active_validators': 15,
                'silent_validators': 0
            }
            
        except Exception as e:
            return {
                'logs_per_minute': 0,
                'error_rate_percent': 0,
                'warning_rate_percent': 0,
                'avg_log_size_bytes': 0,
                'active_validators': 0,
                'silent_validators': 0,
                'error': str(e)
            }
    
    def _collect_performance_metrics(self) -> Dict[str, Any]:
        """Collect performance metrics."""
        try:
            # Measure response time
            start_time = time.time()
            health_check = self.seaweed_client.health_check()
            response_time = (time.time() - start_time) * 1000  # Convert to ms
            
            return {
                'response_time_ms': response_time,
                'health_check_passed': health_check,
                'connection_pool_size': 10,  # Example metric
                'active_connections': 3,     # Example metric
                'failed_requests': 0         # Example metric
            }
            
        except Exception as e:
            return {
                'response_time_ms': 9999,
                'health_check_passed': False,
                'connection_pool_size': 0,
                'active_connections': 0,
                'failed_requests': 1,
                'error': str(e)
            }
    
    def _collect_health_metrics(self) -> Dict[str, Any]:
        """Collect overall health metrics."""
        try:
            bucket_health = self.bucket_manager.get_bucket_health(self.bucket_name)
            
            return {
                'overall_status': 'healthy',
                'seaweedfs_connected': True,
                'bucket_accessible': bucket_health.get('accessible', False),
                'backup_status': 'ok',
                'last_successful_backup': datetime.now().isoformat(),
                'uptime_seconds': 86400  # Example: 24 hours
            }
            
        except Exception as e:
            return {
                'overall_status': 'unhealthy',
                'seaweedfs_connected': False,
                'bucket_accessible': False,
                'backup_status': 'failed',
                'last_successful_backup': None,
                'uptime_seconds': 0,
                'error': str(e)
            }
    
    def check_alerts(self, metrics: Dict[str, Any]) -> List[Alert]:
        """Check metrics against alert thresholds."""
        alerts = []
        
        for alert_config in self.alert_configs:
            if not alert_config.enabled:
                continue
            
            value = self._extract_metric_value(metrics, alert_config.name)
            if value is None:
                continue
            
            if self._evaluate_threshold(value, alert_config.threshold, alert_config.comparison):
                alert = Alert(
                    config=alert_config,
                    value=value,
                    timestamp=datetime.now(),
                    message=alert_config.message.format(value=value)
                )
                alerts.append(alert)
        
        return alerts
    
    def _extract_metric_value(self, metrics: Dict[str, Any], alert_name: str) -> Optional[float]:
        """Extract metric value for alert checking."""
        metric_mappings = {
            'high_error_rate': metrics.get('logs', {}).get('error_rate_percent', 0),
            'storage_space_low': metrics.get('system', {}).get('disk_usage', 0),
            'connection_failures': metrics.get('performance', {}).get('failed_requests', 0),
            'memory_usage_high': metrics.get('system', {}).get('memory_percent', 0),
            'slow_response_time': metrics.get('performance', {}).get('response_time_ms', 0),
            'backup_failure': 0,  # Would check backup status
            'validator_silence': 0  # Would check validator activity
        }
        
        return metric_mappings.get(alert_name)
    
    def _evaluate_threshold(self, value: float, threshold: float, comparison: str) -> bool:
        """Evaluate if value meets threshold criteria."""
        if comparison == ">":
            return value > threshold
        elif comparison == ">=":
            return value >= threshold
        elif comparison == "<":
            return value < threshold
        elif comparison == "<=":
            return value <= threshold
        elif comparison == "==":
            return value == threshold
        elif comparison == "!=":
            return value != threshold
        return False


class AlertManager:
    """
    Alert management and notification system.
    
    Handles alert deduplication, escalation, and multiple
    notification channels.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize alert manager."""
        self.config = config
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        
    def process_alerts(self, alerts: List[Alert]) -> None:
        """Process new alerts and handle notifications."""
        for alert in alerts:
            alert_key = f"{alert.config.name}_{alert.config.severity}"
            
            # Check if this is a new alert or escalation
            if alert_key not in self.active_alerts:
                self.active_alerts[alert_key] = alert
                self.alert_history.append(alert)
                self._send_notification(alert)
            else:
                # Update existing alert but don't re-notify immediately
                existing_alert = self.active_alerts[alert_key]
                time_since_last = alert.timestamp - existing_alert.timestamp
                
                # Re-notify for critical alerts every 15 minutes
                if (alert.config.severity == "critical" and 
                    time_since_last > timedelta(minutes=15)):
                    self._send_notification(alert)
                    self.active_alerts[alert_key] = alert
    
    def _send_notification(self, alert: Alert) -> None:
        """Send alert notification via configured channels."""
        print(f"🚨 ALERT: {alert.message}")
        
        # Send to Slack
        self._send_slack_notification(alert)
        
        # Send email for critical alerts
        if alert.config.severity == "critical":
            self._send_email_notification(alert)
        
        # Log alert
        self._log_alert(alert)
    
    def _send_slack_notification(self, alert: Alert) -> None:
        """Send alert to Slack webhook."""
        webhook_url = self.config.get('alerting', {}).get('webhook_url')
        if not webhook_url:
            return
        
        # Map severity to emoji and color
        severity_config = {
            'info': {'emoji': 'ℹ️', 'color': '#36a64f'},
            'warning': {'emoji': '⚠️', 'color': '#ff9500'},
            'error': {'emoji': '❌', 'color': '#ff0000'},
            'critical': {'emoji': '🚨', 'color': '#ff0000'}
        }
        
        config = severity_config.get(alert.config.severity, severity_config['warning'])
        
        payload = {
            'attachments': [{
                'color': config['color'],
                'title': f"{config['emoji']} Gnosis-Track Alert",
                'text': alert.message,
                'fields': [
                    {'title': 'Severity', 'value': alert.config.severity.upper(), 'short': True},
                    {'title': 'Time', 'value': alert.timestamp.strftime('%Y-%m-%d %H:%M:%S'), 'short': True},
                    {'title': 'Value', 'value': str(alert.value), 'short': True},
                    {'title': 'Alert', 'value': alert.config.name, 'short': True}
                ],
                'footer': 'Gnosis-Track Monitoring',
                'ts': int(alert.timestamp.timestamp())
            }]
        }
        
        try:
            response = requests.post(webhook_url, json=payload, timeout=10)
            response.raise_for_status()
        except Exception as e:
            print(f"Failed to send Slack notification: {e}")
    
    def _send_email_notification(self, alert: Alert) -> None:
        """Send email notification for critical alerts."""
        email_config = self.config.get('alerting', {}).get('email', {})
        if not email_config.get('enabled'):
            return
        
        try:
            msg = MIMEMultipart()
            msg['From'] = email_config['from_address']
            msg['To'] = email_config['to_addresses']
            msg['Subject'] = f"🚨 Gnosis-Track Critical Alert: {alert.config.name}"
            
            body = f"""
            Critical Alert from Gnosis-Track Monitoring System
            
            Alert: {alert.config.name}
            Severity: {alert.config.severity.upper()}
            Message: {alert.message}
            Value: {alert.value}
            Time: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}
            
            Please investigate immediately.
            
            ---
            Gnosis-Track Monitoring System
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(email_config['smtp_server'], email_config['smtp_port'])
            if email_config.get('use_tls'):
                server.starttls()
            if email_config.get('username'):
                server.login(email_config['username'], email_config['password'])
            
            server.send_message(msg)
            server.quit()
            
        except Exception as e:
            print(f"Failed to send email notification: {e}")
    
    def _log_alert(self, alert: Alert) -> None:
        """Log alert to file."""
        log_entry = {
            'timestamp': alert.timestamp.isoformat(),
            'alert_name': alert.config.name,
            'severity': alert.config.severity,
            'message': alert.message,
            'value': alert.value
        }
        
        # In production, write to log file
        print(f"ALERT LOG: {json.dumps(log_entry)}")
    
    def clear_alert(self, alert_name: str, severity: str) -> None:
        """Clear an active alert."""
        alert_key = f"{alert_name}_{severity}"
        if alert_key in self.active_alerts:
            cleared_alert = self.active_alerts.pop(alert_key)
            print(f"✅ Alert cleared: {cleared_alert.config.name}")
    
    def get_active_alerts(self) -> List[Alert]:
        """Get list of currently active alerts."""
        return list(self.active_alerts.values())


def main_monitoring_loop():
    """
    Main monitoring loop example.
    
    This shows how to implement a continuous monitoring system
    that collects metrics and processes alerts.
    """
    print("🔍 Starting Gnosis-Track Monitoring System...")
    
    # Initialize monitoring components
    monitoring = MonitoringSystem()
    alert_manager = AlertManager(monitoring.config)
    
    # Monitoring loop
    try:
        while True:
            print(f"\n📊 Collecting metrics at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Collect metrics
            metrics = monitoring.collect_metrics()
            
            # Check for alerts
            alerts = monitoring.check_alerts(metrics)
            
            # Process alerts
            if alerts:
                alert_manager.process_alerts(alerts)
            else:
                print("✅ No alerts detected")
            
            # Display key metrics
            print(f"   CPU: {metrics['system']['cpu_percent']:.1f}%")
            print(f"   Memory: {metrics['system']['memory_percent']:.1f}%")
            print(f"   Storage: {metrics['storage']['total_size_mb']:.1f} MB")
            print(f"   Response Time: {metrics['performance']['response_time_ms']:.1f} ms")
            
            # Wait before next check
            time.sleep(60)  # Check every minute
            
    except KeyboardInterrupt:
        print("\n🛑 Monitoring stopped by user")
    except Exception as e:
        print(f"❌ Monitoring error: {e}")


def example_custom_monitoring():
    """
    Example of custom monitoring for specific use cases.
    """
    print("🎯 Custom Monitoring Example")
    
    monitoring = MonitoringSystem()
    
    # Example: Monitor specific validators
    important_validators = [100, 101, 102, 200, 201]
    
    for validator_uid in important_validators:
        try:
            # Check if validator has recent logs
            logs = monitoring.log_streamer._fetch_all_logs(
                validator_uid, None, None, 10
            )
            
            if logs:
                latest_log = max(logs, key=lambda x: x.get('timestamp', ''))
                last_seen = datetime.fromisoformat(
                    latest_log['timestamp'].replace('Z', '+00:00')
                )
                
                time_since = datetime.now() - last_seen.replace(tzinfo=None)
                
                if time_since > timedelta(minutes=10):
                    print(f"⚠️  Validator {validator_uid}: No logs for {time_since}")
                else:
                    print(f"✅ Validator {validator_uid}: Active")
            else:
                print(f"❌ Validator {validator_uid}: No logs found")
                
        except Exception as e:
            print(f"❌ Validator {validator_uid}: Error checking logs - {e}")


def example_alerting_integration():
    """
    Example of integrating with external monitoring systems.
    """
    print("🔗 External Integration Example")
    
    monitoring = MonitoringSystem()
    metrics = monitoring.collect_metrics()
    
    # Export metrics to Prometheus format
    prometheus_metrics = f"""
# HELP gnosis_track_response_time Response time in milliseconds
# TYPE gnosis_track_response_time gauge
gnosis_track_response_time {metrics['performance']['response_time_ms']}

# HELP gnosis_track_memory_usage Memory usage percentage
# TYPE gnosis_track_memory_usage gauge
gnosis_track_memory_usage {metrics['system']['memory_percent']}

# HELP gnosis_track_storage_objects Total storage objects
# TYPE gnosis_track_storage_objects gauge
gnosis_track_storage_objects {metrics['storage']['total_objects']}

# HELP gnosis_track_active_validators Active validators count
# TYPE gnosis_track_active_validators gauge
gnosis_track_active_validators {metrics['logs']['active_validators']}
"""
    
    print("Prometheus metrics:")
    print(prometheus_metrics)
    
    # Could write to file for Prometheus scraping
    # with open('/var/lib/prometheus/gnosis_track.prom', 'w') as f:
    #     f.write(prometheus_metrics)


if __name__ == "__main__":
    print("Gnosis-Track Monitoring and Alerting Examples")
    print("=" * 50)
    
    # Run main monitoring loop
    main_monitoring_loop()