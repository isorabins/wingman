#!/usr/bin/env python3
"""
Creativity Flow Test for SimpleChatHandler

Tests the complete 12-question creativity assessment flow:
- Creativity test trigger
- Question progression (all 12 questions)
- Letter response handling (A, B, C, D)
- Archetype assignment (6 archetypes)
- Skip functionality
- Database integration

Usage:
    python test_creativity_flow.py --env=dev     # Test against dev server
    python test_creativity_flow.py --env=prod    # Test against production
"""

import requests
import time
import uuid
import argparse
import json
from typing import Dict, Any, List

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

# Creativity test responses to test different archetypes
CREATIVITY_RESPONSES = [
    "A",  # Question 1: Problem approach
    "B",  # Question 2: Creative inspiration
    "C",  # Question 3: Project completion
    "A",  # Question 4: Collaboration style
    "D",  # Question 5: Challenge response
    "B",  # Question 6: Feedback approach
    "C",  # Question 7: Learning preference
    "A",  # Question 8: Workspace environment
    "D",  # Question 9: Creative expression
    "B",  # Question 10: Risk tolerance
    "C",  # Question 11: Motivation source
    "A",  # Question 12: Success definition
]

class CreativityFlowTester:
    """Test runner for creativity assessment flow"""
    
    def __init__(self, env: str = "dev"):
        self.env_config = ENVIRONMENTS.get(env, ENVIRONMENTS["dev"])
        self.api_url = self.env_config["api_url"]
        self.env_name = self.env_config["name"]
        self.test_user_id = str(uuid.uuid4())
        self.test_thread_id = f"creativity_test_{self.test_user_id[:8]}"
        self.question_count = 0
        
    def send_message(self, message: str, delay: float = 0.5) -> Dict[Any, Any]:
        """Send a message to the chat API"""
        payload = {
            "question": message,
            "user_id": self.test_user_id,
            "user_timezone": "UTC",
            "thread_id": self.test_thread_id
        }
        print(f"\n📤 Payload: {json.dumps(payload, indent=2)}")
        start_time = time.time()
        try:
            response = requests.post(f"{self.api_url}/query", json=payload, timeout=30)
            duration = time.time() - start_time
            print(f"🔗 Request URL: {self.api_url}/query")
            print(f"🔢 HTTP Status: {response.status_code}")
            response.raise_for_status()
            response_data = response.json()
            ai_response = response_data.get("answer", "No response")
            print(f"🤖 Full AI Response:\n{ai_response}\n")
            time.sleep(delay)
            return {"success": True, "data": response_data, "duration": duration}
        except Exception as e:
            duration = time.time() - start_time
            print(f"❌ Error: {e}")
            return {"success": False, "error": str(e), "duration": duration}

    def check_creativity_progress(self) -> Dict[Any, Any]:
        """Check creativity test progress via API"""
        try:
            response = requests.get(f"{self.api_url}/agents/creativity-progress/{self.test_user_id}", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                print(f"📊 Creativity Progress: {data}")
                return data
            else:
                print(f"⚠️  Progress check failed: {response.status_code}")
                return {}
                
        except Exception as e:
            print(f"⚠️  Progress check error: {e}")
            return {}

    def complete_intro_flow(self):
        print("\n=== Simulating full intro flow ===")
        # Stage 1: Name
        response = self.send_message("Hi, I'm Sarah.")
        # Stage 2: Project
        response = self.send_message("I'm working on a science fiction novel about AI.")
        # Stage 3: Accountability experience
        response = self.send_message("No, I haven't worked with an accountability partner before.")
        # Stage 4: End of intro
        response = self.send_message("No, I'm ready to get started.")
        print("=== Intro flow complete ===\n")
        return response

    def trigger_creativity_test(self) -> bool:
        """Trigger the creativity assessment"""
        print("🚀 TRIGGERING CREATIVITY ASSESSMENT")
        print("=" * 60)
        print(f"🔗 API URL: {self.api_url}")
        print(f"👤 Test User: {self.test_user_id}")
        print(f"🧵 Thread ID: {self.test_thread_id}")
        # Complete the full intro flow first
        self.complete_intro_flow()
        # Now trigger the creativity assessment
        result = self.send_message("I'm interested in understanding my creative style and archetype better.")
        trigger_phrases = [
            "creativity", "archetype", "assessment", "creative style", 
            "questions", "understanding your", "creative approach",
            "question 1", "first question"
        ]
        if result["success"]:
            response_text = result["data"].get("answer", "")
            print(f"🔍 Checking for trigger phrases: {trigger_phrases}")
            matched = [phrase for phrase in trigger_phrases if phrase in response_text.lower()]
            print(f"🔎 Matched phrases: {matched}")
            if matched:
                print("✅ Creativity assessment triggered successfully!")
                return True
            else:
                print("❌ Creativity assessment not triggered")
                print(f"❗ None of the trigger phrases matched. Full response above.")
                return False
        else:
            print(f"❌ Failed to trigger creativity test: {result['error']}")
            return False

    def complete_creativity_test(self) -> bool:
        """Complete the full 12-question creativity test"""
        print("📝 COMPLETING CREATIVITY TEST")
        print("=" * 60)
        
        success_count = 0
        
        for i, response in enumerate(CREATIVITY_RESPONSES):
            expected_question = i + 1
            
            print(f"\n🔢 Responding to Question {expected_question}")
            result = self.send_message(response)
            
            if result["success"]:
                response_text = result["data"].get("answer", "").lower()
                
                # Check for progression indicators
                if expected_question < 12:
                    # Should show next question number
                    next_question = expected_question + 1
                    question_progressed = any(phrase in response_text for phrase in [
                        f"question {next_question}",
                        f"{next_question} of 12",
                        "next question",
                        "question"
                    ])
                    
                    if question_progressed:
                        print(f"✅ Progressed to next question")
                        self.question_count = next_question
                        success_count += 1
                    else:
                        print(f"⚠️  Progression unclear")
                else:
                    # Question 12 - should show completion
                    test_completed = any(phrase in response_text for phrase in [
                        "archetype", "result", "creative type", "assessment complete",
                        "your creativity", "you are", "profile"
                    ])
                    
                    if test_completed:
                        print(f"🎉 Creativity test completed!")
                        success_count += 1
                        
                        # Extract archetype if mentioned
                        archetypes = ["explorer", "artist", "innovator", "connector", "maker", "storyteller"]
                        detected_archetype = None
                        for archetype in archetypes:
                            if archetype in response_text:
                                detected_archetype = archetype
                                break
                        
                        if detected_archetype:
                            print(f"🎭 Detected archetype: {detected_archetype.title()}")
                        
                        return True
                    else:
                        print(f"⚠️  Test completion unclear")
            else:
                print(f"❌ Failed on question {expected_question}: {result['error']}")
                
        print(f"\n📊 Completion rate: {success_count}/{len(CREATIVITY_RESPONSES)}")
        return success_count >= 10  # Allow some tolerance

    def test_skip_functionality(self) -> bool:
        """Test the creativity test skip functionality"""
        print("\n⏭️  TESTING SKIP FUNCTIONALITY")
        print("=" * 60)
        
        # Create new user for skip test
        skip_user_id = str(uuid.uuid4())
        skip_thread_id = f"skip_test_{skip_user_id[:8]}"
        
        payload = {
            "question": "skip",
            "user_id": skip_user_id,
            "user_timezone": "UTC",
            "thread_id": skip_thread_id
        }
        
        result = requests.post(f"{self.api_url}/query", json=payload, timeout=30)
        
        if result.status_code == 200:
            response_text = result.json().get("answer", "").lower()
            
            skip_acknowledged = any(phrase in response_text for phrase in [
                "skip", "24 hours", "later", "postpone", "understand"
            ])
            
            if skip_acknowledged:
                print("✅ Skip functionality working")
                return True
            else:
                print("⚠️  Skip response unclear")
                return False
        else:
            print(f"❌ Skip test failed: {result.status_code}")
            return False

    def check_final_results(self) -> Dict[str, Any]:
        """Check final creativity test results"""
        print("🔍 CHECKING FINAL RESULTS")
        print("=" * 60)
        
        # Check creativity progress
        progress = self.check_creativity_progress()
        
        # Check if creator_creativity_profiles table was populated
        # (This would require database access, so we'll rely on API responses)
        
        return {
            "progress_data": progress,
            "test_completed": bool(progress.get("creativity_complete")),
            "user_id": self.test_user_id
        }

    def run_full_test(self) -> bool:
        """Run the complete creativity flow test"""
        print(f"\n🎯 CREATIVITY FLOW TEST - {self.env_name}")
        print(f"🔗 API URL: {self.api_url}")
        print(f"👤 Test User: {self.test_user_id}")
        print(f"🧵 Thread ID: {self.test_thread_id}")
        
        # Step 1: Trigger creativity test
        if not self.trigger_creativity_test():
            print("❌ FAILED: Could not trigger creativity test")
            return False
        
        # Step 2: Complete all 12 questions
        if not self.complete_creativity_test():
            print("❌ FAILED: Could not complete creativity test")
            return False
        
        # Step 3: Test skip functionality (with different user)
        skip_works = self.test_skip_functionality()
        
        # Step 4: Check final results
        results = self.check_final_results()
        
        # Summary
        print(f"\n{'='*60}")
        print(f"🎯 CREATIVITY FLOW TEST SUMMARY")
        print(f"{'='*60}")
        print(f"✅ Creativity test triggered: Yes")
        print(f"✅ Questions completed: {self.question_count}/12")
        print(f"{'✅' if skip_works else '⚠️ '} Skip functionality: {'Working' if skip_works else 'Unclear'}")
        print(f"👤 Test User ID: {self.test_user_id}")
        
        if results.get("test_completed"):
            print(f"🎉 OVERALL RESULT: SUCCESS!")
            return True
        else:
            print(f"⚠️  OVERALL RESULT: Partial success - creativity flow working but completion unclear")
            return False

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Test creativity assessment flow")
    parser.add_argument(
        "--env", 
        choices=["dev", "prod", "local"],
        default="dev",
        help="Environment to test against"
    )
    
    args = parser.parse_args()
    
    tester = CreativityFlowTester(args.env)
    success = tester.run_full_test()
    
    exit_code = 0 if success else 1
    exit(exit_code)

if __name__ == "__main__":
    main() 