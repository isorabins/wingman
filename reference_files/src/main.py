from fastapi import FastAPI, HTTPException, BackgroundTasks, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Dict
import asyncio
from src.config import Config
from supabase import create_client
from src.simple_memory import SimpleMemory
from src.claude_agent import interact_with_agent, interact_with_agent_stream
from datetime import datetime, timezone, timedelta
import logging
from src.zoom_transcript_retrieval import router as zoom_router
from src.zoom_transcript_retrieval import process_meeting_content
from src.zoom_oauth import get_access_token
from fastapi import APIRouter, HTTPException, Request
import requests
from src.config import Config
from typing import Dict, Optional, Any
from pydantic import ValidationError
from contextlib import asynccontextmanager
from src.slack_bot import handler
from src.slack_bot import router as slack_router
import json
import concurrent.futures
import resend
from concurrent.futures import ThreadPoolExecutor
import time

resend.api_key = Config.RESEND_API_KEY 
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        logger.info("Skipping meeting checks on startup because webhook-only mode is enabled.")
    except Exception as e:
        logger.error(f"Error checking meetings on startup: {str(e)}")
    
    yield

# Set up loggings
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.DEBUG,  # Changed to DEBUG for more detailed logs
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s - %(pathname)s:%(lineno)d',
    filters=[
        lambda record: 'REDIS' not in record.getMessage()
    ]
)

# Add a specific logger for Slack verification
slack_logger = logging.getLogger('slack_verification')
slack_logger.setLevel(logging.DEBUG)

# Initialize FastAPI app
app = FastAPI(title="Fridays at Four API", lifespan=lifespan)
router = APIRouter()
supabase = create_client(Config.SUPABASE_URL, Config.SUPABASE_SERVICE_KEY)
#resend email notifications for signups

class NotificationData(BaseModel):
    table: str
    record: dict

@app.post("/send-notification")
async def send_notification(data: NotificationData):
    # List of tables you want notifications from
    NOTIFICATION_TABLES = [
        "waitlist", 
        "applications", 
        "beta_feedback", 
        "creativity_test_results", 
        "creator_profiles"
    ]
    
    # Only send emails for these tables
    if data.table not in NOTIFICATION_TABLES:
        return {"success": True, "message": "Table not in notification list"}
    
    try:
        email = resend.Emails.send({
            "from": "hello@fridaysatfour.co",  
            "to": ["iso@fridaysatfour.co"],
            "subject": f"New {data.table} signup - Fridays at Four",
            "html": f"<h3>New entry in {data.table}</h3><pre>{data.record}</pre>"
        })
        return {"success": True, "email_id": email}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
