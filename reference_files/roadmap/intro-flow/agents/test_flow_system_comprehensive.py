#!/usr/bin/env python3
"""
Comprehensive Flow System Tests
Following the implementation guide exactly as specified by the senior developer
Tests all flow progression, resume functionality, database state, skip functionality, and edge cases
"""

import asyncio
import pytest
import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, Any

from src.flow_based_chat_handler import FlowBasedChatHandler, chat, get_flow_status, reset_flows
from src.flow_manager import FlowManager
from src.intro_flow_handler import IntroFlowHandler  
from src.creativity_flow_handler import CreativityFlowHandler
from src.project_flow_handler import ProjectFlowHandler
from src.config import Config
from supabase import create_client

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestFlowSystemComprehensive:
    """Comprehensive test suite for flow-based system following implementation guide"""
    
    @pytest.fixture
    def supabase_client(self):
        """Create supabase client for testing"""
        return create_client(Config.SUPABASE_URL, Config.SUPABASE_SERVICE_KEY)
    
    @pytest.fixture
    def test_user_id(self):
        """Use the specific user ID from implementation guide"""
        return "8bb85a19-8b6f-45f1-a495-cd66aabb9d52"
    
    @pytest.fixture
    def fresh_user_id(self):
        """Generate fresh user ID for isolated tests"""
        return str(uuid.uuid4())
    
    async def cleanup_user(self, supabase_client, user_id: str):
        """Clean up test user data completely"""
        # Reset using the system function first
        await reset_flows(supabase_client, user_id)
        
        # Additional cleanup to ensure clean state
        tables_to_clear = [
            'creator_profiles',
            'memory',
            'conversations',
            'longterm_memory'
        ]
        
        for table in tables_to_clear:
            try:
                supabase_client.table(table)\
                    .delete()\
                    .eq('user_id', user_id)\
                    .execute()
            except Exception as e:
                logger.warning(f"Could not clear {table}: {e}")

    # Test 1: Flow Progression (Following Implementation Guide)
    @pytest.mark.asyncio
    async def test_flow_progression_new_user(self, supabase_client, test_user_id):
        """Test 1: New user sees intro - Following implementation guide exactly"""
        await self.cleanup_user(supabase_client, test_user_id)
        
        # Test message as specified in guide
        response = await chat(supabase_client, test_user_id, "Hi", "test_thread_1")
        
        # Expected: Intro welcome message
        assert "Hi! I'm Hai, your creative partner" in response
        assert "Fridays at Four" in response
        
        # Verify flow status
        status = await get_flow_status(supabase_client, test_user_id)
        assert status['current_flow'] == 'intro'
        assert not status['status']['intro_complete']

    @pytest.mark.asyncio
    async def test_skip_functionality(self, supabase_client, test_user_id):
        """Test 2: Skip functionality - Following implementation guide exactly"""
        await self.cleanup_user(supabase_client, test_user_id)
        
        # Start intro flow first
        await chat(supabase_client, test_user_id, "Hi", "test_thread_1")
        
        # Test skip as specified in guide
        skip_response = await chat(supabase_client, test_user_id, "skip this for now", "test_thread_1")
        
        # Expected: "No problem! I'll ask you again tomorrow..."
        assert "No problem!" in skip_response or "I'll check back" in skip_response
        assert "tomorrow" in skip_response.lower()

    @pytest.mark.asyncio
    async def test_complete_intro_flow(self, supabase_client, fresh_user_id):
        """Test 3: Complete intro flow - Continue conversation until ready for creativity test"""
        await self.cleanup_user(supabase_client, fresh_user_id)
        
        intro_messages = [
            "Hi there!",
            "I'm working on a creative project",
            "How does your memory work exactly?",
            "That sounds great! What makes this different from other platforms?",
            "I love that you'll adapt to my style. Tell me more about creative support.",
            "Perfect! I'm ready to start the creativity test!"
        ]
        
        for message in intro_messages[:-1]:
            response = await chat(supabase_client, fresh_user_id, message, "test_thread")
            # Should still be in intro
            status = await get_flow_status(supabase_client, fresh_user_id)
            assert status['current_flow'] == 'intro'
        
        # Final message should trigger creativity test
        final_response = await chat(supabase_client, fresh_user_id, intro_messages[-1], "test_thread")
        
        # Should transition to creativity test
        status = await get_flow_status(supabase_client, fresh_user_id)
        assert status['current_flow'] == 'creativity'
        assert "Question 1 of 11" in final_response

    @pytest.mark.asyncio
    async def test_creativity_test_progression(self, supabase_client, fresh_user_id):
        """Test 4: Answer creativity test questions - Respond with A, B, C, or D for each question"""
        await self.cleanup_user(supabase_client, fresh_user_id)
        
        # Complete intro flow first
        await chat(supabase_client, fresh_user_id, "Hi", "test_thread")
        await chat(supabase_client, fresh_user_id, "I understand everything, let's start!", "test_thread")
        
        # Answer all 11 creativity questions
        creativity_answers = ['A', 'B', 'C', 'D', 'A', 'B', 'C', 'D', 'A', 'B', 'C']
        
        for i, answer in enumerate(creativity_answers, 1):
            response = await chat(supabase_client, fresh_user_id, answer, "test_thread")
            
            if i < 11:
                # Should still be in creativity test
                assert f"Question {i+1} of 11" in response
            else:
                # Should complete and show results
                assert "You're" in response and "archetype" in response.lower()
                # Should transition to project planning
                status = await get_flow_status(supabase_client, fresh_user_id)
                assert status['current_flow'] == 'project'

    @pytest.mark.asyncio 
    async def test_project_planning_completion(self, supabase_client, fresh_user_id):
        """Test 5: Complete project planning - Answer 8 topics naturally"""
        await self.cleanup_user(supabase_client, fresh_user_id)
        
        # Complete intro and creativity first
        await self._complete_intro_and_creativity(supabase_client, fresh_user_id)
        
        # Project planning answers for 8 topics
        project_answers = [
            "I want to write a children's book about friendship and acceptance",
            "It's a picture book for ages 4-7 years old", 
            "My target audience is young children and their parents who value diversity",
            "I want to create something that helps kids understand differences and be kind",
            "My biggest challenge is finding the right illustrator and getting published",
            "I'd like to finish the manuscript in 3 months and find a publisher in 6 months",
            "I have writing experience but need help with publishing and illustration",
            "I want to start by outlining the story structure and writing the first draft"
        ]
        
        for i, answer in enumerate(project_answers, 1):
            response = await chat(supabase_client, fresh_user_id, answer, "test_thread")
            
            if i < 8:
                # Should show next topic
                assert f"Topic {i+1} of 8" in response
            else:
                # Should complete project planning
                assert "Excellent!" in response or "complete" in response.lower()
                # Should transition to main chat
                status = await get_flow_status(supabase_client, fresh_user_id)
                assert status['current_flow'] == 'main_chat'

    # Test 2: Resume Functionality (Following Implementation Guide)
    @pytest.mark.asyncio
    async def test_resume_mid_intro(self, supabase_client, fresh_user_id):
        """Start intro flow, then disconnect - Should resume from exact same spot"""
        await self.cleanup_user(supabase_client, fresh_user_id)
        
        # Start intro conversation
        await chat(supabase_client, fresh_user_id, "Hi there!", "test_thread_1")
        await chat(supabase_client, fresh_user_id, "I'm working on a book", "test_thread_1")
        
        # Verify mid-intro state
        status = await get_flow_status(supabase_client, fresh_user_id)
        assert status['current_flow'] == 'intro'
        
        # "Disconnect" and come back with different thread
        response = await chat(supabase_client, fresh_user_id, "Where were we?", "test_thread_2")
        
        # Should still be in intro flow, continuing naturally
        status = await get_flow_status(supabase_client, fresh_user_id)
        assert status['current_flow'] == 'intro'

    @pytest.mark.asyncio
    async def test_resume_mid_creativity(self, supabase_client, fresh_user_id):
        """Start creativity test, disconnect mid-way - Should resume from exact question"""
        await self.cleanup_user(supabase_client, fresh_user_id)
        
        # Complete intro and start creativity
        await self._complete_intro(supabase_client, fresh_user_id)
        
        # Answer first 5 questions
        for answer in ['A', 'B', 'C', 'D', 'A']:
            await chat(supabase_client, fresh_user_id, answer, "test_thread_1")
        
        # "Disconnect" and resume
        response = await chat(supabase_client, fresh_user_id, "What was the question?", "test_thread_2")
        
        # Should show question 6 of 11
        assert "Question 6 of 11" in response

    @pytest.mark.asyncio
    async def test_resume_mid_project(self, supabase_client, fresh_user_id):
        """Start project planning, disconnect mid-way - Should resume from exact topic"""
        await self.cleanup_user(supabase_client, fresh_user_id)
        
        # Complete intro and creativity
        await self._complete_intro_and_creativity(supabase_client, fresh_user_id)
        
        # Answer first 3 project topics
        project_start_answers = [
            "I want to write a children's book",
            "It's a picture book format",
            "Target audience is kids ages 4-7"
        ]
        
        for answer in project_start_answers:
            await chat(supabase_client, fresh_user_id, answer, "test_thread_1")
        
        # "Disconnect" and resume
        response = await chat(supabase_client, fresh_user_id, "What topic are we on?", "test_thread_2")
        
        # Should show topic 4 of 8
        assert "Topic 4 of 8" in response

    # Test 3: Database State (Following Implementation Guide)
    @pytest.mark.asyncio
    async def test_intro_database_state(self, supabase_client, fresh_user_id):
        """Check intro progress in creativity_test_progress table"""
        await self.cleanup_user(supabase_client, fresh_user_id)
        
        # Start intro flow
        await chat(supabase_client, fresh_user_id, "Hi", "test_thread")
        
        # Check database state as specified in guide
        result = supabase_client.table('creativity_test_progress')\
            .select('*')\
            .eq('user_id', fresh_user_id)\
            .execute()
        
        assert len(result.data) == 1
        record = result.data[0]
        assert record['user_id'] == fresh_user_id
        assert record['has_seen_intro'] is False  # Not complete yet
        assert 'intro_data' in record

    @pytest.mark.asyncio
    async def test_creativity_database_state(self, supabase_client, fresh_user_id):
        """Check creativity results in creator_creativity_profiles table"""
        await self.cleanup_user(supabase_client, fresh_user_id)
        
        # Complete intro and creativity test
        await self._complete_intro_and_creativity(supabase_client, fresh_user_id)
        
        # Check creativity results as specified in guide
        result = supabase_client.table('creator_creativity_profiles')\
            .select('*')\
            .eq('user_id', fresh_user_id)\
            .execute()
        
        assert len(result.data) == 1
        profile = result.data[0]
        assert profile['user_id'] == fresh_user_id
        assert profile['archetype'] in ['Big Picture Visionary', 'Creative Sprinter', 'Steady Builder', 
                                      'Collaborative Creator', 'Independent Maker', 'Intuitive Artist']
        assert isinstance(profile['archetype_score'], (int, float))

    @pytest.mark.asyncio
    async def test_project_overview_database_state(self, supabase_client, fresh_user_id):
        """Check project overview in project_overview table"""
        await self.cleanup_user(supabase_client, fresh_user_id)
        
        # Complete full flow
        await self._complete_full_flow(supabase_client, fresh_user_id)
        
        # Check project overview as specified in guide
        result = supabase_client.table('project_overview')\
            .select('*')\
            .eq('user_id', fresh_user_id)\
            .execute()
        
        assert len(result.data) == 1
        project = result.data[0]
        assert project['user_id'] == fresh_user_id
        assert project['project_name'] is not None
        assert project['project_type'] is not None
        assert 'goals' in project
        assert 'challenges' in project

    # Edge Cases (Following Implementation Guide)
    @pytest.mark.asyncio
    async def test_answer_extraction_edge_cases(self, supabase_client, fresh_user_id):
        """Test 1: User types answer in words: 'I choose option A' → extracts 'A'"""
        await self.cleanup_user(supabase_client, fresh_user_id)
        await self._complete_intro(supabase_client, fresh_user_id)
        
        # Test different answer formats
        answer_formats = [
            "I choose option A",
            "A is my answer", 
            "A)",
            "A.",
            "The answer is A",
            "a"  # lowercase
        ]
        
        creativity_handler = CreativityFlowHandler(supabase_client, fresh_user_id)
        
        for answer_text in answer_formats:
            extracted = creativity_handler._extract_answer(answer_text)
            assert extracted == 'A', f"Failed to extract A from: {answer_text}"

    @pytest.mark.asyncio
    async def test_multiple_skip_phrases(self, supabase_client, fresh_user_id):
        """Test 2: Multiple skip phrases: 'not now', 'maybe later', 'skip' all work"""
        skip_phrases = [
            "skip this for now",
            "not now", 
            "maybe later",
            "not right now",
            "another time",
            "pass",
            "not interested",
            "remind me later"
        ]
        
        flow_manager = FlowManager(supabase_client, fresh_user_id)
        
        for phrase in skip_phrases:
            assert flow_manager.detect_skip_intent(phrase), f"Failed to detect skip in: {phrase}"

    @pytest.mark.asyncio
    async def test_invalid_creativity_answers(self, supabase_client, fresh_user_id):
        """Test 4: Invalid answers: Prompts for A, B, C, or D"""
        await self.cleanup_user(supabase_client, fresh_user_id)
        await self._complete_intro(supabase_client, fresh_user_id)
        
        # Send invalid answer
        response = await chat(supabase_client, fresh_user_id, "I don't know", "test_thread")
        
        # Should prompt for valid answer
        assert any(phrase in response for phrase in ["Please choose A, B, C, or D", "A, B, C, or D"])

    @pytest.mark.asyncio
    async def test_network_failure_recovery(self, supabase_client, fresh_user_id):
        """Test 3: Network failures: Saves progress after each message"""
        await self.cleanup_user(supabase_client, fresh_user_id)
        
        # Start creativity test
        await self._complete_intro(supabase_client, fresh_user_id)
        
        # Answer some questions
        await chat(supabase_client, fresh_user_id, "A", "test_thread")
        await chat(supabase_client, fresh_user_id, "B", "test_thread")
        
        # Check that progress was saved
        status = await get_flow_status(supabase_client, fresh_user_id)
        flow_data = status.get('flow_data', {})
        assert len(flow_data.get('responses', {})) == 2

    @pytest.mark.asyncio
    async def test_concurrent_requests(self, supabase_client, fresh_user_id):
        """Test 6: Concurrent requests: Database handles with user_id uniqueness"""
        await self.cleanup_user(supabase_client, fresh_user_id)
        
        # Send multiple concurrent messages (simulating race condition)
        tasks = []
        for i in range(3):
            task = chat(supabase_client, fresh_user_id, f"Hi message {i}", f"thread_{i}")
            tasks.append(task)
        
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # All should succeed (no database constraint violations)
        for response in responses:
            assert isinstance(response, str), f"Got exception: {response}"

    # Performance Tests (Following Implementation Guide)
    @pytest.mark.asyncio
    async def test_flow_routing_performance(self, supabase_client, fresh_user_id):
        """Performance: Flow routing should be 10-50ms (DB queries only)"""
        await self.cleanup_user(supabase_client, fresh_user_id)
        
        flow_manager = FlowManager(supabase_client, fresh_user_id)
        
        # Time the flow routing
        start_time = datetime.now()
        flow_type, flow_data = await flow_manager.get_next_flow()
        end_time = datetime.now()
        
        duration_ms = (end_time - start_time).total_seconds() * 1000
        
        # Should be fast DB queries only (10-50ms target)
        assert duration_ms < 100, f"Flow routing took {duration_ms}ms, expected <100ms"
        assert flow_type == 'intro'  # Fresh user should start with intro

    # Helper Methods
    async def _complete_intro(self, supabase_client, user_id: str):
        """Helper: Complete intro flow"""
        await chat(supabase_client, user_id, "Hi", "test_thread")
        await chat(supabase_client, user_id, "I understand everything, ready to start!", "test_thread")

    async def _complete_intro_and_creativity(self, supabase_client, user_id: str):
        """Helper: Complete intro and creativity flows"""
        await self._complete_intro(supabase_client, user_id)
        
        # Answer all creativity questions
        for answer in ['A', 'B', 'C', 'D', 'A', 'B', 'C', 'D', 'A', 'B', 'C']:
            await chat(supabase_client, user_id, answer, "test_thread")

    async def _complete_full_flow(self, supabase_client, user_id: str):
        """Helper: Complete all flows"""
        await self._complete_intro_and_creativity(supabase_client, user_id)
        
        # Answer all project questions
        project_answers = [
            "I want to write a children's book",
            "Picture book format",
            "Kids ages 4-7",
            "Help children understand friendship",
            "Finding an illustrator",
            "3 months for draft",
            "I have writing experience",
            "Start with story outline"
        ]
        
        for answer in project_answers:
            await chat(supabase_client, user_id, answer, "test_thread")


