#!/usr/bin/env python3
"""
Unit tests for confidence scoring functions

Tests the pure functions for calculating dating confidence archetype scores and experience levels.
"""

import pytest
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from assessment.confidence_scoring import (
    score_responses,
    determine_primary_archetype,
    calculate_experience_level,
    calculate_confidence_assessment,
    get_archetype_info,
    get_all_archetypes,
    CONFIDENCE_ARCHETYPES
)

class TestScoreResponses:
    """Test the score_responses function"""
    
    def test_empty_responses(self):
        """Test with empty responses"""
        result = score_responses({})
        expected = {archetype: 0.0 for archetype in CONFIDENCE_ARCHETYPES.keys()}
        assert result == expected
    
    def test_single_response(self):
        """Test with single response"""
        responses = {"question_1": "A"}
        result = score_responses(responses)
        
        assert result["Analyzer"] == 1.0
        assert result["Sprinter"] == 0.0
        assert result["Ghost"] == 0.0
        assert result["Scholar"] == 0.0
        assert result["Naturalist"] == 0.0
        assert result["Protector"] == 0.0
    
    def test_multiple_responses(self):
        """Test with multiple responses"""
        responses = {
            "question_1": "A",  # Analyzer
            "question_2": "A",  # Analyzer
            "question_3": "B",  # Sprinter
            "question_4": "F"   # Protector
        }
        result = score_responses(responses)
        
        assert result["Analyzer"] == 2.0
        assert result["Sprinter"] == 1.0
        assert result["Ghost"] == 0.0
        assert result["Scholar"] == 0.0
        assert result["Naturalist"] == 0.0
        assert result["Protector"] == 1.0
    
    def test_case_insensitive(self):
        """Test that responses are case-insensitive"""
        responses = {"question_1": "a", "question_2": "B"}
        result = score_responses(responses)
        
        assert result["Analyzer"] == 1.0
        assert result["Sprinter"] == 1.0
    
    def test_invalid_responses(self):
        """Test with invalid response letters"""
        responses = {
            "question_1": "A",  # Valid
            "question_2": "X",  # Invalid
            "question_3": "",   # Empty
            "question_4": None  # None
        }
        result = score_responses(responses)
        
        assert result["Analyzer"] == 1.0
        assert sum(result.values()) == 1.0  # Only one valid response

class TestDeterminePrimaryArchetype:
    """Test the determine_primary_archetype function"""
    
    def test_clear_winner(self):
        """Test with clear highest score"""
        scores = {
            "Analyzer": 3.0,
            "Sprinter": 1.0,
            "Ghost": 0.0,
            "Scholar": 2.0,
            "Naturalist": 1.0,
            "Protector": 0.0
        }
        result = determine_primary_archetype(scores)
        assert result == "Analyzer"
    
    def test_tie_alphabetical_order(self):
        """Test that ties are resolved alphabetically"""
        scores = {
            "Analyzer": 2.0,
            "Sprinter": 2.0,  # Same as Analyzer
            "Ghost": 1.0,
            "Scholar": 0.0,
            "Naturalist": 0.0,
            "Protector": 0.0
        }
        result = determine_primary_archetype(scores)
        assert result == "Analyzer"  # Comes first alphabetically
    
    def test_all_zeros(self):
        """Test with all zero scores"""
        scores = {archetype: 0.0 for archetype in CONFIDENCE_ARCHETYPES.keys()}
        result = determine_primary_archetype(scores)
        assert result == "Naturalist"  # Default
    
    def test_empty_scores(self):
        """Test with empty scores dict"""
        result = determine_primary_archetype({})
        assert result == "Naturalist"  # Default

