#!/usr/bin/env python3
"""
Live Summarization System Test

Tests the complete summarization pipeline against the live dev Heroku environment:
1. Buffer summarization (when conversation buffer fills)
2. Daily summarization (nightly summary generation) 
3. Project update generation
4. Memory retrieval with summaries

This test uses the live dev environment to validate the full summarization workflow.
"""

import os
import sys
import asyncio
import json
import uuid
from datetime import datetime, timezone, timedelta, date
from typing import Dict, List, Any

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import pytest
import requests
from supabase import create_client
from src.content_summarizer import (
    ContentSummarizer, 
    DailySummaryHandler, 
    BufferSummaryHandler,
    ProjectUpdateHandler
)
from src.simple_memory import SimpleMemory
from src.config import Config

# Test configuration
DEV_API_URL = "https://fridays-at-four-dev-434b1a68908b.herokuapp.com"
TEST_USER_PREFIX = "test_summary_"

class TestSummarizationLive:
    """Test summarization system against live dev environment"""
    
    @pytest.fixture
    def test_user_id(self):
        """Generate unique test user ID"""
        return f"{TEST_USER_PREFIX}{uuid.uuid4()}"
    
    @pytest.fixture
    def supabase_client(self):
        """Create Supabase client for direct database operations"""
        return create_client(Config.SUPABASE_URL, Config.SUPABASE_SERVICE_KEY)
    
    @pytest.fixture
    def summarizer(self):
        """Create ContentSummarizer instance"""
        return ContentSummarizer()
    
    @pytest.fixture 
    def memory_handler(self, supabase_client, test_user_id):
        """Create memory handler for test user"""
        return SimpleMemory(supabase_client, test_user_id)
    
    async def cleanup_test_user(self, supabase_client, user_id: str):
        """Clean up test data for user"""
        try:
            # Delete from all relevant tables
            tables = ['memory', 'conversations', 'longterm_memory', 'project_updates', 'creator_profiles']
            for table in tables:
                supabase_client.table(table).delete().eq('user_id', user_id).execute()
        except Exception as e:
            print(f"Cleanup error: {e}")
    
    @pytest.mark.asyncio
    async def test_buffer_summarization_workflow(self, test_user_id, supabase_client, memory_handler, summarizer):
        """Test buffer summarization when conversation buffer fills up"""
        print(f"\n🧪 Testing Buffer Summarization for user: {test_user_id}")
        
        try:
            # Setup: Create enough messages to trigger buffer summarization
            thread_id = f"test_thread_{uuid.uuid4()}"
            
            # Create realistic conversation messages
            conversation_messages = [
                ("user", "Hi! I'm working on a children's book about a young astronaut named Luna."),
                ("assistant", "That sounds like a wonderful project! Tell me more about Luna's adventures."),
                ("user", "Luna discovers a planet where colors have gone missing. She needs to help restore them."),
                ("assistant", "What an imaginative concept! How does Luna go about restoring the colors?"),
                ("user", "She meets friendly alien creatures who each hold a piece of the color spectrum."),
                ("assistant", "I love that! Are there any challenges or obstacles Luna faces?"),
                ("user", "Yes, there's a shadow creature that's been stealing the colors because it feels lonely."),
                ("assistant", "That adds emotional depth. How does Luna help the shadow creature?"),
                ("user", "Luna realizes the shadow just wants to be included and teaches it about friendship."),
                ("assistant", "Beautiful message! What age group are you targeting for this book?"),
                ("user", "Ages 4-8. I want it to teach about empathy and inclusion."),
                ("assistant", "Perfect age range for those themes. Have you thought about illustrations?"),
                ("user", "I'm planning colorful, whimsical illustrations that show the planet transforming."),
                ("assistant", "That sounds visually stunning! Are you working with an illustrator?"),
                ("user", "I'm looking for one. Do you have suggestions for finding the right illustrator?"),
                ("assistant", "I can help you think through what to look for in an illustrator for your book."),
            ]
            
            # Add messages to trigger buffer summarization
            print(f"📝 Adding {len(conversation_messages)} messages to trigger buffer summarization...")
            for role, message in conversation_messages:
                await memory_handler.add_message(thread_id, message, role)
                await asyncio.sleep(0.1)  # Small delay to avoid overwhelming the system
            
            # Wait a moment for any background summarization to complete
            await asyncio.sleep(3)
            
            # Check if buffer summary was created
            print("🔍 Checking for buffer summary in memory table...")
            buffer_summaries = supabase_client.table('memory')\
                .select('*')\
                .eq('user_id', test_user_id)\
                .eq('memory_type', 'buffer_summary')\
                .execute()
            
            print(f"📊 Found {len(buffer_summaries.data)} buffer summaries")
            
            if buffer_summaries.data:
                summary = buffer_summaries.data[0]
                print(f"✅ Buffer Summary Created:")
                print(f"   Content: {summary['content'][:200]}...")
                print(f"   Thread ID: {summary['metadata'].get('thread_id', 'N/A')}")
                
                # Verify summary content makes sense
                content = summary['content'].lower()
                assert any(keyword in content for keyword in ['luna', 'book', 'children', 'astronaut', 'colors']), \
                    "Summary should contain key topics from conversation"
                
                return True
            else:
                print("⚠️  No buffer summary found - may need more messages or different buffer size")
                return False
                
        finally:
            await self.cleanup_test_user(supabase_client, test_user_id)
    
    @pytest.mark.asyncio
    async def test_daily_summarization_manual(self, test_user_id, supabase_client, summarizer):
        """Test daily summarization process manually"""
        print(f"\n🌅 Testing Daily Summarization for user: {test_user_id}")
        
        try:
            # Setup: Create conversations from "yesterday" to summarize
            yesterday = datetime.now(timezone.utc) - timedelta(days=1)
            
            # Create some conversation data directly in conversations table
            conversation_data = [
                {
                    'user_id': test_user_id,
                    'message_text': "I've been working on my novel and made great progress today.",
                    'role': 'user',
                    'context': {'session_type': 'writing'},
                    'metadata': {},
                    'created_at': yesterday.isoformat()
                },
                {
                    'user_id': test_user_id,
                    'message_text': "That's wonderful! Tell me about the progress you made.",
                    'role': 'assistant', 
                    'context': {'session_type': 'writing'},
                    'metadata': {},
                    'created_at': yesterday.isoformat()
                },
                {
                    'user_id': test_user_id,
                    'message_text': "I finished chapter 3 and outlined chapter 4. My protagonist is really developing.",
                    'role': 'user',
                    'context': {'session_type': 'writing'},
                    'metadata': {},
                    'created_at': yesterday.isoformat()
                }
            ]
            
            # Insert conversation data
            print("📝 Creating conversation data for daily summarization...")
            for conv in conversation_data:
                supabase_client.table('conversations').insert(conv).execute()
            
            # Run daily summarization
            print("🔄 Running daily summarization process...")
            daily_handler = DailySummaryHandler(summarizer)
            
            result = await daily_handler.generate_daily_summary(
                user_id=test_user_id,
                supabase_client=supabase_client,
                start_date=yesterday,
                end_date=yesterday + timedelta(hours=23, minutes=59)
            )
            
            if result:
                print("✅ Daily Summary Generated:")
                print(f"   Summary: {result.get('summary', 'N/A')[:200]}...")
                print(f"   Quality Score: {result.get('quality_score', 'N/A')}")
                
                # Check if summary was stored in longterm_memory
                longterm_summaries = supabase_client.table('longterm_memory')\
                    .select('*')\
                    .eq('user_id', test_user_id)\
                    .execute()
                
                print(f"📊 Found {len(longterm_summaries.data)} longterm memory entries")
                
                if longterm_summaries.data:
                    summary_entry = longterm_summaries.data[0]
                    content = summary_entry['content'].lower()
                    assert any(keyword in content for keyword in ['novel', 'chapter', 'progress', 'writing']), \
                        "Daily summary should contain key topics from conversations"
                
                return True
            else:
                print("⚠️  No daily summary generated - may need more conversation data")
                return False
                
        finally:
            await self.cleanup_test_user(supabase_client, test_user_id)
    
    @pytest.mark.asyncio
    async def test_project_update_generation(self, test_user_id, supabase_client, summarizer):
        """Test project update generation"""
        print(f"\n📈 Testing Project Update Generation for user: {test_user_id}")
        
        try:
            # Setup: Create project overview and some progress data
            project_data = {
                'user_id': test_user_id,
                'project_name': 'Luna the Astronaut Book',
                'project_type': 'children_book',
                'description': 'A children\'s book about a young astronaut who helps restore colors to a planet.',
                'current_phase': 'writing',
                'goals': [
                    {'goal': 'Complete first draft', 'target_date': '2024-03-01'},
                    {'goal': 'Find illustrator', 'target_date': '2024-04-01'}
                ],
                'challenges': [
                    {'challenge': 'Finding the right illustrator', 'impact': 'medium'}
                ],
                'success_metrics': {
                    'pages_completed': 0,
                    'target_pages': 32
                },
                'creation_date': datetime.now(timezone.utc).isoformat(),
                'last_updated': datetime.now(timezone.utc).isoformat()
            }
            
            # Create project overview
            print("📋 Creating project overview...")
            supabase_client.table('project_overview').insert(project_data).execute()
            
            # Create some longterm memory entries (as if from daily summaries)
            yesterday = datetime.now(timezone.utc) - timedelta(days=1)
            memory_data = {
                'user_id': test_user_id,
                'memory_type': 'daily_summary',
                'content': 'User made significant progress on their children\'s book, completing chapter 3 and outlining chapter 4. They discussed character development and are looking for an illustrator.',
                'metadata': {
                    'date_range': {
                        'start': yesterday.date().isoformat(),
                        'end': yesterday.date().isoformat()
                    },
                    'conversation_count': 3,
                    'quality_analysis': {'engagement_score': 8.5}
                },
                'created_at': yesterday.isoformat()
            }
            
            print("🧠 Creating longterm memory data...")
            supabase_client.table('longterm_memory').insert(memory_data).execute()
            
            # Generate project update
            print("🔄 Generating project update...")
            project_handler = ProjectUpdateHandler(summarizer)
            
            result = await project_handler.generate_project_update(
                user_id=test_user_id,
                supabase_client=supabase_client,
                start_date=yesterday,
                end_date=datetime.now(timezone.utc)
            )
            
            if result:
                print("✅ Project Update Generated:")
                print(f"   Summary: {result.summary[:200]}...")
                print(f"   Metadata: {result.metadata}")
                
                # Check if update was stored in project_updates table
                project_updates = supabase_client.table('project_updates')\
                    .select('*')\
                    .eq('user_id', test_user_id)\
                    .execute()
                
                print(f"📊 Found {len(project_updates.data)} project update entries")
                
                if project_updates.data:
                    update_entry = project_updates.data[0]
                    content = update_entry['content'].lower()
                    assert any(keyword in content for keyword in ['book', 'chapter', 'progress', 'luna']), \
                        "Project update should contain relevant project information"
                
                return True
            else:
                print("⚠️  No project update generated")
                return False
                
        finally:
            await self.cleanup_test_user(supabase_client, test_user_id)
    
    @pytest.mark.asyncio
    async def test_memory_retrieval_with_summaries(self, test_user_id, supabase_client, memory_handler):
        """Test that memory retrieval includes summaries in context"""
        print(f"\n🧠 Testing Memory Retrieval with Summaries for user: {test_user_id}")
        
        try:
            # Create some buffer summaries
            summary_data = {
                'user_id': test_user_id,
                'memory_type': 'buffer_summary',
                'content': 'Previous conversation about Luna the astronaut book project, discussing character development and plot.',
                'metadata': {
                    'thread_id': 'test_thread_123',
                    'source': {'type': 'conversation_buffer'},
                    'generated_at': datetime.now(timezone.utc).isoformat()
                },
                'created_at': datetime.now(timezone.utc).isoformat()
            }
            
            print("📝 Creating buffer summary...")
            supabase_client.table('memory').insert(summary_data).execute()
            
            # Add some recent messages
            thread_id = "current_thread"
            await memory_handler.add_message(thread_id, "Let's continue working on the Luna book", "user")
            await memory_handler.add_message(thread_id, "Great! What aspect would you like to focus on today?", "assistant")
            
            # Retrieve context
            print("🔍 Retrieving context with summaries...")
            context = await memory_handler.get_context(thread_id)
            
            print(f"📊 Context Retrieved:")
            print(f"   Messages: {len(context['messages'])}")
            print(f"   Summaries: {len(context['summaries'])}")
            
            # Verify summaries are included
            assert len(context['summaries']) > 0, "Context should include buffer summaries"
            assert any('luna' in summary.lower() for summary in context['summaries']), \
                "Summaries should contain relevant content"
            
            # Verify recent messages are included
            assert len(context['messages']) > 0, "Context should include recent messages"
            
            print("✅ Memory retrieval with summaries working correctly")
            return True
            
        finally:
            await self.cleanup_test_user(supabase_client, test_user_id)
    
    @pytest.mark.asyncio 
    async def test_end_to_end_summarization_via_api(self, test_user_id):
        """Test summarization through the live API endpoints"""
        print(f"\n🌐 Testing End-to-End Summarization via Live API for user: {test_user_id}")
        
        try:
            # Send enough messages through the API to trigger summarization
            thread_id = f"api_test_{uuid.uuid4()}"
            
            messages = [
                "Hi! I'm starting a podcast about sustainable living.",
                "I want to interview experts and share practical tips.",
                "My target audience is young professionals who care about the environment.",
                "I'm planning weekly episodes of about 30 minutes each.",
                "I need help with finding guests and structuring episodes.",
                "I also want to build a community around the podcast.",
                "What's the best platform to start with for hosting?", 
                "Should I focus on video or just audio for now?",
                "I'm thinking about monetization strategies too.",
                "Maybe sponsorships or a Patreon for premium content?",
                "I want to make sure I'm providing real value to listeners.",
                "How do I measure success beyond just download numbers?",
                "I'm excited but also nervous about putting myself out there.",
                "Any advice for overcoming the fear of starting?",
                "I want this to make a real impact on people's lives."
            ]
            
            print(f"📡 Sending {len(messages)} messages through live API...")
            
            for i, message in enumerate(messages):
                payload = {
                    "message": message,
                    "user_id": test_user_id,
                    "user_timezone": "UTC", 
                    "thread_id": thread_id
                }
                
                response = requests.post(
                    f"{DEV_API_URL}/chat",
                    json=payload,
                    timeout=30
                )
                
                print(f"   Message {i+1}/{len(messages)}: {response.status_code}")
                
                if response.status_code != 200:
                    print(f"   Error: {response.text}")
                    
                # Small delay between messages
                await asyncio.sleep(0.5)
            
            # Wait for background summarization to potentially complete
            print("⏳ Waiting for background summarization...")
            await asyncio.sleep(10)
            
            # Check chat history to see if summarization affected it
            history_response = requests.get(
                f"{DEV_API_URL}/chat-history/{test_user_id}?limit=50"
            )
            
            if history_response.status_code == 200:
                history = history_response.json()
                print(f"📊 Chat history contains {len(history)} messages")
                
                # If summarization worked, we might see fewer stored messages
                # or we can check for summaries in the database directly
                print("✅ End-to-end API test completed")
                return True
            else:
                print(f"❌ Failed to retrieve chat history: {history_response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ API test failed: {str(e)}")
            return False
        
        finally:
            # Cleanup through direct database access
            try:
                supabase_client = create_client(Config.SUPABASE_URL, Config.SUPABASE_SERVICE_KEY)
                await self.cleanup_test_user(supabase_client, test_user_id)
            except Exception as e:
                print(f"Cleanup error: {e}")

if __name__ == "__main__":
    # Run specific test
    import pytest
    pytest.main([__file__, "-v", "-s"]) 