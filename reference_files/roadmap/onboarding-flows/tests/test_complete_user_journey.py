#!/usr/bin/env python3
"""
End-to-end integration test for complete user journey
Tests: Intro → Creativity Test → Project Overview → General Chat
Verifies cross-session persistence and flow transitions
"""

import pytest
import os
import sys
from unittest.mock import patch, AsyncMock, MagicMock
from datetime import datetime, timezone, timedelta

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.simple_chat_handler import SimpleChatHandler, process_chat_message


class TestCompleteUserJourney:
    """Test complete user journey from intro to general conversation"""
    
    @pytest.fixture
    def mock_database_with_state_persistence(self):
        """Mock database that persists state across operations"""
        supabase = MagicMock()
        
        # State storage to simulate database persistence
        self.user_state = {
            'creativity_test_progress': {},
            'project_overview_progress': {},
            'creator_creativity_profiles': {},
            'project_overview': {},
            'conversation_memory': []
        }
        
        def mock_table_operations(table_name):
            mock_table = MagicMock()
            
            # Mock select operations based on current state
            def mock_select():
                mock_select_query = MagicMock()
                def mock_execute():
                    mock_result = MagicMock()
                    if table_name in self.user_state:
                        mock_result.data = list(self.user_state[table_name].values()) if isinstance(self.user_state[table_name], dict) else self.user_state[table_name]
                    else:
                        mock_result.data = []
                    return mock_result
                
                mock_select_query.eq.return_value.execute = mock_execute
                mock_select_query.eq.return_value.limit.return_value.execute = mock_execute
                mock_select_query.eq.return_value.order.return_value.limit.return_value.execute = mock_execute
                mock_select_query.execute = mock_execute
                return mock_select_query
            
            # Mock insert operations
            def mock_insert(data):
                mock_insert_query = MagicMock()
                def mock_execute():
                    # Simulate inserting data into state
                    if table_name not in self.user_state:
                        self.user_state[table_name] = {}
                    
                    if isinstance(data, dict):
                        data_id = data.get('id', f"generated-{len(self.user_state[table_name])}")
                        self.user_state[table_name][data_id] = data
                    elif isinstance(data, list):
                        for item in data:
                            item_id = item.get('id', f"generated-{len(self.user_state[table_name])}")
                            self.user_state[table_name][item_id] = item
                    
                    return MagicMock()
                
                mock_insert_query.execute = mock_execute
                return mock_insert_query
            
            # Mock update operations
            def mock_update(data):
                mock_update_query = MagicMock()
                def mock_eq(field):
                    mock_eq_query = MagicMock()
                    def mock_execute():
                        # Simulate updating data in state
                        if table_name in self.user_state:
                            for item_id, item in self.user_state[table_name].items():
                                if item.get(field.replace('eq.', '')) == data.get(field.replace('eq.', '')):
                                    item.update(data)
                        return MagicMock()
                    mock_eq_query.execute = mock_execute
                    return mock_eq_query
                mock_update_query.eq = mock_eq
                return mock_update_query
            
            mock_table.select = mock_select
            mock_table.insert = mock_insert
            mock_table.update = mock_update
            
            return mock_table
        
        supabase.table.side_effect = mock_table_operations
        return supabase
    
    @pytest.fixture
    def handler_with_persistent_db(self, mock_database_with_state_persistence):
        """Create handler with persistent database mock"""
        return SimpleChatHandler(mock_database_with_state_persistence)
    
    @pytest.mark.asyncio
    async def test_complete_user_journey_happy_path(self, handler_with_persistent_db):
        """Test complete happy path: intro → creativity → project → general"""
        
        with patch('src.simple_chat_handler.SimpleMemory') as mock_memory:
            with patch('src.simple_chat_handler.get_router') as mock_router:
                # Mock memory operations
                mock_memory_instance = AsyncMock()
                mock_memory_instance.add_message = AsyncMock()
                mock_memory_instance.get_context.return_value = {'messages': [], 'summaries': ''}
                mock_memory.return_value = mock_memory_instance
                
                # Mock LLM router for general conversation
                mock_router_instance = AsyncMock()
                mock_router_instance.chat_completion.return_value = "I'm here to help with your creative project!"
                mock_router.return_value = mock_router_instance
                
                user_id = "journey-test-user"
                thread_id = "journey-test-thread"
                
                # === INTRO FLOW ===
                
                # Stage 1: Initial greeting
                response = await handler_with_persistent_db.process_message(user_id, "Hello", thread_id)
                assert "Hi, I'm Hai" in response
                assert "What's your name" in response
                
                # Stage 2: Name collection
                response = await handler_with_persistent_db.process_message(user_id, "I'm Sarah", thread_id)
                assert "Nice to meet you, Sarah" in response
                assert "creative project" in response
                
                # Stage 3: Project info
                response = await handler_with_persistent_db.process_message(user_id, "I want to write a children's book", thread_id)
                assert "That sounds like something worth building" in response
                
                # Stage 4: Accountability experience
                response = await handler_with_persistent_db.process_message(user_id, "No, I've never had a coach", thread_id)
                assert "creative personality test" in response
                
                # Stage 5: Questions about the process
                response = await handler_with_persistent_db.process_message(user_id, "Sounds good, no questions", thread_id)
                assert "ready to start that creative personality test" in response or "creativity archetype assessment" in response
                
                # Stage 6: Ready to proceed
                response = await handler_with_persistent_db.process_message(user_id, "I'm ready", thread_id)
                assert "Perfect, Sarah!" in response
                assert "Question 1 of 12" in response
                assert "When starting a new creative project" in response
                
                # === CREATIVITY TEST ===
                
                # Answer all 12 questions (mix of answers to get diverse archetype)
                creativity_answers = ['A', 'B', 'A', 'C', 'A', 'D', 'A', 'E', 'A', 'F', 'A', 'B']
                
                for i, answer in enumerate(creativity_answers):
                    response = await handler_with_persistent_db.process_message(user_id, answer, thread_id)
                    
                    if i < len(creativity_answers) - 1:
                        # Should show next question
                        assert f"Question {i+2} of 12" in response or "Question" in response
                    else:
                        # Should complete test and show results
                        assert "🎉 Fantastic!" in response
                        assert "Creative Archetype" in response
                        assert "let's talk about your specific project" in response
                
                # === PROJECT OVERVIEW ===
                
                # Start project overview
                response = await handler_with_persistent_db.process_message(user_id, "Yes, let's plan my project", thread_id)
                assert "Topic 1 of 8" in response
                assert "Project Vision & Core Concept" in response
                
                # Answer all 8 project topics
                project_answers = [
                    "I want to write a children's book about friendship and inclusion",
                    "It will be a picture book for ages 4-8",
                    "My target audience is young children and their parents",
                    "I want to help kids feel less alone and more accepting of differences",
                    "My biggest challenge is finding time to write consistently",
                    "I'd like to finish the first draft in 6 months",
                    "I have basic writing skills but need to learn about illustration",
                    "My first step is to outline the story and create character sketches"
                ]
                
                for i, answer in enumerate(project_answers):
                    response = await handler_with_persistent_db.process_message(user_id, answer, thread_id)
                    
                    if i < len(project_answers) - 1:
                        # Should show next topic
                        assert f"topic {i+1} of 8 complete" in response or f"topic {i+2} of 8" in response
                    else:
                        # Should complete project overview
                        assert "🎉 Excellent!" in response
                        assert "completed your comprehensive project overview" in response
                        assert "What would you like to work on first?" in response
                
                # === GENERAL CONVERSATION ===
                
                # Now in general chat mode
                response = await handler_with_persistent_db.process_message(user_id, "How can you help me with my book?", thread_id)
                assert "I'm here to help with your creative project!" in response
                
                # Verify router was called for general conversation
                mock_router_instance.chat_completion.assert_called()
    
    @pytest.mark.asyncio
    async def test_user_journey_with_skips(self, handler_with_persistent_db):
        """Test user journey with skip functionality"""
        
        with patch('src.simple_chat_handler.SimpleMemory') as mock_memory:
            mock_memory_instance = AsyncMock()
            mock_memory_instance.add_message = AsyncMock()
            mock_memory_instance.get_context.return_value = {'messages': [], 'summaries': ''}
            mock_memory.return_value = mock_memory_instance
            
            user_id = "skip-test-user"
            thread_id = "skip-test-thread"
            
            # Complete intro flow quickly
            await handler_with_persistent_db.process_message(user_id, "Hello", thread_id)
            await handler_with_persistent_db.process_message(user_id, "I'm Alex", thread_id)
            await handler_with_persistent_db.process_message(user_id, "I want to make a podcast", thread_id)
            await handler_with_persistent_db.process_message(user_id, "No coach experience", thread_id)
            await handler_with_persistent_db.process_message(user_id, "No questions", thread_id)
            await handler_with_persistent_db.process_message(user_id, "I'm ready", thread_id)
            
            # Skip creativity test
            response = await handler_with_persistent_db.process_message(user_id, "skip this for now", thread_id)
            assert "No worries!" in response
            assert "skip the creativity test" in response
            assert "What creative project are you working on" in response
            
            # Should go to project overview
            response = await handler_with_persistent_db.process_message(user_id, "Let's plan my podcast", thread_id)
            assert "Topic 1 of 8" in response
            assert "Project Vision & Core Concept" in response
            
            # Skip project planning too
            response = await handler_with_persistent_db.process_message(user_id, "skip this for now", thread_id)
            assert "No problem!" in response
            assert "skip the project planning" in response
    
    @pytest.mark.asyncio
    async def test_cross_session_persistence(self, handler_with_persistent_db):
        """Test that progress persists across different message sessions"""
        
        with patch('src.simple_chat_handler.SimpleMemory') as mock_memory:
            mock_memory_instance = AsyncMock()
            mock_memory_instance.add_message = AsyncMock()
            mock_memory_instance.get_context.return_value = {'messages': [], 'summaries': ''}
            mock_memory.return_value = mock_memory_instance
            
            user_id = "persistence-test-user"
            thread_id = "persistence-test-thread"
            
            # === SESSION 1: Start intro ===
            response = await handler_with_persistent_db.process_message(user_id, "Hello", thread_id)
            assert "Hi, I'm Hai" in response
            
            response = await handler_with_persistent_db.process_message(user_id, "I'm Jordan", thread_id)
            assert "Nice to meet you, Jordan" in response
            
            # === SESSION 2: Continue intro (simulating user return) ===
            response = await handler_with_persistent_db.process_message(user_id, "I want to create a mobile app", thread_id)
            assert "That sounds like something worth building" in response
            
            # Complete intro
            await handler_with_persistent_db.process_message(user_id, "No coach", thread_id)
            await handler_with_persistent_db.process_message(user_id, "No questions", thread_id)
            response = await handler_with_persistent_db.process_message(user_id, "I'm ready", thread_id)
            assert "Perfect, Jordan!" in response
            assert "Question 1 of 12" in response
            
            # === SESSION 3: Progress through creativity test ===
            await handler_with_persistent_db.process_message(user_id, "A", thread_id)
            await handler_with_persistent_db.process_message(user_id, "B", thread_id)
            response = await handler_with_persistent_db.process_message(user_id, "C", thread_id)
            assert "Question 4 of 12" in response or "Question" in response
            
            # === SESSION 4: Complete creativity test ===
            # Answer remaining questions
            remaining_answers = ['D', 'E', 'F', 'A', 'B', 'C', 'D', 'E', 'F']
            for answer in remaining_answers:
                response = await handler_with_persistent_db.process_message(user_id, answer, thread_id)
            
            assert "🎉 Fantastic!" in response
            assert "Creative Archetype" in response
    
    @pytest.mark.asyncio
    async def test_skip_expiration_logic(self, handler_with_persistent_db):
        """Test that skip periods expire correctly"""
        
        with patch('src.simple_chat_handler.SimpleMemory') as mock_memory:
            mock_memory_instance = AsyncMock()
            mock_memory_instance.add_message = AsyncMock()
            mock_memory_instance.get_context.return_value = {'messages': [], 'summaries': ''}
            mock_memory.return_value = mock_memory_instance
            
            user_id = "skip-expiry-test-user"
            thread_id = "skip-expiry-test-thread"
            
            # Complete intro to get to creativity test
            await handler_with_persistent_db.process_message(user_id, "Hello", thread_id)
            await handler_with_persistent_db.process_message(user_id, "I'm Casey", thread_id)
            await handler_with_persistent_db.process_message(user_id, "I want to write music", thread_id)
            await handler_with_persistent_db.process_message(user_id, "No coach", thread_id)
            await handler_with_persistent_db.process_message(user_id, "No questions", thread_id)
            await handler_with_persistent_db.process_message(user_id, "I'm ready", thread_id)
            
            # Skip creativity test (sets 24h skip period)
            response = await handler_with_persistent_db.process_message(user_id, "skip this for now", thread_id)
            assert "skip the creativity test" in response
            
            # Simulate time passing (mock expired skip)
            with patch('src.simple_chat_handler.datetime') as mock_datetime:
                # Mock current time as 25 hours later
                future_time = datetime.now(timezone.utc) + timedelta(hours=25)
                mock_datetime.now.return_value = future_time
                mock_datetime.timezone = timezone
                
                response = await handler_with_persistent_db.process_message(user_id, "Hello again", thread_id)
                
                # Should offer to retry creativity test
                assert "it's been a day since we last talked about the creativity test" in response
                assert "Would you like to try it now" in response


