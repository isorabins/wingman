"""
Performance Dashboard API Endpoints for WingmanMatch
Provides real-time metrics, historical performance data, and health status
"""

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import logging

from src.observability.metrics_collector import (
    metrics_collector, 
    get_performance_summary,
    get_real_time_metrics
)
from src.observability.health_monitor import (
    health_monitor,
    get_health_status,
    get_quick_health,
    get_health_trends
)
from src.observability.alert_system import (
    alert_system,
    get_active_alerts,
    get_alert_history,
    trigger_custom_alert,
    AlertSeverity
)
from src.middleware.performance_middleware import get_performance_middleware

logger = logging.getLogger(__name__)

# Create router for performance endpoints
performance_router = APIRouter(prefix="/api/performance", tags=["performance"])

# Pydantic models for responses
class PerformanceMetricsResponse(BaseModel):
    """Performance metrics response model"""
    time_window_hours: int
    total_metrics: int
    metric_types: Dict[str, Any]
    performance_insights: List[Dict[str, Any]]

class HealthStatusResponse(BaseModel):
    """Health status response model"""
    overall_healthy: bool
    composite_score: int
    total_check_time_ms: float
    timestamp: str
    services: Dict[str, Any]
    health_insights: List[Dict[str, Any]]

class RealTimeMetricsResponse(BaseModel):
    """Real-time metrics response model"""
    timestamp: str
    requests_per_minute: int
    avg_response_time_ms: float
    avg_db_time_ms: float
    total_operations: int

class AlertResponse(BaseModel):
    """Alert response model"""
    rule_name: str
    severity: str
    message: str
    value: float
    threshold: float
    timestamp: str
    resolved: bool = False

class CustomAlertRequest(BaseModel):
    """Custom alert request model"""
    message: str
    severity: str = Field(default="warning", regex="^(info|warning|critical)$")

@performance_router.get("/metrics/realtime", response_model=RealTimeMetricsResponse)
async def get_realtime_metrics():
    """Get current real-time performance metrics"""
    try:
        metrics = await get_real_time_metrics()
        
        if "status" in metrics and metrics["status"] == "no_recent_data":
            # Return default response when no data available
            return RealTimeMetricsResponse(
                timestamp=datetime.now(timezone.utc).isoformat(),
                requests_per_minute=0,
                avg_response_time_ms=0.0,
                avg_db_time_ms=0.0,
                total_operations=0
            )
        
        return RealTimeMetricsResponse(**metrics)
        
    except Exception as e:
        logger.error(f"Failed to get real-time metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve real-time metrics")

@performance_router.get("/metrics/summary", response_model=PerformanceMetricsResponse)
async def get_metrics_summary(
    hours: int = Query(default=1, ge=1, le=168, description="Time window in hours (1-168)")
):
    """Get performance metrics summary for specified time window"""
    try:
        summary = await get_performance_summary(hours=hours)
        
        if "error" in summary:
            raise HTTPException(status_code=404, detail=summary["error"])
        
        return PerformanceMetricsResponse(**summary)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get metrics summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve metrics summary")

