from typing import Dict, List, Optional, Type
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field
import logging
from datetime import datetime, timezone
import asyncio
from supabase import create_client
from src.config import Config
from src.zoom_oauth import get_access_token
import requests
import pytz
from langchain_openai import ChatOpenAI  # For OpenAI model integration
from langchain_core.prompts import PromptTemplate  # For prompt engineering
from src.config import Config

# Define LangChain query chain
llm = ChatOpenAI(model="gpt-4o-mini")

# Error messages
ERROR_MESSAGES = {
    "no_data": "Sorry I couldn't find what you're looking for, can you try asking a different way?",
    "invalid_request": "Sorry, I couldn't process that request. Please check your input and try again.",
    "not_found": "Sorry I couldn't find what you're looking for, can you try asking a different way?",
    "system_error": "Sorry but I'm having trouble, can you try again later?"
}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Input models
class ContentSearchInput(BaseModel):
    query: str = Field(..., description="a noun {persons name, technology, or feature to search in the database}")
    user_id: str = Field(..., description="User's ID")
    content_type: Optional[str] = Field(None, description="Type of content to search")

class ProjectStatusInput(BaseModel):
    user_id: str = Field(..., description="User's ID")
    project_id: str = Field(..., description="Project ID")
    progress_summary: str = Field(..., description="Progress summary")
    milestones_hit: Optional[List[str]] = Field(default=[])
    blockers: Optional[List[str]] = Field(default=[])
    next_steps: Optional[List[str]] = Field(default=[])
    mood_rating: Optional[int] = Field(None)

class CreateMeetingInput(BaseModel):
    start_time: str = Field(..., description='Start time in ISO 8601 format, timezone-naive.')
    user_timezone: str = Field(default="UTC", description="User's time zone.")

