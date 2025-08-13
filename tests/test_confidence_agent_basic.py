#!/usr/bin/env python3
"""
Basic integration test for ConfidenceTestAgent

Tests the agent's question flow and answer parsing without requiring database connection.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from agents.confidence_agent import ConfidenceTestAgent

def test_answer_extraction():
    """Test the _extract_answer method"""
    
    # Create a mock agent (without database)
    class MockAgent(ConfidenceTestAgent):
        def __init__(self):
            # Skip parent init to avoid database dependency
            pass
    
    agent = MockAgent()
    
    # Test valid answers
    assert agent._extract_answer("A") == "A"
    assert agent._extract_answer("a") == "A"
    assert agent._extract_answer("B.") == "B"
    assert agent._extract_answer("C )") == "C"
    assert agent._extract_answer("D ") == "D"
    assert agent._extract_answer("E") == "E"
    assert agent._extract_answer("F") == "F"
    
    # Test invalid answers
    assert agent._extract_answer("X") is None
    assert agent._extract_answer("ANSWER") is None
    assert agent._extract_answer("") is None
    assert agent._extract_answer("123") is None
    
    print("Answer extraction tests passed!")

def test_questions_structure():
    """Test that questions are properly structured"""
    questions = ConfidenceTestAgent.QUESTIONS
    
    # Should have 12 questions
    assert len(questions) == 12, f"Expected 12 questions, got {len(questions)}"
    
    # Each question should have proper structure
    for i, question in enumerate(questions):
        assert "question" in question, f"Question {i+1} missing 'question' field"
        assert "options" in question, f"Question {i+1} missing 'options' field"
        assert "scoring" in question, f"Question {i+1} missing 'scoring' field"
        
        # Should have 6 options (A through F)
        options = question["options"]
        assert len(options) == 6, f"Question {i+1} should have 6 options, got {len(options)}"
        expected_keys = {"A", "B", "C", "D", "E", "F"}
        assert set(options.keys()) == expected_keys, f"Question {i+1} options keys incorrect"
        
        # Scoring should map to valid archetypes
        scoring = question["scoring"]
        assert len(scoring) == 6, f"Question {i+1} should have 6 scoring entries"
        valid_archetypes = {"Analyzer", "Sprinter", "Ghost", "Scholar", "Naturalist", "Protector"}
        for letter, archetype in scoring.items():
            assert letter in expected_keys, f"Question {i+1} scoring has invalid letter {letter}"
            assert archetype in valid_archetypes, f"Question {i+1} scoring has invalid archetype {archetype}"
    
    print("Questions structure tests passed!")

def test_archetype_coverage():
    """Test that all archetypes are represented across questions"""
    questions = ConfidenceTestAgent.QUESTIONS
    archetype_counts = {}
    
    for question in questions:
        for archetype in question["scoring"].values():
            archetype_counts[archetype] = archetype_counts.get(archetype, 0) + 1
    
    # All 6 archetypes should be represented
    expected_archetypes = {"Analyzer", "Sprinter", "Ghost", "Scholar", "Naturalist", "Protector"}
    assert set(archetype_counts.keys()) == expected_archetypes, "Not all archetypes represented"
    
    # Each archetype should appear multiple times (balanced distribution)
    for archetype, count in archetype_counts.items():
        assert count > 0, f"Archetype {archetype} not represented"
        # With 12 questions and 6 archetypes, each should appear at least once
        # In practice, should be roughly balanced
    
    print(f"Archetype coverage tests passed! Distribution: {archetype_counts}")

def test_dating_context():
    """Test that questions are focused on dating scenarios"""
    questions = ConfidenceTestAgent.QUESTIONS
    
    # Check for dating-related keywords in questions
    dating_keywords = [
        "dating", "date", "attractive", "rejection", "romantic", "relationship",
        "approach", "interest", "partner", "social", "conversation", "app",
        "confident", "feelings", "boundaries"
    ]
    
    questions_with_dating_context = 0
    for question in questions:
        question_text = question["question"].lower()
        if any(keyword in question_text for keyword in dating_keywords):
            questions_with_dating_context += 1
    
    # Most questions should have clear dating context
    assert questions_with_dating_context >= 8, f"Only {questions_with_dating_context} questions have dating context"
    
    print("Dating context tests passed!")

if __name__ == "__main__":
    test_answer_extraction()
    test_questions_structure()
    test_archetype_coverage()
    test_dating_context()
    print("\nAll ConfidenceTestAgent tests passed! ✅")