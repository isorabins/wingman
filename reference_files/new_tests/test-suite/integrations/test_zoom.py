# Add project root to Python path for src imports
import sys
import os
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
import jwt
import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, Mock
from src.zoom_transcript_retrieval import (
    get_recent_meetings,
    process_meeting_content,
    fetch_zoom_recordings,
    fetch_zoom_transcript,
    is_token_expired,
    router,
)
from src.zoom_oauth import get_access_token
import asyncio
from src.config import Config
from fastapi import FastAPI
from datetime import datetime, timezone, timedelta

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


# Create a test FastAPI app with the router
app = FastAPI()
app.include_router(router, prefix="/zoom")


@pytest.mark.asyncio
async def test_zoom_webhook_handler_validation():
    """Test Zoom webhook URL validation"""
    with patch("src.zoom_transcript_retrieval.Config.ZOOM_SECRET_TOKEN", "test_secret"):
        client = TestClient(app)
        payload = {
            "event": "endpoint.url_validation",
            "payload": {"plainToken": "test_token"}
        }
        response = client.post("/zoom/webhook", json=payload)
        assert response.status_code == 200
        result = response.json()
        assert "plainToken" in result
        assert "encryptedToken" in result


@pytest.mark.asyncio
async def test_zoom_webhook_handler_event_processing():
    """Test Zoom webhook handling of recording events"""
    with patch("src.zoom_transcript_retrieval.get_access_token", AsyncMock(return_value="test_token")), \
            patch("src.zoom_transcript_retrieval.process_meeting_content", AsyncMock()):
        client = TestClient(app)
        payload = {
            "event": "recording.completed",
            "payload": {"object": {"id": "test_meeting_id"}}
        }
        response = client.post("/zoom/webhook", json=payload)
        assert response.status_code == 200
        assert response.json()["status"] == "success"


@pytest.mark.asyncio
async def test_zoom_webhook_invalid_payload_handling():
    """Test handling of various invalid payload scenarios"""
    client = TestClient(app)
    
    # Test missing payload object
    payload = {"event": "recording.completed"}
    response = client.post("/zoom/webhook", json=payload)
    assert response.status_code == 500
    assert "error" in response.json()["detail"].lower()

    # Test bad json
    response = client.post("/zoom/webhook", content="invalid json")
    assert response.status_code == 500
    assert "error" in response.json()["detail"].lower()


@patch('src.zoom_transcript_retrieval.get_access_token')
@pytest.mark.asyncio
async def test_get_recent_meetings(mock_token):
    """Test fetching recent meetings from Zoom API"""
    mock_response = {"meetings": [{"id": "123", "topic": "Test Meeting"}]}

    # Mock the behavior of the AsyncClient.get method
    with patch("src.zoom_transcript_retrieval.AsyncClient.get", AsyncMock()) as mock_get:
        # Mock the response object returned by AsyncClient.get
        mock_response_object = AsyncMock()
        mock_response_object.json = Mock(return_value=mock_response)
        mock_response_object.raise_for_status = AsyncMock()

        # Set the mocked return value of get() to the mock_response_object
        mock_get.return_value = mock_response_object

        # Call the function under test
        meetings = await get_recent_meetings("test_token")

        # Assertions
        assert len(meetings) == 1
        assert meetings[0]["id"] == "123"
        assert meetings[0]["topic"] == "Test Meeting"

        # Verify the API call was made with the correct authorization header
        mock_get.assert_called_once_with(
            f"{Config.ZOOM_API_URL}/users/me/recordings",
            headers={'Authorization': 'Bearer test_token'}
        )


@patch('src.zoom_transcript_retrieval.get_access_token')
@pytest.mark.asyncio
async def test_fetch_zoom_recordings(mock_token):
    """Test fetching recordings for a specific meeting"""
    mock_response = {"recording_files": [
        {"file_type": "TRANSCRIPT", "download_url": "http://test.com"}]}
    with patch("src.zoom_transcript_retrieval.AsyncClient.get", AsyncMock()) as mock_get:
        mock_response_object = AsyncMock()
        mock_response_object.json = Mock(return_value=mock_response)
        mock_response_object.raise_for_status = AsyncMock()

        mock_get.return_value = mock_response_object

        recordings = await fetch_zoom_recordings("test_meeting_id", "test_token")
        assert "recording_files" in recordings
        assert recordings["recording_files"][0]["file_type"] == "TRANSCRIPT"


