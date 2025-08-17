#!/usr/bin/env python3
"""
Documentation Caching Test

Creates a test user with rich project documentation and tests prompt caching
with real content that exceeds the 1024 token minimum.
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
from src.simple_memory import SimpleMemory
from src.config import Config
from src.context_formatter import format_static_context_for_caching, get_cache_control_header
from anthropic import AsyncAnthropic
import json

async def test_doc_caching():
    """Test prompt caching with real documentation content"""
    
    print("📚 Testing Documentation-Based Prompt Caching")
    print(f"⏰ Test started at: {datetime.now()}")
    
    # Create test user
    test_user_id = str(uuid.uuid4())
    print(f"👤 Created test user: {test_user_id}")
    
    supabase_client = create_client(Config.SUPABASE_URL, Config.SUPABASE_SERVICE_KEY)
    
    try:
        # Create creator profile
        print("📝 Creating creator profile...")
        memory_handler = SimpleMemory(supabase_client, test_user_id)
        await memory_handler.ensure_creator_profile(test_user_id)
        
        # Read some of our documentation files
        print("📖 Reading documentation files...")
        
        # Read memory bank files for rich content
        memory_bank_content = ""
        memory_files = [
            "memory-bank/productContext.md",
            "memory-bank/systemPatterns.md", 
            "memory-bank/userJourney.md"
        ]
        
        for file_path in memory_files:
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                    memory_bank_content += f"\n\n## {file_path}\n{content}"
            except FileNotFoundError:
                print(f"⚠️  File not found: {file_path}")
        
        # Create rich project overview
        project_overview_data = {
            'user_id': test_user_id,
            'project_name': 'Fridays at Four - AI Creative Platform',
            'project_type': 'Software Development',
            'description': f'Production-ready AI-powered creative project management platform. Tech Stack: FastAPI, Supabase, Claude API, React, Heroku. Team: Solo developer with AI assistance.\n\nMemory Bank Documentation:\n{memory_bank_content}',
            'current_phase': 'Production optimization and caching implementation',
            'goals': [
                'Build production-ready AI creative platform',
                'Implement conversational agent with memory',
                'Create intuitive user experience for creative professionals',
                'Deploy scalable backend with FastAPI and Supabase'
            ],
            'challenges': [
                'Optimizing Claude API performance and caching',
                'Managing conversation memory and context',
                'Balancing AI capabilities with user control',
                'Ensuring data persistence and reliability'
            ],
            'success_metrics': {
                'technical': 'Sub-2s API response times, 99%+ uptime',
                'user_experience': 'Natural conversation flow, memory continuity',
                'business': 'User engagement and creative output quality'
            },
            'timeline': '3 months MVP, 6 months production',
            'weekly_commitment': '40+ hours',
            'resources_needed': 'Claude API credits, Heroku hosting, development tools',
            'working_style': 'Iterative development with continuous testing'
        }
        
        print("💾 Inserting rich project overview...")
        result = supabase_client.table('project_overview').insert(project_overview_data).execute()
        print(f"✅ Project overview created with {len(memory_bank_content)} characters of context")
        
        # Test 1: Direct Claude API with large context
        print("\n🧪 Test 1: Direct Claude API with documentation context...")
        
        client = AsyncAnthropic(api_key=Config.ANTHROPIC_API_KEY)
        
                # Create large context using our documentation
        large_context = f"""
# Fridays at Four - AI Creative Platform Documentation

## Project Overview
{project_overview_data['project_name']} is a {project_overview_data['description'][:200]}...

**Goals:**
{chr(10).join('- ' + goal for goal in project_overview_data['goals'])}

**Current Challenges:**
{chr(10).join('- ' + challenge for challenge in project_overview_data['challenges'])}

**Current Phase:** {project_overview_data['current_phase']}
**Timeline:** {project_overview_data['timeline']}
**Working Style:** {project_overview_data['working_style']}

## Memory Bank Documentation
{memory_bank_content}

