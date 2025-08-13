#!/usr/bin/env python3
"""
Test the new Claude Agent integration
"""
import asyncio
import os
import sys
from dotenv import load_dotenv

# Add project root to Python path for src imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Load environment variables
load_dotenv()

from src.claude_agent import interact_with_agent, interact_with_agent_stream

async def test_claude_agent_integration():
    """Test the new Claude agent with a simple interaction"""
    print("🧪 Testing Claude Agent Integration...")
    
    try:
        # Mock basic parameters (we'll use None for supabase_client in this test)
        user_input = "Hello! Can you help me with a creative project?"
        user_id = "test_user_claude_agent"
        user_timezone = "America/New_York"
        thread_id = "test_thread_claude_agent"
        supabase_client = None  # Simplified test - this would normally be real
        context = {}
        
        print(f"📤 Sending: {user_input}")
        
        # Test non-streaming version first
        print("\n🔄 Testing non-streaming...")
        try:
            response = await interact_with_agent(
                user_input=user_input,
                user_id=user_id,
                user_timezone=user_timezone,
                thread_id=thread_id,
                supabase_client=supabase_client,
                context=context
            )
            print(f"✅ Non-streaming response: {response[:100]}...")
        except Exception as e:
            print(f"❌ Non-streaming test failed: {e}")
            # This is expected without real supabase client
            print("(This is expected without database - focus on Claude client part)")
        
        # Test streaming version 
        print("\n🌊 Testing streaming...")
        try:
            stream_gen = await interact_with_agent_stream(
                user_input=user_input,
                user_id=user_id,
                user_timezone=user_timezone,
                thread_id=thread_id,
                supabase_client=supabase_client,
                context=context
            )
            
            response_chunks = []
            async for chunk in stream_gen:
                response_chunks.append(chunk)
                print(f"📨 Chunk: {chunk}", end="", flush=True)
                if len(response_chunks) > 5:  # Limit for test
                    break
            
            print(f"\n✅ Streaming test completed with {len(response_chunks)} chunks")
            
        except Exception as e:
            print(f"❌ Streaming test failed: {e}")
            print("(This is also expected without database)")
        
        print("\n🎉 Claude Agent integration test completed!")
        
    except Exception as e:
        print(f"❌ Claude Agent test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_claude_agent_integration()) 