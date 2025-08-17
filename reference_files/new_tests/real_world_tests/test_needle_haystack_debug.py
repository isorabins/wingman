#!/usr/bin/env python3
"""
Debug Needle-in-Haystack Test

Debug version to see what context is actually being sent to Claude.
"""

import os
import sys
import asyncio
import uuid

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from supabase import create_client
from src.simple_memory import SimpleMemory
from src.config import Config
from src.context_formatter import format_static_context_for_caching

async def debug_context():
    """Debug what context is being sent"""
    
    print("🔍 Debugging Context Formation")
    
    # Create test user
    test_user_id = str(uuid.uuid4())
    supabase_client = create_client(Config.SUPABASE_URL, Config.SUPABASE_SERVICE_KEY)
    
    try:
        # Create memory handler and ensure profile exists
        memory_handler = SimpleMemory(supabase_client, test_user_id)
        await memory_handler.ensure_creator_profile(test_user_id)
        
        # Create project with needle content
        needle_content = """
        # Technical Documentation
        
        ## System Configuration
        The secret API rate limit for premium users is exactly 847 requests per minute.
        
        ## Database Settings
        The hidden database optimization flag is set to 'turbo_mode_delta_7'.
        
        ## Emergency Contacts
        The emergency contact for system failures is Sarah Chen at extension 4472.
        """
        
        project_data = {
            'user_id': test_user_id,
            'project_name': 'Debug Test Project',
            'project_type': 'Software Development',
            'description': needle_content,
            'goals': ['Test context formation'],
            'challenges': ['Debug context issues'],
            'success_metrics': {'accuracy': '100%'},
            'current_phase': 'Debug Phase',
            'timeline': '2025 Q1',
            'working_style': 'Debug testing'
        }
        
        print("💾 Storing project overview...")
        supabase_client.table('project_overview').insert(project_data).execute()
        
        # Get context the same way claude_agent.py does
        print("📋 Getting caching-optimized context...")
        caching_context = await memory_handler.get_caching_optimized_context("debug-thread")
        
        print("🔍 Raw context structure:")
        print(f"  static_context keys: {list(caching_context['static_context'].keys())}")
        print(f"  dynamic_context keys: {list(caching_context['dynamic_context'].keys())}")
        
        # Check project overview specifically
        project = caching_context['static_context'].get('project_overview')
        if project:
            print(f"  project_overview found: {project.get('project_name', 'No name')}")
            print(f"  description length: {len(project.get('description', ''))}")
        else:
            print("  project_overview: None")
        
        # Format for caching (same as claude_agent.py)
        print("\n📝 Formatted context:")
        formatted_context = format_static_context_for_caching(caching_context["static_context"])
        print(f"Length: {len(formatted_context)} characters")
        print("Content preview:")
        print(formatted_context[:1000])
        print("...")
        print(formatted_context[-500:])
        
        # Check if needles are present
        needles = [
            "847 requests per minute",
            "turbo_mode_delta_7", 
            "Sarah Chen at extension 4472"
        ]
        
        print("\n🎯 Needle detection:")
        for needle in needles:
            found = needle in formatted_context
            print(f"  '{needle}': {'✅ FOUND' if found else '❌ MISSING'}")
        
        return formatted_context
        
    except Exception as e:
        print(f"❌ Debug failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return None
        
    finally:
        # Cleanup
        print("🧹 Cleaning up...")
        cleanup_tables = [
            ('memory', 'user_id'),
            ('conversations', 'user_id'), 
            ('longterm_memory', 'user_id'),
            ('project_overview', 'user_id'),
            ('project_updates', 'user_id'),
            ('creator_profiles', 'id')
        ]
        
        for table, id_column in cleanup_tables:
            try:
                supabase_client.table(table).delete().eq(id_column, test_user_id).execute()
            except Exception as e:
                print(f"Cleanup error for {table}: {e}")

if __name__ == "__main__":
    asyncio.run(debug_context()) 