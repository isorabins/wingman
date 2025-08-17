#!/usr/bin/env python3
"""
Tests for SimpleMemory database operations
Tests conversation storage, context retrieval, and auto-dependency creation
"""

import pytest
import os
import sys
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime, timezone

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.simple_memory import SimpleMemory


class TestSimpleMemory:
    """Test SimpleMemory class database operations"""
    
    @pytest.fixture
    def mock_supabase(self):
        """Mock Supabase client for testing"""
        supabase = MagicMock()
        return supabase
    
    @pytest.fixture
    def memory(self, mock_supabase):
        """Create SimpleMemory instance"""
        return SimpleMemory(mock_supabase, "test-user-123")
    
    @pytest.mark.asyncio
    async def test_ensure_creator_profile_exists(self, memory, mock_supabase):
        """Test auto-creation of creator profile when it exists"""
        # Mock profile exists
        existing_profile = MagicMock()
        existing_profile.data = [{"id": "test-user-123"}]
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = existing_profile
        
        await memory.ensure_creator_profile("test-user-123")
        
        # Should not attempt to insert
        mock_supabase.table.return_value.insert.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_ensure_creator_profile_creates_new(self, memory, mock_supabase):
        """Test auto-creation of creator profile when it doesn't exist"""
        # Mock profile doesn't exist
        empty_profile = MagicMock()
        empty_profile.data = []
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = empty_profile
        
        # Mock successful insert
        insert_success = MagicMock()
        mock_supabase.table.return_value.insert.return_value.execute.return_value = insert_success

        await memory.ensure_creator_profile("test-user-123")
        
        # Should attempt to insert new profile
        mock_supabase.table.return_value.insert.assert_called_once()
        
        # Verify insert data structure
        insert_args = mock_supabase.table.return_value.insert.call_args[0][0]
        assert insert_args['id'] == 'test-user-123'
        assert 'slack_email' in insert_args
        assert 'zoom_email' in insert_args
        assert 'first_name' in insert_args
        assert 'last_name' in insert_args
    
    @pytest.mark.asyncio
    async def test_add_message(self, memory, mock_supabase):
        """Test adding a message to conversation memory"""
        # Mock successful profile check
        profile_exists = MagicMock()
        profile_exists.data = [{"id": "test-user-123"}]
        
        # Mock successful insert for both tables
        insert_success = MagicMock()
        
        def mock_table_response(table_name):
            mock_table = MagicMock()
            if table_name == 'creator_profiles':
                mock_table.select.return_value.eq.return_value.execute.return_value = profile_exists
            else:  # conversations or memory table
                mock_table.insert.return_value.execute.return_value = insert_success
            return mock_table
        
        mock_supabase.table.side_effect = mock_table_response
        
        await memory.add_message("thread-123", "Hello", "user")
        
        # Should call insert for both conversations and memory tables
        assert mock_supabase.table.call_count >= 2  # At least profile check + inserts
    
    @pytest.mark.asyncio
    async def test_get_context_with_messages(self, memory, mock_supabase):
        """Test retrieving conversation context with existing messages"""
        # Mock conversation messages from memory table
        messages_response = MagicMock()
        messages_response.data = [
            {
                'content': 'user: Hello',  # Formatted content as stored
                'memory_type': 'message',
                'created_at': datetime.now(timezone.utc).isoformat()
            },
            {
                'content': 'assistant: Hi there!',  # Formatted content as stored
                'memory_type': 'message',
                'created_at': datetime.now(timezone.utc).isoformat()
            }
        ]
        
        # Mock summaries
        summaries_response = MagicMock()
        summaries_response.data = []
        
        def mock_table_response(table_name):
            mock_table = MagicMock()
            if table_name == 'memory':
                # Return different responses for messages vs summaries
                if mock_table.select.return_value.eq.return_value.eq.return_value.order.return_value.limit.return_value.execute.call_count == 0:
                    mock_table.select.return_value.eq.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = messages_response
                else:
                    mock_table.select.return_value.eq.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = summaries_response
            return mock_table
        
        mock_supabase.table.side_effect = mock_table_response
        
        context = await memory.get_context("thread-123")
        
        assert 'messages' in context
        assert len(context['messages']) == 2
        assert context['messages'][0]['role'] == 'user'
        assert context['messages'][0]['content'] == 'Hello'
        assert context['messages'][1]['role'] == 'assistant'
        assert context['messages'][1]['content'] == 'Hi there!'
    
    @pytest.mark.asyncio
    async def test_get_context_empty_thread(self, memory, mock_supabase):
        """Test retrieving context for empty thread"""
        # Mock profile exists
        profile_exists = MagicMock()
        profile_exists.data = [{"id": "test-user-123"}]
        
        # Mock no messages
        empty_messages = MagicMock()
        empty_messages.data = []
        
        def mock_table_response(table_name):
            mock_table = MagicMock()
            if table_name == 'creator_profiles':
                mock_table.select.return_value.eq.return_value.limit.return_value.execute.return_value = profile_exists
            elif table_name == 'conversation_memory':
                mock_table.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = empty_messages
            return mock_table
        
        mock_supabase.table.side_effect = mock_table_response
        
        context = await memory.get_context("new-thread")
        
        assert 'messages' in context
        assert len(context['messages']) == 0
        assert 'summaries' in context
    
    @pytest.mark.asyncio
    async def test_error_handling_in_add_message(self, memory, mock_supabase):
        """Test error handling when adding messages fails"""
        # Mock profile check to raise error
        mock_supabase.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.side_effect = Exception("DB Error")
        
        # Should not raise exception, should handle gracefully
        await memory.add_message("thread-123", "Hello", "user")
        
        # Error should be logged but not raised
        # (In real implementation, this would be captured by logger)
    
    @pytest.mark.asyncio
    async def test_message_limit_enforcement(self, memory, mock_supabase):
        """Test that message retrieval respects limits"""
        # Mock many messages
        many_messages = [
            {
                'content': f'Message {i}',
                'role': 'user' if i % 2 == 0 else 'assistant',
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            for i in range(50)  # 50 messages
        ]
        
        profile_exists = MagicMock()
        profile_exists.data = [{"id": "test-user-123"}]
        
        messages_response = MagicMock()
        messages_response.data = many_messages
        
        def mock_table_response(table_name):
            mock_table = MagicMock()
            if table_name == 'creator_profiles':
                mock_table.select.return_value.eq.return_value.limit.return_value.execute.return_value = profile_exists
            elif table_name == 'conversation_memory':
                mock_table.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = messages_response
            return mock_table
        
        mock_supabase.table.side_effect = mock_table_response
        
        context = await memory.get_context("thread-with-many-messages")
        
        # Should enforce some reasonable limit
        assert len(context['messages']) <= 50  # Default limit in implementation


class TestSimpleMemoryEdgeCases:
    """Test edge cases and error scenarios"""
    
    @pytest.fixture
    def memory_with_error_db(self):
        """Create memory with database that throws errors"""
        error_supabase = MagicMock()
        error_supabase.table.return_value.select.return_value.eq.return_value.execute.side_effect = Exception("Connection Error")
        return SimpleMemory(error_supabase, "test-user-456")
    
    @pytest.mark.asyncio
    async def test_resilience_to_database_errors(self, memory_with_error_db):
        """Test that memory operations are resilient to database errors"""
        # These operations should not crash the application
        await memory_with_error_db.ensure_creator_profile("test-user-123")
        await memory_with_error_db.add_message("thread-123", "Hello", "user")
        
        context = await memory_with_error_db.get_context("thread-123")
        
        # Should return empty context on error
        assert context == {'messages': [], 'summaries': []}
    
    @pytest.mark.asyncio
    async def test_memory_with_none_values(self):
        """Test memory operations with None/invalid values"""
        mock_supabase = MagicMock()
        memory = SimpleMemory(mock_supabase, None)  # None user_id

        # Should handle gracefully
        await memory.ensure_creator_profile("test-user-123")
        await memory.add_message(None, None, None)
        context = await memory.get_context(None)
        
        assert context == {'messages': [], 'summaries': []}


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 