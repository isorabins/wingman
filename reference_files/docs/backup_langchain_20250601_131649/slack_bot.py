from src.config import Config
import logging
from src.react_agent import interact_with_agent
from slack_bolt.error import BoltError
import traceback
from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.fastapi.async_handler import AsyncSlackRequestHandler
from collections import defaultdict
from supabase import create_client
from fastapi import APIRouter, HTTPException, Request
import requests
from src.simple_memory import SimpleMemory
import os
import redis.asyncio as aioredis
from slack_sdk.oauth.state_store.async_state_store import AsyncOAuthStateStore
from slack_sdk.oauth.state_store.async_state_store import AsyncOAuthStateStore
from urllib.parse import urlparse
from datetime import datetime
from slack_bolt.oauth.async_oauth_settings import AsyncOAuthSettings
from slack_sdk.oauth.installation_store.async_installation_store import AsyncInstallationStore
from slack_sdk.oauth.installation_store import Installation
import secrets  
from slack_sdk.errors import SlackApiError
import json

logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
redis_logger = logging.getLogger('aioredis')
redis_logger.setLevel(logging.WARNING)

slack_bot_logger = logging.getLogger('slack_bot')
slack_bot_logger.setLevel(logging.DEBUG)

supabase = create_client(Config.SUPABASE_URL, Config.SUPABASE_SERVICE_KEY)

class RedisManager:
    def __init__(self):
        self.client = None
        self._connect()

    def _connect(self):
        redis_url = os.getenv('REDIS_URL')
        url = urlparse(redis_url)
        try:
            self.client = aioredis.from_url(
                f"rediss://{url.hostname}:{url.port}",
                password=url.password,
                ssl_cert_reqs=None,
                decode_responses=True
            )
            #logger.info("Redis connection established")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {str(e)}")
            raise

    async def is_event_processed(self, event_id: str) -> bool:
        try:
            event_key = f"processed_event:{event_id}"
            return bool(await self.client.get(event_key))
        except aioredis.RedisError as e:
            logger.error(f"Redis error checking event {event_id}: {str(e)}")
            return False

    async def mark_event_processed(self, event_id: str) -> None:
        try:
            event_key = f"processed_event:{event_id}"
            result = await self.client.setex(event_key, 86400, "1")
            logger.info(f"Redis mark event {event_id}: {'Success' if result else 'Failed'}")
        except aioredis.RedisError as e:
            logger.error(f"Redis error marking event {event_id}: {str(e)}")

redis_manager = RedisManager()

class RedisOAuthStateStore(AsyncOAuthStateStore):
    def __init__(self):
        self.redis_url = os.getenv('REDIS_URL')
        url = urlparse(self.redis_url)
        self.redis = aioredis.Redis(
            host=url.hostname,
            port=url.port,
            password=url.password,
            ssl=True,
            ssl_cert_reqs=None
        )

    async def async_issue(self, *args, **kwargs) -> str:
        state = secrets.token_urlsafe(32)  # Generate secure random state
        await self.redis.setex(f"slack_oauth_state:{state}", 600, "1")  # 10 minute expiry
        return state

    async def async_consume(self, state: str) -> bool:
        state_key = f"slack_oauth_state:{state}"
        exists = await self.redis.exists(state_key)
        if exists:
            await self.redis.delete(state_key)
            return True
        return False
         
