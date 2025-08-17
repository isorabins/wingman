"""
Enhanced Database Connection Pool for WingmanMatch
Provides PostgreSQL connection pooling with health monitoring and performance optimization
"""

import asyncio
import logging
import time
from typing import Optional, Dict, Any, List
from contextlib import asynccontextmanager
from datetime import datetime, timezone, timedelta
import asyncpg
from src.config import Config

logger = logging.getLogger(__name__)

class DatabaseConnectionPool:
    """Enhanced PostgreSQL connection pool with health monitoring and performance tracking"""
    
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
        self.pool_stats = {
            "total_connections": 0,
            "available_connections": 0,
            "pool_utilization": 0.0,
            "connection_wait_time": 0.0,
            "query_count": 0,
            "error_count": 0,
            "health_score": 100,
            "last_health_check": None
        }
        self.query_metrics = []
        self.max_metrics_retention = 1000
        
    async def initialize(self) -> bool:
        """Initialize connection pool with optimized settings"""
        if not Config.SUPABASE_URL:
            logger.error("SUPABASE_URL not configured")
            return False
            
        try:
            # Parse Supabase URL to get PostgreSQL connection string
            supabase_url = Config.SUPABASE_URL
            # Convert Supabase URL to PostgreSQL format
            if "supabase.co" in supabase_url:
                project_id = supabase_url.split("//")[1].split(".")[0]
                db_url = f"postgresql://postgres:{Config.SUPABASE_SERVICE_KEY.split('.')[1] if '.' in Config.SUPABASE_SERVICE_KEY else 'password'}@db.{project_id}.supabase.co:5432/postgres"
            else:
                # Use the URL as-is for local development
                db_url = supabase_url.replace("https://", "postgresql://postgres:postgres@localhost:54322/")
            
            # Initialize connection pool with optimized settings
            self.pool = await asyncpg.create_pool(
                db_url,
                min_size=int(Config.get_wingman_settings().get("min_pool_size", 5)),
                max_size=int(Config.get_wingman_settings().get("max_pool_size", 20)),
                max_queries=50000,
                max_inactive_connection_lifetime=3600,  # 1 hour
                timeout=30,
                command_timeout=60,
                server_settings={
                    'jit': 'off',  # Disable JIT for predictable performance
                    'application_name': 'wingman_pool'
                }
            )
            
            # Test pool with simple query
            async with self.pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            
            self.pool_stats["total_connections"] = self.pool.get_size()
            logger.info(f"Database connection pool initialized: {self.pool.get_size()} connections")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize connection pool: {e}")
            self.pool = None
            return False
    
    @asynccontextmanager
    async def get_connection(self):
        """Get connection with performance tracking"""
        if not self.pool:
            raise RuntimeError("Connection pool not initialized")
        
        start_time = time.time()
        connection = None
        
        try:
            # Acquire connection with timeout
            connection = await asyncio.wait_for(
                self.pool.acquire(), 
                timeout=10.0
            )
            
            wait_time = time.time() - start_time
            self.pool_stats["connection_wait_time"] = wait_time
            self.pool_stats["available_connections"] = self.pool.get_idle_size()
            self.pool_stats["pool_utilization"] = (
                (self.pool_stats["total_connections"] - self.pool_stats["available_connections"]) /
                self.pool_stats["total_connections"] * 100
            )
            
            yield connection
            
        except asyncio.TimeoutError:
            logger.error("Connection pool timeout - consider increasing pool size")
            self.pool_stats["error_count"] += 1
            raise
        except Exception as e:
            logger.error(f"Connection pool error: {e}")
            self.pool_stats["error_count"] += 1
            raise
        finally:
            if connection:
                await self.pool.release(connection)
    
    async def execute_query(self, query: str, *args) -> Any:
        """Execute query with performance tracking"""
        start_time = time.time()
        
        try:
            async with self.get_connection() as conn:
                result = await conn.fetch(query, *args)
                
            query_time = time.time() - start_time
            self._record_query_metric(query, query_time, True)
            self.pool_stats["query_count"] += 1
            
            return result
            
        except Exception as e:
            query_time = time.time() - start_time
            self._record_query_metric(query, query_time, False)
            self.pool_stats["error_count"] += 1
            logger.error(f"Query execution failed: {e}")
            raise
    
    async def execute_one(self, query: str, *args) -> Any:
        """Execute query expecting single result"""
        start_time = time.time()
        
        try:
            async with self.get_connection() as conn:
                result = await conn.fetchval(query, *args)
                
            query_time = time.time() - start_time
            self._record_query_metric(query, query_time, True)
            self.pool_stats["query_count"] += 1
            
            return result
            
        except Exception as e:
            query_time = time.time() - start_time
            self._record_query_metric(query, query_time, False)
            self.pool_stats["error_count"] += 1
            logger.error(f"Query execution failed: {e}")
            raise
    
    def _record_query_metric(self, query: str, execution_time: float, success: bool):
        """Record query performance metrics"""
        metric = {
            "timestamp": datetime.now(timezone.utc),
            "query_type": self._get_query_type(query),
            "execution_time": execution_time,
            "success": success
        }
        
        self.query_metrics.append(metric)
        
        # Keep only recent metrics
        if len(self.query_metrics) > self.max_metrics_retention:
            self.query_metrics = self.query_metrics[-self.max_metrics_retention:]
    
    def _get_query_type(self, query: str) -> str:
        """Extract query type for metrics"""
        query_lower = query.strip().lower()
        if query_lower.startswith('select'):
            return 'SELECT'
        elif query_lower.startswith('insert'):
            return 'INSERT'
        elif query_lower.startswith('update'):
            return 'UPDATE'
        elif query_lower.startswith('delete'):
            return 'DELETE'
        else:
            return 'OTHER'
    
    async def health_check(self) -> Dict[str, Any]:
        """Comprehensive pool health check with performance metrics"""
        health = {
            "healthy": False,
            "pool_initialized": bool(self.pool),
            "connection_test": False,
            "performance_metrics": {},
            "pool_stats": self.pool_stats.copy(),
            "error": None
        }
        
        if not self.pool:
            health["error"] = "Connection pool not initialized"
            return health
        
        try:
            # Test connection with simple query
            start_time = time.time()
            async with self.get_connection() as conn:
                await conn.fetchval("SELECT 1")
            connection_time = time.time() - start_time
            
            health["connection_test"] = True
            health["performance_metrics"] = {
                "connection_time_ms": round(connection_time * 1000, 2),
                "pool_size": self.pool.get_size(),
                "idle_connections": self.pool.get_idle_size(),
                "pool_utilization_percent": round(self.pool_stats["pool_utilization"], 2)
            }
            
            # Calculate health score based on performance
            health_score = 100
            if connection_time > 1.0:  # > 1s connection time
                health_score -= 30
            elif connection_time > 0.5:  # > 500ms connection time
                health_score -= 15
            
            if self.pool_stats["pool_utilization"] > 90:  # > 90% utilization
                health_score -= 20
            elif self.pool_stats["pool_utilization"] > 80:  # > 80% utilization
                health_score -= 10
            
            error_rate = (self.pool_stats["error_count"] / max(self.pool_stats["query_count"], 1)) * 100
            if error_rate > 5:  # > 5% error rate
                health_score -= 25
            elif error_rate > 2:  # > 2% error rate
                health_score -= 10
            
            self.pool_stats["health_score"] = max(0, health_score)
            self.pool_stats["last_health_check"] = datetime.now(timezone.utc)
            
            health["healthy"] = health_score >= 70
            health["pool_stats"]["health_score"] = health_score
            
        except Exception as e:
            health["error"] = str(e)
            self.pool_stats["health_score"] = 0
            logger.error(f"Pool health check failed: {e}")
        
        return health
    
    def get_performance_metrics(self, hours: int = 1) -> Dict[str, Any]:
        """Get performance metrics for specified time window"""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        recent_metrics = [m for m in self.query_metrics if m["timestamp"] > cutoff_time]
        
        if not recent_metrics:
            return {"error": "No metrics available for time window"}
        
        # Calculate percentiles
        execution_times = [m["execution_time"] for m in recent_metrics if m["success"]]
        execution_times.sort()
        
        if execution_times:
            p50 = execution_times[len(execution_times) // 2]
            p95 = execution_times[int(len(execution_times) * 0.95)]
            p99 = execution_times[int(len(execution_times) * 0.99)]
        else:
            p50 = p95 = p99 = 0
        
        # Query type breakdown
        query_types = {}
        for metric in recent_metrics:
            qtype = metric["query_type"]
            if qtype not in query_types:
                query_types[qtype] = {"count": 0, "avg_time": 0, "total_time": 0}
            query_types[qtype]["count"] += 1
            query_types[qtype]["total_time"] += metric["execution_time"]
        
        for qtype in query_types:
            query_types[qtype]["avg_time"] = query_types[qtype]["total_time"] / query_types[qtype]["count"]
        
        return {
            "time_window_hours": hours,
            "total_queries": len(recent_metrics),
            "successful_queries": len([m for m in recent_metrics if m["success"]]),
            "error_rate_percent": round((len([m for m in recent_metrics if not m["success"]]) / len(recent_metrics)) * 100, 2),
            "latency_percentiles_ms": {
                "p50": round(p50 * 1000, 2),
                "p95": round(p95 * 1000, 2),
                "p99": round(p99 * 1000, 2)
            },
            "query_types": query_types,
            "pool_stats": self.pool_stats.copy()
        }
    
    async def close(self):
        """Close connection pool"""
        if self.pool:
            await self.pool.close()
            self.pool = None
            logger.info("Database connection pool closed")

# Global pool instance
db_pool = DatabaseConnectionPool()

# Convenience functions
async def get_db_connection():
    """Get database connection from pool"""
    return db_pool.get_connection()

async def execute_query(query: str, *args):
    """Execute query using connection pool"""
    return await db_pool.execute_query(query, *args)

async def execute_one(query: str, *args):
    """Execute query expecting single result"""
    return await db_pool.execute_one(query, *args)
