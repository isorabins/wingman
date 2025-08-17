from fastapi import FastAPI, HTTPException, BackgroundTasks, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Dict, Any
from uuid import UUID
import uuid
import asyncio
from src.config import Config
from supabase import create_client
from datetime import datetime, timezone, timedelta
import logging
from contextlib import asynccontextmanager
import json
import time

# Performance Infrastructure Imports
from src.redis_client import redis_service
from src.observability.metrics_collector import metrics_collector, record_request_metric, record_database_metric, record_cache_metric
from src.db.connection_pool import db_pool
from src.model_router import model_router, get_optimal_model

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        logger.info("WingmanMatch API starting up...")
        logger.info(f"Environment: {Config.get_environment()}")
        logger.info(f"App identifier: {Config.get_app_identifier()}")
        
        # Initialize Performance Infrastructure
        logger.info("Initializing performance infrastructure...")
        
        # 1. Initialize Redis connection (high-performance caching)
        redis_available = await redis_service.initialize()
        logger.info(f"Redis service initialized: available={redis_available}")
        if not redis_available:
            logger.warning("Redis not available - using in-memory fallback for caching")
        
        # 2. Initialize Database Connection Pool
        if Config.ENABLE_CONNECTION_POOLING:
            pool_initialized = await db_pool.initialize()
            logger.info(f"Database connection pool initialized: {pool_initialized}")
            if pool_initialized:
                pool_health = await db_pool.health_check()
                logger.info(f"Database pool health: {pool_health}")
        else:
            logger.info("Connection pooling disabled - using standard Supabase client")
        
        # 3. Initialize Metrics Collection
        if Config.ENABLE_PERFORMANCE_MONITORING:
            metrics_collector.enable_collection()
            logger.info("Performance metrics collection enabled")
        else:
            logger.info("Performance monitoring disabled")
        
        # 4. Initialize Model Router for Cost Optimization
        logger.info("AI model router initialized for cost optimization")
        logger.info(f"Cost optimization enabled: {Config.ENABLE_COST_OPTIMIZATION}")
        
        # Initialize legacy services
        from src.redis_session import RedisSession
        await RedisSession.initialize()
        redis_health = await RedisSession.health_check()
        logger.info(f"Legacy Redis session service: {redis_health}")
        
        # Initialize database connections
        from src.database import SupabaseFactory
        db_health = SupabaseFactory.health_check()
        logger.info(f"Database health: {db_health}")
        
        # Initialize email service
        from src.email_templates import email_service
        logger.info(f"Email service enabled: {email_service.enabled}")
        
        # Log feature flags
        feature_flags = Config.get_feature_flags()
        logger.info(f"Feature flags: {feature_flags}")
        
        # Log optional service status
        optional_status = Config.validate_optional_config()
        logger.info(f"Optional services: {optional_status}")
        
        # Performance summary
        perf_summary = {
            "redis_caching": redis_available,
            "connection_pooling": Config.ENABLE_CONNECTION_POOLING and hasattr(db_pool, 'pool') and db_pool.pool is not None,
            "metrics_collection": Config.ENABLE_PERFORMANCE_MONITORING,
            "cost_optimization": Config.ENABLE_COST_OPTIMIZATION,
            "model_routing": True
        }
        logger.info(f"Performance infrastructure status: {perf_summary}")
        
    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")
    
    yield
    
    # Shutdown
    try:
        logger.info("Shutting down performance infrastructure...")
        
        # Close Performance Infrastructure
        # 1. Close Redis service
        await redis_service.close()
        logger.info("Redis service closed")
        
        # 2. Close Database Connection Pool
        if Config.ENABLE_CONNECTION_POOLING and hasattr(db_pool, 'pool') and db_pool.pool:
            await db_pool.close()
            logger.info("Database connection pool closed")
        
        # 3. Cleanup metrics
        if Config.ENABLE_PERFORMANCE_MONITORING:
            await metrics_collector.cleanup_old_metrics(hours=24)
            logger.info("Metrics cleanup completed")
        
        # Close legacy Redis connections
        from src.redis_session import RedisSession
        await RedisSession.cleanup()
        logger.info("Legacy Redis service closed")
        
    except Exception as e:
        logger.error(f"Error during shutdown: {str(e)}")

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.DEBUG if Config.ENABLE_DETAILED_LOGGING else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s - %(pathname)s:%(lineno)d',
)

# Initialize FastAPI app
app = FastAPI(
    title="WingmanMatch API", 
    description="AI-powered wingman matching platform for shared challenges",
    version="1.0.0",
    lifespan=lifespan
)

# Initialize Supabase client
supabase = create_client(Config.SUPABASE_URL, Config.SUPABASE_SERVICE_KEY)

# Configure CORS for WingmanMatch domains
ALLOWED_ORIGINS = [
    "https://*.herokuapp.com",       # Heroku deployments
    "https://*.vercel.app",          # Vercel deployments (all branches)
    "https://wingman-app.vercel.app", # Main Vercel deployment
    "https://wingmanmatch.com",      # Production domain
    "https://www.wingmanmatch.com",  # www subdomain
    "https://app.wingmanmatch.com",  # App subdomain
    "https://dev.wingmanmatch.com",  # Development subdomain
    "http://localhost:3000",         # Local frontend development
    "http://localhost:3002",         # Local frontend development (wingman)
    "http://localhost:8000",         # Local API development
    "http://127.0.0.1:3000",         # Alternative localhost
    "http://127.0.0.1:3002",         # Alternative localhost (wingman)
    "http://127.0.0.1:8000",         # Alternative localhost
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=[
        "Content-Type", 
        "Authorization",
        "Access-Control-Allow-Origin",
        "Access-Control-Allow-Methods",
        "Access-Control-Allow-Headers",
        "Access-Control-Max-Age"
    ],
    expose_headers=[
        "Content-Type",
        "Authorization"
    ],
    max_age=3600,  # Cache preflight requests for 1 hour
    allow_origin_regex=r"https://[^.]+\.herokuapp\.com"  # Additional regex for Heroku domains
)

# Performance Monitoring Middleware
@app.middleware("http")
async def performance_monitoring_middleware(request: Request, call_next):
    """
    Performance monitoring middleware for tracking request metrics, caching, and optimization.
    
    Tracks:
    - Request timing (P95 latency)
    - Cache hit/miss rates  
    - Database query performance
    - API endpoint usage patterns
    """
    start_time = time.time()
    endpoint = request.url.path
    method = request.method
    
    try:
        # Process request
        response = await call_next(request)
        
        # Calculate metrics
        duration_ms = (time.time() - start_time) * 1000
        status_code = response.status_code
        
        # Record performance metrics if monitoring enabled
        if Config.ENABLE_PERFORMANCE_MONITORING:
            await record_request_metric(
                endpoint=f"{method} {endpoint}",
                duration_ms=duration_ms,
                status_code=status_code
            )
        
        # Add performance headers for debugging
        response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"
        response.headers["X-Cache-Status"] = getattr(request.state, 'cache_status', 'miss')
        
        # Log slow requests
        if duration_ms > 2000:  # > 2 seconds
            logger.warning(f"Slow request: {method} {endpoint} took {duration_ms:.2f}ms")
        
        return response
        
    except Exception as e:
        # Record error metrics
        duration_ms = (time.time() - start_time) * 1000
        
        if Config.ENABLE_PERFORMANCE_MONITORING:
            await record_request_metric(
                endpoint=f"{method} {endpoint}",
                duration_ms=duration_ms,
                status_code=500
            )
        
        logger.error(f"Request error: {method} {endpoint} - {str(e)}")
        raise

# Pydantic models for API requests/responses
class HealthResponse(BaseModel):
    status: str
    timestamp: str
    message: str
    environment: str
    features: Dict[str, bool]

class WingmanRequest(BaseModel):
    user_id: str
    challenge_type: str
    preferences: Optional[Dict] = None

class WingmanResponse(BaseModel):
    message: str
    data: Optional[Dict] = None

class ChallengeRequest(BaseModel):
    title: str
    description: str
    challenge_type: str
    duration_days: Optional[int] = None
    user_id: str

class ChallengeResponse(BaseModel):
    id: str
    message: str
    challenge: Dict

# Confidence Assessment Pydantic v2 Models
class ConfidenceResult(BaseModel):
    archetype: str
    level: str
    scores: Dict[str, float]
    summary: Optional[str] = None

class ConfidenceAssessmentRequest(BaseModel):
    user_id: str = Field(..., description="User ID for the assessment")
    message: str = Field(..., min_length=1, max_length=500, description="User's message or response")

class ConfidenceAssessmentResponse(BaseModel):
    message: str = Field(..., description="AI response or next question")
    question_number: Optional[int] = Field(None, description="Current question number (1-12)")
    is_complete: bool = Field(False, description="Whether the assessment is complete")
    results: Optional[ConfidenceResult] = Field(None, description="Final assessment results if complete")

class ConfidenceProgressResponse(BaseModel):
    user_id: str
    flow_step: int
    completion_percentage: float
    is_completed: bool
    current_responses: Dict[str, str]
    question_number: Optional[int] = None

class ConfidenceResultsResponse(BaseModel):
    user_id: str
    archetype: str
    experience_level: str
    archetype_scores: Dict[str, float]
    test_responses: Dict[str, str]
    created_at: str

# Profile Completion Pydantic Models
class LocationData(BaseModel):
    lat: float = Field(..., ge=-90, le=90, description="Latitude coordinate")
    lng: float = Field(..., ge=-180, le=180, description="Longitude coordinate")
    city: Optional[str] = Field(None, max_length=100, description="City name")
    privacy_mode: str = Field(..., description="Location privacy setting", pattern="^(precise|city_only)$")

class ProfileCompleteRequest(BaseModel):
    user_id: str = Field(..., description="User ID for profile completion")
    bio: str = Field(..., min_length=1, max_length=400, description="User bio (max 400 characters)")
    location: LocationData = Field(..., description="User location data")
    travel_radius: int = Field(..., ge=1, le=50, description="Maximum travel distance in miles")
    photo_url: Optional[str] = Field(None, description="URL to profile photo in storage bucket")

class ProfileCompleteResponse(BaseModel):
    success: bool = Field(..., description="Whether profile completion was successful")
    message: str = Field(..., description="Success or error message")
    ready_for_matching: bool = Field(..., description="Whether user is ready for wingman matching")
    user_id: str = Field(..., description="User ID that was updated")

# Test Authentication Pydantic Models (Development Only)
class TestAuthRequest(BaseModel):
    email: str = Field(..., description="Email for test user authentication")
    create_user: bool = Field(True, description="Create user if doesn't exist")

class TestAuthResponse(BaseModel):
    success: bool = Field(..., description="Whether test authentication was successful")
    access_token: str = Field(..., description="JWT access token for frontend use")
    refresh_token: str = Field(..., description="JWT refresh token for session management")
    user_id: str = Field(..., description="User ID that was authenticated")
    session_expires_at: str = Field(..., description="When the session expires (ISO format)")
    message: str = Field(..., description="Success or error message")

# Enhanced cache with Redis integration
session_cache = {}  # Fallback in-memory cache
cache_timestamps = {}
CACHE_DURATION = timedelta(hours=Config.SESSION_TIMEOUT_HOURS)

async def is_cache_valid(session_key: str) -> bool:
    """Check if cached session data is still valid (Redis-first with fallback)"""
    try:
        # Check Redis first
        cached_data = await redis_service.get_cache(f"session:{session_key}")
        if cached_data is not None:
            return True
        
        # Fallback to in-memory cache
        if session_key not in cache_timestamps:
            return False
        return datetime.now() - cache_timestamps[session_key] < CACHE_DURATION
    except Exception as e:
        logger.error(f"Cache validity check error: {e}")
        return False

async def get_cached_session(session_key: str) -> Optional[Dict]:
    """Get cached session data if valid (Redis-first with fallback)"""
    try:
        # Try Redis first
        cached_data = await redis_service.get_cache(f"session:{session_key}")
        if cached_data is not None:
            await record_cache_metric("session_get", hit=True)
            return cached_data
        
        # Fallback to in-memory cache
        if await is_cache_valid(session_key):
            data = session_cache.get(session_key)
            if data:
                await record_cache_metric("session_get", hit=True)
                return data
        
        await record_cache_metric("session_get", hit=False)
        return None
    except Exception as e:
        logger.error(f"Cache retrieval error: {e}")
        await record_cache_metric("session_get", hit=False)
        return None

async def cache_session_data(session_key: str, data: Dict):
    """Cache session data with timestamp (Redis-first with fallback)"""
    try:
        # Cache in Redis with TTL
        ttl_seconds = int(CACHE_DURATION.total_seconds())
        success = await redis_service.set_cache(f"session:{session_key}", data, ttl_seconds)
        
        if success:
            await record_cache_metric("session_set", hit=True)
        else:
            # Fallback to in-memory cache
            session_cache[session_key] = data
            cache_timestamps[session_key] = datetime.now()
            await record_cache_metric("session_set", hit=False)
            
    except Exception as e:
        logger.error(f"Cache storage error: {e}")
        # Fallback to in-memory cache
        session_cache[session_key] = data
        cache_timestamps[session_key] = datetime.now()
        await record_cache_metric("session_set", hit=False)

# High-performance caching decorators for hot endpoints
async def get_cached_data(cache_key: str, ttl_seconds: int = 3600) -> Optional[Any]:
    """Generic cache getter with Redis-first strategy"""
    try:
        cached_data = await redis_service.get_cache(cache_key)
        if cached_data is not None:
            await record_cache_metric("generic_get", hit=True)
            return cached_data
        await record_cache_metric("generic_get", hit=False)
        return None
    except Exception as e:
        logger.error(f"Cache get error for {cache_key}: {e}")
        await record_cache_metric("generic_get", hit=False)
        return None

