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

# Import performance monitoring components
from src.middleware.performance_middleware import PerformanceMiddleware
from src.observability.metrics_collector import metrics_collector
from src.observability.alert_system import alert_system, start_alert_monitoring
from src.observability.health_monitor import health_monitor
from src.api.performance_endpoints import performance_router
from src.db.connection_pool import db_pool

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        logger.info("WingmanMatch API starting up...")
        logger.info(f"Environment: {Config.get_environment()}")
        logger.info(f"App identifier: {Config.get_app_identifier()}")
        
        # Initialize Redis connection
        from src.redis_session import RedisSession
        await RedisSession.initialize()
        redis_health = await RedisSession.health_check()
        logger.info(f"Redis service initialized: {redis_health}")
        
        # Initialize database connection pool
        if Config.ENABLE_CONNECTION_POOLING:
            pool_initialized = await db_pool.initialize()
            logger.info(f"Database connection pool initialized: {pool_initialized}")
        
        # Initialize database connections (legacy)
        from src.database import SupabaseFactory
        db_health = SupabaseFactory.health_check()
        logger.info(f"Database health: {db_health}")
        
        # Initialize email service
        from src.email_templates import email_service
        logger.info(f"Email service enabled: {email_service.enabled}")
        
        # Start performance monitoring
        if Config.ENABLE_PERFORMANCE_MONITORING:
            logger.info("Performance monitoring enabled")
            
            # Start alert monitoring in background
            if Config.ENABLE_PERFORMANCE_ALERTS:
                asyncio.create_task(start_alert_monitoring())
                logger.info("Alert monitoring started")
        
        # Log feature flags
        feature_flags = Config.get_feature_flags()
        logger.info(f"Feature flags: {feature_flags}")
        
        # Log performance monitoring config
        perf_config = Config.get_performance_monitoring_config()
        logger.info(f"Performance monitoring: {perf_config}")
        
        # Log optional service status
        optional_status = Config.validate_optional_config()
        logger.info(f"Optional services: {optional_status}")
        
    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")
    
    yield
    
    # Shutdown
    try:
        # Close database connection pool
        if Config.ENABLE_CONNECTION_POOLING:
            await db_pool.close()
            logger.info("Database connection pool closed")
        
        # Close Redis connections
        from src.redis_session import RedisSession
        await RedisSession.cleanup()
        logger.info("Redis service closed")
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
    description="AI-powered wingman matching platform for shared challenges with performance monitoring",
    version="2.0.0",
    lifespan=lifespan
)

# Add performance middleware if enabled
if Config.ENABLE_PERFORMANCE_MONITORING:
    performance_middleware = PerformanceMiddleware(app)
    app.middleware("http")(performance_middleware)
    # Store global reference for access
    from src.middleware.performance_middleware import performance_middleware as global_middleware
    global_middleware = performance_middleware

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

# Include performance monitoring endpoints
app.include_router(performance_router)

# Pydantic models for API requests/responses
class HealthResponse(BaseModel):
    status: str
    timestamp: str
    message: str
    environment: str
    features: Dict[str, bool]
    performance_enabled: bool = False

# Enhanced health endpoint with performance monitoring
@app.get("/health", response_model=HealthResponse)
async def health():
    """Enhanced health check with performance monitoring status"""
    try:
        features = Config.get_feature_flags()
        perf_config = Config.get_performance_monitoring_config()
        
        # Basic health check
        health_status = "healthy"
        
        # Check performance monitoring if enabled
        if Config.ENABLE_PERFORMANCE_MONITORING:
            try:
                from src.observability.health_monitor import get_quick_health
                perf_health = await get_quick_health()
                if not perf_health.get("healthy", True):
                    health_status = "degraded"
            except Exception as e:
                logger.warning(f"Performance health check failed: {e}")
                health_status = "degraded"
        
        return HealthResponse(
            status=health_status,
            timestamp=datetime.now(timezone.utc).isoformat(),
            message="WingmanMatch API is running" + (" with performance monitoring" if Config.ENABLE_PERFORMANCE_MONITORING else ""),
            environment=Config.get_environment(),
            features=features,
            performance_enabled=Config.ENABLE_PERFORMANCE_MONITORING
        )
    except Exception as e:
        logger.error(f"Health check error: {e}")
        raise HTTPException(status_code=500, detail="Health check failed")

# Root endpoint
@app.get("/", response_model=Dict)
async def root():
    """Root endpoint with API information including performance monitoring"""
    features = []
    if Config.ENABLE_PERFORMANCE_MONITORING:
        features.append("performance-monitoring")
    if Config.ENABLE_CONNECTION_POOLING:
        features.append("connection-pooling")
    if Config.ENABLE_PERFORMANCE_ALERTS:
        features.append("performance-alerts")
    
    return {
        "message": "Welcome to WingmanMatch API",
        "description": "AI-powered wingman matching platform for shared challenges",
        "version": "2.0.0",
        "features": features,
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "performance": "/api/performance"
        }
    }

# Example endpoint with performance tracking
@app.get("/api/test-performance")
async def test_performance_endpoint(request: Request):
    """Test endpoint to demonstrate performance monitoring"""
    try:
        # Record custom metric
        await metrics_collector.record_metric(
            metric_type="request",
            name="test_performance",
            value=100.0,
            unit="ms",
            tags={"endpoint": "/api/test-performance"}
        )
        
        # Simulate some work
        await asyncio.sleep(0.1)
        
        return {
            "message": "Performance test endpoint",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "performance_monitoring": Config.ENABLE_PERFORMANCE_MONITORING,
            "connection_pooling": Config.ENABLE_CONNECTION_POOLING
        }
        
    except Exception as e:
        logger.error(f"Test performance endpoint error: {e}")
        raise HTTPException(status_code=500, detail="Test endpoint failed")

# Add background task for cleanup
@app.post("/api/admin/cleanup-metrics")
async def cleanup_metrics(background_tasks: BackgroundTasks):
    """Admin endpoint to trigger metrics cleanup"""
    background_tasks.add_task(metrics_collector.cleanup_old_metrics, 48)
    return {"message": "Metrics cleanup scheduled"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main_with_performance:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
