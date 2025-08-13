#!/usr/bin/env python3
"""
Confidence Assessment Scoring Functions for WingmanMatch

Pure functions for calculating dating confidence archetype scores and experience levels.
Based on Connell Barrett's 6 confidence archetypes framework.

Functions:
- score_responses: Convert letter answers to archetype scores
- determine_primary_archetype: Select primary archetype from scores  
- calculate_experience_level: Determine beginner/intermediate/advanced level
"""

from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)

# Dating confidence archetypes based on Connell Barrett's framework
CONFIDENCE_ARCHETYPES = {
    "Analyzer": {
        "description": "Methodical, research-driven approach to dating",
        "traits": ["strategic", "prepared", "thoughtful", "systematic"]
    },
    "Sprinter": {
        "description": "Action-oriented, fast-moving confidence style",
        "traits": ["decisive", "bold", "energetic", "spontaneous"]
    },
    "Ghost": {
        "description": "Introverted, thoughtful, selective approach",
        "traits": ["selective", "introspective", "quality-focused", "patient"]
    },
    "Scholar": {
        "description": "Knowledge-focused, learning-based confidence",
        "traits": ["studious", "informed", "improvement-focused", "analytical"]
    },
    "Naturalist": {
        "description": "Authentic, instinctive dating approach",
        "traits": ["authentic", "instinctive", "genuine", "spontaneous"]
    },
    "Protector": {
        "description": "Caring, relationship-focused confidence style",
        "traits": ["caring", "supportive", "relationship-focused", "empathetic"]
    }
}

def score_responses(responses: Dict[str, str]) -> Dict[str, float]:
    """
    Convert letter responses (A, B, C, D, E, F) to archetype scores.
    
    Args:
        responses: Dict with keys like "question_1": "A", "question_2": "B", etc.
        
    Returns:
        Dict with archetype names as keys and scores as values
        
    Example:
        responses = {"question_1": "A", "question_2": "B"}
        returns = {"Analyzer": 1.0, "Sprinter": 1.0, "Ghost": 0.0, ...}
    """
    # Letter to archetype mapping (consistent across all questions)
    LETTER_TO_ARCHETYPE = {
        "A": "Analyzer",
        "B": "Sprinter", 
        "C": "Ghost",
        "D": "Scholar",
        "E": "Naturalist",
        "F": "Protector"
    }
    
    # Initialize scores
    scores = {archetype: 0.0 for archetype in CONFIDENCE_ARCHETYPES.keys()}
    
    # Count responses for each archetype
    for question_key, answer in responses.items():
        if answer and answer.upper() in LETTER_TO_ARCHETYPE:
            archetype = LETTER_TO_ARCHETYPE[answer.upper()]
            scores[archetype] += 1.0
    
    logger.info(f"Calculated archetype scores: {scores}")
    return scores

def determine_primary_archetype(scores: Dict[str, float]) -> str:
    """
    Select the primary archetype based on highest score.
    
    Args:
        scores: Dict with archetype names as keys and scores as values
        
    Returns:
        Name of the primary archetype
        
    In case of ties, returns the first archetype alphabetically
    """
    if not scores:
        logger.warning("No scores provided, defaulting to Naturalist")
        return "Naturalist"
    
    # Find archetype(s) with highest score
    max_score = max(scores.values())
    
    if max_score == 0:
        logger.warning("All scores are zero, defaulting to Naturalist")
        return "Naturalist"
    
    # Get all archetypes with max score
    top_archetypes = [archetype for archetype, score in scores.items() if score == max_score]
    
    # Return first alphabetically in case of tie
    primary = sorted(top_archetypes)[0]
    
    logger.info(f"Primary archetype determined: {primary} (score: {max_score})")
    return primary

def calculate_experience_level(scores: Dict[str, float], total_questions: int) -> str:
    """
    Calculate experience level based on total engagement across all archetypes.
    
    Args:
        scores: Dict with archetype names as keys and scores as values
        total_questions: Total number of questions in the assessment
        
    Returns:
        "beginner", "intermediate", or "advanced"
        
    Logic:
    - Beginner: < 60% of max possible engagement
    - Intermediate: 60-85% of max possible engagement  
    - Advanced: > 85% of max possible engagement
    """
    if total_questions <= 0:
        logger.warning("Invalid total_questions, defaulting to beginner")
        return "beginner"
    
    # Calculate total engagement (sum of all scores)
    total_engagement = sum(scores.values())
    max_possible = float(total_questions)  # Each question gives max 1 point
    
    # Calculate engagement percentage
    engagement_percentage = (total_engagement / max_possible) * 100 if max_possible > 0 else 0
    
    # Determine level based on engagement
    if engagement_percentage < 60:
        level = "beginner"
    elif engagement_percentage <= 85:
        level = "intermediate"
    else:
        level = "advanced"
    
    logger.info(f"Experience level calculated: {level} (engagement: {engagement_percentage:.1f}%)")
    return level

def calculate_confidence_assessment(responses: Dict[str, str], total_questions: int = 12) -> Dict[str, Any]:
    """
    Complete confidence assessment calculation combining all scoring functions.
    
    Args:
        responses: Dict with question responses
        total_questions: Total number of questions (default 12)
        
    Returns:
        Dict containing:
        - archetype_scores: Individual archetype scores
        - assigned_archetype: Primary archetype
        - experience_level: Calculated experience level
        - test_responses: Original responses
    """
    try:
        # Calculate archetype scores
        archetype_scores = score_responses(responses)
        
        # Determine primary archetype
        assigned_archetype = determine_primary_archetype(archetype_scores)
        
        # Calculate experience level
        experience_level = calculate_experience_level(archetype_scores, total_questions)
        
        result = {
            "archetype_scores": archetype_scores,
            "assigned_archetype": assigned_archetype,
            "experience_level": experience_level,
            "test_responses": responses
        }
        
        logger.info(f"Complete assessment calculated for {len(responses)} responses: {assigned_archetype}/{experience_level}")
        return result
        
    except Exception as e:
        logger.error(f"Error calculating confidence assessment: {e}")
        # Return safe defaults
        return {
            "archetype_scores": {archetype: 0.0 for archetype in CONFIDENCE_ARCHETYPES.keys()},
            "assigned_archetype": "Naturalist",
            "experience_level": "beginner", 
            "test_responses": responses
        }

def get_archetype_info(archetype_name: str) -> Optional[Dict[str, Any]]:
    """
    Get detailed information about a specific archetype.
    
    Args:
        archetype_name: Name of the archetype
        
    Returns:
        Dict with description and traits, or None if not found
    """
    return CONFIDENCE_ARCHETYPES.get(archetype_name)

def get_all_archetypes() -> Dict[str, Dict[str, Any]]:
    """
    Get information about all confidence archetypes.
    
    Returns:
        Dict with all archetype information
    """
    return CONFIDENCE_ARCHETYPES.copy()