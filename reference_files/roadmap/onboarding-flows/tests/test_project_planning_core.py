#!/usr/bin/env python3
"""
Unit Tests for Project Planning Core Functionality

Test-driven development for project planning logic using mocks.
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

from src.project_planning import get_project_planning_prompt


class TestProjectPlanningBasics:
    """Test basic project planning functions with mocks"""

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

    def test_import_project_planning_module(self):
        """Test that we can import the project planning module"""
        # This should now succeed
        from src.project_planning import check_user_has_project_overview
        assert callable(check_user_has_project_overview)

    @pytest.mark.asyncio
    async def test_check_user_no_project_overview(self, mock_supabase_client, test_user_id):
        """Test detecting users without project overview"""
        from src.project_planning import check_user_has_project_overview
        
        # Mock empty response (no project overview)
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
        
        result = await check_user_has_project_overview(mock_supabase_client, test_user_id)
        
        assert result is False
        mock_supabase_client.table.assert_called_with('project_overview')

    @pytest.mark.asyncio  
    async def test_check_user_has_project_overview(self, mock_supabase_client, test_user_id):
        """Test detecting users with project overview"""
        from src.project_planning import check_user_has_project_overview
        
        # Mock response with project data
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
            {"id": "project-123", "user_id": test_user_id, "project_name": "Test Project"}
        ]
        
        result = await check_user_has_project_overview(mock_supabase_client, test_user_id)
        
        assert result is True
        mock_supabase_client.table.assert_called_with('project_overview')

    def test_get_project_planning_prompt_exists(self):
        """Test that project planning prompt function exists and returns a string"""
        from src.project_planning import get_project_planning_prompt
        
        prompt = get_project_planning_prompt()
        
        assert isinstance(prompt, str)
        assert len(prompt) > 100  # Should be substantial
        assert "project" in prompt.lower()
        
    def test_get_project_planning_prompt_content(self):
        """Test that project planning prompt contains expected content"""
        from src.project_planning import get_project_planning_prompt
        
        prompt = get_project_planning_prompt()
        
        # Check for key sections using the updated prompt format
        assert "project" in prompt.lower()
        assert "8" in prompt or "eight" in prompt.lower()  # Should reference 8 steps
        assert "goals" in prompt.lower()
        assert "timeline" in prompt.lower()
        assert "challenges" in prompt.lower()
        assert "resources" in prompt.lower()
        assert "success" in prompt.lower()
        assert "motivation" in prompt.lower()
        assert len(prompt) > 500  # Should be substantial


class TestProjectConversationAnalysis:
    """Test AI-powered conversation analysis functionality"""

    @pytest.fixture
    def sample_project_conversation(self):
        """Sample conversation about a mobile app project"""
        return [
            {"role": "assistant", "content": get_project_planning_prompt()},
            {"role": "user", "content": "I want to build a fitness tracking mobile app that helps people stay motivated through social challenges and gamification."},
            {"role": "assistant", "content": "That sounds like an exciting project! A fitness app with social challenges could really help with user engagement. Tell me more about what inspired you to create this - have you personally struggled with fitness motivation, or is this based on market research?"},
            {"role": "user", "content": "I personally struggled to stick with fitness routines, and I noticed my friends had the same issue. We tried using existing apps but they felt boring and lonely. I want to create something that makes fitness feel like a fun social game."},
            {"role": "assistant", "content": "Perfect! Now let's talk about your specific goals. What would success look like for this app? Are you thinking about user acquisition numbers, engagement metrics, or maybe revenue targets?"},
            {"role": "user", "content": "I'd love to get 10,000 active users in the first year, with people using the app at least 3 times per week. Eventually I want to monetize through premium features and maybe corporate wellness partnerships."}
        ]

    def test_import_conversation_analysis(self):
        """Test that we can import conversation analysis functions"""
        # This should now succeed
        from src.project_planning import analyze_project_conversation
        assert callable(analyze_project_conversation)

    @pytest.mark.asyncio
    async def test_analyze_project_conversation_mock(self, sample_project_conversation):
        """Test conversation analysis with mocked AI response"""
        from src.project_planning import analyze_project_conversation

        # Mock the AI analysis response
        mock_analysis = {
            "project_name": "FitSocial - Fitness Challenge App",
            "project_type": "mobile app",
            "description": "A fitness tracking mobile app that motivates users through social challenges and gamification",
            "goals": [
                {"goal": "Reach 10,000 active users", "timeline": "1 year"},
                {"goal": "Achieve 3+ app uses per week per user", "timeline": "ongoing"}
            ],
            "challenges": [
                {"challenge": "User retention", "mitigation": "Social features and gamification"},
                {"challenge": "Market competition", "mitigation": "Focus on social engagement differentiator"}
            ],
            "success_metrics": {
                "metrics": [
                    {"metric": "Active users", "target": "10,000"},
                    {"metric": "Weekly usage frequency", "target": "3+ times per user"}
                ]
            }
        }

        # Use the updated function name
        with patch('src.project_planning.analyze_conversation_for_project_info') as mock_ai:
            mock_ai.return_value = mock_analysis

            result = await analyze_project_conversation(sample_project_conversation)

            assert result["project_name"] == "FitSocial - Fitness Challenge App"
            assert result["project_type"] == "mobile app"
            assert len(result["goals"]) == 2
            assert len(result["challenges"]) == 2

    def test_should_trigger_project_planning_function_exists(self):
        """Test that function to determine if project planning should trigger exists"""
        # This should now succeed
        from src.project_planning import should_trigger_project_planning
        assert callable(should_trigger_project_planning)
        
    @pytest.mark.asyncio
    async def test_should_trigger_project_planning_with_keywords(self):
        """Test project planning triggers for users with creativity profile but no project overview"""
        from src.project_planning import should_trigger_project_planning

        # Mock supabase client
        mock_supabase = MagicMock()
        
        # We need to mock two different table calls:
        # 1. Check for creativity profile (should return data - user has completed creativity test)
        # 2. Check for project overview (should return empty - user has not completed project planning)
        
        def mock_table_call(table_name):
            mock_table = MagicMock()
            if table_name == 'creator_creativity_profiles':
                # User has creativity profile 
                mock_table.select.return_value.eq.return_value.execute.return_value.data = [
                    {"user_id": "test-user", "creativity_score": 85}
                ]
            elif table_name == 'project_overview':
                # User has no project overview
                mock_table.select.return_value.eq.return_value.execute.return_value.data = []
            return mock_table
            
        mock_supabase.table.side_effect = mock_table_call

        result = await should_trigger_project_planning(mock_supabase, "test-user")
        assert result is True

    @pytest.mark.asyncio  
    async def test_should_not_trigger_project_planning_with_existing_project(self):
        """Test project planning doesn't trigger for users with existing projects"""
        from src.project_planning import should_trigger_project_planning

        # Mock supabase client
        mock_supabase = MagicMock()
        
        def mock_table_call(table_name):
            mock_table = MagicMock()
            if table_name == 'creator_creativity_profiles':
                # User has creativity profile 
                mock_table.select.return_value.eq.return_value.execute.return_value.data = [
                    {"user_id": "test-user", "creativity_score": 85}
                ]
            elif table_name == 'project_overview':
                # User already has project overview
                mock_table.select.return_value.eq.return_value.execute.return_value.data = [
                    {"id": "project-123", "user_id": "test-user"}
                ]
            return mock_table
            
        mock_supabase.table.side_effect = mock_table_call

        result = await should_trigger_project_planning(mock_supabase, "test-user")
        assert result is False

    @pytest.mark.asyncio  
    async def test_should_not_trigger_project_planning_without_creativity_profile(self):
        """Test project planning doesn't trigger for users without creativity profile"""
        from src.project_planning import should_trigger_project_planning

        # Mock supabase client
        mock_supabase = MagicMock()
        
        def mock_table_call(table_name):
            mock_table = MagicMock()
            if table_name == 'creator_creativity_profiles':
                # User has no creativity profile 
                mock_table.select.return_value.eq.return_value.execute.return_value.data = []
            elif table_name == 'project_overview':
                # User has no project overview either
                mock_table.select.return_value.eq.return_value.execute.return_value.data = []
            return mock_table
            
        mock_supabase.table.side_effect = mock_table_call

        result = await should_trigger_project_planning(mock_supabase, "test-user")
        assert result is False

    @pytest.mark.asyncio
    async def test_monitor_conversation_completion(self):
        """Test monitoring conversation for completion"""
        from src.project_planning import monitor_conversation_for_project_completion

        # Mock supabase client that returns no existing project
        mock_supabase = MagicMock()
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []

        # Comprehensive conversation covering key areas with completion signal
        comprehensive_conversation = [
            {"role": "user", "content": "My project is about creating a fitness app with project overview comprehensive plan project title main goals success metrics timeline weekly commitment zoom call current progress required resources potential roadblocks motivation strategies"},
            {"role": "user", "content": "My goal is to help people stay motivated"},
            {"role": "user", "content": "The target audience is busy professionals"},
            {"role": "user", "content": "Key features include social challenges and tracking"},
            {"role": "user", "content": "Timeline is 6 months for MVP"},
            {"role": "user", "content": "Main challenge will be user retention"},
            {"role": "user", "content": "Success metrics include daily active users"},
            {"role": "user", "content": "I have experience in mobile development"},
            {"role": "assistant", "content": "Perfect! We've covered all 8 topics. Let me create your comprehensive project overview now."}
        ]

        # Mock the AI analysis to return a valid project structure
        with patch('src.project_planning.analyze_conversation_for_project_info') as mock_analyze, \
             patch('src.project_planning.create_project_overview_from_conversation') as mock_create:
            
            mock_analyze.return_value = {
                "project_name": "Test Fitness App",
                "project_type": "mobile app",
                "description": "A fitness app",
                "goals": [],
                "challenges": [],
                "success_metrics": {}
            }
            mock_create.return_value = True

            result = await monitor_conversation_for_project_completion(
                mock_supabase, "test-user", comprehensive_conversation
            )

            assert result is True 