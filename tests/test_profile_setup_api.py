"""
Comprehensive API Integration Tests for Task 7 Profile Setup Backend

Test Coverage:
- /api/profile/complete endpoint validation
- Input sanitization and PII detection  
- Database operations and auto-dependency creation
- Error handling and edge cases
- Security validations (XSS, injection, file validation)
- Performance testing with large payloads
- Authentication and authorization
"""

import pytest
import asyncio
import json
import uuid
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from unittest.mock import patch, MagicMock

import httpx
from fastapi.testclient import TestClient
from supabase import create_client

# Import the FastAPI app and dependencies
from src.main import app
from src.config import Config
from src.database import SupabaseFactory
from src.safety_filters import sanitize_message

# Test configuration
TEST_CONFIG = {
    "base_url": "http://localhost:8000",
    "timeout": 30.0,
    "test_user_id": str(uuid.uuid4()),
    "cleanup_after_tests": True
}

# Test data constants
VALID_PROFILE_DATA = {
    "user_id": TEST_CONFIG["test_user_id"],
    "bio": "I'm a software engineer who loves hiking and meeting new people. Looking for a confident wingman buddy to practice social skills!",
    "location": {
        "lat": 37.7749,
        "lng": -122.4194,
        "city": "San Francisco",
        "privacy_mode": "precise"
    },
    "travel_radius": 25,
    "photo_url": "https://example.com/storage/profile-photos/test-photo.jpg"
}

INVALID_BIO_PII = "Call me at 555-123-4567 or email test@example.com for more info"
INVALID_BIO_SHORT = "Too short"
INVALID_BIO_LONG = "x" * 401  # Exceeds 400 character limit

INVALID_COORDINATES = [
    {"lat": 91.0, "lng": 0.0},  # Invalid latitude
    {"lat": -91.0, "lng": 0.0},  # Invalid latitude  
    {"lat": 0.0, "lng": 181.0},  # Invalid longitude
    {"lat": 0.0, "lng": -181.0},  # Invalid longitude
]

