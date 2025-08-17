import httpx
import asyncio
from src.zoom_oauth import get_access_token
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def create_zoom_meeting(start_time: str):
    url = "https://api.zoom.us/v2/users/me/meetings"
    token = await get_access_token()

    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    meeting_details = {
        "topic": "Scheduled Meeting",
        "type": 2,
        "start_time": start_time,
        "duration": 30,
        "timezone": "UTC",
        "settings": {
            "host_video": True,
            "participant_video": True,
            "join_before_host": True,
            "mute_upon_entry": True,
            "waiting_room": True,
            "approval_type": 0  # No registration required
        }
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=meeting_details)
        if response.status_code == 201:
            meeting_info = response.json()
            logger.info("Meeting created successfully!")
            return meeting_info
        else:
            logger.error(f"Error creating meeting: {response.status_code} {response.text}")
            return None

async def delete_zoom_meeting(meeting_id: int):
    url = f"https://api.zoom.us/v2/meetings/{meeting_id}"
    token = await get_access_token()

    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    async with httpx.AsyncClient() as client:
        response = await client.delete(url, headers=headers)
        if response.status_code == 204:
            logger.info("Meeting deleted successfully!")
            return True
        else:
            logger.error(f"Error deleting meeting: {response.status_code} {response.text}")
            return False

# Example usage (should be run within an async environment)
# asyncio.run(create_zoom_meeting("2023-10-04T12:00:00Z"))
# asyncio.run(delete_zoom_meeting(123456789))
