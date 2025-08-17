#!/usr/bin/env python3
"""
Automated Project Onboarding Test Script

Simulates a complete user conversation to test the improved onboarding flow.
Tests all 8 topics and completion detection.
"""

import requests
import time
import json
from typing import Dict, Any

# Configuration
API_BASE_URL = "https://fridays-at-four-dev-434b1a68908b.herokuapp.com"
TEST_USER_ID = "8bb85a19-8b6f-45f1-a495-cd66aabb9d52"  # Back to original test user
TEST_THREAD_ID = "test-onboarding-thread"

class OnboardingTester:
    def __init__(self):
        self.api_url = API_BASE_URL
        self.user_id = TEST_USER_ID
        self.thread_id = TEST_THREAD_ID
        self.conversation_count = 0

    def send_message(self, message: str, delay: float = 1.0) -> Dict[Any, Any]:
        """Send a message to the chat API and return response"""
        self.conversation_count += 1
        
        print(f"\n{'='*60}")
        print(f"MESSAGE {self.conversation_count}: USER")
        print(f"{'='*60}")
        print(f"🗣️  {message}")
        
        payload = {
            "question": message,
            "user_id": self.user_id,
            "user_timezone": "UTC",
            "thread_id": self.thread_id
        }
        
        try:
            response = requests.post(f"{self.api_url}/query", json=payload)
            response.raise_for_status()
            
            ai_response = response.json().get("answer", "No response")
            
            print(f"\n{'='*60}")
            print(f"RESPONSE {self.conversation_count}: HAI")
            print(f"{'='*60}")
            print(f"🤖  {ai_response}")
            
            # Add delay to simulate realistic conversation pace
            time.sleep(delay)
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error sending message: {e}")
            return {"error": str(e)}

    def check_project_overview(self) -> Dict[Any, Any]:
        """Check if project overview was created"""
        try:
            response = requests.get(f"{self.api_url}/project-overview/{self.user_id}")
            result = response.json()
            
            print(f"\n{'='*60}")
            print(f"PROJECT OVERVIEW CHECK")
            print(f"{'='*60}")
            
            if "error" in result:
                print(f"❌ No project overview found: {result.get('message', 'Unknown error')}")
                return result
            else:
                print(f"✅ Project overview found!")
                print(f"📋 Project Name: {result.get('project_name', 'Unknown')}")
                print(f"📋 Project Type: {result.get('project_type', 'Unknown')}")
                print(f"📋 Goals: {len(result.get('goals', []))} goals")
                print(f"📋 Challenges: {len(result.get('challenges', []))} challenges")
                return result
                
        except Exception as e:
            print(f"❌ Error checking project overview: {e}")
            return {"error": str(e)}

    def run_complete_onboarding_test(self):
        """Run the complete onboarding conversation simulation"""
        print(f"\n🚀 STARTING ONBOARDING TEST")
        print(f"👤 User ID: {self.user_id}")
        print(f"🔗 API URL: {self.api_url}")
        print(f"🧵 Thread ID: {self.thread_id}")
        
        # Initial greeting - should trigger intro
        self.send_message("Hi there! I'm excited to start working on my project.")
        
        # Respond to name question
        self.send_message("My name is Sarah.")
        
        # Respond to project question  
        self.send_message("I want to create a fitness app called 'WorkoutBuddy' that helps people stay motivated to exercise by connecting them with workout partners.")
        
        # Continue with project details when asked
        self.send_message("The app will focus on matching people with similar fitness goals and schedules. I want it to have social features like challenges and progress sharing.")
        
        # Respond to accountability/experience question
        self.send_message("I've tried fitness apps before but always lost motivation after a few weeks. I think having a real person to work out with would make a huge difference.")
        
        # Show readiness for creativity test
        self.send_message("Yes, I'm ready to start the creative personality test!")
        
        # Answer creativity test questions with actual A-F responses
        self.send_message("A")  # Question 1
        self.send_message("D")  # Question 2  
        self.send_message("B")  # Question 3
        self.send_message("E")  # Question 4
        self.send_message("C")  # Question 5
        self.send_message("A")  # Question 6
        self.send_message("F")  # Question 7
        self.send_message("B")  # Question 8
        self.send_message("D")  # Question 9
        self.send_message("A")  # Question 10
        self.send_message("E")  # Question 11
        self.send_message("C")  # Question 12
        
        # Post-creativity test conversation
        self.send_message("That was interesting! What does my creative type mean?")
        
        # Continue with project planning
        self.send_message("I'd love to start working on the project planning. What should I focus on first?")
        
        # Final check
        print(f"\n🏁 CONVERSATION COMPLETE - CHECKING RESULTS")
        self.check_project_overview()
        
        print(f"\n✅ Test completed! Sent {self.conversation_count} messages.")

    def run_quick_test(self):
        """Run a shorter test to just trigger onboarding"""
        print(f"\n🚀 STARTING QUICK ONBOARDING TEST")
        
        self.send_message("Hello! I want to work on a project.")
        self.check_project_overview()

def main():
    tester = OnboardingTester()
    
    print("Choose test type:")
    print("1. Complete onboarding conversation (recommended)")
    print("2. Quick trigger test")
    
    choice = input("Enter choice (1 or 2): ").strip()
    
    if choice == "2":
        tester.run_quick_test()
    else:
        tester.run_complete_onboarding_test()

if __name__ == "__main__":
    main() 