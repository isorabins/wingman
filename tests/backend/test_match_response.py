"""
Test suite for match response endpoint - Task 10 implementation

Tests the POST /api/buddy/respond endpoint following TDD approach:
- Accept-first scenario tests
- Accept-second (mutual accept) scenario tests  
- Decline flow tests
- Unauthorized access tests
- Edge cases and validation
"""

import pytest
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import uuid
from datetime import datetime, timezone

# Import the FastAPI app
from src.main import app

class TestMatchResponseEndpoint:
    """Test suite for POST /api/buddy/respond endpoint"""
    
    def setup_method(self):
        """Set up test data for each test"""
        self.client = TestClient(app)
        self.test_match_id = str(uuid.uuid4())
        self.user1_id = str(uuid.uuid4())
        self.user2_id = str(uuid.uuid4())
        self.unauthorized_user_id = str(uuid.uuid4())
        
    @patch('src.database.SupabaseFactory.get_service_client')
    @patch('src.email_templates.email_service')
    def test_accept_match_success(self, mock_email_service, mock_db_factory):
        """Test successful match acceptance"""
        # Mock database client
        mock_client = MagicMock()
        mock_db_factory.return_value = mock_client
        
        # Mock match validation - match exists and is pending
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{
                'user1_id': self.user1_id,
                'user2_id': self.user2_id,
                'status': 'pending'
            }]
        )
        
        # Mock successful update
        mock_client.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock()
        
        # Mock user profiles for email
        mock_client.table.return_value.select.return_value.eq.return_value.execute.side_effect = [
            MagicMock(data=[{'email': 'user1@test.com'}]),
            MagicMock(data=[{'email': 'user2@test.com'}])
        ]
        
        # Test request
        request_data = {
            "user_id": self.user1_id,
            "match_id": self.test_match_id,
            "action": "accept"
        }
        
        response = self.client.post("/api/buddy/respond", json=request_data)
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert data["match_status"] == "accepted"
        assert "Match accepted" in data["message"]
        assert data["next_match"] is None
        
    @patch('src.database.SupabaseFactory.get_service_client')
    @patch('src.services.wingman_matcher.WingmanMatcher')
    def test_decline_match_with_next_match(self, mock_matcher_class, mock_db_factory):
        """Test match decline with successful next match finding"""
        # Mock database client
        mock_client = MagicMock()
        mock_db_factory.return_value = mock_client
        
        # Mock match validation
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{
                'user1_id': self.user1_id,
                'user2_id': self.user2_id,
                'status': 'pending'
            }]
        )
        
        # Mock successful update
        mock_client.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock()
        
        # Mock WingmanMatcher
        mock_matcher = MagicMock()
        mock_matcher_class.return_value = mock_matcher
        
        # Mock next match result
        next_match_result = {
            "success": True,
            "match_id": str(uuid.uuid4()),
            "buddy_user_id": str(uuid.uuid4()),
            "buddy_profile": {"name": "New Buddy"}
        }
        mock_matcher.create_automatic_match.return_value = next_match_result
        
        # Test request
        request_data = {
            "user_id": self.user1_id,
            "match_id": self.test_match_id,
            "action": "decline"
        }
        
        response = self.client.post("/api/buddy/respond", json=request_data)
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert data["match_status"] == "declined"
        assert "next potential wingman buddy" in data["message"]
        assert data["next_match"] is not None
        assert data["next_match"]["match_id"] == next_match_result["match_id"]
        
    @patch('src.database.SupabaseFactory.get_service_client')
    def test_unauthorized_user_cannot_respond(self, mock_db_factory):
        """Test that unauthorized users cannot respond to matches"""
        # Mock database client
        mock_client = MagicMock()
        mock_db_factory.return_value = mock_client
        
        # Mock match validation - match exists but user is not participant
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{
                'user1_id': self.user1_id,
                'user2_id': self.user2_id,
                'status': 'pending'
            }]
        )
        
        # Test request with unauthorized user
        request_data = {
            "user_id": self.unauthorized_user_id,
            "match_id": self.test_match_id,
            "action": "accept"
        }
        
        response = self.client.post("/api/buddy/respond", json=request_data)
        
        # Assertions
        assert response.status_code == 403
        assert "Not authorized" in response.json()["detail"]
        
    @patch('src.database.SupabaseFactory.get_service_client')
    def test_match_not_found(self, mock_db_factory):
        """Test response when match doesn't exist"""
        # Mock database client
        mock_client = MagicMock()
        mock_db_factory.return_value = mock_client
        
        # Mock no match found
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[]
        )
        
        # Test request
        request_data = {
            "user_id": self.user1_id,
            "match_id": self.test_match_id,
            "action": "accept"
        }
        
        response = self.client.post("/api/buddy/respond", json=request_data)
        
        # Assertions
        assert response.status_code == 404
        assert "Match not found" in response.json()["detail"]
        
    @patch('src.database.SupabaseFactory.get_service_client')
    def test_match_already_responded(self, mock_db_factory):
        """Test response when match is already accepted/declined"""
        # Mock database client
        mock_client = MagicMock()
        mock_db_factory.return_value = mock_client
        
        # Mock match that's already accepted
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{
                'user1_id': self.user1_id,
                'user2_id': self.user2_id,
                'status': 'accepted'
            }]
        )
        
        # Test request
        request_data = {
            "user_id": self.user1_id,
            "match_id": self.test_match_id,
            "action": "accept"
        }
        
        response = self.client.post("/api/buddy/respond", json=request_data)
        
        # Assertions
        assert response.status_code == 400
        assert "already accepted" in response.json()["detail"]
        
    def test_invalid_action_validation(self):
        """Test Pydantic validation for invalid action"""
        request_data = {
            "user_id": self.user1_id,
            "match_id": self.test_match_id,
            "action": "invalid_action"
        }
        
        response = self.client.post("/api/buddy/respond", json=request_data)
        
        # Should fail validation
        assert response.status_code == 422
        
    def test_missing_required_fields(self):
        """Test validation for missing required fields"""
        request_data = {
            "user_id": self.user1_id,
            # Missing match_id and action
        }
        
        response = self.client.post("/api/buddy/respond", json=request_data)
        
        # Should fail validation
        assert response.status_code == 422
        
    @patch('src.database.SupabaseFactory.get_service_client')
    @patch('src.services.wingman_matcher.WingmanMatcher')
    def test_decline_with_no_next_match(self, mock_matcher_class, mock_db_factory):
        """Test decline when no next match is available"""
        # Mock database client
        mock_client = MagicMock()
        mock_db_factory.return_value = mock_client
        
        # Mock match validation
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{
                'user1_id': self.user1_id,
                'user2_id': self.user2_id,
                'status': 'pending'
            }]
        )
        
        # Mock successful update
        mock_client.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock()
        
        # Mock WingmanMatcher with no next match
        mock_matcher = MagicMock()
        mock_matcher_class.return_value = mock_matcher
        mock_matcher.create_automatic_match.return_value = {"success": False}
        
        # Test request
        request_data = {
            "user_id": self.user1_id,
            "match_id": self.test_match_id,
            "action": "decline"
        }
        
        response = self.client.post("/api/buddy/respond", json=request_data)
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert data["match_status"] == "declined"
        assert "Match declined." == data["message"]
        assert data["next_match"] is None

if __name__ == "__main__":
    pytest.main([__file__, "-v"])