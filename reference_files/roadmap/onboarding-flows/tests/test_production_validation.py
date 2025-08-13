#!/usr/bin/env python3
"""
Production Validation Test for Claude Prompt Caching

Ensures that the caching implementation:
1. Preserves existing conversation functionality  
2. Maintains onboarding flow
3. Handles all edge cases gracefully
4. Works with real data patterns
"""

import asyncio
import os
import sys
from unittest.mock import AsyncMock, MagicMock

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.claude_agent import interact_with_agent, interact_with_agent_stream
from src.simple_memory import SimpleMemory
from src.context_formatter import format_static_context_for_caching


async def test_existing_conversation_flow():
    """Test that existing conversation functionality still works"""
    print("🔄 Testing Existing Conversation Flow...")
    
    # Mock Supabase with realistic responses
    mock_supabase = MagicMock()
    
    def create_mock_table():
        mock_table = MagicMock()
        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.order.return_value = mock_table
        mock_table.limit.return_value = mock_table
        mock_table.insert.return_value = mock_table
        
        # Return different data based on the context of the call
        # For memory table queries, return empty content
        mock_table.execute.return_value.data = []
        return mock_table
    
    mock_supabase.table.side_effect = lambda x: create_mock_table()
    
    # Test memory operations work correctly
    memory = SimpleMemory(mock_supabase, "test-user-456")
    
    # Test adding messages (should work as before)
    try:
        await memory.add_message("test-thread", "Hello world", "user")
        print("   ✅ Message storage works")
    except Exception as e:
        print(f"   ❌ Message storage failed: {e}")
        raise
    
    # Test context retrieval with new method
    try:
        context = await memory.get_caching_optimized_context("test-thread")
        assert "static_context" in context
        assert "dynamic_context" in context
        print("   ✅ Caching context retrieval works")
    except Exception as e:
        print(f"   ❌ Context retrieval failed: {e}")
        raise
    
    # Test that old get_context method still works (backward compatibility)
    try:
        old_context = await memory.get_context("test-thread")
        assert "messages" in old_context
        assert "summaries" in old_context
        print("   ✅ Backward compatibility preserved")
    except Exception as e:
        print(f"   ❌ Backward compatibility failed: {e}")
        raise


async def test_conversation_with_mocked_claude():
    """Test full conversation flow with mocked Claude API"""
    print("🤖 Testing Full Conversation Flow...")
    
    # Create comprehensive mocks
    mock_supabase = MagicMock()
    mock_anthropic = AsyncMock()
    
    # Mock Supabase responses
    def create_mock_table():
        mock_table = MagicMock()
        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.order.return_value = mock_table
        mock_table.limit.return_value = mock_table
        mock_table.insert.return_value = mock_table
        mock_table.execute.return_value.data = []
        return mock_table
    
    mock_supabase.table.side_effect = lambda x: create_mock_table()
    
    # Mock Claude response
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="Hello! I'm Hai, your AI assistant. How can I help you with your creative project today?")]
    mock_anthropic.messages.create.return_value = mock_response
    
    # Patch the agent's dependencies
    import src.claude_agent as agent_module
    
    # Store original functions to restore later
    original_get_client = agent_module.get_anthropic_client
    original_check_onboarding = agent_module.check_and_handle_project_onboarding
    original_check_project = agent_module.check_user_has_project_overview
    original_monitor = agent_module.monitor_conversation_for_project_completion
    
    try:
        # Apply mocks
        agent_module.get_anthropic_client = AsyncMock(return_value=mock_anthropic)
        agent_module.check_and_handle_project_onboarding = AsyncMock(return_value={
            "should_onboard": False, 
            "prompt": None
        })
        agent_module.check_user_has_project_overview = AsyncMock(return_value=True)
        agent_module.monitor_conversation_for_project_completion = AsyncMock(return_value=False)
        
        # Test conversation
        response = await interact_with_agent(
            user_input="Tell me about my project status",
            user_id="test-user-789",
            user_timezone="America/New_York", 
            thread_id="test-thread-123",
            supabase_client=mock_supabase,
            context={}
        )
        
        assert response == "Hello! I'm Hai, your AI assistant. How can I help you with your creative project today?"
        print("   ✅ Full conversation flow works")
        
        # Verify Claude was called with caching parameters
        mock_anthropic.messages.create.assert_called_once()
        call_kwargs = mock_anthropic.messages.create.call_args.kwargs
        
        # Check critical caching parameters
        assert "system" in call_kwargs, "Missing system prompt (needed for caching)"
        assert "messages" in call_kwargs, "Missing messages"
        assert "extra_headers" in call_kwargs, "Missing cache headers"
        assert call_kwargs["extra_headers"]["anthropic-beta"] == "prompt-caching-2024-07-31"
        
        print("   ✅ Caching parameters correctly applied")
        
        # Check that system prompt is substantial (should contain user context)
        system_prompt = call_kwargs["system"]
        assert len(system_prompt) > 500, f"System prompt too short: {len(system_prompt)} chars"
        assert "USER CONTEXT:" in system_prompt, "Missing user context in system prompt"
        assert "Hai" in system_prompt, "Missing assistant identity"
        
        print(f"   ✅ System prompt properly structured: {len(system_prompt)} chars")
        
    finally:
        # Restore original functions
        agent_module.get_anthropic_client = original_get_client
        agent_module.check_and_handle_project_onboarding = original_check_onboarding
        agent_module.check_user_has_project_overview = original_check_project
        agent_module.monitor_conversation_for_project_completion = original_monitor


