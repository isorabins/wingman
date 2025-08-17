#!/usr/bin/env python3
"""
Test script for POST /api/session/confirm-completion endpoint

Tests Task 15 implementation:
- Session/match membership validation
- Completion confirmation toggle
- Mutual completion detection and session completion
- Reputation updates
- Idempotency handling
- Error cases
"""

import asyncio
import json
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, Any
import httpx
import pytest

# Test configuration
BASE_URL = "http://localhost:8000"
TEST_USER_1 = str(uuid.uuid4())
TEST_USER_2 = str(uuid.uuid4())

class SessionConfirmCompletionTester:
    """Test harness for session confirmation completion endpoint"""
    
    def __init__(self):
        self.base_url = BASE_URL
        self.test_session_id = None
        self.test_match_id = None
        
    async def setup_test_data(self) -> Dict[str, Any]:
        """Create test data: users, profiles, match, and session"""
        print("\n🔧 Setting up test data...")
        
        async with httpx.AsyncClient() as client:
            # Create user profiles
            await self._create_test_profile(client, TEST_USER_1, "User One", "San Francisco")
            await self._create_test_profile(client, TEST_USER_2, "User Two", "Oakland")
            
            # Create a wingman match
            match_data = await self._create_test_match(client)
            self.test_match_id = match_data["match_id"]
            
            # Create a wingman session
            session_data = await self._create_test_session(client, self.test_match_id)
            self.test_session_id = session_data["session_id"]
            
            print(f"✅ Test data ready - Match: {self.test_match_id}, Session: {self.test_session_id}")
            return {
                "match_id": self.test_match_id,
                "session_id": self.test_session_id
            }
    
    async def _create_test_profile(self, client: httpx.AsyncClient, user_id: str, name: str, city: str):
        """Create test user profile"""
        profile_data = {
            "user_id": user_id,
            "bio": f"Test user {name}",
            "location": {
                "lat": 37.7749,
                "lng": -122.4194,
                "city": city,
                "privacy_mode": "city_only"
            },
            "travel_radius": 25
        }
        
        response = await client.post(
            f"{self.base_url}/api/profile/complete",
            json=profile_data,
            headers={"X-Test-User-ID": user_id}
        )
        
        if response.status_code != 200:
            print(f"⚠️ Profile creation warning for {name}: {response.status_code} - {response.text}")
    
    async def _create_test_match(self, client: httpx.AsyncClient) -> Dict[str, Any]:
        """Create and accept a test match"""
        # Create auto match
        response = await client.post(
            f"{self.base_url}/api/matches/auto/{TEST_USER_1}",
            headers={"X-Test-User-ID": TEST_USER_1}
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to create match: {response.status_code} - {response.text}")
        
        match_data = response.json()
        match_id = match_data["match_id"]
        
        # Accept the match from both sides
        for user_id in [TEST_USER_1, TEST_USER_2]:
            response = await client.post(
                f"{self.base_url}/api/buddy/respond",
                json={
                    "user_id": user_id,
                    "match_id": match_id,
                    "action": "accept"
                },
                headers={"X-Test-User-ID": user_id}
            )
            
            if response.status_code != 200:
                print(f"⚠️ Match accept warning for {user_id}: {response.status_code} - {response.text}")
        
        return {"match_id": match_id}
    
    async def _create_test_session(self, client: httpx.AsyncClient, match_id: str) -> Dict[str, Any]:
        """Create a test session"""
        # Get challenges first
        response = await client.get(f"{self.base_url}/api/challenges")
        challenges = response.json().get("challenges", [])
        
        if len(challenges) < 2:
            raise Exception("Need at least 2 challenges for testing")
        
        # Create session scheduled for past time (so we can confirm completion)
        past_time = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        
        session_data = {
            "match_id": match_id,
            "venue_name": "Test Coffee Shop",
            "time": past_time,
            "challenge_ids": [challenges[0]["id"], challenges[1]["id"]]
        }
        
        response = await client.post(
            f"{self.base_url}/api/session/create",
            json=session_data,
            headers={"X-Test-User-ID": TEST_USER_1}
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to create session: {response.status_code} - {response.text}")
        
        session_response = response.json()
        return {"session_id": session_response["session_id"]}
    
    async def test_session_completion_flow(self) -> Dict[str, Any]:
        """Test complete session completion flow"""
        print("\n🧪 Testing session completion flow...")
        results = {}
        
        async with httpx.AsyncClient() as client:
            # Test 1: User1 confirms their own completion
            print("📝 Test 1: User1 confirms completion")
            response = await client.post(
                f"{self.base_url}/api/session/confirm-completion",
                json={"session_id": self.test_session_id},
                headers={"X-Test-User-ID": TEST_USER_1}
            )
            
            results["user1_confirm"] = {
                "status_code": response.status_code,
                "response": response.json() if response.status_code == 200 else response.text
            }
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ User1 confirmation: {data['message']}")
                print(f"   Both confirmed: {data['both_confirmed']}")
                print(f"   Reputation updated: {data['reputation_updated']}")
                print(f"   Session status: {data['session_status']}")
            else:
                print(f"❌ User1 confirmation failed: {response.status_code} - {response.text}")
            
            # Test 2: User2 confirms their own completion (should complete session)
            print("\n📝 Test 2: User2 confirms completion (should complete session)")
            response = await client.post(
                f"{self.base_url}/api/session/confirm-completion",
                json={"session_id": self.test_session_id},
                headers={"X-Test-User-ID": TEST_USER_2}
            )
            
            results["user2_confirm"] = {
                "status_code": response.status_code,
                "response": response.json() if response.status_code == 200 else response.text
            }
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ User2 confirmation: {data['message']}")
                print(f"   Both confirmed: {data['both_confirmed']}")
                print(f"   Reputation updated: {data['reputation_updated']}")
                print(f"   Session status: {data['session_status']}")
            else:
                print(f"❌ User2 confirmation failed: {response.status_code} - {response.text}")
            
            # Test 3: Test idempotency - confirm again
            print("\n📝 Test 3: Test idempotency (User1 confirms again)")
            response = await client.post(
                f"{self.base_url}/api/session/confirm-completion",
                json={"session_id": self.test_session_id},
                headers={"X-Test-User-ID": TEST_USER_1}
            )
            
            results["idempotency_test"] = {
                "status_code": response.status_code,
                "response": response.json() if response.status_code == 200 else response.text
            }
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Idempotency test: {data['message']}")
                print(f"   Session status: {data['session_status']}")
            else:
                print(f"❌ Idempotency test failed: {response.status_code} - {response.text}")
        
        return results
    
    async def test_error_cases(self) -> Dict[str, Any]:
        """Test error cases and validation"""
        print("\n🧪 Testing error cases...")
        results = {}
        
        async with httpx.AsyncClient() as client:
            # Test 1: Invalid session ID
            print("📝 Test 1: Invalid session ID")
            response = await client.post(
                f"{self.base_url}/api/session/confirm-completion",
                json={"session_id": "invalid-uuid"},
                headers={"X-Test-User-ID": TEST_USER_1}
            )
            
            results["invalid_session_id"] = {
                "status_code": response.status_code,
                "response": response.text
            }
            print(f"Status: {response.status_code} (expected 422)")
            
            # Test 2: Non-existent session
            print("\n📝 Test 2: Non-existent session")
            fake_session_id = str(uuid.uuid4())
            response = await client.post(
                f"{self.base_url}/api/session/confirm-completion",
                json={"session_id": fake_session_id},
                headers={"X-Test-User-ID": TEST_USER_1}
            )
            
            results["nonexistent_session"] = {
                "status_code": response.status_code,
                "response": response.text
            }
            print(f"Status: {response.status_code} (expected 404)")
            
            # Test 3: Unauthorized user (not participant)
            print("\n📝 Test 3: Unauthorized user")
            unauthorized_user = str(uuid.uuid4())
            response = await client.post(
                f"{self.base_url}/api/session/confirm-completion",
                json={"session_id": self.test_session_id},
                headers={"X-Test-User-ID": unauthorized_user}
            )
            
            results["unauthorized_user"] = {
                "status_code": response.status_code,
                "response": response.text
            }
            print(f"Status: {response.status_code} (expected 403)")
            
            # Test 4: No authentication
            print("\n📝 Test 4: No authentication")
            response = await client.post(
                f"{self.base_url}/api/session/confirm-completion",
                json={"session_id": self.test_session_id}
                # No headers
            )
            
            results["no_auth"] = {
                "status_code": response.status_code,
                "response": response.text
            }
            print(f"Status: {response.status_code} (expected 401)")
        
        return results
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all tests and return results"""
        print("🚀 Starting session completion endpoint tests...")
        
        try:
            # Setup test data
            setup_data = await self.setup_test_data()
            
            # Run main flow tests
            flow_results = await self.test_session_completion_flow()
            
            # Run error case tests
            error_results = await self.test_error_cases()
            
            return {
                "setup": setup_data,
                "flow_tests": flow_results,
                "error_tests": error_results,
                "success": True
            }
            
        except Exception as e:
            print(f"❌ Test setup failed: {str(e)}")
            return {
                "error": str(e),
                "success": False
            }

async def main():
    """Main test function"""
    tester = SessionConfirmCompletionTester()
    results = await tester.run_all_tests()
    
    print("\n" + "="*60)
    print("🎯 TEST RESULTS SUMMARY")
    print("="*60)
    
    if results["success"]:
        print("✅ Setup completed successfully")
        
        # Analyze flow test results
        flow_tests = results["flow_tests"]
        if all(test["status_code"] == 200 for test in flow_tests.values()):
            print("✅ All flow tests passed")
        else:
            print("❌ Some flow tests failed")
            for test_name, test_result in flow_tests.items():
                status = "✅" if test_result["status_code"] == 200 else "❌"
                print(f"   {status} {test_name}: {test_result['status_code']}")
        
        # Analyze error test results
        error_tests = results["error_tests"]
        expected_statuses = {
            "invalid_session_id": 422,
            "nonexistent_session": 404,
            "unauthorized_user": 403,
            "no_auth": 401
        }
        
        error_success = all(
            error_tests[test_name]["status_code"] == expected_status
            for test_name, expected_status in expected_statuses.items()
        )
        
        if error_success:
            print("✅ All error handling tests passed")
        else:
            print("❌ Some error handling tests failed")
            for test_name, expected_status in expected_statuses.items():
                actual_status = error_tests[test_name]["status_code"]
                status = "✅" if actual_status == expected_status else "❌"
                print(f"   {status} {test_name}: {actual_status} (expected {expected_status})")
        
        print(f"\n🎉 Overall result: {'SUCCESS' if error_success and all(test['status_code'] == 200 for test in flow_tests.values()) else 'PARTIAL SUCCESS'}")
        
    else:
        print(f"❌ Tests failed: {results['error']}")
    
    # Save detailed results
    with open("/Applications/wingman/test_session_confirm_completion_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n📄 Detailed results saved to: test_session_confirm_completion_results.json")

if __name__ == "__main__":
    asyncio.run(main())