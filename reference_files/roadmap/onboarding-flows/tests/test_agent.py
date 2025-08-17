import os
import sys

# Add project root to Python path for src imports
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from src.claude_agent import interact_with_agent
from src.simple_memory import SimpleMemory

# Define mock response class
class MockResponse:
    def __init__(self, content):
        self.content = content

@pytest.mark.asyncio
async def test_interact_with_agent_success():
    """Test successful interaction with agent"""
    
    # Mock supabase client
    mock_supabase = MagicMock()
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
    
    # Mock memory
    mock_memory_instance = AsyncMock()
    mock_memory_instance.get_context.return_value = {
        "messages": [],
        "summaries": []
    }
    mock_memory_instance.get_caching_optimized_context.return_value = {
        "static_context": {
            "user_profile": {},
            "project_overview": {},
            "has_complete_profile": False,
            "has_project": False
        },
        "dynamic_context": {
            "conversation_messages": [],
            "buffer_summaries": [],
            "thread_id": "test-thread"
        }
    }
    mock_memory_instance.ensure_creator_profile = AsyncMock()
    mock_memory_instance.add_message = AsyncMock()
    
    # Mock onboarding check
    mock_onboarding_result = {"should_onboard": False, "prompt": None, "flow_type": None}
    
    # Mock Anthropic client response
    mock_response = MagicMock()
    mock_response.content = [MagicMock()]
    mock_response.content[0].text = "Hello! How can I help you today?"
    
    mock_anthropic_client = AsyncMock()
    mock_anthropic_client.messages.create.return_value = mock_response
    
    with patch("src.claude_agent.SimpleMemory", return_value=mock_memory_instance), \
         patch("src.claude_agent.check_and_handle_project_onboarding", return_value=mock_onboarding_result), \
         patch("src.claude_agent.get_anthropic_client", return_value=mock_anthropic_client):
        
        result = await interact_with_agent(
            user_input="Hello", 
            user_id="test-user-id",
            user_timezone="UTC",
            thread_id="test-thread",
            supabase_client=mock_supabase,
            context={}
        )
        
        assert result == "Hello! How can I help you today?"
        mock_anthropic_client.messages.create.assert_called_once()
        mock_memory_instance.get_caching_optimized_context.assert_called_with("test-thread")
        mock_memory_instance.add_message.assert_called()

@pytest.mark.asyncio 
async def test_interact_with_agent_error_handling():
    """Test error handling in agent interaction"""
    
    # Mock supabase client
    mock_supabase = MagicMock()
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
    
    # Mock memory
    mock_memory_instance = AsyncMock()
    mock_memory_instance.get_context.return_value = {
        "messages": [],
        "summaries": []
    }
    mock_memory_instance.get_caching_optimized_context.return_value = {
        "static_context": {
            "user_profile": {},
            "project_overview": {},
            "has_complete_profile": False,
            "has_project": False
        },
        "dynamic_context": {
            "conversation_messages": [],
            "buffer_summaries": [],
            "thread_id": "test-thread"
        }
    }
    mock_memory_instance.ensure_creator_profile = AsyncMock()
    mock_memory_instance.add_message = AsyncMock()
    
    # Mock onboarding check
    mock_onboarding_result = {"should_onboard": False, "prompt": None, "flow_type": None}
    
    # Mock Anthropic client to raise an exception
    mock_anthropic_client = AsyncMock()
    mock_anthropic_client.messages.create.side_effect = Exception("Test API error")
    
    with patch("src.claude_agent.SimpleMemory", return_value=mock_memory_instance), \
         patch("src.claude_agent.check_and_handle_project_onboarding", return_value=mock_onboarding_result), \
         patch("src.claude_agent.get_anthropic_client", return_value=mock_anthropic_client):
        
        result = await interact_with_agent(
            user_input="Hello",
            user_id="test-user-id", 
            user_timezone="UTC",
            thread_id="test-thread",
            supabase_client=mock_supabase,
            context={}
        )
        
        # Should return error message
        assert "error" in result.lower() or "failed" in result.lower()
