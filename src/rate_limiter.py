"""
Rate Limiter for WingmanMatch

Provides comprehensive rate limiting using token bucket algorithm with Redis backend.
Includes IP-based and user-based limiting, configurable limits per endpoint,
and graceful degradation when Redis is unavailable.
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union
from enum import Enum
from collections import defaultdict

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse

from src.config import Config
from src.redis_client import redis_service, get_redis

logger = logging.getLogger(__name__)

class RateLimitType(Enum):
    """Types of rate limiting"""
    IP_BASED = "ip"
    USER_BASED = "user"
    ENDPOINT_BASED = "endpoint"
    GLOBAL = "global"

class RateLimitScope(Enum):
    """Scope of rate limiting"""
    PER_MINUTE = "minute"
    PER_HOUR = "hour"
    PER_DAY = "day"

class RateLimitError(Exception):
    """Exception raised when rate limit is exceeded"""
    pass

class RateLimitConfig:
    """Configuration for rate limiting rules"""
    
    def __init__(
        self,
        requests: int,
        window_seconds: int,
        burst_allowance: int = None,
        scope: RateLimitScope = RateLimitScope.PER_MINUTE
    ):
        self.requests = requests
        self.window_seconds = window_seconds
        self.burst_allowance = burst_allowance or int(requests * 1.5)
        self.scope = scope

class TokenBucket:
    """
    Token bucket implementation for rate limiting.
    
    Allows burst traffic up to bucket capacity while maintaining
    long-term rate compliance.
    """
    
    def __init__(
        self,
        capacity: int,
        refill_rate: float,
        initial_tokens: Optional[int] = None
    ):
        self.capacity = capacity
        self.refill_rate = refill_rate  # tokens per second
        self.tokens = initial_tokens if initial_tokens is not None else capacity
        self.last_refill = time.time()
    
    def _refill_tokens(self):
        """Refill tokens based on elapsed time"""
        now = time.time()
        elapsed = now - self.last_refill
        tokens_to_add = elapsed * self.refill_rate
        
        self.tokens = min(self.capacity, self.tokens + tokens_to_add)
        self.last_refill = now
    
    def consume(self, tokens: int = 1) -> bool:
        """
        Attempt to consume tokens from bucket.
        
        Args:
            tokens: Number of tokens to consume
            
        Returns:
            bool: True if tokens were consumed, False if insufficient tokens
        """
        self._refill_tokens()
        
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get current bucket status"""
        self._refill_tokens()
        return {
            "tokens": self.tokens,
            "capacity": self.capacity,
            "refill_rate": self.refill_rate,
            "last_refill": self.last_refill
        }

