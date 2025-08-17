#!/usr/bin/env python3
"""
Performance Monitoring Test Script for WingmanMatch
Tests all performance monitoring components to validate implementation
"""

import asyncio
import aiohttp
import time
import json
from datetime import datetime, timezone

# Test configuration
API_BASE_URL = "http://localhost:8000"
TEST_ENDPOINTS = [
    "/health",
    "/api/performance/metrics/realtime",
    "/api/performance/metrics/summary?hours=1",
    "/api/performance/health/status",
    "/api/performance/health/quick",
    "/api/performance/alerts/active",
    "/api/performance/dashboard",
    "/api/test-performance"
]

class PerformanceMonitoringTester:
    """Test harness for performance monitoring implementation"""
    
    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def test_endpoint(self, endpoint: str) -> dict:
        """Test a single endpoint and measure performance"""
        start_time = time.time()
        
        try:
            url = f"{self.base_url}{endpoint}"
            print(f"Testing: {endpoint}")
            
            async with self.session.get(url) as response:
                duration = (time.time() - start_time) * 1000
                content = await response.text()
                
                result = {
                    "endpoint": endpoint,
                    "status_code": response.status,
                    "duration_ms": round(duration, 2),
                    "success": response.status < 400,
                    "response_size": len(content),
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                
                if response.status < 400:
                    try:
                        data = json.loads(content)
                        result["has_data"] = True
                        result["data_keys"] = list(data.keys()) if isinstance(data, dict) else []
                    except json.JSONDecodeError:
                        result["has_data"] = False
                else:
                    result["error"] = content
                
                return result
                
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            return {
                "endpoint": endpoint,
                "status_code": 0,
                "duration_ms": round(duration, 2),
                "success": False,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    async def test_all_endpoints(self) -> dict:
        """Test all performance monitoring endpoints"""
        print("🚀 Starting Performance Monitoring Tests")
        print("=" * 60)
        
        results = []
        total_start = time.time()
        
        for endpoint in TEST_ENDPOINTS:
            result = await self.test_endpoint(endpoint)
            results.append(result)
            
            # Print result
            status_emoji = "✅" if result["success"] else "❌"
            print(f"{status_emoji} {endpoint}: {result['status_code']} ({result['duration_ms']:.1f}ms)")
            
            if not result["success"]:
                print(f"   Error: {result.get('error', 'Unknown error')}")
            elif result.get("has_data"):
                print(f"   Data keys: {result.get('data_keys', [])}")
            
            # Small delay between requests
            await asyncio.sleep(0.1)
        
        total_duration = (time.time() - total_start) * 1000
        
        # Calculate summary statistics
        successful_tests = len([r for r in results if r["success"]])
        avg_response_time = sum(r["duration_ms"] for r in results if r["success"]) / max(successful_tests, 1)
        
        summary = {
            "total_tests": len(results),
            "successful_tests": successful_tests,
            "failed_tests": len(results) - successful_tests,
            "success_rate": (successful_tests / len(results)) * 100,
            "total_duration_ms": round(total_duration, 2),
            "avg_response_time_ms": round(avg_response_time, 2),
            "test_results": results,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        print("\n" + "=" * 60)
        print("📊 Test Summary:")
        print(f"   Total Tests: {summary['total_tests']}")
        print(f"   Successful: {summary['successful_tests']}")
        print(f"   Failed: {summary['failed_tests']}")
        print(f"   Success Rate: {summary['success_rate']:.1f}%")
        print(f"   Average Response Time: {summary['avg_response_time_ms']:.1f}ms")
        print(f"   Total Test Duration: {summary['total_duration_ms']:.1f}ms")
        
        return summary
    
    async def load_test_endpoint(self, endpoint: str, num_requests: int = 10) -> dict:
        """Perform load test on specific endpoint"""
        print(f"\n🔥 Load Testing: {endpoint} ({num_requests} requests)")
        print("-" * 40)
        
        tasks = []
        start_time = time.time()
        
        for i in range(num_requests):
            task = self.test_endpoint(endpoint)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        total_duration = (time.time() - start_time) * 1000
        
        # Calculate load test statistics
        successful_requests = [r for r in results if r["success"]]
        response_times = [r["duration_ms"] for r in successful_requests]
        
        if response_times:
            response_times.sort()
            p50 = response_times[len(response_times) // 2]
            p95 = response_times[int(len(response_times) * 0.95)]
            p99 = response_times[int(len(response_times) * 0.99)]
        else:
            p50 = p95 = p99 = 0
        
        load_summary = {
            "endpoint": endpoint,
            "total_requests": num_requests,
            "successful_requests": len(successful_requests),
            "failed_requests": num_requests - len(successful_requests),
            "success_rate": (len(successful_requests) / num_requests) * 100,
            "total_duration_ms": round(total_duration, 2),
            "requests_per_second": round(num_requests / (total_duration / 1000), 2),
            "response_time_percentiles": {
                "p50": p50,
                "p95": p95,
                "p99": p99,
                "min": min(response_times) if response_times else 0,
                "max": max(response_times) if response_times else 0,
                "avg": sum(response_times) / len(response_times) if response_times else 0
            }
        }
        
        print(f"   Requests: {load_summary['successful_requests']}/{load_summary['total_requests']}")
        print(f"   Success Rate: {load_summary['success_rate']:.1f}%")
        print(f"   RPS: {load_summary['requests_per_second']:.1f}")
        print(f"   P50: {load_summary['response_time_percentiles']['p50']:.1f}ms")
        print(f"   P95: {load_summary['response_time_percentiles']['p95']:.1f}ms")
        print(f"   P99: {load_summary['response_time_percentiles']['p99']:.1f}ms")
        
        return load_summary

async def main():
    """Main test function"""
    print("🎯 WingmanMatch Performance Monitoring Test Suite")
    print("Testing implementation and performance characteristics\n")
    
    async with PerformanceMonitoringTester() as tester:
        # Test all endpoints
        endpoint_results = await tester.test_all_endpoints()
        
        # Load test critical endpoints
        critical_endpoints = ["/health", "/api/performance/dashboard"]
        load_test_results = []
        
        for endpoint in critical_endpoints:
            load_result = await tester.load_test_endpoint(endpoint, 20)
            load_test_results.append(load_result)
        
        # Generate final report
        print("\n" + "=" * 60)
        print("🎉 PERFORMANCE MONITORING VALIDATION COMPLETE")
        print("=" * 60)
        
        # Check implementation quality
        quality_score = 0
        max_score = 100
        
        # Endpoint availability (40 points)
        success_rate = endpoint_results["success_rate"]
        quality_score += (success_rate / 100) * 40
        
        # Performance (30 points)
        avg_response_time = endpoint_results["avg_response_time_ms"]
        if avg_response_time < 100:
            quality_score += 30
        elif avg_response_time < 500:
            quality_score += 20
        elif avg_response_time < 1000:
            quality_score += 10
        
        # Load test performance (30 points)
        for load_result in load_test_results:
            if load_result["success_rate"] > 95:
                quality_score += 15
            elif load_result["success_rate"] > 90:
                quality_score += 10
            elif load_result["success_rate"] > 80:
                quality_score += 5
        
        print(f"📊 Implementation Quality Score: {quality_score:.1f}/{max_score}")
        
        if quality_score >= 90:
            print("🏆 EXCELLENT: Production-ready performance monitoring implementation!")
        elif quality_score >= 70:
            print("✅ GOOD: Performance monitoring working well with minor optimizations needed")
        elif quality_score >= 50:
            print("⚠️  FAIR: Performance monitoring functional but needs improvement")
        else:
            print("❌ POOR: Performance monitoring needs significant work")
        
        # Save detailed results
        test_report = {
            "test_timestamp": datetime.now(timezone.utc).isoformat(),
            "quality_score": quality_score,
            "endpoint_tests": endpoint_results,
            "load_tests": load_test_results
        }
        
        with open("performance_monitoring_test_report.json", "w") as f:
            json.dump(test_report, f, indent=2)
        
        print(f"\n📁 Detailed test report saved to: performance_monitoring_test_report.json")

if __name__ == "__main__":
    asyncio.run(main())
