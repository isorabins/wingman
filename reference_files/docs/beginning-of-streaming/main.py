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
                    logger.info(f"DEBUG: Received chunk from agent: {chunk}")
                    # Get content from the message chunk
                    content = None
                    # Extract content from message format used by react_agent
                    if isinstance(chunk, dict) and "messages" in chunk and chunk["messages"]:
                        last_message = chunk["messages"][-1]
                        if hasattr(last_message, "content"):
                            content = last_message.content
                        elif isinstance(last_message, dict) and "content" in last_message:
                            content = last_message["content"]
                    # If content found, send it
                    if content:
                        # Add to full response
                        full_response += content
                        # Stream it to client as JSON
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

if __name__ == "__main__":
     import uvicorn
     uvicorn.run(app, host="0.0.0.0", port=8000)