class SupabaseInstallationStore(AsyncInstallationStore):  
    def __init__(self, client):
        self.client = client
        
    async def save(self, installation: Installation):  
        try:
            current_time = datetime.now().isoformat()
            
            result = self.client.table('slack_installations').upsert({
                'slack_workspace_id': installation.team_id,
                'slack_workspace_name': installation.team_name,
                'bot_user_id': installation.bot_user_id,
                'bot_token': installation.bot_token,
                'installing_slack_user_id': installation.user_id,
                'installed_at': current_time,
                'updated_at': current_time
            }).execute()
            
            logger.info(f"Saved installation for workspace: {installation.team_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error saving installation: {str(e)}")
            raise

    async def verify_token(self, bot_token: str) -> bool:
        try:
            # Use Slack's built-in client for token verification
            app.client.auth_test(token=bot_token)
            return True
        except SlackApiError as e:
            logger.error(f"Token validation failed: {str(e)}")
            return False
    
    async def async_find_bot(self, *, enterprise_id: str | None, team_id: str | None, is_enterprise_install: bool):
        logger.info(f"Looking for bot installation - team_id: {team_id}")  
        try:
            result = self.client.table('slack_installations')\
                .select('*')\
                .eq('slack_workspace_id', team_id)\
                .single()\
                .execute()
                
            if not result.data:
                logger.info(f"No installation found for team_id: {team_id}")
                return None

            # Get token and verify it
            token = result.data['bot_token']
            if await self.verify_token(token):
                logger.info(f"Token verified for team_id: {team_id}")
                return Installation(
                    app_id='A07LGR59XGQ',  # Our app's ID from the Slack logs
                    enterprise_id=enterprise_id,
                    team_id=result.data['slack_workspace_id'],
                    bot_token=token,
                    bot_user_id=result.data['bot_user_id'],
                    user_id=result.data['installing_slack_user_id'],  # Key addition
                    bot_scopes=["app_mentions:read", "assistant:write", "channels:history", 
                            "chat:write", "groups:history", "im:history", "users:read", 
                            "im:read", "chat:write.public", "users:read.email"],
                    is_enterprise_install=is_enterprise_install
                )
            else:
                logger.error(f"Token validation failed for team_id: {team_id}")
                return None

        except Exception as e:
            logger.error(f"Error in async_find_bot: {str(e)}")
            return None
    async def find_installation(self, enterprise_id: str | None, team_id: str | None, is_enterprise_install: bool):
        try:
            result = self.client.table('slack_installations')\
                .select('*')\
                .eq('slack_workspace_id', team_id)\
                .single()\
                .execute()
                
            if not result.data:
                return None
                
            return Installation(
                team_id=result.data['slack_workspace_id'],
                bot_token=result.data['bot_token'],
                bot_user_id=result.data['bot_user_id'],
                # Add these additional fields we have
                team_name=result.data['slack_workspace_name'],
                installed_at=result.data['installed_at']
            )
        except Exception as e:
            logger.error(f"Error finding installation: {str(e)}")
            return None
    

router = APIRouter()

installation_store = SupabaseInstallationStore(supabase)

oauth_settings = AsyncOAuthSettings(
    client_id=Config.SLACK_CLIENT_ID,
    client_secret=Config.SLACK_CLIENT_SECRET,
    scopes=["app_mentions:read", "users:read.email", "assistant:write", "channels:history", "chat:write", "groups:history", "im:history", "users:read", "im:read", "chat:write.public"],
    installation_store=installation_store,
    state_store=RedisOAuthStateStore()
)



# Initialize the Slack app with async support
app = AsyncApp(
    signing_secret=Config.SLACK_SIGNING_SECRET,
    oauth_settings=oauth_settings,
    process_before_response=True
)

handler = AsyncSlackRequestHandler(app)


@app.event("app_mention")
async def handle_mention(body, say):
    """Handle mentions in channels"""
    logger.info("=== Handling Mention ===")
    logger.info(f"Event body: {body}")
    try:
        event_id = body.get("event_id")
        
        # Check Redis for duplicate event
        if await redis_manager.is_event_processed(event_id):
            logger.info(f"Duplicate event received: {event_id}")
            return
        
        # Mark in Redis as processed
        await redis_manager.mark_event_processed(event_id)
        logger.info(f"Processing new event: {event_id}")

        installation = await installation_store.async_find_bot(
            enterprise_id=None,
            team_id=body["team_id"],
            is_enterprise_install=False
        )
          # Add this check
        if not installation:
            logger.error(f"Invalid or missing installation for team {body['team_id']}")
            await say("I'm sorry, but I'm having trouble accessing this workspace. Please try reinstalling the app.")
            return

        user_id = body["event"]["user"]
        user_timezone_info = await app.client.users_info(
        token=installation.bot_token,
        user=user_id
    )
        user_timezone_info = user_timezone_info['user']['tz']
        logger.info(user_timezone_info)
        question = body["event"]["text"].split(">")[1].strip()
        
        logger.info(f"Processing mention from user {user_id}: {question}")
        
        client = create_client(Config.SUPABASE_URL,
                             Config.SUPABASE_SERVICE_KEY)
        user_id_results = client.rpc(
            'get_user_id_based_on_slack_id',
            {
                'input_slack_id': user_id
            }
        ).execute()
        internal_user_id = [_ for _ in user_id_results][0][1]

        if internal_user_id is None: 
            await say(f"Hi <@{user_id}>! We don't have any account associated with your Slack ID, can you double check?")
            return

        logger.info(f"Real user ID is {internal_user_id}")

        memory_handler = SimpleMemory(supabase, internal_user_id)
        thread_id = f"channel_{internal_user_id}"
        
        await memory_handler.add_message(
            thread_id=thread_id,
            message=question,
            role="user"
        )
        
        response = await interact_with_agent(
            user_input=question,
            user_id=internal_user_id,
            user_timezone=user_timezone_info,
            thread_id=thread_id,
            supabase_client=client,
            context={"thread_type": "channel"}
        )

        await memory_handler.add_message(
            thread_id=thread_id,
            message=response,
            role="assistant"
        )
        
        await say(f"Hi <@{user_id}>! {response}")
        logger.info(f"Response to message {event_id} sent to Slack")

    except Exception as e:
        logger.error(f"Error in handle_message: {str(e)}", exc_info=True)
        await say("I'm sorry, but I encountered an error while processing your message.")
        
