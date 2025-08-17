"""
Production Monitoring Dashboard for WingmanMatch
Comprehensive dashboard integrating all monitoring systems
"""

import asyncio
import logging
from typing import Dict, Any, List
from datetime import datetime, timezone, timedelta
import json

from src.config import Config
from src.deployment.production_config import production_config
from src.deployment.enhanced_monitoring import enhanced_monitoring
from src.deployment.backup_recovery import backup_verification
from src.deployment.feature_flags import feature_flag_manager
from src.observability.metrics_collector import metrics_collector
from src.observability.alert_system import alert_system

logger = logging.getLogger(__name__)

class MonitoringDashboard:
    """Comprehensive production monitoring dashboard"""
    
    def __init__(self):
        self.refresh_interval_seconds = 60
        self.dashboard_cache = {}
        self.last_refresh = None
        
    async def get_dashboard_data(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Get comprehensive dashboard data"""
        try:
            # Check cache freshness
            if not force_refresh and self._is_cache_valid():
                return self.dashboard_cache
            
            # Collect all monitoring data
            dashboard_data = await self._collect_dashboard_data()
            
            # Update cache
            self.dashboard_cache = dashboard_data
            self.last_refresh = datetime.now(timezone.utc)
            
            return dashboard_data
            
        except Exception as e:
            logger.error(f"Dashboard data collection failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    async def _collect_dashboard_data(self) -> Dict[str, Any]:
        """Collect comprehensive monitoring data"""
        timestamp = datetime.now(timezone.utc)
        
        # Collect data from all systems in parallel
        tasks = {
            "system_health": self._get_system_health(),
            "performance_metrics": self._get_performance_metrics(),
            "alert_status": self._get_alert_status(),
            "deployment_status": self._get_deployment_status(),
            "feature_flags": self._get_feature_flags_status(),
            "backup_status": self._get_backup_status(),
            "service_status": self._get_service_status()
        }
        
        # Execute all tasks concurrently
        results = {}
        for key, task in tasks.items():
            try:
                results[key] = await task
            except Exception as e:
                logger.error(f"Failed to collect {key}: {e}")
                results[key] = {
                    "status": "error",
                    "error": str(e)
                }
        
        # Calculate overall health score
        health_score = self._calculate_health_score(results)
        
        return {
            "timestamp": timestamp.isoformat(),
            "environment": production_config.environment,
            "health_score": health_score,
            "overall_status": self._get_overall_status(health_score),
            "refresh_interval_seconds": self.refresh_interval_seconds,
            **results
        }
    
    async def _get_system_health(self) -> Dict[str, Any]:
        """Get system health status"""
        try:
            health_data = await enhanced_monitoring.health_check_with_monitoring()
            
            return {
                "status": "healthy" if health_data.get("status") == "healthy" else "unhealthy",
                "database_healthy": health_data.get("database", {}).get("status") == "healthy",
                "redis_healthy": health_data.get("redis", {}).get("status") == "healthy",
                "monitoring_services": health_data.get("monitoring", {}),
                "response_time_ms": health_data.get("response_time_ms", 0),
                "last_check": health_data.get("timestamp")
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def _get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        try:
            # Get performance summary for last hour
            summary = await metrics_collector.get_performance_summary(hours=1)
            real_time = await metrics_collector.get_real_time_metrics()
            
            # Calculate key metrics
            request_metrics = summary.get("metric_types", {}).get("request", {}).get("metrics", {})
            db_metrics = summary.get("metric_types", {}).get("database", {}).get("metrics", {})
            
            # Extract performance indicators
            avg_response_time = 0
            p95_response_time = 0
            if request_metrics:
                for endpoint, stats in request_metrics.items():
                    avg_response_time = max(avg_response_time, stats.get("avg", 0))
                    p95_response_time = max(p95_response_time, stats.get("percentiles", {}).get("p95", 0))
            
            avg_db_time = 0
            if db_metrics:
                for query, stats in db_metrics.items():
                    avg_db_time = max(avg_db_time, stats.get("avg", 0))
            
            return {
                "requests_per_minute": real_time.get("requests_per_minute", 0),
                "avg_response_time_ms": real_time.get("avg_response_time_ms", 0),
                "p95_response_time_ms": p95_response_time,
                "avg_database_time_ms": real_time.get("avg_db_time_ms", 0),
                "total_operations_last_hour": summary.get("total_metrics", 0),
                "performance_insights": summary.get("performance_insights", [])
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def _get_alert_status(self) -> Dict[str, Any]:
        """Get alert system status"""
        try:
            active_alerts = alert_system.get_active_alerts()
            alert_history = alert_system.get_alert_history(hours=24)
            
            # Categorize alerts by severity
            critical_alerts = [a for a in active_alerts if a.severity.value == "critical"]
            warning_alerts = [a for a in active_alerts if a.severity.value == "warning"]
            
            return {
                "active_alerts_count": len(active_alerts),
                "critical_alerts_count": len(critical_alerts),
                "warning_alerts_count": len(warning_alerts),
                "alerts_last_24h": len(alert_history),
                "latest_alerts": [
                    {
                        "severity": alert.severity.value,
                        "message": alert.message,
                        "timestamp": alert.timestamp.isoformat(),
                        "rule_name": alert.rule_name
                    }
                    for alert in active_alerts[:5]
                ],
                "notification_enabled": alert_system.notification_enabled
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def _get_deployment_status(self) -> Dict[str, Any]:
        """Get deployment status"""
        try:
            deployment_info = production_config.get_deployment_info()
            readiness_check = production_config.validate_production_readiness()
            
            return {
                "environment": deployment_info["environment"],
                "version": deployment_info["version"],
                "deployment_timestamp": deployment_info.get("deployment_timestamp"),
                "git_commit": deployment_info.get("git_commit"),
                "production_ready": readiness_check["production_ready"],
                "issues_count": len(readiness_check.get("issues", [])),
                "warnings_count": len(readiness_check.get("warnings", [])),
                "critical_issues": readiness_check.get("issues", []),
                "warnings": readiness_check.get("warnings", [])
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def _get_feature_flags_status(self) -> Dict[str, Any]:
        """Get feature flags status"""
        try:
            all_flags = await feature_flag_manager.get_all_flags()
            
            enabled_count = sum(1 for flag in all_flags.values() if flag.enabled)
            production_flags = {
                name: flag for name, flag in all_flags.items()
                if flag.environment in ["all", "production"]
            }
            
            return {
                "total_flags": len(all_flags),
                "enabled_flags": enabled_count,
                "production_flags": len(production_flags),
                "recent_changes": [
                    {
                        "name": flag.name,
                        "enabled": flag.enabled,
                        "updated_at": flag.updated_at.isoformat() if flag.updated_at else None
                    }
                    for flag in sorted(all_flags.values(), 
                                     key=lambda f: f.updated_at or f.created_at or datetime.min.replace(tzinfo=timezone.utc),
                                     reverse=True)[:5]
                ]
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def _get_backup_status(self) -> Dict[str, Any]:
        """Get backup system status"""
        try:
            backup_verification_result = await backup_verification.verify_daily_backups()
            
            return {
                "backup_system_healthy": backup_verification_result.get("backup_system_healthy", False),
                "automatic_backups": backup_verification_result.get("automatic_backups", {}),
                "point_in_time_recovery": backup_verification_result.get("point_in_time_recovery", {}),
                "last_verification": backup_verification_result.get("timestamp"),
                "retention_policy": backup_verification_result.get("retention_policy", {})
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def _get_service_status(self) -> Dict[str, Any]:
        """Get external service status"""
        try:
            services = production_config.get_deployment_info()["services"]
            
            return {
                "redis": {
                    "configured": services["redis"]["configured"],
                    "provider": services["redis"]["provider"],
                    "fallback_enabled": services["redis"]["fallback_enabled"]
                },
                "email": {
                    "configured": services["email"]["configured"],
                    "provider": services["email"]["provider"],
                    "fallback_enabled": services["email"]["fallback_enabled"]
                },
                "monitoring": services["monitoring"],
                "database": {
                    "provider": "supabase",
                    "configured": True
                }
            }
        except Exception as e:
            return {
                "status": "error", 
                "error": str(e)
            }
    
    def _calculate_health_score(self, results: Dict[str, Any]) -> int:
        """Calculate overall health score (0-100)"""
        try:
            score = 100
            
            # System health (30 points)
            system_health = results.get("system_health", {})
            if system_health.get("status") != "healthy":
                score -= 30
            elif not system_health.get("database_healthy", True):
                score -= 15
            elif not system_health.get("redis_healthy", True):
                score -= 10
            
            # Performance metrics (25 points)
            performance = results.get("performance_metrics", {})
            p95_time = performance.get("p95_response_time_ms", 0)
            if p95_time > 3000:  # > 3 seconds
                score -= 25
            elif p95_time > 2000:  # > 2 seconds
                score -= 15
            elif p95_time > 1000:  # > 1 second
                score -= 10
            
            # Active alerts (20 points)
            alerts = results.get("alert_status", {})
            critical_alerts = alerts.get("critical_alerts_count", 0)
            warning_alerts = alerts.get("warning_alerts_count", 0)
            if critical_alerts > 0:
                score -= 20
            elif warning_alerts > 2:
                score -= 10
            
            # Deployment readiness (15 points)
            deployment = results.get("deployment_status", {})
            if not deployment.get("production_ready", True):
                score -= 15
            elif deployment.get("issues_count", 0) > 0:
                score -= 10
            
            # Backup system (10 points)
            backup = results.get("backup_status", {})
            if not backup.get("backup_system_healthy", True):
                score -= 10
            
            return max(0, min(100, score))
            
        except Exception:
            return 50  # Default to medium health if calculation fails
    
    def _get_overall_status(self, health_score: int) -> str:
        """Get overall status based on health score"""
        if health_score >= 90:
            return "excellent"
        elif health_score >= 75:
            return "good"
        elif health_score >= 60:
            return "fair"
        elif health_score >= 40:
            return "poor"
        else:
            return "critical"
    
    def _is_cache_valid(self) -> bool:
        """Check if dashboard cache is still valid"""
        if not self.last_refresh:
            return False
        
        cache_age = datetime.now(timezone.utc) - self.last_refresh
        return cache_age.total_seconds() < self.refresh_interval_seconds
    
    async def get_alert_summary(self) -> Dict[str, Any]:
        """Get alert summary for quick status check"""
        try:
            active_alerts = alert_system.get_active_alerts()
            
            summary = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "has_critical_alerts": any(a.severity.value == "critical" for a in active_alerts),
                "total_active_alerts": len(active_alerts),
                "latest_critical_alert": None
            }
            
            # Get latest critical alert
            critical_alerts = [a for a in active_alerts if a.severity.value == "critical"]
            if critical_alerts:
                latest = max(critical_alerts, key=lambda a: a.timestamp)
                summary["latest_critical_alert"] = {
                    "message": latest.message,
                    "timestamp": latest.timestamp.isoformat(),
                    "rule_name": latest.rule_name
                }
            
            return summary
            
        except Exception as e:
            logger.error(f"Alert summary failed: {e}")
            return {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "error": str(e)
            }

# Global dashboard instance
monitoring_dashboard = MonitoringDashboard()

# Convenience functions
async def get_dashboard():
    """Get monitoring dashboard data"""
    return await monitoring_dashboard.get_dashboard_data()

async def get_dashboard_fresh():
    """Get fresh monitoring dashboard data (force refresh)"""
    return await monitoring_dashboard.get_dashboard_data(force_refresh=True)

async def get_alert_summary():
    """Get alert summary"""
    return await monitoring_dashboard.get_alert_summary()
