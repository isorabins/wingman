#!/usr/bin/env python3
"""
Cache Middleware for WingmanMatch Performance Optimization

Provides FastAPI middleware for intelligent caching with Redis integration,
ETag support, and automatic cache invalidation for hot data access.

Features:
- Automatic response caching for cacheable endpoints
- ETag generation and validation for static content
- Cache-Control headers for browser optimization
- User-specific cache isolation
- Configurable TTL per endpoint type
- Cache invalidation on data mutations
"""

import hashlib
import json
import logging
from typing import Dict, List, Optional, Any, Callable, Set
from datetime import datetime, timedelta
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from src.redis_client import redis_service
from src.config import Config

logger = logging.getLogger(__name__)

class CacheMiddleware(BaseHTTPMiddleware):
    """
    Intelligent caching middleware for WingmanMatch API endpoints.
    
    Provides automatic caching with Redis backend, ETag support for static content,
    and user-scoped cache isolation for security and performance.
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        
        # Cacheable endpoints configuration
        self.cacheable_endpoints = {
            # Challenge data - relatively static
            "/api/challenges": {
                "ttl": 3600,  # 1 hour
                "cache_type": "challenges",
                "user_scoped": False,
                "invalidate_on": ["POST /api/challenges", "PUT /api/challenges", "DELETE /api/challenges"]
            },
            
            # User location data - changes occasionally
            "/api/user/location": {
                "ttl": 1800,  # 30 minutes
                "cache_type": "location",
                "user_scoped": True,
                "invalidate_on": ["POST /api/user/location", "PUT /api/user/location"]
            },
            
            # Reputation data - semi-dynamic
            "/api/user/reputation": {
                "ttl": 300,   # 5 minutes
                "cache_type": "reputation",
                "user_scoped": True,
                "invalidate_on": ["POST /api/matches", "POST /api/reviews"]
            },
            
            # Match results - dynamic but can be cached briefly
            "/api/matches": {
                "ttl": 600,   # 10 minutes
                "cache_type": "matches",
                "user_scoped": True,
                "invalidate_on": ["POST /api/user/location", "POST /api/user/preferences"]
            },
            
            # Confidence test results - relatively static after completion
            "/api/assessment/results": {
                "ttl": 7200,  # 2 hours
                "cache_type": "assessment",
                "user_scoped": True,
                "invalidate_on": ["POST /api/assessment/confidence"]
            },
            
            # Project data - already cached but can be optimized
            "/project-overview": {
                "ttl": 1800,  # 30 minutes
                "cache_type": "project_overview",
                "user_scoped": True,
                "invalidate_on": ["POST /query_stream", "POST /project-updates"]
            },
            
            # Static content
            "/api/static": {
                "ttl": 86400,  # 24 hours
                "cache_type": "static_content",
                "user_scoped": False,
                "etag_enabled": True,
                "invalidate_on": []
            }
        }
        
        # Endpoints that should invalidate caches
        self.cache_invalidating_endpoints = set()
        for config in self.cacheable_endpoints.values():
            self.cache_invalidating_endpoints.update(config.get("invalidate_on", []))
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Main middleware dispatch method.
        
        Handles caching logic for incoming requests and outgoing responses.
        """
        # Skip caching for non-GET requests by default
        if request.method != "GET":
            response = await call_next(request)
            
            # Check if this endpoint invalidates any caches
            await self._handle_cache_invalidation(request)
            
            return response
        
        # Check if this endpoint is cacheable
        cache_config = self._get_cache_config(request)
        if not cache_config:
            return await call_next(request)
        
        # Try to serve from cache
        cached_response = await self._get_cached_response(request, cache_config)
        if cached_response:
            return cached_response
        
        # Not in cache - process request
        response = await call_next(request)
        
        # Cache the response if successful
        if response.status_code == 200:
            await self._cache_response(request, response, cache_config)
        
        return response
    
    def _get_cache_config(self, request: Request) -> Optional[Dict[str, Any]]:
        """
        Get cache configuration for the current request.
        
        Args:
            request: FastAPI request object
            
        Returns:
            Cache configuration dict or None if not cacheable
        """
        path = request.url.path
        
        # Check for exact path match
        if path in self.cacheable_endpoints:
            return self.cacheable_endpoints[path]
        
        # Check for path prefix matches (for parameterized endpoints)
        for endpoint_pattern, config in self.cacheable_endpoints.items():
            if self._path_matches_pattern(path, endpoint_pattern):
                return config
        
        return None
    
    def _path_matches_pattern(self, path: str, pattern: str) -> bool:
        """
        Check if a path matches a cache pattern.
        
        Supports basic path parameter matching like /api/user/{user_id}/data
        """
        # For now, simple prefix matching
        # Could be enhanced with regex patterns if needed
        if pattern.endswith("*"):
            return path.startswith(pattern[:-1])
        
        # Check for path parameters
        if "{" in pattern and "}" in pattern:
            pattern_parts = pattern.split("/")
            path_parts = path.split("/")
            
            if len(pattern_parts) != len(path_parts):
                return False
            
            for pattern_part, path_part in zip(pattern_parts, path_parts):
                if pattern_part.startswith("{") and pattern_part.endswith("}"):
                    continue  # Parameter match
                elif pattern_part != path_part:
                    return False
            
            return True
        
        return path == pattern
    
    async def _get_cached_response(self, request: Request, 
                                  cache_config: Dict[str, Any]) -> Optional[Response]:
        """
        Attempt to retrieve cached response for the request.
        
        Args:
            request: FastAPI request object
            cache_config: Cache configuration
            
        Returns:
            Cached response or None if not found
        """
        try:
            cache_key = self._generate_cache_key(request, cache_config)
            
            # Check Redis cache
            if not await redis_service.health_check():
                return None
            
            cached_data = await redis_service.get_cache(cache_key)
            if not cached_data:
                return None
            
            # Handle ETag validation if enabled
            if cache_config.get("etag_enabled", False):
                etag = cached_data.get("etag")
                if etag and request.headers.get("If-None-Match") == etag:
                    # Client has current version
                    return Response(status_code=304)
            
            # Reconstruct response
            response_data = cached_data.get("response_data")
            headers = cached_data.get("headers", {})
            
            if response_data:
                response = JSONResponse(content=response_data)
                
                # Add cache headers
                response.headers.update(headers)
                response.headers["X-Cache"] = "HIT"
                response.headers["X-Cache-Key"] = cache_key
                
                logger.debug(f"Cache HIT for {request.url.path}: {cache_key}")
                return response
        
        except Exception as e:
            logger.error(f"Error retrieving cached response: {e}")
        
        return None
    
    async def _cache_response(self, request: Request, response: Response, 
                             cache_config: Dict[str, Any]) -> None:
        """
        Cache the response data.
        
        Args:
            request: FastAPI request object
            response: Response to cache
            cache_config: Cache configuration
        """
        try:
            cache_key = self._generate_cache_key(request, cache_config)
            
            # Only cache JSON responses
            if not response.headers.get("content-type", "").startswith("application/json"):
                return
            
            # Read response body
            if hasattr(response, 'body'):
                response_body = response.body
            else:
                # For streaming responses, we can't easily cache
                return
            
            # Parse JSON response
            try:
                response_data = json.loads(response_body.decode())
            except (json.JSONDecodeError, UnicodeDecodeError):
                return
            
            # Prepare cache data
            cache_data = {
                "response_data": response_data,
                "headers": dict(response.headers),
                "cached_at": datetime.now().isoformat(),
                "cache_key": cache_key
            }
            
            # Generate ETag if enabled
            if cache_config.get("etag_enabled", False):
                etag = self._generate_etag(response_body)
                cache_data["etag"] = etag
                response.headers["ETag"] = etag
            
            # Add cache control headers
            ttl = cache_config["ttl"]
            response.headers["Cache-Control"] = f"public, max-age={ttl}"
            response.headers["X-Cache"] = "MISS"
            response.headers["X-Cache-TTL"] = str(ttl)
            
            # Store in cache
            await redis_service.set_cache(cache_key, cache_data, ttl)
            
            logger.debug(f"Cached response for {request.url.path}: {cache_key} (TTL: {ttl}s)")
        
        except Exception as e:
            logger.error(f"Error caching response: {e}")
    
    def _generate_cache_key(self, request: Request, cache_config: Dict[str, Any]) -> str:
        """
        Generate a unique cache key for the request.
        
        Args:
            request: FastAPI request object
            cache_config: Cache configuration
            
        Returns:
            Unique cache key string
        """
        key_parts = ["wingman", "api"]
        
        # Add cache type
        key_parts.append(cache_config["cache_type"])
        
        # Add user ID if user-scoped
        if cache_config.get("user_scoped", False):
            user_id = self._extract_user_id(request)
            if user_id:
                key_parts.append(f"user:{user_id}")
        
        # Add path
        path = request.url.path.strip("/").replace("/", ":")
        key_parts.append(path)
        
        # Add query parameters (sorted for consistency)
        if request.query_params:
            query_string = "&".join(
                f"{k}={v}" for k, v in sorted(request.query_params.items())
            )
            query_hash = hashlib.md5(query_string.encode()).hexdigest()[:8]
            key_parts.append(f"q:{query_hash}")
        
        return ":".join(key_parts)
    
    def _extract_user_id(self, request: Request) -> Optional[str]:
        """
        Extract user ID from request for user-scoped caching.
        
        Args:
            request: FastAPI request object
            
        Returns:
            User ID string or None if not found
        """
        # Try to get user ID from various sources
        
        # 1. Path parameters
        if hasattr(request, 'path_params') and 'user_id' in request.path_params:
            return request.path_params['user_id']
        
        # 2. Query parameters
        if 'user_id' in request.query_params:
            return request.query_params['user_id']
        
        # 3. Authorization header (JWT token)
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            # Would need JWT parsing here in a real implementation
            # For now, just use a placeholder
            return "jwt_user"
        
        # 4. Custom user header
        user_id = request.headers.get("X-User-ID")
        if user_id:
            return user_id
        
        return None
    
    def _generate_etag(self, content: bytes) -> str:
        """
        Generate ETag for content.
        
        Args:
            content: Response content bytes
            
        Returns:
            ETag string
        """
        content_hash = hashlib.md5(content).hexdigest()
        return f'"{content_hash}"'
    
    async def _handle_cache_invalidation(self, request: Request) -> None:
        """
        Handle cache invalidation for endpoints that modify data.
        
        Args:
            request: FastAPI request object
        """
        endpoint_key = f"{request.method} {request.url.path}"
        
        if endpoint_key in self.cache_invalidating_endpoints:
            await self._invalidate_related_caches(request, endpoint_key)
    
    async def _invalidate_related_caches(self, request: Request, endpoint_key: str) -> None:
        """
        Invalidate caches that are affected by the current endpoint.
        
        Args:
            request: FastAPI request object
            endpoint_key: Key identifying the current endpoint
        """
        try:
            user_id = self._extract_user_id(request)
            patterns_to_invalidate = []
            
            # Find all cache configs that should be invalidated
            for path, config in self.cacheable_endpoints.items():
                if endpoint_key in config.get("invalidate_on", []):
                    if config.get("user_scoped", False) and user_id:
                        # User-specific invalidation
                        pattern = f"wingman:*:user:{user_id}:*"
                        patterns_to_invalidate.append(pattern)
                    else:
                        # Global invalidation for this cache type
                        cache_type = config["cache_type"]
                        pattern = f"wingman:*:{cache_type}:*"
                        patterns_to_invalidate.append(pattern)
            
            # Execute invalidations
            for pattern in patterns_to_invalidate:
                if await redis_service.health_check():
                    # Delete keys matching pattern
                    keys = await redis_service._client.keys(pattern)
                    if keys:
                        await redis_service._client.delete(*keys)
                        logger.info(f"Invalidated {len(keys)} cache entries for pattern: {pattern}")
        
        except Exception as e:
            logger.error(f"Error invalidating caches: {e}")

