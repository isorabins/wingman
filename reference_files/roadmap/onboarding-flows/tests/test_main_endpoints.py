#!/usr/bin/env python3
"""
Tests for main FastAPI endpoints with simple Claude client.
These tests verify that all API endpoints work correctly with mocked dependencies.
"""

import pytest
import os
import sys
import unittest.mock
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.main import app


@pytest.fixture
def client():
    """Create test client for FastAPI app"""
    return TestClient(app)


@pytest.fixture
def mock_supabase():
    """Mock Supabase client with proper structure"""
    supabase = MagicMock()
    
    # Mock table operations for different scenarios
    def mock_table_response(table_name):
        mock_table = MagicMock()
        
        if table_name == 'creator_profiles':
            # Mock profile exists
            mock_table.select.return_value.eq.return_value.limit.return_value.execute.return_value.data = [
                {"id": "test-user-123", "first_name": "Test", "last_name": "User"}
            ]
        elif table_name == 'project_overview':
            # Mock no project overview initially
            mock_table.select.return_value.eq.return_value.limit.return_value.execute.return_value.data = []
        elif table_name == 'memory':
            # Mock memory/conversation data
            mock_table.select.return_value.eq.return_value.order.return_value.range.return_value.execute.return_value.data = [
                {"content": "user: Hello", "created_at": "2024-12-01T10:00:00Z"},
                {"content": "assistant: Hi there!", "created_at": "2024-12-01T10:01:00Z"}
            ]
        
        mock_table.insert.return_value.execute.return_value = {"data": [{"id": "new-id"}]}
        return mock_table
    
    supabase.table.side_effect = mock_table_response
    return supabase