@performance_router.get("/metrics/slow-requests")
async def get_slow_requests(
    threshold_ms: float = Query(default=1000, ge=100, description="Minimum response time in ms"),
    limit: int = Query(default=10, ge=1, le=100, description="Maximum number of results")
):
    """Get slowest requests above threshold"""
    try:
        middleware = get_performance_middleware()
        if not middleware:
            raise HTTPException(status_code=503, detail="Performance middleware not available")
        
        slow_requests = middleware.get_slow_requests(threshold_ms=threshold_ms, limit=limit)
        
        return {
            "threshold_ms": threshold_ms,
            "total_slow_requests": len(slow_requests),
            "slow_requests": slow_requests
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get slow requests: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve slow requests")

@performance_router.get("/metrics/errors")
async def get_error_requests(
    limit: int = Query(default=10, ge=1, le=100, description="Maximum number of results")
):
    """Get recent error requests"""
    try:
        middleware = get_performance_middleware()
        if not middleware:
            raise HTTPException(status_code=503, detail="Performance middleware not available")
        
        error_requests = middleware.get_error_requests(limit=limit)
        
        return {
            "total_error_requests": len(error_requests),
            "error_requests": error_requests
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get error requests: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve error requests")

@performance_router.get("/health/status", response_model=HealthStatusResponse)
async def get_detailed_health_status():
    """Get comprehensive health status across all services"""
    try:
        health_status = await get_health_status()
        return HealthStatusResponse(**health_status)
        
    except Exception as e:
        logger.error(f"Failed to get health status: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve health status")

@performance_router.get("/health/quick")
async def get_quick_health_check():
    """Get quick health check for basic service availability"""
    try:
        health = await get_quick_health()
        return health
        
    except Exception as e:
        logger.error(f"Failed to get quick health check: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve health status")

@performance_router.get("/health/trends")
async def get_health_trend_data(
    hours: int = Query(default=24, ge=1, le=168, description="Time window in hours (1-168)")
):
    """Get health trends over specified time window"""
    try:
        trends = await get_health_trends(hours=hours)
        
        if "error" in trends:
            raise HTTPException(status_code=404, detail=trends["error"])
        
        return trends
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get health trends: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve health trends")

@performance_router.get("/alerts/active", response_model=List[AlertResponse])
async def get_active_alert_list():
    """Get currently active performance alerts"""
    try:
        active_alerts = get_active_alerts()
        
        return [
            AlertResponse(
                rule_name=alert.rule_name,
                severity=alert.severity.value,
                message=alert.message,
                value=alert.value,
                threshold=alert.threshold,
                timestamp=alert.timestamp.isoformat(),
                resolved=alert.resolved
            )
            for alert in active_alerts
        ]
        
    except Exception as e:
        logger.error(f"Failed to get active alerts: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve active alerts")

@performance_router.get("/alerts/history", response_model=List[AlertResponse])
async def get_alert_history_data(
    hours: int = Query(default=24, ge=1, le=168, description="Time window in hours (1-168)")
):
    """Get alert history for specified time window"""
    try:
        alert_history = get_alert_history(hours=hours)
        
        return [
            AlertResponse(
                rule_name=alert.rule_name,
                severity=alert.severity.value,
                message=alert.message,
                value=alert.value,
                threshold=alert.threshold,
                timestamp=alert.timestamp.isoformat(),
                resolved=alert.resolved
            )
            for alert in alert_history
        ]
        
    except Exception as e:
        logger.error(f"Failed to get alert history: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve alert history")

@performance_router.post("/alerts/custom")
async def create_custom_alert(alert_request: CustomAlertRequest):
    """Trigger a custom performance alert"""
    try:
        severity_map = {
            "info": AlertSeverity.INFO,
            "warning": AlertSeverity.WARNING,
            "critical": AlertSeverity.CRITICAL
        }
        
        severity = severity_map.get(alert_request.severity.lower(), AlertSeverity.WARNING)
        
        await trigger_custom_alert(
            message=alert_request.message,
            severity=severity
        )
        
        return {
            "success": True,
            "message": "Custom alert triggered successfully",
            "alert": {
                "message": alert_request.message,
                "severity": alert_request.severity,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to trigger custom alert: {e}")
        raise HTTPException(status_code=500, detail="Failed to trigger custom alert")

@performance_router.post("/alerts/enable")
async def enable_alert_notifications():
    """Enable alert notifications"""
    try:
        alert_system.enable_notifications()
        return {"success": True, "message": "Alert notifications enabled"}
        
    except Exception as e:
        logger.error(f"Failed to enable alerts: {e}")
        raise HTTPException(status_code=500, detail="Failed to enable alert notifications")

@performance_router.post("/alerts/disable")
async def disable_alert_notifications():
    """Disable alert notifications"""
    try:
        alert_system.disable_notifications()
        return {"success": True, "message": "Alert notifications disabled"}
        
    except Exception as e:
        logger.error(f"Failed to disable alerts: {e}")
        raise HTTPException(status_code=500, detail="Failed to disable alert notifications")

@performance_router.get("/dashboard")
async def get_performance_dashboard():
    """Get comprehensive performance dashboard data"""
    try:
        # Gather all dashboard data
        real_time = await get_real_time_metrics()
        summary_1h = await get_performance_summary(hours=1)
        summary_24h = await get_performance_summary(hours=24)
        health = await get_health_status()
        active_alerts = get_active_alerts()
        
        # Get middleware metrics if available
        middleware = get_performance_middleware()
        middleware_summary = {}
        if middleware:
            middleware_summary = middleware.get_metrics_summary(hours=1)
        
        dashboard_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "real_time_metrics": real_time,
            "performance_summary_1h": summary_1h,
            "performance_summary_24h": summary_24h,
            "health_status": health,
            "active_alerts_count": len(active_alerts),
            "active_alerts": [
                {
                    "rule_name": alert.rule_name,
                    "severity": alert.severity.value,
                    "message": alert.message,
                    "timestamp": alert.timestamp.isoformat()
                }
                for alert in active_alerts[:5]  # Show only top 5
            ],
            "middleware_metrics": middleware_summary
        }
        
        return dashboard_data
        
    except Exception as e:
        logger.error(f"Failed to get dashboard data: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve dashboard data")

@performance_router.post("/metrics/cleanup")
async def cleanup_old_metrics(
    hours: int = Query(default=48, ge=24, le=168, description="Clean metrics older than X hours")
):
    """Clean up old performance metrics (admin operation)"""
    try:
        await metrics_collector.cleanup_old_metrics(hours=hours)
        return {
            "success": True,
            "message": f"Cleaned up metrics older than {hours} hours"
        }
        
    except Exception as e:
        logger.error(f"Failed to cleanup metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to cleanup old metrics")

@performance_router.get("/status")
async def get_performance_monitoring_status():
    """Get status of performance monitoring systems"""
    try:
        middleware = get_performance_middleware()
        
        status = {
            "monitoring_enabled": True,
            "metrics_collection_enabled": metrics_collector.collection_enabled,
            "alert_notifications_enabled": alert_system.notification_enabled,
            "middleware_available": middleware is not None,
            "total_metrics_collected": len(metrics_collector.metrics),
            "total_alert_rules": len(alert_system.alert_rules),
            "active_alerts_count": len(get_active_alerts()),
            "last_alert_check": alert_system.last_check_time.isoformat() if alert_system.last_check_time else None
        }
        
        if middleware:
            status["middleware_metrics_count"] = len(middleware.request_metrics)
        
        return status
        
    except Exception as e:
        logger.error(f"Failed to get monitoring status: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve monitoring status")

# Background task for metrics cleanup
async def schedule_metrics_cleanup():
    """Background task to clean up old metrics"""
    try:
        await metrics_collector.cleanup_old_metrics(hours=48)
        logger.info("Scheduled metrics cleanup completed")
    except Exception as e:
        logger.error(f"Scheduled metrics cleanup failed: {e}")
