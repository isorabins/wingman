#!/usr/bin/env python3
"""
Test the new Simple Claude Client
"""
import asyncio
import os
import sys
from dotenv import load_dotenv

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Load environment variables
load_dotenv()

from src.claude_client_simple import SimpleClaudeClient, ClaudeCredentials


async def test_simple_non_streaming():
    """Test basic non-streaming Claude API call"""
    print("🧪 Testing Simple Claude non-streaming API...")
    
    try:
        # Initialize credentials and client
        credentials = ClaudeCredentials()
        client = SimpleClaudeClient(credentials)
        
        # Simple test message
        messages = [{"role": "user", "content": "Say 'Hello from Simple Claude!' and nothing else."}]
        
        # Send message
        response = await client.send_message(messages)
        
        print(f"✅ Non-streaming response: {response}")
        return True
        
    except Exception as e:
        print(f"❌ Non-streaming test failed: {e}")
        return False


async def test_simple_streaming():
    """Test streaming Claude API call"""
    print("\n🧪 Testing Simple Claude streaming API...")
    
    try:
        # Initialize credentials and client
        credentials = ClaudeCredentials()
        client = SimpleClaudeClient(credentials)
        
        # Simple test message
        messages = [{"role": "user", "content": "Count from 1 to 5, one number per line."}]
        
        # Send streaming message
        print("📡 Streaming response:")
        async for chunk in await client.send_message(messages, stream=True):
            print(chunk, end="", flush=True)
        
        print("\n✅ Streaming test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Streaming test failed: {e}")
        return False


async def main():
    """Run all tests"""
    print("🚀 Testing Simple Claude Client with Official SDK\n")
    
    # Test non-streaming
    non_streaming_ok = await test_simple_non_streaming()
    
    # Test streaming
    streaming_ok = await test_simple_streaming()
    
    # Summary
    if non_streaming_ok and streaming_ok:
        print("\n🎉 All tests passed! Simple Claude client is working perfectly!")
    else:
        print("\n💥 Some tests failed. Check the errors above.")


if __name__ == "__main__":
    asyncio.run(main()) 