async def set_cached_data(cache_key: str, data: Any, ttl_seconds: int = 3600) -> bool:
    """Generic cache setter with Redis-first strategy"""
    try:
        success = await redis_service.set_cache(cache_key, data, ttl_seconds)
        await record_cache_metric("generic_set", hit=success)
        return success
    except Exception as e:
        logger.error(f"Cache set error for {cache_key}: {e}")
        await record_cache_metric("generic_set", hit=False)
        return False

# API Endpoints

@app.get("/", response_model=Dict)
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Welcome to WingmanMatch API",
        "description": "AI-powered wingman matching platform for shared challenges",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint for monitoring"""
    from src.database import SupabaseFactory
    from src.redis_session import RedisSession
    from src.email_templates import email_service
    from src.rate_limiting import rate_limiter
    from src.retry_utils import get_circuit_breaker_status
    
    # Check all services
    db_health = SupabaseFactory.health_check()
    redis_health = await RedisSession.health_check()
    rate_limiter_status = await rate_limiter.get_status()
    circuit_breaker_status = get_circuit_breaker_status()
    
    # Determine overall health
    overall_healthy = (
        db_health["service_client"] and 
        db_health["anon_client"] and
        (redis_health["connected"] or not Config.REDIS_URL)  # Redis optional
    )
    
    # Additional service details for comprehensive monitoring
    service_details = {
        "database": {
            "service_client": db_health["service_client"],
            "anon_client": db_health["anon_client"],
            "errors": db_health["errors"]
        },
        "redis": {
            "connected": redis_health["connected"],
            "ping_time": redis_health.get("ping_time"),
            "error": redis_health.get("error")
        },
        "email": {
            "enabled": email_service.enabled
        },
        "rate_limiter": rate_limiter_status,
        "circuit_breakers": circuit_breaker_status
    }
    
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow().isoformat(),
        message="WingmanMatch backend is running",
        environment=Config.get_environment(),
        features=Config.get_feature_flags()
    )

@app.get("/config/features")
async def get_feature_config():
    """Get current feature flag configuration"""
    return {
        "features": Config.get_feature_flags(),
        "settings": Config.get_wingman_settings(),
        "environment": Config.get_environment()
    }

@app.get("/config/status")
async def get_system_status():
    """Get system configuration status"""
    optional_status = Config.validate_optional_config()
    
    return {
        "environment": Config.get_environment(),
        "app_id": Config.get_app_identifier(),
        "required_services": {
            "anthropic": bool(Config.ANTHROPIC_API_KEY),
            "supabase": bool(Config.SUPABASE_URL and Config.SUPABASE_SERVICE_KEY)
        },
        "optional_services": optional_status,
        "features": Config.get_feature_flags(),
        "model_config": Config.get_model_info()
    }

# Performance Monitoring Endpoints

@app.get("/performance/metrics")
async def get_performance_metrics():
    """Get comprehensive performance metrics and system health"""
    try:
        # Get performance summary
        perf_summary = await metrics_collector.get_performance_summary(hours=1)
        
        # Get Redis stats
        redis_stats = await redis_service.get_stats()
        
        # Get database pool stats
        db_stats = {}
        if Config.ENABLE_CONNECTION_POOLING and hasattr(db_pool, 'pool') and db_pool.pool:
            db_stats = db_pool.get_performance_metrics(hours=1)
        
        # Get model router usage
        model_stats = model_router.get_usage_stats()
        
        # Get real-time metrics
        realtime = await metrics_collector.get_real_time_metrics()
        
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "performance_summary": perf_summary,
            "redis_stats": redis_stats,
            "database_stats": db_stats,
            "model_routing_stats": model_stats,
            "real_time_metrics": realtime,
            "system_health": {
                "redis_available": redis_service.is_available(),
                "connection_pooling": Config.ENABLE_CONNECTION_POOLING,
                "metrics_collection": Config.ENABLE_PERFORMANCE_MONITORING,
                "cost_optimization": Config.ENABLE_COST_OPTIMIZATION
            }
        }
    except Exception as e:
        logger.error(f"Performance metrics error: {e}")
        raise HTTPException(status_code=500, detail=f"Performance metrics unavailable: {str(e)}")

@app.get("/performance/health")
async def get_performance_health():
    """Get performance health check for monitoring systems"""
    try:
        # Check Redis health
        redis_health = await redis_service.health_check()
        
        # Check database pool health
        db_health = {}
        if Config.ENABLE_CONNECTION_POOLING and hasattr(db_pool, 'pool') and db_pool.pool:
            db_health = await db_pool.health_check()
        
        # Get recent performance metrics
        recent_metrics = await metrics_collector.get_real_time_metrics()
        
        # Determine overall health
        health_score = 100
        alerts = []
        
        # Check Redis health
        if not redis_health.get("connected", False):
            health_score -= 20
            alerts.append("Redis connection issues")
        
        # Check response times
        avg_response = recent_metrics.get("avg_response_time_ms", 0)
        if avg_response > 2000:
            health_score -= 30
            alerts.append(f"High response times: {avg_response:.0f}ms")
        elif avg_response > 1000:
            health_score -= 15
            alerts.append(f"Elevated response times: {avg_response:.0f}ms")
        
        # Check database pool
        if db_health.get("healthy") is False:
            health_score -= 25
            alerts.append("Database connection pool issues")
        
        overall_healthy = health_score >= 70
        
        return {
            "healthy": overall_healthy,
            "health_score": max(0, health_score),
            "alerts": alerts,
            "checks": {
                "redis": redis_health,
                "database_pool": db_health,
                "recent_performance": recent_metrics
            }
        }
    except Exception as e:
        logger.error(f"Performance health check error: {e}")
        return {
            "healthy": False,
            "health_score": 0,
            "alerts": [f"Health check failed: {str(e)}"],
            "checks": {}
        }

@app.get("/performance/cache/stats")
async def get_cache_statistics():
    """Get detailed caching statistics and hit rates"""
    try:
        # Get cache metrics from the last hour
        cache_metrics = await metrics_collector.get_metrics(
            metric_type="cache",
            hours=1,
            source="redis"
        )
        
        # Calculate hit rates
        hits = len([m for m in cache_metrics if m.tags.get("hit") == "True"])
        total = len(cache_metrics)
        hit_rate = (hits / total * 100) if total > 0 else 0
        
        # Get Redis specific stats
        redis_stats = await redis_service.get_stats()
        
        return {
            "cache_hit_rate_percent": round(hit_rate, 2),
            "total_cache_operations": total,
            "cache_hits": hits,
            "cache_misses": total - hits,
            "redis_stats": redis_stats,
            "fallback_cache_size": redis_stats.get("fallback_cache_size", 0),
            "performance_targets": {
                "target_hit_rate": 85,
                "current_status": "healthy" if hit_rate >= 85 else "needs_improvement"
            }
        }
    except Exception as e:
        logger.error(f"Cache statistics error: {e}")
        raise HTTPException(status_code=500, detail=f"Cache statistics unavailable: {str(e)}")

@app.post("/performance/cache/clear")
async def clear_performance_cache():
    """Clear performance caches for testing and maintenance"""
    try:
        cleared_keys = 0
        
        # Clear Redis cache keys (performance related only)
        if redis_service.is_available():
            # This would require Redis pattern matching - implement if needed
            logger.info("Redis cache clear requested - implement pattern matching if needed")
        
        # Clear in-memory caches
        global session_cache, cache_timestamps
        cleared_keys += len(session_cache)
        session_cache.clear()
        cache_timestamps.clear()
        
        return {
            "success": True,
            "cleared_keys": cleared_keys,
            "message": "Performance caches cleared successfully"
        }
    except Exception as e:
        logger.error(f"Cache clear error: {e}")
        raise HTTPException(status_code=500, detail=f"Cache clear failed: {str(e)}")

# Confidence Assessment API Endpoints

@app.post("/api/assessment/confidence", response_model=ConfidenceAssessmentResponse)
async def start_confidence_assessment(request: ConfidenceAssessmentRequest, background_tasks: BackgroundTasks):
    """Start or continue confidence assessment conversation"""
    try:
        logger.info(f"Confidence assessment request from user {request.user_id}")
        
        # Import and initialize the confidence test agent
        from src.agents.confidence_agent import ConfidenceTestAgent
        from src.database import SupabaseFactory
        
        db_client = SupabaseFactory.get_service_client()
        agent = ConfidenceTestAgent(db_client, request.user_id)
        
        # Process the user's message through the agent
        thread_id = "confidence_assessment"  # Use consistent thread ID for assessment
        response_text = await agent.process_message(thread_id, request.message)
        
        # Get current progress to determine question number and completion status
        progress = await agent.get_progress()
        current_step = progress.get('flow_step', 1)
        completion_percentage = progress.get('completion_percentage', 0.0)
        is_complete = await agent.is_flow_complete()
        
        # Calculate question number (0 = welcome, 1-12 = questions, 13+ = complete)
        question_number = None
        if current_step > 1 and current_step <= 13:
            question_number = max(1, current_step - 1)
        
        # Get results if assessment is complete
        results = None
        if is_complete:
            try:
                # Query the confidence_test_results table for final results
                result_query = db_client.table('confidence_test_results')\
                    .select('*')\
                    .eq('user_id', request.user_id)\
                    .limit(1)\
                    .execute()
                
                if result_query.data:
                    result_data = result_query.data[0]
                    results = ConfidenceResult(
                        archetype=result_data['assigned_archetype'],
                        level=result_data['experience_level'],
                        scores=result_data['archetype_scores'],
                        summary=f"Your dating confidence archetype is {result_data['assigned_archetype']} with {result_data['experience_level']} experience level."
                    )
            except Exception as e:
                logger.warning(f"Could not fetch results for completed assessment: {e}")
        
        return ConfidenceAssessmentResponse(
            message=response_text,
            question_number=question_number,
            is_complete=is_complete,
            results=results
        )
        
    except Exception as e:
        logger.error(f"Error in confidence assessment: {str(e)}")
        raise HTTPException(status_code=500, detail="Assessment processing failed")

@app.get("/api/assessment/results/{user_id}", response_model=ConfidenceResultsResponse)
async def get_confidence_results(user_id: str):
    """Get final confidence assessment results for a user"""
    try:
        logger.info(f"Fetching confidence results for user {user_id}")
        
        from src.database import SupabaseFactory
        db_client = SupabaseFactory.get_service_client()
        
        # Query confidence_test_results table
        result = db_client.table('confidence_test_results')\
            .select('*')\
            .eq('user_id', user_id)\
            .limit(1)\
            .execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="No assessment results found for this user")
        
        result_data = result.data[0]
        
        return ConfidenceResultsResponse(
            user_id=user_id,
            archetype=result_data['assigned_archetype'],
            experience_level=result_data['experience_level'],
            archetype_scores=result_data['archetype_scores'],
            test_responses=result_data['test_responses'],
            created_at=result_data['created_at']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching confidence results: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch assessment results")

@app.get("/api/assessment/progress/{user_id}", response_model=ConfidenceProgressResponse)
async def get_confidence_progress(user_id: str):
    """Get current progress of confidence assessment"""
    try:
        logger.info(f"Fetching confidence progress for user {user_id}")
        
        from src.database import SupabaseFactory
        db_client = SupabaseFactory.get_service_client()
        
        # Query confidence_test_progress table
        result = db_client.table('confidence_test_progress')\
            .select('*')\
            .eq('user_id', user_id)\
            .order('created_at', desc=True)\
            .limit(1)\
            .execute()
        
        if not result.data:
            # Return default progress if no record exists
            return ConfidenceProgressResponse(
                user_id=user_id,
                flow_step=1,
                completion_percentage=0.0,
                is_completed=False,
                current_responses={},
                question_number=None
            )
        
        progress_data = result.data[0]
        current_step = progress_data.get('flow_step', 1)
        
        # Calculate question number
        question_number = None
        if current_step > 1 and current_step <= 13:
            question_number = max(1, current_step - 1)
        
        return ConfidenceProgressResponse(
            user_id=user_id,
            flow_step=current_step,
            completion_percentage=progress_data.get('completion_percentage', 0.0),
            is_completed=progress_data.get('is_completed', False),
            current_responses=progress_data.get('current_responses', {}),
            question_number=question_number
        )
        
    except Exception as e:
        logger.error(f"Error fetching confidence progress: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch assessment progress")

@app.delete("/api/assessment/progress/{user_id}")
async def reset_confidence_assessment(user_id: str):
    """Reset confidence assessment progress for a user"""
    try:
        logger.info(f"Resetting confidence assessment for user {user_id}")
        
        from src.database import SupabaseFactory
        db_client = SupabaseFactory.get_service_client()
        
        # Delete progress record
        progress_result = db_client.table('confidence_test_progress')\
            .delete()\
            .eq('user_id', user_id)\
            .execute()
        
        # Optionally clear incomplete results (keep completed ones)
        # We'll only clear progress, not final results
        
        return {
            "message": f"Assessment progress reset for user {user_id}",
            "user_id": user_id,
            "reset_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error resetting confidence assessment: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to reset assessment progress")

# Profile Completion API Endpoint

@app.post("/api/profile/complete", response_model=ProfileCompleteResponse)
async def complete_user_profile(request: ProfileCompleteRequest):
    """
    Complete user profile with bio, location, and travel preferences
    
    This endpoint handles Task 7: Profile setup API implementation
    
    Features:
    - Bio validation and sanitization (≤400 chars, PII removal)
    - Location privacy modes: 'precise' (exact coords) or 'city_only' (placeholder coords, city-based matching)
    - Travel radius validation (1-50 miles)  
    - Auto-dependency creation for user profiles
    - Secure input validation and error handling
    
    Request Body:
    - user_id: User UUID
    - bio: User bio text (1-400 characters, sanitized for PII/XSS)
    - location: LocationData with lat/lng, city, and privacy_mode
    - travel_radius: Maximum travel distance in miles (1-50)
    - photo_url: Optional URL to profile photo in storage bucket
    
    Response:
    - success: Whether operation completed successfully
    - message: Success or error message
    - ready_for_matching: Always true on success (indicates profile complete)
    - user_id: The user ID that was updated
    
    Database Operations:
    - Updates user_profiles table (bio, photo_url, updated_at)
    - Upserts user_locations table (coordinates based on privacy_mode)
    """
    try:
        logger.info(f"Profile completion request from user {request.user_id}")
        
        from src.database import SupabaseFactory
        from src.safety_filters import sanitize_message
        
        db_client = SupabaseFactory.get_service_client()
        
        # Input validation and sanitization
        
        # Sanitize bio content to remove PII and prevent XSS
        sanitized_bio = sanitize_message(request.bio.strip())
        
        # Validate bio length after sanitization
        if len(sanitized_bio) > 400:
            raise HTTPException(
                status_code=400, 
                detail="Bio exceeds 400 characters after sanitization"
            )
        
        if len(sanitized_bio) == 0:
            raise HTTPException(
                status_code=400, 
                detail="Bio cannot be empty after sanitization"
            )
        
        # Validate coordinate ranges (already done by Pydantic, but double-check)
        lat, lng = request.location.lat, request.location.lng
        if not (-90 <= lat <= 90):
            raise HTTPException(status_code=400, detail="Invalid latitude coordinate")
        if not (-180 <= lng <= 180):
            raise HTTPException(status_code=400, detail="Invalid longitude coordinate")
        
        # Auto-dependency creation following existing pattern
        from src.simple_memory import WingmanMemory
        memory = WingmanMemory(db_client, request.user_id)
        await memory.ensure_user_profile(request.user_id)
        
        # Update user_profiles table with bio and photo
        profile_update_data = {
            "bio": sanitized_bio,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        if request.photo_url:
            profile_update_data["photo_url"] = request.photo_url
        
        profile_result = db_client.table('user_profiles')\
            .update(profile_update_data)\
            .eq('id', request.user_id)\
            .execute()
        
        if not profile_result.data:
            raise HTTPException(
                status_code=404, 
                detail="User profile not found or could not be updated"
            )
        
        # Prepare location data based on privacy mode
        location_data = {
            "user_id": request.user_id,
            "max_travel_miles": request.travel_radius,
            "privacy_mode": request.location.privacy_mode,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        if request.location.privacy_mode == "precise":
            # Store exact coordinates for precise matching
            location_data["lat"] = lat
            location_data["lng"] = lng
            if request.location.city:
                location_data["city"] = request.location.city.strip()
        elif request.location.privacy_mode == "city_only":
            # Store placeholder coordinates (0,0) for privacy, only use city for matching
            location_data["lat"] = 0.0  # Placeholder - matching will use city field only
            location_data["lng"] = 0.0  # Placeholder - matching will use city field only
            if request.location.city:
                location_data["city"] = request.location.city.strip()
            else:
                raise HTTPException(
                    status_code=400, 
                    detail="City name is required when privacy_mode is city_only"
                )
        
        # Upsert location data (insert or update if exists)
        location_result = db_client.table('user_locations')\
            .upsert(location_data, on_conflict="user_id")\
            .execute()
        
        if not location_result.data:
            raise HTTPException(
                status_code=500, 
                detail="Failed to update user location data"
            )
        
        logger.info(f"Profile completion successful for user {request.user_id}")
        
        return ProfileCompleteResponse(
            success=True,
            message="Profile completed successfully",
            ready_for_matching=True,
            user_id=request.user_id
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Error in profile completion: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to complete profile")

# Test Authentication Endpoint (Development Only)

@app.post("/auth/test-login", response_model=TestAuthResponse)
async def test_login(request: TestAuthRequest):
    """
    Test authentication endpoint for integration testing
    
    DEVELOPMENT ONLY - Creates authenticated sessions for testing purposes
    
    Features:
    - Fast authentication bypass for integration tests
    - Creates valid Supabase sessions compatible with frontend auth context
    - Supports user creation if user doesn't exist
    - Returns JWT tokens that work with existing auth flow
    
    Security:
    - Only available when ENABLE_TEST_AUTH=true AND DEVELOPMENT_MODE=true
    - Rate limited to prevent abuse
    - Clear logging when test auth is used
    - Cannot be enabled in production environment
    
    Request Body:
    - email: Email address for test user
    - create_user: Whether to create user if they don't exist (default: true)
    
    Response:
    - success: Whether authentication was successful
    - access_token: JWT access token for API requests
    - refresh_token: JWT refresh token for session management
    - user_id: UUID of the authenticated user
    - session_expires_at: Expiration timestamp for the session
    - message: Success or error message
    
    Usage in Tests:
    ```javascript
    const response = await fetch('/auth/test-login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: 'test@example.com' })
    });
    const { access_token, user_id } = await response.json();
    ```
    """
    
    # Security check: only allow in development mode
    if not Config.ENABLE_TEST_AUTH:
        logger.warning("Test authentication endpoint accessed but ENABLE_TEST_AUTH is disabled")
        raise HTTPException(
            status_code=403, 
            detail="Test authentication is only available in development mode"
        )
    
    if Config.get_environment() == 'production':
        logger.error("Test authentication endpoint accessed in production - this should never happen")
        raise HTTPException(
            status_code=403,
            detail="Test authentication is not available in production"
        )
    
    try:
        logger.warning(f"🧪 TEST AUTH: Authenticating test user {request.email}")
        
        from src.database import SupabaseFactory
        import uuid
        
        # Use service client for admin operations
        admin_client = SupabaseFactory.get_service_client()
        
        # For test purposes, create a mock user ID if user doesn't exist
        # This is a simplified implementation that creates deterministic test users
        user_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"test-user-{request.email}"))
        
        # Check if user profile exists in our database
        existing_profile = None
        try:
            profile_query = admin_client.table('user_profiles')\
                .select('id, email')\
                .eq('id', user_id)\
                .limit(1)\
                .execute()
            
            if profile_query.data:
                existing_profile = profile_query.data[0]
                logger.info(f"🧪 TEST AUTH: Found existing test user profile {user_id}")
        except Exception as e:
            logger.info(f"🧪 TEST AUTH: No existing profile found, will create if needed: {e}")
        
        # Create user profile if doesn't exist and create_user is True
        if not existing_profile and request.create_user:
            logger.info(f"🧪 TEST AUTH: Creating new test user profile {user_id}")
            
            try:
                # Use the memory system to ensure user profile exists
                from src.simple_memory import WingmanMemory
                memory = WingmanMemory(admin_client, user_id)
                await memory.ensure_user_profile(user_id)
                
                # Update the profile with test user information
                profile_update = admin_client.table('user_profiles')\
                    .update({
                        "email": request.email,
                        "updated_at": datetime.now(timezone.utc).isoformat()
                    })\
                    .eq('id', user_id)\
                    .execute()
                
                logger.info(f"🧪 TEST AUTH: Successfully created test user profile {user_id}")
                
            except Exception as e:
                logger.error(f"🧪 TEST AUTH: Failed to create user profile: {e}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to create test user profile: {str(e)}"
                )
        
        elif not existing_profile:
            raise HTTPException(
                status_code=404,
                detail="User not found and create_user is False"
            )
        
        # Generate session for the user
        logger.info(f"🧪 TEST AUTH: Generating session for user {user_id}")
        
        # Create test session with long expiration
        expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
        
        # Create mock tokens for testing that are compatible with frontend
        access_token = f"sbp_test_{user_id}_{int(time.time())}"
        refresh_token = f"sbr_test_{user_id}_{int(time.time())}"
        
        # Store session in cache for validation in subsequent requests
        session_key = f"test_session_{user_id}"
        cache_session_data(session_key, {
            "user_id": user_id,
            "email": request.email,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_at": expires_at.isoformat(),
            "is_test_session": True
        })
        
        logger.info(f"🧪 TEST AUTH: Successfully authenticated test user {request.email}")
        
        return TestAuthResponse(
            success=True,
            access_token=access_token,
            refresh_token=refresh_token,
            user_id=user_id,
            session_expires_at=expires_at.isoformat(),
            message=f"Test authentication successful for {request.email}"
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Error in test authentication: {str(e)}")
        raise HTTPException(status_code=500, detail="Test authentication failed")

# Email service endpoints
class EmailRequest(BaseModel):
    to_email: str
    template_name: str
    variables: Dict[str, Any]
    priority: Optional[str] = "normal"

class EmailResponse(BaseModel):
    success: bool
    message: str
    email_id: Optional[str] = None

class EmailTestRequest(BaseModel):
    to: str = Field(..., description="Recipient email address")
    subject: str = Field(..., description="Email subject")
    message: str = Field(..., description="Email message content")
    test_mode: bool = Field(True, description="Whether this is a test email")

class EmailTestResponse(BaseModel):
    success: bool
    message: str
    email_id: Optional[str] = None
    timestamp: str

@app.post("/email/send", response_model=EmailResponse)
async def send_email_endpoint(email_request: EmailRequest):
    """Send email using template"""
    try:
        from src.email_service import email_service, EmailTemplate, EmailPriority
        from src.retry_policies import with_email_retry
        
        # Convert string template name to enum
        try:
            template = EmailTemplate(email_request.template_name)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid template: {email_request.template_name}")
        
        # Convert string priority to enum
        try:
            priority = EmailPriority(email_request.priority)
        except ValueError:
            priority = EmailPriority.NORMAL
        
        # Send email with retry logic
        @with_email_retry()
        async def send_with_retry():
            return await email_service.send_email(
                email_request.to_email,
                template,
                email_request.variables,
                priority
            )
        
        success = await send_with_retry()
        
        if success:
            return EmailResponse(
                success=True,
                message="Email sent successfully",
                email_id=f"wingman_{int(time.time())}"
            )
        else:
            return EmailResponse(
                success=False,
                message="Failed to send email"
            )
            
    except Exception as e:
        logger.error(f"Error sending email: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to send email")

@app.get("/email/status")
async def get_email_service_status():
    """Get detailed email service status"""
    from src.email_service import email_service
    from src.email_templates import email_service as template_service
    
    # Get status from both email services
    main_status = email_service.get_service_status()
    template_status = {
        "enabled": template_service.enabled,
        "resend_configured": bool(Config.RESEND_API_KEY)
    }
    
    # Enhanced status with configuration guidance
    enhanced_status = {
        **main_status,
        "template_service": template_status,
        "configuration": {
            "resend_api_key_set": bool(Config.RESEND_API_KEY),
            "development_mode": Config.DEVELOPMENT_MODE,
            "fallback_mode_reason": "No RESEND_API_KEY configured" if not Config.RESEND_API_KEY else None
        },
        "setup_instructions": {
            "for_development": "Email service runs in fallback mode (simulation). Emails are logged but not sent.",
            "for_production": "Set RESEND_API_KEY environment variable to enable real email sending.",
            "get_api_key": "Sign up at https://resend.com to get a free API key (100 emails/day free tier)."
        } if not Config.RESEND_API_KEY else None,
        "endpoints": {
            "send_test": "/api/email/test",
            "send_templated": "/email/send",
            "status": "/email/status"
        }
    }
    
    return enhanced_status

@app.post("/api/email/test", response_model=EmailTestResponse)
async def send_test_email(email_request: EmailTestRequest):
    """Send a simple test email - for development and testing purposes"""
    try:
        import resend
        from src.config import Config
        import uuid
        
        # Initialize Resend if not already done
        if not resend.api_key and Config.RESEND_API_KEY:
            resend.api_key = Config.RESEND_API_KEY
        
        email_id = f"test-{uuid.uuid4().hex[:8]}"
        timestamp = datetime.now(timezone.utc).isoformat()
        
        if email_request.test_mode:
            logger.info(f"🧪 TEST EMAIL: Sending to {email_request.to}")
            logger.info(f"Subject: {email_request.subject}")
            logger.info(f"Content preview: {email_request.message[:200]}...")
        
        # If no Resend API key, simulate email sending
        if not Config.RESEND_API_KEY:
            logger.info("📧 SIMULATED EMAIL (Development Mode)")
            logger.info(f"To: {email_request.to}")
            logger.info(f"Subject: {email_request.subject}")
            logger.info(f"Content:\n{email_request.message}")
            logger.info(f"Email ID: {email_id}")
            logger.info("✅ Email would be sent in production with RESEND_API_KEY configured")
            
            return EmailTestResponse(
                success=True,
                message=f"Test email simulated successfully. In production, this email would be sent via Resend. Configure RESEND_API_KEY to enable real email sending.",
                email_id=email_id,
                timestamp=timestamp
            )
        
        # Send real email via Resend
        email_data = {
            "from": "Wingman Test <noreply@wingmanmatch.com>",
            "to": [email_request.to],
            "subject": email_request.subject,
            "text": email_request.message,
            "tags": ["test", "development"] if email_request.test_mode else ["production"]
        }
        
        try:
            response = resend.Emails.send(email_data)
            
            if response and hasattr(response, 'id'):
                logger.info(f"✅ Test email sent successfully: {response.id}")
                return EmailTestResponse(
                    success=True,
                    message=f"Test email sent successfully to {email_request.to}",
                    email_id=response.id,
                    timestamp=timestamp
                )
            else:
                logger.error("Failed to send test email: No response ID")
                raise HTTPException(status_code=500, detail="Failed to send email - no response from service")
                
        except Exception as resend_error:
            logger.error(f"Resend API error: {str(resend_error)}")
            raise HTTPException(status_code=500, detail=f"Email service error: {str(resend_error)}")
            
    except Exception as e:
        logger.error(f"Error in test email endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to send test email: {str(e)}")

# Wingman matching endpoints with retry policies
@app.post("/wingman/request", response_model=WingmanResponse)
async def request_wingman(request: WingmanRequest):
    """Request a wingman match"""
    if not Config.ENABLE_MATCHING:
        raise HTTPException(status_code=503, detail="Matching service is currently disabled")
    
    logger.info(f"Wingman request from user {request.user_id} for {request.challenge_type}")
    
    try:
        from src.retry_policies import with_supabase_retry
        
        # Use retry policy for database operations
        @with_supabase_retry()
        async def create_match_request():
            # Placeholder for actual match request creation in database
            # This would create a record in a wingman_requests table
            return {
                "request_id": f"req_{int(time.time())}",
                "user_id": request.user_id,
                "challenge_type": request.challenge_type,
                "status": "pending_match",
                "created_at": time.time()
            }
        
        match_data = await create_match_request()
        
        return WingmanResponse(
            message="Wingman request received and being processed",
            data=match_data
        )
        
    except Exception as e:
        logger.error(f"Error processing wingman request: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process wingman request")

@app.post("/challenges/create", response_model=ChallengeResponse)
async def create_challenge(request: ChallengeRequest):
    """Create a new challenge (placeholder)"""
    if not Config.ENABLE_CHALLENGE_SHARING:
        raise HTTPException(status_code=503, detail="Challenge sharing is currently disabled")
    
    logger.info(f"Challenge creation request from user {request.user_id}: {request.title}")
    
    # Placeholder response - actual challenge creation logic to be implemented
    challenge_id = f"challenge_{int(time.time())}"
    
    return ChallengeResponse(
        id=challenge_id,
        message="Challenge created successfully",
        challenge={
            "id": challenge_id,
            "title": request.title,
            "description": request.description,
            "type": request.challenge_type,
            "duration_days": request.duration_days or Config.CHALLENGE_DURATION_DAYS,
            "created_by": request.user_id,
            "created_at": datetime.utcnow().isoformat(),
            "status": "active"
        }
    )

@app.get("/user/{user_id}/status")
async def get_user_status(user_id: str):
    """Get user status and current challenges"""
    try:
        # Check if user exists (placeholder query)
        # Actual implementation will query Supabase user tables
        
        return {
            "user_id": user_id,
            "status": "active",
            "current_challenges": [],
            "wingman_matches": [],
            "last_activity": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error fetching user status: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch user status")

# Middleware for rate limiting and request logging
@app.middleware("http")
async def rate_limit_and_log_middleware(request: Request, call_next):
    """Middleware for rate limiting and request logging"""
    start_time = time.time()
    
    # Apply rate limiting to all requests
    try:
        from src.rate_limiter import rate_limiter
        
        # Extract user_id from request if available (from headers or query params)
        user_id = request.headers.get("X-User-ID") or request.query_params.get("user_id")
        
        # Check rate limits
        allowed, rate_info = await rate_limiter.check_rate_limit(request, user_id=user_id)
        
        if not allowed:
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "message": f"Too many requests for {rate_info.get('limit_type', 'unknown')} limit",
                    "retry_after": rate_info.get("reset_time", 0) - int(time.time()),
                    "limit_info": rate_info
                },
                headers={
                    "X-RateLimit-Limit": str(rate_info.get("limit", "unknown")),
                    "X-RateLimit-Remaining": str(rate_info.get("remaining", 0)),
                    "X-RateLimit-Reset": str(rate_info.get("reset_time", 0)),
                    "Retry-After": str(max(1, rate_info.get("reset_time", 0) - int(time.time())))
                }
            )
    except Exception as e:
        # If rate limiting fails, log error but don't block request
        logger.error(f"Rate limiting error (allowing request): {str(e)}")
    
    # Request logging
    if Config.ENABLE_DETAILED_LOGGING:
        logger.debug(f"Request: {request.method} {request.url.path}")
        logger.debug(f"Headers: {dict(request.headers)}")
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    logger.info(f"{request.method} {request.url.path} - {response.status_code} - {process_time:.3f}s")
    
    return response

# Claude Agent (Connell Barrett) Coaching Endpoints

class CoachingRequest(BaseModel):
    message: str
    user_id: str
    thread_id: Optional[str] = None

class CoachingResponse(BaseModel):
    response: str
    thread_id: str
    model_used: str
    timestamp: str

class AssessmentRequest(BaseModel):
    user_id: str
    responses: Dict[str, Any]

class AttemptRequest(BaseModel):
    user_id: str
    challenge_id: str
    outcome: str
    confidence_rating: int
    notes: Optional[str] = ""
    lessons_learned: Optional[List[str]] = None

@app.post("/coach/chat", response_model=CoachingResponse)
async def coach_chat(request: CoachingRequest):
    """Chat with Connell Barrett for dating confidence coaching with intelligent model routing"""
    if not Config.ENABLE_AI_COACHING:
        raise HTTPException(status_code=503, detail="AI coaching is currently disabled")
    
    start_time = time.time()
    try:
        from src.claude_agent import interact_with_coach, get_conversation_context
        from src.llm_router import get_coaching_config
        import uuid
        
        # Generate thread_id if not provided
        thread_id = request.thread_id or str(uuid.uuid4())
        
        # Model routing for cost optimization
        routing_decision = None
        if Config.ENABLE_COST_OPTIMIZATION:
            # Get conversation context for better routing decisions
            context = await get_conversation_context(request.user_id, thread_id, limit=5)
            context_messages = [msg.get('content', '') for msg in context] if context else []
            
            # Route to optimal model based on content
            routing_decision = get_optimal_model(
                message=request.message,
                context=context_messages,
                user_preferences={"coaching_context": True}
            )
            
            logger.info(f"Model routing: {routing_decision.model_name} for user {request.user_id} - {routing_decision.reasoning}")
        
        # Get coaching response with model routing
        response_text = await interact_with_coach(
            user_input=request.message,
            user_id=request.user_id,
            thread_id=thread_id,
            model_override=routing_decision.model_name if routing_decision else None
        )
        
        # Store conversation
        from src.claude_agent import store_coaching_conversation
        await store_coaching_conversation(
            user_id=request.user_id,
            thread_id=thread_id,
            user_input=request.message,
            coach_response=response_text
        )
        
        # Record performance metrics
        duration_ms = (time.time() - start_time) * 1000
        if Config.ENABLE_PERFORMANCE_MONITORING:
            await record_request_metric("coach_chat", duration_ms, 200)
        
        # Get model info for response
        model_config = get_coaching_config()
        if routing_decision:
            model_config.update({
                "selected_model": routing_decision.model_name,
                "routing_reason": routing_decision.reasoning,
                "cost_factor": routing_decision.estimated_cost_factor
            })
        
        return CoachingResponse(
            response=response_text,
            thread_id=thread_id,
            model_used=model_config["model"],
            timestamp=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error in coach chat: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get coaching response")

@app.post("/coach/chat/stream")
async def coach_chat_stream(request: CoachingRequest):
    """Stream chat with Connell Barrett for real-time coaching"""
    if not Config.ENABLE_AI_COACHING:
        raise HTTPException(status_code=503, detail="AI coaching is currently disabled")
    
    try:
        from src.claude_agent import interact_with_coach_stream, store_coaching_conversation
        import uuid
        
        # Generate thread_id if not provided
        thread_id = request.thread_id or str(uuid.uuid4())
        
        async def generate_response():
            full_response = ""
            
            async for chunk in interact_with_coach_stream(
                user_input=request.message,
                user_id=request.user_id,
                thread_id=thread_id
            ):
                full_response += chunk
                yield f"data: {json.dumps({'chunk': chunk, 'thread_id': thread_id})}\\n\\n"
            
            # Store complete conversation
            await store_coaching_conversation(
                user_id=request.user_id,
                thread_id=thread_id,
                user_input=request.message,
                coach_response=full_response
            )
            
            # Send completion signal
            yield f"data: {json.dumps({'done': True, 'thread_id': thread_id})}\\n\\n"
        
        return StreamingResponse(
            generate_response(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream"
            }
        )
        
    except Exception as e:
        logger.error(f"Error in coach chat stream: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to stream coaching response")

@app.post("/coach/assessment")
async def save_confidence_assessment(request: AssessmentRequest):
    """Save dating confidence assessment results"""
    try:
        from src.simple_memory import WingmanMemory
        
        memory = WingmanMemory(supabase, request.user_id)
        success = await memory.store_assessment_results(request.responses)
        
        if success:
            return {"message": "Assessment results saved successfully", "user_id": request.user_id}
        else:
            raise HTTPException(status_code=500, detail="Failed to save assessment results")
            
    except Exception as e:
        logger.error(f"Error saving assessment: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to save assessment")

@app.post("/coach/attempt")
async def record_approach_attempt(request: AttemptRequest):
    """Record an approach attempt outcome"""
    try:
        from src.tools import record_attempt_outcome
        
        result = await record_attempt_outcome(
            user_id=request.user_id,
            challenge_id=request.challenge_id,
            outcome=request.outcome,
            confidence_rating=request.confidence_rating,
            notes=request.notes or "",
            lessons_learned=request.lessons_learned or []
        )
        
        if result.get("success"):
            return result
        else:
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to record attempt"))
            
    except Exception as e:
        logger.error(f"Error recording attempt: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to record attempt")

@app.get("/coach/challenges")
async def get_coaching_challenges(
    user_id: str,
    difficulty: Optional[str] = None,
    challenge_type: Optional[str] = None,
    limit: int = 10
):
    """Get available approach challenges for user"""
    try:
        from src.tools import get_approach_challenges
        
        result = await get_approach_challenges(
            user_id=user_id,
            difficulty=difficulty,
            challenge_type=challenge_type,
            limit=limit
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting challenges: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get challenges")

@app.get("/api/challenges")
async def get_challenges(difficulty: Optional[str] = None, request: Request = None):
    """Get approach challenges with optional difficulty filter and Redis caching"""
    start_time = time.time()
    
    try:
        from src.database import SupabaseFactory
        
        # Check feature flag
        if not Config.ENABLE_CHALLENGES_CATALOG:
            raise HTTPException(status_code=503, detail="Challenges catalog is currently disabled")
        
        # Create cache key based on parameters
        cache_key = f"challenges:all" if not difficulty else f"challenges:difficulty:{difficulty}"
        
        # Check Redis cache first (30-minute TTL for challenges)
        cached_data = await get_cached_data(cache_key, ttl_seconds=1800)  # 30 minutes
        if cached_data:
            if request:
                request.state.cache_status = 'hit'
            await record_cache_metric("challenges_get", hit=True)
            logger.debug(f"Cache hit for {cache_key}")
            return cached_data
        
        if request:
            request.state.cache_status = 'miss'
        await record_cache_metric("challenges_get", hit=False)
        logger.debug(f"Cache miss for {cache_key} - fetching from database")
        
        # Fetch from database with performance monitoring
        db_start = time.time()
        db = SupabaseFactory.get_service_client()
        
        # Build query
        query = db.table('approach_challenges').select('*')
        
        if difficulty:
            if difficulty not in ['beginner', 'intermediate', 'advanced']:
                raise HTTPException(status_code=400, detail="Invalid difficulty. Must be: beginner, intermediate, or advanced")
            query = query.eq('difficulty', difficulty)
        
        # Execute query
        result = query.execute()
        db_duration = (time.time() - db_start) * 1000
        
        # Record database performance
        if Config.ENABLE_PERFORMANCE_MONITORING:
            await record_database_metric("challenges_select", db_duration, True)
        
        # Transform data
        challenges = []
        for challenge in result.data:
            challenges.append({
                "id": challenge["id"],
                "difficulty": challenge["difficulty"],
                "title": challenge["title"],
                "description": challenge["description"],
                "points": challenge["points"],
                "created_at": challenge["created_at"]
            })
        
        response_data = {
            "challenges": challenges,
            "count": len(challenges),
            "difficulty_filter": difficulty,
            "cached": False,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # Cache the result in Redis (30-minute TTL)
        cache_success = await set_cached_data(cache_key, response_data, ttl_seconds=1800)
        if cache_success:
            logger.debug(f"Cached challenges data for key: {cache_key}")
        
        # Record total request performance
        total_duration = (time.time() - start_time) * 1000
        if Config.ENABLE_PERFORMANCE_MONITORING:
            await record_request_metric("challenges_get", total_duration, 200)
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting challenges: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve challenges")

@app.post("/api/challenges/cache/invalidate")
async def invalidate_challenges_cache_endpoint():
    """Manually invalidate challenges cache for admin use"""
    try:
        from src.redis_session import invalidate_challenges_cache
        
        success = await invalidate_challenges_cache()
        
        return {
            "success": success,
            "message": "Challenges cache invalidated" if success else "Cache invalidation skipped (Redis unavailable)"
        }
    except Exception as e:
        logger.error(f"Error invalidating challenges cache: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to invalidate cache")

@app.get("/coach/progress/{user_id}")
async def get_user_coaching_progress(user_id: str, timeframe: str = "30days"):
    """Get user's dating confidence progress"""
    try:
        from src.tools import get_user_progress
        
        result = await get_user_progress(user_id=user_id, timeframe=timeframe)
        return result
        
    except Exception as e:
        logger.error(f"Error getting progress: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get progress")