# Cache decorator for manual cache control
def cache_response(cache_type: str, ttl: int = 3600, user_scoped: bool = True):
    """
    Decorator for manual response caching.
    
    Args:
        cache_type: Type of cache for key generation
        ttl: Time to live in seconds
        user_scoped: Whether to scope cache to user
        
    Returns:
        Decorator function
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # This would need to be implemented based on the specific framework
            # For now, just call the original function
            return await func(*args, **kwargs)
        return wrapper
    return decorator

# Utility functions for cache management

async def invalidate_user_cache(user_id: str, cache_types: Optional[List[str]] = None) -> int:
    """
    Invalidate all cached data for a specific user.
    
    Args:
        user_id: User ID to invalidate caches for
        cache_types: Specific cache types to invalidate (all if None)
        
    Returns:
        Number of cache entries invalidated
    """
    try:
        if not await redis_service.health_check():
            return 0
        
        if cache_types:
            total_invalidated = 0
            for cache_type in cache_types:
                pattern = f"wingman:*:{cache_type}:user:{user_id}:*"
                keys = await redis_service._client.keys(pattern)
                if keys:
                    await redis_service._client.delete(*keys)
                    total_invalidated += len(keys)
            return total_invalidated
        else:
            # Invalidate all user caches
            pattern = f"wingman:*:user:{user_id}:*"
            keys = await redis_service._client.keys(pattern)
            if keys:
                await redis_service._client.delete(*keys)
                return len(keys)
            return 0
    
    except Exception as e:
        logger.error(f"Error invalidating user cache: {e}")
        return 0

async def invalidate_cache_type(cache_type: str) -> int:
    """
    Invalidate all cached data of a specific type.
    
    Args:
        cache_type: Type of cache to invalidate
        
    Returns:
        Number of cache entries invalidated
    """
    try:
        if not await redis_service.health_check():
            return 0
        
        pattern = f"wingman:*:{cache_type}:*"
        keys = await redis_service._client.keys(pattern)
        if keys:
            await redis_service._client.delete(*keys)
            logger.info(f"Invalidated {len(keys)} entries for cache type: {cache_type}")
            return len(keys)
        return 0
    
    except Exception as e:
        logger.error(f"Error invalidating cache type: {e}")
        return 0

async def get_cache_stats() -> Dict[str, Any]:
    """
    Get comprehensive cache performance statistics.
    
    Returns:
        Dictionary with cache performance metrics
    """
    redis_stats = await redis_service.get_stats()
    
    return {
        "redis_status": redis_stats,
        "cacheable_endpoints": len(CacheMiddleware(None).cacheable_endpoints),
        "cache_invalidating_endpoints": len(CacheMiddleware(None).cache_invalidating_endpoints),
        "middleware_active": True
    }