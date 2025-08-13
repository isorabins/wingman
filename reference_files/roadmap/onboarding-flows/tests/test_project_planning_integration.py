#!/usr/bin/env python3
"""
Integration Tests for Project Planning with React Agent

Test the complete flow of project onboarding integration.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import sys
import os

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


class TestClaudeAgentProjectIntegration:
    """Test Claude Agent integration with project planning"""

    @pytest.fixture
    def mock_supabase_client(self):
        """Create a mock Supabase client"""
        client = MagicMock()
        client.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock()
        return client

    @pytest.fixture
    def test_user_id(self):
        """Real test user ID provided"""
        return "3189d065-7a5c-41a7-8cf6-4a6164fd7d1b"

    @pytest.fixture  
    def test_thread_id(self):
        """Sample thread ID"""
        return "thread-123"

    @pytest.fixture
    def sample_context(self):
        """Sample context for agent interaction"""
        return {
            "user_timezone": "America/New_York",
            "session_id": "session-123"
        }

    def test_import_claude_agent_enhancement(self):
        """Test that we can import enhanced Claude agent functions"""
        # This should now succeed
        from src.claude_agent import check_and_handle_project_onboarding
        assert callable(check_and_handle_project_onboarding)

    @pytest.mark.asyncio
    async def test_user_without_project_triggers_onboarding(self, mock_supabase_client, test_user_id, test_thread_id, sample_context):
        """Test that users without project overview automatically trigger onboarding flow"""
        from src.claude_agent import check_and_handle_project_onboarding
        from src.project_planning import get_project_planning_prompt
        
        # Mock user has no project overview
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
        
        # ANY input should trigger onboarding if user has no project overview
        result = await check_and_handle_project_onboarding(
            mock_supabase_client, 
            test_user_id, 
            "Hello, how are you?"  # Non-project related input
        )
        
        assert result["should_onboard"] is True
        assert "project" in result["prompt"].lower()
        
        # Also test with project-related input
        result2 = await check_and_handle_project_onboarding(
            mock_supabase_client, 
            test_user_id, 
            "I want to start working on something new"
        )
        
        assert result2["should_onboard"] is True
        assert "project" in result2["prompt"].lower()

    @pytest.mark.asyncio
    async def test_user_with_project_skips_onboarding(self, mock_supabase_client, test_user_id, test_thread_id, sample_context):
        """Test that users with project overview skip onboarding"""
        from src.claude_agent import check_and_handle_project_onboarding
        
        # Mock user has project overview
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
            {"id": "project-123", "user_id": test_user_id}
        ]
        
        result = await check_and_handle_project_onboarding(
            mock_supabase_client, 
            test_user_id, 
            "How's my project going?"
        )
        
        assert result["should_onboard"] is False
        assert result["prompt"] is None

    @pytest.mark.asyncio  
    async def test_conversation_completion_triggers_project_creation(self, mock_supabase_client, test_user_id):
        """Test that completed conversations trigger project overview creation"""
        from src.claude_agent import handle_completed_project_conversation
        
        # Mock comprehensive conversation
        conversation = [
            {"role": "user", "content": "I want to build a fitness app"},
            {"role": "assistant", "content": "Tell me about your goals"},
            {"role": "user", "content": "I want 10,000 users and help people stay motivated"},
            {"role": "assistant", "content": "What about your target audience?"},
            {"role": "user", "content": "Busy professionals who struggle with consistency"},
            {"role": "assistant", "content": "What features are you thinking?"},
            {"role": "user", "content": "Social challenges, progress tracking, and gamification"},
            {"role": "assistant", "content": "What's your timeline?"},
            {"role": "user", "content": "6 months for MVP, 1 year for full launch"}
        ]
        
        # Mock successful project creation
        mock_supabase_client.table.return_value.insert.return_value.execute.return_value.data = [
            {"id": "project-new-123"}
        ]
        
        with patch('src.project_planning.analyze_project_conversation') as mock_analysis:
            mock_analysis.return_value = {
                "project_name": "FitTrack Pro",
                "project_type": "mobile app",
                "description": "Fitness tracking app with social features",
                "goals": [{"goal": "Reach 10,000 users", "timeline": "1 year"}],
                "challenges": [{"challenge": "User retention", "mitigation": "Social features"}],
                "success_metrics": {"metrics": [{"metric": "Daily active users", "target": "1000"}]}
            }
            
            # Mock OnboardingManager
            with patch('src.onboarding_manager.OnboardingManager') as mock_onboarding:
                mock_manager = AsyncMock()
                mock_manager.create_project_overview.return_value = "project-new-123"
                mock_onboarding.return_value = mock_manager
                
                result = await handle_completed_project_conversation(
                    mock_supabase_client,
                    test_user_id,
                    conversation
                )
                
                assert result["project_created"] is True
                assert result["project_id"] == "project-new-123"


class TestProjectOnboardingFlow:
    """Test the complete project onboarding flow end-to-end"""

    @pytest.fixture
    def mock_memory(self):
        """Mock SimpleMemory instance"""
        memory = AsyncMock()
        memory.get_context.return_value = {
            "messages": [],
            "summaries": []
        }
        return memory

    def test_import_enhanced_interact_function(self):
        """Test that we can import the enhanced interact_with_agent function"""
        # Should not fail - the function exists, we're just enhancing it
        from src.claude_agent import interact_with_agent
        assert callable(interact_with_agent)

    @pytest.mark.asyncio
    async def test_new_user_gets_project_planning_prompt(self, mock_memory):
        """Test that new users without projects get the planning prompt"""
        pytest.skip("Will implement after enhancing the interact_with_agent function")
        
        with patch('src.claude_agent.SimpleMemory', return_value=mock_memory):
            with patch('src.project_planning.check_user_has_project_overview', return_value=False):
                with patch('src.project_planning.should_trigger_project_planning', return_value=True):
                    with patch('src.claude_agent.create_agent') as mock_create_agent:
                        
                        # Mock agent response
                        mock_agent = AsyncMock()
                        mock_agent.ainvoke.return_value = {
                            "messages": [MagicMock(content="Let's start planning your project!")]
                        }
                        mock_create_agent.return_value = mock_agent
                        
                        from src.claude_agent import interact_with_agent
                        
                        response = await interact_with_agent(
                            user_input="I have an idea for a new app",
                            user_id="test-user",
                            user_timezone="UTC",
                            thread_id="test-thread",
                            supabase_client=MagicMock(),
                            context={}
                        )
                        
                        # Check that project planning prompt was included
                        mock_agent.ainvoke.assert_called_once()
                        call_args = mock_agent.ainvoke.call_args[0][0]
                        
                        # Should include project planning prompt in system messages
                        system_contents = [msg.content for msg in call_args["messages"] 
                                         if hasattr(msg, 'content') and 'project' in msg.content.lower()]
                        assert len(system_contents) > 0

    @pytest.mark.asyncio
    async def test_project_conversation_monitoring(self, mock_memory):
        """Test that project conversations are monitored for completion"""
        pytest.skip("Will implement after enhancing the interact_with_agent function")
        
        # Mock conversation history that should trigger completion
        mock_memory.get_context.return_value = {
            "messages": [
                {"role": "user", "content": "My project is a fitness app"},
                {"role": "user", "content": "Goal is 10,000 users"},
                {"role": "user", "content": "Target audience is professionals"},
                {"role": "user", "content": "Features include social challenges"},
                {"role": "user", "content": "Timeline is 6 months"},
                {"role": "user", "content": "Main challenge is user retention"}
            ],
            "summaries": []
        }
        
        with patch('src.claude_agent.SimpleMemory', return_value=mock_memory):
            with patch('src.project_planning.check_user_has_project_overview', return_value=False):
                with patch('src.project_planning.monitor_conversation_for_project_completion', return_value=True):
                    with patch('src.onboarding_manager.OnboardingManager.create_project_overview', return_value="project-123"):
                        with patch('src.claude_agent.create_agent') as mock_create_agent:
                            
                            mock_agent = AsyncMock()
                            mock_agent.ainvoke.return_value = {
                                "messages": [MagicMock(content="Great! I've created your project overview.")]
                            }
                            mock_create_agent.return_value = mock_agent
                            
                            from src.claude_agent import interact_with_agent
                            
                            response = await interact_with_agent(
                                user_input="That covers everything about my project",
                                user_id="test-user",
                                user_timezone="UTC", 
                                thread_id="test-thread",
                                supabase_client=MagicMock(),
                                context={}
                            )
                            
                            # Should have attempted to create project overview
                            assert "project overview" in response.lower() or "project" in response.lower() 