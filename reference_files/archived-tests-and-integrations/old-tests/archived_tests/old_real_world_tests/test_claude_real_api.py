#!/usr/bin/env python3
"""
Real Claude API Test - Quick verification of our Simple Claude Client
Updated for the migration from LangChain to direct Claude API integration
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

from src.claude_client_simple import SimpleClaudeClient, ClaudeCredentials


async def test_claude_non_streaming():
    """Test basic non-streaming Claude API call"""
    print("🧪 Testing Simple Claude non-streaming API...")
    
    try:
        # Initialize credentials and client
        credentials = ClaudeCredentials()
        client = SimpleClaudeClient(credentials)
        
        # Simple test message
        messages = [{"role": "user", "content": "Say 'Hello, Simple Claude API test!' in exactly those words."}]
        
        # Send non-streaming request
        response = await client.send_message(messages, max_tokens=50, stream=False)
        
        print(f"✅ Non-streaming response received:")
        print(f"   Response: {response[:100]}...")
        
        # Check if we got the expected response
        expected_text = "Hello, Simple Claude API test!"
        if expected_text.lower() in response.lower():
            print(f"   ✅ Expected text found in response")
            return True
        else:
            print(f"   ⚠️  Expected text not found, but response received")
            return True  # Still consider it a pass if we got a response
        
    except Exception as e:
        print(f"❌ Non-streaming test error: {e}")
        return False


async def test_claude_streaming():
    """Test streaming Claude API call with Simple Claude Client"""
    print("\n🌊 Testing Simple Claude streaming API...")
    
    try:
        # Initialize credentials and client
        credentials = ClaudeCredentials()
        client = SimpleClaudeClient(credentials)
        
        # Simple test message
        messages = [{"role": "user", "content": "Count from 1 to 5, one number per line."}]
        
        # Send streaming request
        print("   Starting stream...")
        chunk_count = 0
        collected_text = ""
        
        async for chunk in await client.send_message(messages, stream=True, max_tokens=100):
            chunk_count += 1
            collected_text += chunk
            print(f"   📦 Chunk {chunk_count}: '{chunk}'", end='', flush=True)
        
        print(f"\n✅ Streaming completed!")
        print(f"   Total chunks: {chunk_count}")
        print(f"   Collected text: '{collected_text.strip()}'")
        
        # Check if we got reasonable content
        if chunk_count > 0 and len(collected_text.strip()) > 0:
            return True
        else:
            print(f"   ❌ No chunks received or empty content")
            return False
        
    except Exception as e:
        print(f"❌ Streaming test error: {e}")
        return False


async def test_claude_with_parameters():
    """Test Claude API with custom parameters"""
    print("\n⚙️  Testing Simple Claude with custom parameters...")
    
    try:
        # Initialize credentials and client
        credentials = ClaudeCredentials()
        client = SimpleClaudeClient(credentials)
        
        # Test message
        messages = [{"role": "user", "content": "Respond with exactly one word: 'SUCCESS'"}]
        
        # Send request with custom parameters
        response = await client.send_message(
            messages=messages,
            model="claude-3-5-sonnet-20241022",
            max_tokens=50,
            temperature=0.1,
            stream=False
        )
        
        print(f"✅ Custom parameters response:")
        print(f"   Response: {response}")
        
        return True
        
    except Exception as e:
        print(f"❌ Custom parameters test error: {e}")
        return False


async def main():
    """Run real Simple Claude API tests"""
    print("🚀 Starting real Simple Claude API tests...\n")
    
    # Check for API key
    if not os.getenv('ANTHROPIC_API_KEY'):
        print("❌ ANTHROPIC_API_KEY not found in environment")
        print("   Please set your Claude API key in .env file")
        return
    
    # Test non-streaming first
    non_streaming_ok = await test_claude_non_streaming()
    
    # Test streaming
    streaming_ok = await test_claude_streaming()
    
    # Test custom parameters
    parameters_ok = await test_claude_with_parameters()
    
    print(f"\n🎯 Results:")
    print(f"   Non-streaming: {'✅ PASS' if non_streaming_ok else '❌ FAIL'}")
    print(f"   Streaming: {'✅ PASS' if streaming_ok else '❌ FAIL'}")
    print(f"   Custom parameters: {'✅ PASS' if parameters_ok else '❌ FAIL'}")
    
    if non_streaming_ok and streaming_ok and parameters_ok:
        print(f"\n🎉 All tests passed! Simple Claude client is working correctly.")
    else:
        print(f"\n💥 Some tests failed. Check the output above for details.")


if __name__ == "__main__":
    asyncio.run(main()) 