class TestMultiUserIsolation:
    """Test that different users don't interfere with each other"""
    
    @pytest.fixture
    def shared_database_mock(self):
        """Mock database that handles multiple users"""
        supabase = MagicMock()
        
        # Shared state storage for multiple users
        self.global_state = {}
        
        def mock_table_operations(table_name):
            mock_table = MagicMock()
            
            def mock_select():
                mock_select_query = MagicMock()
                
                def mock_eq(user_id):
                    mock_eq_query = MagicMock()
                    
                    def mock_execute():
                        mock_result = MagicMock()
                        # Filter data by user_id
                        user_data = []
                        if table_name in self.global_state:
                            for item in self.global_state[table_name].values():
                                if item.get('user_id') == user_id or item.get('id') == user_id:
                                    user_data.append(item)
                        mock_result.data = user_data
                        return mock_result
                    
                    mock_eq_query.execute = mock_execute
                    mock_eq_query.limit.return_value.execute = mock_execute
                    mock_eq_query.order.return_value.limit.return_value.execute = mock_execute
                    return mock_eq_query
                
                mock_select_query.eq = mock_eq
                return mock_select_query
            
            def mock_insert(data):
                mock_insert_query = MagicMock()
                
                def mock_execute():
                    if table_name not in self.global_state:
                        self.global_state[table_name] = {}
                    
                    data_id = data.get('user_id') or data.get('id') or f"generated-{len(self.global_state[table_name])}"
                    self.global_state[table_name][data_id] = data
                    return MagicMock()
                
                mock_insert_query.execute = mock_execute
                return mock_insert_query
            
            mock_table.select = mock_select
            mock_table.insert = mock_insert
            mock_table.update = lambda data: MagicMock(eq=lambda field: MagicMock(execute=lambda: MagicMock()))
            
            return mock_table
        
        supabase.table.side_effect = mock_table_operations
        return supabase
    
    @pytest.mark.asyncio
    async def test_user_isolation(self, shared_database_mock):
        """Test that multiple users can use the system simultaneously without interference"""
        
        with patch('src.simple_chat_handler.SimpleMemory') as mock_memory:
            mock_memory_instance = AsyncMock()
            mock_memory_instance.add_message = AsyncMock()
            mock_memory_instance.get_context.return_value = {'messages': [], 'summaries': ''}
            mock_memory.return_value = mock_memory_instance
            
            # Create handlers for different users
            handler1 = SimpleChatHandler(shared_database_mock)
            handler2 = SimpleChatHandler(shared_database_mock)
            
            user1_id = "user-1"
            user2_id = "user-2"
            thread1_id = "thread-1"
            thread2_id = "thread-2"
            
            # User 1 starts intro
            response1 = await handler1.process_message(user1_id, "Hello", thread1_id)
            assert "Hi, I'm Hai" in response1
            
            # User 2 starts intro
            response2 = await handler2.process_message(user2_id, "Hi there", thread2_id)
            assert "Hi, I'm Hai" in response2
            
            # User 1 provides name
            response1 = await handler1.process_message(user1_id, "I'm Alice", thread1_id)
            assert "Nice to meet you, Alice" in response1
            
            # User 2 provides different name
            response2 = await handler2.process_message(user2_id, "I'm Bob", thread2_id)
            assert "Nice to meet you, Bob" in response2
            
            # Verify users are in same stage but with different names
            assert "Alice" not in response2
            assert "Bob" not in response1


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 