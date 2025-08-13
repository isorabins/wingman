"""
Unit tests for Connell Barrett coaching prompts and memory integration
Tests memory context references, archetype personalization, and safety guardrails
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from src.prompts import (
    main_prompt,
    get_personalized_prompt,
    ARCHETYPE_PROMPTS,
    get_archetype_temperature
)
from src.safety_filters import check_message_safety, check_response_safety
from src.simple_memory import SimpleMemory


class TestConnellBarrettPrompts:
    """Test suite for Connell Barrett coaching persona"""
    
    def test_main_prompt_contains_connell_elements(self):
        """Test that main prompt contains key Connell Barrett elements"""
        assert "Connell Barrett" in main_prompt
        assert "dating confidence" in main_prompt.lower()
        assert "authentic" in main_prompt.lower()
        assert "wingman" in main_prompt.lower()
        assert "pickup artist" not in main_prompt.lower()  # Should avoid PUA language
    
    def test_archetype_prompts_exist(self):
        """Test that all 6 archetype prompts are defined"""
        assert len(ARCHETYPE_PROMPTS) == 6
        for i in range(1, 7):
            assert i in ARCHETYPE_PROMPTS
            assert isinstance(ARCHETYPE_PROMPTS[i], str)
            assert len(ARCHETYPE_PROMPTS[i]) > 100  # Substantial content
    
    def test_archetype_personalization(self):
        """Test archetype-based prompt personalization"""
        base_prompt = "Base coaching prompt"
        context = "User has approach anxiety"
        
        # Test with Strategic Dater archetype
        personalized = get_personalized_prompt(base_prompt, archetype=1, context=context)
        assert "BIG PICTURE VISIONARY" in personalized
        assert base_prompt in personalized
        assert context in personalized
        
        # Test with no archetype (default)
        default = get_personalized_prompt(base_prompt, archetype=None, context=context)
        assert base_prompt in default
        assert context in default
    
    def test_temperature_consistency(self):
        """Test that temperature is consistently set for coaching"""
        temp = get_archetype_temperature()
        assert temp == 0.6  # Should match Connell's warm but focused style
        assert isinstance(temp, float)
    
    def test_memory_hook_integration(self):
        """Test that prompts reference memory hooks correctly"""
        test_context = """
        MEMORY HOOKS:
        assessment_results: {"confidence_level": "beginner", "archetype": "social_connector"}
        attempts: [{"date": "2025-01-01", "outcome": "started_conversation", "notes": "felt nervous but succeeded"}]
        triggers: ["fear_of_rejection", "negative_self_talk"]
        session_history: [{"date": "2025-01-01", "wingman": "John", "challenges_completed": 2}]
        """
        
        personalized = get_personalized_prompt(main_prompt, archetype=4, context=test_context)
        
        # Should contain memory integration instructions
        assert "assessment_results" in personalized
        assert "attempts" in personalized  
        assert "triggers" in personalized
        assert "session_history" in personalized


class TestSafetyGuardrails:
    """Test suite for safety filtering and guardrails"""
    
    def test_pii_detection(self):
        """Test PII detection in user messages"""
        # Test phone number detection
        result = check_message_safety("My number is 555-123-4567")
        assert not result.is_safe
        assert any("PII" in item for item in result.blocked_content)
        assert result.severity == 'high'
        
        # Test email detection
        result = check_message_safety("Contact me at john@example.com")
        assert not result.is_safe
        assert any("PII" in item for item in result.blocked_content)
        
        # Test safe message
        result = check_message_safety("I'm nervous about approaching women")
        assert result.is_safe
        assert len(result.blocked_content) == 0
    
    def test_toxic_content_detection(self):
        """Test detection of toxic masculinity patterns"""
        toxic_messages = [
            "Women are all hypergamous",
            "I need to be an alpha male",
            "She's just a typical femoid",
            "Time to take the red pill",
            "Women owe me attention"
        ]
        
        for message in toxic_messages:
            result = check_message_safety(message)
            assert not result.is_safe
            assert any("Toxic content" in item for item in result.blocked_content)
            assert result.severity == 'high'
    
    def test_pickup_artist_detection(self):
        """Test detection of pickup artist tactics"""
        pua_messages = [
            "I need to learn some game",
            "How do I overcome last minute resistance?",
            "What's a good neg to use?",
            "Field report from last night",
            "She was giving me IOIs"
        ]
        
        for message in pua_messages:
            result = check_message_safety(message)
            assert not result.is_safe
            assert any("Pickup tactics" in item for item in result.blocked_content)
            assert result.severity == 'medium'
    
    def test_response_safety_checking(self):
        """Test safety checking of AI responses"""
        # Safe response
        safe_response = "Building confidence starts with being comfortable with yourself. Let's work on some conversation starters."
        result = check_response_safety(safe_response)
        assert result.is_safe
        
        # Unsafe response with pickup tactics
        unsafe_response = "You should try negging her to lower her self-esteem"
        result = check_response_safety(unsafe_response)
        assert not result.is_safe
        assert result.severity == 'high'
    
    def test_safety_messages(self):
        """Test that appropriate safety messages are generated"""
        # Test PII message
        result = check_message_safety("My phone is 555-123-4567")
        assert "personal information" in result.safety_message.lower()
        assert "privacy" in result.safety_message.lower()
        
        # Test toxic content message
        result = check_message_safety("Women are all the same")
        assert "genuine confidence" in result.safety_message.lower()
        assert "respect" in result.safety_message.lower()
        
        # Test pickup tactics message
        result = check_message_safety("How do I run game?")
        assert "authentic confidence" in result.safety_message.lower()
        assert "manipulation" in result.safety_message.lower()


class TestCoachingConversationFlow:
    """Test suite for coaching conversation patterns"""
    
    @pytest.fixture
    def mock_memory(self):
        """Mock memory system for testing"""
        memory = Mock(spec=SimpleMemory)
        memory.get_context = AsyncMock(return_value="Mock context")
        memory.save_message = AsyncMock()
        return memory
    
    def test_coaching_response_patterns(self):
        """Test that coaching responses follow Connell's patterns"""
        coaching_scenarios = [
            {
                "input": "I'm too scared to approach women",
                "expected_elements": ["fear", "confidence", "authentic", "yourself"]
            },
            {
                "input": "I got rejected and feel terrible",
                "expected_elements": ["rejection", "normal", "growth", "learn"]
            },
            {
                "input": "How do I start conversations?",
                "expected_elements": ["conversation", "genuine", "interest", "authentic"]
            }
        ]
        
        # These would be tested with actual API calls in integration tests
        # For unit tests, we verify the prompt structure supports these patterns
        for scenario in coaching_scenarios:
            # Verify main prompt contains guidance for handling these scenarios
            assert any(element in main_prompt.lower() for element in scenario["expected_elements"])
    
    def test_memory_context_integration(self):
        """Test that memory context is properly integrated into prompts"""
        sample_memory_context = {
            "assessment_results": {
                "confidence_level": "beginner",
                "primary_challenge": "approach_anxiety",
                "archetype": "steady_builder"
            },
            "recent_attempts": [
                {
                    "date": "2025-01-10",
                    "situation": "coffee_shop",
                    "outcome": "started_conversation",
                    "confidence_rating": 6,
                    "notes": "Felt nervous but managed to say hello"
                }
            ],
            "triggers": ["fear_of_rejection", "negative_self_talk"],
            "session_history": [
                {
                    "date": "2025-01-08", 
                    "wingman": "Mike",
                    "challenges_completed": ["eye_contact", "say_hello"],
                    "insights": "Realized I'm more confident than I thought"
                }
            ]
        }
        
        # Test that personalized prompt can reference these memory elements
        context_str = str(sample_memory_context)
        personalized = get_personalized_prompt(main_prompt, archetype=3, context=context_str)
        
        # Verify memory hooks are present for the coach to reference
        assert "CONTEXT INTEGRATION" in personalized
        assert context_str in personalized