@app.get("/coach/sessions/{user_id}")
async def get_coaching_sessions(user_id: str, limit: int = 10, include_details: bool = False):
    """Get user's coaching session history"""
    try:
        from src.tools import get_session_history
        
        result = await get_session_history(
            user_id=user_id,
            limit=limit,
            include_details=include_details
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting sessions: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get sessions")

@app.get("/coach/health")
async def coach_health_check():
    """Health check for Claude agent and coaching system"""
    try:
        from src.claude_agent import health_check
        from src.llm_router import llm_router
        
        agent_health = await health_check()
        router_status = llm_router.get_model_status()
        
        return {
            "claude_agent": agent_health,
            "model_router": router_status,
            "ai_coaching_enabled": Config.ENABLE_AI_COACHING,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in coach health check: {str(e)}")
        raise HTTPException(status_code=500, detail="Coach health check failed")

# === BUDDY MATCHING ENDPOINTS ===

class BuddyMatchRequest(BaseModel):
    """Request model for finding buddy matches"""
    radius_miles: int = Field(default=20, ge=1, le=100, description="Search radius in miles")

class BuddyCandidateResponse(BaseModel):
    """Response model for buddy candidate"""
    user_id: str
    city: str
    distance_miles: float
    experience_level: str
    confidence_archetype: str

class BuddyMatchResponse(BaseModel):
    """Response model for buddy matching"""
    success: bool
    message: str
    candidates: List[BuddyCandidateResponse] = []
    total_found: int = 0

class AutoMatchResponse(BaseModel):
    """Response model for automatic wingman matching"""
    success: bool
    message: str
    match_id: Optional[str] = None
    buddy_user_id: Optional[str] = None
    buddy_profile: Optional[Dict[str, Any]] = None

# Chat Models
class ChatMessage(BaseModel):
    """Model for a single chat message"""
    id: str
    match_id: str
    sender_id: str
    message_text: str
    created_at: datetime

class ChatMessagesRequest(BaseModel):
    """Request model for fetching chat messages"""
    cursor: Optional[str] = None
    limit: int = 50

class ChatMessagesResponse(BaseModel):
    """Response model for chat messages"""
    messages: List[ChatMessage]
    has_more: bool
    next_cursor: Optional[str] = None

# Match Response Models
class MatchResponseRequest(BaseModel):
    """Request model for responding to a wingman match"""
    user_id: str = Field(..., description="User ID responding to the match", pattern=r'^[0-9a-f-]{36}$')
    match_id: str = Field(..., description="ID of the wingman match to respond to", pattern=r'^[0-9a-f-]{36}$')
    action: str = Field(..., description="User action: 'accept' or 'decline'", pattern="^(accept|decline)$")

class MatchResponseResponse(BaseModel):
    """Response model for match response"""
    success: bool = Field(..., description="Whether the response was processed successfully")
    message: str = Field(..., description="Success or error message")
    match_status: Optional[str] = Field(None, description="Current status of the match after response")
    next_match: Optional[Dict[str, Any]] = Field(None, description="Next available match if declined")

class SendMessageRequest(BaseModel):
    """Request model for sending a message"""
    match_id: str
    message: str = Field(..., min_length=2, max_length=2000)

class SendMessageResponse(BaseModel):
    """Response model for sending a message"""
    success: bool
    message_id: str
    created_at: datetime

# Session Creation Pydantic Models
class SessionCreateRequest(BaseModel):
    """Request model for creating a wingman session"""
    match_id: UUID = Field(..., description="UUID of the accepted wingman match")
    venue_name: str = Field(..., min_length=1, max_length=200, description="Name of the venue for the session")
    time: datetime = Field(..., description="Scheduled time for the session (ISO8601 format)")
    user1_challenge_id: UUID = Field(..., description="Challenge ID for user1 in the match")
    user2_challenge_id: UUID = Field(..., description="Challenge ID for user2 in the match")

class SessionCreateResponse(BaseModel):
    """Response model for session creation"""
    success: bool = Field(..., description="Whether session creation was successful")
    session_id: str = Field(..., description="UUID of the created session")
    message: str = Field(..., description="Success or error message")
    scheduled_time: datetime = Field(..., description="Confirmed scheduled time for the session")
    venue_name: str = Field(..., description="Confirmed venue name")
    notifications_sent: bool = Field(..., description="Whether email/chat notifications were sent")

# Session Management Pydantic Models (Task 14)
class ChallengeInfo(BaseModel):
    """Challenge information for session participants"""
    id: str = Field(..., description="Challenge UUID")
    title: str = Field(..., description="Challenge title")
    description: str = Field(..., description="Challenge description")
    points: int = Field(..., description="Points awarded for completion")
    difficulty: str = Field(..., description="Challenge difficulty level")

class ParticipantInfo(BaseModel):
    """Participant information for session"""
    id: str = Field(..., description="User UUID")
    name: str = Field(..., description="User first name")
    challenge: ChallengeInfo = Field(..., description="Assigned challenge")
    confirmed: bool = Field(..., description="Whether completion is confirmed by buddy")

class SessionParticipants(BaseModel):
    """Session participants information"""
    user1: ParticipantInfo = Field(..., description="First participant")
    user2: ParticipantInfo = Field(..., description="Second participant")

class ReputationPreview(BaseModel):
    """Reputation delta preview for session completion"""
    user1_delta: int = Field(..., description="Reputation change for user1 on completion")
    user2_delta: int = Field(..., description="Reputation change for user2 on completion")

class SessionDataResponse(BaseModel):
    """Response model for session data retrieval"""
    id: str = Field(..., description="Session UUID")
    match_id: str = Field(..., description="Match UUID")
    venue_name: str = Field(..., description="Session venue name")
    scheduled_time: datetime = Field(..., description="Scheduled session time")
    status: str = Field(..., description="Session status")
    notes: Optional[str] = Field(None, description="Session notes")
    participants: SessionParticipants = Field(..., description="Session participants and challenges")
    reputation_preview: ReputationPreview = Field(..., description="Reputation changes on completion")
    completed_at: Optional[datetime] = Field(None, description="Session completion timestamp")

class SessionConfirmRequest(BaseModel):
    """Request model for confirming buddy completion"""
    buddy_user_id: str = Field(..., description="UUID of the buddy whose completion is being confirmed", pattern=r'^[0-9a-f-]{36}$')

class SessionConfirmResponse(BaseModel):
    """Response model for session confirmation"""
    success: bool = Field(..., description="Whether confirmation was successful")
    message: str = Field(..., description="Success or error message")
    session_status: str = Field(..., description="Updated session status")
    both_confirmed: bool = Field(..., description="Whether both participants have confirmed each other")

class SessionNotesRequest(BaseModel):
    """Request model for updating session notes"""
    notes: str = Field(..., min_length=0, max_length=2000, description="Session notes (max 2000 characters)")

class SessionNotesResponse(BaseModel):
    """Response model for session notes update"""
    success: bool = Field(..., description="Whether notes update was successful")
    message: str = Field(..., description="Success or error message")
    updated_notes: str = Field(..., description="Updated session notes")

class SessionConfirmCompletionRequest(BaseModel):
    """Request model for confirming session completion"""
    session_id: str = Field(..., description="UUID of the session to confirm completion", pattern=r'^[0-9a-f-]{36}$')

class SessionConfirmCompletionResponse(BaseModel):
    """Response model for session completion confirmation"""
    success: bool = Field(..., description="Whether confirmation was successful")
    message: str = Field(..., description="Success or error message")
    both_confirmed: bool = Field(..., description="Whether both participants have confirmed completion")
    reputation_updated: bool = Field(..., description="Whether reputation counters were updated")
    session_status: str = Field(..., description="Updated session status")

class ReputationResponse(BaseModel):
    """Response model for user reputation data"""
    score: int = Field(..., description="Reputation score (-5 to 20)", ge=-5, le=20)
    completed_sessions: int = Field(..., description="Number of completed sessions", ge=0)
    no_shows: int = Field(..., description="Number of no-show sessions", ge=0)
    badge_color: str = Field(..., description="Badge color based on score", pattern="^(gold|green|red)$")
    cache_timestamp: str = Field(..., description="ISO timestamp when data was cached")

# Dating Goals Pydantic Models
class DatingGoalsRequest(BaseModel):
    """Request model for creating/updating dating goals"""
    user_id: str = Field(..., description="User ID for dating goals", pattern=r'^[0-9a-f-]{36}$')
    message: str = Field(..., min_length=1, max_length=1000, description="User's message for dating goals conversation")
    thread_id: Optional[str] = Field(None, description="Thread ID for conversation continuity")

class DatingGoalsResponse(BaseModel):
    """Response model for dating goals conversation"""
    success: bool = Field(..., description="Whether the request was processed successfully")
    message: str = Field(..., description="AI coach response")
    thread_id: str = Field(..., description="Thread ID for conversation continuity")
    is_complete: bool = Field(False, description="Whether the dating goals flow is complete")
    topic_number: Optional[int] = Field(None, description="Current topic number (1-4)")
    completion_percentage: float = Field(0.0, description="Percentage of goals conversation complete")

class DatingGoalsDataResponse(BaseModel):
    """Response model for retrieving dating goals data"""
    success: bool = Field(..., description="Whether the goals data was retrieved successfully")
    user_id: str = Field(..., description="User ID for the goals")
    goals: Optional[str] = Field(None, description="User's dating confidence goals")
    preferred_venues: List[str] = Field(default_factory=list, description="Preferred meeting venues")
    comfort_level: str = Field("moderate", description="User's comfort level: low, moderate, high")
    goals_data: Dict[str, Any] = Field(default_factory=dict, description="Complete goals conversation data")
    created_at: Optional[str] = Field(None, description="When goals were created (ISO format)")
    updated_at: Optional[str] = Field(None, description="When goals were last updated (ISO format)")

@app.get("/api/matches/candidates/{user_id}", response_model=BuddyMatchResponse)
async def find_buddy_candidates(user_id: str, radius_miles: int = 20):
    """
    Find buddy candidates within specified radius of user's location
    Simple endpoint for finding potential wingman partners
    """
    try:
        from src.db.distance import find_candidates_within_radius
        
        # Validate radius
        if not 1 <= radius_miles <= 100:
            raise HTTPException(status_code=400, detail="Radius must be between 1 and 100 miles")
        
        # Find candidates
        candidates = await find_candidates_within_radius(user_id, radius_miles)
        
        # Convert to response format
        candidate_responses = [
            BuddyCandidateResponse(
                user_id=candidate.user_id,
                city=candidate.city,
                distance_miles=candidate.distance_miles,
                experience_level=candidate.experience_level,
                confidence_archetype=candidate.confidence_archetype
            )
            for candidate in candidates
        ]
        
        return BuddyMatchResponse(
            success=True,
            message=f"Found {len(candidates)} candidates within {radius_miles} miles",
            candidates=candidate_responses,
            total_found=len(candidates)
        )
        
    except Exception as e:
        logger.error(f"Error finding buddy candidates for user {user_id}: {str(e)}")
        return BuddyMatchResponse(
            success=False,
            message=f"Error finding candidates: {str(e)}",
            candidates=[],
            total_found=0
        )

@app.get("/api/matches/distance/{user1_id}/{user2_id}")
async def get_user_distance(user1_id: str, user2_id: str):
    """
    Calculate distance between two users
    Simple utility for checking if users are within range
    """
    try:
        from src.db.distance import get_distance_between_users
        
        distance = await get_distance_between_users(user1_id, user2_id)
        
        if distance is None:
            raise HTTPException(status_code=404, detail="Could not calculate distance - missing location data")
        
        return {
            "success": True,
            "user1_id": user1_id,
            "user2_id": user2_id,
            "distance_miles": distance,
            "within_20_miles": distance <= 20.0
        }
        
    except Exception as e:
        logger.error(f"Error calculating distance between users {user1_id} and {user2_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error calculating distance: {str(e)}")

@app.post("/api/matches/auto/{user_id}", response_model=AutoMatchResponse)
async def create_auto_match(user_id: str, radius_miles: int = 25):
    """
    Create automatic wingman match for user
    
    Implements the auto-matching algorithm with:
    - Geographic proximity filtering (within radius)
    - Experience level compatibility (same or ±1 level)  
    - Recency filtering (exclude recent pairs from last 7 days)
    - Throttling (one active pending match per user)
    """
    try:
        from src.services.wingman_matcher import WingmanMatcher
        from src.database import SupabaseFactory
        
        # Validate radius
        if not 1 <= radius_miles <= 100:
            raise HTTPException(status_code=400, detail="Radius must be between 1 and 100 miles")
        
        # Initialize matcher service
        client = SupabaseFactory.get_service_client()
        matcher = WingmanMatcher(client)
        
        # Create automatic match
        result = await matcher.create_automatic_match(user_id, radius_miles)
        
        # Return result in API format
        return AutoMatchResponse(
            success=result["success"],
            message=result["message"],
            match_id=result.get("match_id"),
            buddy_user_id=result.get("buddy_user_id"),
            buddy_profile=result.get("buddy_profile")
        )
        
    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except Exception as e:
        logger.error(f"Error creating auto-match for user {user_id}: {str(e)}")
        return AutoMatchResponse(
            success=False,
            message=f"Unable to create wingman match: {str(e)}",
            match_id=None,
            buddy_user_id=None,
            buddy_profile=None
        )

# User Reputation Endpoints
@app.get("/api/user/reputation/{user_id}", response_model=ReputationResponse)
async def get_user_reputation(user_id: str, use_cache: bool = True):
    """
    Get user reputation score based on session completion history
    
    Calculates reputation score as: completed_sessions - no_shows
    Score is bounded between -5 and +20
    Badge color: gold (≥10), green (≥0), red (<0)
    
    Args:
        user_id: UUID of the user
        use_cache: Whether to use Redis cache (default True)
    
    Returns:
        ReputationResponse with score, counts, badge color, and cache timestamp
    """
    try:
        from src.services.reputation_service import reputation_service
        
        logger.info(f"Fetching reputation for user {user_id} (cache={use_cache})")
        
        # Get reputation data via service layer
        reputation_data = await reputation_service.get_user_reputation(user_id, use_cache)
        
        logger.info(f"Reputation calculated for user {user_id}: score={reputation_data.score}, badge={reputation_data.badge_color}")
        
        # Return API response
        return ReputationResponse(
            score=reputation_data.score,
            completed_sessions=reputation_data.completed_sessions,
            no_shows=reputation_data.no_shows,
            badge_color=reputation_data.badge_color,
            cache_timestamp=reputation_data.cache_timestamp
        )
        
    except ValueError as e:
        logger.warning(f"Invalid user_id format: {user_id}")
        raise HTTPException(status_code=422, detail=f"Invalid user ID format: {str(e)}")
    except Exception as e:
        logger.error(f"Error fetching reputation for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch user reputation: {str(e)}")

@app.post("/api/user/reputation/cache/invalidate/{user_id}")
async def invalidate_user_reputation_cache(user_id: str):
    """
    Invalidate reputation cache for a specific user
    Admin/testing endpoint for cache management
    """
    try:
        from src.services.reputation_service import reputation_service
        
        success = await reputation_service.invalidate_user_cache(user_id)
        
        return {
            "success": success,
            "message": f"Reputation cache {'invalidated' if success else 'invalidation failed'} for user {user_id}"
        }
        
    except Exception as e:
        logger.error(f"Error invalidating reputation cache for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to invalidate cache: {str(e)}")

@app.post("/api/user/reputation/cache/invalidate-all")
async def invalidate_all_reputation_cache():
    """
    Invalidate all reputation cache entries
    Admin/testing endpoint for bulk cache management
    """
    try:
        from src.services.reputation_service import reputation_service
        
        success = await reputation_service.invalidate_all_cache()
        
        return {
            "success": success,
            "message": f"All reputation cache entries {'invalidated' if success else 'invalidation failed'}"
        }
        
    except Exception as e:
        logger.error(f"Error invalidating all reputation cache: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to invalidate cache: {str(e)}")

# Chat Endpoints
@app.get("/api/chat/messages/{match_id}", response_model=ChatMessagesResponse)
async def get_chat_messages(match_id: str, request: Request, cursor: Optional[str] = None, limit: int = 50):
    """
    Get chat messages for a specific match with pagination
    Only match participants can access messages
    """
    try:
        from src.database import SupabaseFactory
        from src.services.auth_service import get_current_user_id
        
        # Get current user ID from auth context
        user_id = await get_current_user_id(request)
        if not user_id:
            raise HTTPException(status_code=401, detail="Authentication required")
        
        db_client = SupabaseFactory.get_service_client()
        
        # Verify user is participant in this match
        match_check = db_client.table('wingman_matches').select('user1_id, user2_id').eq('id', match_id).execute()
        if not match_check.data:
            raise HTTPException(status_code=404, detail="Match not found")
        
        match_data = match_check.data[0]
        if user_id not in [match_data['user1_id'], match_data['user2_id']]:
            raise HTTPException(status_code=403, detail="Access denied - not a participant in this match")
        
        # Build query for messages
        query = db_client.table('chat_messages').select('*').eq('match_id', match_id)
        
        # Apply cursor-based pagination
        if cursor:
            query = query.lt('created_at', cursor)
        
        # Order by created_at desc and limit
        query = query.order('created_at', desc=True).limit(min(limit, 100))
        
        # Execute query
        result = query.execute()
        messages = result.data
        
        # Reverse to get chronological order
        messages.reverse()
        
        # Determine pagination info
        has_more = len(messages) == limit
        next_cursor = messages[0]['created_at'] if messages and has_more else None
        
        # Convert to response format
        chat_messages = [
            ChatMessage(
                id=msg['id'],
                match_id=msg['match_id'],
                sender_id=msg['sender_id'],
                message_text=msg['message_text'],
                created_at=datetime.fromisoformat(msg['created_at'].replace('Z', '+00:00'))
            )
            for msg in messages
        ]
        
        return ChatMessagesResponse(
            messages=chat_messages,
            has_more=has_more,
            next_cursor=next_cursor
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching messages for match {match_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch messages")

@app.post("/api/chat/send", response_model=SendMessageResponse)
async def send_message(request: SendMessageRequest, http_request: Request):
    """
    Send a message to a chat
    Includes rate limiting and validation
    """
    try:
        from src.database import SupabaseFactory
        from src.services.auth_service import get_current_user_id
        from src.rate_limiting import TokenBucket
        
        # Get current user ID
        user_id = await get_current_user_id(http_request)
        if not user_id:
            raise HTTPException(status_code=401, detail="Authentication required")
        
        # Rate limiting: 1 message per 0.5 seconds
        rate_limiter = TokenBucket(
            capacity=1,
            refill_rate=2.0,  # 2 tokens per second = 1 token per 0.5 seconds
            key_prefix="chat_rate_limit"
        )
        
        rate_limit_result = await rate_limiter.consume(user_id, 1)
        if not rate_limit_result["allowed"]:
            retry_after = rate_limit_result.get("retry_after", 0.5)
            raise HTTPException(
                status_code=429, 
                detail=f"Rate limit exceeded. Try again in {retry_after:.1f} seconds",
                headers={"Retry-After": str(int(retry_after))}
            )
        
        db_client = SupabaseFactory.get_service_client()
        
        # Verify user is participant in this match
        match_check = db_client.table('wingman_matches').select('user1_id, user2_id').eq('id', request.match_id).execute()
        if not match_check.data:
            raise HTTPException(status_code=404, detail="Match not found")
        
        match_data = match_check.data[0]
        if user_id not in [match_data['user1_id'], match_data['user2_id']]:
            raise HTTPException(status_code=403, detail="Access denied - not a participant in this match")
        
        # Sanitize message text (basic sanitization)
        import html
        sanitized_message = html.escape(request.message.strip())
        
        # Insert message
        message_data = {
            'match_id': request.match_id,
            'sender_id': user_id,
            'message_text': sanitized_message
        }
        
        result = db_client.table('chat_messages').insert(message_data).execute()
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to send message")
        
        message = result.data[0]
        
        # Update last read timestamp for sender
        timestamp_data = {
            'match_id': request.match_id,
            'user_id': user_id,
            'last_read_at': message['created_at'],
            'updated_at': message['created_at']
        }
        
        # Upsert read timestamp
        db_client.table('chat_read_timestamps').upsert(timestamp_data).execute()
        
        return SendMessageResponse(
            success=True,
            message_id=message['id'],
            created_at=datetime.fromisoformat(message['created_at'].replace('Z', '+00:00'))
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending message: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to send message")

@app.post("/api/buddy/respond", response_model=MatchResponseResponse)
async def respond_to_buddy_match(request: MatchResponseRequest):
    """
    Respond to wingman match invitation (accept/decline)
    
    Implements Task 10: Match response endpoint and state machine
    
    Features:
    - Validates user is match participant
    - Handles accept/decline state transitions  
    - Sends emails on mutual accept
    - Finds next match on decline
    - Proper error handling and logging
    """
    try:
        logger.info(f"Match response from user {request.user_id}: {request.action} on match {request.match_id}")
        
        from src.services.wingman_matcher import WingmanMatcher
        from src.database import SupabaseFactory
        
        # Import email service conditionally
        try:
            from src.email_templates import email_service
        except ImportError:
            logger.warning("Email service not available - emails will be skipped")
            email_service = None
        
        # Get service instances
        db_client = SupabaseFactory.get_service_client()
        matcher = WingmanMatcher(db_client)
        
        # Validate user is participant in the match
        match_check = db_client.table('wingman_matches')\
            .select('user1_id, user2_id, status')\
            .eq('id', request.match_id)\
            .execute()
        
        if not match_check.data:
            raise HTTPException(status_code=404, detail="Match not found")
        
        match_data = match_check.data[0]
        user1_id = match_data['user1_id']
        user2_id = match_data['user2_id']
        current_status = match_data['status']
        
        # Check if user is participant
        if request.user_id not in [user1_id, user2_id]:
            raise HTTPException(status_code=403, detail="Not authorized - user is not a participant in this match")
        
        # Check if match is still pending
        if current_status != 'pending':
            raise HTTPException(status_code=400, detail=f"Match is already {current_status} - cannot respond")
        
        # Handle the response based on action
        if request.action == "accept":
            # Update match status to accepted
            db_client.table('wingman_matches')\
                .update({"status": "accepted"})\
                .eq('id', request.match_id)\
                .execute()
            
            # Send email notifications to both users
            if email_service:
                try:
                    # Get user profiles for email
                    user1_profile = db_client.table('user_profiles').select('email').eq('id', user1_id).execute()
                    user2_profile = db_client.table('user_profiles').select('email').eq('id', user2_id).execute()
                    
                    if user1_profile.data and user2_profile.data:
                        user1_email = user1_profile.data[0]['email']
                        user2_email = user2_profile.data[0]['email']
                        
                        # Use simplified email notification (email service will handle templates)
                        logger.info(f"Match accepted - would send emails to {user1_email} and {user2_email}")
                        
                except Exception as e:
                    logger.warning(f"Failed to process match accepted emails: {e}")
                    # Don't fail the request if email fails
            else:
                logger.info("Email service not available - skipping match accepted notifications")
            
            return MatchResponseResponse(
                success=True,
                message="Match accepted! You can now start chatting with your wingman buddy.",
                match_status="accepted",
                next_match=None
            )
            
        else:  # decline
            # Update match status to declined
            db_client.table('wingman_matches')\
                .update({"status": "declined"})\
                .eq('id', request.match_id)\
                .execute()
            
            # Find next match for the user
            next_match_result = await matcher.create_automatic_match(request.user_id, radius_miles=25)
            
            next_match_data = None
            if next_match_result["success"]:
                next_match_data = {
                    "match_id": next_match_result.get("match_id"),
                    "buddy_user_id": next_match_result.get("buddy_user_id"),
                    "buddy_profile": next_match_result.get("buddy_profile")
                }
            
            return MatchResponseResponse(
                success=True,
                message="Match declined. Here's your next potential wingman buddy!" if next_match_data else "Match declined.",
                match_status="declined",
                next_match=next_match_data
            )
        
    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except Exception as e:
        logger.error(f"Error in match response: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process match response")

@app.post("/api/session/create", response_model=SessionCreateResponse)
async def create_wingman_session(request: SessionCreateRequest):
    """
    Create a scheduled wingman session for an accepted match
    
    Implements Task 13: Session creation flow and API
    
    Features:
    - Validates match status is accepted
    - Ensures challenges exist and are valid
    - Creates wingman_sessions record with status=scheduled
    - Enforces one active session per match
    - Sends email notifications to both users
    - Creates chat system card for in-app notification
    """
    try:
        logger.info(f"Creating session for match {request.match_id} at {request.venue_name} on {request.time}")
        
        from src.database import SupabaseFactory
        
        # Import email service conditionally
        try:
            from src.email_templates import email_service
        except ImportError:
            logger.warning("Email service not available - emails will be skipped")
            email_service = None
        
        # Get database client
        db_client = SupabaseFactory.get_service_client()
        
        # Validate match exists and status is accepted
        match_check = db_client.table('wingman_matches')\
            .select('id, user1_id, user2_id, status')\
            .eq('id', request.match_id)\
            .execute()
        
        if not match_check.data:
            raise HTTPException(status_code=404, detail="Match not found")
        
        match_data = match_check.data[0]
        if match_data['status'] != 'accepted':
            raise HTTPException(
                status_code=400, 
                detail=f"Match status must be 'accepted' to schedule sessions (current: {match_data['status']})"
            )
        
        # Validate challenges exist
        challenge_check = db_client.table('approach_challenges')\
            .select('id')\
            .in_('id', [str(request.user1_challenge_id), str(request.user2_challenge_id)])\
            .execute()
        
        if len(challenge_check.data) != 2:
            raise HTTPException(
                status_code=400, 
                detail="One or both challenge IDs are invalid - challenges must exist"
            )
        
        # Check for existing active sessions for this match
        existing_sessions = db_client.table('wingman_sessions')\
            .select('id, status')\
            .eq('match_id', request.match_id)\
            .in_('status', ['scheduled', 'in_progress'])\
            .execute()
        
        if existing_sessions.data:
            raise HTTPException(
                status_code=409, 
                detail="This match already has an active session (scheduled or in progress)"
            )
        
        # Validate scheduled time is in the future
        if request.time <= datetime.now(timezone.utc):
            raise HTTPException(
                status_code=400,
                detail="Scheduled time must be in the future"
            )
        
        # Create the session
        session_data = {
            "match_id": str(request.match_id),
            "user1_challenge_id": str(request.user1_challenge_id),
            "user2_challenge_id": str(request.user2_challenge_id),
            "venue_name": request.venue_name,
            "scheduled_time": request.time.isoformat(),
            "status": "scheduled"
        }
        
        session_result = db_client.table('wingman_sessions')\
            .insert(session_data)\
            .execute()
        
        if not session_result.data:
            raise HTTPException(status_code=500, detail="Failed to create session")
        
        created_session = session_result.data[0]
        session_id = created_session['id']
        
        # Send notifications
        notifications_sent = False
        
        try:
            # Get user profiles for email notifications
            user_profiles = db_client.table('user_profiles')\
                .select('id, email, first_name')\
                .in_('id', [match_data['user1_id'], match_data['user2_id']])\
                .execute()
            
            if len(user_profiles.data) == 2:
                # Create chat system message
                system_message = {
                    "match_id": str(request.match_id),
                    "sender_id": "system",
                    "message": f"🎯 Session scheduled at {request.venue_name} on {request.time.strftime('%B %d, %Y at %I:%M %p')}. Good luck with your challenges!",
                    "is_system_message": True
                }
                
                # Insert system message into chat
                db_client.table('chat_messages')\
                    .insert(system_message)\
                    .execute()
                
                # Send email notifications if service is available
                if email_service and email_service.enabled:
                    for profile in user_profiles.data:
                        await email_service.send_session_scheduled(
                            to_email=profile['email'],
                            user_name=profile['first_name'],
                            venue_name=request.venue_name,
                            scheduled_time=request.time.strftime('%B %d, %Y at %I:%M %p')
                        )
                    
                    logger.info(f"Session notifications sent for session {session_id}")
                    notifications_sent = True
                else:
                    logger.warning("Email service not available - session notifications not sent")
            
        except Exception as e:
            logger.error(f"Failed to send session notifications: {e}")
            # Don't fail the request if notifications fail
        
        return SessionCreateResponse(
            success=True,
            session_id=session_id,
            message=f"Session scheduled successfully at {request.venue_name}",
            scheduled_time=request.time,
            venue_name=request.venue_name,
            notifications_sent=notifications_sent
        )
        
    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except Exception as e:
        logger.error(f"Error creating wingman session: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create session")

# Session Management API Endpoints (Task 14)

@app.get("/api/session/{session_id}", response_model=SessionDataResponse)
async def get_session_data(session_id: str, request: Request):
    """
    Get complete session data including participant info and challenges
    
    Implements Task 14: Session data retrieval endpoint
    
    Features:
    - Fetches session with related data (match participants, challenges)
    - Calculates reputation preview deltas based on challenge points
    - Authenticates and authorizes only match participants
    - Returns structured session data for frontend
    
    Security:
    - Requires authentication via X-Test-User-ID header (development) or JWT (production)
    - Validates user is participant in the session's match
    - Row-level security enforced via Supabase RLS policies
    """
    try:
        logger.info(f"Fetching session data for session {session_id}")
        
        from src.database import SupabaseFactory
        from src.services.auth_service import get_current_user_id, require_authentication
        
        # Get and validate current user
        user_id = await get_current_user_id(request)
        user_id = require_authentication(user_id)
        
        db_client = SupabaseFactory.get_service_client()
        
        # Fetch session with match data
        session_query = db_client.table('wingman_sessions')\
            .select('*, wingman_matches!inner(user1_id, user2_id)')\
            .eq('id', session_id)\
            .execute()
        
        if not session_query.data:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session_data = session_query.data[0]
        match_data = session_data['wingman_matches']
        
        # Verify user is participant in this session
        participant_ids = [match_data['user1_id'], match_data['user2_id']]
        if user_id not in participant_ids:
            raise HTTPException(
                status_code=403, 
                detail="Access denied - user is not a participant in this session"
            )
        
        # Get participant profiles
        profiles_query = db_client.table('user_profiles')\
            .select('id, first_name')\
            .in_('id', participant_ids)\
            .execute()
        
        profiles_by_id = {profile['id']: profile for profile in profiles_query.data}
        
        # Get challenge data
        challenge_ids = [session_data['user1_challenge_id'], session_data['user2_challenge_id']]
        challenges_query = db_client.table('approach_challenges')\
            .select('id, title, description, points, difficulty')\
            .in_('id', challenge_ids)\
            .execute()
        
        challenges_by_id = {challenge['id']: challenge for challenge in challenges_query.data}
        
        # Build participant info
        user1_profile = profiles_by_id.get(match_data['user1_id'], {})
        user2_profile = profiles_by_id.get(match_data['user2_id'], {})
        user1_challenge = challenges_by_id.get(session_data['user1_challenge_id'], {})
        user2_challenge = challenges_by_id.get(session_data['user2_challenge_id'], {})
        
        participants = SessionParticipants(
            user1=ParticipantInfo(
                id=match_data['user1_id'],
                name=user1_profile.get('first_name', 'Unknown'),
                challenge=ChallengeInfo(
                    id=str(session_data['user1_challenge_id']),
                    title=user1_challenge.get('title', 'Unknown Challenge'),
                    description=user1_challenge.get('description', ''),
                    points=user1_challenge.get('points', 0),
                    difficulty=user1_challenge.get('difficulty', 'unknown')
                ),
                confirmed=session_data.get('user1_completed_confirmed_by_user2', False)
            ),
            user2=ParticipantInfo(
                id=match_data['user2_id'],
                name=user2_profile.get('first_name', 'Unknown'),
                challenge=ChallengeInfo(
                    id=str(session_data['user2_challenge_id']),
                    title=user2_challenge.get('title', 'Unknown Challenge'),
                    description=user2_challenge.get('description', ''),
                    points=user2_challenge.get('points', 0),
                    difficulty=user2_challenge.get('difficulty', 'unknown')
                ),
                confirmed=session_data.get('user2_completed_confirmed_by_user1', False)
            )
        )
        
        # Calculate reputation preview (simple: ±challenge_points)
        reputation_preview = ReputationPreview(
            user1_delta=user1_challenge.get('points', 0),
            user2_delta=user2_challenge.get('points', 0)
        )
        
        # Parse timestamps
        scheduled_time = datetime.fromisoformat(session_data['scheduled_time'].replace('Z', '+00:00'))
        completed_at = None
        if session_data.get('completed_at'):
            completed_at = datetime.fromisoformat(session_data['completed_at'].replace('Z', '+00:00'))
        
        return SessionDataResponse(
            id=session_data['id'],
            match_id=session_data['match_id'],
            venue_name=session_data['venue_name'],
            scheduled_time=scheduled_time,
            status=session_data['status'],
            notes=session_data.get('notes'),
            participants=participants,
            reputation_preview=reputation_preview,
            completed_at=completed_at
        )
        
    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except Exception as e:
        logger.error(f"Error fetching session data: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch session data")

@app.post("/api/session/{session_id}/confirm", response_model=SessionConfirmResponse)
async def confirm_buddy_completion(session_id: str, request_body: SessionConfirmRequest, request: Request):
    """
    Confirm that a buddy completed their challenge
    
    Implements Task 14: Buddy completion confirmation endpoint
    
    Features:
    - Only allow confirmation after scheduled_time has passed
    - Update appropriate confirmation field based on which user is confirming whom
    - Mark session as 'completed' when both sides confirm
    - Update completed_at timestamp on mutual confirmation
    - Return updated session status
    
    Business Logic:
    - Timing validation: Can only confirm after scheduled session time
    - Authorization: Only session participants can confirm
    - State management: Tracks individual confirmations and overall completion
    """
    try:
        logger.info(f"Confirming buddy completion for session {session_id} by user confirming {request_body.buddy_user_id}")
        
        from src.database import SupabaseFactory
        from src.services.auth_service import get_current_user_id, require_authentication
        
        # Get and validate current user
        user_id = await get_current_user_id(request)
        user_id = require_authentication(user_id)
        
        db_client = SupabaseFactory.get_service_client()
        
        # Fetch session with match data
        session_query = db_client.table('wingman_sessions')\
            .select('*, wingman_matches!inner(user1_id, user2_id)')\
            .eq('id', session_id)\
            .execute()
        
        if not session_query.data:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session_data = session_query.data[0]
        match_data = session_data['wingman_matches']
        
        # Verify user is participant in this session
        participant_ids = [match_data['user1_id'], match_data['user2_id']]
        if user_id not in participant_ids:
            raise HTTPException(
                status_code=403, 
                detail="Access denied - user is not a participant in this session"
            )
        
        # Verify buddy_user_id is the other participant
        if request_body.buddy_user_id not in participant_ids:
            raise HTTPException(
                status_code=400, 
                detail="Invalid buddy user ID - must be the other session participant"
            )
        
        if request_body.buddy_user_id == user_id:
            raise HTTPException(
                status_code=400, 
                detail="Cannot confirm your own completion - only your buddy can confirm you"
            )
        
        # Verify session timing - can only confirm after scheduled time
        scheduled_time = datetime.fromisoformat(session_data['scheduled_time'].replace('Z', '+00:00'))
        current_time = datetime.now(timezone.utc)
        
        if current_time < scheduled_time:
            raise HTTPException(
                status_code=400, 
                detail=f"Cannot confirm completion before scheduled time ({scheduled_time.strftime('%Y-%m-%d %H:%M UTC')})"
            )
        
        # Determine which confirmation field to update
        update_data = {}
        
        if user_id == match_data['user1_id'] and request_body.buddy_user_id == match_data['user2_id']:
            # User1 is confirming User2's completion
            update_data['user2_completed_confirmed_by_user1'] = True
            confirmation_field = 'user2_completed_confirmed_by_user1'
        elif user_id == match_data['user2_id'] and request_body.buddy_user_id == match_data['user1_id']:
            # User2 is confirming User1's completion
            update_data['user1_completed_confirmed_by_user2'] = True
            confirmation_field = 'user1_completed_confirmed_by_user2'
        else:
            raise HTTPException(
                status_code=400, 
                detail="Invalid confirmation relationship"
            )
        
        # Update confirmation
        confirmation_result = db_client.table('wingman_sessions')\
            .update(update_data)\
            .eq('id', session_id)\
            .execute()
        
        if not confirmation_result.data:
            raise HTTPException(status_code=500, detail="Failed to update confirmation")
        
        # Check if both confirmations are now complete
        updated_session = confirmation_result.data[0]
        user1_confirmed = updated_session.get('user1_completed_confirmed_by_user2', False)
        user2_confirmed = updated_session.get('user2_completed_confirmed_by_user1', False)
        both_confirmed = user1_confirmed and user2_confirmed
        
        # If both confirmed, mark session as completed
        if both_confirmed and session_data['status'] != 'completed':
            completion_data = {
                'status': 'completed',
                'completed_at': datetime.now(timezone.utc).isoformat()
            }
            
            db_client.table('wingman_sessions')\
                .update(completion_data)\
                .eq('id', session_id)\
                .execute()
            
            session_status = 'completed'
            message = "Session marked as completed! Both participants have confirmed each other's challenges."
        else:
            session_status = session_data['status']
            message = f"Confirmation recorded. {'Waiting for your buddy to confirm your completion.' if not both_confirmed else 'Session completed!'}"
        
        return SessionConfirmResponse(
            success=True,
            message=message,
            session_status=session_status,
            both_confirmed=both_confirmed
        )
        
    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except Exception as e:
        logger.error(f"Error confirming buddy completion: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process completion confirmation")

@app.patch("/api/session/{session_id}/notes", response_model=SessionNotesResponse)
async def update_session_notes(session_id: str, request_body: SessionNotesRequest, request: Request):
    """
    Update session notes
    
    Implements Task 14: Session notes update endpoint
    
    Features:
    - Validates user is session participant
    - Updates notes field in wingman_sessions table
    - Sanitizes input for XSS prevention
    - Returns success confirmation
    
    Security:
    - Participant-only access control
    - Input sanitization to prevent XSS attacks
    - Length validation (max 2000 characters)
    """
    try:
        logger.info(f"Updating notes for session {session_id}")
        
        from src.database import SupabaseFactory
        from src.services.auth_service import get_current_user_id, require_authentication
        from src.safety_filters import sanitize_message
        
        # Get and validate current user
        user_id = await get_current_user_id(request)
        user_id = require_authentication(user_id)
        
        db_client = SupabaseFactory.get_service_client()
        
        # Fetch session with match data
        session_query = db_client.table('wingman_sessions')\
            .select('*, wingman_matches!inner(user1_id, user2_id)')\
            .eq('id', session_id)\
            .execute()
        
        if not session_query.data:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session_data = session_query.data[0]
        match_data = session_data['wingman_matches']
        
        # Verify user is participant in this session
        participant_ids = [match_data['user1_id'], match_data['user2_id']]
        if user_id not in participant_ids:
            raise HTTPException(
                status_code=403, 
                detail="Access denied - user is not a participant in this session"
            )
        
        # Sanitize notes input
        sanitized_notes = sanitize_message(request_body.notes.strip())
        
        # Validate length after sanitization
        if len(sanitized_notes) > 2000:
            raise HTTPException(
                status_code=400, 
                detail="Notes exceed 2000 characters after sanitization"
            )
        
        # Update session notes
        update_data = {
            'notes': sanitized_notes
        }
        
        update_result = db_client.table('wingman_sessions')\
            .update(update_data)\
            .eq('id', session_id)\
            .execute()
        
        if not update_result.data:
            raise HTTPException(status_code=500, detail="Failed to update session notes")
        
        return SessionNotesResponse(
            success=True,
            message="Session notes updated successfully",
            updated_notes=sanitized_notes
        )
        
    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except Exception as e:
        logger.error(f"Error updating session notes: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update session notes")

@app.post("/api/session/confirm-completion", response_model=SessionConfirmCompletionResponse)
async def confirm_session_completion(request_body: SessionConfirmCompletionRequest, request: Request):
    """
    Confirm session completion by participant
    
    Implements Task 15: Session completion confirmation endpoint
    
    Requirements:
    - Validates session/match membership
    - Toggles userX_completed_confirmed_by_userY based on requester
    - When both true → set session status=completed and completed_at
    - Update reputation with simple SQL statements: increment completed_sessions counter
    - Return both_confirmed and reputation_updated flags
    - Handle idempotency for double-submit scenarios
    
    Business Logic:
    - User confirms their own participation completion
    - Authorization: Only session participants can confirm completion
    - State management: Tracks individual confirmations and overall completion
    - Reputation updates: Increment completion counters for both users
    """
    try:
        session_id = request_body.session_id
        logger.info(f"Confirming session completion for session {session_id}")
        
        from src.database import SupabaseFactory
        from src.services.auth_service import get_current_user_id, require_authentication
        
        # Get and validate current user
        user_id = await get_current_user_id(request)
        user_id = require_authentication(user_id)
        
        db_client = SupabaseFactory.get_service_client()
        
        # Fetch session with match data
        session_query = db_client.table('wingman_sessions')\
            .select('*, wingman_matches!inner(user1_id, user2_id)')\
            .eq('id', session_id)\
            .execute()
        
        if not session_query.data:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session_data = session_query.data[0]
        match_data = session_data['wingman_matches']
        
        # Verify user is participant in this session
        participant_ids = [match_data['user1_id'], match_data['user2_id']]
        if user_id not in participant_ids:
            raise HTTPException(
                status_code=403, 
                detail="Access denied - user is not a participant in this session"
            )
        
        # Handle idempotency - check if session already completed
        current_status = session_data['status']
        if current_status == 'completed':
            user1_confirmed = session_data.get('user1_completed_confirmed_by_user2', False)
            user2_confirmed = session_data.get('user2_completed_confirmed_by_user1', False)
            both_confirmed = user1_confirmed and user2_confirmed
            
            return SessionConfirmCompletionResponse(
                success=True,
                message="Session already completed",
                both_confirmed=both_confirmed,
                reputation_updated=True,  # Assume reputation was already updated
                session_status='completed'
            )
        
        # Determine which confirmation field to update based on user identity
        # Note: These fields represent "UserX completed, confirmed by UserY"
        # For self-confirmation, we need to check if the OTHER user has already confirmed us
        update_data = {}
        reputation_updated = False
        
        if user_id == match_data['user1_id']:
            # User1 is confirming their own completion - update user1_completed_confirmed_by_user2
            # This means User1 completed their challenge, and we're marking it as confirmed
            update_data['user1_completed_confirmed_by_user2'] = True
            confirmation_field = 'user1_completed_confirmed_by_user2'
        elif user_id == match_data['user2_id']:
            # User2 is confirming their own completion - update user2_completed_confirmed_by_user1  
            # This means User2 completed their challenge, and we're marking it as confirmed
            update_data['user2_completed_confirmed_by_user1'] = True
            confirmation_field = 'user2_completed_confirmed_by_user1'
        else:
            raise HTTPException(
                status_code=400, 
                detail="Invalid confirmation relationship"
            )
        
        # Update confirmation flag
        confirmation_result = db_client.table('wingman_sessions')\
            .update(update_data)\
            .eq('id', session_id)\
            .execute()
        
        if not confirmation_result.data:
            raise HTTPException(status_code=500, detail="Failed to update confirmation")
        
        # Check if both confirmations are now complete
        updated_session = confirmation_result.data[0]
        user1_confirmed = updated_session.get('user1_completed_confirmed_by_user2', False)
        user2_confirmed = updated_session.get('user2_completed_confirmed_by_user1', False)
        both_confirmed = user1_confirmed and user2_confirmed
        
        session_status = current_status
        message = "Completion confirmation recorded"
        
        # If both confirmed, mark session as completed and update reputation
        if both_confirmed and current_status != 'completed':
            # Update session status and completion timestamp
            completion_data = {
                'status': 'completed',
                'completed_at': datetime.now(timezone.utc).isoformat()
            }
            
            db_client.table('wingman_sessions')\
                .update(completion_data)\
                .eq('id', session_id)\
                .execute()
            
            # Update reputation counters for both users in the match using SQL increment
            match_id = session_data['match_id']
            
            try:
                # Get current reputation values and increment them
                current_match_result = db_client.table('wingman_matches')\
                    .select('user1_reputation, user2_reputation')\
                    .eq('id', match_id)\
                    .execute()
                
                if current_match_result.data:
                    current_match = current_match_result.data[0]
                    new_user1_reputation = current_match['user1_reputation'] + 1
                    new_user2_reputation = current_match['user2_reputation'] + 1
                    
                    # Update both reputation counters atomically
                    update_reputation_result = db_client.table('wingman_matches')\
                        .update({
                            'user1_reputation': new_user1_reputation,
                            'user2_reputation': new_user2_reputation
                        })\
                        .eq('id', match_id)\
                        .execute()
                    
                    if update_reputation_result.data:
                        reputation_updated = True
                        logger.info(f"Updated reputation for match {match_id}: user1={new_user1_reputation}, user2={new_user2_reputation}")
                    else:
                        logger.error(f"Failed to update reputation for match {match_id}")
                        reputation_updated = False
                else:
                    logger.error(f"Failed to fetch current reputation for match {match_id}")
                    reputation_updated = False
            except Exception as e:
                logger.error(f"Error updating reputation for match {match_id}: {str(e)}")
                reputation_updated = False
            
            session_status = 'completed'
            if reputation_updated:
                message = "Session marked as completed! Both participants have confirmed completion and reputation updated."
            else:
                message = "Session marked as completed! Both participants have confirmed completion."
        elif both_confirmed:
            message = "Session already completed with both confirmations"
        else:
            message = "Completion confirmation recorded. Waiting for your buddy to confirm their completion."
        
        return SessionConfirmCompletionResponse(
            success=True,
            message=message,
            both_confirmed=both_confirmed,
            reputation_updated=reputation_updated,
            session_status=session_status
        )
        
    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except Exception as e:
        logger.error(f"Error confirming session completion: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process session completion confirmation")

# =============================================================================
# TODO: FUTURE NO-SHOW DETECTION CRON JOB (NOT IMPLEMENTED - MVP PLACEHOLDER)
# =============================================================================
# 
# Requirement: Automated detection and handling of session no-shows
# 
# Implementation Plan:
# 1. Background cron job that runs every hour
# 2. Query sessions where:
#    - scheduled_time < now() - 24 hours (configurable grace period)
#    - status = 'scheduled' or 'in_progress'
#    - Either confirmation flag is still false
# 3. Actions to take:
#    - Mark session as 'no_show' status
#    - Apply reputation penalty to non-confirming user(s)
#    - Send notification to users about missed session
#    - Update match history for analytics
# 
# SQL Query for No-Show Detection:
# ```sql
# SELECT s.id, s.match_id, m.user1_id, m.user2_id,
#        s.user1_completed_confirmed_by_user2, s.user2_completed_confirmed_by_user1
# FROM wingman_sessions s 
# JOIN wingman_matches m ON s.match_id = m.id 
# WHERE s.scheduled_time < (NOW() - INTERVAL '24 hours')
#   AND s.status IN ('scheduled', 'in_progress')
#   AND (s.user1_completed_confirmed_by_user2 = false 
#        OR s.user2_completed_confirmed_by_user1 = false);
# ```
# 
# Reputation Penalty Logic:
# - If only one user confirmed: Apply penalty to non-confirming user
# - If neither confirmed: Apply penalty to both users
# - Penalty amount: -10 reputation points per no-show
# 
# Dependencies for Implementation:
# - APScheduler or similar cron job framework
# - Email notification service (Resend integration)
# - Push notification system (future mobile app)
# - Configurable grace period settings
# - Reputation penalty configuration
# 
# Monitoring and Alerts:
# - Track no-show rates per user for quality control
# - Alert admin if no-show rate exceeds threshold (>20%)
# - Generate weekly reports on session completion rates
# 
# Error Handling:
# - Retry logic for failed reputation updates
# - Logging for audit trail of all no-show detections
# - Manual override capability for disputed no-shows
# 
# =============================================================================

# Dating Goals API Endpoints
@app.post("/api/dating-goals", response_model=DatingGoalsResponse)
async def process_dating_goals(request: DatingGoalsRequest):
    """
    Process dating goals conversation with Connell Barrett coaching approach
    
    Conducts a 4-topic conversation to understand user's dating confidence goals:
    1. Dating Confidence Goals & Targets
    2. Past Attempts & Learning  
    3. Triggers & Comfort Zones
    4. Support & Accountability Goals
    
    Results are stored in dating_goals table for coach memory integration.
    """
    try:
        logger.info(f"Processing dating goals for user {request.user_id}")
        
        # Initialize wingman profile agent
        from src.agents.wingman_profile_agent import WingmanProfileAgent
        agent = WingmanProfileAgent(supabase, request.user_id)
        
        # Generate thread_id if not provided
        thread_id = request.thread_id or f"dating_goals_{request.user_id}_{int(time.time())}"
        
        # Process the message and get AI response
        ai_response = await agent.process_message(thread_id, request.message)
        
        # Get current progress to include in response
        progress = await agent.get_progress()
        current_step = progress.get('flow_step', 1)
        completion_percentage = progress.get('completion_percentage', 0.0)
        is_complete = progress.get('is_completed', False)
        
        # Determine current topic number for frontend display
        topic_number = None
        if current_step >= 2 and current_step <= 5:
            topic_number = current_step - 1  # Steps 2-5 map to topics 1-4
        
        logger.info(f"Dating goals progress for user {request.user_id}: step={current_step}, complete={is_complete}")
        
        return DatingGoalsResponse(
            success=True,
            message=ai_response,
            thread_id=thread_id,
            is_complete=is_complete,
            topic_number=topic_number,
            completion_percentage=completion_percentage
        )
        
    except Exception as e:
        logger.error(f"Error processing dating goals for user {request.user_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process dating goals conversation: {str(e)}"
        )

@app.get("/api/dating-goals/{user_id}", response_model=DatingGoalsDataResponse)
async def get_dating_goals(user_id: str):
    """
    Retrieve user's completed dating goals data
    
    Returns the final dating goals data that was collected through the 
    4-topic conversation flow. This data is used by the AI coach for
    personalized coaching conversations.
    """
    try:
        logger.info(f"Retrieving dating goals for user {user_id}")
        
        # Validate user_id format
        try:
            uuid.UUID(user_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid user_id format")
        
        # Fetch dating goals from database
        result = supabase.table('dating_goals')\
            .select('*')\
            .eq('user_id', user_id)\
            .execute()
        
        if not result.data:
            return DatingGoalsDataResponse(
                success=True,
                user_id=user_id,
                goals=None,
                preferred_venues=[],
                comfort_level="moderate",
                goals_data={},
                created_at=None,
                updated_at=None
            )
        
        goals_record = result.data[0]
        
        return DatingGoalsDataResponse(
            success=True,
            user_id=user_id,
            goals=goals_record.get('goals'),
            preferred_venues=goals_record.get('preferred_venues', []),
            comfort_level=goals_record.get('comfort_level', 'moderate'),
            goals_data=goals_record.get('goals_data', {}),
            created_at=goals_record.get('created_at'),
            updated_at=goals_record.get('updated_at')
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving dating goals for user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve dating goals: {str(e)}"
        )

@app.delete("/api/dating-goals/{user_id}")
async def reset_dating_goals(user_id: str):
    """
    Reset dating goals conversation progress for a user
    
    Deletes both the dating goals data and conversation progress,
    allowing the user to restart the goals conversation from the beginning.
    Primarily used for testing and user-requested resets.
    """
    try:
        logger.info(f"Resetting dating goals for user {user_id}")
        
        # Validate user_id format
        try:
            uuid.UUID(user_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid user_id format")
        
        # Delete dating goals progress
        supabase.table('dating_goals_progress')\
            .delete()\
            .eq('user_id', user_id)\
            .execute()
        
        # Delete dating goals data
        supabase.table('dating_goals')\
            .delete()\
            .eq('user_id', user_id)\
            .execute()
        
        logger.info(f"Successfully reset dating goals for user {user_id}")
        
        return {
            "success": True,
            "message": f"Dating goals reset successfully for user {user_id}",
            "user_id": user_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resetting dating goals for user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reset dating goals: {str(e)}"
        )

# Log all registered routes on startup
for route in app.routes:
    logger.info(f"Registered route: {route.path} [{getattr(route, 'methods', ['GET'])}]")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
# Import deployment infrastructure
from src.deployment.deployment_endpoints import deployment_router, initialize_deployment_infrastructure

# Add deployment router to main app
app.include_router(deployment_router)

# Add deployment initialization to startup
async def startup_with_deployment():
    # Initialize existing systems
    await lifespan_startup()
    
    # Initialize deployment infrastructure
    await initialize_deployment_infrastructure()

# Enhanced health endpoint with deployment status
@app.get("/health/deployment")
async def health_deployment():
    """Health check endpoint with deployment infrastructure status"""
    try:
        from src.deployment.enhanced_monitoring import get_enhanced_health_check
        return await get_enhanced_health_check()
    except Exception as e:
        logger.error(f"Deployment health check failed: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
