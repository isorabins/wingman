from fastapi import FastAPI, HTTPException, BackgroundTasks, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Dict, Any
from uuid import UUID
import asyncio
from src.config import Config
from supabase import create_client
from datetime import datetime, timezone, timedelta
import logging
from contextlib import asynccontextmanager
import json
import time

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
        
    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")
    
    yield
    
    # Shutdown
    try:
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
    "http://localhost:8000",         # Local API development
    "http://127.0.0.1:3000",         # Alternative localhost
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

# Simple in-memory cache for session data
session_cache = {}
cache_timestamps = {}
CACHE_DURATION = timedelta(hours=Config.SESSION_TIMEOUT_HOURS)

def is_cache_valid(session_key: str) -> bool:
    """Check if cached session data is still valid"""
    if session_key not in cache_timestamps:
        return False
    return datetime.now() - cache_timestamps[session_key] < CACHE_DURATION

def get_cached_session(session_key: str) -> Optional[Dict]:
    """Get cached session data if valid"""
    if is_cache_valid(session_key):
        return session_cache.get(session_key)
    return None

def cache_session_data(session_key: str, data: Dict):
    """Cache session data with timestamp"""
    session_cache[session_key] = data
    cache_timestamps[session_key] = datetime.now()

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
    """Get email service status"""
    from src.email_service import email_service
    return email_service.get_service_status()

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
    """Chat with Connell Barrett for dating confidence coaching"""
    if not Config.ENABLE_AI_COACHING:
        raise HTTPException(status_code=503, detail="AI coaching is currently disabled")
    
    try:
        from src.claude_agent import interact_with_coach
        from src.llm_router import get_coaching_config
        import uuid
        
        # Generate thread_id if not provided
        thread_id = request.thread_id or str(uuid.uuid4())
        
        # Get coaching response
        response_text = await interact_with_coach(
            user_input=request.message,
            user_id=request.user_id,
            thread_id=thread_id
        )
        
        # Store conversation
        from src.claude_agent import store_coaching_conversation
        await store_coaching_conversation(
            user_id=request.user_id,
            thread_id=thread_id,
            user_input=request.message,
            coach_response=response_text
        )
        
        # Get model info for response
        model_config = get_coaching_config()
        
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

# Log all registered routes on startup
for route in app.routes:
    logger.info(f"Registered route: {route.path} [{getattr(route, 'methods', ['GET'])}]")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)