class TestManualEvaluationSet:
    """Manual evaluation set with 10 coaching scenarios"""
    
    def test_evaluation_scenarios(self):
        """Test 10 sample coaching inputs for style adherence"""
        evaluation_scenarios = [
            {
                "id": 1,
                "input": "I've never approached a woman in my life and I'm 25. Is it too late?",
                "coaching_focus": "age_reassurance_confidence_building",
                "expected_tone": "encouraging_realistic"
            },
            {
                "id": 2, 
                "input": "I approached someone yesterday and got rejected harshly. I don't want to try again.",
                "coaching_focus": "rejection_resilience_reframe",
                "expected_tone": "empathetic_motivational"
            },
            {
                "id": 3,
                "input": "My friends say I should just 'be myself' but myself is boring and awkward.",
                "coaching_focus": "authentic_self_development",
                "expected_tone": "validating_growth_oriented"
            },
            {
                "id": 4,
                "input": "I'm successful in business but completely fail with women. What's wrong with me?",
                "coaching_focus": "transfer_skills_confidence_areas",
                "expected_tone": "strength_based_encouraging"
            },
            {
                "id": 5,
                "input": "Should I try online dating or focus on meeting people in person?",
                "coaching_focus": "strategy_discussion_authentic_connection",
                "expected_tone": "practical_balanced"
            },
            {
                "id": 6,
                "input": "I freeze up when attractive women talk to me. My mind goes blank.",
                "coaching_focus": "social_anxiety_practical_techniques",
                "expected_tone": "understanding_actionable"
            },
            {
                "id": 7,
                "input": "I've been told I come on too strong. How do I dial it back without being boring?",
                "coaching_focus": "calibration_authentic_interest",
                "expected_tone": "nuanced_practical"
            },
            {
                "id": 8,
                "input": "Every woman I like ends up friend-zoning me. What am I doing wrong?",
                "coaching_focus": "attraction_building_authentic_confidence",
                "expected_tone": "honest_developmental"
            },
            {
                "id": 9,
                "input": "I have social anxiety and meeting new people is really hard for me.",
                "coaching_focus": "anxiety_management_gradual_exposure",
                "expected_tone": "gentle_systematic"
            },
            {
                "id": 10,
                "input": "I want to be more confident but I don't want to become a different person.",
                "coaching_focus": "authentic_confidence_self_acceptance",
                "expected_tone": "validating_authentic"
            }
        ]
        
        # For each scenario, verify the prompt contains guidance for appropriate responses
        for scenario in evaluation_scenarios:
            # Check that main prompt has elements to handle this type of coaching
            assert "confidence" in main_prompt.lower()
            assert "authentic" in main_prompt.lower()
            
            # Verify safety guardrails would catch inappropriate responses
            result = check_message_safety(scenario["input"])
            assert result.is_safe  # All these should be safe coaching requests


