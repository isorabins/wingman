#!/usr/bin/env python3
"""
LangChain to Claude Migration Verification Tests

This test suite verifies that all critical functionality is preserved
after migrating from LangChain to direct Claude API integration.

Real-world tests that actually connect to:
- Production Supabase database
- Claude API 
- Production API endpoints
"""

import asyncio
import json
import uuid
import requests
from datetime import datetime
from typing import Dict, List, Any
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import Config
from src.simple_memory import SimpleMemory
from src.claude_agent import interact_with_agent, interact_with_agent_stream
from src.project_planning import (
    should_trigger_project_planning,
    check_user_has_project_overview,
    monitor_conversation_for_project_completion
)
from src.content_summarizer import ContentSummarizer, BufferSummaryHandler
from src.claude_client_simple import SimpleClaudeClient, ClaudeCredentials
from supabase import create_client

# Test configuration
API_BASE_URL = "https://fridays-at-four-c9c6b7a513be.herokuapp.com"
SUPABASE_CLIENT = create_client(Config.SUPABASE_URL, Config.SUPABASE_SERVICE_KEY)

class MigrationVerificationTests:
    """Comprehensive test suite for migration verification"""
    
    def __init__(self):
        self.test_user_ids = []
        self.passed_tests = 0
        self.failed_tests = 0
        
    def create_test_user(self) -> str:
        """Create a unique test user ID"""
        user_id = str(uuid.uuid4())
        self.test_user_ids.append(user_id)
        return user_id
    
    async def cleanup_test_data(self):
        """Clean up all test data"""
        print("\n🧹 Cleaning up test data...")
        for user_id in self.test_user_ids:
            # Delete from all relevant tables
            tables = ['conversations', 'memory', 'project_overview', 'creator_profiles']
            for table in tables:
                try:
                    SUPABASE_CLIENT.table(table).delete().eq('user_id', user_id).execute()
                except:
                    try:
                        SUPABASE_CLIENT.table(table).delete().eq('id', user_id).execute()
                    except:
                        pass
        print("✅ Test cleanup complete")
    
    def assert_test(self, condition: bool, test_name: str, details: str = ""):
        """Assert a test condition and track results"""
        if condition:
            print(f"✅ {test_name}")
            if details:
                print(f"   {details}")
            self.passed_tests += 1
        else:
            print(f"❌ {test_name}")
            if details:
                print(f"   {details}")
            self.failed_tests += 1
    
    async def test_claude_client_integration(self):
        """Test 1: Direct Claude API client functionality"""
        print("\n🧪 Test 1: Claude Client Integration")
        
        try:
            credentials = ClaudeCredentials()
            client = SimpleClaudeClient(credentials)
            
            # Test non-streaming message
            messages = [{"role": "user", "content": "Say 'test successful' if you receive this."}]
            response = await client.send_message(
                messages=messages,
                model="claude-3-5-sonnet-20241022",
                max_tokens=100,
                temperature=0.3,
                stream=False
            )
            
            self.assert_test(
                "test successful" in response.lower(),
                "Non-streaming Claude API integration",
                f"Response: {response[:50]}..."
            )
            
            # Test streaming message
            full_response = ""
            stream_generator = await client.send_message(
                messages=messages,
                model="claude-3-5-sonnet-20241022", 
                max_tokens=100,
                temperature=0.3,
                stream=True
            )
            
            async for chunk in stream_generator:
                full_response += chunk
            
            self.assert_test(
                "test successful" in full_response.lower(),
                "Streaming Claude API integration",
                f"Streamed response: {full_response[:50]}..."
            )
            
        except Exception as e:
            self.assert_test(False, "Claude client integration", f"Error: {e}")
    
    async def test_memory_system_preservation(self):
        """Test 2: Memory system functionality"""
        print("\n🧪 Test 2: Memory System Preservation")
        
        user_id = self.create_test_user()
        thread_id = f"test_thread_{user_id}"
        
        try:
            memory = SimpleMemory(SUPABASE_CLIENT, user_id)
            
            # Test auto-dependency creation
            await memory.ensure_creator_profile(user_id)
            
            # Verify creator profile creation
            profile_result = SUPABASE_CLIENT.table('creator_profiles')\
                .select('id').eq('id', user_id).execute()
            
            self.assert_test(
                len(profile_result.data) > 0,
                "Auto-dependency creation (creator profile)",
                f"Profile created for user {user_id[:8]}..."
            )
            
            # Test message storage
            await memory.add_message(thread_id, "Test message 1", "user")
            await memory.add_message(thread_id, "Test response 1", "assistant")
            
            # Test context retrieval
            context = await memory.get_context(thread_id)
            
            self.assert_test(
                len(context["messages"]) == 2,
                "Message storage and retrieval",
                f"Stored and retrieved {len(context['messages'])} messages"
            )
            
            self.assert_test(
                context["messages"][0]["role"] == "user",
                "Message format preservation",
                "User message role correctly preserved"
            )
            
        except Exception as e:
            self.assert_test(False, "Memory system preservation", f"Error: {e}")
    
    async def test_project_onboarding_logic(self):
        """Test 3: Project onboarding logic preservation"""
        print("\n🧪 Test 3: Project Onboarding Logic")
        
        user_id = self.create_test_user()
        
        try:
            # Test onboarding trigger for new user
            should_onboard = await should_trigger_project_planning(SUPABASE_CLIENT, user_id)
            
            self.assert_test(
                should_onboard == True,
                "Onboarding trigger for new user",
                "New user correctly identified as needing onboarding"
            )
            
            # Test conversation completion monitoring
            mock_conversation = [
                {"role": "user", "content": "I want to create a mobile app"},
                {"role": "assistant", "content": "Great! Let's start with Topic 1 of 8: Project Description"},
                {"role": "user", "content": "It's a fitness app for runners"},
                {"role": "assistant", "content": "Topic 2 of 8: What are your main goals?"},
                {"role": "user", "content": "I want 10,000 users in first year"},
                {"role": "assistant", "content": "Perfect! We've covered all 8 topics and I have a comprehensive project overview"}
            ]
            
            completion_detected = await monitor_conversation_for_project_completion(
                SUPABASE_CLIENT, user_id, mock_conversation
            )
            
            self.assert_test(
                completion_detected == True,
                "Project completion detection",
                "Completion signals correctly identified"
            )
            
        except Exception as e:
            self.assert_test(False, "Project onboarding logic", f"Error: {e}")
    
    async def test_content_summarization_migration(self):
        """Test 4: Content summarization with Claude"""
        print("\n🧪 Test 4: Content Summarization Migration")
        
        user_id = self.create_test_user()
        thread_id = f"summary_test_{user_id}"
        
        try:
            # Test ContentSummarizer with Claude
            summarizer = ContentSummarizer()
            
            test_content = """
            User: I need help with my creative writing project.
            Assistant: I'd be happy to help! What kind of writing are you working on?
            User: I'm writing a science fiction novel about space exploration.
            Assistant: That sounds exciting! What's the main conflict in your story?
            User: The crew discovers an alien artifact that changes everything.
            Assistant: Interesting premise! How far along are you in the writing process?
            """
            
            # Test map-reduce summarization
            result = await summarizer.ainvoke(test_content)
            
            self.assert_test(
                "final_summary" in result and len(result["final_summary"]) > 0,
                "Claude-based map-reduce summarization",
                f"Generated summary: {result['final_summary'][:50]}..."
            )
            
            # Test BufferSummaryHandler
            buffer_handler = BufferSummaryHandler(summarizer)
            
            mock_messages = [
                {"content": "user: Hello, I need help with my project", "created_at": "2024-01-01T10:00:00Z"},
                {"content": "assistant: I'd be happy to help! What's your project about?", "created_at": "2024-01-01T10:01:00Z"},
                {"content": "user: It's a mobile app for fitness tracking", "created_at": "2024-01-01T10:02:00Z"}
            ]
            
            summary_result = await buffer_handler.create_buffer_summary(
                thread_id, mock_messages, user_id, SUPABASE_CLIENT
            )
            
            self.assert_test(
                summary_result.error is None and len(summary_result.summary) > 0,
                "Buffer summary handler with Claude",
                f"Generated buffer summary: {summary_result.summary[:50]}..."
            )
            
        except Exception as e:
            self.assert_test(False, "Content summarization migration", f"Error: {e}")
    
    async def test_agent_integration_comprehensive(self):
        """Test 5: Complete agent integration with all features"""
        print("\n🧪 Test 5: Comprehensive Agent Integration")
        
        user_id = self.create_test_user()
        thread_id = f"agent_test_{user_id}"
        
        try:
            # Test non-streaming agent interaction
            response = await interact_with_agent(
                user_input="I want to start a creative writing project about fantasy novels",
                user_id=user_id,
                user_timezone="UTC",
                thread_id=thread_id,
                supabase_client=SUPABASE_CLIENT,
                context={}
            )
            
            self.assert_test(
                len(response) > 0 and "project" in response.lower(),
                "Non-streaming agent interaction",
                f"Response generated: {response[:50]}..."
            )
            
            # Test streaming agent interaction
            full_streaming_response = ""
            async for chunk in interact_with_agent_stream(
                user_input="Tell me more about character development in fantasy novels",
                user_id=user_id,
                user_timezone="UTC", 
                thread_id=thread_id,
                supabase_client=SUPABASE_CLIENT,
                context={}
            ):
                full_streaming_response += chunk
            
            self.assert_test(
                len(full_streaming_response) > 0,
                "Streaming agent interaction",
                f"Streaming response: {full_streaming_response[:50]}..."
            )
            
            # Test memory persistence after interactions
            memory = SimpleMemory(SUPABASE_CLIENT, user_id)
            context = await memory.get_context(thread_id)
            
            self.assert_test(
                len(context["messages"]) >= 4,  # Should have both user inputs and agent responses
                "Memory persistence during agent interactions",
                f"Persisted {len(context['messages'])} messages"
            )
            
        except Exception as e:
            self.assert_test(False, "Comprehensive agent integration", f"Error: {e}")
    
    async def test_api_endpoints_functionality(self):
        """Test 6: API endpoints still work with migrated backend"""
        print("\n🧪 Test 6: API Endpoints Functionality")
        
        user_id = self.create_test_user()
        
        try:
            # Test chat endpoint
            chat_payload = {
                "message": "I need help planning a creative project",
                "user_id": user_id,
                "user_timezone": "UTC",
                "thread_id": f"api_test_{user_id}"
            }
            
            response = requests.post(
                f"{API_BASE_URL}/chat",
                json=chat_payload,
                timeout=30
            )
            
            self.assert_test(
                response.status_code == 200,
                "Chat endpoint functionality",
                f"Status: {response.status_code}"
            )
            
            if response.status_code == 200:
                response_data = response.json()
                self.assert_test(
                    "response" in response_data and len(response_data["response"]) > 0,
                    "Chat endpoint response format",
                    f"Response: {response_data['response'][:50]}..."
                )
            
            # Test project overview endpoint
            project_response = requests.get(
                f"{API_BASE_URL}/project-overview/{user_id}",
                timeout=10
            )
            
            self.assert_test(
                project_response.status_code == 200,
                "Project overview endpoint",
                f"Status: {project_response.status_code}"
            )
            
        except Exception as e:
            self.assert_test(False, "API endpoints functionality", f"Error: {e}")
    
    async def test_database_schema_integrity(self):
        """Test 7: Database operations maintain schema integrity"""
        print("\n🧪 Test 7: Database Schema Integrity")
        
        user_id = self.create_test_user()
        
        try:
            # Test all table operations work as expected
            memory = SimpleMemory(SUPABASE_CLIENT, user_id)
            await memory.ensure_creator_profile(user_id)
            
            # Test conversations table
            conversation_data = {
                'user_id': user_id,
                'message_text': 'Test message for schema verification',
                'role': 'user',
                'context': {'thread_id': 'schema_test'},
                'metadata': {},
                'created_at': datetime.now().isoformat()
            }
            
            conv_result = SUPABASE_CLIENT.table('conversations').insert(conversation_data).execute()
            
            self.assert_test(
                len(conv_result.data) > 0,
                "Conversations table schema integrity",
                "Conversation record inserted successfully"
            )
            
            # Test memory table
            memory_data = {
                'user_id': user_id,
                'memory_type': 'message',
                'content': 'user: Test message for memory schema',
                'metadata': {'thread_id': 'schema_test'},
                'created_at': datetime.now().isoformat()
            }
            
            memory_result = SUPABASE_CLIENT.table('memory').insert(memory_data).execute()
            
            self.assert_test(
                len(memory_result.data) > 0,
                "Memory table schema integrity",
                "Memory record inserted successfully"
            )
            
            # Test foreign key relationships
            profile_check = SUPABASE_CLIENT.table('creator_profiles')\
                .select('id').eq('id', user_id).execute()
            
            self.assert_test(
                len(profile_check.data) > 0,
                "Foreign key relationship integrity",
                "Creator profile exists for foreign key references"
            )
            
        except Exception as e:
            self.assert_test(False, "Database schema integrity", f"Error: {e}")
    
    async def test_performance_regression(self):
        """Test 8: Performance hasn't regressed significantly"""
        print("\n🧪 Test 8: Performance Regression Check")
        
        user_id = self.create_test_user()
        
        try:
            import time
            
            # Time a typical interaction
            start_time = time.time()
            
            response = await interact_with_agent(
                user_input="Quick test for performance timing",
                user_id=user_id,
                user_timezone="UTC",
                thread_id=f"perf_test_{user_id}",
                supabase_client=SUPABASE_CLIENT,
                context={}
            )
            
            end_time = time.time()
            response_time = end_time - start_time
            
            self.assert_test(
                response_time < 10.0,  # Should complete within 10 seconds
                "Response time performance",
                f"Response time: {response_time:.2f} seconds"
            )
            
            self.assert_test(
                len(response) > 0,
                "Response quality maintained",
                f"Generated response: {response[:50]}..."
            )
            
        except Exception as e:
            self.assert_test(False, "Performance regression check", f"Error: {e}")
    
    def print_test_summary(self):
        """Print final test results"""
        total_tests = self.passed_tests + self.failed_tests
        pass_rate = (self.passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"\n{'='*60}")
        print(f"🎯 MIGRATION VERIFICATION TEST RESULTS")
        print(f"{'='*60}")
        print(f"✅ Passed: {self.passed_tests}")
        print(f"❌ Failed: {self.failed_tests}")
        print(f"📊 Pass Rate: {pass_rate:.1f}%")
        
        if self.failed_tests == 0:
            print(f"\n🎉 ALL TESTS PASSED! Migration is successful.")
            print(f"✅ LangChain to Claude migration preserved all functionality.")
        else:
            print(f"\n⚠️  {self.failed_tests} tests failed. Review required.")
            print(f"❌ Migration may have introduced regressions.")
        
        return self.failed_tests == 0

async def main():
    """Run comprehensive migration verification tests"""
    print("🚀 Starting LangChain to Claude Migration Verification")
    print("=" * 60)
    
    tests = MigrationVerificationTests()
    
    try:
        # Run all verification tests
        await tests.test_claude_client_integration()
        await tests.test_memory_system_preservation()
        await tests.test_project_onboarding_logic()
        await tests.test_content_summarization_migration()
        await tests.test_agent_integration_comprehensive()
        await tests.test_api_endpoints_functionality()
        await tests.test_database_schema_integrity()
        await tests.test_performance_regression()
        
        # Print results
        success = tests.print_test_summary()
        
        return success
        
    finally:
        # Always cleanup test data
        await tests.cleanup_test_data()

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 