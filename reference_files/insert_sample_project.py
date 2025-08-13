#!/usr/bin/env python3
"""
Insert sample project overview data for testing
"""

import sys
import os
from datetime import datetime, timezone

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from config import Config
from supabase import create_client

def main():
    """Insert sample project overview for testing"""
    
    # Use the same connection setup as the main app
    supabase = create_client(Config.SUPABASE_URL, Config.SUPABASE_SERVICE_KEY)
    
    user_id = '25872b7d-36cc-4a6e-b5f7-fdbb8fe2fd96'
    
    # First ensure creator profile exists
    print(f"🔍 Checking if creator profile exists for {user_id}...")
    
    profile_result = supabase.table('creator_profiles')\
        .select('*')\
        .eq('id', user_id)\
        .limit(1)\
        .execute()
    
    if not profile_result.data:
        print("🔧 Creating creator profile...")
        profile_data = {
            'id': user_id,
            'slack_email': 'projecttest627@gmail.com',
            'zoom_email': 'projecttest627@gmail.com', 
            'first_name': 'project',
            'last_name': 'test 6-27'
        }
        
        supabase.table('creator_profiles').insert(profile_data).execute()
        print("✅ Creator profile created")
    else:
        print("✅ Creator profile exists")
    
    # Now insert/update project overview
    print("🔧 Inserting project overview...")
    
    project_data = {
        'id': user_id,
        'user_id': user_id,
        'project_name': 'AI-Powered Creative Writing Assistant',
        'project_type': 'Technology/Writing',
        'description': 'Developing an innovative AI writing assistant that helps authors overcome creative blocks and enhance their storytelling capabilities through intelligent suggestions and writing prompts.',
        'current_phase': 'Planning',
        'goals': [
            {"title": "MVP Development", "description": "Complete core AI writing assistance features"},
            {"title": "User Testing", "description": "Conduct beta testing with 50 authors"},
            {"title": "Feature Enhancement", "description": "Implement user feedback and optimize AI responses"}
        ],
        'challenges': [
            {"title": "AI Accuracy", "description": "Ensuring AI suggestions are contextually relevant"},
            {"title": "User Experience", "description": "Creating an intuitive interface for writers"},
            {"title": "Performance", "description": "Optimizing response times for real-time assistance"}
        ],
        'success_metrics': {
            "timeline": "6 months", 
            "kpis": ["User engagement", "Writing quality improvement", "Time saved"], 
            "targets": {"beta_users": 50, "satisfaction_rate": 85}
        },
        'creation_date': datetime.now(timezone.utc).isoformat(),
        'last_updated': datetime.now(timezone.utc).isoformat(),
        'timeline': {
            "phases": [
                {"name": "Planning", "duration": "1 month"}, 
                {"name": "Development", "duration": "3 months"}, 
                {"name": "Testing", "duration": "1 month"}, 
                {"name": "Launch", "duration": "1 month"}
            ]
        },
        'weekly_commitment': '20 hours',
        'resources_needed': {
            "technical": ["AI API access", "Cloud hosting", "Development tools"], 
            "human": ["AI specialist", "UX designer", "Beta testers"]
        },
        'working_style': 'Agile with weekly sprints and daily check-ins'
    }
    
    # Use upsert to handle both insert and update
    result = supabase.table('project_overview').upsert(project_data).execute()
    
    if result.data:
        print("✅ Project overview inserted successfully!")
        print(f"📊 Project: {result.data[0]['project_name']}")
        print(f"📈 Phase: {result.data[0]['current_phase']}")
        print(f"🎯 Goals: {len(result.data[0]['goals'])} goals")
        print(f"⚠️  Challenges: {len(result.data[0]['challenges'])} challenges")
    else:
        print("❌ Failed to insert project overview")
        print(f"Error: {result}")

if __name__ == "__main__":
    main() 