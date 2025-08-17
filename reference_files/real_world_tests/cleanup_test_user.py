#!/usr/bin/env python3
"""
Cleanup Test User Script

Clears project overview and conversation history for the test user
so we can test onboarding from a fresh state.
"""

import requests
import sys

# Configuration
API_BASE_URL = "https://fridays-at-four-dev-434b1a68908b.herokuapp.com"
TEST_USER_ID = "8bb85a19-8b6f-45f1-a495-cd66aabb9d52"

def cleanup_test_user():
    """Clean up test user data for fresh onboarding testing"""
    
    print(f"🧹 CLEANING UP TEST USER")
    print(f"👤 User ID: {TEST_USER_ID}")
    print(f"🔗 API URL: {API_BASE_URL}")
    
    # Check current state
    print(f"\n📋 Checking current project overview...")
    try:
        response = requests.get(f"{API_BASE_URL}/project-overview/{TEST_USER_ID}")
        if response.status_code == 200:
            result = response.json()
            if "error" not in result:
                print(f"✅ Found project: {result.get('project_name', 'Unknown')}")
                print(f"⚠️  NOTE: Cannot delete via API - need to clean up manually in database")
                print(f"   DELETE FROM project_overview WHERE user_id = '{TEST_USER_ID}';")
            else:
                print(f"✅ No project overview found - ready for testing!")
        else:
            print(f"❌ Error checking project overview: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Check conversation history
    print(f"\n💬 Checking conversation history...")
    try:
        response = requests.get(f"{API_BASE_URL}/chat-history/{TEST_USER_ID}")
        if response.status_code == 200:
            messages = response.json()
            if messages:
                print(f"✅ Found {len(messages)} conversation messages")
                print(f"⚠️  NOTE: Cannot delete via API - need to clean up manually in database")
                print(f"   DELETE FROM memory WHERE user_id = '{TEST_USER_ID}';")
            else:
                print(f"✅ No conversation history found - ready for testing!")
        else:
            print(f"❌ Error checking chat history: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print(f"\n🎯 TO CLEAN UP MANUALLY:")
    print(f"1. Go to Supabase dashboard")
    print(f"2. Run these SQL commands:")
    print(f"   DELETE FROM project_overview WHERE user_id = '{TEST_USER_ID}';")
    print(f"   DELETE FROM memory WHERE user_id = '{TEST_USER_ID}';")
    print(f"3. Then run: python test_onboarding_conversation.py")
    
    return True

if __name__ == "__main__":
    cleanup_test_user() 