class TestCalculateExperienceLevel:
    """Test the calculate_experience_level function"""
    
    def test_beginner_level(self):
        """Test beginner level calculation (< 60%)"""
        scores = {
            "Analyzer": 2.0,
            "Sprinter": 1.0,
            "Ghost": 0.0,
            "Scholar": 0.0,
            "Naturalist": 0.0,
            "Protector": 0.0
        }
        # Total engagement: 3.0 / 12.0 = 25%
        result = calculate_experience_level(scores, 12)
        assert result == "beginner"
    
    def test_intermediate_level(self):
        """Test intermediate level calculation (60-85%)"""
        scores = {
            "Analyzer": 3.0,
            "Sprinter": 2.0,
            "Ghost": 1.0,
            "Scholar": 2.0,
            "Naturalist": 1.0,
            "Protector": 0.0
        }
        # Total engagement: 9.0 / 12.0 = 75%
        result = calculate_experience_level(scores, 12)
        assert result == "intermediate"
    
    def test_advanced_level(self):
        """Test advanced level calculation (> 85%)"""
        scores = {
            "Analyzer": 3.0,
            "Sprinter": 3.0,
            "Ghost": 2.0,
            "Scholar": 3.0,
            "Naturalist": 1.0,
            "Protector": 0.0
        }
        # Total engagement: 12.0 / 12.0 = 100%
        result = calculate_experience_level(scores, 12)
        assert result == "advanced"
    
    def test_invalid_total_questions(self):
        """Test with invalid total_questions"""
        scores = {"Analyzer": 5.0}
        result = calculate_experience_level(scores, 0)
        assert result == "beginner"  # Default for invalid input

class TestCalculateConfidenceAssessment:
    """Test the complete assessment calculation"""
    
    def test_complete_assessment(self):
        """Test complete assessment flow"""
        responses = {
            "question_1": "A",  # Analyzer
            "question_2": "A",  # Analyzer
            "question_3": "A",  # Analyzer
            "question_4": "B",  # Sprinter
            "question_5": "C",  # Ghost
            "question_6": "D",  # Scholar
            "question_7": "E",  # Naturalist
            "question_8": "F",  # Protector
            "question_9": "A",  # Analyzer
            "question_10": "A", # Analyzer
            "question_11": "A", # Analyzer
            "question_12": "A"  # Analyzer
        }
        
        result = calculate_confidence_assessment(responses, 12)
        
        # Verify structure
        assert "archetype_scores" in result
        assert "assigned_archetype" in result
        assert "experience_level" in result
        assert "test_responses" in result
        
        # Verify values
        assert result["assigned_archetype"] == "Analyzer"  # Should win with 7 points
        assert result["experience_level"] == "advanced"   # 12/12 = 100%
        assert result["test_responses"] == responses
        
        # Verify scores
        scores = result["archetype_scores"]
        assert scores["Analyzer"] == 7.0
        assert scores["Sprinter"] == 1.0
        assert scores["Ghost"] == 1.0
        assert scores["Scholar"] == 1.0
        assert scores["Naturalist"] == 1.0
        assert scores["Protector"] == 1.0
    
    def test_assessment_with_error_handling(self):
        """Test assessment handles errors gracefully"""
        # This should not raise an exception
        result = calculate_confidence_assessment(None, 12)
        
        # Should return safe defaults
        assert result["assigned_archetype"] == "Naturalist"
        assert result["experience_level"] == "beginner"
        assert "archetype_scores" in result
        assert "test_responses" in result

class TestArchetypeInfo:
    """Test archetype information functions"""
    
    def test_get_archetype_info_valid(self):
        """Test getting valid archetype info"""
        info = get_archetype_info("Analyzer")
        assert info is not None
        assert "description" in info
        assert "traits" in info
        assert info["description"] == "Methodical, research-driven approach to dating"
    
    def test_get_archetype_info_invalid(self):
        """Test getting invalid archetype info"""
        info = get_archetype_info("InvalidArchetype")
        assert info is None
    
    def test_get_all_archetypes(self):
        """Test getting all archetypes"""
        all_archetypes = get_all_archetypes()
        assert len(all_archetypes) == 6
        assert "Analyzer" in all_archetypes
        assert "Sprinter" in all_archetypes
        assert "Ghost" in all_archetypes
        assert "Scholar" in all_archetypes
        assert "Naturalist" in all_archetypes
        assert "Protector" in all_archetypes
        
        # Verify structure
        for archetype, info in all_archetypes.items():
            assert "description" in info
            assert "traits" in info
            assert isinstance(info["traits"], list)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])