@patch('src.zoom_transcript_retrieval.fetch_zoom_recordings')
@patch('src.zoom_transcript_retrieval.AsyncClient.get')
@pytest.mark.asyncio
async def test_fetch_zoom_transcript(mock_client_get, mock_fetch_recordings):
    """Test fetching a transcript for a specific meeting"""
    mock_recordings = {
        "recording_files": [{"file_type": "TRANSCRIPT", "download_url": "http://test.com"}]
    }
    with patch("src.zoom_transcript_retrieval.fetch_zoom_recordings", AsyncMock(return_value=mock_recordings)), \
            patch("src.zoom_transcript_retrieval.AsyncClient.get", AsyncMock(return_value=AsyncMock(text="Test Transcript"))):
        transcript = await fetch_zoom_transcript("test_meeting_id", "test_token")
        assert transcript == "Test Transcript"


def test_is_token_expired():
    """Test token expiration checking"""
    valid_token = jwt.encode(
        {"exp": (datetime.now(timezone.utc) +
                 timedelta(minutes=10)).timestamp()},
        "test_secret",
        algorithm="HS256"
    )
    expired_token = jwt.encode(
        {"exp": (datetime.now(timezone.utc) - timedelta(minutes=1)).timestamp()},
        "test_secret",
        algorithm="HS256"
    )
    assert not is_token_expired(valid_token)
    assert is_token_expired(expired_token)


@patch('src.zoom_transcript_retrieval.fetch_zoom_recordings')
@patch('src.zoom_transcript_retrieval.fetch_zoom_transcript')
@patch('src.zoom_transcript_retrieval.get_transcript_manager')
@pytest.mark.asyncio
async def test_process_meeting_content(mock_get_manager, mock_fetch_transcript, mock_fetch_recordings):
    """Test processing meeting content"""
    # Setup mocks
    mock_fetch_recordings.return_value = {
        "recording_files": [
            {
                "file_type": "TRANSCRIPT", 
                "download_url": "http://test.com/transcript"
            }
        ], 
        "host_id": "test_host_id"
    }
    mock_fetch_transcript.return_value = "Test transcript"
    
    # Mock the transcript manager
    mock_manager = AsyncMock()
    mock_manager.process_raw_meeting_content.return_value = {"status": "success"}
    mock_get_manager.return_value = mock_manager
    
    # Create a mock client that can be used in an async with statement
    mock_client = AsyncMock()
    mock_response = AsyncMock()
    mock_response.text = "Test transcript content"
    mock_response.raise_for_status = AsyncMock()
    mock_client.get.return_value = mock_response
    
    # Mock the AsyncClient class
    class MockAsyncClient:
        def __init__(self, *args, **kwargs):
            pass
        
        async def __aenter__(self):
            return mock_client
            
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass
    
    # Mock asyncio.sleep to avoid delays in tests
    with patch("asyncio.sleep", AsyncMock()), \
         patch("src.zoom_transcript_retrieval.AsyncClient", MockAsyncClient), \
         patch("src.zoom_transcript_retrieval.is_token_expired", return_value=False):
        # Call the function
        await process_meeting_content("meeting123", "test_token")
    
    # Assertions
    mock_fetch_recordings.assert_called_with("meeting123", "test_token")
    # We don't assert on fetch_transcript because it's not called directly in the function


@patch('src.zoom_transcript_retrieval.fetch_zoom_recordings')
@patch('src.zoom_transcript_retrieval.logger')
@pytest.mark.asyncio
async def test_process_meeting_content_exception_handling(mock_logger, mock_fetch_recordings):
    """
    Test exception handling in the function.
    
    Ensures exceptions are logged and re-raised.
    """
    # Setup mock to raise an exception
    mock_fetch_recordings.side_effect = Exception("Test Error")
    
    # Call the function and expect an exception
    with pytest.raises(Exception, match="Test Error"):
        await process_meeting_content("meeting123", "test_token")
    
    # Verify error is logged
    mock_logger.error.assert_called_once()