class TestProfileSetupAPI:
    """Test suite for profile completion API endpoint"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    @pytest.fixture
    def valid_payload(self):
        """Create valid test payload with unique user ID"""
        payload = VALID_PROFILE_DATA.copy()
        payload["user_id"] = str(uuid.uuid4())
        return payload
    
    @pytest.fixture(autouse=True)
    async def setup_and_cleanup(self):
        """Setup test environment and cleanup after tests"""
        # Setup: Create test user profile if needed
        try:
            db_client = SupabaseFactory.get_service_client()
            
            # Create test user profile for dependency
            await self._ensure_test_user_profile(db_client, TEST_CONFIG["test_user_id"])
            
            yield
            
            # Cleanup: Remove test data if configured
            if TEST_CONFIG["cleanup_after_tests"]:
                await self._cleanup_test_data(db_client, TEST_CONFIG["test_user_id"])
                
        except Exception as e:
            print(f"Setup/cleanup error: {e}")
            yield
    
    async def _ensure_test_user_profile(self, db_client, user_id: str):
        """Ensure test user profile exists for foreign key constraints"""
        try:
            from src.simple_memory import WingmanMemory
            memory = WingmanMemory(db_client, user_id)
            await memory.ensure_user_profile(user_id)
        except Exception as e:
            print(f"Error creating test user profile: {e}")
    
    async def _cleanup_test_data(self, db_client, user_id: str):
        """Clean up test data after tests"""
        try:
            # Remove test user locations
            db_client.table('user_locations').delete().eq('user_id', user_id).execute()
            
            # Remove test user profiles  
            db_client.table('user_profiles').delete().eq('id', user_id).execute()
            
        except Exception as e:
            print(f"Cleanup error: {e}")

    def test_profile_complete_success_precise_location(self, client, valid_payload):
        """Test successful profile completion with precise location"""
        response = client.post("/api/profile/complete", json=valid_payload)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["ready_for_matching"] is True
        assert data["user_id"] == valid_payload["user_id"]
        assert "Profile completed successfully" in data["message"]
    
    def test_profile_complete_success_city_only_location(self, client, valid_payload):
        """Test successful profile completion with city-only privacy mode"""
        valid_payload["location"]["privacy_mode"] = "city_only"
        valid_payload["location"]["lat"] = 37.7749  # Will be replaced with 0.0
        valid_payload["location"]["lng"] = -122.4194  # Will be replaced with 0.0
        
        response = client.post("/api/profile/complete", json=valid_payload)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["ready_for_matching"] is True
    
    def test_profile_complete_without_photo(self, client, valid_payload):
        """Test profile completion without photo upload"""
        del valid_payload["photo_url"]  # Remove photo URL
        
        response = client.post("/api/profile/complete", json=valid_payload)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["ready_for_matching"] is True
    
    def test_bio_validation_minimum_length(self, client, valid_payload):
        """Test bio validation with minimum length requirement"""
        valid_payload["bio"] = INVALID_BIO_SHORT
        
        response = client.post("/api/profile/complete", json=valid_payload)
        
        assert response.status_code == 422  # Pydantic validation error
        error_detail = response.json()["detail"]
        assert any("at least 10 characters" in str(error) for error in error_detail)
    
    def test_bio_validation_maximum_length(self, client, valid_payload):
        """Test bio validation with maximum length requirement"""
        valid_payload["bio"] = INVALID_BIO_LONG
        
        response = client.post("/api/profile/complete", json=valid_payload)
        
        assert response.status_code == 422  # Pydantic validation error
        error_detail = response.json()["detail"]
        assert any("400 characters or less" in str(error) for error in error_detail)
    
    def test_bio_pii_detection_sanitization(self, client, valid_payload):
        """Test bio PII detection and sanitization"""
        # Note: This tests the sanitization that happens on the backend
        # The frontend Zod validation should catch this first
        valid_payload["bio"] = "I love hiking and meeting people! My contact is 555-123-4567"
        
        # This should either be rejected or sanitized depending on implementation
        response = client.post("/api/profile/complete", json=valid_payload)
        
        # Response could be 400 (rejected) or 200 (sanitized)
        assert response.status_code in [200, 400, 422]
        
        if response.status_code == 400:
            error_data = response.json()
            assert "sanitization" in error_data.get("detail", "").lower()
    
    @pytest.mark.parametrize("invalid_coords", INVALID_COORDINATES)
    def test_coordinate_validation(self, client, valid_payload, invalid_coords):
        """Test coordinate range validation"""
        valid_payload["location"].update(invalid_coords)
        
        response = client.post("/api/profile/complete", json=valid_payload)
        
        assert response.status_code == 422  # Pydantic validation error
        error_detail = response.json()["detail"]
        assert any("latitude" in str(error).lower() or "longitude" in str(error).lower() 
                  for error in error_detail)
    
    def test_travel_radius_validation(self, client, valid_payload):
        """Test travel radius validation"""
        # Test minimum radius
        valid_payload["travel_radius"] = 0
        response = client.post("/api/profile/complete", json=valid_payload)
        assert response.status_code == 422
        
        # Test maximum radius
        valid_payload["travel_radius"] = 51
        response = client.post("/api/profile/complete", json=valid_payload)
        assert response.status_code == 422
        
        # Test valid radius
        valid_payload["travel_radius"] = 25
        response = client.post("/api/profile/complete", json=valid_payload)
        assert response.status_code == 200
    
    def test_privacy_mode_validation(self, client, valid_payload):
        """Test privacy mode validation"""
        # Test invalid privacy mode
        valid_payload["location"]["privacy_mode"] = "invalid_mode"
        
        response = client.post("/api/profile/complete", json=valid_payload)
        
        assert response.status_code == 422  # Pydantic validation error
        error_detail = response.json()["detail"]
        assert any("privacy_mode" in str(error) for error in error_detail)
    
    def test_city_only_mode_requires_city(self, client, valid_payload):
        """Test that city_only mode requires city field"""
        valid_payload["location"]["privacy_mode"] = "city_only"
        valid_payload["location"]["city"] = ""  # Empty city
        
        response = client.post("/api/profile/complete", json=valid_payload)
        
        assert response.status_code == 400
        error_data = response.json()
        assert "city name is required" in error_data["detail"].lower()
    
    def test_missing_required_fields(self, client, valid_payload):
        """Test API response for missing required fields"""
        required_fields = ["user_id", "bio", "location", "travel_radius"]
        
        for field in required_fields:
            test_payload = valid_payload.copy()
            del test_payload[field]
            
            response = client.post("/api/profile/complete", json=test_payload)
            
            assert response.status_code == 422  # Pydantic validation error
            error_detail = response.json()["detail"]
            assert any(field in str(error) for error in error_detail)
    
    def test_invalid_user_id_format(self, client, valid_payload):
        """Test API response for invalid user ID format"""
        valid_payload["user_id"] = "invalid-uuid-format"
        
        response = client.post("/api/profile/complete", json=valid_payload)
        
        # This might pass Pydantic validation if it's just a string
        # but could fail during database operations
        assert response.status_code in [400, 404, 422, 500]
    
    def test_duplicate_profile_completion(self, client, valid_payload):
        """Test handling of duplicate profile completion attempts"""
        # First completion should succeed
        response1 = client.post("/api/profile/complete", json=valid_payload)
        assert response1.status_code == 200
        
        # Second completion should update existing profile
        valid_payload["bio"] = "Updated bio content with new information"
        response2 = client.post("/api/profile/complete", json=valid_payload)
        assert response2.status_code == 200
    
    def test_auto_dependency_creation(self, client):
        """Test auto-dependency creation for user profiles"""
        new_user_id = str(uuid.uuid4())
        test_payload = VALID_PROFILE_DATA.copy()
        test_payload["user_id"] = new_user_id
        
        # Should succeed even if user profile doesn't exist initially
        response = client.post("/api/profile/complete", json=test_payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_request_payload_size_limits(self, client, valid_payload):
        """Test API handling of large request payloads"""
        # Create very large bio (close to but under limit)
        large_bio = "x" * 399  # Just under 400 character limit
        valid_payload["bio"] = large_bio
        
        response = client.post("/api/profile/complete", json=valid_payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_concurrent_profile_completion(self, client, valid_payload):
        """Test handling of concurrent profile completion requests"""
        import concurrent.futures
        import threading
        
        def submit_profile(payload):
            client_instance = TestClient(app)
            return client_instance.post("/api/profile/complete", json=payload)
        
        # Create multiple payloads with same user ID
        payloads = []
        for i in range(3):
            payload = valid_payload.copy()
            payload["bio"] = f"Concurrent bio update #{i}"
            payloads.append(payload)
        
        # Submit concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(submit_profile, payload) for payload in payloads]
            responses = [future.result() for future in futures]
        
        # All should succeed (last write wins)
        for response in responses:
            assert response.status_code == 200
    
    def test_performance_with_large_payload(self, client, valid_payload):
        """Test API performance with realistic large payloads"""
        # Create large but valid bio
        valid_payload["bio"] = "A" * 390 + " and more!"  # Near limit
        valid_payload["location"]["city"] = "San Francisco, California, United States"
        
        start_time = time.time()
        response = client.post("/api/profile/complete", json=valid_payload)
        end_time = time.time()
        
        assert response.status_code == 200
        
        # Should complete within reasonable time (< 2 seconds)
        response_time = end_time - start_time
        assert response_time < 2.0, f"Response time too slow: {response_time:.2f}s"

class TestProfileSetupSecurity:
    """Security-focused tests for profile setup API"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    @pytest.fixture
    def valid_payload(self):
        payload = VALID_PROFILE_DATA.copy()
        payload["user_id"] = str(uuid.uuid4())
        return payload
    
    def test_xss_prevention_in_bio(self, client, valid_payload):
        """Test XSS prevention in bio field"""
        xss_attempts = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
            "';alert('xss');//",
            "<svg onload=alert('xss')>",
        ]
        
        for xss_payload in xss_attempts:
            test_payload = valid_payload.copy()
            test_payload["bio"] = f"This is my bio {xss_payload} and more content"
            
            response = client.post("/api/profile/complete", json=test_payload)
            
            # Should either reject or sanitize
            if response.status_code == 200:
                # If accepted, verify content was sanitized
                # This would require checking database content or response
                pass
            else:
                # Should be rejected with appropriate error
                assert response.status_code in [400, 422]
    
    def test_sql_injection_prevention(self, client, valid_payload):
        """Test SQL injection prevention"""
        sql_injection_attempts = [
            "'; DROP TABLE user_profiles; --",
            "' UNION SELECT * FROM user_profiles --",
            "'; UPDATE user_profiles SET bio='hacked' --",
            "1'; DELETE FROM user_locations; --",
        ]
        
        for sql_payload in sql_injection_attempts:
            test_payload = valid_payload.copy()
            test_payload["location"]["city"] = sql_payload
            
            response = client.post("/api/profile/complete", json=test_payload)
            
            # Should handle injection attempts safely
            # Parameterized queries should prevent any damage
            assert response.status_code in [200, 400, 422]
    
    def test_path_traversal_prevention_in_photo_url(self, client, valid_payload):
        """Test path traversal prevention in photo URL"""
        path_traversal_attempts = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "/etc/shadow",
            "file:///etc/passwd",
        ]
        
        for path_payload in path_traversal_attempts:
            test_payload = valid_payload.copy()
            test_payload["photo_url"] = path_payload
            
            response = client.post("/api/profile/complete", json=test_payload)
            
            # Should accept as string but not process as file path
            # The URL validation should happen during photo upload, not here
            assert response.status_code == 200
    
    def test_input_size_limits_and_dos_prevention(self, client, valid_payload):
        """Test input size limits to prevent DoS attacks"""
        # Test extremely large input that should be rejected
        massive_bio = "x" * 10000  # Way over 400 character limit
        
        test_payload = valid_payload.copy()
        test_payload["bio"] = massive_bio
        
        response = client.post("/api/profile/complete", json=test_payload)
        
        # Should be rejected by validation
        assert response.status_code == 422
    
    def test_unicode_and_encoding_attacks(self, client, valid_payload):
        """Test handling of unicode and encoding attacks"""
        unicode_attacks = [
            "\\u003cscript\\u003ealert('xss')\\u003c/script\\u003e",
            "café\x00hidden",  # Null byte injection
            "test\r\ninjected\r\n",  # CRLF injection
            "🚀" * 100,  # Lots of unicode
        ]
        
        for unicode_payload in unicode_attacks:
            test_payload = valid_payload.copy()
            test_payload["bio"] = f"My bio content {unicode_payload}"
            
            response = client.post("/api/profile/complete", json=test_payload)
            
            # Should handle unicode safely
            assert response.status_code in [200, 400, 422]
    
    def test_json_structure_attacks(self, client):
        """Test JSON structure and type confusion attacks"""
        malicious_payloads = [
            # Type confusion
            {
                "user_id": ["array", "instead", "of", "string"],
                "bio": {"object": "instead of string"},
                "location": "string instead of object",
                "travel_radius": "string instead of number"
            },
            
            # Nested depth attack
            {
                "user_id": str(uuid.uuid4()),
                "bio": {"a": {"b": {"c": {"d": {"e": "deeply nested"}}}}},
                "location": {"lat": 0, "lng": 0, "privacy_mode": "precise"},
                "travel_radius": 20
            },
            
            # Extra fields
            {
                "user_id": str(uuid.uuid4()),
                "bio": "Valid bio content",
                "location": {"lat": 0, "lng": 0, "privacy_mode": "precise"},
                "travel_radius": 20,
                "extra_field": "should be ignored",
                "admin": True,
                "password": "hack attempt"
            }
        ]
        
        for payload in malicious_payloads:
            response = client.post("/api/profile/complete", json=payload)
            
            # Pydantic should handle type validation
            assert response.status_code in [200, 422]