@app.event("message")
async def handle_message(body, say):
    logger.info("=== Handling Direct Message ===")
    logger.info(f"Event body: {body}")
    try:
        # Early return for non-DM messages
        if body["event"].get("channel_type") != "im":
            logger.info("Ignoring non-DM message")
            return
            
         # Get event_id directly from body, not nested
        event_id = body.get("event_id")
        if await redis_manager.is_event_processed(event_id):
            logger.info(f"Duplicate event received: {event_id}")
            return
        await redis_manager.mark_event_processed(event_id)
        
        user_id = body["event"]["user"]
        text = body["event"]["text"]
        
        logger.info(f"Processing DM from user {user_id}: {text}")
        
        # First check for profile with slack_id
        slack_bot_logger.debug("=== New Message Handler Debug ===")
        slack_bot_logger.debug(f"Message body: {json.dumps(body, indent=2)}")
        slack_bot_logger.debug(f"Looking up user with Slack ID: {user_id}")

        profile = supabase.table('creator_profiles')\
            .select('*')\
            .eq('slack_id', user_id)\
            .single()\
            .execute()

        slack_bot_logger.debug(f"Profile lookup result: {json.dumps(profile.data, indent=2)}")

        installation = await installation_store.async_find_bot(
            enterprise_id=None,
            team_id=body["team_id"],
            is_enterprise_install=False
        )
          # Add this check
        if not installation:
            logger.error(f"Invalid or missing installation for team {body['team_id']}")
            await say("I'm sorry, but I'm having trouble accessing this workspace. Please try reinstalling the app.")
            return
    
        if profile.data:
            # Initialize memory system with thread_id for this DM
            thread_id = f"dm_{user_id}"
            logger.info(f"Initializing memory with thread_id: {thread_id}")
            
             # Get user timezone
            user_timezone_info = await app.client.users_info(
                token=installation.bot_token,
                user=user_id
            )
            user_timezone = user_timezone_info['user']['tz']
            logger.info(f"User timezone: {user_timezone}")

            memory_handler = SimpleMemory(supabase, profile.data['id'])
            
            # Store user's message
            logger.info("Storing user message in memory")
            await memory_handler.add_message(
                thread_id=thread_id,
                message=text,
                role="user"
            )
            
            # Get context before agent interaction
            logger.info("Getting context")
            context = await memory_handler.get_context(thread_id)
            context["thread_type"] = "dm"
            
            logger.info(f"Retrieved context: {context}")
            
            # Get AI response
            response = await interact_with_agent(
            user_input=text,
            user_id=profile.data['id'],
            user_timezone=user_timezone,
            thread_id=thread_id,
            supabase_client=supabase,
            context=context
        )
                
            # Store AI's response in memory
            logger.info("Storing AI response in memory")
            await memory_handler.add_message(
                thread_id=thread_id,
                message=response,
                role="assistant"
            )
        else:
            response = "Hi! Looks like you haven't signed up for Fridays at Four yet. Please visit fridaysatfour.com to join our community!"

        await say(response)

    except Exception as e:
        logger.error(f"Error in handle_message: {str(e)}", exc_info=True)
            
