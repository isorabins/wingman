#!/usr/bin/env python3
"""
Tests for Claude Agent - Direct Anthropic SDK implementation
Tests that the agent correctly integrates with the official Anthropic SDK.
"""

import pytest
import os
import sys
from unittest.mock import patch, AsyncMock, MagicMock

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.claude_agent import get_anthropic_client, interact_with_agent, interact_with_agent_stream


class TestClaudeAgentSingleton:
    """Test Claude Agent singleton pattern"""
    
    @pytest.mark.asyncio
    async def test_get_anthropic_client_singleton(self):
        """Test that get_anthropic_client returns the same instance"""
        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'sk-ant-test-key'}):
            # Reset the global singleton for clean test
            import src.claude_agent
            src.claude_agent._anthropic_client = None
            
            client1 = await get_anthropic_client()
            client2 = await get_anthropic_client()
            
            assert client1 is client2  # Same instance


class TestClaudeAgentInteraction:
    """Test Claude Agent interaction functions"""
    
    @pytest.fixture
    def mock_supabase(self):
        """Mock Supabase client with proper async structure"""
        supabase = MagicMock()
        # Mock the table().select().eq().execute() chain
        supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock()
        supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
        supabase.table.return_value.insert.return_value.execute.return_value = MagicMock()
        return supabase
    
    @pytest.fixture 
    def mock_memory(self):
        """Mock memory context"""
        memory = AsyncMock()
        memory.get_context.return_value = {
            "messages": [],
            "summaries": []
        }
        memory.get_caching_optimized_context.return_value = {
            "static_context": {
                "user_profile": {},
                "project_overview": {},
                "has_complete_profile": False,
                "has_project": False
            },
            "dynamic_context": {
                "conversation_messages": [],
                "buffer_summaries": [],
                "thread_id": "test-thread-456"
            }
        }
        memory.ensure_creator_profile = AsyncMock()
        memory.add_message = AsyncMock()
        return memory
    
    @pytest.mark.asyncio
    async def test_interact_with_agent_basic(self, mock_supabase, mock_memory):
        """Test basic agent interaction"""
        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'sk-ant-test-key'}):
            with patch('src.claude_agent.SimpleMemory', return_value=mock_memory):
                with patch('src.claude_agent.check_and_handle_project_onboarding') as mock_onboarding:
                    with patch('src.claude_agent.get_anthropic_client') as mock_get_client:
                        
                        # Setup mocks for new Anthropic SDK pattern
                        mock_onboarding.return_value = {"should_onboard": False, "prompt": None, "flow_type": None}
                        mock_anthropic_client = AsyncMock()
                        
                        # Mock the messages.create response structure
                        mock_response = MagicMock()
                        mock_response.content = [MagicMock()]
                        mock_response.content[0].text = "Hello! How can I help you today?"
                        mock_anthropic_client.messages.create.return_value = mock_response
                        
                        mock_get_client.return_value = mock_anthropic_client
                        
                        # Call the function
                        response = await interact_with_agent(
                            user_input="Hello",
                            user_id="test-user-123",
                            user_timezone="UTC",
                            thread_id="test-thread-456",
                            supabase_client=mock_supabase,
                            context={}
                        )
                        
                        # Verify response
                        assert response == "Hello! How can I help you today?"
                        
                        # Verify Anthropic client was called
                        mock_anthropic_client.messages.create.assert_called_once()
                        
                        # Verify memory operations were called (with new caching implementation)
                        mock_memory.get_caching_optimized_context.assert_called_with("test-thread-456")
                        mock_memory.add_message.assert_called()
    
    @pytest.mark.asyncio
    async def test_interact_with_agent_streaming(self, mock_supabase, mock_memory):
        """Test streaming agent interaction"""
        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'sk-ant-test-key'}):
            with patch('src.claude_agent.SimpleMemory', return_value=mock_memory):
                with patch('src.claude_agent.get_anthropic_client') as mock_get_client:
                    
                    # Mock streaming response with correct async context manager pattern
                    mock_anthropic_client = AsyncMock()
                    
                    # Create a proper async context manager mock
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
                    mock_anthropic_client.messages = MagicMock()
                    mock_anthropic_client.messages.stream = MagicMock(return_value=mock_stream_context)
                    mock_get_client.return_value = mock_anthropic_client
                    
                    # Call the streaming function
                    chunks = []
                    async for chunk in interact_with_agent_stream(
                        user_input="Tell me a story",
                        user_id="test-user-123", 
                        user_timezone="UTC",
                        thread_id="test-thread-456",
                        supabase_client=mock_supabase,
                        context={}
                    ):
                        chunks.append(chunk)
                    
                    # Verify streaming response
                    assert chunks == ["Hello ", "from ", "Claude!"]
                    
                    # Verify Anthropic client streaming was called
                    mock_anthropic_client.messages.stream.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_interact_with_agent_with_onboarding(self, mock_supabase, mock_memory):
        """Test agent interaction that triggers project onboarding"""
        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'sk-ant-test-key'}):
            with patch('src.claude_agent.SimpleMemory', return_value=mock_memory):
                with patch('src.claude_agent.check_and_handle_project_onboarding') as mock_onboarding:
                    with patch('src.claude_agent.get_anthropic_client') as mock_get_client:
                        
                                                # Setup onboarding trigger
                        mock_onboarding.return_value = {
                            "should_onboard": True,
                            "prompt": "Let's plan your project!",
                            "flow_type": "project_planning"
                        }
                        mock_anthropic_client = AsyncMock()
                        
                        # Mock the messages.create response structure
                        mock_response = MagicMock()
                        mock_response.content = [MagicMock()]
                        mock_response.content[0].text = "Great! Let's start planning."
                        mock_anthropic_client.messages.create.return_value = mock_response
                        
                        mock_get_client.return_value = mock_anthropic_client
                        
                        # Call the function
                        response = await interact_with_agent(
                            user_input="I want to build an app",
                            user_id="test-user-123",
                            user_timezone="UTC", 
                            thread_id="test-thread-456",
                            supabase_client=mock_supabase,
                            context={}
                        )
                        
                        # Verify response
                        assert response == "Great! Let's start planning."
                        
                        # Verify onboarding was triggered
                        mock_onboarding.assert_called_once()
                        
                        # Verify Anthropic client was called
                        mock_anthropic_client.messages.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_interact_with_agent_error_handling(self, mock_supabase, mock_memory):
        """Test agent error handling"""
        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'sk-ant-test-key'}):
            with patch('src.claude_agent.SimpleMemory', return_value=mock_memory):
                with patch('src.claude_agent.check_and_handle_project_onboarding') as mock_onboarding:
                    with patch('src.claude_agent.get_anthropic_client') as mock_get_client:
                        
                        # Setup mocks
                        mock_onboarding.return_value = {"should_onboard": False, "prompt": None}
                        mock_anthropic_client = AsyncMock()
                        mock_anthropic_client.messages.create.side_effect = Exception("API Error")
                        mock_get_client.return_value = mock_anthropic_client
                        
                        # Call the function
                        response = await interact_with_agent(
                            user_input="Hello",
                            user_id="test-user-123",
                            user_timezone="UTC",
                            thread_id="test-thread-456", 
                            supabase_client=mock_supabase,
                            context={}
                        )
                        
                        # Should return error message
                        assert "error" in response.lower() or "failed" in response.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 