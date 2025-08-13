import os
import sys
import asyncio
import json
from typing import List, Dict, Any, AsyncGenerator

# Add project root to Python path for src imports
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from src.claude_agent import interact_with_agent_stream

# Test configuration
class TestConfig:
    TEST_ENV = "ci"  # Set to "local_with_api" for real API tests

@pytest.mark.asyncio
async def test_interact_with_agent_stream():
    """Test streaming interaction with Claude agent"""
    # Setup mock dependencies
    mock_supabase_client = MagicMock()
    
    # Mock Supabase table operations
    mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
    mock_supabase_client.table.return_value.insert.return_value.execute.return_value = MagicMock()
    
    # Create mock memory instance
    mock_memory_instance = AsyncMock()
    mock_memory_instance.get_caching_optimized_context = AsyncMock(
        return_value={
            "static_context": {
                "user_profile": None,
                "project_overview": None,
                "project_updates": [],
                "longterm_summaries": [],
                "has_complete_profile": False,
                "has_project": False
            },
            "dynamic_context": {
                "conversation_messages": [],
                "buffer_summaries": [],
                "thread_id": "test_thread_456"
            }
        }
    )
    mock_memory_instance.ensure_creator_profile = AsyncMock()
    mock_memory_instance.add_message = AsyncMock()
    
    # Setup test input
    user_input = "Tell me a story about AI"
    user_id = "test_user_123"
    user_timezone = "UTC"
    thread_id = "test_thread_456"
    context = {}
    
    # Mock streaming response
    async def mock_stream():
        yield "Hello "
        yield "from "
        yield "Claude!"
    
    # Mock the get_anthropic_client function and memory
    with patch("src.claude_agent.SimpleMemory", return_value=mock_memory_instance), \
         patch("src.claude_agent.get_anthropic_client") as mock_get_client:
        
        # Mock Anthropic client instance with proper streaming support
        mock_client_instance = AsyncMock()
        
        # Create a proper async context manager mock for streaming
        class MockStreamContext:
            def __init__(self):
                pass
            
            async def __aenter__(self):
                return self
                
            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass
                
            @property
            def text_stream(self):
                async def _text_stream():
                    yield "Hello "
                    yield "from "
                    yield "Claude!"
                return _text_stream()
        
        mock_stream_context = MockStreamContext()
        # Ensure that messages.stream returns the context directly, not a coroutine
        mock_client_instance.messages = MagicMock()
        mock_client_instance.messages.stream = MagicMock(return_value=mock_stream_context)
        mock_get_client.return_value = mock_client_instance
        
        # Mock project onboarding check
        with patch("src.claude_agent.check_and_handle_project_onboarding") as mock_onboarding:
            mock_onboarding.return_value = {"should_onboard": False, "prompt": None}
            
            # Call the streaming function and collect results
            response_chunks = []
            async for chunk in interact_with_agent_stream(
                user_input, user_id, user_timezone, thread_id, mock_supabase_client, context
            ):
                response_chunks.append(chunk)
            
            # Assertions
            assert len(response_chunks) == 3
            assert response_chunks == ["Hello ", "from ", "Claude!"]
            mock_memory_instance.get_caching_optimized_context.assert_called_once_with(thread_id)
            mock_client_instance.messages.stream.assert_called_once()


@pytest.mark.asyncio
async def test_interact_with_agent_stream_error():
    """Test error handling in streaming interaction"""
    # Setup mock dependencies
    mock_supabase_client = MagicMock()
    
    # Mock Supabase table operations
    mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
    mock_supabase_client.table.return_value.insert.return_value.execute.return_value = MagicMock()
    
    # Create mock memory instance
    mock_memory_instance = AsyncMock()
    mock_memory_instance.get_caching_optimized_context = AsyncMock(
        return_value={
            "static_context": {
                "user_profile": None,
                "project_overview": None,
                "project_updates": [],
                "longterm_summaries": [],
                "has_complete_profile": False,
                "has_project": False
            },
            "dynamic_context": {
                "conversation_messages": [],
                "buffer_summaries": [],
                "thread_id": "test_thread_456"
            }
        }
    )
    mock_memory_instance.ensure_creator_profile = AsyncMock()
    
    # Setup test input
    user_input = "Tell me a story"
    user_id = "test_user_123"
    user_timezone = "UTC"
    thread_id = "test_thread_456"
    context = {}
    
    # Mock the get_anthropic_client function to raise an exception
    with patch("src.claude_agent.SimpleMemory", return_value=mock_memory_instance), \
         patch("src.claude_agent.get_anthropic_client") as mock_get_client:
        
        # Mock Anthropic client instance that raises an exception
        mock_client_instance = AsyncMock()
        mock_client_instance.messages.stream.return_value = AsyncMock(side_effect=Exception("Streaming API error"))
        mock_get_client.return_value = mock_client_instance
        
        # Mock project onboarding check
        with patch("src.claude_agent.check_and_handle_project_onboarding") as mock_onboarding:
            mock_onboarding.return_value = {"should_onboard": False, "prompt": None}
            
            # Call the streaming function and collect results
            response_chunks = []
            async for chunk in interact_with_agent_stream(
                user_input, user_id, user_timezone, thread_id, mock_supabase_client, context
            ):
                response_chunks.append(chunk)
            
            # Should get error message instead of raising
            assert len(response_chunks) >= 1
            assert any("error" in chunk.lower() for chunk in response_chunks)


@pytest.mark.asyncio 
async def test_streaming_endpoint_integration():
    """Test streaming endpoint integration - only runs with real API"""
    if TestConfig.TEST_ENV != "local_with_api":
        pytest.skip("Skipping real API test in CI environment")
        
    # This test would only run in local development with real API keys
    # In CI, it's automatically skipped
    pass 