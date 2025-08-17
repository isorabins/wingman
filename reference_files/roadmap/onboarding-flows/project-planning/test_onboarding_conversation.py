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
        
        print(f"\n📤 Payload: {json.dumps(payload, indent=2)}")
        
        try:
            response = requests.post(f"{self.api_url}/query", json=payload)
            print(f"🔗 Request URL: {self.api_url}/query")
            print(f"🔢 HTTP Status: {response.status_code}")
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
            if hasattr(e, 'response') and e.response is not None:
                print(f"🔢 HTTP Status: {e.response.status_code}")
                print(f"📝 Response Text: {e.response.text}")
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
        
        # Initial trigger message
        self.send_message("Hi there! I'm excited to start working on my project.")
        
        # Topic 1: Project Description
        self.send_message("I want to create a fitness app called 'WorkoutBuddy' that helps people stay motivated to exercise by connecting them with workout partners.")
        
        self.send_message("The app will focus on matching people with similar fitness goals and schedules. I want it to have social features like challenges and progress sharing.")
        
        # Topic 2: Goals and Success  
        self.send_message("My main goal is to reach 10,000 active users within the first year. I also want to achieve a 4.5+ app store rating.")
        
        self.send_message("Success for me means seeing people actually stick to their workout routines and building lasting fitness habits through the social connections.")
        
        # Topic 3: Timeline
        self.send_message("I want to have an MVP ready in 6 months, with beta testing starting in 4 months. I can dedicate about 20 hours per week to this project.")
        
        self.send_message("My target launch date is early next year, and I'm planning to submit to app stores by December.")
        
        # Topic 4: Current Progress
        self.send_message("I've already done market research and created some initial wireframes. I have about 30% of the user interface designed.")
        
        self.send_message("What's working well is the concept validation - I've interviewed 25 potential users and got really positive feedback. I need to focus more on the technical architecture.")
        
        # Topic 5: Required Resources
        self.send_message("I'll need React Native for development, Firebase for the backend, and design tools like Figma. I also want to use AI for matching algorithms.")
        
        self.send_message("I need to learn more about mobile app development and probably find a technical co-founder or freelance developer to help with the complex features.")
        
        # Topic 6: Potential Roadblocks
        self.send_message("My biggest challenge will be user acquisition and competing with established fitness apps. I'm also worried about the technical complexity of real-time matching.")
        
        self.send_message("Time management could be tough with my day job, and I'll need to be careful about feature creep - keeping the MVP focused.")
        
        # Topic 7: Motivation and Momentum
        self.send_message("I'm excited about helping people improve their health and fitness. I've struggled with workout motivation myself, so this feels personal and meaningful.")
        
        self.send_message("To maintain momentum, I plan to ship small features regularly and get user feedback early. I also want to join a founder community for accountability.")
        
        # Topic 8: Weekly Check-ins
        self.send_message("I'd love weekly check-ins on Tuesday evenings or Saturday mornings. I'll set up the video calls myself when we get to that point.")
        
        # Completion trigger
        self.send_message("I think we've covered everything about my project! This has been really helpful for organizing my thoughts.")
        
        # Post-completion message to test transition
        self.send_message("What should I focus on first to get started?")
        
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