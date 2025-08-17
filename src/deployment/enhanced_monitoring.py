"""
Enhanced Monitoring Integration for Production Deployment
Integrates existing Task 22 performance infrastructure with external monitoring services
"""

import asyncio
import logging
import time
import uuid
from typing import Dict, Any, Optional
from datetime import datetime, timezone
import json
import traceback
from contextlib import asynccontextmanager

from src.config import Config
from src.observability.metrics_collector import metrics_collector, record_request_metric
from src.observability.alert_system import alert_system, AlertSeverity
from src.deployment.production_config import production_config

logger = logging.getLogger(__name__)

class EnhancedMonitoring:
    """Enhanced monitoring with external service integration"""
    
    def __init__(self):
        self.sentry_enabled = False
        self.datadog_enabled = False
        self.uptime_robot_enabled = False
        self.correlation_id_header = "X-Correlation-ID"
        
        # Initialize external services
        self._init_sentry()
        self._init_datadog()
        self._init_uptime_robot()
        
    def _init_sentry(self):
        """Initialize Sentry error tracking"""
        try:
            if production_config.monitoring_config.sentry_dsn:
                import sentry_sdk
                from sentry_sdk.integrations.fastapi import FastApiIntegration
                from sentry_sdk.integrations.asyncio import AsyncioIntegration
                
                sentry_sdk.init(
                    dsn=production_config.monitoring_config.sentry_dsn,
                    environment=production_config.environment,
                    traces_sample_rate=0.1,  # 10% performance monitoring
                    profiles_sample_rate=0.1,  # 10% profiling
                    integrations=[
                        FastApiIntegration(auto_enabling_integrations=False),
                        AsyncioIntegration()
                    ],
                    before_send=self._filter_sentry_event
                )
                
                self.sentry_enabled = True
                self.sentry_sdk = sentry_sdk
                logger.info("Sentry error tracking initialized")
                
        except ImportError:
            logger.warning("Sentry SDK not available - error tracking disabled")
        except Exception as e:
            logger.error(f"Failed to initialize Sentry: {e}")
    
    def _init_datadog(self):
        """Initialize Datadog logging"""
        try:
            if production_config.monitoring_config.datadog_api_key:
                # Datadog logging would be configured here
                # For now, we'll integrate with structured logging
                self.datadog_enabled = True
                logger.info("Datadog integration enabled")
                
        except Exception as e:
            logger.error(f"Failed to initialize Datadog: {e}")
    
    def _init_uptime_robot(self):
        """Initialize UptimeRobot monitoring"""
        try:
            if production_config.monitoring_config.uptime_robot_api_key:
                self.uptime_robot_enabled = True
                logger.info("UptimeRobot monitoring enabled")
                
        except Exception as e:
            logger.error(f"Failed to initialize UptimeRobot: {e}")
    
    def _filter_sentry_event(self, event, hint):
        """Filter Sentry events before sending"""
        # Filter out expected errors or noise
        if 'exc_info' in hint:
            exc_type, exc_value, tb = hint['exc_info']
            
            # Don't send health check 404s
            if "404" in str(exc_value) and "/health" in str(exc_value):
                return None
                
            # Don't send rate limiting errors
            if "rate limit" in str(exc_value).lower():
                return None
        
        return event
    
    async def create_monitoring_middleware(self):
        """Create enhanced monitoring middleware"""
        async def monitoring_middleware(request, call_next):
            start_time = time.time()
            correlation_id = str(uuid.uuid4())
            
            # Add correlation ID to request
            request.state.correlation_id = correlation_id
            
            # Add to Sentry scope
            if self.sentry_enabled:
                with self.sentry_sdk.configure_scope() as scope:
                    scope.set_tag("correlation_id", correlation_id)
                    scope.set_tag("endpoint", request.url.path)
                    scope.set_tag("method", request.method)
            
            # Structured logging with correlation ID
            logger.info(
                "Request started",
                extra={
                    "correlation_id": correlation_id,
                    "method": request.method,
                    "path": request.url.path,
                    "user_agent": request.headers.get("user-agent"),
                    "ip": request.client.host if request.client else None
                }
            )
            
            try:
                response = await call_next(request)
                duration_ms = (time.time() - start_time) * 1000
                
                # Record metrics using existing system
                await record_request_metric(
                    endpoint=request.url.path,
                    duration_ms=duration_ms,
                    status_code=response.status_code
                )
                
                # Enhanced logging
                logger.info(
                    "Request completed",
                    extra={
                        "correlation_id": correlation_id,
                        "status_code": response.status_code,
                        "duration_ms": duration_ms,
                        "path": request.url.path
                    }
                )
                
                # Add correlation ID to response headers
                response.headers[self.correlation_id_header] = correlation_id
                
                return response
                
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                
                # Enhanced error logging
                logger.error(
                    "Request failed",
                    extra={
                        "correlation_id": correlation_id,
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "duration_ms": duration_ms,
                        "path": request.url.path,
                        "traceback": traceback.format_exc()
                    }
                )
                
                # Send to Sentry
                if self.sentry_enabled:
                    self.sentry_sdk.capture_exception(e)
                
                # Trigger custom alert for critical errors
                if response.status_code >= 500:
                    await self._trigger_error_alert(request.url.path, str(e), correlation_id)
                
                raise
        
        return monitoring_middleware
    
    async def _trigger_error_alert(self, endpoint: str, error: str, correlation_id: str):
        """Trigger alert for critical errors"""
        try:
            from src.observability.alert_system import trigger_custom_alert
            
            message = f"Critical error on {endpoint}: {error} (ID: {correlation_id})"
            await trigger_custom_alert(message, AlertSeverity.CRITICAL)
            
        except Exception as e:
            logger.error(f"Failed to trigger error alert: {e}")
    
    async def health_check_with_monitoring(self) -> Dict[str, Any]:
        """Enhanced health check with monitoring service status"""
        from src.observability.health_monitor import health_monitor
        
        # Get basic health check
        basic_health = await health_monitor.get_health_status()
        
        # Add monitoring service status
        monitoring_status = {
            "sentry": {
                "enabled": self.sentry_enabled,
                "configured": bool(production_config.monitoring_config.sentry_dsn)
            },
            "datadog": {
                "enabled": self.datadog_enabled,
                "configured": bool(production_config.monitoring_config.datadog_api_key)
            },
            "uptime_robot": {
                "enabled": self.uptime_robot_enabled,
                "configured": bool(production_config.monitoring_config.uptime_robot_api_key)
            },
            "slack_alerts": {
                "configured": bool(production_config.monitoring_config.slack_webhook_url)
            }
        }
        
        # Add deployment info
        deployment_info = production_config.get_deployment_info()
        
        return {
            **basic_health,
            "monitoring": monitoring_status,
            "deployment": deployment_info,
            "correlation_id": str(uuid.uuid4())
        }
    
    async def get_performance_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive performance data for dashboard"""
        # Get performance summary from existing system
        performance_summary = await metrics_collector.get_performance_summary(hours=1)
        
        # Get real-time metrics
        real_time_metrics = await metrics_collector.get_real_time_metrics()
        
        # Get alert status
        active_alerts = alert_system.get_active_alerts()
        alert_history = alert_system.get_alert_history(hours=24)
        
        # Production readiness check
        readiness_check = production_config.validate_production_readiness()
        
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "environment": production_config.environment,
            "performance_summary": performance_summary,
            "real_time_metrics": real_time_metrics,
            "alerts": {
                "active": len(active_alerts),
                "last_24h": len(alert_history),
                "details": [
                    {
                        "severity": alert.severity.value,
                        "message": alert.message,
                        "timestamp": alert.timestamp.isoformat()
                    }
                    for alert in active_alerts[:5]  # Latest 5 alerts
                ]
            },
            "production_readiness": readiness_check,
            "monitoring_services": {
                "sentry_enabled": self.sentry_enabled,
                "datadog_enabled": self.datadog_enabled,
                "uptime_robot_enabled": self.uptime_robot_enabled
            }
        }
    
    def create_structured_logger(self, name: str):
        """Create structured logger with correlation ID support"""
        base_logger = logging.getLogger(name)
        
        class StructuredLogger:
            def __init__(self, logger):
                self.logger = logger
            
            def _log_with_structure(self, level, message, **kwargs):
                extra = {
                    "service": "wingman-match",
                    "environment": production_config.environment,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    **kwargs
                }
                
                self.logger.log(level, message, extra=extra)
            
            def info(self, message, **kwargs):
                self._log_with_structure(logging.INFO, message, **kwargs)
            
            def warning(self, message, **kwargs):
                self._log_with_structure(logging.WARNING, message, **kwargs)
            
            def error(self, message, **kwargs):
                self._log_with_structure(logging.ERROR, message, **kwargs)
            
            def critical(self, message, **kwargs):
                self._log_with_structure(logging.CRITICAL, message, **kwargs)
        
        return StructuredLogger(base_logger)

# Global enhanced monitoring instance
enhanced_monitoring = EnhancedMonitoring()

# Convenience functions for integration
async def get_monitoring_middleware():
    """Get enhanced monitoring middleware"""
    return await enhanced_monitoring.create_monitoring_middleware()

async def get_enhanced_health_check():
    """Get enhanced health check"""
    return await enhanced_monitoring.health_check_with_monitoring()

async def get_performance_dashboard():
    """Get performance dashboard data"""
    return await enhanced_monitoring.get_performance_dashboard_data()

def get_structured_logger(name: str):
    """Get structured logger"""
    return enhanced_monitoring.create_structured_logger(name)
