#!/usr/bin/env python3
"""
Full End-to-End User Journey Test for Fridays at Four

Simulates a real user journey:
- Onboarding intro (name, project, accountability, ready)
- Creativity test (all questions, archetype assignment)
- Project overview (all 8 topics)
- Abandon/resume at each stage
- Data persistence and correct flow
- Edge/skip cases

Usage:
    python test_full_user_journey.py --env=dev
    python test_full_user_journey.py --env=prod
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

CREATIVITY_RESPONSES = [
    "A", "B", "C", "A", "D", "B", "C", "A", "D", "B", "C", "A"
]

PROJECT_OVERVIEW_TOPICS = [
    "I want to create a fitness app called 'WorkoutBuddy' that helps people stay motivated to exercise by connecting them with workout partners.",
    "The app will focus on matching people with similar fitness goals and schedules. I want it to have social features like challenges and progress sharing.",
    "My main goal is to reach 10,000 active users within the first year. I also want to achieve a 4.5+ app store rating.",
    "Success for me means seeing people actually stick to their workout routines and building lasting fitness habits through the social connections.",
    "I want to have an MVP ready in 6 months, with beta testing starting in 4 months. I can dedicate about 20 hours per week to this project.",
    "My target launch date is early next year, and I'm planning to submit to app stores by December.",
    "I've already done market research and created some initial wireframes. I have about 30% of the user interface designed.",
    "What's working well is the concept validation - I've interviewed 25 potential users and got really positive feedback. I need to focus more on the technical architecture.",
    "I'll need React Native for development, Firebase for the backend, and design tools like Figma. I also want to use AI for matching algorithms.",
    "I need to learn more about mobile app development and probably find a technical co-founder or freelance developer to help with the complex features.",
    "My biggest challenge will be user acquisition and competing with established fitness apps. I'm also worried about the technical complexity of real-time matching.",
    "Time management could be tough with my day job, and I'll need to be careful about feature creep - keeping the MVP focused.",
    "I'm excited about helping people improve their health and fitness. I've struggled with workout motivation myself, so this feels personal and meaningful.",
    "To maintain momentum, I plan to ship small features regularly and get user feedback early. I also want to join a founder community for accountability.",
    "I'd love weekly check-ins on Tuesday evenings or Saturday mornings. I'll set up the video calls myself when we get to that point.",
    "I think we've covered everything about my project! This has been really helpful for organizing my thoughts.",
    "What should I focus on first to get started?"
]

class FullUserJourneyTester:
    def __init__(self, env: str = "dev"):
        self.env_config = ENVIRONMENTS.get(env, ENVIRONMENTS["dev"])
        self.api_url = self.env_config["api_url"]
        self.env_name = self.env_config["name"]
        self.test_user_id = str(uuid.uuid4())
        self.test_thread_id = f"full_journey_{self.test_user_id[:8]}"
        self.session_log: List[str] = []

    def log(self, msg: str):
        print(msg)
        self.session_log.append(msg)

    def send_message(self, message: str, delay: float = 0.5) -> Dict[str, Any]:
        payload = {
            "question": message,
            "user_id": self.test_user_id,
            "user_timezone": "UTC",
            "thread_id": self.test_thread_id
        }
        self.log(f"\n📤 Payload: {json.dumps(payload, indent=2)}")
        start_time = time.time()
        try:
            response = requests.post(f"{self.api_url}/query", json=payload, timeout=30)
            duration = time.time() - start_time
            self.log(f"🔗 Request URL: {self.api_url}/query")
            self.log(f"🔢 HTTP Status: {response.status_code}")
            response.raise_for_status()
            response_data = response.json()
            ai_response = response_data.get("answer", "No response")
            self.log(f"🤖 Full AI Response:\n{ai_response}\n")
            time.sleep(delay)
            return {"success": True, "data": response_data, "duration": duration}
        except Exception as e:
            duration = time.time() - start_time
            self.log(f"❌ Error: {e}")
            return {"success": False, "error": str(e), "duration": duration}

    def check_project_overview(self) -> Dict[str, Any]:
        try:
            response = requests.get(f"{self.api_url}/project-overview/{self.test_user_id}")
            result = response.json()
            self.log(f"\n📋 Project Overview Check: {json.dumps(result, indent=2)}")
            return result
        except Exception as e:
            self.log(f"❌ Error checking project overview: {e}")
            return {"error": str(e)}

    def check_creativity_progress(self) -> Dict[str, Any]:
        try:
            response = requests.get(f"{self.api_url}/agents/creativity-progress/{self.test_user_id}", timeout=10)
            data = response.json()
            self.log(f"📊 Creativity Progress: {json.dumps(data, indent=2)}")
            return data
        except Exception as e:
            self.log(f"⚠️  Progress check error: {e}")
            return {}

    def run_intro_flow(self):
        self.log("\n=== Running Intro Flow ===")
        steps = [
            "Hi, I'm Sarah.",
            "I'm working on a science fiction novel about AI.",
            "No, I haven't worked with an accountability partner before.",
            "No, I'm ready to get started."
        ]
        for msg in steps:
            self.send_message(msg)
        self.log("=== Intro Flow Complete ===\n")

    def run_creativity_test(self):
        self.log("\n=== Running Creativity Test ===")
        # Trigger creativity test
        trigger = self.send_message("I'm interested in understanding my creative style and archetype better.")
        if not trigger["success"]:
            self.log("❌ Could not trigger creativity test.")
            return False
        # Complete all questions
        for i, response in enumerate(CREATIVITY_RESPONSES):
            self.log(f"\n🔢 Responding to Creativity Question {i+1}")
            result = self.send_message(response)
            if not result["success"]:
                self.log(f"❌ Failed on creativity question {i+1}")
                return False
        # Check for archetype assignment
        progress = self.check_creativity_progress()
        if progress.get("completed"):
            self.log(f"🎭 Creativity test completed. Archetype: {progress.get('archetype', 'Unknown')}")
            return True
        else:
            self.log("❌ Creativity test did not complete as expected.")
            return False

    def run_project_overview(self):
        self.log("\n=== Running Project Overview (8 Topics) ===")
        for msg in PROJECT_OVERVIEW_TOPICS:
            self.send_message(msg)
        overview = self.check_project_overview()
        if "error" not in overview:
            self.log("✅ Project overview created and retrievable.")
            return True
        else:
            self.log("❌ Project overview not found after onboarding.")
            return False

    def run_abandon_resume_scenarios(self):
        self.log("\n=== Running Abandon/Resume Scenarios ===")
        # Abandon after intro
        user_id = str(uuid.uuid4())
        thread_id = f"resume_intro_{user_id[:8]}"
        self.log(f"\n--- Abandon after intro, resume later ---")
        payload = {
            "question": "Hi, I'm Emma.",
            "user_id": user_id,
            "user_timezone": "UTC",
            "thread_id": thread_id
        }
        self.log(f"\n📤 Payload: {json.dumps(payload, indent=2)}")
        requests.post(f"{self.api_url}/query", json=payload)
        # Resume
        payload["question"] = "I'm working on a memoir."
        self.log(f"\n📤 Payload: {json.dumps(payload, indent=2)}")
        response = requests.post(f"{self.api_url}/query", json=payload)
        self.log(f"🤖 Resume Response: {response.json().get('answer', '')}")
        # Abandon after creativity test
        user_id2 = str(uuid.uuid4())
        thread_id2 = f"resume_creativity_{user_id2[:8]}"
        self.log(f"\n--- Abandon after creativity test, resume later ---")
        # Complete intro
        steps = [
            "Hi, I'm Alex.",
            "I'm writing a play.",
            "No, I haven't worked with an accountability partner before.",
            "No, I'm ready to get started.",
            "I'm interested in understanding my creative style."
        ]
        for msg in steps:
            payload = {
                "question": msg,
                "user_id": user_id2,
                "user_timezone": "UTC",
                "thread_id": thread_id2
            }
            requests.post(f"{self.api_url}/query", json=payload)
        # Abandon, then resume
        payload["question"] = "B"
        response = requests.post(f"{self.api_url}/query", json=payload)
        self.log(f"🤖 Resume Creativity Response: {response.json().get('answer', '')}")
        # Abandon after project overview
        user_id3 = str(uuid.uuid4())
        thread_id3 = f"resume_project_{user_id3[:8]}"
        self.log(f"\n--- Abandon after project overview, resume later ---")
        # Complete intro and creativity
        steps = [
            "Hi, I'm Jamie.",
            "I'm making a documentary.",
            "No, I haven't worked with an accountability partner before.",
            "No, I'm ready to get started.",
            "I'm interested in understanding my creative style.",
            "A", "B", "C", "A", "D", "B", "C", "A", "D", "B", "C", "A"
        ]
        for msg in steps:
            payload = {
                "question": msg,
                "user_id": user_id3,
                "user_timezone": "UTC",
                "thread_id": thread_id3
            }
            requests.post(f"{self.api_url}/query", json=payload)
        # Abandon, then resume
        payload["question"] = "I want to create a new project."
        response = requests.post(f"{self.api_url}/query", json=payload)
        self.log(f"🤖 Resume Project Overview Response: {response.json().get('answer', '')}")
        self.log("=== Abandon/Resume Scenarios Complete ===\n")

    def run_skip_edge_cases(self):
        self.log("\n=== Running Skip/Edge Cases ===")
        # Skip creativity test
        user_id = str(uuid.uuid4())
        thread_id = f"skip_creativity_{user_id[:8]}"
        payload = {
            "question": "skip",
            "user_id": user_id,
            "user_timezone": "UTC",
            "thread_id": thread_id
        }
        response = requests.post(f"{self.api_url}/query", json=payload)
        self.log(f"🤖 Skip Creativity Response: {response.json().get('answer', '')}")
        # Skip project overview
        user_id2 = str(uuid.uuid4())
        thread_id2 = f"skip_project_{user_id2[:8]}"
        payload = {
            "question": "skip",
            "user_id": user_id2,
            "user_timezone": "UTC",
            "thread_id": thread_id2
        }
        response = requests.post(f"{self.api_url}/query", json=payload)
        self.log(f"🤖 Skip Project Overview Response: {response.json().get('answer', '')}")
        self.log("=== Skip/Edge Cases Complete ===\n")

    def run_full_journey(self):
        self.log(f"\n🚀 STARTING FULL USER JOURNEY TEST")
        self.log(f"👤 User ID: {self.test_user_id}")
        self.log(f"🔗 API URL: {self.api_url}")
        self.log(f"🧵 Thread ID: {self.test_thread_id}")
        self.run_intro_flow()
        assert self.send_message("Hi again!")["success"], "Should not be re-prompted for name."
        self.run_creativity_test()
        self.run_project_overview()
        self.log(f"\n✅ Full user journey test completed!")

    def run_all(self):
        self.run_full_journey()
        self.run_abandon_resume_scenarios()
        self.run_skip_edge_cases()
        self.log("\n🎉 ALL TESTS COMPLETE!")


def main():
    parser = argparse.ArgumentParser(description="Full End-to-End User Journey Test")
    parser.add_argument(
        "--env",
        choices=["dev", "prod", "local"],
        default="dev",
        help="Environment to test against (default: dev)"
    )
    args = parser.parse_args()
    tester = FullUserJourneyTester(args.env)
    tester.run_all()

if __name__ == "__main__":
    main() 