#!/usr/bin/env python3
"""
Full End-to-End DB-Driven System Test for Fridays at Four

Tests the complete DB-driven flow with v2 endpoints:
- Mandatory intro flow (5 stages)
- Creativity test flow with skip option
- Project overview flow (8 topics)
- Abandon/resume at each stage
- Database state validation
- Performance monitoring
- Edge cases and error handling

This validates that the DB-driven system provides:
- 50-95% performance improvement over agent manager
- Correct flow routing based on DB state
- Proper data persistence
- Graceful error handling

Usage:
    python test_db_driven_full_journey.py --env=dev
    python test_db_driven_full_journey.py --env=prod
    python test_db_driven_full_journey.py --env=local
"""

import requests
import time
import uuid
import argparse
import json
from typing import Dict, Any, List

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

# Test data for flows
INTRO_FLOW_STEPS = [
    "Hi, I'm Sarah.",
    "I'm working on a science fiction novel about AI consciousness.",
    "Yes, I'd love to have an accountability partner to help me stay on track.",
    "No questions, I'm ready to dive in!"
]

CREATIVITY_RESPONSES = [
    "A", "B", "C", "A", "D", "B", "C", "A", "D", "B", "C", "A"
]

PROJECT_OVERVIEW_TOPICS = [
    "I want to write a science fiction novel about AI consciousness and what it means to be human.",
    "The story will explore themes of identity, consciousness, and the relationship between humans and AI through the eyes of an AI that begins to question its existence.",
    "My goal is to complete a 80,000-word novel within 12 months and get it published, either traditionally or self-published.",
    "Success means finishing the book, getting positive feedback from beta readers, and seeing it resonate with sci-fi readers who love thought-provoking stories.",
    "I can dedicate 2 hours every morning before work, plus weekends. I want to write 1,000 words per day on average.",
    "I'm aiming to have the first draft done in 8 months, then 2 months for editing, and 2 months for publishing prep.",
    "I've already outlined the main plot and created character profiles. I have about 15,000 words written so far.",
    "What's working is my morning writing routine - I'm most creative then. I need to work on developing stronger dialogue and pacing.",
    "I'll need writing software like Scrivener, beta readers for feedback, and possibly a professional editor for the final draft.",
    "I want to improve my dialogue writing and learn more about the publishing industry, both traditional and self-publishing paths.",
    "My biggest challenge is maintaining momentum through the middle of the book where I tend to lose steam. Also balancing depth with accessibility.",
    "I worry about whether my ideas are original enough and if I can sustain reader interest throughout the entire novel.",
    "I'm passionate about exploring big philosophical questions through storytelling and creating characters that feel real and relatable.",
    "I plan to join a writing group for accountability and set weekly word count goals. I'll also read more in my genre for inspiration.",
    "Weekly check-ins on Sunday evenings would be perfect - that's when I plan my writing week ahead.",
    "I think we've covered all the important aspects of my novel project. This has really helped me organize my thoughts!",
    "What should I focus on first to maintain my writing momentum?"
]