# Tools
class SearchDatabaseTool(BaseTool):
    name: str = "search_database"
    description: str = """Search across all content types with relevance ranking. 
    Used for finding information in past meetings, memory, and project updates."""
    args_schema: Type[BaseModel] = ContentSearchInput

    def _run(self, query: str, user_id: str, content_type: Optional[str] = None) -> Dict:
        """Synchronous wrapper for async search"""
        return asyncio.run(self._arun(query, user_id, content_type))

    async def _arun(self, query: str, user_id: str, content_type: Optional[str] = None) -> Dict:
        try:
            logger.info(f"Searching content for user {user_id} with query: {query}")
            
            client = create_client(Config.SUPABASE_URL, Config.SUPABASE_SERVICE_KEY)
      
            internal_user_id = user_id
            
            logger.info(f"Converted user ID {user_id} to internal ID {internal_user_id}")
            logger.info(f"Searching with parameters - query: {query}, user_id: {user_id}")

            response = client.rpc(
                'search_all_content',
                {
                    'p_query': query,
                    'p_user_id': internal_user_id  # Now using the converted UUID
                }
            ).execute()
            # After the response = client.rpc(...) line
            logger.info(f"Raw RPC response data: {response.data}")
            logger.info(f"First result (if any): {response.data[0] if response.data else 'No results'}")
          
            logger.info(f"Total results returned: {len(response.data)}")
            logger.info("Results by source_type:")
            source_types = {}
            for result in response.data:
                source_type = result.get('source_type')
                source_types[source_type] = source_types.get(source_type, 0) + 1
            logger.info(f"Source type breakdown: {source_types}")

            if not response.data:
                return {
                    "status": "not_found",
                    "message": ERROR_MESSAGES["no_data"],
                    "results": []
                }

            results = response.data

            # Filter by content_type if specified
            if content_type:
                results = [r for r in results if r['source_type'] == content_type]

            return {
                "status": "success",
                "results": results,
                "total_count": len(results),
                "metadata": {
                    "query": query,
                    "content_type": content_type,
                    "user_id": user_id,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            }

        except Exception as e:
            logger.error(f"Search error: {str(e)}", exc_info=True)
            return {"status": "error", "message": ERROR_MESSAGES["system_error"]}
        
class ProjectStatusUpdateTool(BaseTool):
    name: str = "project_status_update"
    description: str = "Updates project status with daily summary and metadata"
    args_schema: Type[BaseModel] = ProjectStatusInput

    def _run(self, project_id: str, user_id: str, progress_summary: str,
             milestones_hit: List[str] = [], blockers: List[str] = [],
             next_steps: List[str] = [], mood_rating: Optional[int] = None) -> Dict:
        """Synchronous method that calls async"""
        return asyncio.run(self._arun(
            project_id=project_id,
            user_id=user_id,
            progress_summary=progress_summary,
            milestones_hit=milestones_hit,
            blockers=blockers,
            next_steps=next_steps,
            mood_rating=mood_rating
        ))

    async def _arun(self, project_id: str, user_id: str, progress_summary: str,
                   milestones_hit: List[str] = [], blockers: List[str] = [],
                   next_steps: List[str] = [], mood_rating: Optional[int] = None) -> Dict:
        try:
            logger.info(f"Updating project status for user {user_id}")
            
            # Create client inside async function
            client = create_client(Config.SUPABASE_URL, Config.SUPABASE_SERVICE_KEY)
            
            # Add diagnostic queries for each table
            memory_count = client.table('memory').select('id').eq('user_id', user_id).execute()
            longterm_count = client.table('longterm_memory').select('id').eq('user_id', user_id).execute()
            project_count = client.table('project_overview').select('id').eq('user_id', user_id).execute()
            updates_count = client.table('project_updates').select('id').eq('user_id', user_id).execute()
            
            logger.info(f"""
            Direct table counts:
            Memory: {len(memory_count.data)}
            Longterm: {len(longterm_count.data)}
            Projects: {len(project_count.data)}
            Updates: {len(updates_count.data)}
            """)
            
            # Check if update exists for today
            today = datetime.now().date()
            existing = client.table('project_updates').select('id')\
                .eq('project_id', project_id)\
                .eq('update_date', str(today))\
                .execute()

            if existing.data:
                # Update existing record
                response = client.table('project_updates')\
                    .update({
                        'progress_summary': progress_summary,
                        'milestones_hit': milestones_hit,
                        'blockers': blockers,
                        'next_steps': next_steps,
                        'mood_rating': mood_rating
                    })\
                    .eq('id', existing.data[0]['id'])\
                    .execute()
            else:
                # Create new record
                response = client.table('project_updates')\
                    .insert({
                        'project_id': project_id,
                        'user_id': user_id,
                        'progress_summary': progress_summary,
                        'milestones_hit': milestones_hit,
                        'blockers': blockers,
                        'next_steps': next_steps,
                        'mood_rating': mood_rating
                    })\
                    .execute()

            return {
                "status": "success",
                "message": "Status updated successfully",
                "data": response.data
            }

        except Exception as e:
            logger.error(f"Status update error: {e}")
            return {"status": "error", "message": ERROR_MESSAGES["system_error"]}

# class UserProfileTool(BaseTool):
#     name: str = "user_profile"
#     description: str = "Get user profile information"
    
#     def _run(self, user_id: str) -> Dict:
#         """Synchronous method that calls async"""
#         return asyncio.run(self._arun(user_id))

#     async def _arun(self, user_id: str) -> Dict:
#         try:
#             logger.info(f"Querying user profile for {user_id}")
            
#             # Create client inside async function
#             client = create_client(Config.SUPABASE_URL, Config.SUPABASE_SERVICE_KEY)
            
#             # Execute query synchronously
#             response = client.table('creator_profiles')\
#                 .select('*')\
#                 .eq('id', user_id)\
#                 .single()\
#                 .execute()

#             if not response.data:
#                 return {"status": "not_found", "message": ERROR_MESSAGES["no_data"]}
            
#             return {
#                 "status": "success",
#                 "data": response.data
#             }

#         except Exception as e:
#             logger.error(f"Profile query error: {e}")
#             return {"status": "error", "message": ERROR_MESSAGES["system_error"]}
        

class CreateMeetingTool(BaseTool):
    name: str = "create_meeting"
    description: str = "Creates a Zoom meeting adjusted for the user's timezone."
    args_schema: Type[BaseModel] = CreateMeetingInput

    async def _create_zoom_meeting(self, start_time: str) -> Dict:
        """Asynchronous helper function to create a Zoom meeting."""
        url = "https://api.zoom.us/v2/users/me/meetings"
        token = await get_access_token()

        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }

        meeting_details = {
            "topic": "My Test Meeting",
            "type": 2,
            "start_time": start_time,
            "duration": 30,
            "timezone": "UTC",
            "agenda": "Discuss project updates",
            "settings": {
                "host_video": True,
                "participant_video": True,
                "join_before_host": True,
                "mute_upon_entry": True,
                "waiting_room": True,
                "approval_type": 0
            }
        }

        response = requests.post(url, headers=headers, json=meeting_details)

        if response.status_code == 201:
            meeting_info = response.json()
            logger.info("Meeting created successfully!")
            return {
                "status": "success",
                "meeting_id": meeting_info["id"],
                "join_url": meeting_info["join_url"],
                "start_url": meeting_info["start_url"]
            }
        else:
            logger.error(f"Error creating meeting: {response.status_code} - {response.text}")
            return {
                "status": "error",
                "message": f"Error creating meeting: {response.status_code}",
                "details": response.text
            }

            
    def _run(self, start_time: str, user_timezone: str = "UTC") -> Dict:
        """Synchronous method to create a Zoom meeting with time zone adjustment."""
        return asyncio.run(self._arun(start_time, user_timezone))

    async def _arun(self, start_time: str, user_timezone: str = "UTC") -> Dict:
        """Asynchronous method to handle the meeting creation process with time zone adjustment."""
        try:
            # Convert start_time from user timezone to UTC
            local_time = datetime.fromisoformat(start_time)
            timezone = pytz.timezone(user_timezone)
            local_time = timezone.localize(local_time)
            utc_time = local_time.astimezone(pytz.UTC)

            logger.info("Creating Zoom meeting in UTC time: " +utc_time.isoformat())
            return await self._create_zoom_meeting(utc_time.isoformat())

        except Exception as e:
            logger.error(f"Meeting creation error: {e}")
            return {
                "status": "error",
                "message": "System error during meeting creation"
            }

# Tool Groups
def get_all_tools() -> List[BaseTool]:
    """Get all available tools"""
    return [
        SearchDatabaseTool(),
        ProjectStatusUpdateTool(),
        #UserProfileTool(),
        CreateMeetingTool()
    ]