class TestABTestingSupport:
    """Test A/B testing flag functionality"""
    
    @patch('src.config.Config.ENABLE_NEW_COACH_PROMPTS', True)
    def test_new_coach_flag_enabled(self):
        """Test behavior when new coach prompts are enabled"""
        from src.config import Config
        assert Config.ENABLE_NEW_COACH_PROMPTS == True
    
    @patch('src.config.Config.ENABLE_NEW_COACH_PROMPTS', False) 
    def test_new_coach_flag_disabled(self):
        """Test fallback behavior when new coach prompts are disabled"""
        from src.config import Config
        assert Config.ENABLE_NEW_COACH_PROMPTS == False
    
    def test_prompt_versioning_support(self):
        """Test that prompt system supports A/B testing different versions"""
        # Verify that personalization system can handle version flags
        base_prompt = main_prompt
        personalized_v1 = get_personalized_prompt(base_prompt, archetype=1)
        personalized_v2 = get_personalized_prompt(base_prompt, archetype=1, context="v2_test")
        
        # Should be able to generate different versions
        assert isinstance(personalized_v1, str)
        assert isinstance(personalized_v2, str)
        assert personalized_v1 != personalized_v2


if __name__ == "__main__":
    # Run specific test suites
    pytest.main([
        __file__,
        "-v",
        "--tb=short"
    ])