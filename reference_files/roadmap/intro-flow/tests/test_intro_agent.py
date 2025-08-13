#!/usr/bin/env python3
"""
Unit tests for IntroAgent - the new mandatory intro flow that replaced direct creativity entry
Tests conversation stages, name extraction, and transition logic
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.agents.intro_agent import IntroAgent

class TestIntroAgent:
    """Test the new mandatory intro flow"""
    
    @pytest.fixture
    def mock_flow_state_manager(self):
        """Mock FlowStateManager for testing"""
        mock_manager = Mock()
        return mock_manager
    
    @pytest.fixture
    def mock_llm_router(self):
        """Mock LLMRouter for testing"""
        mock_router = Mock()
        mock_router.generate_response = AsyncMock()
        return mock_router
    
    @pytest.fixture
    def intro_agent(self, mock_flow_state_manager, mock_llm_router):
        """Create IntroAgent with mocked dependencies"""
        agent = IntroAgent(mock_flow_state_manager, mock_llm_router)
        return agent
    
    def test_name_extraction_patterns(self, intro_agent):
        """Test robust name extraction from various user inputs"""
        test_cases = [
            ("Hi, I'm Sarah", "Sarah"),
            ("I'm Sarah Johnson", "Sarah Johnson"),
            ("My name is Emma", "Emma"),
            ("Call me Mike", "Mike"),
            ("I am Alex", "Alex"),
            ("Sarah here", "Sarah"),
            ("It's Mike", "Mike"),
            ("Hey, Sarah", "Sarah"),
            ("sarah", "Sarah"),  # Single word capitalize
            ("JOHN", "John"),   # All caps normalize
            ("Hi there, I'm wondering about this platform", None),  # No clear name
            ("What is this about?", None),  # Question, no name
        ]
        
        for input_text, expected_name in test_cases:
            result = intro_agent._extract_name(input_text)
            assert result == expected_name, f"Failed for input: '{input_text}'"
    
    def test_proceed_to_test_detection(self, intro_agent):
        """Test detection of user readiness to proceed"""
        proceed_cases = [
            ("Yes, I'm ready", True),
            ("Let's start", True),
            ("Sounds good", True),
            ("Let's do it", True),
            ("No questions", True),
            ("I have a question about privacy", False),
            ("What if I want to change my project later?", False),
            ("How does the AI remember things?", False),
        ]
        
        for input_text, should_proceed in proceed_cases:
            result = intro_agent._wants_to_proceed_to_test(input_text)
            assert result == should_proceed, f"Failed for input: '{input_text}'"
    
    def test_off_topic_question_detection(self, intro_agent):
        """Test detection of off-topic questions during intro"""
        # Stage 2 (name collection) - project questions are on-topic
        stage_2_cases = [
            ("What kind of projects do people usually work on?", False),  # On-topic
            ("How does Fridays at Four work?", False),  # On-topic
            ("What's the weather like?", True),  # Off-topic
            ("Can I use this for business projects?", False),  # On-topic
        ]
        
        for input_text, is_off_topic in stage_2_cases:
            result = intro_agent._is_off_topic_question(input_text, 2)
            assert result == is_off_topic, f"Stage 2 failed for: '{input_text}'"
    
    @pytest.mark.asyncio
    async def test_stage_1_welcome_message(self, intro_agent):
        """Test initial welcome and name request"""
        intro_agent.llm_router.generate_response.return_value = "Hi, I'm Hai. What's your name?"
        
        response = await intro_agent._generate_stage_response(1, {}, "Hi there")
        
        assert "name" in response.lower()
        intro_agent.llm_router.generate_response.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_stage_2_platform_explanation(self, intro_agent):
        """Test platform explanation after name collection"""
        intro_agent.llm_router.generate_response.return_value = "Nice to meet you, Sarah. This is where you keep track of your creative project..."
        
        context = {'name': 'Sarah'}
        response = await intro_agent._generate_stage_response(2, context, "Hi, I'm Sarah")
        
        assert "sarah" in response.lower()
        assert "creative project" in response.lower()
    
    @pytest.mark.asyncio
    async def test_stage_3_hai_explanation(self, intro_agent):
        """Test explanation of how Hai works"""
        intro_agent.llm_router.generate_response.return_value = "That sounds interesting. Here's how I work: I remember everything..."
        
        context = {'name': 'Emma', 'project_info': 'science fiction novel'}
        response = await intro_agent._generate_stage_response(3, context, "I'm working on a sci-fi novel")
        
        assert "remember" in response.lower()
        assert "accountability" in response.lower()
    
    @pytest.mark.asyncio
    async def test_stage_4_creative_test_intro(self, intro_agent):
        """Test creative test introduction"""
        intro_agent.llm_router.generate_response.return_value = "I'll learn your creative style through a quick test..."
        
        context = {'name': 'Alex', 'accountability_experience': 'Never worked with a coach before'}
        response = await intro_agent._generate_stage_response(4, context, "No coaching experience")
        
        assert "creative" in response.lower()
        assert "test" in response.lower() or "assessment" in response.lower()
    
    @pytest.mark.asyncio
    async def test_stage_5_question_handling(self, intro_agent):
        """Test question answering in final intro stage"""
        intro_agent.llm_router.generate_response.return_value = "Great question! Let me answer that..."
        
        context = {'name': 'Jordan'}
        response = await intro_agent._generate_stage_response(5, context, "How private is my data?")
        
        # Should answer the question
        intro_agent.llm_router.generate_response.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_creativity_test_transition(self, intro_agent):
        """Test smooth transition to creativity test"""
        # Mock creativity questions
        with patch('src.agents.intro_agent.CREATIVITY_QUESTIONS', [
            {
                'question': 'How do you approach new projects?',
                'options': {
                    'A': 'Plan everything first',
                    'B': 'Jump right in',
                    'C': 'Research extensively'
                }
            }
        ]):
            intro_agent.llm_router.generate_response.return_value = "Perfect! Let's start that creative personality test. Question 1 of 12: How do you approach new projects?"
            
            context = {'name': 'Sam'}
            response = await intro_agent._generate_creativity_test_start(context)
            
            assert "question 1" in response.lower()
            assert "how do you approach" in response.lower()
            assert "a, b" in response.lower() or "a." in response.lower()
    
    @pytest.mark.asyncio
    async def test_fallback_responses(self, intro_agent):
        """Test static fallback responses when LLM fails"""
        # Mock LLM failure
        intro_agent.llm_router.generate_response.side_effect = Exception("LLM failed")
        
        # Test each stage has fallback
        for stage in range(1, 6):
            response = await intro_agent._generate_stage_response(stage, {}, "test message")
            assert response is not None
            assert len(response) > 0
            assert "error" not in response.lower()  # Should be user-friendly
    
    @pytest.mark.asyncio
    async def test_off_topic_question_redirect(self, intro_agent):
        """Test gentle redirect for off-topic questions"""
        intro_agent.llm_router.generate_response.return_value = "That's interesting! We can explore that later. Right now I'm excited to learn about you..."
        
        context = {'name': 'Casey'}
        response = await intro_agent._handle_off_topic_question(context, "What's the weather like?")
        
        assert "later" in response.lower() or "explore" in response.lower()
        assert "learn about you" in response.lower() or "get to know" in response.lower()
    
    def test_conversation_context_building(self, intro_agent):
        """Test that conversation context is properly built through stages"""
        # Simulate stage progression
        context = {}
        
        # Stage 1 -> 2: Add name
        intro_agent._update_context_for_stage(context, 2, "Hi, I'm Taylor")
        assert context.get('name') == 'Taylor'
        
        # Stage 2 -> 3: Add project info
        intro_agent._update_context_for_stage(context, 3, "I'm writing a mystery novel")
        assert context.get('project_info') == 'I\'m writing a mystery novel'
        
        # Stage 3 -> 4: Add accountability experience
        intro_agent._update_context_for_stage(context, 4, "I've worked with a writing coach before")
        assert context.get('accountability_experience') == 'I\'ve worked with a writing coach before'
        
        # Context should accumulate
        assert len(context) == 3
    
    @pytest.mark.asyncio
    async def test_error_recovery(self, intro_agent):
        """Test graceful error recovery in intro flow"""
        # Mock database error in flow state manager
        intro_agent.flow_state_manager.get_intro_context.side_effect = Exception("DB error")
        
        # Should still provide fallback response
        response = await intro_agent.handle_message("test_user", "Hello", "thread_123")
        
        assert response is not None
        assert "Hi, I'm Hai" in response  # Default welcome message
    
    def test_stage_validation(self, intro_agent):
        """Test stage number validation"""
        # Valid stages should work
        for stage in range(1, 6):
            assert intro_agent._is_valid_stage(stage) == True
        
        # Invalid stages should be rejected
        assert intro_agent._is_valid_stage(0) == False
        assert intro_agent._is_valid_stage(7) == False
        assert intro_agent._is_valid_stage(-1) == False 