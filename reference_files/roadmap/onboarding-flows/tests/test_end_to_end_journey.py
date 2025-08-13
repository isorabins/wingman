#!/usr/bin/env python3
"""
End-to-end integration test for complete user journey
Tests: Intro → Creativity Test → Project Overview → General Chat
"""

import pytest
import os
import sys
from unittest.mock import patch, AsyncMock, MagicMock

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.simple_chat_handler import SimpleChatHandler


class TestEndToEndUserJourney:
    """Test complete user journey through all conversation flows"""
    
    @pytest.fixture
    def mock_persistent_db(self):
        """Mock database that maintains state across operations"""
        supabase = MagicMock()
        
        # State storage
        self.db_state = {
            'creativity_test_progress': {},
            'project_overview_progress': {},
            'creator_creativity_profiles': {},
            'project_overview': {}
        }
        
        def mock_table(table_name):
            mock_t = MagicMock()
            
            # Mock select
            def mock_select():
                mock_s = MagicMock()
                def mock_execute():
                    result = MagicMock()
                    result.data = list(self.db_state.get(table_name, {}).values())
                    return result
                mock_s.eq.return_value.execute = mock_execute
                mock_s.eq.return_value.limit.return_value.execute = mock_execute
                mock_s.execute = mock_execute
                return mock_s
            
            # Mock insert
            def mock_insert(data):
                mock_i = MagicMock()
                def mock_execute():
                    if table_name not in self.db_state:
                        self.db_state[table_name] = {}
                    
                    data_id = data.get('user_id', f"id-{len(self.db_state[table_name])}")
                    self.db_state[table_name][data_id] = data
                    return MagicMock()
                mock_i.execute = mock_execute
                return mock_i
            
            mock_t.select = mock_select
            mock_t.insert = mock_insert
            mock_t.update = lambda data: MagicMock(eq=lambda field: MagicMock(execute=lambda: MagicMock()))
            
            return mock_t
        
        supabase.table.side_effect = mock_table
        return supabase
    
    @pytest.fixture
    def handler(self, mock_persistent_db):
        return SimpleChatHandler(mock_persistent_db)
    
    @pytest.mark.asyncio
    async def test_complete_journey_happy_path(self, handler):
        """Test complete user journey from intro to general chat"""
        
        with patch('src.simple_chat_handler.SimpleMemory') as mock_memory:
            with patch('src.simple_chat_handler.get_router') as mock_router:
                # Mock memory
                mock_mem = AsyncMock()
                mock_mem.add_message = AsyncMock()
                mock_mem.get_context.return_value = {'messages': [], 'summaries': ''}
                mock_memory.return_value = mock_mem
                
                # Mock router for general chat
                mock_r = AsyncMock()
                mock_r.chat_completion.return_value = "I'm here to help!"
                mock_router.return_value = mock_r
                
                user_id = "test-journey-user"
                thread_id = "test-thread"
                
                # === INTRO FLOW ===
                response = await handler.process_message(user_id, "Hello", thread_id)
                assert "Hi, I'm Hai" in response
                
                response = await handler.process_message(user_id, "I'm Sarah", thread_id)
                assert "Nice to meet you, Sarah" in response
                
                # Skip through remaining intro stages
                await handler.process_message(user_id, "I want to write a book", thread_id)
                await handler.process_message(user_id, "No coach experience", thread_id)
                await handler.process_message(user_id, "No questions", thread_id)
                
                response = await handler.process_message(user_id, "I'm ready", thread_id)
                assert "Perfect, Sarah!" in response
                assert "Question 1 of 12" in response
                
                # === CREATIVITY TEST ===
                # Answer all 12 questions
                for i in range(12):
                    response = await handler.process_message(user_id, "A", thread_id)
                
                # Should complete test
                assert "🎉 Fantastic!" in response
                assert "Creative Archetype" in response
                
                # === PROJECT OVERVIEW ===
                response = await handler.process_message(user_id, "Let's plan my project", thread_id)
                assert "Topic 1 of 8" in response
                
                # Answer all 8 topics
                for i in range(8):
                    response = await handler.process_message(user_id, f"Answer to topic {i+1}", thread_id)
                
                # Should complete project overview
                assert "🎉 Excellent!" in response
                assert "comprehensive project overview" in response
                
                # === GENERAL CONVERSATION ===
                response = await handler.process_message(user_id, "How can you help me?", thread_id)
                assert "I'm here to help!" in response
                
                # Verify router was called
                mock_r.chat_completion.assert_called()


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 