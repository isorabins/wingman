"""
zoom_transcript_retrieval.py
---------------------------
Handles all Zoom API interactions for retrieving meeting content.

Primary responsibilities:
1. Receive and validate Zoom webhooks
2. Fetch transcripts from Zoom API
3. Fetch video recordings from Zoom API
4. Pass retrieved content to transcript_search.py for processing

Does NOT handle:
- Content processing
- Storage
- Summarization

Flow:
1. Webhook received for meeting.ended or recording.completed
2. Validate webhook
3. Fetch relevant content (transcript/video)
4. Pass to transcript_search.py for processing
"""

import logging
from fastapi import APIRouter, HTTPException, BackgroundTasks, Request
from httpx import AsyncClient
from src.config import Config
from src.zoom_oauth import get_access_token
from datetime import datetime, timezone, timedelta
from tenacity import retry, stop_after_attempt, wait_exponential
from typing import Dict, Any, Optional, Union
import hashlib
import hmac
from src.transcript_search import get_transcript_manager
import asyncio
import jwt

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/webhook")
async def zoom_webhook_handler(request: Request, background_tasks: BackgroundTasks):
    """Handle all Zoom webhooks including verification challenge"""
    try:
        body = await request.json()
        event_type = body.get("event")
        logger.info(f"Webhook received with event: {event_type}")
        
        # Handle URL verification challenge
        if event_type == "endpoint.url_validation":
            plainToken = body.get("payload", {}).get("plainToken")
            if not plainToken:
                raise HTTPException(status_code=400, detail="Missing plainToken")
                
            hash_obj = hmac.new(
                Config.ZOOM_SECRET_TOKEN.encode('utf-8'),
                plainToken.encode('utf-8'),
                hashlib.sha256
            )
            return {
                "plainToken": plainToken,
                "encryptedToken": hash_obj.hexdigest()
            }
        
        # Only process when recordings (including transcript) are ready
        if event_type in ["recording.completed", "recording.transcript_completed"]:
            meeting_id = body["payload"]["object"]["id"]
            access_token = await get_access_token()
            logger.info(f"{event_type} for meeting {meeting_id}, initiating content retrieval")
            background_tasks.add_task(process_meeting_content, meeting_id, access_token)
        return {"status": "success", "event": event_type}

    except Exception as e:
        logger.error(f"Webhook handler error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
async def get_recent_meetings(access_token: str):
    """Fetch recent meetings with recordings from Zoom API"""
    try:
        url = f"{Config.ZOOM_API_URL}/users/me/recordings"
        headers = {'Authorization': f'Bearer {access_token}'}
        
        async with AsyncClient() as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            meetings = data.get('meetings', [])
            logger.info(f"Found {len(meetings)} recent meetings")
            return meetings
            
    except Exception as e:
        logger.error(f"Error fetching recent meetings: {str(e)}")
        return []
    
async def process_meeting_content(meeting_id: str, access_token: str):
    """Fetch all meeting content when recordings and transcript are ready."""
    try:
        # Add delay to ensure Zoom has finished processing
        await asyncio.sleep(30)  # 30 second delay
        
        # Verify recording is ready
        max_attempts = 3
        for attempt in range(max_attempts):
            recordings = await fetch_zoom_recordings(meeting_id, access_token)
            if recordings and recordings.get("recording_files"):
                break
            if attempt < max_attempts - 1:
                await asyncio.sleep(30)  # Wait between attempts
                continue
            logger.error(f"No recordings found for meeting {meeting_id} after {max_attempts} attempts")
            return

        logger.info(f"Starting content retrieval for meeting {meeting_id}")
        content = {
            "transcript": None,
            "recordings": None,
            "metadata": {
                "meeting_id": meeting_id,
                "retrieval_time": datetime.now(timezone.utc).isoformat(),
                "source": "zoom"
            }
        }

        # Add token refresh check
        if is_token_expired(access_token):
            access_token = await get_access_token()

        # First get recordings info
        recordings = await fetch_zoom_recordings(meeting_id, access_token)
        if not recordings or not recordings.get("recording_files"):
            logger.error(f"No recordings found for meeting {meeting_id}")
            return

        # Now we can get the user_id
        logger.info(f"Content metadata: {content.get('metadata', {})}")
        logger.info(f"Extracted User ID: {content.get('metadata', {}).get('user_id', '00000000-0000-0000-0000-000000000000')}")
        user_id = recordings.get("host_id") or "00000000-0000-0000-0000-000000000000"
        content["metadata"]["user_id"] = user_id

        # Process recordings and find transcript
        content["recordings"] = recordings
        content["metadata"].update({
            "recording_count": len(recordings["recording_files"]),
            "host_id": recordings.get("host_id"),
            "topic": recordings.get("topic", ""),
            "start_time": recordings.get("start_time", ""),
            "duration": recordings.get("duration", 0)
        })

        # Look for transcript in recording files
        transcript_file = next(
            (f for f in recordings["recording_files"] if f["file_type"] == "TRANSCRIPT"),
            None
        )
        
        if transcript_file:
            logger.info(f"Found transcript for meeting {meeting_id}")
            # Fetch the actual transcript content
            headers = {'Authorization': f'Bearer {access_token}'}
            async with AsyncClient(follow_redirects=True) as client:
                response = await client.get(transcript_file["download_url"], headers=headers)
                response.raise_for_status()
                content["transcript"] = response.text
        else:
            logger.warning(f"No transcript found in recordings for meeting {meeting_id}")


        manager = get_transcript_manager()
        #added manager.supabase 1/13 to try to troubleshoot client passing failure
        await manager.process_raw_meeting_content(content, manager.supabase)
        
        logger.info(f"Successfully retrieved and passed content for meeting {meeting_id}")

    except Exception as e:
        logger.error(f"Error processing meeting content: {str(e)}", exc_info=True)
        raise

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
async def fetch_zoom_recordings(meeting_id: str, access_token: str) -> Dict[str, Any]:
    """Fetch recording information for a specific meeting"""
    url = f"{Config.ZOOM_API_URL}/meetings/{meeting_id}/recordings"
    headers = {'Authorization': f'Bearer {access_token}'}
    
    async with AsyncClient() as client:
        response = await client.get(url, headers=headers)
        response.raise_for_status()
        logger.info(f"Successfully fetched recordings for meeting ID: {meeting_id}")
        return response.json()

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
async def fetch_zoom_transcript(meeting_id: Union[str, int], access_token: str) -> Optional[str]:
    """Fetch and download transcript for a specific meeting"""
    meeting_id = str(meeting_id).replace(" ", "")
    
    try:
        recordings = await fetch_zoom_recordings(meeting_id, access_token)
        if not recordings:
            logger.warning(f"No recordings found for meeting ID: {meeting_id}")
            return None
            
        for file in recordings.get("recording_files", []):
            if file["file_type"] == "TRANSCRIPT":
                transcript_url = file["download_url"]
                headers = {'Authorization': f'Bearer {access_token}'}
                
                async with AsyncClient(follow_redirects=True) as client:
                    response = await client.get(transcript_url, headers=headers)
                    response.raise_for_status()
                    
                    logger.info(f"Successfully fetched transcript for meeting ID: {meeting_id}")
                    return response.text
                    
        logger.warning(f"No transcript found for meeting ID: {meeting_id}")
        return None
        
    except Exception as e:
        logger.error(f"Error fetching transcript for meeting ID {meeting_id}: {str(e)}", exc_info=True)
        raise


@router.get("/transcripts/{meeting_id}")
async def get_meeting_transcript(meeting_id: str, user_id: str):
    """Fetch transcript from Zoom - processing and storage handled by transcript_search"""
    try:
        access_token = await get_access_token()
        # Just fetch the content
        transcript = await fetch_zoom_transcript(meeting_id, access_token)
        recordings = await fetch_zoom_recordings(meeting_id, access_token)

        if not transcript and not recordings:
            logger.warning(f"No content found for meeting ID: {meeting_id}")
            return {
                "message": "No content available",
                "meeting_id": meeting_id
            }

        # Pass to transcript_search for processing
        from transcript_search import process_and_retrieve_transcript
        result = await process_and_retrieve_transcript(
            meeting_id=meeting_id,
            user_id=user_id,
            transcript=transcript,
            recordings=recordings
        )
        
        return result

    except Exception as e:
        logger.error(f"Error fetching meeting content: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

def is_token_expired(access_token: str) -> bool:
    """Check if the token is nearing expiration"""
    try:
        # Decode JWT token to check expiration
        decoded = jwt.decode(access_token, options={"verify_signature": False})
        exp_time = datetime.fromtimestamp(decoded['exp'], tz=timezone.utc)
        # Return True if token expires in less than 5 minutes
        return exp_time - datetime.now(timezone.utc) < timedelta(minutes=5)
    except Exception as e:
        logger.error(f"Error checking token expiration: {e}")
        return True  # Assume expired if we can't check