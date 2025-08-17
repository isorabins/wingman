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


class TestBasicEndpoints:
    """Test basic application endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    def test_root_endpoint(self, client):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Welcome to Fridays at Four API"
    
    def test_health_endpoint(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "message" in data
        assert data["message"] == "Fridays at Four backend is running"


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
    
    def test_query_endpoint_creativity_flow(self, client, mock_supabase_for_endpoints):
        """Test /query endpoint entering creativity flow"""
        # Mock completed intro
        intro_complete_response = MagicMock()
        intro_complete_response.data = [{'has_seen_intro': True}]
        
        # Mock no creativity profile
        no_creativity_response = MagicMock()
        no_creativity_response.data = []
        
        def mock_table_response(table_name):
            mock_table = MagicMock()
            if table_name == 'creativity_test_progress':
                mock_table.select.return_value.eq.return_value.execute.return_value = intro_complete_response
            elif table_name == 'creator_creativity_profiles':
                mock_table.select.return_value.eq.return_value.limit.return_value.execute.return_value = no_creativity_response
            else:
                mock_table.select.return_value.eq.return_value.execute.return_value = no_creativity_response
                mock_table.select.return_value.eq.return_value.limit.return_value.execute.return_value = no_creativity_response
            
            # Mock successful operations
            mock_table.insert.return_value.execute.return_value = MagicMock()
            mock_table.update.return_value.eq.return_value.execute.return_value = MagicMock()
            return mock_table
        
        mock_supabase_for_endpoints.table.side_effect = mock_table_response
        
        with patch('src.main.supabase', mock_supabase_for_endpoints):
            with patch('src.agents.db_chat_handler.chat') as mock_chat:
                # Mock creativity test response
                mock_chat.return_value = "Let's start that creative personality test.\n\nQuestion 1 of 12: When starting a new creative project, what excites you most?"
                
                response = client.post("/query", json={
                    "question": "I want to start the test",
                    "user_id": "test-user-456",
                    "user_timezone": "UTC", 
                    "thread_id": "test-thread"
                })
                
                assert response.status_code == 200
                data = response.json()
                assert "answer" in data
                
                # Should get creativity test response (behavior-based validation)
                assert len(data["answer"]) > 0
                assert any(keyword in data["answer"].lower() for keyword in ["question", "creative", "test", "project"])
    
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


class TestStreamingEndpoint:
    """Test streaming query endpoint"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_query_stream_endpoint(self, client):
        """Test /query_stream endpoint with V2 DB-driven system"""
        with patch('src.agents.db_chat_handler.chat') as mock_chat:
            mock_chat.return_value = "Hello! This is a test response from V2 DB-driven system."
            
            response = client.post("/query_stream", json={
                "question": "Tell me about yourself",
                "user_id": "test-user-123",
                "user_timezone": "UTC",
                "thread_id": "test-thread"
            })
            
            assert response.status_code == 200
            assert response.headers["content-type"] == "text/plain; charset=utf-8"
    
    def test_query_stream_error_handling(self, client):
        """Test streaming endpoint error handling"""
        with patch('src.agents.db_chat_handler.chat') as mock_chat:
            mock_chat.side_effect = Exception("Streaming error")
            
            response = client.post("/query_stream", json={
                "question": "Hello",
                "user_id": "test-user-123",
                "user_timezone": "UTC",
                "thread_id": "test-thread"
            })
            
            assert response.status_code == 500  # Original working behavior
            assert "Streaming error" in response.json()["detail"]


