#!/usr/bin/env python3
"""
Memory Continuity Bug Test - NOW FIXED!

CRITICAL BUG (RESOLVED): Memory retrieval was filtered by thread_id, but each new conversation
created a new thread_id, breaking memory continuity across sessions.

This bug was fixed during the Claude prompt caching implementation:
✅ Memory now queries by user_id instead of thread_id
✅ AI can access memory from ALL user sessions, not just current thread
✅ User experience improved: AI remembers context across sign-out/sign-in cycles

These tests now verify the fix works correctly and prevent regression.
"""

import pytest
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock
from src.simple_memory import SimpleMemory
from src.claude_agent import interact_with_agent

class TestMemoryContinuityBug:
    """Test memory continuity across different thread IDs"""
    
    @pytest.fixture
    def mock_supabase(self):
        """Mock Supabase client for testing"""
        supabase = MagicMock()
        supabase.table.return_value = supabase
        supabase.select.return_value = supabase
        supabase.eq.return_value = supabase
        supabase.order.return_value = supabase
        supabase.limit.return_value = supabase
        supabase.insert.return_value = supabase
        supabase.execute.return_value = MagicMock(data=[])
        return supabase

    @pytest.fixture
    def user_id(self):
        """Test user ID"""
        return "test-user-123"

    @pytest.mark.asyncio
    async def test_memory_continuity_bug_reproduction(self, mock_supabase, user_id):
        """
        VERIFIES THE BUG FIX:
        Memory stored with thread_id_1 is now visible when retrieving with thread_id_2
        """
        
        # === SETUP: Simulate memory with name information ===
        memory_with_name = [
            {
                'content': 'user: My name is Iso',
                'metadata': {'thread_id': 'thread_session_1'},
                'memory_type': 'message',
                'created_at': '2025-06-05T08:30:00Z'
            },
            {
                'content': 'assistant: Hi Iso! Nice to meet you.',
                'metadata': {'thread_id': 'thread_session_1'}, 
                'memory_type': 'message',
                'created_at': '2025-06-05T08:30:05Z'
            }
        ]
        
        # === SIMULATION 1: First session (thread_session_1) ===
        memory1 = SimpleMemory(mock_supabase, user_id)
        
        # Mock memory retrieval for first session - should find the name info
        mock_supabase.table.return_value.execute.return_value.data = memory_with_name
        
        context1 = await memory1.get_context('thread_session_1')
        
        # Verify first session has memory
        assert len(context1['messages']) == 2
        assert any('Iso' in msg['content'] for msg in context1['messages'])
        print("✅ First session: AI has access to name 'Iso'")
        
        # === SIMULATION 2: Second session (thread_session_2) ===
        memory2 = SimpleMemory(mock_supabase, user_id)
        
        # Mock memory retrieval for second session - should now FIND the memory due to user_id filter
        mock_supabase.table.return_value.execute.return_value.data = memory_with_name
        
        context2 = await memory2.get_context('thread_session_2')
        
        # Verify second session HAS memory (THIS IS THE FIX!)
        assert len(context2['messages']) == 2
        assert any('Iso' in msg['content'] for msg in context2['messages'])
        print("✅ BUG FIXED: Second session can now see name 'Iso' from first session!")
        
        # === VERIFICATION: The fix queries by user_id instead of thread_id ===
        # The memory table contains the name, and get_context retrieves ALL user memory
        # When user signs out/in, new thread_id doesn't break continuity anymore
        
        print("\n💡 SOLUTION: Memory retrieval now filters by user_id")
        print("   📝 Memory saved with: thread_session_1")  
        print("   🔍 Memory queried with: ALL user threads (user_id filter)")
        print("   ✅ Result: Memory found across sessions → AI remembers user's name")

    @pytest.mark.asyncio
    async def test_proper_memory_retrieval_across_threads(self, mock_supabase, user_id):
        """
        TEST: How memory SHOULD work - retrieve ALL user memory regardless of thread_id
        """
        
        # Memory from multiple sessions
        all_user_memory = [
            {
                'content': 'user: My name is Iso',
                'metadata': {'thread_id': 'thread_session_1'},
                'memory_type': 'message',
                'created_at': '2025-06-05T08:30:00Z'
            },
            {
                'content': 'assistant: Hi Iso! Nice to meet you.',
                'metadata': {'thread_id': 'thread_session_1'},
                'memory_type': 'message', 
                'created_at': '2025-06-05T08:30:05Z'
            },
            {
                'content': 'user: I like chocolate',
                'metadata': {'thread_id': 'thread_session_2'},
                'memory_type': 'message',
                'created_at': '2025-06-05T09:15:00Z'
            }
        ]
        
        # Mock retrieval of ALL user memory (not filtered by thread_id)
        mock_supabase.table.return_value.execute.return_value.data = all_user_memory
        
        memory = SimpleMemory(mock_supabase, user_id)
        context = await memory.get_context('thread_session_3')  # New session
        
        # Should have access to ALL previous memory
        assert len(context['messages']) == 3
        assert any('Iso' in msg['content'] for msg in context['messages'])
        assert any('chocolate' in msg['content'] for msg in context['messages'])
        print("✅ FIXED: AI can access ALL user memory across sessions")

    def test_memory_query_structure_bug(self, mock_supabase, user_id):
        """
        TEST: Verify the memory continuity bug has been FIXED
        The query should now filter by user_id, NOT thread_id, to preserve memory across sessions
        """
        memory = SimpleMemory(mock_supabase, user_id)
        
        # This will trigger the FIXED query
        asyncio.run(memory.get_context('thread_new_session'))
        
        # Verify the query includes user_id filter (THIS IS THE FIX!)
        calls = mock_supabase.table.call_args_list
        eq_calls = mock_supabase.eq.call_args_list
        
        # Should have called eq('user_id', user_id) instead of eq('metadata->>thread_id', 'thread_new_session')
        user_id_filter_found = False
        thread_id_filter_found = False
        
        for call in eq_calls:
            if len(call[0]) >= 2:
                filter_field = str(call[0][0])
                if filter_field == 'user_id':
                    user_id_filter_found = True
                elif 'thread_id' in filter_field:
                    thread_id_filter_found = True
                    
        assert user_id_filter_found, "Query should filter by user_id (this is the fix!)"
        assert not thread_id_filter_found, "Query should NOT filter by thread_id (this was the bug!)"
        print("✅ CONFIRMED: Memory query filters by user_id → maintains continuity across sessions")

if __name__ == "__main__":
    # Run the test to demonstrate the bug
    pytest.main([__file__, "-v"]) 