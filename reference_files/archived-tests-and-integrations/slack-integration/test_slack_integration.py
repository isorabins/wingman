import sys
import os
# Add project root to Python path for src imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import pytest_asyncio
from test_config import TestConfig as Config

import asyncio

os.environ["SLACK_CLIENT_ID"] = Config.SLACK_CLIENT_ID
os.environ["SLACK_CLIENT_SECRET"] = "No"

from src.slack_bot import handle_message
from src.slack_bot import RedisManager
redis_manager = RedisManager()


@pytest.fixture
def mock_dependencies():
    """Create mock objects for dependencies used in the message handler."""

    # Create mock objects
    mock_supabase = MagicMock()
    mock_table = MagicMock()
    mock_select = MagicMock()
    mock_eq = MagicMock()
    mock_single = MagicMock()

    # Create an AsyncMock for execute
    # mock_execute = AsyncMock()
    # mock_execute.return_value = MagicMock(
    #     data={'id': 'creator1', 'slack_id': 'U12345'})
    # Create a MagicMock for execute to simulate synchronous behavior
    mock_execute = MagicMock(return_value=MagicMock(data={'id': 'creator1', 'slack_id': 'U12345'}))


    # Build the chain
    mock_single.execute = mock_execute
    mock_eq.single.return_value = mock_single
    mock_select.eq.return_value = mock_eq
    mock_table.select.return_value = mock_select
    mock_supabase.table.return_value = mock_table

    return {
        'redis_manager': AsyncMock(),
        'supabase': mock_supabase,
        'installation_store': AsyncMock(),
        'app': AsyncMock(),
        'say': AsyncMock(),
    }


@pytest_asyncio.fixture
async def typical_slack_dm_event(mock_dependencies):
    """Create a typical Slack direct message event for testing."""
    return {
        "event": {
            "type": "message",
            "channel_type": "im",
            "user": "U12345",
            "text": "Hello, test message"
        },
        "team_id": "T54321",
        "event_id": "Ev123456"
    }


@patch("src.slack_bot.redis_manager", new_callable=AsyncMock)
@pytest.mark.asyncio
async def test_handle_message_successful_dm(mock_redis, mock_dependencies, typical_slack_dm_event):
    """Test successful handling of a direct message for a registered user."""

    # Configure Redis mock
    mock_redis.is_event_processed.return_value = False
    mock_redis.mark_event_processed = AsyncMock()

    # Debug: Test the mock chain directly
    mock_supabase = mock_dependencies['supabase']
    # test_result = await mock_supabase.table('creator_profiles').select('*').eq('slack_id', 'U12345').single().execute()
    # print(f"\nTest result before actual test: {test_result}")
    # print(f"Test result data: {test_result.data}")

    test_result = mock_supabase.table('creator_profiles').select('*').eq('slack_id', 'U12345').single().execute()
    print(f"\nTest result before actual test: {test_result}")
    print(f"Test result data: {test_result.data}")


    # Update patch to use src.slack_bot
    with patch("src.slack_bot.supabase", mock_dependencies['supabase']):
        # Call the handler with mocked dependencies
        await handle_message(
            body=typical_slack_dm_event,
            say=mock_dependencies['say']
        )

        # Assertions
        mock_redis.mark_event_processed.assert_called_once()
        mock_dependencies['say'].assert_called_once()

        # Verify Supabase calls
        mock_supabase.table.assert_called_with('creator_profiles')
        mock_supabase.table().select.assert_called_with('*')
