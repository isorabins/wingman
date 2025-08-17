#!/usr/bin/env python3
"""
Test Database Integration with New Claude Agent
"""
import asyncio
import os
import sys
from dotenv import load_dotenv
from supabase import create_client
import uuid

# Add project root to Python path for src imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Load environment variables
load_dotenv()

from src.claude_agent import interact_with_agent
from src.simple_memory import SimpleMemory
from src.config import Config

async def test_database_integration():
    """Test complete database integration with Claude agent"""
    print("🧪 Testing Database Integration with Claude Agent...")
    
    try:
        # Create test user ID in proper UUID format
        test_user_id = str(uuid.uuid4())
        test_thread_id = f"thread_{test_user_id}"
        
        print(f"🔧 Created test user: {test_user_id}")
        
        # Initialize Supabase client
        supabase_client = create_client(Config.SUPABASE_URL, Config.SUPABASE_SERVICE_KEY)
        
        # Initialize memory system with proper parameters
        memory = SimpleMemory(supabase_client, test_user_id)
        
        # Ensure creator profile exists
        await memory.ensure_creator_profile(test_user_id)
        print("✅ Creator profile ensured")
        
        # Test 1: Basic conversation
        print("\n🎯 Test 1: Basic conversation...")
        response1 = await interact_with_agent(
            user_input="Hello! I'm interested in starting a creative writing project.",
            user_id=test_user_id,
            user_timezone="America/New_York",
            thread_id=test_thread_id,
            supabase_client=supabase_client,
            context={}
        )
        
        print(f"✅ Response 1: {response1[:150]}...")
        
        # Test 2: Check if conversation was stored
        print("\n🎯 Test 2: Verify conversation storage...")
        context = await memory.get_context(test_thread_id)
        
        print(f"✅ Stored messages: {len(context.get('messages', []))}")
        assert len(context.get('messages', [])) >= 2, "Should have at least user message and assistant response"
        
        # Test 3: Continued conversation with memory
        print("\n🎯 Test 3: Continued conversation with memory...")
        response2 = await interact_with_agent(
            user_input="What did I just tell you about my project?",
            user_id=test_user_id,
            user_timezone="America/New_York",
            thread_id=test_thread_id,
            supabase_client=supabase_client,
            context={}
        )
        
        print(f"✅ Response 2: {response2[:150]}...")
        
        # Verify the AI remembers the conversation
        assert "writing" in response2.lower() or "creative" in response2.lower(), "Should remember the writing project"
        
        # Test 4: Project onboarding trigger
        print("\n🎯 Test 4: Project onboarding flow...")
        response3 = await interact_with_agent(
            user_input="I want to write a fantasy novel about dragons and magic.",
            user_id=test_user_id,
            user_timezone="America/New_York",
            thread_id=test_thread_id,
            supabase_client=supabase_client,
            context={}
        )
        
        print(f"✅ Response 3: {response3[:150]}...")
        
        # Should trigger onboarding for new users
        assert "topic 1 of 8" in response3.lower() or "project" in response3.lower(), "Should trigger onboarding"
        
        # Test 5: Check database tables
        print("\n🎯 Test 5: Verify database tables...")
        
        # Check creator_profiles
        profiles = supabase_client.table('creator_profiles').select('id').eq('id', test_user_id).execute()
        assert len(profiles.data) > 0, "Creator profile should exist"
        print("✅ Creator profile exists")
        
        # Check memory table
        memory_entries = supabase_client.table('memory').select('id').eq('user_id', test_user_id).execute()
        print(f"✅ Memory entries: {len(memory_entries.data)}")
        
        # Test 6: Memory persistence across sessions
        print("\n🎯 Test 6: Memory persistence...")
        
        # Create new memory instance (simulating new session)
        new_memory = SimpleMemory(supabase_client, test_user_id)
        new_context = await new_memory.get_context(test_thread_id)
        
        print(f"✅ Persisted messages: {len(new_context.get('messages', []))}")
        assert len(new_context.get('messages', [])) >= 4, "Should have multiple conversation turns"
        
        print("\n🎉 All database integration tests PASSED!")
        
        # Cleanup
        print("\n🧹 Cleaning up test data...")
        
        # Delete test user data in correct order to avoid foreign key constraints
        supabase_client.table('conversations').delete().eq('user_id', test_user_id).execute()
        supabase_client.table('memory').delete().eq('user_id', test_user_id).execute()
        supabase_client.table('creator_profiles').delete().eq('id', test_user_id).execute()
        
        print("✅ Test cleanup complete")
        
        return True
        
    except Exception as e:
        print(f"❌ Database integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_streaming_integration():
    """Test streaming with database integration"""
    print("\n🧪 Testing Streaming Integration...")
    
    try:
        from src.claude_agent import interact_with_agent_stream
        
        # Create test user in proper UUID format
        test_user_id = str(uuid.uuid4())
        test_thread_id = f"thread_{test_user_id}"
        
        print(f"🔧 Created test user: {test_user_id}")
        
        # Initialize Supabase client
        supabase_client = create_client(Config.SUPABASE_URL, Config.SUPABASE_SERVICE_KEY)
        
        # Initialize memory system with proper parameters
        memory = SimpleMemory(supabase_client, test_user_id)
        await memory.ensure_creator_profile(test_user_id)
        
        print("\n🎯 Testing streaming response...")
        
        response_chunks = []
        async for chunk in interact_with_agent_stream(
            user_input="Tell me a short creative writing tip.",
            user_id=test_user_id,
            user_timezone="America/New_York",
            thread_id=test_thread_id,
            supabase_client=supabase_client,
            context={}
        ):
            response_chunks.append(chunk)
            print(f"📡 Chunk: {chunk[:50]}...", end='\r')
            
        full_response = ''.join(response_chunks)
        print(f"\n✅ Streaming complete. Total response: {len(full_response)} chars")
        
        # Verify the response was stored
        context = await memory.get_context(test_thread_id)
        assert len(context.get('messages', [])) >= 2, "Streaming response should be stored"
        
        print("✅ Streaming integration test PASSED!")
        
        # Cleanup in correct order
        supabase_client.table('conversations').delete().eq('user_id', test_user_id).execute()
        supabase_client.table('memory').delete().eq('user_id', test_user_id).execute()
        supabase_client.table('creator_profiles').delete().eq('id', test_user_id).execute()
        
        return True
        
    except Exception as e:
        print(f"❌ Streaming integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all database integration tests"""
    print("🚀 Starting Database Integration Tests...")
    
    test1_passed = await test_database_integration()
    test2_passed = await test_streaming_integration()
    
    if test1_passed and test2_passed:
        print("\n🎉 ALL TESTS PASSED! Claude agent is fully integrated with the database!")
    else:
        print("\n❌ Some tests failed. Check the logs above.")
        
if __name__ == "__main__":
    asyncio.run(main()) 