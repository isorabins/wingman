#!/usr/bin/env python3
"""
Updated tests for main FastAPI endpoints using actual SimpleChatHandler
Tests the real production endpoints without mocking the core system
"""

import pytest
import os
import sys
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.main import app


class TestQueryEndpointWithSimpleChatHandler:
    """Test query endpoint using actual SimpleChatHandler"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    @pytest.fixture
    def mock_supabase_for_endpoints(self):
        """Mock Supabase for endpoint testing"""
        supabase = MagicMock()
        
        # Mock empty responses (new user)
        empty_response = MagicMock()
        empty_response.data = []
        supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = empty_response
        supabase.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = empty_response
        
        # Mock successful operations
        success_response = MagicMock()
        success_response.data = [{"id": "test-id"}]
        supabase.table.return_value.insert.return_value.execute.return_value = success_response
        supabase.table.return_value.update.return_value.eq.return_value.execute.return_value = success_response
        
        return supabase
    
    def test_query_endpoint_with_simple_chat_handler(self, client, mock_supabase_for_endpoints):
        """Test /query endpoint using actual SimpleChatHandler"""
        with patch('src.main.supabase', mock_supabase_for_endpoints):
            with patch('src.simple_chat_handler.SimpleMemory') as mock_memory:
                # Mock memory operations
                mock_memory_instance = AsyncMock()
                mock_memory_instance.add_message = AsyncMock()
                mock_memory.return_value = mock_memory_instance
                
                response = client.post("/query", json={
                    "question": "Hello, I'm new here",
                    "user_id": "test-user-123",
                    "user_timezone": "UTC",
                    "thread_id": "test-thread"
                })
                
                assert response.status_code == 200
                data = response.json()
                assert "answer" in data
                assert "sources" in data
                assert data["sources"] == ["Processed by SimpleChatHandler"]
                
                # Should get intro flow response
                assert "Hi, I'm Hai" in data["answer"] or len(data["answer"]) > 0
    
    def test_query_endpoint_error_handling(self, client):
        """Test /query endpoint error handling"""
        with patch('src.simple_chat_handler.process_chat_message') as mock_process:
            mock_process.side_effect = Exception("SimpleChatHandler error")
            
            response = client.post("/query", json={
                "question": "Hello",
                "user_id": "test-user-123",
                "user_timezone": "UTC",
                "thread_id": "test-thread"
            })
            
            assert response.status_code == 500
            assert "SimpleChatHandler error" in response.json()["detail"]


class TestAgentEndpoints:
    """Test new agent endpoints using SimpleChatHandler"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_agent_chat_endpoint_new_user(self, client):
        """Test /agents/chat endpoint for new user (intro flow)"""
        with patch('src.simple_chat_handler.process_chat_message') as mock_process:
            with patch('src.main._check_creativity_complete') as mock_creativity:
                with patch('src.main._check_project_complete') as mock_project:
                    with patch('src.main._needs_intro') as mock_intro:
                        # Mock new user state
                        mock_creativity.return_value = False
                        mock_project.return_value = False
                        mock_intro.return_value = True
                        mock_process.return_value = "Hi, I'm Hai. What's your name?"
                        
                        response = client.post("/agents/chat", json={
                            "message": "Hello",
                            "user_id": "new-user-123",
                            "thread_id": "test-thread"
                        })
                        
                        assert response.status_code == 200
                        data = response.json()
                        assert "response" in data
                        assert data["agent_type"] == "intro"
                        assert data["flow_status"]["flow_type"] == "intro"
                        assert data["flow_status"]["is_complete"] == False


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 