class RateLimiter:
    """
    Comprehensive rate limiter with Redis backend and in-memory fallback.
    
    Supports multiple rate limiting strategies:
    - IP-based limiting
    - User-based limiting
    - Endpoint-specific limiting
    - Global rate limiting
    """
    
    def __init__(self):
        self.default_config = self._get_default_rate_limits()
        self.endpoint_configs = self._get_endpoint_rate_limits()
        
        # In-memory fallback storage
        self._memory_buckets: Dict[str, TokenBucket] = {}
        self._memory_counters: Dict[str, Dict[str, Any]] = defaultdict(dict)
        
    def _get_default_rate_limits(self) -> Dict[RateLimitType, RateLimitConfig]:
        """Get default rate limit configurations"""
        return {
            RateLimitType.IP_BASED: RateLimitConfig(
                requests=100,
                window_seconds=3600,  # 1 hour
                burst_allowance=150,
                scope=RateLimitScope.PER_HOUR
            ),
            RateLimitType.USER_BASED: RateLimitConfig(
                requests=1000,
                window_seconds=3600,  # 1 hour
                burst_allowance=1200,
                scope=RateLimitScope.PER_HOUR
            ),
            RateLimitType.GLOBAL: RateLimitConfig(
                requests=10000,
                window_seconds=3600,  # 1 hour
                burst_allowance=12000,
                scope=RateLimitScope.PER_HOUR
            )
        }
    
    def _get_endpoint_rate_limits(self) -> Dict[str, RateLimitConfig]:
        """Get endpoint-specific rate limit configurations"""
        return {
            # Authentication endpoints (more restrictive)
            "/auth/login": RateLimitConfig(
                requests=5,
                window_seconds=300,  # 5 minutes
                burst_allowance=7
            ),
            "/auth/register": RateLimitConfig(
                requests=3,
                window_seconds=300,  # 5 minutes
                burst_allowance=5
            ),
            "/auth/forgot-password": RateLimitConfig(
                requests=3,
                window_seconds=900,  # 15 minutes
                burst_allowance=4
            ),
            
            # Wingman matching endpoints
            "/wingman/request": RateLimitConfig(
                requests=10,
                window_seconds=3600,  # 1 hour
                burst_allowance=15
            ),
            "/wingman/respond": RateLimitConfig(
                requests=20,
                window_seconds=3600,  # 1 hour
                burst_allowance=25
            ),
            
            # Challenge endpoints
            "/challenges/create": RateLimitConfig(
                requests=5,
                window_seconds=3600,  # 1 hour
                burst_allowance=7
            ),
            "/challenges/join": RateLimitConfig(
                requests=10,
                window_seconds=3600,  # 1 hour
                burst_allowance=15
            ),
            
            # Email endpoints (very restrictive)
            "/email/send": RateLimitConfig(
                requests=10,
                window_seconds=3600,  # 1 hour
                burst_allowance=12
            ),
            
            # Public endpoints (moderate limits)
            "/health": RateLimitConfig(
                requests=60,
                window_seconds=60,  # 1 minute
                burst_allowance=100
            ),
            "/config/features": RateLimitConfig(
                requests=30,
                window_seconds=60,  # 1 minute
                burst_allowance=50
            )
        }
    
    def _get_rate_limit_key(
        self,
        limit_type: RateLimitType,
        identifier: str,
        endpoint: Optional[str] = None,
        window_start: Optional[int] = None
    ) -> str:
        """Generate Redis key for rate limiting"""
        timestamp = window_start or int(time.time())
        
        if limit_type == RateLimitType.IP_BASED:
            return f"ratelimit:ip:{identifier}:{timestamp}"
        elif limit_type == RateLimitType.USER_BASED:
            return f"ratelimit:user:{identifier}:{timestamp}"
        elif limit_type == RateLimitType.ENDPOINT_BASED and endpoint:
            return f"ratelimit:endpoint:{endpoint}:{identifier}:{timestamp}"
        elif limit_type == RateLimitType.GLOBAL:
            return f"ratelimit:global:{timestamp}"
        else:
            return f"ratelimit:unknown:{identifier}:{timestamp}"
    
    def _get_window_start(self, window_seconds: int) -> int:
        """Get the start of the current time window"""
        return int(time.time()) // window_seconds * window_seconds
    
    async def _check_redis_rate_limit(
        self,
        key: str,
        config: RateLimitConfig,
        tokens_requested: int = 1
    ) -> Tuple[bool, Dict[str, Any]]:
        """Check rate limit using Redis backend"""
        try:
            async with get_redis() as redis_client:
                if not redis_client.is_available():
                    return await self._check_memory_rate_limit(key, config, tokens_requested)
                
                # Use Redis for sliding window rate limiting
                window_start = self._get_window_start(config.window_seconds)
                rate_key = f"{key}:{window_start}"
                
                # Get current count and increment
                current_count = await redis_client.increment_counter(
                    rate_key, 
                    config.window_seconds
                )
                
                allowed = current_count <= config.requests
                
                # Calculate reset time
                reset_time = window_start + config.window_seconds
                remaining = max(0, config.requests - current_count)
                
                return allowed, {
                    "allowed": allowed,
                    "count": current_count,
                    "limit": config.requests,
                    "remaining": remaining,
                    "reset_time": reset_time,
                    "window_seconds": config.window_seconds
                }
                
        except Exception as e:
            logger.error(f"Error checking Redis rate limit: {str(e)}")
            return await self._check_memory_rate_limit(key, config, tokens_requested)
    
    async def _check_memory_rate_limit(
        self,
        key: str,
        config: RateLimitConfig,
        tokens_requested: int = 1
    ) -> Tuple[bool, Dict[str, Any]]:
        """Check rate limit using in-memory fallback"""
        try:
            # Get or create token bucket for this key
            if key not in self._memory_buckets:
                refill_rate = config.requests / config.window_seconds
                self._memory_buckets[key] = TokenBucket(
                    capacity=config.burst_allowance,
                    refill_rate=refill_rate
                )
            
            bucket = self._memory_buckets[key]
            allowed = bucket.consume(tokens_requested)
            
            status = bucket.get_status()
            
            return allowed, {
                "allowed": allowed,
                "tokens": status["tokens"],
                "capacity": status["capacity"],
                "refill_rate": status["refill_rate"],
                "window_seconds": config.window_seconds
            }
            
        except Exception as e:
            logger.error(f"Error in memory rate limiting: {str(e)}")
            # Ultimate fallback - allow request
            return True, {"allowed": True, "fallback": True}
    
    async def check_rate_limit(
        self,
        request: Request,
        endpoint: Optional[str] = None,
        user_id: Optional[str] = None,
        tokens_requested: int = 1
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Check rate limits for a request.
        
        Args:
            request: FastAPI request object
            endpoint: Specific endpoint being accessed
            user_id: User ID if authenticated
            tokens_requested: Number of tokens to consume
            
        Returns:
            Tuple of (allowed, rate_limit_info)
        """
        client_ip = self._get_client_ip(request)
        endpoint_path = endpoint or request.url.path
        
        # Check endpoint-specific rate limit
        if endpoint_path in self.endpoint_configs:
            config = self.endpoint_configs[endpoint_path]
            key = self._get_rate_limit_key(
                RateLimitType.ENDPOINT_BASED,
                client_ip,
                endpoint_path
            )
            
            allowed, info = await self._check_redis_rate_limit(key, config, tokens_requested)
            if not allowed:
                return False, {**info, "limit_type": "endpoint", "endpoint": endpoint_path}
        
        # Check user-based rate limit (if authenticated)
        if user_id:
            config = self.default_config[RateLimitType.USER_BASED]
            key = self._get_rate_limit_key(RateLimitType.USER_BASED, user_id)
            
            allowed, info = await self._check_redis_rate_limit(key, config, tokens_requested)
            if not allowed:
                return False, {**info, "limit_type": "user", "user_id": user_id}
        
        # Check IP-based rate limit
        config = self.default_config[RateLimitType.IP_BASED]
        key = self._get_rate_limit_key(RateLimitType.IP_BASED, client_ip)
        
        allowed, info = await self._check_redis_rate_limit(key, config, tokens_requested)
        if not allowed:
            return False, {**info, "limit_type": "ip", "client_ip": client_ip}
        
        # Check global rate limit
        config = self.default_config[RateLimitType.GLOBAL]
        key = self._get_rate_limit_key(RateLimitType.GLOBAL, "global")
        
        allowed, info = await self._check_redis_rate_limit(key, config, tokens_requested)
        if not allowed:
            return False, {**info, "limit_type": "global"}
        
        # All checks passed
        return True, {"allowed": True, "limit_type": "none"}
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request, considering proxies"""
        # Check for forwarded IP (from load balancers/proxies)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take the first IP in the chain
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fallback to client host
        return request.client.host if request.client else "unknown"
    
    async def get_rate_limit_status(
        self,
        request: Request,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get current rate limit status for debugging.
        
        Args:
            request: FastAPI request object
            user_id: User ID if authenticated
            
        Returns:
            Dict with rate limit status information
        """
        client_ip = self._get_client_ip(request)
        endpoint_path = request.url.path
        
        status = {
            "client_ip": client_ip,
            "endpoint": endpoint_path,
            "user_id": user_id,
            "limits": {}
        }
        
        # Check each rate limit type
        limit_checks = [
            ("ip", RateLimitType.IP_BASED, client_ip),
            ("global", RateLimitType.GLOBAL, "global")
        ]
        
        if user_id:
            limit_checks.append(("user", RateLimitType.USER_BASED, user_id))
        
        if endpoint_path in self.endpoint_configs:
            limit_checks.append(("endpoint", RateLimitType.ENDPOINT_BASED, client_ip))
        
        for check_name, limit_type, identifier in limit_checks:
            try:
                config = (self.endpoint_configs.get(endpoint_path) 
                         if limit_type == RateLimitType.ENDPOINT_BASED 
                         else self.default_config[limit_type])
                
                key = self._get_rate_limit_key(limit_type, identifier, endpoint_path)
                _, info = await self._check_redis_rate_limit(key, config, 0)  # Don't consume tokens
                
                status["limits"][check_name] = info
                
            except Exception as e:
                status["limits"][check_name] = {"error": str(e)}
        
        return status
    
    def get_service_stats(self) -> Dict[str, Any]:
        """Get rate limiter service statistics"""
        return {
            "memory_buckets_count": len(self._memory_buckets),
            "memory_counters_count": len(self._memory_counters),
            "endpoint_configs_count": len(self.endpoint_configs),
            "default_configs_count": len(self.default_config),
            "redis_available": redis_service.is_available()
        }
    
    def clear_memory_cache(self) -> Dict[str, int]:
        """Clear in-memory rate limiting cache"""
        buckets_cleared = len(self._memory_buckets)
        counters_cleared = len(self._memory_counters)
        
        self._memory_buckets.clear()
        self._memory_counters.clear()
        
        return {
            "buckets_cleared": buckets_cleared,
            "counters_cleared": counters_cleared
        }

# Global rate limiter instance
rate_limiter = RateLimiter()

# FastAPI dependency for rate limiting
async def check_rate_limit_dependency(
    request: Request,
    user_id: Optional[str] = None
) -> None:
    """
    FastAPI dependency for rate limiting.
    
    Raises HTTPException if rate limit is exceeded.
    """
    allowed, info = await rate_limiter.check_rate_limit(request, user_id=user_id)
    
    if not allowed:
        # Add rate limit headers to response
        headers = {
            "X-RateLimit-Limit": str(info.get("limit", "unknown")),
            "X-RateLimit-Remaining": str(info.get("remaining", 0)),
            "X-RateLimit-Reset": str(info.get("reset_time", 0)),
        }
        
        if "window_seconds" in info:
            headers["X-RateLimit-Window"] = str(info["window_seconds"])
        
        raise HTTPException(
            status_code=429,
            detail={
                "error": "Rate limit exceeded",
                "message": f"Too many requests for {info.get('limit_type', 'unknown')} limit",
                "retry_after": info.get("reset_time", 0) - int(time.time()),
                "limit_info": info
            },
            headers=headers
        )

# Decorator for rate limiting
def rate_limit(
    endpoint: Optional[str] = None,
    tokens: int = 1
):
    """
    Decorator for rate limiting endpoints.
    
    Args:
        endpoint: Endpoint identifier (uses function name if not provided)
        tokens: Number of tokens to consume
    """
    def decorator(func):
        async def wrapper(request: Request, *args, **kwargs):
            endpoint_name = endpoint or f"/{func.__name__}"
            
            # Extract user_id from kwargs if available
            user_id = kwargs.get("user_id")
            
            allowed, info = await rate_limiter.check_rate_limit(
                request, 
                endpoint=endpoint_name,
                user_id=user_id,
                tokens_requested=tokens
            )
            
            if not allowed:
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": "Rate limit exceeded",
                        "limit_info": info
                    },
                    headers={
                        "X-RateLimit-Limit": str(info.get("limit", "unknown")),
                        "X-RateLimit-Remaining": str(info.get("remaining", 0)),
                        "X-RateLimit-Reset": str(info.get("reset_time", 0)),
                    }
                )
            
            return await func(request, *args, **kwargs)
        
        return wrapper
    return decorator

# Convenience functions

async def check_ip_rate_limit(ip_address: str) -> Tuple[bool, Dict[str, Any]]:
    """Check rate limit for specific IP address"""
    config = rate_limiter.default_config[RateLimitType.IP_BASED]
    key = rate_limiter._get_rate_limit_key(RateLimitType.IP_BASED, ip_address)
    return await rate_limiter._check_redis_rate_limit(key, config)

async def check_user_rate_limit(user_id: str) -> Tuple[bool, Dict[str, Any]]:
    """Check rate limit for specific user"""
    config = rate_limiter.default_config[RateLimitType.USER_BASED]
    key = rate_limiter._get_rate_limit_key(RateLimitType.USER_BASED, user_id)
    return await rate_limiter._check_redis_rate_limit(key, config)

async def get_rate_limiter_health() -> Dict[str, Any]:
    """Get rate limiter health status"""
    return {
        **rate_limiter.get_service_stats(),
        "redis_status": await redis_service.get_stats() if redis_service.is_available() else None
    }