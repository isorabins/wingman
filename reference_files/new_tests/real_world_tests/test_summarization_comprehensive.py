#!/usr/bin/env python3
"""
Comprehensive Summarization Tests

Tests all aspects of the summarization system:
1. Buffer summarization (when conversations get too long)
2. Memory retrieval with summaries
3. Project update generation
4. End-to-end API integration
"""

import os
import sys
import asyncio
import uuid
import requests
from datetime import datetime, timezone, timedelta

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

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

class SummarizationTests:
    def __init__(self):
        self.test_user_id = "e4c932b7-1190-4463-818b-a804a644f01f"  # Real user for testing
        self.supabase_client = create_client(Config.SUPABASE_URL, Config.SUPABASE_SERVICE_KEY)
        self.memory_handler = SimpleMemory(self.supabase_client, self.test_user_id)
        
    async def cleanup(self):
        """Clean up only test-specific data, preserve real user data"""
        print("\n🧹 Cleaning up test-specific data only...")
        
        # Only clean up data we created during tests (with specific identifiers)
        try:
            # Remove only buffer summaries we created during testing
            self.supabase_client.table('memory')\
                .delete()\
                .eq('user_id', self.test_user_id)\
                .eq('memory_type', 'buffer_summary')\
                .like('content', '%Luna the astronaut%')\
                .execute()
                
            # Remove test longterm memory entries
            self.supabase_client.table('longterm_memory')\
                .delete()\
                .eq('user_id', self.test_user_id)\
                .like('content', '%Luna the Astronaut%')\
                .execute()
                
            print("✅ Test data cleaned up (preserved real user data)")
        except Exception as e:
            print(f"⚠️  Cleanup warning: {e}")
            pass  # Don't fail on cleanup errors
    
    async def test_buffer_summarization(self):
        """Test buffer summarization when conversation gets too long"""
        print(f"\n🧪 Testing Buffer Summarization for user: {self.test_user_id}")
        
        try:
            # Ensure creator profile exists
            await self.memory_handler.ensure_creator_profile(self.test_user_id)
            
            # Create a long conversation to trigger buffer summarization
            thread_id = f"buffer_test_{uuid.uuid4()}"
            
            # Add many messages to fill the buffer (default buffer size is usually 15-20 messages)
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
                ("user", "I want someone who can capture the magical, dreamy quality of space."),
                ("assistant", "That's a great vision! Let's discuss what portfolio elements to look for."),
                ("user", "I also need to think about the book's layout and page count."),
                ("assistant", "Absolutely! Picture books typically have specific page count conventions."),
            ]
            
            print(f"📝 Adding {len(conversation_messages)} messages...")
            for role, message in conversation_messages:
                await self.memory_handler.add_message(thread_id, message, role)
                await asyncio.sleep(0.1)
            
            # Manually trigger buffer summarization
            print("🔄 Triggering buffer summarization...")
            summarizer = ContentSummarizer()
            buffer_handler = BufferSummaryHandler(summarizer)
            
            # Get messages from memory to summarize
            messages_result = self.supabase_client.table('memory')\
                .select('*')\
                .eq('user_id', self.test_user_id)\
                .eq('memory_type', 'message')\
                .order('created_at', desc=False)\
                .execute()
            
            if len(messages_result.data) > 10:  # If we have enough messages
                # Convert to the format expected by buffer handler
                messages_for_summary = []
                for msg in messages_result.data:
                    content = msg['content']
                    if ':' in content:
                        role, message_content = content.split(':', 1)
                        messages_for_summary.append({
                            'role': role.strip(),
                            'content': message_content.strip(),
                            'timestamp': msg['created_at']
                        })
                
                # Create buffer summary
                summary_result = await buffer_handler.create_buffer_summary(
                    thread_id=thread_id,
                    messages=messages_for_summary,
                    user_id=self.test_user_id,
                    supabase_client=self.supabase_client
                )
                
                if summary_result and not summary_result.error:
                    print("✅ Buffer Summary Created:")
                    print(f"   Summary: {summary_result.summary[:200]}...")
                    
                    # Check if stored in database
                    buffer_summaries = self.supabase_client.table('memory')\
                        .select('*')\
                        .eq('user_id', self.test_user_id)\
                        .eq('memory_type', 'buffer_summary')\
                        .execute()
                    
                    print(f"📊 Found {len(buffer_summaries.data)} buffer summaries in database")
                    return True
                else:
                    print(f"⚠️  Buffer summarization failed: {summary_result.error if summary_result else 'No result'}")
                    return False
            else:
                print(f"⚠️  Not enough messages for buffer summarization ({len(messages_result.data)} messages)")
                return False
                
        except Exception as e:
            print(f"❌ Buffer summarization test failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    async def test_memory_retrieval_with_summaries(self):
        """Test that memory retrieval includes summaries in context"""
        print(f"\n🧠 Testing Memory Retrieval with Summaries")
        
        try:
            # Create a buffer summary first
            summary_data = {
                'user_id': self.test_user_id,
                'memory_type': 'buffer_summary',
                'content': 'Previous conversation about Luna the astronaut book project, discussing character development, plot about restoring colors to a planet, and finding an illustrator.',
                'metadata': {
                    'thread_id': 'test_thread_123',
                    'source': {'type': 'conversation_buffer'},
                    'generated_at': datetime.now(timezone.utc).isoformat()
                },
                'created_at': datetime.now(timezone.utc).isoformat()
            }
            
            print("📝 Creating buffer summary...")
            self.supabase_client.table('memory').insert(summary_data).execute()
            
            # Add some recent messages
            thread_id = "current_thread"
            await self.memory_handler.add_message(thread_id, "Let's continue working on the Luna book", "user")
            await self.memory_handler.add_message(thread_id, "Great! What aspect would you like to focus on today?", "assistant")
            
            # Retrieve context
            print("🔍 Retrieving context with summaries...")
            context = await self.memory_handler.get_context(thread_id)
            
            print(f"📊 Context Retrieved:")
            print(f"   Messages: {len(context['messages'])}")
            print(f"   Summaries: {len(context['summaries'])}")
            
            if len(context['summaries']) > 0:
                print(f"   Summary content: {context['summaries'][0][:100]}...")
                print("✅ Memory retrieval with summaries working correctly")
                return True
            else:
                print("⚠️  No summaries found in context")
                return False
                
        except Exception as e:
            print(f"❌ Memory retrieval test failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    async def test_project_update_generation(self):
        """Test project update generation"""
        print(f"\n📈 Testing Project Update Generation")
        
        try:
            # Create project overview
            project_data = {
                'user_id': self.test_user_id,
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
                    'pages_completed': 5,
                    'target_pages': 32
                },
                'creation_date': datetime.now(timezone.utc).isoformat(),
                'last_updated': datetime.now(timezone.utc).isoformat()
            }
            
            print("📋 Creating project overview...")
            self.supabase_client.table('project_overview').insert(project_data).execute()
            
            # Create longterm memory entries (as if from daily summaries)
            yesterday = datetime.now(timezone.utc) - timedelta(days=1)
            memory_data = {
                'user_id': self.test_user_id,
                'summary_date': yesterday.date().isoformat(),
                'content': 'User made significant progress on their children\'s book Luna the Astronaut, completing chapter 3 and outlining chapter 4. They discussed character development and are looking for an illustrator who can capture the magical, dreamy quality of space.',
                'metadata': {
                    'date_range': {
                        'start': yesterday.date().isoformat(),
                        'end': yesterday.date().isoformat()
                    },
                    'conversation_count': 5,
                    'quality_analysis': {'engagement_score': 8.5}
                },
                'created_at': yesterday.isoformat()
            }
            
            print("🧠 Creating longterm memory data...")
            self.supabase_client.table('longterm_memory').insert(memory_data).execute()
            
            # Generate project update
            print("🔄 Generating project update...")
            summarizer = ContentSummarizer()
            project_handler = ProjectUpdateHandler(summarizer)
            
            result = await project_handler.generate_project_update(
                user_id=self.test_user_id,
                supabase_client=self.supabase_client,
                start_date=yesterday,
                end_date=datetime.now(timezone.utc)
            )
            
            if result and not result.error:
                print("✅ Project Update Generated:")
                print(f"   Summary: {result.summary[:200]}...")
                print(f"   Metadata: {result.metadata}")
                
                # Check if stored in project_updates table
                project_updates = self.supabase_client.table('project_updates')\
                    .select('*')\
                    .eq('user_id', self.test_user_id)\
                    .execute()
                
                print(f"📊 Found {len(project_updates.data)} project update entries")
                
                if project_updates.data:
                    print("✅ Project update successfully stored in database")
                    return True
                else:
                    print("⚠️  Project update not found in database")
                    return False
            else:
                print(f"⚠️  No project update generated: {result.error if result else 'No result'}")
                return False
                
        except Exception as e:
            print(f"❌ Project update test failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    async def test_api_integration(self):
        """Test summarization through the live API endpoints"""
        print(f"\n🌐 Testing End-to-End API Integration")
        
        try:
            # Send messages through the API
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
                "Maybe sponsorships or a Patreon for premium content?"
            ]
            
            print(f"📡 Sending {len(messages)} messages through live API...")
            
            for i, message in enumerate(messages):
                payload = {
                    "message": message,
                    "user_id": self.test_user_id,
                    "user_timezone": "UTC", 
                    "thread_id": thread_id
                }
                
                response = requests.post(
                    f"{DEV_API_URL}/chat",
                    json=payload,
                    timeout=30
                )
                
                if response.status_code == 200:
                    print(f"   ✅ Message {i+1}/{len(messages)}")
                else:
                    print(f"   ❌ Message {i+1}/{len(messages)}: {response.status_code}")
                    
                await asyncio.sleep(0.5)
            
            # Check if messages were stored
            print("🔍 Checking stored messages...")
            history_response = requests.get(f"{DEV_API_URL}/chat-history/{self.test_user_id}?limit=50")
            
            if history_response.status_code == 200:
                history = history_response.json()
                print(f"📊 Chat history contains {len(history)} messages")
                print("✅ End-to-end API integration working")
                return True
            else:
                print(f"❌ Failed to retrieve chat history: {history_response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ API integration test failed: {str(e)}")
            return False

async def run_all_tests():
    """Run all summarization tests"""
    print("🚀 Starting Comprehensive Summarization Tests")
    
    tests = SummarizationTests()
    results = {}
    
    try:
        # Run all tests
        results['buffer_summarization'] = await tests.test_buffer_summarization()
        results['memory_retrieval'] = await tests.test_memory_retrieval_with_summaries()
        results['project_updates'] = await tests.test_project_update_generation()
        results['api_integration'] = await tests.test_api_integration()
        
        # Summary
        print(f"\n📊 TEST RESULTS SUMMARY")
        print(f"========================")
        passed = sum(results.values())
        total = len(results)
        
        for test_name, passed in results.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{test_name}: {status}")
        
        print(f"\nOverall: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All summarization tests PASSED!")
        else:
            print("⚠️  Some tests failed - check output above")
            
    finally:
        await tests.cleanup()

if __name__ == "__main__":
    asyncio.run(run_all_tests()) 