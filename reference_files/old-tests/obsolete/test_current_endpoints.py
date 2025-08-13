#!/usr/bin/env python3
"""
Updated tests for main FastAPI endpoints using V2 DB-driven system
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


class TestQueryEndpointWithV2System:
    """Test query endpoint using V2 DB-driven system"""
    
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
    
    def test_query_endpoint_with_v2_system(self, client, mock_supabase_for_endpoints):
        """Test /query endpoint using V2 DB-driven system"""
        with patch('src.main.supabase', mock_supabase_for_endpoints):
            with patch('src.agents.db_chat_handler.chat') as mock_chat:
                # Mock V2 system response
                mock_chat.return_value = "Hi! I'm Hai, your creative partner here at Fridays at Four.\n\nWhat's your name? I'd love to know what to call you."
                
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
                assert data["sources"] == ["Processed by V2 DB-Driven System"]
                
                # Should get intro flow response (behavior-based validation)
                assert len(data["answer"]) > 0
                assert any(keyword in data["answer"].lower() for keyword in ["hai", "fridays", "creative", "partner"])
    
    def test_query_endpoint_error_handling(self, client):
        """Test /query endpoint error handling"""
        with patch('src.agents.db_chat_handler.chat') as mock_chat:
            mock_chat.side_effect = Exception("V2 system error")
            
            response = client.post("/query", json={
                "question": "Hello",
                "user_id": "test-user-123",
                "user_timezone": "UTC",
                "thread_id": "test-thread"
            })
            
            assert response.status_code == 500
            assert "V2 system error" in response.json()["detail"]


class TestAgentEndpoints:
    """Test new agent endpoints using V2 DB-driven system"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_agent_chat_endpoint_new_user(self, client):
        """Test /agents/chat endpoint for new user (intro flow)"""
        with patch('src.agents.db_chat_handler.chat') as mock_chat:
            with patch('src.main._check_creativity_complete') as mock_creativity:
                with patch('src.main._check_project_complete') as mock_project:
                    with patch('src.main._needs_intro') as mock_intro:
                        # Mock new user state
                        mock_creativity.return_value = False
                        mock_project.return_value = False
                        mock_intro.return_value = True
                        mock_chat.return_value = "Hi! I'm Hai, your creative partner here at Fridays at Four.\n\nWhat's your name? I'd love to know what to call you."
                        
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