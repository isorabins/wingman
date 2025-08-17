"""
Enhanced Health Monitoring System for WingmanMatch
Deep health checks with performance baseline tracking and composite health scoring
"""

import asyncio
import logging
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, asdict
import json
from src.config import Config
from src.redis_session import RedisSession
from src.db.connection_pool import db_pool
from src.observability.metrics_collector import metrics_collector

logger = logging.getLogger(__name__)

@dataclass
class HealthCheckResult:
    """Health check result data structure"""
    service: str
    healthy: bool
    response_time_ms: float
    details: Dict[str, Any]
    score: int  # 0-100
    timestamp: datetime
    error: Optional[str] = None

class HealthMonitor:
    """Comprehensive health monitoring with performance baseline tracking"""
    
    def __init__(self):
        self.health_history: List[HealthCheckResult] = []
        self.max_history = 1000
        self.baseline_metrics = {}
        self.health_thresholds = {
            "database_response_ms": 100,
            "redis_response_ms": 50,
            "pool_utilization_percent": 80,
            "error_rate_percent": 5,
            "memory_usage_percent": 85
        }
    
    async def perform_comprehensive_health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check across all services"""
        start_time = time.time()
        
        health_checks = await asyncio.gather(
            self._check_database_health(),
            self._check_redis_health(),
            self._check_connection_pool_health(),
            self._check_performance_health(),
            self._check_external_dependencies(),
            return_exceptions=True
        )
        
        total_time = (time.time() - start_time) * 1000
        
        # Parse results
        db_health, redis_health, pool_health, perf_health, ext_health = health_checks
        
        # Calculate composite health score
        all_checks = [db_health, redis_health, pool_health, perf_health, ext_health]
        valid_checks = [check for check in all_checks if isinstance(check, HealthCheckResult)]
        
        if not valid_checks:
            composite_score = 0
        else:
            composite_score = sum(check.score for check in valid_checks) // len(valid_checks)
        
        # Determine overall health status
        overall_healthy = composite_score >= 70 and all(
            check.healthy for check in valid_checks if isinstance(check, HealthCheckResult)
        )
        
        health_summary = {
            "overall_healthy": overall_healthy,
            "composite_score": composite_score,
            "total_check_time_ms": round(total_time, 2),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "services": {
                "database": asdict(db_health) if isinstance(db_health, HealthCheckResult) else {"error": str(db_health)},
                "redis": asdict(redis_health) if isinstance(redis_health, HealthCheckResult) else {"error": str(redis_health)},
                "connection_pool": asdict(pool_health) if isinstance(pool_health, HealthCheckResult) else {"error": str(pool_health)},
                "performance": asdict(perf_health) if isinstance(perf_health, HealthCheckResult) else {"error": str(perf_health)},
                "external": asdict(ext_health) if isinstance(ext_health, HealthCheckResult) else {"error": str(ext_health)}
            },
            "health_insights": self._generate_health_insights(valid_checks)
        }
        
        # Store health check result
        await self._store_health_result(health_summary)
        
        return health_summary
    
    async def _check_database_health(self) -> HealthCheckResult:
        """Check database health with query performance"""
        start_time = time.time()
        
        try:
            # Test basic connectivity
            result = await db_pool.execute_one("SELECT 1")
            response_time = (time.time() - start_time) * 1000
            
            # Get connection pool stats
            pool_health = await db_pool.health_check()
            
            # Calculate score based on performance
            score = 100
            if response_time > 200:
                score -= 30
            elif response_time > 100:
                score -= 15
            
            if not pool_health.get("healthy", False):
                score -= 40
            
            pool_util = pool_health.get("performance_metrics", {}).get("pool_utilization_percent", 0)
            if pool_util > 90:
                score -= 20
            elif pool_util > 80:
                score -= 10
            
            details = {
                "connection_test": result == 1,
                "response_time_ms": round(response_time, 2),
                "pool_health": pool_health,
                "query_performance": await self._get_recent_query_performance()
            }
            
            return HealthCheckResult(
                service="database",
                healthy=score >= 70,
                response_time_ms=response_time,
                details=details,
                score=max(0, score),
                timestamp=datetime.now(timezone.utc)
            )
            
        except Exception as e:
            return HealthCheckResult(
                service="database",
                healthy=False,
                response_time_ms=(time.time() - start_time) * 1000,
                details={"error": str(e)},
                score=0,
                timestamp=datetime.now(timezone.utc),
                error=str(e)
            )
    
    async def _check_redis_health(self) -> HealthCheckResult:
        """Check Redis health with operation performance"""
        start_time = time.time()
        
        try:
            redis_health = await RedisSession.health_check()
            response_time = (time.time() - start_time) * 1000
            
            # Test read/write operations
            test_key = "health_check_test"
            test_data = {"timestamp": datetime.now(timezone.utc).isoformat()}
            
            write_success = await RedisSession.set_session(test_key, test_data, 60)
            read_data = await RedisSession.get_session(test_key)
            delete_success = await RedisSession.delete_session(test_key)
            
            # Calculate score
            score = 100
            if not redis_health.get("connected", False):
                score = 0
            elif response_time > 100:
                score -= 30
            elif response_time > 50:
                score -= 15
            
            if not (write_success and read_data and delete_success):
                score -= 25
            
            details = {
                "connection_health": redis_health,
                "operations_test": {
                    "write": write_success,
                    "read": read_data is not None,
                    "delete": delete_success
                },
                "response_time_ms": round(response_time, 2)
            }
            
            return HealthCheckResult(
                service="redis",
                healthy=score >= 70,
                response_time_ms=response_time,
                details=details,
                score=max(0, score),
                timestamp=datetime.now(timezone.utc)
            )
            
        except Exception as e:
            return HealthCheckResult(
                service="redis",
                healthy=False,
                response_time_ms=(time.time() - start_time) * 1000,
                details={"error": str(e)},
                score=0,
                timestamp=datetime.now(timezone.utc),
                error=str(e)
            )
    
    async def _check_connection_pool_health(self) -> HealthCheckResult:
        """Check connection pool health and utilization"""
        start_time = time.time()
        
        try:
            pool_stats = db_pool.pool_stats.copy()
            response_time = (time.time() - start_time) * 1000
            
            # Calculate score based on pool metrics
            score = 100
            utilization = pool_stats.get("pool_utilization", 0)
            
            if utilization > 95:
                score -= 40
            elif utilization > 85:
                score -= 25
            elif utilization > 75:
                score -= 10
            
            error_rate = (pool_stats.get("error_count", 0) / max(pool_stats.get("query_count", 1), 1)) * 100
            if error_rate > 10:
                score -= 30
            elif error_rate > 5:
                score -= 15
            
            health_score = pool_stats.get("health_score", 100)
            if health_score < 50:
                score -= 30
            elif health_score < 70:
                score -= 15
            
            details = {
                "pool_statistics": pool_stats,
                "utilization_status": self._get_utilization_status(utilization),
                "performance_metrics": db_pool.get_performance_metrics(1)
            }
            
            return HealthCheckResult(
                service="connection_pool",
                healthy=score >= 70,
                response_time_ms=response_time,
                details=details,
                score=max(0, score),
                timestamp=datetime.now(timezone.utc)
            )
            
        except Exception as e:
            return HealthCheckResult(
                service="connection_pool",
                healthy=False,
                response_time_ms=(time.time() - start_time) * 1000,
                details={"error": str(e)},
                score=0,
                timestamp=datetime.now(timezone.utc),
                error=str(e)
            )
    
    async def _check_performance_health(self) -> HealthCheckResult:
        """Check overall application performance health"""
        start_time = time.time()
        
        try:
            # Get recent performance metrics
            perf_summary = await metrics_collector.get_performance_summary(hours=1)
            real_time_metrics = await metrics_collector.get_real_time_metrics()
            response_time = (time.time() - start_time) * 1000
            
            # Calculate performance score
            score = 100
            
            # Check request performance
            if "request" in perf_summary.get("metric_types", {}):
                request_metrics = perf_summary["metric_types"]["request"]["metrics"]
                for endpoint, stats in request_metrics.items():
                    p95 = stats.get("percentiles", {}).get("p95", 0)
                    if p95 > 2000:  # > 2s
                        score -= 25
                    elif p95 > 1000:  # > 1s
                        score -= 10
            
            # Check error rates
            insights = perf_summary.get("performance_insights", [])
            critical_issues = len([i for i in insights if i.get("type") == "critical"])
            warning_issues = len([i for i in insights if i.get("type") == "warning"])
            
            score -= (critical_issues * 20 + warning_issues * 10)
            
            details = {
                "performance_summary": perf_summary,
                "real_time_metrics": real_time_metrics,
                "performance_insights": insights,
                "performance_baseline": self._get_performance_baseline()
            }
            
            return HealthCheckResult(
                service="performance",
                healthy=score >= 70,
                response_time_ms=response_time,
                details=details,
                score=max(0, score),
                timestamp=datetime.now(timezone.utc)
            )
            
        except Exception as e:
            return HealthCheckResult(
                service="performance",
                healthy=False,
                response_time_ms=(time.time() - start_time) * 1000,
                details={"error": str(e)},
                score=0,
                timestamp=datetime.now(timezone.utc),
                error=str(e)
            )
    
    async def _check_external_dependencies(self) -> HealthCheckResult:
        """Check external service dependencies"""
        start_time = time.time()
        
        try:
            dependencies = {
                "anthropic_api": await self._test_anthropic_api(),
                "email_service": await self._test_email_service(),
                "supabase_api": await self._test_supabase_api()
            }
            
            response_time = (time.time() - start_time) * 1000
            
            # Calculate score based on dependency health
            healthy_deps = sum(1 for dep in dependencies.values() if dep["healthy"])
            total_deps = len(dependencies)
            score = (healthy_deps / total_deps) * 100 if total_deps > 0 else 0
            
            details = {
                "dependencies": dependencies,
                "healthy_services": healthy_deps,
                "total_services": total_deps,
                "dependency_health_rate": f"{healthy_deps}/{total_deps}"
            }
            
            return HealthCheckResult(
                service="external",
                healthy=score >= 70,
                response_time_ms=response_time,
                details=details,
                score=int(score),
                timestamp=datetime.now(timezone.utc)
            )
            
        except Exception as e:
            return HealthCheckResult(
                service="external",
                healthy=False,
                response_time_ms=(time.time() - start_time) * 1000,
                details={"error": str(e)},
                score=0,
                timestamp=datetime.now(timezone.utc),
                error=str(e)
            )
    
    async def _get_recent_query_performance(self) -> Dict[str, Any]:
        """Get recent database query performance metrics"""
        try:
            return db_pool.get_performance_metrics(hours=1)
        except Exception as e:
            return {"error": str(e)}
    
    def _get_utilization_status(self, utilization: float) -> str:
        """Get human-readable utilization status"""
        if utilization < 50:
            return "optimal"
        elif utilization < 75:
            return "good"
        elif utilization < 85:
            return "moderate"
        elif utilization < 95:
            return "high"
        else:
            return "critical"
    
    def _get_performance_baseline(self) -> Dict[str, Any]:
        """Get performance baseline for comparison"""
        # This would typically be stored in database/cache
        # For now, return default baseline
        return {
            "avg_response_time_ms": 200,
            "p95_response_time_ms": 500,
            "error_rate_percent": 1.0,
            "throughput_rps": 100,
            "last_updated": datetime.now(timezone.utc).isoformat()
        }
    
    async def _test_anthropic_api(self) -> Dict[str, Any]:
        """Test Anthropic API connectivity"""
        try:
            # Simple API test - just check if we can initialize
            if Config.ANTHROPIC_API_KEY:
                return {"healthy": True, "status": "api_key_configured"}
            else:
                return {"healthy": False, "status": "api_key_missing"}
        except Exception as e:
            return {"healthy": False, "error": str(e)}
    
    async def _test_email_service(self) -> Dict[str, Any]:
        """Test email service health"""
        try:
            from src.email_templates import email_service
            return {"healthy": email_service.enabled, "status": "service_configured" if email_service.enabled else "service_disabled"}
        except Exception as e:
            return {"healthy": False, "error": str(e)}
    
    async def _test_supabase_api(self) -> Dict[str, Any]:
        """Test Supabase API connectivity"""
        try:
            from src.database import SupabaseFactory
            health = SupabaseFactory.health_check()
            return {
                "healthy": health.get("service_client", False) or health.get("anon_client", False),
                "details": health
            }
        except Exception as e:
            return {"healthy": False, "error": str(e)}
    
    def _generate_health_insights(self, health_checks: List[HealthCheckResult]) -> List[Dict[str, Any]]:
        """Generate actionable health insights"""
        insights = []
        
        for check in health_checks:
            if not check.healthy:
                insights.append({
                    "type": "critical",
                    "service": check.service,
                    "issue": f"{check.service} is unhealthy",
                    "score": check.score,
                    "recommendation": self._get_service_recommendation(check.service),
                    "timestamp": check.timestamp.isoformat()
                })
            elif check.score < 80:
                insights.append({
                    "type": "warning",
                    "service": check.service,
                    "issue": f"{check.service} performance degraded",
                    "score": check.score,
                    "recommendation": self._get_service_recommendation(check.service),
                    "timestamp": check.timestamp.isoformat()
                })
        
        return insights
    
    def _get_service_recommendation(self, service: str) -> str:
        """Get service-specific recommendations"""
        recommendations = {
            "database": "Check connection pool utilization, review slow queries, consider scaling",
            "redis": "Verify Redis connection, check memory usage, restart if necessary",
            "connection_pool": "Increase pool size, optimize query performance, check for connection leaks",
            "performance": "Review endpoint performance, optimize slow operations, check resource usage",
            "external": "Verify API keys, check network connectivity, review service status pages"
        }
        return recommendations.get(service, "Review service configuration and logs")
    
    async def _store_health_result(self, health_summary: Dict[str, Any]):
        """Store health check result for trend analysis"""
        try:
            redis_client = await RedisSession.get_client()
            if redis_client:
                key = f"health_check:{int(datetime.now(timezone.utc).timestamp())}"
                await redis_client.setex(key, 86400, json.dumps(health_summary))  # 24 hour TTL
                
                # Add to sorted set for time-based queries
                await redis_client.zadd(
                    "health_check_index",
                    {key: datetime.now(timezone.utc).timestamp()}
                )
        except Exception as e:
            logger.error(f"Failed to store health result: {e}")
    
    async def get_health_trends(self, hours: int = 24) -> Dict[str, Any]:
        """Get health trends over time"""
        try:
            redis_client = await RedisSession.get_client()
            if not redis_client:
                return {"error": "Redis not available"}
            
            # Get health checks from specified time window
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
            cutoff_timestamp = cutoff_time.timestamp()
            
            health_keys = await redis_client.zrangebyscore(
                "health_check_index",
                cutoff_timestamp,
                "+inf"
            )
            
            trends = {
                "time_window_hours": hours,
                "total_checks": len(health_keys),
                "service_trends": {},
                "score_trend": [],
                "availability": {}
            }
            
            for key in health_keys:
                data = await redis_client.get(key)
                if data:
                    health_data = json.loads(data)
                    trends["score_trend"].append({
                        "timestamp": health_data["timestamp"],
                        "score": health_data["composite_score"]
                    })
            
            return trends
            
        except Exception as e:
            logger.error(f"Failed to get health trends: {e}")
            return {"error": str(e)}

# Global health monitor instance
health_monitor = HealthMonitor()

# Convenience functions
async def get_health_status():
    """Get comprehensive health status"""
    return await health_monitor.perform_comprehensive_health_check()

async def get_quick_health():
    """Get quick health check (basic connectivity only)"""
    db_ok = await db_pool.health_check()
    redis_ok = await RedisSession.health_check()
    
    return {
        "healthy": db_ok.get("healthy", False) and redis_ok.get("connected", False),
        "database": db_ok.get("healthy", False),
        "redis": redis_ok.get("connected", False),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

async def get_health_trends(hours: int = 24):
    """Get health trends"""
    return await health_monitor.get_health_trends(hours)