## Current Development Focus
We are optimizing Claude API performance through prompt caching implementation.
The system uses FastAPI backend with Supabase database for conversation memory.
Key patterns include singleton agent architecture and memory injection strategies.
"""
        
        print(f"📏 Context size: {len(large_context)} characters (~{len(large_context.split())} words)")
        
        # First API call - should create cache
        start_time = time.time()
        
        first_response = await client.messages.create(
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
                {
                    "role": "user", 
                    "content": "Based on this documentation, what are the top 3 technical priorities for optimizing the platform?"
                }
            ],
            extra_headers=get_cache_control_header()
        )
        
        first_time = time.time() - start_time
        print(f"✅ First call: {first_time:.2f}s")
        print(f"   Cache creation: {first_response.usage.cache_creation_input_tokens} tokens")
        print(f"   Cache read: {first_response.usage.cache_read_input_tokens} tokens")
        print(f"   Input tokens: {first_response.usage.input_tokens} tokens")
        
        # Second API call - should hit cache
        start_time = time.time()
        
        second_response = await client.messages.create(
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
                {
                    "role": "user",
                    "content": "What specific caching optimizations should we implement next?"
                }
            ],
            extra_headers=get_cache_control_header()
        )
        
        second_time = time.time() - start_time
        print(f"✅ Second call: {second_time:.2f}s")
        print(f"   Cache creation: {second_response.usage.cache_creation_input_tokens} tokens")
        print(f"   Cache read: {second_response.usage.cache_read_input_tokens} tokens")
        print(f"   Input tokens: {second_response.usage.input_tokens} tokens")
        
        # Test 2: API integration test
        print("\n🌐 Test 2: API integration test with rich context...")
        
        import requests
        
        # Test API call with rich user context
        start_time = time.time()
        
        api_response = requests.post(
            "http://localhost:8000/chat",
            json={
                "user_id": test_user_id,
                "message": "Given our platform's architecture, what's the best approach for implementing real-time notifications?",
                "thread_id": f"test-doc-thread-{uuid.uuid4()}"
            },
            timeout=30
        )
        
        api_time = time.time() - start_time
        print(f"✅ API call: {api_time:.2f}s")
        
        if api_response.status_code == 200:
            response_data = api_response.json()
            print(f"   Response length: {len(response_data.get('response', ''))} characters")
            print(f"   Response preview: {response_data.get('response', '')[:150]}...")
        else:
            print(f"❌ API call failed: {api_response.status_code}")
            print(f"   Error: {api_response.text}")
        
        # Calculate improvements
        if first_time > 0 and second_time > 0:
            cache_improvement = ((first_time - second_time) / first_time) * 100
            print(f"\n📊 Performance Analysis:")
            print(f"   First call (cache creation): {first_time:.2f}s")
            print(f"   Second call (cache hit): {second_time:.2f}s")
            print(f"   🚀 Cache improvement: {cache_improvement:.1f}%")
            
            if first_response.usage.cache_creation_input_tokens > 0:
                print(f"   ✅ Cache creation working: {first_response.usage.cache_creation_input_tokens} tokens")
            if second_response.usage.cache_read_input_tokens > 0:
                print(f"   ✅ Cache reading working: {second_response.usage.cache_read_input_tokens} tokens")
        
        print(f"\n🎯 Caching Assessment:")
        if first_response.usage.cache_creation_input_tokens > 1000:
            print("   ✅ Successfully created cache with substantial content")
        elif first_response.usage.cache_creation_input_tokens > 0:
            print("   ⚠️  Cache created but may be below optimal size")
        else:
            print("   ❌ No cache creation detected")
            
        if second_response.usage.cache_read_input_tokens > 1000:
            print("   ✅ Successfully reading from cache")
        elif second_response.usage.cache_read_input_tokens > 0:
            print("   ⚠️  Cache reading but may be partial")
        else:
            print("   ❌ No cache reading detected")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Cleanup
        print("\n🧹 Cleaning up test data...")
        cleanup_tables = [
            ('project_overview', 'user_id'),
            ('memory', 'user_id'),
            ('conversations', 'user_id'),
            ('longterm_memory', 'user_id'),
            ('creator_profiles', 'id')
        ]
        
        for table, id_column in cleanup_tables:
            try:
                result = supabase_client.table(table).delete().eq(id_column, test_user_id).execute()
                print(f"✅ Cleaned up {table}")
            except Exception as e:
                print(f"Cleanup error for {table}: {e}")

if __name__ == "__main__":
    asyncio.run(test_doc_caching()) 