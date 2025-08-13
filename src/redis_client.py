"""
Redis Client Service for WingmanMatch

Provides Redis connection management with health checks, graceful fallback,
session storage, and rate limiting support. Follows async patterns with
comprehensive error handling.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from contextlib import asynccontextmanager

import redis.asyncio as redis
from redis.asyncio import ConnectionPool, Redis
from redis.exceptions import ConnectionError, TimeoutError, RedisError

from src.config import Config

logger = logging.getLogger(__name__)

class RedisConnectionError(Exception):
    """Custom exception for Redis connection issues"""
    pass

class RedisService:
    """
    Async Redis service with connection pooling, health checks, and graceful fallback.
    
    Provides session management, caching, and rate limiting support for WingmanMatch.
    Designed to degrade gracefully when Redis is unavailable.
    """
    
    def __init__(self):
        self._pool: Optional[ConnectionPool] = None
        self._client: Optional[Redis] = None
        self._is_available = False
        self._last_health_check = None
        self._health_check_interval = timedelta(minutes=5)
        
        # Fallback in-memory storage when Redis is unavailable
        self._memory_cache: Dict[str, Any] = {}
        self._memory_timestamps: Dict[str, datetime] = {}
        
    async def initialize(self) -> bool:
        """
        Initialize Redis connection pool and client.
        
        Returns:
            bool: True if Redis is available, False if using fallback mode
        """
        if not Config.REDIS_URL:
            logger.warning("Redis URL not configured, using in-memory fallback")
            return False
            
        try:
            # Create connection pool
            self._pool = ConnectionPool.from_url(
                Config.REDIS_URL,
                password=Config.REDIS_PASSWORD,
                max_connections=20,
                retry_on_timeout=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                health_check_interval=30
            )
            
            # Create Redis client
            self._client = Redis(connection_pool=self._pool)
            
            # Test connection
            await self._client.ping()
            self._is_available = True
            self._last_health_check = datetime.now()
            
            logger.info("Redis client initialized successfully")
            return True
            
        except (ConnectionError, TimeoutError, RedisError) as e:
            logger.warning(f"Redis connection failed, using fallback mode: {str(e)}")
            self._is_available = False
            return False
        except Exception as e:
            logger.error(f"Unexpected error initializing Redis: {str(e)}")
            self._is_available = False
            return False
    
    async def health_check(self) -> bool:
        """
        Perform health check on Redis connection.
        
        Returns:
            bool: True if Redis is healthy, False otherwise
        """
        now = datetime.now()
        
        # Skip health check if recently performed
        if (self._last_health_check and 
            now - self._last_health_check < self._health_check_interval):
            return self._is_available
            
        if not self._client:
            return False
            
        try:
            await self._client.ping()
            self._is_available = True
            self._last_health_check = now
            return True
        except (ConnectionError, TimeoutError, RedisError):
            logger.warning("Redis health check failed, switching to fallback mode")
            self._is_available = False
            self._last_health_check = now
            return False
        except Exception as e:
            logger.error(f"Unexpected error during Redis health check: {str(e)}")
            self._is_available = False
            self._last_health_check = now
            return False
    
    async def close(self) -> None:
        """Close Redis connections and cleanup resources"""
        if self._client:
            try:
                await self._client.close()
            except Exception as e:
                logger.error(f"Error closing Redis client: {str(e)}")
        
        if self._pool:
            try:
                await self._pool.disconnect()
            except Exception as e:
                logger.error(f"Error closing Redis pool: {str(e)}")
        
        # Clear in-memory cache
        self._memory_cache.clear()
        self._memory_timestamps.clear()
        
        logger.info("Redis client closed")
    
    # Session Management Methods
    
    async def set_session(self, session_key: str, data: Dict[str, Any], 
                         expiry_seconds: int = 86400) -> bool:
        """
        Store session data with expiry.
        
        Args:
            session_key: Unique session identifier
            data: Session data to store
            expiry_seconds: Expiry time in seconds (default 24 hours)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            serialized_data = json.dumps(data, default=str)
            
            if await self.health_check():
                await self._client.setex(session_key, expiry_seconds, serialized_data)
                logger.debug(f"Session stored in Redis: {session_key}")
            else:
                # Fallback to in-memory storage
                self._memory_cache[session_key] = serialized_data
                self._memory_timestamps[session_key] = datetime.now() + timedelta(seconds=expiry_seconds)
                logger.debug(f"Session stored in memory fallback: {session_key}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error storing session {session_key}: {str(e)}")
            return False
    
    async def get_session(self, session_key: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve session data.
        
        Args:
            session_key: Session identifier
            
        Returns:
            Dict with session data or None if not found/expired
        """
        try:
            if await self.health_check():
                data = await self._client.get(session_key)
                if data:
                    return json.loads(data)
            else:
                # Check in-memory fallback
                if session_key in self._memory_cache:
                    # Check if expired
                    if datetime.now() < self._memory_timestamps.get(session_key, datetime.now()):
                        return json.loads(self._memory_cache[session_key])
                    else:
                        # Remove expired data
                        self._memory_cache.pop(session_key, None)
                        self._memory_timestamps.pop(session_key, None)
            
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving session {session_key}: {str(e)}")
            return None
    
    async def delete_session(self, session_key: str) -> bool:
        """
        Delete session data.
        
        Args:
            session_key: Session identifier
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if await self.health_check():
                await self._client.delete(session_key)
            else:
                # Remove from in-memory fallback
                self._memory_cache.pop(session_key, None)
                self._memory_timestamps.pop(session_key, None)
            
            logger.debug(f"Session deleted: {session_key}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting session {session_key}: {str(e)}")
            return False
    
    # Rate Limiting Support Methods
    
    async def increment_counter(self, key: str, expiry_seconds: int = 3600) -> int:
        """
        Increment a counter with expiry (for rate limiting).
        
        Args:
            key: Counter key
            expiry_seconds: Expiry time in seconds
            
        Returns:
            int: Current counter value
        """
        try:
            if await self.health_check():
                # Use Redis INCR with expiry
                pipe = self._client.pipeline()
                pipe.incr(key)
                pipe.expire(key, expiry_seconds)
                results = await pipe.execute()
                return results[0]
            else:
                # In-memory fallback
                current_time = datetime.now()
                
                # Clean expired counters
                expired_keys = [
                    k for k, expiry in self._memory_timestamps.items()
                    if current_time > expiry
                ]
                for k in expired_keys:
                    self._memory_cache.pop(k, None)
                    self._memory_timestamps.pop(k, None)
                
                # Increment counter
                current_value = self._memory_cache.get(key, 0) + 1
                self._memory_cache[key] = current_value
                self._memory_timestamps[key] = current_time + timedelta(seconds=expiry_seconds)
                
                return current_value
                
        except Exception as e:
            logger.error(f"Error incrementing counter {key}: {str(e)}")
            return 1  # Safe fallback
    
    async def get_counter(self, key: str) -> int:
        """
        Get current counter value.
        
        Args:
            key: Counter key
            
        Returns:
            int: Current counter value (0 if not found)
        """
        try:
            if await self.health_check():
                value = await self._client.get(key)
                return int(value) if value else 0
            else:
                # Check in-memory fallback
                if key in self._memory_cache:
                    if datetime.now() < self._memory_timestamps.get(key, datetime.now()):
                        return self._memory_cache[key]
                    else:
                        # Remove expired data
                        self._memory_cache.pop(key, None)
                        self._memory_timestamps.pop(key, None)
                
                return 0
                
        except Exception as e:
            logger.error(f"Error getting counter {key}: {str(e)}")
            return 0
    
    # General Caching Methods
    
    async def set_cache(self, key: str, value: Any, expiry_seconds: int = 3600) -> bool:
        """
        Set cache value with expiry.
        
        Args:
            key: Cache key
            value: Value to cache
            expiry_seconds: Expiry time in seconds
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            serialized_value = json.dumps(value, default=str)
            
            if await self.health_check():
                await self._client.setex(key, expiry_seconds, serialized_value)
            else:
                # In-memory fallback
                self._memory_cache[key] = serialized_value
                self._memory_timestamps[key] = datetime.now() + timedelta(seconds=expiry_seconds)
            
            return True
            
        except Exception as e:
            logger.error(f"Error setting cache {key}: {str(e)}")
            return False
    
    async def get_cache(self, key: str) -> Optional[Any]:
        """
        Get cached value.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        try:
            if await self.health_check():
                data = await self._client.get(key)
                if data:
                    return json.loads(data)
            else:
                # Check in-memory fallback
                if key in self._memory_cache:
                    if datetime.now() < self._memory_timestamps.get(key, datetime.now()):
                        return json.loads(self._memory_cache[key])
                    else:
                        # Remove expired data
                        self._memory_cache.pop(key, None)
                        self._memory_timestamps.pop(key, None)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting cache {key}: {str(e)}")
            return None
    
    async def delete_cache(self, key: str) -> bool:
        """
        Delete cached value.
        
        Args:
            key: Cache key
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if await self.health_check():
                await self._client.delete(key)
            else:
                # Remove from in-memory fallback
                self._memory_cache.pop(key, None)
                self._memory_timestamps.pop(key, None)
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting cache {key}: {str(e)}")
            return False
    
    # Utility Methods
    
    def is_available(self) -> bool:
        """Check if Redis is currently available"""
        return self._is_available
    
    async def get_stats(self) -> Dict[str, Any]:
        """
        Get Redis connection and usage statistics.
        
        Returns:
            Dict with connection stats and cache information
        """
        stats = {
            "redis_available": self._is_available,
            "last_health_check": self._last_health_check.isoformat() if self._last_health_check else None,
            "fallback_cache_size": len(self._memory_cache),
            "redis_url_configured": bool(Config.REDIS_URL)
        }
        
        if self._is_available and self._client:
            try:
                info = await self._client.info()
                stats.update({
                    "redis_version": info.get("redis_version"),
                    "connected_clients": info.get("connected_clients"),
                    "used_memory_human": info.get("used_memory_human"),
                    "total_commands_processed": info.get("total_commands_processed")
                })
            except Exception as e:
                logger.error(f"Error getting Redis stats: {str(e)}")
        
        return stats

# Global Redis service instance
redis_service = RedisService()

@asynccontextmanager
async def get_redis():
    """
    Context manager for Redis operations.
    
    Ensures proper initialization and provides the Redis service instance.
    """
    if not redis_service._client:
        await redis_service.initialize()
    
    try:
        yield redis_service
    finally:
        # Context manager cleanup if needed
        pass

# Convenience functions for common operations

async def get_session_data(session_key: str) -> Optional[Dict[str, Any]]:
    """Convenience function to get session data"""
    async with get_redis() as redis_client:
        return await redis_client.get_session(session_key)

async def set_session_data(session_key: str, data: Dict[str, Any], 
                          expiry_seconds: int = 86400) -> bool:
    """Convenience function to set session data"""
    async with get_redis() as redis_client:
        return await redis_client.set_session(session_key, data, expiry_seconds)

async def increment_rate_limit_counter(key: str, window_seconds: int = 3600) -> int:
    """Convenience function for rate limiting counters"""
    async with get_redis() as redis_client:
        return await redis_client.increment_counter(key, window_seconds)