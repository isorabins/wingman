#!/usr/bin/env python3
"""
Real-world test for DB-driven system v2 endpoints
Tests the actual API endpoints and end-to-end functionality
Location: new_tests/real_world_tests/test_db_driven_endpoints.py
"""

import asyncio
import aiohttp
import json
import time
import logging
import argparse
from typing import Dict, Any

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment configurations
ENVIRONMENTS = {
    "dev": {
        "api_url": "https://fridays-at-four-dev-434b1a68908b.herokuapp.com",
        "name": "Development"
    },
    "prod": {
        "api_url": "https://fridays-at-four-c9c6b7a513be.herokuapp.com", 
        "name": "Production"
    },
    "local": {
        "api_url": "http://localhost:8000",
        "name": "Local Development"
    }
}

TEST_USER_ID = "550e8400-e29b-41d4-a716-446655440000"
TEST_THREAD_ID = "test_thread_db_real_001"

class DBDrivenEndpointTester:
    """Test v2 DB-driven endpoints in real environment"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def test_v2_status_endpoint(self) -> Dict[str, Any]:
        """Test /v2/status/{user_id} endpoint performance"""
        logger.info("Testing v2 status endpoint...")
        
        start_time = time.time()
        
        try:
            async with self.session.get(f"{self.base_url}/v2/status/{TEST_USER_ID}") as response:
                data = await response.json()
                
            end_time = time.time()
            response_time = (end_time - start_time) * 1000
            
            return {
                "endpoint": "/v2/status",
                "status_code": response.status,
                "response_time_ms": response_time,
                "data": data,
                "success": response.status == 200 and response_time < 1000  # More lenient for remote
            }
        except Exception as e:
            return {
                "endpoint": "/v2/status",
                "status_code": 0,
                "response_time_ms": 0,
                "error": str(e),
                "success": False
            }
    
    async def test_v2_chat_endpoint(self) -> Dict[str, Any]:
        """Test /v2/chat endpoint with intro flow"""
        logger.info("Testing v2 chat endpoint...")
        
        payload = {
            "message": "Hi there!",
            "user_id": TEST_USER_ID,
            "thread_id": TEST_THREAD_ID
        }
        
        start_time = time.time()
        
        try:
            async with self.session.post(
                f"{self.base_url}/v2/chat",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                data = await response.json()
                
            end_time = time.time()
            response_time = (end_time - start_time) * 1000
            
            return {
                "endpoint": "/v2/chat",
                "status_code": response.status,
                "response_time_ms": response_time,
                "data": data,
                "success": response.status == 200 and "response" in data
            }
        except Exception as e:
            return {
                "endpoint": "/v2/chat",
                "status_code": 0,
                "response_time_ms": 0,
                "error": str(e),
                "success": False
            }
    
    async def test_v2_reset_endpoint(self) -> Dict[str, Any]:
        """Test /v2/reset/{user_id} endpoint"""
        logger.info("Testing v2 reset endpoint...")
        
        start_time = time.time()
        
        try:
            async with self.session.post(f"{self.base_url}/v2/reset/{TEST_USER_ID}") as response:
                data = await response.json()
                
            end_time = time.time()
            response_time = (end_time - start_time) * 1000
            
            return {
                "endpoint": "/v2/reset",
                "status_code": response.status,
                "response_time_ms": response_time,
                "data": data,
                "success": response.status == 200
            }
        except Exception as e:
            return {
                "endpoint": "/v2/reset",
                "status_code": 0,
                "response_time_ms": 0,
                "error": str(e),
                "success": False
            }
    
    async def test_v2_test_intro_endpoint(self) -> Dict[str, Any]:
        """Test /v2/test-intro/{user_id} endpoint"""
        logger.info("Testing v2 test-intro endpoint...")
        
        start_time = time.time()
        
        try:
            async with self.session.post(f"{self.base_url}/v2/test-intro/{TEST_USER_ID}?message=Hello") as response:
                data = await response.json()
                
            end_time = time.time()
            response_time = (end_time - start_time) * 1000
            
            return {
                "endpoint": "/v2/test-intro",
                "status_code": response.status,
                "response_time_ms": response_time,
                "data": data,
                "success": response.status == 200 and "response" in data
            }
        except Exception as e:
            return {
                "endpoint": "/v2/test-intro",
                "status_code": 0,
                "response_time_ms": 0,
                "error": str(e),
                "success": False
            }
    
    async def test_performance_comparison(self) -> Dict[str, Any]:
        """Compare v2 vs v1 performance if available"""
        logger.info("Testing performance comparison...")
        
        # Test v2 endpoint
        start_time = time.time()
        try:
            async with self.session.get(f"{self.base_url}/v2/status/{TEST_USER_ID}") as response:
                await response.json()
            v2_time = (time.time() - start_time) * 1000
        except Exception:
            v2_time = None
        
        # Test original endpoint (if available)
        v1_time = None
        try:
            start_time = time.time()
            async with self.session.get(f"{self.base_url}/agents/status/{TEST_USER_ID}") as response:
                await response.json()
            v1_time = (time.time() - start_time) * 1000
        except Exception as e:
            logger.info(f"v1 endpoint not available: {e}")
        
        improvement = None
        if v1_time and v2_time:
            improvement = ((v1_time - v2_time) / v1_time) * 100
        
        return {
            "test": "performance_comparison",
            "v2_time_ms": v2_time,
            "v1_time_ms": v1_time,
            "improvement_percentage": improvement,
            "success": v2_time is not None and v2_time < 1000  # Should be under 1s for remote
        }

async def run_db_driven_endpoint_tests(env: str = "dev"):
    """Run comprehensive DB-driven endpoint tests"""
    
    if env not in ENVIRONMENTS:
        print(f"❌ Unknown environment: {env}")
        return False
    
    env_config = ENVIRONMENTS[env]
    base_url = env_config["api_url"]
    env_name = env_config["name"]
    
    print(f"🚀 Testing DB-Driven System v2 Endpoints")
    print(f"🌍 Environment: {env_name}")
    print(f"🔗 API URL: {base_url}")
    print("=" * 50)
    
    async with DBDrivenEndpointTester(base_url) as tester:
        results = []
        
        try:
            # Test all endpoints
            tests = [
                tester.test_v2_status_endpoint(),
                tester.test_v2_reset_endpoint(),
                tester.test_v2_test_intro_endpoint(),
                tester.test_v2_chat_endpoint(),
                tester.test_performance_comparison()
            ]
            
            # Run tests
            for test_result in await asyncio.gather(*tests, return_exceptions=True):
                if isinstance(test_result, Exception):
                    results.append({
                        "test": "unknown",
                        "success": False,
                        "error": str(test_result)
                    })
                else:
                    results.append(test_result)
            
            # Print results
            print("\n📊 Test Results:")
            print("-" * 30)
            
            successful_tests = 0
            total_tests = len(results)
            
            for result in results:
                endpoint = result.get('endpoint', result.get('test', 'unknown'))
                success = result.get('success', False)
                response_time = result.get('response_time_ms')
                
                status = "✅ PASS" if success else "❌ FAIL"
                
                if response_time:
                    print(f"{status} {endpoint}: {response_time:.1f}ms")
                else:
                    print(f"{status} {endpoint}")
                
                if success:
                    successful_tests += 1
                
                if 'error' in result:
                    print(f"   Error: {result['error']}")
            
            print(f"\n🎯 Summary: {successful_tests}/{total_tests} tests passed")
            
            # Performance summary
            v2_times = [r.get('response_time_ms') for r in results if r.get('response_time_ms')]
            if v2_times:
                avg_time = sum(v2_times) / len(v2_times)
                print(f"⚡ Average v2 response time: {avg_time:.1f}ms")
                
                if avg_time < 100:
                    print("🚀 Performance: Excellent (< 100ms)")
                elif avg_time < 500:
                    print("✅ Performance: Good (< 500ms)")
                elif avg_time < 1000:
                    print("⚠️  Performance: Acceptable (< 1s)")
                else:
                    print("❌ Performance: Needs improvement (> 1s)")
            
            # Check for improvement
            perf_result = next((r for r in results if r.get('test') == 'performance_comparison'), None)
            if perf_result and perf_result.get('improvement_percentage'):
                improvement = perf_result['improvement_percentage']
                print(f"📈 Performance improvement: {improvement:.1f}% faster than v1")
            
            return successful_tests == total_tests
            
        except Exception as e:
            print(f"❌ Test suite failed: {e}")
            logger.error(f"Test suite error: {e}", exc_info=True)
            return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test DB-driven v2 endpoints")
    parser.add_argument(
        "--env", 
        choices=["dev", "prod", "local"],
        default="dev",
        help="Environment to test against (default: dev)"
    )
    
    args = parser.parse_args()
    success = asyncio.run(run_db_driven_endpoint_tests(args.env))
    exit(0 if success else 1) 