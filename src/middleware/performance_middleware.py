"""
Performance Middleware for WingmanMatch
Automatic request timing and performance metric collection
"""

import time
import logging
from typing import Callable, Dict, Any, List
from datetime import datetime, timezone, timedelta
from fastapi import Request, Response
from fastapi.responses import JSONResponse
import json

logger = logging.getLogger(__name__)

class PerformanceMiddleware:
    """FastAPI middleware for automatic performance tracking"""
    
    def __init__(self, app):
        self.app = app
        self.request_metrics: List[Dict[str, Any]] = []
        self.max_metrics_retention = 1000
        
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        request = Request(scope, receive)
        start_time = time.time()
        
        # Track request start
        request_data = {
            "method": request.method,
            "path": request.url.path,
            "start_time": start_time,
            "timestamp": datetime.now(timezone.utc),
            "client_ip": self._get_client_ip(request),
            "user_agent": request.headers.get("user-agent", ""),
            "database_queries": 0,
            "cache_hits": 0,
            "cache_misses": 0
        }
        
        # Add request data to request state for other components to access
        request.state.perf_data = request_data
        
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                # Calculate response time
                end_time = time.time()
                duration = end_time - start_time
                
                # Extract response info
                status_code = message["status"]
                headers = dict(message.get("headers", []))
                
                # Update request data
                request_data.update({
                    "duration_ms": round(duration * 1000, 2),
                    "status_code": status_code,
                    "response_size": self._get_response_size(headers),
                    "cache_hit_rate": self._calculate_cache_hit_rate(request_data)
                })
                
                # Record metric
                self._record_metric(request_data)
                
                # Log slow requests
                if duration > 2.0:  # > 2 seconds
                    logger.warning(f"Slow request: {request.method} {request.url.path} took {duration:.2f}s")
                elif duration > 1.0:  # > 1 second
                    logger.info(f"Moderate request: {request.method} {request.url.path} took {duration:.2f}s")
            
            await send(message)
        
        await self.app(scope, receive, send_wrapper)
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request"""
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"
    
    def _get_response_size(self, headers: Dict) -> int:
        """Extract response size from headers"""
        content_length = headers.get(b"content-length")
        if content_length:
            return int(content_length.decode())
        return 0
    
    def _calculate_cache_hit_rate(self, request_data: Dict) -> float:
        """Calculate cache hit rate for request"""
        total_cache_ops = request_data["cache_hits"] + request_data["cache_misses"]
        if total_cache_ops == 0:
            return 0.0
        return round((request_data["cache_hits"] / total_cache_ops) * 100, 2)
    
    def _record_metric(self, request_data: Dict[str, Any]):
        """Record request metric with cleanup"""
        self.request_metrics.append(request_data)
        
        # Keep only recent metrics
        if len(self.request_metrics) > self.max_metrics_retention:
            self.request_metrics = self.request_metrics[-self.max_metrics_retention:]
    
    def get_metrics_summary(self, hours: int = 1) -> Dict[str, Any]:
        """Get performance metrics summary for time window"""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        recent_metrics = [m for m in self.request_metrics if m["timestamp"] > cutoff_time]
        
        if not recent_metrics:
            return {"error": "No metrics available for time window"}
        
        # Calculate response time percentiles
        durations = [m["duration_ms"] for m in recent_metrics]
        durations.sort()
        
        p50 = durations[len(durations) // 2] if durations else 0
        p95 = durations[int(len(durations) * 0.95)] if durations else 0
        p99 = durations[int(len(durations) * 0.99)] if durations else 0
        
        # Status code breakdown
        status_codes = {}
        for metric in recent_metrics:
            status = metric["status_code"]
            status_codes[status] = status_codes.get(status, 0) + 1
        
        # Endpoint performance
        endpoints = {}
        for metric in recent_metrics:
            path = metric["path"]
            if path not in endpoints:
                endpoints[path] = {
                    "count": 0,
                    "total_time": 0,
                    "min_time": float('inf'),
                    "max_time": 0,
                    "error_count": 0
                }
            
            endpoints[path]["count"] += 1
            endpoints[path]["total_time"] += metric["duration_ms"]
            endpoints[path]["min_time"] = min(endpoints[path]["min_time"], metric["duration_ms"])
            endpoints[path]["max_time"] = max(endpoints[path]["max_time"], metric["duration_ms"])
            
            if metric["status_code"] >= 400:
                endpoints[path]["error_count"] += 1
        
        # Calculate averages
        for path in endpoints:
            endpoints[path]["avg_time"] = round(endpoints[path]["total_time"] / endpoints[path]["count"], 2)
            endpoints[path]["error_rate"] = round((endpoints[path]["error_count"] / endpoints[path]["count"]) * 100, 2)
        
        # Overall statistics
        total_requests = len(recent_metrics)
        error_requests = len([m for m in recent_metrics if m["status_code"] >= 400])
        avg_response_time = sum(durations) / len(durations) if durations else 0
        
        return {
            "time_window_hours": hours,
            "total_requests": total_requests,
            "error_rate_percent": round((error_requests / total_requests) * 100, 2) if total_requests > 0 else 0,
            "response_time_percentiles_ms": {
                "p50": p50,
                "p95": p95,
                "p99": p99,
                "avg": round(avg_response_time, 2)
            },
            "status_code_distribution": status_codes,
            "endpoint_performance": endpoints,
            "throughput_rps": round(total_requests / hours, 2) if hours > 0 else 0
        }
    
    def get_slow_requests(self, threshold_ms: float = 1000, limit: int = 10) -> List[Dict[str, Any]]:
        """Get slowest requests above threshold"""
        slow_requests = [
            m for m in self.request_metrics 
            if m["duration_ms"] > threshold_ms
        ]
        
        # Sort by duration (slowest first)
        slow_requests.sort(key=lambda x: x["duration_ms"], reverse=True)
        
        return slow_requests[:limit]
    
    def get_error_requests(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent error requests"""
        error_requests = [
            m for m in self.request_metrics 
            if m["status_code"] >= 400
        ]
        
        # Sort by timestamp (newest first)
        error_requests.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return error_requests[:limit]

# Global middleware instance
performance_middleware = None

def get_performance_middleware():
    """Get global performance middleware instance"""
    global performance_middleware
    return performance_middleware

def track_database_query(request: Request, duration_ms: float):
    """Track database query performance for request"""
    if hasattr(request.state, 'perf_data'):
        request.state.perf_data["database_queries"] += 1

def track_cache_hit(request: Request):
    """Track cache hit for request"""
    if hasattr(request.state, 'perf_data'):
        request.state.perf_data["cache_hits"] += 1

def track_cache_miss(request: Request):
    """Track cache miss for request"""
    if hasattr(request.state, 'perf_data'):
        request.state.perf_data["cache_misses"] += 1