def test_onboarding_compatibility():
    """Test that onboarding flow is preserved with caching"""
    print("📋 Testing Onboarding Compatibility...")
    
    # Test that static context handles missing project data correctly
    empty_static_context = {
        "user_profile": {
            "id": "new-user-123", 
            "first_name": "New",
            "last_name": "User",
            "slack_email": "new@example.com",
            "interaction_count": 0
        },
        "project_overview": None,  # No project yet
        "project_updates": [],
        "longterm_summaries": [],
        "has_complete_profile": True,
        "has_project": False  # This should trigger onboarding
    }
    
    formatted = format_static_context_for_caching(empty_static_context)
    
    # Should contain new user indicators
    assert "New User" in formatted, "New user name not preserved"
    assert "Status: No project overview yet" in formatted, "Missing project status"
    assert "Recommendation: Guide user through project planning" in formatted, "Missing onboarding hint"
    
    print("   ✅ New user onboarding context preserved")
    
    # Test existing user with project
    established_static_context = {
        "user_profile": {
            "id": "experienced-user-789",
            "first_name": "Alice", 
            "last_name": "Writer",
            "slack_email": "alice@example.com",
            "interaction_count": 150
        },
        "project_overview": {
            "project_name": "My Novel",
            "project_type": "Creative Writing",
            "description": "A coming-of-age story"
        },
        "project_updates": [
            {"created_at": "2025-01-15", "content": "Finished chapter 3"}
        ],
        "longterm_summaries": [],
        "has_complete_profile": True,
        "has_project": True
    }
    
    formatted_experienced = format_static_context_for_caching(established_static_context)
    
    assert "Alice Writer" in formatted_experienced, "Experienced user name not preserved"
    assert "My Novel" in formatted_experienced, "Project name not preserved"
    assert "Finished chapter 3" in formatted_experienced, "Project updates not preserved"
    
    print("   ✅ Experienced user context preserved")


def test_error_resilience():
    """Test that the system handles errors gracefully"""
    print("🛡️ Testing Error Resilience...")
    
    # Test with malformed static context
    malformed_context = {
        "user_profile": "not a dict",  # Wrong type
        "project_overview": None,
        "project_updates": "also wrong type",
        "longterm_summaries": None
    }
    
    try:
        formatted = format_static_context_for_caching(malformed_context)
        # Should not crash, should handle gracefully
        assert len(formatted) > 0, "Should produce some output even with bad data"
        print("   ✅ Malformed data handled gracefully")
    except Exception as e:
        print(f"   ❌ Error handling failed: {e}")
        raise
    
    # Test with None context
    try:
        formatted_none = format_static_context_for_caching({})
        assert len(formatted_none) > 0, "Should handle empty context"
        print("   ✅ Empty context handled gracefully")
    except Exception as e:
        print(f"   ❌ Empty context handling failed: {e}")
        raise


