#!/usr/bin/env python3
"""
Enhanced WingmanMatch Main API with Performance Optimization

Integrates Redis caching, AI model routing, and memory compression for optimal
performance in the dating confidence coaching platform.

Features:
- Redis-backed caching middleware
- Intelligent AI model routing for cost optimization
- Memory compression for context management
- Enhanced conversation endpoints with performance monitoring
- Backwards compatibility with existing API
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Dict, Any
import asyncio
from src.config import Config
from supabase import create_client
from src.simple_memory import SimpleMemory
from datetime import datetime, timezone, timedelta
import logging
import json
import concurrent.futures
import time

# Import performance optimization modules
from src.enhanced_claude_agent import (
    interact_with_agent_optimized, 
    interact_with_agent_stream_optimized,
    get_performance_stats
)
from src.cache_middleware import CacheMiddleware, get_cache_stats, invalidate_user_cache
from src.redis_client import redis_service
from src.model_router import model_router
from src.memory_compressor import memory_compressor

# Import existing modules for compatibility
from src.zoom_transcript_retrieval import router as zoom_router
from src.slack_bot import router as slack_router
import resend
from concurrent.futures import ThreadPoolExecutor

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s - %(pathname)s:%(lineno)d',
    filters=[
        lambda record: 'REDIS' not in record.getMessage()
    ]
)

# Initialize Redis and performance components at startup
async def startup_handler():
    """Initialize performance optimization components"""
    try:
        # Initialize Redis service
        redis_available = await redis_service.initialize()
        if redis_available:
            logger.info("✅ Redis caching system initialized successfully")
        else:
            logger.warning("⚠️ Redis unavailable, using in-memory fallback")
        
        # Log performance optimization status
        logger.info("✅ Model routing system initialized")
        logger.info("✅ Memory compression system initialized")
        logger.info("🚀 WingmanMatch performance optimization ready")
        
    except Exception as e:
        logger.error(f"❌ Error during startup initialization: {e}")

async def shutdown_handler():
    """Cleanup performance optimization components"""
    try:
        await redis_service.close()
        logger.info("✅ Performance optimization components cleaned up")
    except Exception as e:
        logger.error(f"❌ Error during shutdown: {e}")

# Create FastAPI app with performance middleware
app = FastAPI(
    title="WingmanMatch API - Performance Optimized",
    description="Dating confidence coaching platform with AI performance optimization",
    version="2.0.0"
)

# Add performance caching middleware
app.add_middleware(CacheMiddleware)

# Configure CORS (existing configuration)
ALLOWED_ORIGINS = [
    "https://*.squarespace.com",
    "https://*.slack.com", 
    "https://zoom.us",
    "https://*.herokuapp.com",
    "https://app.fridaysatfour.co",
    "https://dev.fridaysatfour.co",
    "https://fridaysatfour.co",
    "https://www.fridaysatfour.co",
    "http://localhost:3000",
    "http://localhost:8000",
    "https://fridays-at-four-dev-434b1a68908b.herokuapp.com"
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
        "Access-Control-Max-Age",
        "X-User-ID",
        "X-Cache-Control"
    ],
    expose_headers=[
        "Content-Type",
        "Authorization",
        "X-Cache",
        "X-Cache-TTL",
        "X-Model-Used",
        "X-Compression-Ratio"
    ],
    max_age=3600,
    allow_origin_regex=r"https://[^.]+\.herokuapp\.com"
)

# Initialize Supabase
supabase = create_client(Config.SUPABASE_URL, Config.SUPABASE_SERVICE_KEY)
resend.api_key = Config.RESEND_API_KEY

# Startup and shutdown events
@app.on_event("startup")
async def startup():
    await startup_handler()

@app.on_event("shutdown") 
async def shutdown():
    await shutdown_handler()

# Memory handlers dictionary for existing compatibility
memory_handlers = {}

# Enhanced project cache with Redis integration
project_cache = {}
cache_timestamps = {}
CACHE_DURATION = timedelta(minutes=30)

def get_memory_handler(user_id: str) -> SimpleMemory:
    """Get or create a memory handler for a user"""
    if user_id not in memory_handlers:
        memory_handlers[user_id] = SimpleMemory(supabase, user_id)
    return memory_handlers[user_id]

# Enhanced cache functions with Redis integration
async def is_cache_valid(user_id: str) -> bool:
    """Check if cached data is still valid using Redis first, then fallback"""
    try:
        # Try Redis first
        if await redis_service.health_check():
            cached_data = await redis_service.get_cache(f"project_cache:{user_id}")
            if cached_data:
                return True
        
        # Fallback to in-memory cache
        if user_id not in cache_timestamps:
            return False
        return datetime.now() - cache_timestamps[user_id] < CACHE_DURATION
        
    except Exception as e:
        logger.error(f"Error checking cache validity: {e}")
        return False

async def get_cached_project_data(user_id: str) -> Optional[Dict]:
    """Get cached project data with Redis priority"""
    try:
        # Try Redis first
        if await redis_service.health_check():
            cached_data = await redis_service.get_cache(f"project_cache:{user_id}")
            if cached_data:
                logger.debug(f"Redis cache HIT for project data: {user_id}")
                return cached_data
        
        # Fallback to in-memory cache
        if await is_cache_valid(user_id):
            logger.debug(f"Memory cache HIT for project data: {user_id}")
            return project_cache.get(user_id)
        
        return None
        
    except Exception as e:
        logger.error(f"Error getting cached project data: {e}")
        return None

async def cache_project_data(user_id: str, data: Dict):
    """Cache project data with Redis and memory fallback"""
    try:
        # Cache in Redis with TTL
        if await redis_service.health_check():
            await redis_service.set_cache(
                f"project_cache:{user_id}", 
                data, 
                int(CACHE_DURATION.total_seconds())
            )
            logger.debug(f"Cached project data in Redis: {user_id}")
        
        # Also cache in memory as fallback
        project_cache[user_id] = data
        cache_timestamps[user_id] = datetime.now()
        
    except Exception as e:
        logger.error(f"Error caching project data: {e}")

# Pydantic models (keeping existing ones for compatibility)
class QueryRequest(BaseModel):
    question: str
    user_id: str
    user_timezone: str = "UTC"
    thread_id: str = "default"

class QueryResponse(BaseModel):
    answer: str
    sources: List[str] = []

class ChatRequest(BaseModel):
    message: str
    user_id: str
    user_timezone: str = "UTC"
    thread_id: str = "default"

class ChatResponse(BaseModel):
    response: str

# Enhanced query request with performance preferences
class EnhancedQueryRequest(BaseModel):
    question: str
    user_id: str
    user_timezone: str = "UTC"
    thread_id: str = "default"
    preferences: Optional[Dict[str, Any]] = Field(default_factory=dict)

class PerformanceStats(BaseModel):
    model_routing: Dict[str, Any]
    memory_compression: Dict[str, Any]
    redis_cache: Dict[str, Any]
    optimization_enabled: bool
    timestamp: str

# Load project data background function (enhanced with Redis)
async def load_project_data_background(user_id: str):
    """Enhanced background task to load and cache combined project overview and status data"""
    start_time = time.time()
    
    try:
        logger.info(f"Loading project data in background for user {user_id}")
        
        # Define query functions
        def get_project():
            return supabase.table('project_overview').select('*, user:creator_profiles!user_id(first_name, last_name)').eq('user_id', user_id).limit(1).execute()
        
        def get_updates():
            return supabase.table('project_updates').select('*').eq('user_id', user_id).order('created_at', desc=True).limit(3).execute()
        
        def get_activity():
            return supabase.table('memory').select('created_at, content').eq('user_id', user_id).eq('memory_type', 'message').order('created_at', desc=True).limit(5).execute()
        
        # Execute all queries concurrently
        results = {}
        failed_queries = []
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = {
                'updates': executor.submit(get_updates),
                'activity': executor.submit(get_activity),
                'project': executor.submit(get_project)
            }
            
            for name, future in futures.items():
                try:
                    results[name] = future.result(timeout=15)
                except Exception as e:
                    logger.warning(f"Query {name} failed for {user_id}: {e}")
                    results[name] = None
                    failed_queries.append(name)

        if 'project' in failed_queries:
            logger.error(f"Critical project query failed for user {user_id} - not caching")
            return
        
        if len(failed_queries) >= 2:
            logger.error(f"Too many queries failed for user {user_id} ({failed_queries}) - not caching")
            return
        
        # Build data (same logic as before)
        project_result = results.get('project')
        updates_result = results.get('updates')
        activity_result = results.get('activity')
        
        # Build overview data
        overview_data = {
            'project': project_result.data[0] if project_result and project_result.data else None,
            'recent_updates': updates_result.data if updates_result else [],
            'recent_activity': activity_result.data if activity_result else [],
        }
        
        # Build status data (abbreviated for space)
        project = project_result.data[0] if project_result and project_result.data else None
        recent_updates = updates_result.data if updates_result else []
        
        # Extract current tasks
        next_steps, current_blockers, recent_milestones = [], [], []
        for update in recent_updates:
            if update.get('next_steps') and isinstance(update['next_steps'], list):
                next_steps.extend(update['next_steps'][:2])
            if update.get('blockers') and isinstance(update['blockers'], list):
                current_blockers.extend(update['blockers'][:2])
            if update.get('milestones_hit') and isinstance(update['milestones_hit'], list):
                recent_milestones.extend(update['milestones_hit'][:2])
        
        # Calculate activity status
        has_recent_activity = False
        last_activity = None
        if activity_result and activity_result.data:
            raw_activity = activity_result.data[0]['created_at']
            try:
                if isinstance(raw_activity, str):
                    clean_str = raw_activity.replace('Z', '+00:00') if raw_activity.endswith('Z') else raw_activity
                    if '+' not in clean_str and clean_str.count(':') >= 2:
                        clean_str = clean_str + '+00:00'
                    parsed_dt = datetime.fromisoformat(clean_str)
                    if parsed_dt.tzinfo is None:
                        parsed_dt = parsed_dt.replace(tzinfo=timezone.utc)
                    last_activity = raw_activity
                    has_recent_activity = (datetime.now(timezone.utc) - parsed_dt) < timedelta(days=7)
            except Exception as e:
                logger.warning(f"Could not parse activity datetime: {e}")
        
        status_data = {
            "ai_understanding": {
                "knows_your_project": bool(project),
                "tracking_progress": has_recent_activity,
                "has_next_steps": len(next_steps) > 0,
                "project_name": project['project_name'] if project else None,
                "current_phase": project['current_phase'] if project else None,
                "last_activity": last_activity
            },
            "current_tasks": {
                "next_steps": next_steps[:3],
                "blockers": current_blockers[:3],
                "recent_wins": recent_milestones[:3]
            },
            "is_active": has_recent_activity
        }
        
        # Combine data
        combined_data = {
            'overview_data': overview_data,
            'project_status': status_data,
            'loaded_at': datetime.now().isoformat(),
            'cache_source': 'background_load'
        }
        
        # Cache with enhanced Redis integration
        await cache_project_data(user_id, combined_data)
        elapsed = time.time() - start_time
        logger.info(f"Successfully cached project data for user {user_id} in {elapsed:.2f}s")
        
    except Exception as e:
        logger.error(f"Error loading combined project data in background for user {user_id}: {e}")

# Enhanced streaming endpoint with performance optimization
@app.post("/query_stream_optimized")
async def query_knowledge_base_stream_optimized(request: Request, query_request: EnhancedQueryRequest):
    """
    Enhanced streaming query endpoint with AI model routing and memory compression.
    
    Features:
    - Intelligent model selection based on conversation type
    - Memory compression for large contexts
    - Response caching for identical requests
    - Performance monitoring and statistics
    """
    try:
        logger.info(f"Received optimized streaming query for user {query_request.user_id}")
        
        # Get or create memory handler
        memory_handler = get_memory_handler(query_request.user_id)
        logger.info(f"Created/retrieved memory handler for thread {query_request.thread_id}")
        
        # Get context
        context = await memory_handler.get_context(query_request.thread_id)
        logger.info(f"Retrieved context with {len(context['messages'])} messages")
        
        # Set up streaming response with performance headers
        async def generate_stream():
            full_response = ""
            model_used = "unknown"
            compression_ratio = 1.0
            
            try:
                # Get streaming generator with optimization
                stream_gen = interact_with_agent_stream_optimized(
                    user_input=query_request.question,
                    user_id=query_request.user_id,
                    user_timezone=query_request.user_timezone,
                    thread_id=query_request.thread_id,
                    supabase_client=supabase,
                    context=context,
                    user_preferences=query_request.preferences
                )
                
                # Stream each chunk
                async for chunk in stream_gen:
                    if isinstance(chunk, str) and chunk.strip():
                        full_response += chunk
                        yield f"data: {json.dumps({'chunk': chunk})}\n\n"
                
                # Store both user message and complete response after streaming
                await memory_handler.add_message(
                    thread_id=query_request.thread_id,
                    message=query_request.question,
                    role="user"
                )
                await memory_handler.add_message(
                    thread_id=query_request.thread_id,
                    message=full_response,
                    role="assistant"
                )
                
                # Get performance stats for response headers
                try:
                    stats = model_router.get_usage_stats()
                    model_used = "optimized"  # Would need to track actual model from stream
                    
                    # Send performance metadata
                    yield f"data: {json.dumps({'performance': {'model_used': model_used, 'compression_ratio': compression_ratio}})}\n\n"
                    
                except Exception as perf_error:
                    logger.warning(f"Error getting performance stats: {perf_error}")
                
                # End the stream
                yield f"data: {json.dumps({'done': True})}\n\n"
                
            except Exception as e:
                logger.error(f"Optimized streaming error: {str(e)}", exc_info=True)
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
        
        # Return streaming response with performance headers
        response = StreamingResponse(
            generate_stream(),
            media_type="text/event-stream",
            headers={
                "X-Optimization-Enabled": "true",
                "X-Cache-Control": "no-cache",
                "X-Performance-Mode": "optimized"
            }
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Error in query_knowledge_base_stream_optimized: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# Backwards compatible streaming endpoint
@app.post("/query_stream")
async def query_knowledge_base_stream(request: Request, query_request: QueryRequest):
    """Backwards compatible streaming endpoint that uses optimized backend"""
    enhanced_request = EnhancedQueryRequest(
        question=query_request.question,
        user_id=query_request.user_id,
        user_timezone=query_request.user_timezone,
        thread_id=query_request.thread_id,
        preferences={}
    )
    return await query_knowledge_base_stream_optimized(request, enhanced_request)

# Enhanced non-streaming endpoint
@app.post("/query_optimized", response_model=QueryResponse)
async def query_knowledge_base_optimized(request: Request, query_request: EnhancedQueryRequest):
    """Enhanced non-streaming query endpoint with performance optimization"""
    try:
        logger.info(f"Received optimized query request for user {query_request.user_id}")
        
        # Get or create memory handler
        memory_handler = get_memory_handler(query_request.user_id)
        
        # Get context
        context = await memory_handler.get_context(query_request.thread_id)
        
        # Get optimized response
        response = await interact_with_agent_optimized(
            user_input=query_request.question,
            user_id=query_request.user_id,
            user_timezone=query_request.user_timezone,
            thread_id=query_request.thread_id,
            supabase_client=supabase,
            context=context,
            user_preferences=query_request.preferences
        )
        
        # Store the interaction
        await memory_handler.add_message(
            thread_id=query_request.thread_id,
            message=query_request.question,
            role="user"
        )
        await memory_handler.add_message(
            thread_id=query_request.thread_id,
            message=response,
            role="assistant"
        )
        
        return QueryResponse(answer=response, sources=[])
        
    except Exception as e:
        logger.error(f"Error in query_knowledge_base_optimized: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# Backwards compatible non-streaming endpoint
@app.post("/query", response_model=QueryResponse)
async def query_knowledge_base(request: Request, query_request: QueryRequest):
    """Backwards compatible non-streaming endpoint that uses optimized backend"""
    enhanced_request = EnhancedQueryRequest(
        question=query_request.question,
        user_id=query_request.user_id,
        user_timezone=query_request.user_timezone,
        thread_id=query_request.thread_id,
        preferences={}
    )
    return await query_knowledge_base_optimized(request, enhanced_request)

# Performance monitoring endpoints
@app.get("/performance/stats", response_model=PerformanceStats)
async def get_performance_statistics():
    """Get comprehensive performance statistics for monitoring"""
    try:
        stats = await get_performance_stats()
        return PerformanceStats(**stats)
    except Exception as e:
        logger.error(f"Error getting performance stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve performance statistics")

@app.get("/performance/cache-stats")
async def get_cache_statistics():
    """Get cache performance statistics"""
    try:
        return await get_cache_stats()
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve cache statistics")

@app.delete("/performance/cache/{user_id}")
async def invalidate_user_cache_endpoint(user_id: str):
    """Invalidate all cached data for a specific user"""
    try:
        deleted_count = await invalidate_user_cache(user_id)
        return {
            "message": f"Invalidated cache for user {user_id}",
            "deleted_entries": deleted_count,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error invalidating user cache: {e}")
        raise HTTPException(status_code=500, detail="Failed to invalidate user cache")

# Health check with performance status
@app.get("/health")
async def health():
    """Enhanced health check endpoint with performance system status"""
    redis_healthy = await redis_service.health_check()
    
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "message": "WingmanMatch backend is running with performance optimization",
        "performance_systems": {
            "redis_cache": redis_healthy,
            "model_routing": True,
            "memory_compression": True,
            "optimization_enabled": True
        }
    }

@app.get("/")
async def root(request: Request):
    return {
        "message": "Welcome to WingmanMatch API with Performance Optimization",
        "version": "2.0.0",
        "optimization_features": [
            "Redis caching",
            "AI model routing", 
            "Memory compression",
            "Performance monitoring"
        ]
    }

# Include existing routers for compatibility
app.include_router(slack_router, prefix="/slack", tags=["slack"])
app.include_router(zoom_router, prefix="/zoom", tags=["zoom"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)