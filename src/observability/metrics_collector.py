"""
Metrics Collection System for WingmanMatch
Real-time performance metrics with percentile calculations and time-series storage
"""

import asyncio
import logging
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, asdict
import json
from src.redis_session import RedisSession

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetric:
    """Performance metric data structure"""
    timestamp: datetime
    metric_type: str  # 'request', 'database', 'cache', 'system'
    name: str
    value: float
    unit: str
    tags: Dict[str, str]
    metadata: Optional[Dict[str, Any]] = None

class MetricsCollector:
    """Real-time metrics collection with percentile calculation"""
    
    def __init__(self):
        self.metrics: List[PerformanceMetric] = []
        self.max_memory_metrics = 5000
        self.collection_enabled = True
        self.redis_cache_ttl = 3600  # 1 hour
        
    async def record_metric(self, 
                          metric_type: str,
                          name: str,
                          value: float,
                          unit: str = "ms",
                          tags: Optional[Dict[str, str]] = None,
                          metadata: Optional[Dict[str, Any]] = None):
        """Record a performance metric"""
        if not self.collection_enabled:
            return
        
        metric = PerformanceMetric(
            timestamp=datetime.now(timezone.utc),
            metric_type=metric_type,
            name=name,
            value=value,
            unit=unit,
            tags=tags or {},
            metadata=metadata
        )
        
        self.metrics.append(metric)
        
        # Store in Redis for persistence
        await self._store_metric_in_redis(metric)
        
        # Clean up old metrics from memory
        if len(self.metrics) > self.max_memory_metrics:
            self.metrics = self.metrics[-self.max_memory_metrics:]
    
    async def _store_metric_in_redis(self, metric: PerformanceMetric):
        """Store metric in Redis for persistence"""
        try:
            redis_client = await RedisSession.get_client()
            if not redis_client:
                return
            
            # Create metric key with timestamp for time-series storage
            metric_key = f"metrics:{metric.metric_type}:{metric.name}:{int(metric.timestamp.timestamp())}"
            
            # Store metric data
            metric_data = {
                "timestamp": metric.timestamp.isoformat(),
                "value": metric.value,
                "unit": metric.unit,
                "tags": metric.tags,
                "metadata": metric.metadata
            }
            
            await redis_client.setex(
                metric_key,
                self.redis_cache_ttl,
                json.dumps(metric_data)
            )
            
            # Add to sorted set for time-based queries
            await redis_client.zadd(
                f"metrics_index:{metric.metric_type}:{metric.name}",
                {metric_key: metric.timestamp.timestamp()}
            )
            
        except Exception as e:
            logger.error(f"Failed to store metric in Redis: {e}")
    
    async def get_metrics(self, 
                         metric_type: Optional[str] = None,
                         name: Optional[str] = None,
                         hours: int = 1,
                         source: str = "memory") -> List[PerformanceMetric]:
        """Get metrics from memory or Redis"""
        if source == "redis":
            return await self._get_metrics_from_redis(metric_type, name, hours)
        
        # Filter from memory
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        filtered_metrics = []
        
        for metric in self.metrics:
            if metric.timestamp < cutoff_time:
                continue
            if metric_type and metric.metric_type != metric_type:
                continue
            if name and metric.name != name:
                continue
            filtered_metrics.append(metric)
        
        return filtered_metrics
    
    async def _get_metrics_from_redis(self, 
                                    metric_type: Optional[str],
                                    name: Optional[str],
                                    hours: int) -> List[PerformanceMetric]:
        """Get metrics from Redis storage"""
        try:
            redis_client = await RedisSession.get_client()
            if not redis_client:
                return []
            
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
            cutoff_timestamp = cutoff_time.timestamp()
            
            metrics = []
            
            if metric_type and name:
                # Get specific metric
                index_key = f"metrics_index:{metric_type}:{name}"
                metric_keys = await redis_client.zrangebyscore(
                    index_key,
                    cutoff_timestamp,
                    "+inf"
                )
                
                for key in metric_keys:
                    metric_data = await redis_client.get(key)
                    if metric_data:
                        data = json.loads(metric_data)
                        metric = PerformanceMetric(
                            timestamp=datetime.fromisoformat(data["timestamp"]),
                            metric_type=metric_type,
                            name=name,
                            value=data["value"],
                            unit=data["unit"],
                            tags=data["tags"],
                            metadata=data["metadata"]
                        )
                        metrics.append(metric)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to get metrics from Redis: {e}")
            return []
    
    def calculate_percentiles(self, 
                            values: List[float],
                            percentiles: List[int] = [50, 95, 99]) -> Dict[str, float]:
        """Calculate percentiles for a list of values"""
        if not values:
            return {f"p{p}": 0.0 for p in percentiles}
        
        sorted_values = sorted(values)
        result = {}
        
        for p in percentiles:
            index = int(len(sorted_values) * (p / 100.0))
            if index >= len(sorted_values):
                index = len(sorted_values) - 1
            result[f"p{p}"] = sorted_values[index]
        
        return result
    
    async def get_performance_summary(self, hours: int = 1) -> Dict[str, Any]:
        """Get comprehensive performance summary"""
        metrics = await self.get_metrics(hours=hours)
        
        summary = {
            "time_window_hours": hours,
            "total_metrics": len(metrics),
            "metric_types": {},
            "performance_insights": {}
        }
        
        # Group metrics by type
        metrics_by_type = {}
        for metric in metrics:
            if metric.metric_type not in metrics_by_type:
                metrics_by_type[metric.metric_type] = []
            metrics_by_type[metric.metric_type].append(metric)
        
        # Analyze each metric type
        for metric_type, type_metrics in metrics_by_type.items():
            type_summary = {
                "count": len(type_metrics),
                "metrics": {}
            }
            
            # Group by metric name
            metrics_by_name = {}
            for metric in type_metrics:
                if metric.name not in metrics_by_name:
                    metrics_by_name[metric.name] = []
                metrics_by_name[metric.name].append(metric.value)
            
            # Calculate statistics for each metric
            for name, values in metrics_by_name.items():
                percentiles = self.calculate_percentiles(values)
                type_summary["metrics"][name] = {
                    "count": len(values),
                    "min": min(values),
                    "max": max(values),
                    "avg": sum(values) / len(values),
                    "percentiles": percentiles,
                    "unit": type_metrics[0].unit
                }
            
            summary["metric_types"][metric_type] = type_summary
        
        # Generate performance insights
        await self._generate_performance_insights(summary)
        
        return summary
    
    async def _generate_performance_insights(self, summary: Dict[str, Any]):
        """Generate performance insights and alerts"""
        insights = []
        
        # Check request performance
        if "request" in summary["metric_types"]:
            request_metrics = summary["metric_types"]["request"]["metrics"]
            
            for endpoint, stats in request_metrics.items():
                p95 = stats["percentiles"]["p95"]
                avg = stats["avg"]
                
                if p95 > 2000:  # > 2 seconds
                    insights.append({
                        "type": "critical",
                        "metric": f"request.{endpoint}",
                        "message": f"High P95 latency: {p95:.0f}ms",
                        "threshold": "2000ms",
                        "suggestion": "Consider optimizing database queries or adding caching"
                    })
                elif p95 > 1000:  # > 1 second
                    insights.append({
                        "type": "warning",
                        "metric": f"request.{endpoint}",
                        "message": f"Moderate P95 latency: {p95:.0f}ms",
                        "threshold": "1000ms",
                        "suggestion": "Monitor for performance degradation"
                    })
        
        # Check database performance
        if "database" in summary["metric_types"]:
            db_metrics = summary["metric_types"]["database"]["metrics"]
            
            for query_type, stats in db_metrics.items():
                avg = stats["avg"]
                
                if avg > 500:  # > 500ms average
                    insights.append({
                        "type": "warning",
                        "metric": f"database.{query_type}",
                        "message": f"Slow database queries: {avg:.0f}ms average",
                        "threshold": "500ms",
                        "suggestion": "Review query optimization and indexes"
                    })
        
        summary["performance_insights"] = insights
    
    async def get_real_time_metrics(self) -> Dict[str, Any]:
        """Get current real-time performance metrics"""
        now = datetime.now(timezone.utc)
        last_minute = now - timedelta(minutes=1)
        
        recent_metrics = [m for m in self.metrics if m.timestamp > last_minute]
        
        if not recent_metrics:
            return {"status": "no_recent_data"}
        
        # Calculate current performance
        request_times = [m.value for m in recent_metrics if m.metric_type == "request"]
        db_times = [m.value for m in recent_metrics if m.metric_type == "database"]
        
        return {
            "timestamp": now.isoformat(),
            "requests_per_minute": len([m for m in recent_metrics if m.metric_type == "request"]),
            "avg_response_time_ms": sum(request_times) / len(request_times) if request_times else 0,
            "avg_db_time_ms": sum(db_times) / len(db_times) if db_times else 0,
            "total_operations": len(recent_metrics)
        }
    
    def enable_collection(self):
        """Enable metrics collection"""
        self.collection_enabled = True
        logger.info("Metrics collection enabled")
    
    def disable_collection(self):
        """Disable metrics collection"""
        self.collection_enabled = False
        logger.info("Metrics collection disabled")
    
    async def cleanup_old_metrics(self, hours: int = 24):
        """Clean up old metrics from Redis"""
        try:
            redis_client = await RedisSession.get_client()
            if not redis_client:
                return
            
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
            cutoff_timestamp = cutoff_time.timestamp()
            
            # Get all metric index keys
            index_keys = await redis_client.keys("metrics_index:*")
            
            for index_key in index_keys:
                # Remove old entries from sorted set
                await redis_client.zremrangebyscore(index_key, "-inf", cutoff_timestamp)
                
                # Clean up empty sets
                count = await redis_client.zcard(index_key)
                if count == 0:
                    await redis_client.delete(index_key)
            
            logger.info(f"Cleaned up metrics older than {hours} hours")
            
        except Exception as e:
            logger.error(f"Failed to cleanup old metrics: {e}")

# Global metrics collector instance
metrics_collector = MetricsCollector()

# Convenience functions
async def record_request_metric(endpoint: str, duration_ms: float, status_code: int):
    """Record request performance metric"""
    await metrics_collector.record_metric(
        metric_type="request",
        name=endpoint,
        value=duration_ms,
        unit="ms",
        tags={"status_code": str(status_code)}
    )

async def record_database_metric(query_type: str, duration_ms: float, success: bool):
    """Record database performance metric"""
    await metrics_collector.record_metric(
        metric_type="database",
        name=query_type,
        value=duration_ms,
        unit="ms",
        tags={"success": str(success)}
    )

async def record_cache_metric(operation: str, hit: bool, duration_ms: float = 0):
    """Record cache performance metric"""
    await metrics_collector.record_metric(
        metric_type="cache",
        name=operation,
        value=duration_ms,
        unit="ms",
        tags={"hit": str(hit)}
    )

async def get_performance_summary(hours: int = 1):
    """Get performance summary"""
    return await metrics_collector.get_performance_summary(hours)

async def get_real_time_metrics():
    """Get real-time metrics"""
    return await metrics_collector.get_real_time_metrics()
