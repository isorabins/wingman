#!/usr/bin/env python3
"""
Live Prompt Caching Test

Tests Claude prompt caching functionality against the development server.
Verifies that caching headers are sent and caching is working properly.
"""

import os
import sys
import asyncio
import uuid
import time
from datetime import datetime, timezone

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from supabase import create_client
from src.context_formatter import format_static_context_for_caching, get_cache_control_header
from src.simple_memory import SimpleMemory
from src.config import Config
from anthropic import AsyncAnthropic
import json

async def test_prompt_caching():
    """Test Claude prompt caching functionality"""
    print("🧪 Testing Claude Prompt Caching Functionality")
    
    # Create test user with proper UUID format
    test_user_id = str(uuid.uuid4())
    supabase_client = create_client(Config.SUPABASE_URL, Config.SUPABASE_SERVICE_KEY)
    
    try:
        # Test 1: Setup test data with proper context
        print("\n1. Setting up test data...")
        memory_handler = SimpleMemory(supabase_client, test_user_id)
        await memory_handler.ensure_creator_profile(test_user_id)
        
        # Create rich test context
        test_context = {
            "user_profile": {
                "id": test_user_id,
                "first_name": "Test",
                "last_name": "User",
                "slack_email": f"{test_user_id}@test.local",
                "interaction_count": 5,
                "preferences": {"theme": "creative", "focus": "writing"}
            },
            "creativity_profile": {
                "archetype": "authentic_creator",
                "secondary_archetype": "knowledge_seeker", 
                "archetype_score": 4,
                "secondary_score": 3,
                "date_taken": "2024-01-15"
            },
            "project_overview": {
                "project_name": "Mystery Novel",
                "project_type": "creative_writing",
                "description": "A psychological thriller set in small town",
                "goals": ["Write compelling characters", "Build suspense"],
                "challenges": ["Pacing the reveals", "Character depth"]
            },
            "longterm_summaries": [
                {
                    "content": "User discussed character development for protagonist",
                    "created_at": "2024-01-10T10:00:00Z"
                },
                {
                    "content": "Explored plot structure and three-act format",
                    "created_at": "2024-01-11T14:30:00Z"
                }
            ]
        }
        
        # Test 2: Format context using caching optimizer
        print("2. Testing context formatting for caching...")
        cached_context = format_static_context_for_caching(test_context)
        print(f"✅ Formatted context: {len(cached_context)} characters")
        print(f"Preview: {cached_context[:200]}...")
        
        # Test 3: Verify cache headers
        print("\n3. Testing cache control headers...")
        cache_headers = get_cache_control_header()
        print(f"✅ Cache headers: {cache_headers}")
        
        # Test 4: Test actual Claude API calls with caching
        print("\n4. Testing Claude API calls with caching...")
        anthropic_client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        
        # Build test messages with cache-controlled context
        test_messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": cached_context,
                        "cache_control": {"type": "ephemeral"}  # Enable caching for this content
                    }
                ]
            },
            {
                "role": "user", 
                "content": "What writing advice would you give me based on my project?"
            }
        ]
        
        # First call - should populate cache
        print("   Making first API call (should populate cache)...")
        start_time = time.time()
        
        response1 = await anthropic_client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=500,
            temperature=0.7,
            extra_headers=cache_headers,  # Include cache headers
            system="You are a helpful creative writing assistant.",
            messages=test_messages
        )
        
        first_call_time = time.time() - start_time
        first_response = ""
        for block in response1.content:
            if hasattr(block, 'text'):
                first_response += block.text
        
        print(f"   ✅ First call completed in {first_call_time:.2f}s")
        print(f"   Response length: {len(first_response)} characters")
        
        # Second call - should use cache (faster)
        print("   Making second API call (should use cache)...")
        start_time = time.time()
        
        # Same context, different question to test caching
        test_messages[1]["content"] = "How can I improve the pacing of my thriller?"
        
        response2 = await anthropic_client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=500,
            temperature=0.7,
            extra_headers=cache_headers,  # Include cache headers
            system="You are a helpful creative writing assistant.",
            messages=test_messages
        )
        
        second_call_time = time.time() - start_time
        second_response = ""
        for block in response2.content:
            if hasattr(block, 'text'):
                second_response += block.text
        
        print(f"   ✅ Second call completed in {second_call_time:.2f}s")
        print(f"   Response length: {len(second_response)} characters")
        
        # Test 5: Analyze caching performance
        print("\n5. Analyzing caching performance...")
        speed_improvement = ((first_call_time - second_call_time) / first_call_time) * 100
        
        print(f"   First call time: {first_call_time:.2f}s")
        print(f"   Second call time: {second_call_time:.2f}s") 
        print(f"   Speed improvement: {speed_improvement:.1f}%")
        
        if second_call_time < first_call_time:
            print("   ✅ Caching appears to be working - second call was faster!")
        else:
            print("   ⚠️  Caching may not be working - second call was not faster")
        
        # Test 6: Check cache usage in response metadata
        print("\n6. Checking response metadata for cache indicators...")
        
        # Check if response has usage information (Claude sometimes includes cache hit info)
        if hasattr(response1, 'usage'):
            print(f"   First call usage: {response1.usage}")
        if hasattr(response2, 'usage'):
            print(f"   Second call usage: {response2.usage}")
            
        # Test 7: Test context consistency 
        print("\n7. Testing context consistency for caching...")
        
        # Format same context twice - should be identical
        cached_context2 = format_static_context_for_caching(test_context)
        
        if cached_context == cached_context2:
            print("   ✅ Context formatting is consistent - enables caching")
        else:
            print("   ❌ Context formatting is inconsistent - breaks caching")
            print(f"   Length 1: {len(cached_context)}, Length 2: {len(cached_context2)}")
        
        print("\n🎉 Prompt caching test completed!")
        print(f"📊 Summary:")
        print(f"   - Context size: {len(cached_context)} characters")
        print(f"   - First call: {first_call_time:.2f}s")
        print(f"   - Second call: {second_call_time:.2f}s")
        print(f"   - Performance improvement: {speed_improvement:.1f}%")
        print(f"   - Cache headers: {cache_headers}")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Cleanup test data
        print("\n🧹 Cleaning up test data...")
        cleanup_tables = [
            ('memory', 'user_id'),
            ('conversations', 'user_id'), 
            ('longterm_memory', 'user_id'),
            ('project_updates', 'user_id'),
            ('creator_profiles', 'id')
        ]
        
        for table, id_column in cleanup_tables:
            try:
                result = supabase_client.table(table).delete().eq(id_column, test_user_id).execute()
                print(f"✅ Cleaned up {table}")
            except Exception as e:
                print(f"Cleanup error for {table}: {e}")

if __name__ == "__main__":
    asyncio.run(test_prompt_caching()) 