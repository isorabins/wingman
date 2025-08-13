#!/usr/bin/env python3
"""
API Speed Diagnosis Test

Diagnoses why Claude API calls are taking 6-8 seconds.
"""

import os
import sys
import asyncio
import time
from datetime import datetime

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from anthropic import AsyncAnthropic
from src.config import Config
from src.context_formatter import format_static_context_for_caching, get_cache_control_header

async def test_api_speed():
    """Test Claude API speed with minimal vs full context"""
    
    print("🔍 Diagnosing Claude API Speed")
    print(f"⏰ Test started at: {datetime.now()}")
    
    client = AsyncAnthropic(api_key=Config.ANTHROPIC_API_KEY)
    
    # Test 1: Minimal request
    print("\n1. Testing minimal request...")
    start_time = time.time()
    
    minimal_response = await client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=100,
        messages=[{"role": "user", "content": "Say hello in exactly 5 words."}],
        extra_headers=get_cache_control_header()
    )
    
    minimal_time = time.time() - start_time
    print(f"✅ Minimal request: {minimal_time:.2f}s")
    print(f"   Response: {minimal_response.content[0].text}")
    
    # Test 2: Medium context (like our current)
    print("\n2. Testing medium context...")
    start_time = time.time()
    
    # Create a medium-sized context
    context = """
User Profile: Test user working on creative writing
Recent conversation about character development and plot pacing
Project: Psychological thriller set in small town
Goals: Build tension, develop complex characters
Challenges: Pacing reveals appropriately
""" * 3  # About 600 characters
    
    medium_response = await client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=200,
        messages=[
            {
                "role": "user", 
                "content": [
                    {
                        "type": "text",
                        "text": context,
                        "cache_control": {"type": "ephemeral"}
                    }
                ]
            },
            {"role": "user", "content": "Give me one specific writing tip based on this context."}
        ],
        extra_headers=get_cache_control_header()
    )
    
    medium_time = time.time() - start_time
    print(f"✅ Medium context: {medium_time:.2f}s")
    print(f"   Cache usage: creation={medium_response.usage.cache_creation_input_tokens}, read={medium_response.usage.cache_read_input_tokens}")
    
    # Test 3: Large context (what might trigger caching)
    print("\n3. Testing large context...")
    start_time = time.time()
    
    # Create a larger context to trigger caching
    large_context = """
User Profile: Sarah is a creative professional working on her first novel
Background: Former marketing executive, now pursuing creative writing
Creative Profile: Analytical creator with strong planning skills
Project Overview: Psychological thriller set in fictional small town "Millbrook"
Genre: Literary thriller with psychological elements
Target Audience: Adult readers who enjoy character-driven mysteries
Current Progress: First draft, 45,000 words completed

Recent Session History:
- Discussed character development techniques
- Worked on plot pacing strategies  
- Explored small town setting dynamics
- Addressed reveal timing challenges
- Brainstormed tension-building methods

Character Development Focus:
Protagonist: Elena Rodriguez, newcomer to town with mysterious past
Supporting Cast: Town residents each harboring secrets
Antagonist: Unknown figure manipulating town events
Character Arc: Elena must confront her past to save the town

Plot Structure:
Act 1: Elena arrives, strange events begin
Act 2: Mysteries deepen, Elena investigates
Act 3: Truth revealed, confrontation, resolution

Writing Challenges:
1. Balancing multiple character perspectives
2. Maintaining consistent tone
3. Building atmospheric tension
4. Timing reveals for maximum impact
5. Avoiding common thriller tropes

User Goals:
- Create compelling, complex characters
- Build genuine suspense without cheap tricks
- Develop authentic small-town atmosphere
- Write memorable, impactful scenes
- Complete first draft within 3 months
""" * 2  # About 2400 characters

    large_response = await client.messages.create(
        model="claude-3-5-sonnet-20241022", 
        max_tokens=300,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": large_context,
                        "cache_control": {"type": "ephemeral"}
                    }
                ]
            },
            {"role": "user", "content": "Based on all this context, what's the most important next step for Elena's character development?"}
        ],
        extra_headers=get_cache_control_header()
    )
    
    large_time = time.time() - start_time
    print(f"✅ Large context: {large_time:.2f}s")
    print(f"   Cache usage: creation={large_response.usage.cache_creation_input_tokens}, read={large_response.usage.cache_read_input_tokens}")
    
    # Test 4: Repeat large context to test caching
    print("\n4. Testing cache hit...")
    start_time = time.time()
    
    cache_response = await client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=200,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text", 
                        "text": large_context,
                        "cache_control": {"type": "ephemeral"}
                    }
                ]
            },
            {"role": "user", "content": "What's another important aspect of Elena's development?"}
        ],
        extra_headers=get_cache_control_header()
    )
    
    cache_time = time.time() - start_time
    print(f"✅ Cache hit: {cache_time:.2f}s")
    print(f"   Cache usage: creation={cache_response.usage.cache_creation_input_tokens}, read={cache_response.usage.cache_read_input_tokens}")
    
    # Summary
    print(f"\n📊 Speed Analysis:")
    print(f"   Minimal (5 words): {minimal_time:.2f}s")
    print(f"   Medium context: {medium_time:.2f}s") 
    print(f"   Large context: {large_time:.2f}s")
    print(f"   Cache hit: {cache_time:.2f}s")
    
    if cache_time < large_time:
        improvement = ((large_time - cache_time) / large_time) * 100
        print(f"   🚀 Cache improvement: {improvement:.1f}%")
    
    print(f"\n🎯 Diagnosis:")
    if minimal_time > 2.0:
        print("   ⚠️  Even minimal requests are slow - possible network/API issue")
    if medium_time > 4.0:
        print("   ⚠️  Medium context unusually slow - investigate context size/format")
    if large_response.usage.cache_creation_input_tokens > 0:
        print(f"   ✅ Cache creation working: {large_response.usage.cache_creation_input_tokens} tokens")
    if cache_response.usage.cache_read_input_tokens > 0:
        print(f"   ✅ Cache reading working: {cache_response.usage.cache_read_input_tokens} tokens")

if __name__ == "__main__":
    asyncio.run(test_api_speed()) 