# Integration test that can be run standalone
async def run_comprehensive_tests():
    """Run all tests for manual execution"""
    from src.config import Config
    
    supabase = create_client(Config.SUPABASE_URL, Config.SUPABASE_SERVICE_KEY)
    test_user = "8bb85a19-8b6f-45f1-a495-cd66aabb9d52"
    
    test_suite = TestFlowSystemComprehensive()
    
    try:
        logger.info("🧪 Running Comprehensive Flow System Tests")
        logger.info("=" * 60)
        
        # Test flow progression
        logger.info("\n1. Testing flow progression...")
        await test_suite.test_flow_progression_new_user(supabase, test_user)
        logger.info("✅ Flow progression test passed")
        
        # Test skip functionality
        logger.info("\n2. Testing skip functionality...")
        await test_suite.test_skip_functionality(supabase, test_user)
        logger.info("✅ Skip functionality test passed")
        
        # Test database state
        logger.info("\n3. Testing database state...")
        fresh_user = str(uuid.uuid4())
        await test_suite.test_intro_database_state(supabase, fresh_user)
        logger.info("✅ Database state test passed")
        
        # Test edge cases
        logger.info("\n4. Testing edge cases...")
        await test_suite.test_answer_extraction_edge_cases(supabase, fresh_user)
        await test_suite.test_multiple_skip_phrases(supabase, fresh_user)
        logger.info("✅ Edge cases test passed")
        
        # Test performance
        logger.info("\n5. Testing performance...")
        await test_suite.test_flow_routing_performance(supabase, fresh_user)
        logger.info("✅ Performance test passed")
        
        logger.info("\n🎉 All comprehensive tests passed!")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(run_comprehensive_tests()) 