def test_real_world_data_patterns():
    """Test with realistic data patterns"""
    print("🌍 Testing Real-world Data Patterns...")
    
    # Test with realistic user data  
    realistic_context = {
        "user_profile": {
            "id": "emma-creative-456",
            "first_name": "Emma",
            "last_name": "Rodriguez", 
            "slack_email": "emma.rodriguez@company.com",
            "preferences": {
                "theme": "dark",
                "notifications": True,
                "timezone": "America/Los_Angeles",
                "language": "en"
            },
            "interaction_count": 87
        },
        "project_overview": {
            "project_name": "Community Garden Documentary",
            "project_type": "Documentary Film",
            "description": "A short documentary about urban community gardens and their impact on neighborhood revitalization",
            "goals": [
                "Complete 15-minute documentary by March 2025",
                "Interview 8-10 community members and organizers", 
                "Capture seasonal changes in the garden",
                "Submit to 3 local film festivals",
                "Create educational materials for schools"
            ],
            "challenges": [
                "Coordinating schedules with busy community members",
                "Weather-dependent outdoor filming",
                "Limited budget for equipment and post-production",
                "Balancing multiple perspectives and storylines",
                "Technical learning curve for new editing software"
            ],
            "success_metrics": {
                "completion": "Documentary finished and submitted to festivals",
                "community_impact": "Garden featured in local media",
                "personal_growth": "Improved filmmaking and storytelling skills"
            }
        },
        "project_updates": [
            {
                "created_at": "2025-01-15T14:30:00Z",
                "content": "Completed interview with garden coordinator Maria - great insights about starting the garden 5 years ago"
            },
            {
                "created_at": "2025-01-14T10:15:00Z", 
                "content": "Filmed B-roll footage of winter garden preparations, captured community work day with 12 volunteers"
            },
            {
                "created_at": "2025-01-12T16:45:00Z",
                "content": "Secured permission for filming from all garden plot holders, created shooting schedule for next 3 weeks"
            }
        ],
        "longterm_summaries": [
            {
                "created_at": "2025-01-10T12:00:00Z",
                "content": "Emma is making excellent progress on documentary project, showing strong commitment to storytelling and community engagement"
            },
            {
                "created_at": "2025-01-05T15:30:00Z",
                "content": "Discussed interview techniques and equipment setup, user is gaining confidence with technical aspects"
            }
        ]
    }
    
    formatted = format_static_context_for_caching(realistic_context)
    
    # Verify all important information is preserved
    assert "Emma Rodriguez" in formatted, "User name missing"
    assert "Community Garden Documentary" in formatted, "Project name missing"
    assert "15-minute documentary" in formatted, "Project goals missing"
    assert "Weather-dependent outdoor filming" in formatted, "Challenges missing"
    assert "interview with garden coordinator Maria" in formatted, "Updates missing"
    assert "excellent progress on documentary" in formatted, "Summaries missing"
    
    # Check size is reasonable for caching
    size = len(formatted)
    assert 1500 < size < 8000, f"Context size unreasonable for caching: {size}"
    
    print(f"   ✅ Real-world context processed: {size} chars")
    print("   ✅ All critical information preserved")


async def run_production_validation():
    """Run all production validation tests"""
    print("\n🔍 Production Validation for Claude Prompt Caching\n")
    print("Ensuring existing functionality is preserved...\n")
    
    try:
        await test_existing_conversation_flow()
        await test_conversation_with_mocked_claude()
        test_onboarding_compatibility()
        test_error_resilience()
        test_real_world_data_patterns()
        
        print("\n✅ PRODUCTION VALIDATION PASSED!")
        print("\n🎯 Summary:")
        print("   • All existing conversation functionality preserved")
        print("   • Onboarding flow compatibility maintained") 
        print("   • Error handling remains robust")
        print("   • Real-world data patterns supported")
        print("   • Caching optimization successfully integrated")
        
        print("\n🚀 READY FOR DEPLOYMENT")
        print("   The Claude prompt caching implementation is production-ready!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ PRODUCTION VALIDATION FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(run_production_validation())
    
    if success:
        print("\n🎉 Implementation validated - proceed with deployment!")
        exit(0)
    else:
        print("\n🚨 Fix issues before deploying to production!")
        exit(1) 