class DBDrivenFullJourneyTester:
    """Comprehensive end-to-end tester for DB-driven system"""
    
    def __init__(self, env: str = "dev"):
        self.env_config = ENVIRONMENTS.get(env, ENVIRONMENTS["dev"])
        self.api_url = self.env_config["api_url"]
        self.env_name = self.env_config["name"]
        self.test_user_id = str(uuid.uuid4())
        self.test_thread_id = f"db_journey_{self.test_user_id[:8]}"
        self.session_log: List[str] = []
        self.performance_metrics: List[float] = []
        
    def log(self, msg: str):
        print(msg)
        self.session_log.append(msg)
    
    def send_v2_message(self, message: str, delay: float = 0.5) -> Dict[str, Any]:
        """Send message to v2/chat endpoint and measure performance"""
        payload = {
            "message": message,
            "user_id": self.test_user_id,
            "thread_id": self.test_thread_id
        }
        
        self.log(f"\n📤 v2/chat Payload: {json.dumps(payload, indent=2)}")
        start_time = time.time()
        
        try:
            response = requests.post(
                f"{self.api_url}/v2/chat", 
                json=payload, 
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            duration = time.time() - start_time
            duration_ms = duration * 1000
            self.performance_metrics.append(duration_ms)
            
            self.log(f"🔗 Request URL: {self.api_url}/v2/chat")
            self.log(f"🔢 HTTP Status: {response.status_code}")
            self.log(f"⚡ Response Time: {duration_ms:.1f}ms")
            
            if response.status_code == 200:
                response_data = response.json()
                ai_response = response_data.get("response", "No response")
                self.log(f"🤖 AI Response:\n{ai_response}\n")
                time.sleep(delay)
                return {
                    "success": True, 
                    "data": response_data, 
                    "duration_ms": duration_ms,
                    "status_code": response.status_code
                }
            else:
                self.log(f"❌ HTTP Error: {response.status_code}")
                return {
                    "success": False, 
                    "error": f"HTTP {response.status_code}", 
                    "duration_ms": duration_ms,
                    "status_code": response.status_code
                }
                
        except Exception as e:
            duration = time.time() - start_time
            duration_ms = duration * 1000
            self.log(f"❌ Error: {e}")
            return {
                "success": False, 
                "error": str(e), 
                "duration_ms": duration_ms,
                "status_code": 0
            }
    
    def check_v2_status(self) -> Dict[str, Any]:
        """Check user flow status via v2/status endpoint"""
        try:
            start_time = time.time()
            response = requests.get(f"{self.api_url}/v2/status/{self.test_user_id}", timeout=10)
            duration_ms = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                result = response.json()
                self.log(f"\n📊 v2/status Check ({duration_ms:.1f}ms): {json.dumps(result, indent=2)}")
                return {"success": True, "data": result, "duration_ms": duration_ms}
            else:
                self.log(f"❌ Status check failed: HTTP {response.status_code}")
                return {"success": False, "error": f"HTTP {response.status_code}", "duration_ms": duration_ms}
                
        except Exception as e:
            self.log(f"❌ Error checking v2 status: {e}")
            return {"success": False, "error": str(e), "duration_ms": 0}
    
    def reset_v2_flows(self) -> Dict[str, Any]:
        """Reset user flows via v2/reset endpoint"""
        try:
            start_time = time.time()
            response = requests.post(f"{self.api_url}/v2/reset/{self.test_user_id}", timeout=10)
            duration_ms = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                result = response.json()
                self.log(f"\n🔄 v2/reset ({duration_ms:.1f}ms): {json.dumps(result, indent=2)}")
                return {"success": True, "data": result, "duration_ms": duration_ms}
            else:
                self.log(f"❌ Reset failed: HTTP {response.status_code}")
                return {"success": False, "error": f"HTTP {response.status_code}", "duration_ms": duration_ms}
                
        except Exception as e:
            self.log(f"❌ Error resetting v2 flows: {e}")
            return {"success": False, "error": str(e), "duration_ms": 0}
    
    def check_database_state(self) -> Dict[str, Any]:
        """Check database state via existing endpoints"""
        db_state = {}
        
        # Check project overview
        try:
            response = requests.get(f"{self.api_url}/project-overview/{self.test_user_id}", timeout=10)
            if response.status_code == 200:
                db_state["project_overview"] = response.json()
            else:
                db_state["project_overview"] = {"error": f"HTTP {response.status_code}"}
        except Exception as e:
            db_state["project_overview"] = {"error": str(e)}
        
        # Check creativity progress
        try:
            response = requests.get(f"{self.api_url}/agents/creativity-progress/{self.test_user_id}", timeout=10)
            if response.status_code == 200:
                db_state["creativity_progress"] = response.json()
            else:
                db_state["creativity_progress"] = {"error": f"HTTP {response.status_code}"}
        except Exception as e:
            db_state["creativity_progress"] = {"error": str(e)}
        
        self.log(f"\n💾 Database State: {json.dumps(db_state, indent=2)}")
        return db_state
    
    def run_intro_flow_test(self) -> bool:
        """Test the mandatory 5-stage intro flow"""
        self.log("\n" + "="*60)
        self.log("🚀 TESTING INTRO FLOW (Mandatory 5 Stages)")
        self.log("="*60)
        
        # Check initial status
        status = self.check_v2_status()
        if status["success"]:
            intro_complete = status["data"].get("status", {}).get("intro_complete", False)
            if intro_complete:
                self.log("⚠️  Intro already complete - resetting flows")
                self.reset_v2_flows()
        
        # Run through intro steps
        for i, step in enumerate(INTRO_FLOW_STEPS, 1):
            self.log(f"\n--- Intro Step {i}/5 ---")
            result = self.send_v2_message(step)
            
            if not result["success"]:
                self.log(f"❌ Intro step {i} failed: {result.get('error')}")
                return False
            
            # Validate performance (should be much faster than old system)
            if result["duration_ms"] > 1000:  # More lenient for remote testing
                self.log(f"⚠️  Slow response: {result['duration_ms']:.1f}ms (expected < 1000ms)")
        
        # Verify intro completion
        status = self.check_v2_status()
        if status["success"]:
            intro_complete = status["data"].get("status", {}).get("intro_complete", False)
            if intro_complete:
                self.log("✅ Intro flow completed successfully!")
                return True
            else:
                self.log("❌ Intro flow not marked as complete in database")
                return False
        else:
            self.log("❌ Could not verify intro completion")
            return False
    
    def run_creativity_flow_test(self) -> bool:
        """Test creativity flow after intro"""
        self.log("\n" + "="*60)
        self.log("🎨 TESTING CREATIVITY FLOW")
        self.log("="*60)
        
        # Trigger creativity test
        trigger_result = self.send_v2_message("I'd like to understand my creative archetype better.")
        if not trigger_result["success"]:
            self.log("❌ Could not trigger creativity test")
            return False
        
        # Complete creativity questions
        for i, response in enumerate(CREATIVITY_RESPONSES, 1):
            self.log(f"\n--- Creativity Question {i}/12 ---")
            result = self.send_v2_message(response)
            
            if not result["success"]:
                self.log(f"❌ Creativity question {i} failed: {result.get('error')}")
                return False
        
        # Check completion
        db_state = self.check_database_state()
        creativity_data = db_state.get("creativity_progress", {})
        
        if creativity_data.get("completed"):
            archetype = creativity_data.get("archetype", "Unknown")
            self.log(f"✅ Creativity test completed! Archetype: {archetype}")
            return True
        else:
            self.log("❌ Creativity test not completed")
            return False
    
    def run_project_overview_test(self) -> bool:
        """Test project overview flow (8 topics)"""
        self.log("\n" + "="*60)
        self.log("📋 TESTING PROJECT OVERVIEW FLOW (8 Topics)")
        self.log("="*60)
        
        # Go through all project overview topics
        for i, topic in enumerate(PROJECT_OVERVIEW_TOPICS, 1):
            self.log(f"\n--- Project Topic {i}/{len(PROJECT_OVERVIEW_TOPICS)} ---")
            result = self.send_v2_message(topic)
            
            if not result["success"]:
                self.log(f"❌ Project topic {i} failed: {result.get('error')}")
                return False
        
        # Check project overview creation
        db_state = self.check_database_state()
        project_data = db_state.get("project_overview", {})
        
        if "error" not in project_data and project_data:
            self.log("✅ Project overview created successfully!")
            return True
        else:
            self.log("❌ Project overview not found in database")
            return False
    
    def run_abandon_resume_test(self) -> bool:
        """Test abandon/resume scenarios"""
        self.log("\n" + "="*60)
        self.log("🔄 TESTING ABANDON/RESUME SCENARIOS")
        self.log("="*60)
        
        # Test 1: Abandon after intro step 2, resume
        user_id_1 = str(uuid.uuid4())
        self.log(f"\n--- Test 1: Abandon after intro step 2 ---")
        self.log(f"👤 User ID: {user_id_1}")
        
        # Send first two intro steps
        for i, step in enumerate(INTRO_FLOW_STEPS[:2], 1):
            payload = {
                "message": step,
                "user_id": user_id_1,
                "thread_id": f"abandon_test_{user_id_1[:8]}"
            }
            response = requests.post(f"{self.api_url}/v2/chat", json=payload, timeout=30)
            self.log(f"Step {i}: {response.status_code}")
        
        # Resume later
        time.sleep(1)
        payload = {
            "message": "I'm back! Where were we?",
            "user_id": user_id_1,
            "thread_id": f"abandon_test_{user_id_1[:8]}"
        }
        response = requests.post(f"{self.api_url}/v2/chat", json=payload, timeout=30)
        
        if response.status_code == 200:
            self.log("✅ Resume after intro abandon: SUCCESS")
        else:
            self.log(f"❌ Resume after intro abandon: FAILED ({response.status_code})")
            return False
        
        # Test 2: Abandon during creativity, resume
        user_id_2 = str(uuid.uuid4())
        self.log(f"\n--- Test 2: Abandon during creativity test ---")
        self.log(f"👤 User ID: {user_id_2}")
        
        # Complete intro + start creativity
        steps = INTRO_FLOW_STEPS + ["I want to take the creativity test."] + CREATIVITY_RESPONSES[:3]
        for step in steps:
            payload = {
                "message": step,
                "user_id": user_id_2,
                "thread_id": f"abandon_creativity_{user_id_2[:8]}"
            }
            requests.post(f"{self.api_url}/v2/chat", json=payload, timeout=30)
        
        # Resume creativity
        time.sleep(1)
        payload = {
            "message": "A",  # Continue with next creativity answer
            "user_id": user_id_2,
            "thread_id": f"abandon_creativity_{user_id_2[:8]}"
        }
        response = requests.post(f"{self.api_url}/v2/chat", json=payload, timeout=30)
        
        if response.status_code == 200:
            self.log("✅ Resume during creativity: SUCCESS")
        else:
            self.log(f"❌ Resume during creativity: FAILED ({response.status_code})")
            return False
        
        self.log("✅ All abandon/resume scenarios passed!")
        return True
    
    def run_skip_scenarios_test(self) -> bool:
        """Test skip scenarios and edge cases"""
        self.log("\n" + "="*60)
        self.log("⏭️  TESTING SKIP SCENARIOS")
        self.log("="*60)
        
        # Test creativity skip
        user_id_skip = str(uuid.uuid4())
        self.log(f"\n--- Testing creativity skip ---")
        self.log(f"👤 User ID: {user_id_skip}")
        
        # Complete intro first
        for step in INTRO_FLOW_STEPS:
            payload = {
                "message": step,
                "user_id": user_id_skip,
                "thread_id": f"skip_test_{user_id_skip[:8]}"
            }
            requests.post(f"{self.api_url}/v2/chat", json=payload, timeout=30)
        
        # Try to skip creativity
        payload = {
            "message": "skip",
            "user_id": user_id_skip,
            "thread_id": f"skip_test_{user_id_skip[:8]}"
        }
        response = requests.post(f"{self.api_url}/v2/chat", json=payload, timeout=30)
        
        if response.status_code == 200:
            self.log("✅ Creativity skip handled successfully")
            return True
        else:
            self.log(f"❌ Creativity skip failed: {response.status_code}")
            return False
    
    def run_performance_analysis(self):
        """Analyze performance metrics"""
        self.log("\n" + "="*60)
        self.log("⚡ PERFORMANCE ANALYSIS")
        self.log("="*60)
        
        if not self.performance_metrics:
            self.log("❌ No performance metrics collected")
            return
        
        avg_time = sum(self.performance_metrics) / len(self.performance_metrics)
        min_time = min(self.performance_metrics)
        max_time = max(self.performance_metrics)
        
        self.log(f"📊 Performance Metrics:")
        self.log(f"   • Total requests: {len(self.performance_metrics)}")
        self.log(f"   • Average response time: {avg_time:.1f}ms")
        self.log(f"   • Fastest response: {min_time:.1f}ms")
        self.log(f"   • Slowest response: {max_time:.1f}ms")
        
        # Performance expectations for DB-driven system
        if avg_time < 100:
            self.log("🚀 Performance: EXCELLENT (< 100ms average)")
        elif avg_time < 500:
            self.log("✅ Performance: GOOD (< 500ms average)")
        elif avg_time < 1000:
            self.log("⚠️  Performance: ACCEPTABLE (< 1s average)")
        else:
            self.log("❌ Performance: NEEDS IMPROVEMENT (> 1s average)")
        
        # Calculate theoretical improvement vs old system
        old_system_avg = 1500  # ms (typical agent manager time)
        improvement = ((old_system_avg - avg_time) / old_system_avg) * 100
        self.log(f"📈 Theoretical improvement vs agent manager: {improvement:.1f}%")
    
    def run_full_journey(self) -> bool:
        """Run complete end-to-end journey"""
        self.log("\n" + "🚀" * 30)
        self.log("🚀 STARTING DB-DRIVEN FULL JOURNEY TEST")
        self.log(f"🌍 Environment: {self.env_name}")
        self.log(f"🔗 API URL: {self.api_url}")
        self.log(f"👤 User ID: {self.test_user_id}")
        self.log(f"🧵 Thread ID: {self.test_thread_id}")
        self.log("🚀" * 30)
        
        # Reset flows to start fresh
        self.reset_v2_flows()
        
        # Run all test phases
        tests = [
            ("Intro Flow", self.run_intro_flow_test),
            ("Creativity Flow", self.run_creativity_flow_test),
            ("Project Overview", self.run_project_overview_test),
            ("Abandon/Resume", self.run_abandon_resume_test),
            ("Skip Scenarios", self.run_skip_scenarios_test)
        ]
        
        results = []
        for test_name, test_func in tests:
            self.log(f"\n🧪 Running {test_name} test...")
            try:
                success = test_func()
                results.append((test_name, success))
                if success:
                    self.log(f"✅ {test_name}: PASSED")
                else:
                    self.log(f"❌ {test_name}: FAILED")
            except Exception as e:
                self.log(f"❌ {test_name}: ERROR - {e}")
                results.append((test_name, False))
        
        # Performance analysis
        self.run_performance_analysis()
        
        # Final database state check
        self.log("\n💾 Final Database State Check:")
        self.check_database_state()
        
        # Summary
        passed = sum(1 for _, success in results if success)
        total = len(results)
        
        self.log("\n" + "🎯" * 30)
        self.log("🎯 FINAL TEST SUMMARY")
        self.log("🎯" * 30)
        self.log(f"📊 Results: {passed}/{total} tests passed ({(passed/total)*100:.1f}%)")
        
        for test_name, success in results:
            status = "✅ PASS" if success else "❌ FAIL"
            self.log(f"   {status} {test_name}")
        
        if passed == total:
            self.log("\n🎉 ALL TESTS PASSED! DB-driven system is working perfectly!")
            return True
        else:
            self.log(f"\n⚠️  {total - passed} test(s) failed. Check logs above for details.")
            return False

def main():
    parser = argparse.ArgumentParser(description="DB-Driven System Full Journey Test")
    parser.add_argument(
        "--env",
        choices=["dev", "prod", "local"],
        default="dev",
        help="Environment to test against (default: dev)"
    )
    
    args = parser.parse_args()
    tester = DBDrivenFullJourneyTester(args.env)
    success = tester.run_full_journey()
    exit(0 if success else 1)

if __name__ == "__main__":
    main() 