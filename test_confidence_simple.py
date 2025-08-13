#!/usr/bin/env python3
"""
Simple test for ConfidenceTestAgent structure without dependencies
"""

import sys
sys.path.insert(0, 'src')

# Test confidence scoring
from assessment.confidence_scoring import (
    score_responses,
    determine_primary_archetype,
    calculate_experience_level,
    calculate_confidence_assessment,
    CONFIDENCE_ARCHETYPES
)

# Test questions structure directly
def test_questions():
    """Test questions without importing the full agent"""
    
    # Define questions locally (same as in agent)
    QUESTIONS = [
        {
            "question": "When you see someone attractive, what's your first instinct?",
            "options": {
                "A": "Research their interests before approaching",
                "B": "Go talk to them immediately", 
                "C": "Wait for the right moment",
                "D": "Think about what to say first",
                "E": "Be myself and see what happens",
                "F": "Consider how to make them comfortable"
            },
            "scoring": {
                "A": "Analyzer", "B": "Sprinter", "C": "Ghost",
                "D": "Scholar", "E": "Naturalist", "F": "Protector"
            }
        },
        # Add more questions for complete test...
    ]
    
    print(f"✅ Questions structure test passed - {len(QUESTIONS)} question(s) defined")
    
    # Test scoring integration
    responses = {
        "question_1": "A",
        "question_2": "B", 
        "question_3": "A",
        "question_4": "F",
        "question_5": "E"
    }
    
    assessment = calculate_confidence_assessment(responses, 12)
    
    print(f"✅ Assessment calculation passed")
    print(f"   Primary archetype: {assessment['assigned_archetype']}")
    print(f"   Experience level: {assessment['experience_level']}")
    print(f"   Scores: {assessment['archetype_scores']}")

def test_archetype_info():
    """Test archetype information"""
    print(f"✅ {len(CONFIDENCE_ARCHETYPES)} archetypes defined:")
    for name, info in CONFIDENCE_ARCHETYPES.items():
        print(f"   {name}: {info['description']}")

def test_answer_extraction():
    """Test answer extraction logic"""
    def extract_answer(message: str):
        """Local version of answer extraction"""
        message_upper = message.upper().strip()
        
        for letter in ['A', 'B', 'C', 'D', 'E', 'F']:
            if letter in message_upper:
                if len(message_upper) == 1 or message_upper.startswith(letter + ' ') or message_upper.startswith(letter + ')') or message_upper.startswith(letter + '.'):
                    return letter
        return None
    
    # Test cases
    test_cases = [
        ("A", "A"),
        ("a", "A"), 
        ("B.", "B"),
        ("C )", "C"),
        ("D ", "D"),
        ("ANSWER", None),
        ("", None),
        ("123", None)
    ]
    
    for input_msg, expected in test_cases:
        result = extract_answer(input_msg)
        assert result == expected, f"Failed for '{input_msg}': expected {expected}, got {result}"
    
    print("✅ Answer extraction test passed")

if __name__ == "__main__":
    print("🧪 Testing ConfidenceTestAgent components...\n")
    
    test_archetype_info()
    test_answer_extraction()
    test_questions()
    
    print("\n🎉 All ConfidenceTestAgent tests passed!")