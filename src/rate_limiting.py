"""
Rate limiting for WingmanMatch using token bucket algorithm
Provides public endpoint protection with Redis-backed persistence
"""

import logging
import time
from typing import Dict, Any, Optional
from src.redis_session import RedisSession
from src.config import Config

logger = logging.getLogger(__name__)

class TokenBucket:
    """Token bucket rate limiter with Redis persistence"""
    
    def __init__(self, capacity: int, refill_rate: float, key_prefix: str = "rate_limit"):
        self.capacity = capacity
        self.refill_rate = refill_rate  # tokens per second
        self.key_prefix = key_prefix
    
    async def consume(self, identifier: str, tokens: int = 1) -> Dict[str, Any]:
        """
        Attempt to consume tokens from bucket
        Returns dict with success status and current state
        """
        redis_client = await RedisSession.get_client()
        bucket_key = f"{self.key_prefix}:{identifier}"
        
        # If Redis unavailable, allow request but log warning
        if not redis_client:
            logger.warning(f"Redis unavailable - rate limiting disabled for {identifier}")
            return {
                "allowed": True,
                "tokens_remaining": self.capacity,
                "retry_after": None,
                "redis_fallback": True
            }
        
        try:
            current_time = time.time()
            
            # Get current bucket state
            bucket_data = await redis_client.hgetall(bucket_key)
            
            if bucket_data:
                # Parse existing bucket
                last_refill = float(bucket_data.get("last_refill", current_time))
                current_tokens = float(bucket_data.get("tokens", self.capacity))
            else:
                # Initialize new bucket
                last_refill = current_time
                current_tokens = self.capacity
            
            # Calculate tokens to add based on time elapsed
            time_elapsed = current_time - last_refill
            tokens_to_add = time_elapsed * self.refill_rate
            current_tokens = min(self.capacity, current_tokens + tokens_to_add)
            
            # Check if we can consume requested tokens
            if current_tokens >= tokens:
                # Consume tokens
                current_tokens -= tokens
                allowed = True
                retry_after = None
            else:
                # Not enough tokens
                allowed = False
                tokens_needed = tokens - current_tokens
                retry_after = tokens_needed / self.refill_rate
            
            # Update bucket state in Redis
            bucket_state = {
                "tokens": str(current_tokens),
                "last_refill": str(current_time),
                "capacity": str(self.capacity),
                "refill_rate": str(self.refill_rate)
            }
            
            await redis_client.hset(bucket_key, mapping=bucket_state)
            await redis_client.expire(bucket_key, int(self.capacity / self.refill_rate) + 60)  # TTL with buffer
            
            return {
                "allowed": allowed,
                "tokens_remaining": int(current_tokens),
                "retry_after": retry_after,
                "redis_fallback": False
            }
            
        except Exception as e:
            logger.error(f"Rate limiting error for {identifier}: {e}")
            # Fail open - allow request if rate limiting fails
            return {
                "allowed": True,
                "tokens_remaining": 0,
                "retry_after": None,
                "error": str(e)
            }

class RateLimiter:
    """Rate limiter manager with predefined limits for different endpoints"""
    
    # Predefined rate limits (capacity, refill_rate per second)
    LIMITS = {
        "public_api": (100, 1.0),      # 100 requests, 1 per second refill
        "auth_endpoint": (10, 0.1),    # 10 requests, 1 per 10 seconds
        "match_request": (5, 0.05),    # 5 requests, 1 per 20 seconds
        "email_send": (3, 0.01),       # 3 requests, 1 per 100 seconds
        "challenge_submit": (20, 0.2), # 20 requests, 1 per 5 seconds
    }
    
    def __init__(self):
        self.buckets = {}
        for limit_type, (capacity, refill_rate) in self.LIMITS.items():
            self.buckets[limit_type] = TokenBucket(
                capacity=capacity,
                refill_rate=refill_rate,
                key_prefix=f"rate_limit:{limit_type}"
            )
    
    async def check_limit(self, limit_type: str, identifier: str, tokens: int = 1) -> Dict[str, Any]:
        """Check rate limit for specific endpoint and identifier"""
        if limit_type not in self.buckets:
            logger.warning(f"Unknown rate limit type: {limit_type}")
            return {"allowed": True, "unknown_limit_type": True}
        
        bucket = self.buckets[limit_type]
        result = await bucket.consume(identifier, tokens)
        
        # Add limit type to result for logging
        result["limit_type"] = limit_type
        result["identifier"] = identifier
        
        if not result["allowed"]:
            logger.warning(f"Rate limit exceeded for {limit_type}:{identifier}")
        
        return result
    
    async def check_ip_limit(self, endpoint: str, ip_address: str) -> Dict[str, Any]:
        """Check rate limit based on IP address"""
        limit_type = self._get_limit_type_for_endpoint(endpoint)
        return await self.check_limit(limit_type, f"ip:{ip_address}")
    
    async def check_user_limit(self, endpoint: str, user_id: str) -> Dict[str, Any]:
        """Check rate limit based on user ID"""
        limit_type = self._get_limit_type_for_endpoint(endpoint)
        return await self.check_limit(limit_type, f"user:{user_id}")
    
    def _get_limit_type_for_endpoint(self, endpoint: str) -> str:
        """Map endpoint to rate limit type"""
        endpoint_mapping = {
            "/auth/": "auth_endpoint",
            "/wingman/request": "match_request", 
            "/email/": "email_send",
            "/challenges/": "challenge_submit",
        }
        
        for pattern, limit_type in endpoint_mapping.items():
            if pattern in endpoint:
                return limit_type
        
        return "public_api"  # Default limit
    
    async def get_status(self) -> Dict[str, Any]:
        """Get rate limiter status"""
        redis_health = await RedisSession.health_check()
        
        return {
            "enabled": Config.ENABLE_RATE_LIMITING,
            "redis_available": redis_health.get("connected", False),
            "configured_limits": {
                limit_type: {
                    "capacity": capacity,
                    "refill_rate_per_second": refill_rate
                }
                for limit_type, (capacity, refill_rate) in self.LIMITS.items()
            }
        }

# Global rate limiter instance
rate_limiter = RateLimiter()