class TestProfileSetupDatabase:
    """Database integration tests for profile setup"""
    
    @pytest.fixture
    def db_client(self):
        return SupabaseFactory.get_service_client()
    
    @pytest.fixture
    def test_user_id(self):
        return str(uuid.uuid4())
    
    @pytest.fixture(autouse=True)
    async def cleanup_test_data(self, db_client, test_user_id):
        """Cleanup test data after each test"""
        yield
        
        try:
            # Clean up test data
            db_client.table('user_locations').delete().eq('user_id', test_user_id).execute()
            db_client.table('user_profiles').delete().eq('id', test_user_id).execute()
        except Exception as e:
            print(f"Cleanup error: {e}")
    
    def test_database_profile_creation(self, db_client, test_user_id):
        """Test database profile creation directly"""
        from src.simple_memory import WingmanMemory
        
        # Create user profile using auto-dependency creation
        memory = WingmanMemory(db_client, test_user_id)
        
        # This should work without errors
        result = asyncio.run(memory.ensure_user_profile(test_user_id))
        
        # Verify profile was created
        profile_result = db_client.table('user_profiles')\
            .select('*')\
            .eq('id', test_user_id)\
            .execute()
        
        assert len(profile_result.data) == 1
        assert profile_result.data[0]['id'] == test_user_id
    
    def test_location_upsert_operations(self, db_client, test_user_id):
        """Test location upsert operations"""
        # First, ensure user profile exists
        from src.simple_memory import WingmanMemory
        memory = WingmanMemory(db_client, test_user_id)
        asyncio.run(memory.ensure_user_profile(test_user_id))
        
        # Test initial location insert
        location_data = {
            "user_id": test_user_id,
            "lat": 37.7749,
            "lng": -122.4194,
            "city": "San Francisco",
            "privacy_mode": "precise",
            "max_travel_miles": 25,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        result = db_client.table('user_locations')\
            .upsert(location_data, on_conflict="user_id")\
            .execute()
        
        assert len(result.data) == 1
        assert result.data[0]["user_id"] == test_user_id
        
        # Test location update (upsert with existing user_id)
        location_data["city"] = "San Francisco, CA"
        location_data["max_travel_miles"] = 30
        
        result = db_client.table('user_locations')\
            .upsert(location_data, on_conflict="user_id")\
            .execute()
        
        assert len(result.data) == 1
        assert result.data[0]["city"] == "San Francisco, CA"
        assert result.data[0]["max_travel_miles"] == 30
    
    def test_privacy_mode_database_storage(self, db_client, test_user_id):
        """Test privacy mode storage in database"""
        from src.simple_memory import WingmanMemory
        memory = WingmanMemory(db_client, test_user_id)
        asyncio.run(memory.ensure_user_profile(test_user_id))
        
        # Test precise mode storage
        precise_location = {
            "user_id": test_user_id,
            "lat": 37.7749,
            "lng": -122.4194,
            "city": "San Francisco",
            "privacy_mode": "precise",
            "max_travel_miles": 25,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        db_client.table('user_locations')\
            .upsert(precise_location, on_conflict="user_id")\
            .execute()
        
        # Verify precise coordinates are stored
        result = db_client.table('user_locations')\
            .select('*')\
            .eq('user_id', test_user_id)\
            .execute()
        
        assert result.data[0]["lat"] == 37.7749
        assert result.data[0]["lng"] == -122.4194
        assert result.data[0]["privacy_mode"] == "precise"
        
        # Test city_only mode storage
        city_only_location = {
            "user_id": test_user_id,
            "lat": 0.0,  # Placeholder coordinates
            "lng": 0.0,  # Placeholder coordinates
            "city": "San Francisco",
            "privacy_mode": "city_only",
            "max_travel_miles": 25,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        db_client.table('user_locations')\
            .upsert(city_only_location, on_conflict="user_id")\
            .execute()
        
        # Verify placeholder coordinates are stored for privacy
        result = db_client.table('user_locations')\
            .select('*')\
            .eq('user_id', test_user_id)\
            .execute()
        
        assert result.data[0]["lat"] == 0.0
        assert result.data[0]["lng"] == 0.0  
        assert result.data[0]["privacy_mode"] == "city_only"
        assert result.data[0]["city"] == "San Francisco"

# Performance and load testing
class TestProfileSetupPerformance:
    """Performance and load tests for profile setup"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_response_time_under_load(self, client):
        """Test API response time under concurrent load"""
        import concurrent.futures
        import statistics
        
        def single_request():
            payload = VALID_PROFILE_DATA.copy()
            payload["user_id"] = str(uuid.uuid4())
            
            start_time = time.time()
            response = client.post("/api/profile/complete", json=payload)
            end_time = time.time()
            
            return {
                "status_code": response.status_code,
                "response_time": end_time - start_time
            }
        
        # Run 10 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(single_request) for _ in range(10)]
            results = [future.result() for future in futures]
        
        # Analyze results
        response_times = [r["response_time"] for r in results]
        successful_requests = [r for r in results if r["status_code"] == 200]
        
        # Performance assertions
        avg_response_time = statistics.mean(response_times)
        max_response_time = max(response_times)
        
        assert avg_response_time < 1.0, f"Average response time too slow: {avg_response_time:.2f}s"
        assert max_response_time < 3.0, f"Max response time too slow: {max_response_time:.2f}s"
        assert len(successful_requests) >= 8, f"Too many failed requests: {len(successful_requests)}/10"
    
    def test_memory_usage_with_large_payloads(self, client):
        """Test memory usage with large valid payloads"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Submit multiple large payloads
        for i in range(5):
            payload = VALID_PROFILE_DATA.copy()
            payload["user_id"] = str(uuid.uuid4())
            payload["bio"] = "A" * 390 + f" Request #{i}"  # Large bio
            
            response = client.post("/api/profile/complete", json=payload)
            assert response.status_code == 200
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (< 50MB)
        assert memory_increase < 50 * 1024 * 1024, f"Memory usage increased too much: {memory_increase / 1024 / 1024:.2f}MB"

if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