class TestBasicEndpoints:
    """Test basic API endpoints"""
    
    def test_root_endpoint(self, client):
        """Test root endpoint returns welcome message"""
        response = client.get("/")
        assert response.status_code == 200
        assert "Welcome to Fridays at Four API" in response.json()["message"]
    
    @patch('src.main.SimpleMemory')
    def test_health_check_success(self, mock_memory, client, mock_supabase):
        """Test health check endpoint with successful dependencies"""
        
        # Mock memory
        mock_memory_instance = AsyncMock()
        mock_memory_instance.get_context.return_value = {"messages": [], "summaries": []}
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
        mock_memory.return_value = mock_memory_instance
        
        # Patch supabase in main
        with patch('src.main.supabase', mock_supabase):
            response = client.get("/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert "timestamp" in data
            assert "message" in data
            assert data["message"] == "Fridays at Four backend is running"


class TestChatHistoryEndpoint:
    """Test chat history endpoint"""
    
    def test_get_chat_history_success(self, client, mock_supabase):
        """Test successful chat history retrieval"""
        with patch('src.main.supabase', mock_supabase):
            response = client.get("/chat-history/test-user-123?limit=10")
            
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            
            # Verify the parsed message format
            if data:
                message = data[0]
                assert "role" in message
                assert "content" in message
                assert "timestamp" in message
    
    def test_get_chat_history_with_pagination(self, client, mock_supabase):
        """Test chat history with pagination parameters"""
        with patch('src.main.supabase', mock_supabase):
            response = client.get("/chat-history/test-user-123?limit=5&offset=10")
            
            assert response.status_code == 200
            # Verify pagination parameters are handled - just check that table was called
            mock_supabase.table.assert_called_with('memory')


class TestProjectOverviewEndpoint:
    """Test project overview endpoint"""
    
    def test_get_project_overview_no_profile(self, client):
        """Test project overview when user profile doesn't exist"""
        mock_supabase = MagicMock()
        # Mock no creator profile
        mock_supabase.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value.data = []
        
        with patch('src.main.supabase', mock_supabase):
            response = client.get("/project-overview/nonexistent-user")
            
            assert response.status_code == 200
            data = response.json()
            assert data["error"] == "user_not_found"
            assert data["needs_auth"] is True
    
    def test_get_project_overview_no_project(self, client, mock_supabase):
        """Test project overview when user exists but has no project"""
        with patch('src.main.supabase', mock_supabase):
            response = client.get("/project-overview/test-user-123")
            
            assert response.status_code == 200
            data = response.json()
            assert data["error"] == "no_project_overview"
            assert data["needs_onboarding"] is True
            assert "onboarding_prompt" in data
    
    def test_get_project_overview_exists(self, client):
        """Test project overview when project exists"""
        mock_supabase = MagicMock()
        
        # Mock profile exists
        mock_supabase.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value.data = [
            {"id": "test-user-123"}
        ]
        
        # Mock project overview exists
        def mock_table_response(table_name):
            mock_table = MagicMock()
            if table_name == 'creator_profiles':
                mock_table.select.return_value.eq.return_value.limit.return_value.execute.return_value.data = [
                    {"id": "test-user-123"}
                ]
            elif table_name == 'project_overview':
                mock_table.select.return_value.eq.return_value.limit.return_value.execute.return_value.data = [
                    {
                        "id": "project-123",
                        "user_id": "test-user-123",
                        "project_name": "My Test Project",
                        "project_type": "Book",
                        "description": "A test project",
                        "current_phase": "Planning",
                        "goals": [],
                        "challenges": [],
                        "success_metrics": {},
                        "creation_date": "2024-12-01",
                        "last_updated": "2024-12-01"
                    }
                ]
            return mock_table
        
        mock_supabase.table.side_effect = mock_table_response
        
        with patch('src.main.supabase', mock_supabase):
            response = client.get("/project-overview/test-user-123")
            
            assert response.status_code == 200
            data = response.json()
            assert data["project_name"] == "My Test Project"
            assert data["user_id"] == "test-user-123"


class TestQueryEndpoint:
    """Test main query endpoint with SimpleChatHandler integration"""
    
    @patch('src.simple_chat_handler.process_chat_message')
    def test_query_success(self, mock_process_chat, client):
        """Test successful query processing with SimpleChatHandler"""
        # Mock process_chat_message response
        mock_process_chat.return_value = "Hello! How can I help you today?"
        
        response = client.post("/query", json={
            "question": "Hello",
            "user_id": "test-user-123",
            "user_timezone": "UTC",
            "thread_id": "test-thread"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["answer"] == "Hello! How can I help you today?"
        assert "sources" in data
        assert data["sources"] == ["Processed by SimpleChatHandler"]
        
        # Verify process_chat_message was called with correct parameters
        mock_process_chat.assert_called_once_with(
            user_id="test-user-123",
            message="Hello",
            thread_id="test-thread",
            supabase_client=unittest.mock.ANY
        )
    
    @patch('src.simple_chat_handler.process_chat_message')
    def test_query_agent_error(self, mock_process_chat, client):
        """Test query endpoint when SimpleChatHandler raises an error"""
        # Mock SimpleChatHandler error
        mock_process_chat.side_effect = Exception("SimpleChatHandler error")
        
        response = client.post("/query", json={
            "question": "Hello",
            "user_id": "test-user-123",
            "user_timezone": "UTC",
            "thread_id": "test-thread"
        })
        
        assert response.status_code == 500
        assert "SimpleChatHandler error" in response.json()["detail"]


class TestStreamingEndpoint:
    """Test streaming query endpoint"""
    
    @patch('src.simple_chat_handler.process_chat_message')
    def test_query_stream_success(self, mock_process_chat, client):
        """Test successful streaming query with SimpleChatHandler"""
        # Mock process_chat_message response for streaming
        mock_process_chat.return_value = "Hello from SimpleChatHandler!"
        
        response = client.post("/query_stream", json={
            "question": "Tell me a story",
            "user_id": "test-user-123",
            "user_timezone": "UTC",
            "thread_id": "test-thread"
        })
        
        assert response.status_code == 200
        # For streaming, we mainly verify the response started successfully
        # Full streaming testing is better done in integration tests


class TestChatEndpoint:
    """Test chat endpoint that maps to query logic"""
    
    @patch('src.simple_chat_handler.process_chat_message')
    def test_chat_endpoint_mapping(self, mock_process_chat, client):
        """Test that chat endpoint correctly maps to SimpleChatHandler logic"""
        # Mock process_chat_message response
        mock_process_chat.return_value = "Chat response from SimpleChatHandler"
        
        response = client.post("/chat", json={
            "message": "Hello",
            "user_id": "test-user-123",
            "user_timezone": "UTC",
            "thread_id": "chat-thread"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["response"] == "Chat response from SimpleChatHandler"
        
        # Verify process_chat_message was called
        mock_process_chat.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 