# Configure CORS
ALLOWED_ORIGINS = [
    "https://*.squarespace.com",
    "https://*.slack.com",
    "https://zoom.us",
    "https://*.herokuapp.com",  # Allow all Heroku domains
    "https://app.fridaysatfour.co",  # Frontend domain (legacy)
    "https://dev.fridaysatfour.co",  # Dev frontend domain
    "https://fridaysatfour.co",      # Root domain
    "https://www.fridaysatfour.co",  # www subdomain
    "http://localhost:3000",         # Local development
    "http://localhost:8000",         # Local API development
    "https://fridays-at-four-dev-434b1a68908b.herokuapp.com"  # Specific dev instance
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

# Dictionary to store memory handlers
memory_handlers = {}

# Simple in-memory cache for project data
project_cache = {}
cache_timestamps = {}
CACHE_DURATION = timedelta(minutes=30)  # Cache for 30 mins

def is_cache_valid(user_id: str) -> bool:
    """Check if cached data is still valid"""
    if user_id not in cache_timestamps:
        return False
    return datetime.now() - cache_timestamps[user_id] < CACHE_DURATION

def get_cached_project_data(user_id: str) -> Optional[Dict]:
    """Get cached project data if valid"""
    if is_cache_valid(user_id):
        return project_cache.get(user_id)
    return None

def cache_project_data(user_id: str, data: Dict):
    """Cache project data with timestamp"""
    project_cache[user_id] = data
    cache_timestamps[user_id] = datetime.now()
def load_project_data_background(user_id: str):
    """Fast concurrent background task to load and cache combined project overview and status data"""
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
            # Submit all queries
            futures = {
                'updates': executor.submit(get_updates),
                'activity': executor.submit(get_activity),
                'project': executor.submit(get_project)
            }
            
            # Collect results with timeout
            for name, future in futures.items():
                try:
                    results[name] = future.result(timeout=15)  # 15 second timeout
                except Exception as e:
                    logger.warning(f"Query {name} failed for {user_id}: {e}")
                    results[name] = None
                    failed_queries.append(name)

        if 'project' in failed_queries:
            logger.error(f"Critical project query failed for user {user_id} - not caching")
            return  # Don't cache if main project query fails
        
        # If too many queries failed, don't cache
        if len(failed_queries) >= 2:  # If 2 out of 3 queries failed
            logger.error(f"Too many queries failed for user {user_id} ({failed_queries}) - not caching")
            return
        
        # Extract results (same as your original code)
        project_result = results.get('project')
        updates_result = results.get('updates')
        activity_result = results.get('activity')
        
        # Build overview data
        overview_data = {
            'project': project_result.data[0] if project_result and project_result.data else None,
            'recent_updates': updates_result.data if updates_result else [],
            'recent_activity': activity_result.data if activity_result else [],
        }
        
        # Build status data
        project = project_result.data[0] if project_result and project_result.data else None
        recent_updates = updates_result.data if updates_result else []
        
        # Extract current tasks from updates
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
        
        # Combine overview and status data (UNCHANGED)
        combined_data = {
            'overview_data': overview_data,
            'project_status': status_data,
            'loaded_at': datetime.now().isoformat()
        }
        # Cache the combined data
        cache_project_data(user_id, combined_data)
        elapsed = time.time() - start_time
        logger.info(f"Successfully cached project data for user {user_id} in {elapsed:.2f}s")
        
    except Exception as e:
        logger.error(f"Error loading combined project data in background for user {user_id}: {e}")

# Pydantic models
class QueryRequest(BaseModel):
    question: str
    user_id: str
    user_timezone: str
    thread_id: str

class QueryResponse(BaseModel):
    answer: str
    sources: List[str]

class ChatRequest(BaseModel):
    message: str
    user_id: str
    user_timezone: str = "UTC"
    thread_id: str = "default"

class ChatResponse(BaseModel):
    response: str
    
class ChatHistoryItem(BaseModel):
    role: str
    content: str
    timestamp: str

# Sub-models for structured data
class Goal(BaseModel):
    goal: str
    description: str

class Challenge(BaseModel):
    challenge: str
    description: str

class ProjectOverview(BaseModel):
    id: str
    user_id: str
    project_name: str
    project_type: str
    description: str
    current_phase: str
    goals: List[Goal]  # CORRECTED: database actually stores as List[dict] with goal/description
    challenges: List[Challenge]  # CORRECTED: database actually stores as List[dict] with challenge/description
    success_metrics: dict
    creation_date: str
    last_updated: str

class TopTasks(BaseModel):
    next_steps: List[str]
    current_blockers: List[str] 
    recent_milestones: List[str]

class ProjectStatus(BaseModel):
    recent_updates: List[dict]
    last_activity: Optional[str]
    has_recent_activity: bool
    update_count: int

class EnhancedProjectOverview(BaseModel):
    # All original ProjectOverview fields
    id: str
    user_id: str
    project_name: str
    project_type: str
    description: str
    current_phase: str
    goals: List[Goal]  # CORRECTED: database actually stores as List[dict] with goal/description
    challenges: List[Challenge]  # CORRECTED: database actually stores as List[dict] with challenge/description
    success_metrics: dict
    creation_date: str
    last_updated: str
    # Enhanced fields
    project_status: ProjectStatus
    top_tasks: TopTasks

class ProjectUpdate(BaseModel):
    id: str
    project_id: str
    user_id: str
    update_date: str
    progress_summary: str
    milestones_hit: List[str]
    blockers: List[str]
    next_steps: List[str]
    mood_rating: Optional[int]
    created_at: str

class AIUnderstanding(BaseModel):
    knows_your_project: bool
    tracking_progress: bool
    has_next_steps: bool
    project_name: Optional[str]
    current_phase: Optional[str]
    last_activity: Optional[str]

class CurrentTasks(BaseModel):
    next_steps: List[str]
    blockers: List[str]
    recent_wins: List[str]

class GoalsProgress(BaseModel):
    primary_goals: List[Goal]
    main_challenges: List[Challenge]

class ProjectStatusResponse(BaseModel):
    ai_understanding: AIUnderstanding
    current_tasks: CurrentTasks
    project_summary: dict
    goals_progress: GoalsProgress
    project_overview: Optional[ProjectOverview]
    recent_updates: List[ProjectUpdate]
    is_active: bool

class ApplicationSubmission(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    project_type: str
    responses: Dict

class ProjectStatus(BaseModel):
    project_overview: Optional[ProjectOverview]
    recent_updates: List[ProjectUpdate]
    total_updates: int

def get_memory_handler(user_id: str) -> SimpleMemory:
    """Get or create a memory handler for a user"""
    if user_id not in memory_handlers:
        memory_handlers[user_id] = SimpleMemory(supabase, user_id)
    return memory_handlers[user_id]

@app.get("/chat-history/{user_id}")
async def get_chat_history(user_id: str, limit: int = 50, offset: int = 0):
    """Get chat history for a user"""
    try:
        logger.info(f"Fetching chat history for user {user_id}")
        
        # Get messages from memory table
        result = supabase.table('memory')\
            .select('*')\
            .eq('user_id', user_id)\
            .eq('memory_type', 'message')\
            .order('created_at', desc=True)\
            .range(offset, offset + limit - 1)\
            .execute()
        
        messages = []
        for item in result.data:
            content = item.get('content', '')
            # Parse role and content from stored format
            if ':' in content:
                role, message_content = content.split(':', 1)
                messages.append({
                    'role': role.strip(),
                    'content': message_content.strip(),
                    'timestamp': item.get('created_at', '')
                })
        
        return messages
        
    except Exception as e:
        logger.error(f"Error fetching chat history: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# Add new flexible response model for project overview
class ProjectOverviewResponse(BaseModel):
    status: str  # "cached", "loading", "error"
    data: Optional[Dict] = None
    message: Optional[str] = None
    cache_age_minutes: Optional[int] = None

@app.get("/project-overview/{user_id}")
async def get_project_overview(user_id: str, background_tasks: BackgroundTasks):
    """Get project overview - returns cached data immediately or triggers background load"""
    try:
        logger.info(f"Project overview requested for user {user_id}")
        
        # Check cache first
        cached_data = get_cached_project_data(user_id)
        if cached_data:
            logger.info(f"Returning cached project data for user {user_id}")
            return ProjectOverviewResponse(
                status="cached",
                data=cached_data,
                cache_age_minutes=int((datetime.now() - cache_timestamps[user_id]).total_seconds() / 60)
            )
        
        # No cache - trigger background load and return minimal data immediately
        background_tasks.add_task(load_project_data_background, user_id)
        
        # Return minimal immediate data
        try:
            quick_project = supabase.table('project_overview').select('*').eq('user_id', user_id).limit(1).execute()
            
            return ProjectOverviewResponse(
                status="loading",
                data={
                    "project": quick_project.data[0] if quick_project.data else None,
                    "loading": True
                },
                message="Full project data is loading in the background..."
            )
        except Exception as e:
            logger.error(f"Error getting quick project data: {e}")
            return ProjectOverviewResponse(
                status="loading",
                data={
                    "project": None,
                    "loading": True
                },
                message="Project data is loading..."
            )
            
    except Exception as e:
        logger.error(f"Error in project overview endpoint: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch project overview")

@app.get("/project-data/{user_id}")
async def get_unified_project_data(user_id: str, background_tasks: BackgroundTasks):
    """Get unified project data - returns cached overview + status data immediately or triggers background load"""
    try:
        logger.info(f"Unified project data requested for user {user_id}")
        
        profile_result = supabase.table('creator_profiles')\
            .select('id')\
            .eq('id', user_id)\
            .limit(1)\
            .execute()
            
        if not profile_result.data:
            return {
                "error": "user_not_found",
                "message": "User profile not found. Please sign in first.",
                "needs_auth": True
            }
        
        # Check cache first
        cached_data = get_cached_project_data(user_id)
        if cached_data:
            cache_age_minutes = int((datetime.now() - cache_timestamps[user_id]).total_seconds() / 60)
            return {
                "status": "cached",
                "overview_data": cached_data.get('overview_data', {}),
                "project_status": cached_data.get('project_status', {}),
                "cache_age_minutes": cache_age_minutes
            }
        
        # No cache - trigger background load and return minimal data immediately
        background_tasks.add_task(load_project_data_background, user_id)
        
        # Return minimal immediate data for better UX (same queries as individual endpoints)
        try:
            # Use same query as project-overview endpoint
            quick_project = supabase.table('project_overview').select(('*, user:creator_profiles!user_id(first_name, last_name)')).eq('user_id', user_id).limit(1).execute()
            
            return {
                "status": "loading",
                "overview_data": {
                    "project": quick_project.data[0] if quick_project.data else None,
                    "recent_updates": [],
                    "recent_activity": []
                },
                "project_status": {
                    "ai_understanding": {
                        "knows_your_project": bool(quick_project.data),
                        "tracking_progress": False,
                        "has_next_steps": False,
                        "project_name": quick_project.data[0]['project_name'] if quick_project.data else None,
                        "current_phase": quick_project.data[0]['current_phase'] if quick_project.data else None,
                        "last_activity": None
                    },
                    "current_tasks": {"next_steps": [], "blockers": [], "recent_wins": []},
                    "is_active": False
                },
                "message": "Full project data is loading in the background..."
            }
        except Exception as e:
            logger.error(f"Error getting quick project data: {e}")
            return {
                "status": "loading",
                "overview_data": {"project": None, "recent_updates": [], "recent_activity": []},
                "project_status": {
                    "ai_understanding": {
                        "knows_your_project": False,
                        "tracking_progress": False,
                        "has_next_steps": False,
                        "project_name": None,
                        "current_phase": None,
                        "last_activity": None
                    },
                    "current_tasks": {"next_steps": [], "blockers": [], "recent_wins": []},
                    "is_active": False
                },
                "message": "Project data is loading..."
            }
            
    except Exception as e:
        logger.error(f"Error in unified project data endpoint: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch unified project data")

@app.get("/project-data-status/{user_id}")
async def check_project_data_status(user_id: str):
    """Check if project data is ready (for frontend polling)"""
    cached_data = get_cached_project_data(user_id)
    if cached_data:
        return {
            "ready": True,
            "data": cached_data,
            "cache_age_minutes": int((datetime.now() - cache_timestamps[user_id]).total_seconds() / 60)
        }
    else:
        return {
            "ready": False,
            "message": "Project data is still loading..."
        }

@app.post("/query", response_model=QueryResponse)
async def query_knowledge_base(request: Request, query_request: QueryRequest):
    try:
        logger.info(f"Received query request for user {query_request.user_id}")
        
        # Get or create memory handler
        memory_handler = get_memory_handler(query_request.user_id)
        logger.info(f"Created/retrieved memory handler for thread {query_request.thread_id}")
        
        # Get context
        context = await memory_handler.get_context(query_request.thread_id)
        logger.info(f"Retrieved context with {len(context['messages'])} messages")
        
        # Get response from agent
        logger.info(f"Requesting agent response for: {query_request.question}")
        response = await interact_with_agent(
            user_input=query_request.question,
            user_id=query_request.user_id,
            user_timezone=query_request.user_timezone,
            thread_id=query_request.thread_id,
            supabase_client=supabase,
            context=context
        )
        logger.info("Received response from agent")
        
        # Store the interaction
        logger.info("Storing interaction in memory")
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
        logger.info("Interaction stored successfully")
        
        return QueryResponse(
            answer=response,
            sources=[]
        )
    except Exception as e:
        logger.error(f"Error in query_knowledge_base: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/query_stream")
async def query_knowledge_base_stream(request: Request, query_request: QueryRequest):
    try:
        logger.info(f"Received streaming query request for user {query_request.user_id}")
        
        # Get or create memory handler
        memory_handler = get_memory_handler(query_request.user_id)
        logger.info(f"Created/retrieved memory handler for thread {query_request.thread_id}")
        
        # Get context
        context = await memory_handler.get_context(query_request.thread_id)
        logger.info(f"Retrieved context with {len(context['messages'])} messages")
        
        # Note: User message will be stored AFTER streaming completes to avoid duplication
        
        # Set up streaming response
        async def generate_stream():
            full_response = ""
            
            try:
                # Get streaming generator - NO await needed, returns AsyncGenerator directly
                stream_gen = interact_with_agent_stream(
                    user_input=query_request.question,
                    user_id=query_request.user_id,
                    user_timezone=query_request.user_timezone,
                    thread_id=query_request.thread_id,
                    supabase_client=supabase,
                    context=context
                )
                
                # Stream each chunk - interact_with_agent_stream yields simple strings
                async for chunk in stream_gen:
                    if isinstance(chunk, str) and chunk.strip():
                        full_response += chunk
                        yield f"data: {json.dumps({'chunk': chunk})}\n\n"
                
                # Store both user message and complete response after streaming is done
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
                
                # End the stream
                yield f"data: {json.dumps({'done': True})}\n\n"
                
            except Exception as e:
                logger.error(f"Streaming error: {str(e)}", exc_info=True)
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
        
        # Return streaming response
        return StreamingResponse(
            generate_stream(),
            media_type="text/event-stream"
        )
        
    except Exception as e:
        logger.error(f"Error in query_knowledge_base_stream: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root(request: Request):
    return {"message": "Welcome to Fridays at Four API"}

@app.get("/health")
async def health():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "message": "Fridays at Four backend is running"
    }
    
# Include the Slack router
app.include_router(slack_router, prefix="/slack", tags=["slack"])
app.include_router(zoom_router, prefix="/zoom", tags=["zoom"])
app.include_router(router)

for route in app.routes:
    logger.info(f"Registered route: {route.path} [{route.methods}]")

@app.middleware("http")
async def log_slack_requests(request: Request, call_next):
    """Middleware to log Slack request details"""
    if request.url.path.startswith("/slack"):
        slack_logger.debug("=== Slack Request Debug ===")
        slack_logger.debug(f"Method: {request.method}")
        slack_logger.debug(f"Path: {request.url.path}")
        slack_logger.debug(f"Headers: {dict(request.headers)}")
        
        # Log specific Slack headers
        slack_logger.debug("Slack-Specific Headers:")
        slack_logger.debug(f"X-Slack-Signature: {request.headers.get('x-slack-signature', 'NOT FOUND')}")
        slack_logger.debug(f"X-Slack-Request-Timestamp: {request.headers.get('x-slack-request-timestamp', 'NOT FOUND')}")
        
        # Log configured signing secret (partially masked)
        secret = Config.SLACK_SIGNING_SECRET
        if secret:
            masked_secret = f"{secret[:4]}...{secret[-4:]}" if len(secret) > 8 else "***"
            slack_logger.debug(f"Configured Signing Secret (masked): {masked_secret}")
        else:
            slack_logger.error("No Slack signing secret configured!")

    response = await call_next(request)
    return response

@app.post("/chat", response_model=ChatResponse)
async def chat(request: Request, chat_request: ChatRequest):
    """Chat endpoint that maps to the existing query logic"""
    try:
        logger.info(f"Received chat request for user {chat_request.user_id}, mapping to query endpoint")
        
        # Convert ChatRequest to QueryRequest format
        query_request = QueryRequest(
            question=chat_request.message,
            user_id=chat_request.user_id,
            user_timezone=chat_request.user_timezone,
            thread_id=chat_request.thread_id
        )
        
        # Use the existing working query logic
        query_response = await query_knowledge_base(request, query_request)
        
        # Return in ChatResponse format
        return ChatResponse(response=query_response.answer)
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/project-status/{user_id}", response_model=ProjectStatusResponse)
async def get_project_status(user_id: str, limit: int = 10):
    """Get project status focused on current tasks and AI understanding of project state"""
    try:
        logger.info(f"Fetching project status for user {user_id}")
        
        # First, check if creator profile exists
        profile_result = supabase.table('creator_profiles')\
            .select('*')\
            .eq('id', user_id)\
            .limit(1)\
            .execute()
            
        if not profile_result.data:
            return {
                "error": "user_not_found",
                "message": "User profile not found. Please sign in first.",
                "needs_auth": True
            }
        
        # Get project overview
        project_overview = None
        overview_result = supabase.table('project_overview')\
            .select('*')\
            .eq('user_id', user_id)\
            .limit(1)\
            .execute()
        
        if overview_result.data:
            project_overview = ProjectOverview(**overview_result.data[0])
        
        # Get recent project updates
        updates_result = supabase.table('project_updates')\
            .select('*')\
            .eq('user_id', user_id)\
            .order('created_at', desc=True)\
            .limit(limit)\
            .execute()
        
        recent_updates = []
        if updates_result.data:
            for update_data in updates_result.data:
                # Handle potential None values in arrays
                update_data['milestones_hit'] = update_data.get('milestones_hit') or []
                update_data['blockers'] = update_data.get('blockers') or []
                update_data['next_steps'] = update_data.get('next_steps') or []
                recent_updates.append(ProjectUpdate(**update_data))
        
        # Get total count of updates
        count_result = supabase.table('project_updates')\
            .select('id', count='exact')\
            .eq('user_id', user_id)\
            .execute()
        
        total_updates = count_result.count or 0
        
        # Extract and organize current tasks (limit to 3 each to avoid overwhelm)
        next_steps = []
        blockers = []
        recent_wins = []
        
        for update in recent_updates:
            if update.next_steps:
                next_steps.extend(update.next_steps)
            if update.blockers:
                blockers.extend(update.blockers)
            if update.milestones_hit:
                recent_wins.extend(update.milestones_hit)
        
        # Limit to 3 items each to keep it manageable
        current_tasks = {
            "next_steps": next_steps[:3],
            "blockers": blockers[:3], 
            "recent_wins": recent_wins[:3]
        }
        
        # Calculate project health indicators
        has_active_project = project_overview is not None
        has_recent_activity = bool(total_updates > 0 and recent_updates and recent_updates[0].created_at)
        has_current_tasks = len(current_tasks["next_steps"]) > 0 or len(current_tasks["blockers"]) > 0 or len(current_tasks["recent_wins"]) > 0
        
        # Build AI understanding summary
        ai_understanding = {
            "knows_your_project": has_active_project,
            "tracking_progress": has_recent_activity,
            "has_next_steps": has_current_tasks,
            "project_name": project_overview.project_name if project_overview else None,
            "current_phase": project_overview.current_phase if project_overview else None,
            "last_activity": recent_updates[0].created_at if recent_updates else None
        }
        
        # Build response focused on user-facing task information
        response = {
            "ai_understanding": ai_understanding,
            "current_tasks": current_tasks,
            "project_summary": {
                "name": project_overview.project_name if project_overview else None,
                "type": project_overview.project_type if project_overview else None,
                "phase": project_overview.current_phase if project_overview else None,
                "total_updates": total_updates,
                "last_update": recent_updates[0].created_at if recent_updates else None
            },
            "goals_progress": {
                "primary_goals": project_overview.goals if project_overview else [],
                "main_challenges": project_overview.challenges if project_overview else []
            },
            # Include full data for compatibility but focus UI on the above
            "project_overview": project_overview,
            "recent_updates": recent_updates[:5],  # Limit to 5 most recent for UI
            "is_active": has_active_project and has_recent_activity
        }
        
        return response
        
    except Exception as e:
        logger.error(f"Error fetching project status: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/agents/project-progress/{user_id}")
async def get_project_progress_alias(user_id: str, limit: int = 10):
    """Alias for project status endpoint - for frontend compatibility"""
    return await get_project_status(user_id, limit)

@app.post("/refresh-project-cache/{user_id}")
async def refresh_project_cache(user_id: str, background_tasks: BackgroundTasks):
    """Manually refresh project cache for a user"""
    try:
        # Clear existing cache
        if user_id in project_cache:
            del project_cache[user_id]
        if user_id in cache_timestamps:
            del cache_timestamps[user_id]
        
        # Trigger background refresh
        background_tasks.add_task(load_project_data_background, user_id)
        
        return {
            "message": f"Project cache refresh initiated for user {user_id}",
            "status": "refreshing"
        }
    except Exception as e:
        logger.error(f"Error refreshing project cache: {e}")
        raise HTTPException(status_code=500, detail="Failed to refresh project cache")

if __name__ == "__main__":
     import uvicorn
     uvicorn.run(app, host="0.0.0.0", port=8000)