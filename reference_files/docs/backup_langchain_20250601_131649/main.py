from fastapi import FastAPI, HTTPException, BackgroundTasks, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
import asyncio
from src.config import Config
from supabase import create_client, Client
from src.simple_memory import SimpleMemory
from src.react_agent import interact_with_agent, interact_with_agent_stream
from datetime import datetime, timezone
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
from src.project_planning import get_project_planning_prompt


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

# Set up CORS middleware
ALLOWED_ORIGINS = [
    "https://*.squarespace.com",
    "https://*.slack.com",
    "https://zoom.us",
    "https://fridays-at-four-c9c6b7a513be.herokuapp.com",
    "https://app.fridaysatfour.co",  # Frontend domain
    "http://localhost:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)


# Dictionary to store memory handlers
memory_handlers = {}

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

class ProjectOverview(BaseModel):
    id: str
    user_id: str
    project_name: str
    project_type: str
    description: str
    current_phase: str
    goals: List[dict]
    challenges: List[dict]
    success_metrics: dict
    creation_date: str
    last_updated: str

class ApplicationSubmission(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    project_type: str
    responses: Dict

    
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

@app.get("/project-overview/{user_id}")
async def get_project_overview(user_id: str):
    """Get project overview for a user - auto-creates if needed"""
    try:
        logger.info(f"Fetching project overview for user {user_id}")
        
        # First, check if creator profile exists (required for foreign key constraints)
        profile_result = supabase.table('creator_profiles')\
            .select('*')\
            .eq('id', user_id)\
            .limit(1)\
            .execute()
            
        if not profile_result.data:
            # Return helpful response for missing creator profile
            return {
                "error": "user_not_found",
                "message": "User profile not found. Please sign in first.",
                "needs_auth": True
            }
        
        # Get project overview from database
        result = supabase.table('project_overview')\
            .select('*')\
            .eq('user_id', user_id)\
            .limit(1)\
            .execute()
        
        if not result.data:
            # No project overview exists - return onboarding needed response
            logger.info(f"No project overview found for user {user_id} - triggering onboarding")
            
            return {
                "error": "no_project_overview",
                "message": "No project overview found. Let's create one!",
                "needs_onboarding": True,
                "onboarding_prompt": get_project_planning_prompt()
            }
        
        project = result.data[0]
        return ProjectOverview(**project)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching project overview: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

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
        
        # Store user message immediately
        await memory_handler.add_message(
            thread_id=query_request.thread_id,
            message=query_request.question,
            role="user"
        )
        
        # Set up streaming response
        async def generate_stream():
            full_response = ""
            
            try:
                # Get streaming generator
                stream_gen = await interact_with_agent_stream(
                    user_input=query_request.question,
                    user_id=query_request.user_id,
                    user_timezone=query_request.user_timezone,
                    thread_id=query_request.thread_id,
                    supabase_client=supabase,
                    context=context
                )
                
                # Stream each chunk
                async for chunk in stream_gen:
                    if "messages" in chunk and chunk["messages"]:
                        content = chunk["messages"][-1].content
                        if content:
                            full_response += content
                            yield f"data: {json.dumps({'chunk': content})}\n\n"
                
                # Store the complete response after streaming is done
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
async def health_check():
    """Health check endpoint to verify all critical system components."""
    try:
        # Test Supabase connection
        logger.info("Health check: Testing Supabase connection...")
        supabase.table('conversations').select('id').limit(1).execute()
        
        # Test memory system
        logger.info("Health check: Testing memory system...")
        test_memory = SimpleMemory(supabase, "00000000-0000-0000-0000-000000000000")
        
        # Test agent and memory interaction
        logger.info("Health check: Testing agent response...")
        test_context = await test_memory.get_context("health_check")
        logger.info(f"Health check context: {test_context}")
        test_response = await interact_with_agent(
            user_input="test",
            user_id="health_check",
            user_timezone="UTC",
            thread_id="health_check",
            supabase_client=supabase,
            context=test_context
        )
        
        return {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "components": {
                "supabase": "connected",
                "memory": "working",
                "agent": "responding"
            },
            "version": "1.0.0"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
    
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

if __name__ == "__main__":
     import uvicorn
     uvicorn.run(app, host="0.0.0.0", port=8000)