"""
Redis session management for WingmanMatch
Provides connection pool with health monitoring and graceful fallback
"""

import logging
import json
from typing import Optional, Any, Dict
import redis.asyncio as redis
from redis.asyncio import ConnectionPool
from src.config import Config

logger = logging.getLogger(__name__)

class RedisSession:
    """Redis session manager with connection pool and health monitoring"""
    
    _pool: Optional[ConnectionPool] = None
    _client: Optional[redis.Redis] = None
    _healthy: bool = False
    
    @classmethod
    async def initialize(cls):
        """Initialize Redis connection pool"""
        if not Config.REDIS_URL:
            logger.warning("REDIS_URL not configured - Redis features disabled")
            return
        
        try:
            cls._pool = ConnectionPool.from_url(
                Config.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                max_connections=20,
                retry_on_timeout=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            
            cls._client = redis.Redis(connection_pool=cls._pool)
            
            # Test connection
            await cls._client.ping()
            cls._healthy = True
            logger.info("Redis connection pool initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Redis: {e}")
            cls._healthy = False
            cls._client = None
    
    @classmethod
    async def get_client(cls) -> Optional[redis.Redis]:
        """Get Redis client if available"""
        if cls._client is None:
            await cls.initialize()
        return cls._client
    
    @classmethod
    async def health_check(cls) -> Dict[str, Any]:
        """Perform Redis health check with ping"""
        health = {
            "connected": False,
            "ping_time": None,
            "error": None
        }
        
        if not cls._client:
            health["error"] = "Redis client not initialized"
            return health
        
        try:
            import time
            start_time = time.time()
            await cls._client.ping()
            ping_time = (time.time() - start_time) * 1000  # ms
            
            health.update({
                "connected": True,
                "ping_time": f"{ping_time:.2f}ms"
            })
            cls._healthy = True
            
        except Exception as e:
            health["error"] = str(e)
            cls._healthy = False
            logger.error(f"Redis health check failed: {e}")
        
        return health
    
    @classmethod
    async def set_session(cls, session_id: str, data: Dict[str, Any], ttl: int = 3600):
        """Store session data with TTL (default 1 hour)"""
        if not cls._healthy or not cls._client:
            logger.warning("Redis unavailable - session not stored")
            return False
        
        try:
            json_data = json.dumps(data)
            await cls._client.setex(f"session:{session_id}", ttl, json_data)
            return True
        except Exception as e:
            logger.error(f"Failed to store session {session_id}: {e}")
            return False
    
    @classmethod
    async def get_session(cls, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve session data"""
        if not cls._healthy or not cls._client:
            logger.warning("Redis unavailable - session not retrieved")
            return None
        
        try:
            json_data = await cls._client.get(f"session:{session_id}")
            if json_data:
                return json.loads(json_data)
            return None
        except Exception as e:
            logger.error(f"Failed to retrieve session {session_id}: {e}")
            return None
    
    @classmethod
    async def delete_session(cls, session_id: str) -> bool:
        """Delete session data"""
        if not cls._healthy or not cls._client:
            logger.warning("Redis unavailable - session not deleted")
            return False
        
        try:
            result = await cls._client.delete(f"session:{session_id}")
            return result > 0
        except Exception as e:
            logger.error(f"Failed to delete session {session_id}: {e}")
            return False
    
    @classmethod
    async def extend_session(cls, session_id: str, ttl: int = 3600) -> bool:
        """Extend session TTL"""
        if not cls._healthy or not cls._client:
            return False
        
        try:
            result = await cls._client.expire(f"session:{session_id}", ttl)
            return result
        except Exception as e:
            logger.error(f"Failed to extend session {session_id}: {e}")
            return False
    
    @classmethod
    async def cleanup(cls):
        """Clean up Redis connections"""
        if cls._client:
            await cls._client.close()
        if cls._pool:
            await cls._pool.disconnect()
        cls._healthy = False
        logger.info("Redis connections cleaned up")

# Convenience functions
async def store_user_session(user_id: str, session_data: Dict[str, Any], ttl: int = 3600) -> bool:
    """Store user session data"""
    return await RedisSession.set_session(f"user:{user_id}", session_data, ttl)

async def get_user_session(user_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve user session data"""
    return await RedisSession.get_session(f"user:{user_id}")

async def clear_user_session(user_id: str) -> bool:
    """Clear user session data"""
    return await RedisSession.delete_session(f"user:{user_id}")

# Cache functions for challenges
async def cache_challenges(cache_key: str, data: dict, ttl: int = 600) -> bool:
    """Cache challenges data with TTL (default 10 minutes)"""
    return await RedisSession.set_session(cache_key, data, ttl)

async def get_cached_challenges(cache_key: str) -> Optional[dict]:
    """Retrieve cached challenges data"""
    return await RedisSession.get_session(cache_key)

async def invalidate_challenges_cache(tag: str = "challenges") -> bool:
    """Invalidate challenges cache by tag"""
    if not RedisSession._healthy or not RedisSession._client:
        logger.warning("Redis unavailable - cache not invalidated")
        return False
    
    try:
        # For MVP, we'll use a simple pattern match to find keys
        keys = await RedisSession._client.keys(f"challenges:*")
        if keys:
            await RedisSession._client.delete(*keys)
            logger.info(f"Invalidated {len(keys)} challenge cache keys")
        return True
    except Exception as e:
        logger.error(f"Failed to invalidate challenges cache: {e}")
        return False