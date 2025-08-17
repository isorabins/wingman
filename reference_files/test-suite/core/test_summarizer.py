import os
import sys

# Add project root to Python path for src imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from src.content_summarizer import ContentSummarizer, BufferSummaryHandler, SummaryResult


@pytest.mark.asyncio
async def test_create_buffer_summary():
    """Test BufferSummaryHandler using mocked ContentSummarizer."""
    
    # Mock summarizer instead of using real one
    mock_summarizer = AsyncMock()
    mock_summarizer.ainvoke.return_value = {
        "final_summary": "Meeting summary: main_goal was to discuss project deadline. Key topics_to_revisit include task assignments. Deadline is friday."
    }
    
    # Create BufferSummaryHandler with the mocked summarizer
    buffer_handler = BufferSummaryHandler(mock_summarizer)
    
    # Sample conversation messages
    sample_messages = [
        {"role": "user", "message_text": "Hello, can you summarize our last meeting?"},
        {"role": "assistant", "message_text": "Sure! What was the main topic?"},
        {"role": "user", "message_text": "It was about the project deadline and tasks for next week."},
        {"role": "assistant", "message_text": "Got it! The deadline is next Friday, and tasks include report submission."}
    ]
    
    # Sample thread_id and user_id
    thread_id = "test_thread"
    user_id = "test_user"
    
    # Mock Supabase client
    mock_supabase_client = MagicMock()
    mock_supabase_table = MagicMock()
    
    # Mock table method to return another mock
    mock_supabase_client.table.return_value = mock_supabase_table
    
    # Mock insert operation
    mock_supabase_table.insert.return_value.execute.return_value = {
        "status": "success"}
    
    # Mock delete operation (to avoid errors in delete step)
    mock_supabase_table.delete.return_value.eq.return_value.execute.return_value = {
        "status": "success"}
    
    # Run summarization with mocked components
    result = await buffer_handler.create_buffer_summary(thread_id, sample_messages, user_id, mock_supabase_client)
    
    # Assertions
    assert isinstance(result, SummaryResult)
    assert result.summary, "The summary should not be empty."
    print(result.summary)
    
    # Check if important keywords appear in the summary
    expected_keywords = ["main_goal", "topics_to_revisit", "friday"]
    for keyword in expected_keywords:
        assert keyword in result.summary.lower(), f"Expected keyword '{keyword}' not found in summary."

    # Ensure Supabase insert was called
    mock_supabase_table.insert.assert_called_once()

    print(f"Generated Summary:\n{result.summary}")
