#!/usr/bin/env python3
"""
Comprehensive Integration Tests for Auto-Match API Endpoint

Test Coverage:
- POST /api/matches/auto/{user_id} endpoint end-to-end
- Successful match creation in wingman_matches table
- Throttling behavior (multiple requests return same match)
- Recency rules (exclude recent pairs from selection)
- Integration with real sample users from existing database
- Error scenarios (invalid user IDs, database errors)
- Response format validation
- Performance under concurrent load
- Geographic filtering integration
- Experience level compatibility validation
"""

import pytest
import asyncio
import uuid
import json
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor

import httpx
from fastapi.testclient import TestClient

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from main import app
from database import SupabaseFactory
from services.wingman_matcher import WingmanMatcher

# Test configuration
TEST_CONFIG = {
    "base_url": "http://localhost:8000",
    "timeout": 30.0,
    "cleanup_after_tests": True
}

class TestAutoMatchEndpointSuccess:
    """Test successful auto-match endpoint scenarios"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    @pytest.fixture
    def db_client(self):
        """Create database client"""
        return SupabaseFactory.get_service_client()
    
    @pytest.fixture
    def test_user_ids(self):
        """Generate unique test user IDs"""
        return [str(uuid.uuid4()) for _ in range(5)]
    
    @pytest.fixture(autouse=True)
    async def setup_test_data(self, db_client, test_user_ids):
        """Setup test users with proper geographic distribution"""
        # San Francisco Bay Area coordinates for testing
        test_locations = [
            {"city": "San Francisco", "lat": 37.7749, "lng": -122.4194},
            {"city": "Oakland", "lat": 37.8044, "lng": -122.2711},
            {"city": "Berkeley", "lat": 37.8715, "lng": -122.2730},
            {"city": "San Jose", "lat": 37.3382, "lng": -121.8863},
            {"city": "Palo Alto", "lat": 37.4419, "lng": -122.1430}
        ]
        
        experience_levels = ["beginner", "intermediate", "advanced", "intermediate", "beginner"]
        archetypes = ["Naturalist", "Analyzer", "Sprinter", "Scholar", "Protector"]
        
        # Create test user profiles
        for i, user_id in enumerate(test_user_ids):
            try:
                # Create user profile
                profile_data = {
                    "id": user_id,
                    "email": f"test-user-{i}@wingmanmatch.test",
                    "first_name": f"TestUser{i}",
                    "last_name": "AutoMatch",
                    "bio": f"Test user {i} for auto-match testing. Ready to practice social skills!",
                    "experience_level": experience_levels[i],
                    "confidence_archetype": archetypes[i],
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
                
                db_client.table('user_profiles').upsert(profile_data, on_conflict="id").execute()
                
                # Create user location
                location_data = {
                    "user_id": user_id,
                    "lat": test_locations[i]["lat"],
                    "lng": test_locations[i]["lng"],
                    "city": test_locations[i]["city"],
                    "privacy_mode": "precise",
                    "max_travel_miles": 30,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
                
                db_client.table('user_locations').upsert(location_data, on_conflict="user_id").execute()
                
            except Exception as e:
                print(f"Setup error for user {user_id}: {e}")
        
        yield
        
        # Cleanup test data
        if TEST_CONFIG["cleanup_after_tests"]:
            try:
                # Clean up wingman_matches
                for user_id in test_user_ids:
                    db_client.table('wingman_matches')\
                        .delete()\
                        .or_(f'user1_id.eq.{user_id},user2_id.eq.{user_id}')\
                        .execute()
                
                # Clean up locations and profiles
                for user_id in test_user_ids:
                    db_client.table('user_locations').delete().eq('user_id', user_id).execute()
                    db_client.table('user_profiles').delete().eq('id', user_id).execute()
                    
            except Exception as e:
                print(f"Cleanup error: {e}")
    
    def test_successful_match_creation(self, client, test_user_ids):
        """Test successful match creation between compatible users"""
        user_id = test_user_ids[0]  # San Francisco user
        
        response = client.post(f"/api/matches/auto/{user_id}?radius_miles=25")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["message"] == "Wingman buddy match created successfully!"
        assert data["match_id"] is not None
        assert data["buddy_user_id"] is not None
        assert data["buddy_profile"] is not None
        
        # Verify buddy profile structure
        buddy_profile = data["buddy_profile"]
        assert "id" in buddy_profile
        assert "first_name" in buddy_profile
        assert "experience_level" in buddy_profile
        assert "confidence_archetype" in buddy_profile
        
        # Verify buddy is not the same user
        assert data["buddy_user_id"] != user_id
    
    def test_match_creation_with_specific_radius(self, client, test_user_ids):
        """Test match creation with specific radius constraints"""
        user_id = test_user_ids[0]  # San Francisco user
        
        # Test with small radius (should find Oakland user ~10 miles away)
        response = client.post(f"/api/matches/auto/{user_id}?radius_miles=15")
        
        assert response.status_code == 200
        data = response.json()
        
        if data["success"]:
            # Verify match was found within radius
            assert data["buddy_user_id"] is not None
            # Would be user in Oakland (test_user_ids[1])
        else:
            # Acceptable if no compatible users within small radius
            assert "No compatible wingman buddies found" in data["message"]
    
    def test_match_with_experience_compatibility(self, client, test_user_ids):
        """Test that matches respect experience level compatibility"""
        user_id = test_user_ids[0]  # Beginner level user
        
        response = client.post(f"/api/matches/auto/{user_id}?radius_miles=30")
        
        assert response.status_code == 200
        data = response.json()
        
        if data["success"]:
            # Verify matched user has compatible experience level
            buddy_level = data["buddy_profile"]["experience_level"]
            # Beginner should match with beginner or intermediate only
            assert buddy_level in ["beginner", "intermediate"]
    
    def test_database_match_record_creation(self, client, db_client, test_user_ids):
        """Test that match record is properly created in database"""
        user_id = test_user_ids[0]
        
        # Get initial match count
        initial_matches = db_client.table('wingman_matches')\
            .select('*')\
            .or_(f'user1_id.eq.{user_id},user2_id.eq.{user_id}')\
            .execute()
        initial_count = len(initial_matches.data)
        
        response = client.post(f"/api/matches/auto/{user_id}?radius_miles=25")
        
        assert response.status_code == 200
        data = response.json()
        
        if data["success"]:
            # Verify match record was created
            final_matches = db_client.table('wingman_matches')\
                .select('*')\
                .or_(f'user1_id.eq.{user_id},user2_id.eq.{user_id}')\
                .execute()
            final_count = len(final_matches.data)
            
            assert final_count == initial_count + 1
            
            # Verify match record structure
            new_match = final_matches.data[-1]  # Most recent match
            assert new_match["status"] == "pending"
            assert new_match["user1_reputation"] == 0
            assert new_match["user2_reputation"] == 0
            assert new_match["created_at"] is not None
            
            # Verify user ordering (alphabetically)
            if user_id < data["buddy_user_id"]:
                assert new_match["user1_id"] == user_id
                assert new_match["user2_id"] == data["buddy_user_id"]
            else:
                assert new_match["user1_id"] == data["buddy_user_id"]
                assert new_match["user2_id"] == user_id

class TestAutoMatchThrottling:
    """Test throttling behavior (one pending match per user)"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    @pytest.fixture
    def db_client(self):
        return SupabaseFactory.get_service_client()
    
    def test_throttling_returns_existing_match(self, client, db_client):
        """Test that multiple requests return same existing match"""
        # Create test users
        user1_id = str(uuid.uuid4())
        user2_id = str(uuid.uuid4())
        
        # Setup test users with profiles and locations
        for i, user_id in enumerate([user1_id, user2_id]):
            profile_data = {
                "id": user_id,
                "email": f"throttle-test-{i}@wingmanmatch.test",
                "first_name": f"ThrottleUser{i}",
                "last_name": "Test",
                "bio": "Test user for throttling tests",
                "experience_level": "intermediate",
                "confidence_archetype": "Analyzer",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            db_client.table('user_profiles').upsert(profile_data, on_conflict="id").execute()
            
            location_data = {
                "user_id": user_id,
                "lat": 37.7749 + i * 0.01,  # Slightly different locations
                "lng": -122.4194,
                "city": "San Francisco",
                "privacy_mode": "precise",
                "max_travel_miles": 25,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            db_client.table('user_locations').upsert(location_data, on_conflict="user_id").execute()
        
        try:
            # First request should create match
            response1 = client.post(f"/api/matches/auto/{user1_id}?radius_miles=25")
            assert response1.status_code == 200
            data1 = response1.json()
            
            # Second request should return existing match
            response2 = client.post(f"/api/matches/auto/{user1_id}?radius_miles=25")
            assert response2.status_code == 200
            data2 = response2.json()
            
            if data1["success"]:
                assert data2["success"] is True
                assert data2["message"] == "You already have a pending wingman match"
                assert data2["match_id"] == data1["match_id"]
                assert data2["buddy_user_id"] == data1["buddy_user_id"]
            
        finally:
            # Cleanup
            for user_id in [user1_id, user2_id]:
                db_client.table('wingman_matches')\
                    .delete()\
                    .or_(f'user1_id.eq.{user_id},user2_id.eq.{user_id}')\
                    .execute()
                db_client.table('user_locations').delete().eq('user_id', user_id).execute()
                db_client.table('user_profiles').delete().eq('id', user_id).execute()
    
    def test_different_users_can_create_matches(self, client, db_client):
        """Test that different users can create their own matches"""
        # Create test users
        test_users = [str(uuid.uuid4()) for _ in range(4)]
        
        # Setup all test users
        for i, user_id in enumerate(test_users):
            profile_data = {
                "id": user_id,
                "email": f"multi-user-{i}@wingmanmatch.test",
                "first_name": f"MultiUser{i}",
                "last_name": "Test",
                "bio": "Test user for multi-user matching",
                "experience_level": "intermediate",
                "confidence_archetype": "Analyzer",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            db_client.table('user_profiles').upsert(profile_data, on_conflict="id").execute()
            
            location_data = {
                "user_id": user_id,
                "lat": 37.7749 + i * 0.01,
                "lng": -122.4194,
                "city": "San Francisco",
                "privacy_mode": "precise",
                "max_travel_miles": 25,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            db_client.table('user_locations').upsert(location_data, on_conflict="user_id").execute()
        
        try:
            # Each user should be able to create a match
            successful_matches = 0
            
            for user_id in test_users:
                response = client.post(f"/api/matches/auto/{user_id}?radius_miles=25")
                assert response.status_code == 200
                data = response.json()
                
                if data["success"] and "Wingman buddy match created successfully" in data["message"]:
                    successful_matches += 1
            
            # At least 2 users should be able to create matches (paired together)
            assert successful_matches >= 2
            
        finally:
            # Cleanup
            for user_id in test_users:
                db_client.table('wingman_matches')\
                    .delete()\
                    .or_(f'user1_id.eq.{user_id},user2_id.eq.{user_id}')\
                    .execute()
                db_client.table('user_locations').delete().eq('user_id', user_id).execute()
                db_client.table('user_profiles').delete().eq('id', user_id).execute()

class TestAutoMatchRecencyRules:
    """Test recency rules (exclude recent pairs from selection)"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    @pytest.fixture
    def db_client(self):
        return SupabaseFactory.get_service_client()
    
    def test_recent_pairs_excluded_from_new_matches(self, client, db_client):
        """Test that users paired within last 7 days are excluded"""
        # Create test users
        user1_id = str(uuid.uuid4())
        user2_id = str(uuid.uuid4())
        user3_id = str(uuid.uuid4())
        
        # Setup test users
        for i, user_id in enumerate([user1_id, user2_id, user3_id]):
            profile_data = {
                "id": user_id,
                "email": f"recency-test-{i}@wingmanmatch.test",
                "first_name": f"RecencyUser{i}",
                "last_name": "Test",
                "bio": "Test user for recency rules",
                "experience_level": "intermediate",
                "confidence_archetype": "Analyzer",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            db_client.table('user_profiles').upsert(profile_data, on_conflict="id").execute()
            
            location_data = {
                "user_id": user_id,
                "lat": 37.7749 + i * 0.01,
                "lng": -122.4194,
                "city": "San Francisco",
                "privacy_mode": "precise",
                "max_travel_miles": 25,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            db_client.table('user_locations').upsert(location_data, on_conflict="user_id").execute()
        
        try:
            # Create a recent match between user1 and user2
            recent_match_data = {
                "user1_id": min(user1_id, user2_id),  # Alphabetical ordering
                "user2_id": max(user1_id, user2_id),
                "status": "completed",  # Recent completed match
                "user1_reputation": 5,
                "user2_reputation": 5,
                "created_at": (datetime.now(timezone.utc) - timedelta(days=3)).isoformat()  # 3 days ago
            }
            db_client.table('wingman_matches').insert(recent_match_data).execute()
            
            # Now user1 tries to find a new match
            response = client.post(f"/api/matches/auto/{user1_id}?radius_miles=25")
            assert response.status_code == 200
            data = response.json()
            
            if data["success"]:
                # Should not be matched with user2 (recent pair)
                assert data["buddy_user_id"] != user2_id
                # Should potentially be matched with user3
                if data["buddy_user_id"]:
                    assert data["buddy_user_id"] == user3_id
            
        finally:
            # Cleanup
            for user_id in [user1_id, user2_id, user3_id]:
                db_client.table('wingman_matches')\
                    .delete()\
                    .or_(f'user1_id.eq.{user_id},user2_id.eq.{user_id}')\
                    .execute()
                db_client.table('user_locations').delete().eq('user_id', user_id).execute()
                db_client.table('user_profiles').delete().eq('id', user_id).execute()
    
    def test_old_pairs_allowed_for_new_matches(self, client, db_client):
        """Test that users paired >7 days ago can be matched again"""
        # Create test users
        user1_id = str(uuid.uuid4())
        user2_id = str(uuid.uuid4())
        
        # Setup test users
        for i, user_id in enumerate([user1_id, user2_id]):
            profile_data = {
                "id": user_id,
                "email": f"old-match-{i}@wingmanmatch.test",
                "first_name": f"OldMatchUser{i}",
                "last_name": "Test",
                "bio": "Test user for old match repairing",
                "experience_level": "intermediate",
                "confidence_archetype": "Analyzer",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            db_client.table('user_profiles').upsert(profile_data, on_conflict="id").execute()
            
            location_data = {
                "user_id": user_id,
                "lat": 37.7749 + i * 0.01,
                "lng": -122.4194,
                "city": "San Francisco",
                "privacy_mode": "precise",
                "max_travel_miles": 25,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            db_client.table('user_locations').upsert(location_data, on_conflict="user_id").execute()
        
        try:
            # Create an old match (>7 days ago)
            old_match_data = {
                "user1_id": min(user1_id, user2_id),
                "user2_id": max(user1_id, user2_id),
                "status": "completed",
                "user1_reputation": 5,
                "user2_reputation": 5,
                "created_at": (datetime.now(timezone.utc) - timedelta(days=10)).isoformat()  # 10 days ago
            }
            db_client.table('wingman_matches').insert(old_match_data).execute()
            
            # User1 tries to find a new match
            response = client.post(f"/api/matches/auto/{user1_id}?radius_miles=25")
            assert response.status_code == 200
            data = response.json()
            
            # Should be allowed to match with user2 again (old pairing)
            if data["success"]:
                assert data["buddy_user_id"] == user2_id
            
        finally:
            # Cleanup
            for user_id in [user1_id, user2_id]:
                db_client.table('wingman_matches')\
                    .delete()\
                    .or_(f'user1_id.eq.{user_id},user2_id.eq.{user_id}')\
                    .execute()
                db_client.table('user_locations').delete().eq('user_id', user_id).execute()
                db_client.table('user_profiles').delete().eq('id', user_id).execute()

class TestAutoMatchErrorScenarios:
    """Test error scenarios and edge cases"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_invalid_user_id_format(self, client):
        """Test API response for invalid user ID format"""
        invalid_user_id = "not-a-valid-uuid"
        
        response = client.post(f"/api/matches/auto/{invalid_user_id}?radius_miles=25")
        
        # Should handle gracefully (may return 400, 404, or 200 with error message)
        assert response.status_code in [200, 400, 404, 422]
        
        if response.status_code == 200:
            data = response.json()
            assert data["success"] is False
    
    def test_nonexistent_user_id(self, client):
        """Test API response for nonexistent user ID"""
        nonexistent_user_id = str(uuid.uuid4())
        
        response = client.post(f"/api/matches/auto/{nonexistent_user_id}?radius_miles=25")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should handle gracefully with auto-dependency creation
        # May succeed (creating profile) or fail (no candidates)
        assert isinstance(data["success"], bool)
        if not data["success"]:
            assert "No compatible wingman buddies found" in data["message"]
    
    def test_invalid_radius_parameter(self, client):
        """Test API response for invalid radius parameters"""
        user_id = str(uuid.uuid4())
        
        # Test negative radius
        response = client.post(f"/api/matches/auto/{user_id}?radius_miles=-5")
        assert response.status_code == 400
        error_data = response.json()
        assert "Radius must be between 1 and 100 miles" in error_data["detail"]
        
        # Test zero radius
        response = client.post(f"/api/matches/auto/{user_id}?radius_miles=0")
        assert response.status_code == 400
        
        # Test excessive radius
        response = client.post(f"/api/matches/auto/{user_id}?radius_miles=101")
        assert response.status_code == 400
    
    def test_no_candidates_within_radius(self, client, db_client):
        """Test response when no candidates exist within radius"""
        # Create isolated user in remote location
        isolated_user_id = str(uuid.uuid4())
        
        profile_data = {
            "id": isolated_user_id,
            "email": "isolated@wingmanmatch.test",
            "first_name": "Isolated",
            "last_name": "User",
            "bio": "Isolated user for no-candidates test",
            "experience_level": "intermediate",
            "confidence_archetype": "Analyzer",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        db_client.table('user_profiles').upsert(profile_data, on_conflict="id").execute()
        
        # Remote location (middle of Nevada)
        location_data = {
            "user_id": isolated_user_id,
            "lat": 39.1638,
            "lng": -119.7674,
            "city": "Remote Location",
            "privacy_mode": "precise",
            "max_travel_miles": 25,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        db_client.table('user_locations').upsert(location_data, on_conflict="user_id").execute()
        
        try:
            response = client.post(f"/api/matches/auto/{isolated_user_id}?radius_miles=10")
            assert response.status_code == 200
            data = response.json()
            
            assert data["success"] is False
            assert "No compatible wingman buddies found" in data["message"]
            assert data["match_id"] is None
            assert data["buddy_user_id"] is None
            
        finally:
            # Cleanup
            db_client.table('user_locations').delete().eq('user_id', isolated_user_id).execute()
            db_client.table('user_profiles').delete().eq('id', isolated_user_id).execute()

class TestAutoMatchResponseFormat:
    """Test response format validation"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_success_response_format(self, client):
        """Test successful response format matches AutoMatchResponse model"""
        user_id = str(uuid.uuid4())
        
        response = client.post(f"/api/matches/auto/{user_id}?radius_miles=25")
        assert response.status_code == 200
        
        data = response.json()
        
        # Verify required fields exist
        required_fields = ["success", "message", "match_id", "buddy_user_id", "buddy_profile"]
        for field in required_fields:
            assert field in data
        
        # Verify field types
        assert isinstance(data["success"], bool)
        assert isinstance(data["message"], str)
        
        # Optional fields should be None or proper type
        if data["match_id"] is not None:
            assert isinstance(data["match_id"], str)
        
        if data["buddy_user_id"] is not None:
            assert isinstance(data["buddy_user_id"], str)
        
        if data["buddy_profile"] is not None:
            assert isinstance(data["buddy_profile"], dict)
            # Verify buddy profile structure
            profile_fields = ["id", "first_name", "experience_level", "confidence_archetype"]
            for field in profile_fields:
                assert field in data["buddy_profile"]
    
    def test_error_response_format(self, client):
        """Test error response format is consistent"""
        user_id = str(uuid.uuid4())
        
        # Trigger error with invalid radius
        response = client.post(f"/api/matches/auto/{user_id}?radius_miles=-1")
        assert response.status_code == 400
        
        # Should have error detail
        error_data = response.json()
        assert "detail" in error_data

class TestAutoMatchPerformance:
    """Test performance and concurrent access"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_response_time_performance(self, client):
        """Test API response time is reasonable"""
        user_id = str(uuid.uuid4())
        
        start_time = time.time()
        response = client.post(f"/api/matches/auto/{user_id}?radius_miles=25")
        end_time = time.time()
        
        response_time = end_time - start_time
        
        assert response.status_code == 200
        assert response_time < 5.0  # Should complete within 5 seconds
    
    def test_concurrent_requests_different_users(self, client):
        """Test concurrent requests from different users"""
        test_user_ids = [str(uuid.uuid4()) for _ in range(3)]
        
        def make_request(user_id):
            start_time = time.time()
            response = client.post(f"/api/matches/auto/{user_id}?radius_miles=25")
            end_time = time.time()
            return {
                "user_id": user_id,
                "status_code": response.status_code,
                "response_time": end_time - start_time,
                "data": response.json() if response.status_code == 200 else None
            }
        
        # Execute concurrent requests
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(make_request, user_id) for user_id in test_user_ids]
            results = [future.result() for future in futures]
        
        # Verify all requests completed successfully
        for result in results:
            assert result["status_code"] == 200
            assert result["response_time"] < 10.0  # Reasonable timeout
        
        # Check that responses are valid
        successful_matches = [r for r in results if r["data"] and r["data"]["success"]]
        # At least some matches should be possible (depending on test data availability)
        
    def test_concurrent_requests_same_user(self, client):
        """Test concurrent requests from same user (throttling test)"""
        user_id = str(uuid.uuid4())
        
        def make_request():
            response = client.post(f"/api/matches/auto/{user_id}?radius_miles=25")
            return response.json() if response.status_code == 200 else None
        
        # Execute 3 concurrent requests for same user
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(make_request) for _ in range(3)]
            results = [future.result() for future in futures if future.result()]
        
        # All should return similar results due to throttling
        if len(results) >= 2:
            # Check consistency in responses
            success_count = sum(1 for r in results if r and r["success"])
            # Either all succeed with same match, or all fail consistently
            if success_count > 0:
                match_ids = [r["match_id"] for r in results if r and r["success"] and r["match_id"]]
                if len(match_ids) > 1:
                    # All successful matches should have same ID (throttling)
                    assert all(mid == match_ids[0] for mid in match_ids)

if __name__ == "__main__":
    # Run tests with pytest
    import pytest
    pytest.main([__file__, "-v", "--tb=short", "-s"])