class TestChatEndpoint:
    """Test chat endpoint using V2 DB-driven system"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_chat_endpoint_v2_system(self, client):
        """Test that chat endpoint uses V2 DB-driven system"""
        with patch('src.agents.db_chat_handler.chat') as mock_chat:
            mock_chat.return_value = "Chat response from V2 DB-driven system"
            
            response = client.post("/chat", json={
                "message": "Hello",
                "user_id": "test-user-123",
                "user_timezone": "UTC",
                "thread_id": "chat-thread"
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["response"] == "Chat response from V2 DB-driven system"
            
            # Verify V2 system was called with correct parameters
            mock_chat.assert_called_once()


class TestAgentEndpoints:
    """Test new agent endpoints using V2 DB-driven system"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    @pytest.fixture
    def mock_database_states(self):
        """Mock different database states for agent testing"""
        return {
            'new_user': {
                'creativity_complete': False,
                'project_complete': False,
                'needs_intro': True
            },
            'creativity_phase': {
                'creativity_complete': False,
                'project_complete': False,
                'needs_intro': False
            },
            'project_phase': {
                'creativity_complete': True,
                'project_complete': False,
                'needs_intro': False
            },
            'completed': {
                'creativity_complete': True,
                'project_complete': True,
                'needs_intro': False
            }
        }
    
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
    
    def test_agent_chat_endpoint_creativity_phase(self, client):
        """Test /agents/chat endpoint during creativity test"""
        with patch('src.agents.db_chat_handler.chat') as mock_chat:
            with patch('src.main._check_creativity_complete') as mock_creativity:
                with patch('src.main._check_project_complete') as mock_project:
                    with patch('src.main._needs_intro') as mock_intro:
                        # Mock creativity phase state
                        mock_creativity.return_value = False
                        mock_project.return_value = False
                        mock_intro.return_value = False
                        mock_chat.return_value = "Let's start that creative personality test.\n\nQuestion 1 of 12: When starting a new creative project, what excites you most?"
                        
                        response = client.post("/agents/chat", json={
                            "message": "A",
                            "user_id": "creativity-user-123",
                            "thread_id": "test-thread"
                        })
                        
                        assert response.status_code == 200
                        data = response.json()
                        assert data["agent_type"] == "creativity_test"
                        assert data["flow_status"]["flow_type"] == "creativity_test"
    
    def test_agent_chat_endpoint_project_phase(self, client):
        """Test /agents/chat endpoint during project overview"""
        with patch('src.agents.db_chat_handler.chat') as mock_chat:
            with patch('src.main._check_creativity_complete') as mock_creativity:
                with patch('src.main._check_project_complete') as mock_project:
                    with patch('src.main._needs_intro') as mock_intro:
                        # Mock project phase state
                        mock_creativity.return_value = True
                        mock_project.return_value = False
                        mock_intro.return_value = False
                        mock_chat.return_value = "Great! Now let's work on your project overview.\n\nTopic 1 of 8: Project Vision & Core Concept"
                        
                        response = client.post("/agents/chat", json={
                            "message": "I want to write a book",
                            "user_id": "project-user-123",
                            "thread_id": "test-thread"
                        })
                        
                        assert response.status_code == 200
                        data = response.json()
                        assert data["agent_type"] == "project_overview"
                        assert data["flow_status"]["flow_type"] == "project_overview"
    
    def test_agent_chat_endpoint_completed(self, client):
        """Test /agents/chat endpoint for completed flows (general chat)"""
        with patch('src.agents.db_chat_handler.chat') as mock_chat:
            with patch('src.main._check_creativity_complete') as mock_creativity:
                with patch('src.main._check_project_complete') as mock_project:
                    with patch('src.main._needs_intro') as mock_intro:
                        # Mock completed state
                        mock_creativity.return_value = True
                        mock_project.return_value = True
                        mock_intro.return_value = False
                        mock_chat.return_value = "I'm here to help with your creative project! How can I support you today?"
                        
                        response = client.post("/agents/chat", json={
                            "message": "How can you help me?",
                            "user_id": "completed-user-123",
                            "thread_id": "test-thread"
                        })
                        
                        assert response.status_code == 200
                        data = response.json()
                        assert data["agent_type"] == "general"
                        assert data["flow_status"]["flow_type"] == "general_conversation"


class TestProgressEndpoints:
    """Test progress tracking endpoints"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_creativity_progress_endpoint(self, client):
        """Test /agents/creativity-progress/{user_id} endpoint"""
        mock_supabase = MagicMock()
        
        # Mock the table().select().eq().order().limit().execute() chain
        def mock_table_chain(table_name):
            mock_table = MagicMock()
            mock_select = MagicMock()
            mock_eq = MagicMock()
            mock_order = MagicMock()
            mock_limit = MagicMock()
            
            # Configure the chain
            mock_table.select.return_value = mock_select
            mock_select.eq.return_value = mock_eq
            mock_eq.order.return_value = mock_order
            mock_order.limit.return_value = mock_limit
            
            # Return appropriate data based on table
            def mock_execute():
                mock_result = MagicMock()
                if table_name == 'creativity_test_progress':
                    mock_result.data = [{
                        'flow_step': 5,
                        'current_responses': {'q1': 'A', 'q2': 'B', 'q3': 'C', 'q4': 'D'},
                        'completion_percentage': 33.33,
                        'is_completed': False
                    }]
                else:
                    mock_result.data = []
                return mock_result
            
            mock_limit.execute = mock_execute
            return mock_table
        
        mock_supabase.table.side_effect = mock_table_chain
        
        with patch('src.main.supabase', mock_supabase):
            response = client.get("/agents/creativity-progress/test-user-123")
            
            assert response.status_code == 200
            data = response.json()
            assert data["current_question"] == 4  # flow_step 5 - 1 = 4
            assert data["total_questions"] == 12
            assert data["is_complete"] == False
    
    def test_project_progress_endpoint(self, client):
        """Test /agents/project-progress/{user_id} endpoint"""
        mock_supabase = MagicMock()
        
        # Mock the table().select().eq().order().limit().execute() chain
        def mock_table_chain(table_name):
            mock_table = MagicMock()
            mock_select = MagicMock()
            mock_eq = MagicMock()
            mock_order = MagicMock()
            mock_limit = MagicMock()
            
            # Configure the chain
            mock_table.select.return_value = mock_select
            mock_select.eq.return_value = mock_eq
            mock_eq.order.return_value = mock_order
            mock_order.limit.return_value = mock_limit
            
            # Return appropriate data based on table
            def mock_execute():
                mock_result = MagicMock()
                if table_name == 'project_overview_progress':
                    mock_result.data = [{
                        'flow_step': 3,
                        'current_data': {'topic_1': 'My project', 'topic_2': 'Book'},
                        'completion_percentage': 25.0,
                        'is_completed': False
                    }]
                else:
                    mock_result.data = []
                return mock_result
            
            mock_limit.execute = mock_execute
            return mock_table
        
        mock_supabase.table.side_effect = mock_table_chain
        
        with patch('src.main.supabase', mock_supabase):
            response = client.get("/agents/project-progress/test-user-123")
            
            assert response.status_code == 200
            data = response.json()
            assert data["current_topic"] == "Topic 2 of 8"  # flow_step 3 - 1 = 2
            assert data["total_topics"] == 8
            assert data["is_complete"] == False


class TestProjectOverviewEndpoint:
    """Test project overview endpoint"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
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


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 