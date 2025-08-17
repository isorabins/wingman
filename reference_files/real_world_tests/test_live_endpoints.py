#!/usr/bin/env python3
"""
Live Endpoint Testing for SimpleChatHandler System

Tests real API endpoints against dev/production servers to verify:
- SimpleChatHandler flows (creativity test, project overview, general chat)
- All major API endpoints 
- Database integration
- Error handling
- User flows end-to-end

Usage:
    python test_live_endpoints.py --env=dev      # Test against dev server
    python test_live_endpoints.py --env=prod     # Test against production
    python test_live_endpoints.py --quick        # Run quick smoke tests only
"""

import requests
import time
import json
import uuid
import argparse
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

# Environment configurations
ENVIRONMENTS = {
    "dev": {
        "api_url": "https://fridays-at-four-dev-434b1a68908b.herokuapp.com",  # Correct dev URL
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

@dataclass
class TestResult:
    test_name: str
    passed: bool
    message: str
    duration: float
    response_data: Optional[Dict] = None

class LiveEndpointTester:
    """Test runner for live API endpoints"""
    
    def __init__(self, env: str = "dev"):
        self.env_config = ENVIRONMENTS.get(env, ENVIRONMENTS["dev"])
        self.api_url = self.env_config["api_url"]
        self.env_name = self.env_config["name"]
        self.test_user_id = str(uuid.uuid4())
        self.test_thread_id = f"test_thread_{self.test_user_id[:8]}"
        self.results: List[TestResult] = []
        
    def log_test_start(self, test_name: str):
        """Log the start of a test"""
        print(f"\n🧪 {test_name}")
        print("=" * 60)
        
    def add_result(self, test_name: str, passed: bool, message: str, duration: float = 0.0, response_data: Optional[Dict] = None):
        """Add a test result"""
        result = TestResult(test_name, passed, message, duration, response_data)
        self.results.append(result)
        
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {message}")
        if duration > 0:
            print(f"⏱️  Duration: {duration:.2f}s")
        
    def send_message(self, message: str, delay: float = 0.5) -> Dict[Any, Any]:
        """Send a message to the chat API"""
        payload = {
            "question": message,
            "user_id": self.test_user_id,
            "user_timezone": "UTC",
            "thread_id": self.test_thread_id
        }
        
        print(f"📤 Sending: {message[:100]}...")
        start_time = time.time()
        
        try:
            response = requests.post(f"{self.api_url}/query", json=payload, timeout=30)
            duration = time.time() - start_time
            
            response.raise_for_status()
            response_data = response.json()
            
            ai_response = response_data.get("answer", "No response")
            print(f"📥 Response: {ai_response[:150]}...")
            
            time.sleep(delay)
            return {"success": True, "data": response_data, "duration": duration}
            
        except Exception as e:
            duration = time.time() - start_time
            print(f"❌ Error: {e}")
            return {"success": False, "error": str(e), "duration": duration}

    def test_health_endpoint(self):
        """Test the health check endpoint"""
        self.log_test_start("Health Check Endpoint")
        
        try:
            start_time = time.time()
            response = requests.get(f"{self.api_url}/health", timeout=10)
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                self.add_result(
                    "Health Check", 
                    True, 
                    f"Service healthy: {data.get('message', 'OK')}", 
                    duration,
                    data
                )
            else:
                self.add_result("Health Check", False, f"Unexpected status: {response.status_code}", duration)
                
        except Exception as e:
            self.add_result("Health Check", False, f"Request failed: {e}")

    def test_creativity_flow(self):
        """Test the intro flow when user expresses creativity interest"""
        self.log_test_start("Creativity Assessment Flow")
        
        # Test that creativity interest triggers intro flow (not direct creativity test)
        result = self.send_message("I'm interested in understanding my creative style better.")
        
        if result["success"]:
            response_text = result["data"].get("answer", "").lower()
            
            # Check if intro flow is triggered (mandatory for new users)
            intro_triggered = any(phrase in response_text for phrase in [
                "hi, i'm hai", "creative partner", "fridays at four", 
                "what's your name", "i'd love to know what to call you"
            ])
            
            self.add_result(
                "Intro Flow Trigger",
                intro_triggered,
                "Intro flow correctly triggered for new user" if intro_triggered else "Intro flow not triggered",
                result["duration"],
                result["data"]
            )
            
            # Test intro progression - provide name
            if intro_triggered:
                follow_up = self.send_message("My name is Sarah")
                
                if follow_up["success"]:
                    follow_response = follow_up["data"].get("answer", "").lower()
                    
                    # Check for intro progression (explaining what F@F does)
                    intro_progression = any(phrase in follow_response for phrase in [
                        "nice to meet you", "fridays at four is about", "creative project",
                        "support you need", "what kind of creative project"
                    ])
                    
                    self.add_result(
                        "Intro Flow Progression",
                        intro_progression,
                        "Intro flow progressed correctly" if intro_progression else "Intro flow didn't progress",
                        follow_up["duration"]
                    )
        else:
            self.add_result("Intro Flow Trigger", False, f"Request failed: {result['error']}")

    def test_project_overview_flow(self):
        """Test the intro flow when user expresses project interest"""
        self.log_test_start("Project Overview Flow")
        
        # Test that project interest triggers intro flow (not direct project planning)
        result = self.send_message("I want to start a new creative project - a science fiction novel about AI.")
        
        if result["success"]:
            response_text = result["data"].get("answer", "").lower()
            
            # Check if intro flow is triggered (mandatory for new users)
            intro_triggered = any(phrase in response_text for phrase in [
                "hi, i'm hai", "creative partner", "fridays at four",
                "what's your name", "i'd love to know what to call you"
            ])
            
            self.add_result(
                "Project Intro Trigger",
                intro_triggered,
                "Intro flow correctly triggered for project interest" if intro_triggered else "Intro flow not triggered",
                result["duration"],
                result["data"]
            )
            
            # Test intro progression with project context
            if intro_triggered:
                follow_up = self.send_message("I'm Alex")
                
                if follow_up["success"]:
                    follow_response = follow_up["data"].get("answer", "").lower()
                    
                    # Check for intro progression explaining F@F value
                    intro_progression = any(phrase in follow_response for phrase in [
                        "nice to meet you", "fridays at four is about", "creative project",
                        "support you need", "what kind of creative project"
                    ])
                    
                    self.add_result(
                        "Project Intro Progression", 
                        intro_progression,
                        "Intro flow progressed with project context" if intro_progression else "Intro flow didn't progress",
                        follow_up["duration"]
                    )
        else:
            self.add_result("Project Intro Trigger", False, f"Request failed: {result['error']}")

    def test_general_conversation(self):
        """Test general conversation capability"""
        self.log_test_start("General Conversation")
        
        # Test general creative question
        result = self.send_message("What are some tips for overcoming writer's block?")
        
        if result["success"]:
            response_text = result["data"].get("answer", "")
            
            # Check for helpful response
            helpful_response = len(response_text) > 50 and any(word in response_text.lower() for word in [
                "writing", "creative", "ideas", "inspiration", "tips", "suggestions"
            ])
            
            self.add_result(
                "General Creative Question",
                helpful_response,
                f"Helpful response provided ({len(response_text)} chars)" if helpful_response else "Response not helpful",
                result["duration"],
                result["data"]
            )
        else:
            self.add_result("General Creative Question", False, f"Request failed: {result['error']}")

    def test_streaming_endpoint(self):
        """Test the streaming endpoint"""
        self.log_test_start("Streaming Endpoint")
        
        payload = {
            "question": "Tell me a short creative writing tip in one paragraph.",
            "user_id": self.test_user_id,
            "user_timezone": "UTC", 
            "thread_id": self.test_thread_id
        }
        
        try:
            start_time = time.time()
            response = requests.post(f"{self.api_url}/query_stream", json=payload, timeout=30, stream=True)
            
            if response.status_code == 200:
                chunks_received = 0
                total_data = ""
                
                for line in response.iter_lines():
                    if line:
                        chunks_received += 1
                        try:
                            data = line.decode('utf-8')
                            if data.startswith('data: '):
                                chunk_data = json.loads(data[6:])
                                if 'chunk' in chunk_data:
                                    total_data += chunk_data['chunk']
                        except:
                            pass
                        
                        if chunks_received > 10:  # Limit for testing
                            break
                
                duration = time.time() - start_time
                
                self.add_result(
                    "Streaming Response",
                    chunks_received > 0,
                    f"Received {chunks_received} chunks, {len(total_data)} total chars",
                    duration
                )
            else:
                self.add_result("Streaming Response", False, f"Unexpected status: {response.status_code}")
                
        except Exception as e:
            self.add_result("Streaming Response", False, f"Streaming failed: {e}")

    def test_chat_history_endpoint(self):
        """Test the chat history endpoint"""
        self.log_test_start("Chat History Endpoint")
        
        try:
            start_time = time.time()
            response = requests.get(f"{self.api_url}/chat-history/{self.test_user_id}?limit=10", timeout=10)
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                self.add_result(
                    "Chat History Retrieval",
                    isinstance(data, list),
                    f"Retrieved {len(data)} messages from history",
                    duration,
                    {"message_count": len(data)}
                )
            else:
                self.add_result("Chat History Retrieval", False, f"Unexpected status: {response.status_code}", duration)
                
        except Exception as e:
            self.add_result("Chat History Retrieval", False, f"Request failed: {e}")

    def test_project_overview_endpoint(self):
        """Test the project overview endpoint"""
        self.log_test_start("Project Overview Endpoint")
        
        try:
            start_time = time.time()
            response = requests.get(f"{self.api_url}/project-overview/{self.test_user_id}", timeout=10)
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                if "error" in data:
                    # Expected for new test user
                    self.add_result(
                        "Project Overview Check",
                        data.get("error") in ["user_not_found", "no_project_overview"],
                        f"Expected error for new user: {data.get('error')}",
                        duration,
                        data
                    )
                else:
                    # User has project overview
                    self.add_result(
                        "Project Overview Check",
                        "project_name" in data,
                        f"Project overview found: {data.get('project_name', 'Unknown')}",
                        duration,
                        data
                    )
            else:
                self.add_result("Project Overview Check", False, f"Unexpected status: {response.status_code}", duration)
                
        except Exception as e:
            self.add_result("Project Overview Check", False, f"Request failed: {e}")

    def cleanup_test_data(self):
        """Attempt to cleanup test data (note: this requires admin access)"""
        print(f"\n🧹 Test cleanup")
        print("=" * 60)
        print(f"Test user ID: {self.test_user_id}")
        print("Note: Automatic cleanup requires admin database access")
        print("Manual cleanup may be needed via database tools")

    def print_summary(self):
        """Print comprehensive test results summary"""
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.passed)
        failed_tests = total_tests - passed_tests
        pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"\n{'='*60}")
        print(f"🎯 TEST SUMMARY - {self.env_name} Environment")
        print(f"{'='*60}")
        print(f"🔗 API URL: {self.api_url}")
        print(f"👤 Test User: {self.test_user_id}")
        print(f"📊 Results: {passed_tests}/{total_tests} passed ({pass_rate:.1f}%)")
        
        if failed_tests > 0:
            print(f"\n❌ Failed Tests ({failed_tests}):")
            for result in self.results:
                if not result.passed:
                    print(f"   • {result.test_name}: {result.message}")
        
        if passed_tests > 0:
            print(f"\n✅ Passed Tests ({passed_tests}):")
            for result in self.results:
                if result.passed:
                    print(f"   • {result.test_name}: {result.message}")
                    if result.duration > 0:
                        print(f"     ⏱️  {result.duration:.2f}s")
        
        # Performance summary
        avg_duration = sum(r.duration for r in self.results if r.duration > 0) / max(1, sum(1 for r in self.results if r.duration > 0))
        print(f"\n⚡ Performance: Average response time: {avg_duration:.2f}s")
        
        return pass_rate

    def run_quick_tests(self):
        """Run a quick smoke test suite"""
        print(f"\n🚀 QUICK SMOKE TESTS - {self.env_name}")
        print(f"🔗 Testing: {self.api_url}")
        
        self.test_health_endpoint()
        
        # One quick conversation test
        result = self.send_message("Hello! Can you help me with a creative project?")
        if result["success"]:
            self.add_result(
                "Basic Conversation",
                True,
                f"Got response ({len(result['data'].get('answer', ''))} chars)",
                result["duration"]
            )
        else:
            self.add_result("Basic Conversation", False, f"Failed: {result['error']}")
            
        self.cleanup_test_data()
        return self.print_summary()

    def run_comprehensive_tests(self):
        """Run the full test suite"""
        print(f"\n🚀 COMPREHENSIVE LIVE TESTS - {self.env_name}")
        print(f"🔗 Testing: {self.api_url}")
        print(f"👤 Test User: {self.test_user_id}")
        
        # Run all test categories
        self.test_health_endpoint()
        self.test_creativity_flow()
        self.test_project_overview_flow()
        self.test_general_conversation()
        self.test_streaming_endpoint()
        self.test_chat_history_endpoint()
        self.test_project_overview_endpoint()
        
        self.cleanup_test_data()
        return self.print_summary()

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Test live API endpoints")
    parser.add_argument(
        "--env", 
        choices=["dev", "prod", "local"],
        default="dev",
        help="Environment to test against"
    )
    parser.add_argument(
        "--quick",
        action="store_true", 
        help="Run quick smoke tests only"
    )
    
    args = parser.parse_args()
    
    tester = LiveEndpointTester(args.env)
    
    if args.quick:
        pass_rate = tester.run_quick_tests()
    else:
        pass_rate = tester.run_comprehensive_tests()
    
    # Exit with appropriate code
    exit_code = 0 if pass_rate >= 80 else 1
    exit(exit_code)

if __name__ == "__main__":
    main() 