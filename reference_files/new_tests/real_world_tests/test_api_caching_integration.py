#!/usr/bin/env python3
"""
API Caching Integration Test

Tests prompt caching through the actual FastAPI endpoints to ensure
the development server properly implements caching.
"""

import os
import sys
import asyncio
import uuid
import time
import requests
import json
from datetime import datetime, timezone

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from supabase import create_client
from src.simple_memory import SimpleMemory
from src.config import Config

# Development server URL
DEV_SERVER_URL = "http://localhost:8000"

async def test_api_caching_integration():
    """Test prompt caching through actual API endpoints"""
    print("🌐 Testing Prompt Caching Through API Endpoints")
    
    # Create test user with proper UUID format
    test_user_id = str(uuid.uuid4())
    thread_id = f"test-thread-{uuid.uuid4()}"
    supabase_client = create_client(Config.SUPABASE_URL, Config.SUPABASE_SERVICE_KEY)
    
    try:
        # Test 1: Setup test user and rich context
        print("\n1. Setting up test user with rich context...")
        memory_handler = SimpleMemory(supabase_client, test_user_id)
        await memory_handler.ensure_creator_profile(test_user_id)
        
        # Create rich context by storing data directly in database
        # Insert creativity profile
        creativity_data = {
            "user_id": test_user_id,
            "archetype": "authentic_creator",
            "secondary_archetype": "knowledge_seeker",
            "archetype_score": 4,
            "secondary_score": 3,
            "responses": {
                "question_1": "Personal expression matters most",
                "question_2": "Authenticity drives my work",
                "question_3": "Research helps creativity"
            },
            "date_taken": datetime.now(timezone.utc).isoformat()
        }
        
        try:
            supabase_client.table('creativity_profiles').insert(creativity_data).execute()
            print("   ✅ Created creativity profile")
        except Exception as e:
            print(f"   ⚠️ Creativity profile creation: {e}")
        
        # Insert project overview
        project_data = {
            "user_id": test_user_id,
            "project_name": "Mystery Novel: The Hidden Truth",
            "project_type": "creative_writing",
            "description": "A psychological thriller exploring family secrets in a small coastal town",
            "current_phase": "character_development",
            "goals": [
                {"goal": "Develop complex protagonist", "priority": "high"},
                {"goal": "Build atmospheric tension", "priority": "high"},
                {"goal": "Research small town dynamics", "priority": "medium"}
            ],
            "challenges": [
                {"challenge": "Balancing reveal pacing", "difficulty": "high"},
                {"challenge": "Character voice consistency", "difficulty": "medium"}
            ],
            "success_metrics": {
                "word_count_target": 80000,
                "completion_timeline": "6 months",
                "quality_goals": ["compelling characters", "tight pacing", "authentic dialogue"]
            }
        }
        
        try:
            supabase_client.table('project_overview').insert(project_data).execute()
            print("   ✅ Created project overview")
        except Exception as e:
            print(f"   ⚠️ Project overview creation: {e}")
        
        # Insert some conversation history to build context
        conversation_data = [
            {
                "user_id": test_user_id,
                "thread_id": thread_id,
                "role": "user",
                "content": "I'm working on developing my protagonist for my mystery novel",
                "created_at": datetime.now(timezone.utc).isoformat()
            },
            {
                "user_id": test_user_id,
                "thread_id": thread_id,
                "role": "assistant", 
                "content": "That's exciting! Tell me about your protagonist. What makes them compelling?",
                "created_at": datetime.now(timezone.utc).isoformat()
            },
            {
                "user_id": test_user_id,
                "thread_id": thread_id,
                "role": "user",
                "content": "She's a forensic psychologist returning to her hometown after 15 years",
                "created_at": datetime.now(timezone.utc).isoformat()
            }
        ]
        
        for conv in conversation_data:
            try:
                supabase_client.table('conversations').insert(conv).execute()
            except Exception as e:
                print(f"   ⚠️ Conversation insert: {e}")
        
        print("   ✅ Created conversation history")
        
        # Test 2: Make API calls to test caching
        print("\n2. Testing API calls with caching...")
        
        # Prepare request data
        chat_request = {
            "message": "What character development techniques would work well for my protagonist?",
            "user_id": test_user_id,
            "user_timezone": "UTC",
            "thread_id": thread_id
        }
        
        # First API call - should populate cache
        print("   Making first API call (populating cache)...")
        start_time = time.time()
        
        try:
            response1 = requests.post(
                f"{DEV_SERVER_URL}/chat",
                json=chat_request,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            first_call_time = time.time() - start_time
            
            if response1.status_code == 200:
                first_response = response1.json()
                print(f"   ✅ First call successful in {first_call_time:.2f}s")
                print(f"   Response length: {len(first_response.get('response', ''))}")
            else:
                print(f"   ❌ First call failed: {response1.status_code} - {response1.text}")
                return
                
        except Exception as e:
            print(f"   ❌ First call error: {e}")
            return
        
        # Second API call - should use cache (same context, different question)
        print("   Making second API call (should use cache)...")
        start_time = time.time()
        
        chat_request["message"] = "How can I make the small town setting more atmospheric?"
        
        try:
            response2 = requests.post(
                f"{DEV_SERVER_URL}/chat",
                json=chat_request,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            second_call_time = time.time() - start_time
            
            if response2.status_code == 200:
                second_response = response2.json()
                print(f"   ✅ Second call successful in {second_call_time:.2f}s")
                print(f"   Response length: {len(second_response.get('response', ''))}")
            else:
                print(f"   ❌ Second call failed: {response2.status_code} - {response2.text}")
                return
                
        except Exception as e:
            print(f"   ❌ Second call error: {e}")
            return
        
        # Test 3: Analyze caching performance
        print("\n3. Analyzing API caching performance...")
        speed_improvement = ((first_call_time - second_call_time) / first_call_time) * 100
        
        print(f"   First API call time: {first_call_time:.2f}s")
        print(f"   Second API call time: {second_call_time:.2f}s")
        print(f"   Speed improvement: {speed_improvement:.1f}%")
        
        if second_call_time < first_call_time:
            print("   ✅ API caching appears to be working - second call was faster!")
        else:
            print("   ⚠️  API caching may not be working - second call was not faster")
            
        # Test 4: Test streaming endpoint caching
        print("\n4. Testing streaming endpoint caching...")
        
        stream_request = {
            "question": "What are some techniques for building suspense gradually?", 
            "user_id": test_user_id,
            "user_timezone": "UTC",
            "thread_id": thread_id
        }
        
        print("   Testing streaming with caching...")
        start_time = time.time()
        
        try:
            stream_response = requests.post(
                f"{DEV_SERVER_URL}/query_stream",
                json=stream_request,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            stream_time = time.time() - start_time
            
            if stream_response.status_code == 200:
                print(f"   ✅ Streaming call successful in {stream_time:.2f}s")
                # Note: We can't easily measure stream content here, but timing is useful
            else:
                print(f"   ❌ Streaming call failed: {stream_response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Streaming call error: {e}")
        
        # Test 5: Verify context persistence across calls
        print("\n5. Testing context persistence...")
        
        # Third call referencing previous conversation
        chat_request["message"] = "Building on our previous discussion about my protagonist, how should I handle her backstory reveal?"
        
        try:
            response3 = requests.post(
                f"{DEV_SERVER_URL}/chat",
                json=chat_request,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response3.status_code == 200:
                third_response = response3.json()
                response_text = third_response.get('response', '').lower()
                
                # Check if response shows awareness of context
                context_indicators = [
                    'protagonist', 'forensic psychologist', 'hometown', 
                    'mystery', 'novel', 'character'
                ]
                
                context_matches = sum(1 for indicator in context_indicators if indicator in response_text)
                
                print(f"   ✅ Context awareness: {context_matches}/{len(context_indicators)} indicators found")
                
                if context_matches >= 3:
                    print("   ✅ Strong context persistence - AI remembers previous conversation")
                else:
                    print("   ⚠️  Weak context persistence - AI may not be using full context")
                    
            else:
                print(f"   ❌ Context test failed: {response3.status_code}")
                
        except Exception as e:
            print(f"   ❌ Context test error: {e}")
        
        print("\n🎉 API caching integration test completed!")
        print(f"📊 Summary:")
        print(f"   - First API call: {first_call_time:.2f}s")
        print(f"   - Second API call: {second_call_time:.2f}s")
        print(f"   - Performance improvement: {speed_improvement:.1f}%")
        print(f"   - Streaming call: {stream_time:.2f}s")
        print(f"   - Context awareness: {context_matches}/{len(context_indicators)} indicators")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Cleanup test data
        print("\n🧹 Cleaning up test data...")
        cleanup_tables = [
            ('conversations', 'user_id'),
            ('memory', 'user_id'),
            ('creativity_profiles', 'user_id'),
            ('project_overview', 'user_id'),
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
    asyncio.run(test_api_caching_integration()) 