@router.get("/callback")
async def slack_callback(code: str):
    """
    Handle OAuth callback from Slack with comprehensive logging.
    Stores installation details in the slack_installations table.
    """
    try:
        # Initial debug logging
        logger.info("=== Starting Slack OAuth Callback Process ===")
        logger.info(f"Received authorization code: {code[:10]}...")  # Truncated for security
        
        # Log environment configuration
        logger.info("=== Configuration Check ===")
        logger.info(f"Client ID from config: {Config.SLACK_CLIENT_ID}")
        logger.info(f"Client Secret configured: {'Yes' if Config.SLACK_CLIENT_SECRET else 'No'}")
        logger.info(f"Callback URL: {Config.SLACK_CALLBACK_URL}")
        
        # Prepare request data
        request_data = {
            "client_id": Config.SLACK_CLIENT_ID,
            "client_secret": Config.SLACK_CLIENT_SECRET,
            "code": code,
            "redirect_uri": Config.SLACK_CALLBACK_URL
        }
        
        # Log request data (excluding secret)
        safe_request_data = {**request_data, "client_secret": "[REDACTED]"}
        logger.info("=== OAuth Request Data ===")
        logger.info(f"Request data being sent: {safe_request_data}")
        
        # Make the OAuth request
        logger.info("=== Making OAuth Request ===")
        response = requests.post(
            "https://slack.com/api/oauth.v2.access",
            data=request_data
        )
        
        # Log response details
        logger.info("=== OAuth Response Details ===")
        logger.info(f"Response status code: {response.status_code}")
        logger.info(f"Response headers: {dict(response.headers)}")
        
        # Parse response
        data = response.json()
        logger.info(f"Response body: {data}")
        
        # Check for OAuth success
        if not data.get("ok"):
            error_msg = data.get('error', 'Unknown error')
            logger.error("=== OAuth Error ===")
            logger.error(f"Error type: {error_msg}")
            logger.error(f"Full error response: {data}")
            raise HTTPException(status_code=400, detail=f"OAuth failed: {error_msg}")
        
        # Extract and log success details
        logger.info("=== OAuth Success ===")
        # Validate required fields
        required_fields = {
            'access_token': data.get('access_token'),
            'team_id': data.get('team', {}).get('id'),
            'bot_user_id': data.get('bot_user_id')
        }

        # Check if any required fields are missing
        missing_fields = [k for k, v in required_fields.items() if not v]
        if missing_fields:
            error_msg = f"Missing required fields: {', '.join(missing_fields)}"
            logger.error(error_msg)
            raise HTTPException(status_code=400, detail=error_msg)

        # Extract fields with proper defaults
        bot_token = required_fields['access_token']
        slack_workspace_id = required_fields['team_id']
        bot_user_id = required_fields['bot_user_id']
        slack_workspace_name = data.get('team', {}).get('name', 'Unknown Workspace')
        installing_slack_user_id = data.get('authed_user', {}).get('id')
        installing_user_email = data.get('authed_user', {}).get('email')

        # Log extracted fields
        logger.info("=== Extracted Fields ===")
        logger.info(f"Workspace ID: {slack_workspace_id}")
        logger.info(f"Workspace Name: {slack_workspace_name}")
        logger.info(f"Bot User ID: {bot_user_id}")
        logger.info(f"Installing User ID: {installing_slack_user_id}")
        logger.info(f"Installing User Email: {installing_user_email}")

        # Before the upsert, get current time once
        current_time = datetime.now().isoformat()

        # Perform the upsert with all available fields
        install_result = supabase.table('slack_installations').upsert({
            'slack_workspace_id': slack_workspace_id,  # Use our validated variable
            'slack_workspace_name': slack_workspace_name,  # Use our validated variable
            'bot_user_id': bot_user_id,  # Use our validated variable
            'bot_token': bot_token,  # Use our validated variable
            'installing_slack_user_id': installing_slack_user_id,  # Use our validated variable
            'installing_user_email': installing_user_email,  # Add this field
            'installed_at': current_time,
            'updated_at': current_time
        }).execute()
                        
        logger.info(f"Installation stored: {slack_workspace_id} for workspace {slack_workspace_name}")

        return {
            "status": "success",
            "message": f"App successfully installed for workspace {slack_workspace_name}!"
        }

    except Exception as e:
        logger.error("=== Unhandled OAuth Error ===")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Error message: {str(e)}")
        logger.error("Full traceback:", exc_info=True)
        raise HTTPException(status_code=500, detail="An error occurred during OAuth.")
    
@router.post("/events")
async def endpoint(request: Request):
    """Handle incoming Slack events"""
    try:
        slack_bot_logger.debug("=== New Slack Event ===")
        slack_bot_logger.debug(f"Headers: {dict(request.headers)}")
        slack_bot_logger.debug(f"Signing Secret configured: {'Yes' if Config.SLACK_SIGNING_SECRET else 'No'}")
        
        # Log the timestamp and signature (key verification components)
        slack_bot_logger.debug(f"X-Slack-Request-Timestamp: {request.headers.get('x-slack-request-timestamp')}")
        # Only log first few chars of signature for security
        signature = request.headers.get('x-slack-signature', '')
        masked_signature = f"{signature[:10]}..." if signature else "None"
        slack_bot_logger.debug(f"X-Slack-Signature (masked): {masked_signature}")
        
        return await handler.handle(request)
    except Exception as e:
        slack_bot_logger.error(f"Error in Slack event handling: {str(e)}", exc_info=True)
        return {"status": "error", "message": str(e)}
        
  