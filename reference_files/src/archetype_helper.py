#!/usr/bin/env python3
"""
Archetype Helper Functions

Contains functions for getting personalized prompts and settings based on user creativity archetypes.
This module provides the integration between the archetype system and the main AI agent.
"""

import logging
from typing import Tuple
from src.simple_memory import SimpleMemory

logger = logging.getLogger(__name__)

# Consistent temperature for all archetypes (no extreme variations)
CONSISTENT_TEMPERATURE = 0.6

# Archetype-specific style guidance templates
ARCHETYPE_STYLES = {
    1: """
    WORKING WITH A VISIONARY:
    This person thrives on big-picture thinking and creative possibilities. They get energized by connecting ideas and seeing how their project fits into larger themes. Help them connect current tasks to their bigger vision, ask questions that expand their thinking, and celebrate the unique perspective they bring. When they get stuck on details, help them zoom back out to see the bigger picture that motivates them.
    """,
    
    2: """
    WORKING WITH A STEADY BUILDER:
    This person finds satisfaction in consistent progress and methodical approaches. They appreciate clear next steps and steady momentum. Consistently acknowledge their steady effort and cumulative progress, help break overwhelming tasks into manageable daily actions, and celebrate the reliability of their process. When they feel impatient, remind them how their consistent approach creates lasting results.
    """,
    
    3: """
    WORKING WITH A COLLABORATIVE SPIRIT:
    This person gets energized by sharing ideas and building on feedback from others. They love the iterative process of refining ideas through conversation. Encourage them to share their work and get input from others, ask questions that help them think through different perspectives, and celebrate how their openness to collaboration strengthens their work. Help them see feedback as fuel for creativity.
    """,
    
    4: """
    WORKING WITH AN INTUITIVE EXPLORER:
    This person follows creative instincts and enjoys discovering where their ideas lead them. They work best when they have space to explore and experiment. Support their natural creative flow and trust in their instincts, help them capture insights as they emerge, and celebrate the unique discoveries that come from their exploratory approach. When they need structure, help them create flexible frameworks that support rather than constrain their exploration.
    """,
    
    5: """
    WORKING WITH A FOCUSED ACHIEVER:
    This person is driven by clear goals and measurable progress. They appreciate efficiency and results-oriented approaches. Help them set clear milestones and track meaningful progress, acknowledge their drive and determination, and celebrate when they hit important targets. When they feel overwhelmed, help them prioritize what matters most and break big goals into achievable steps.
    """,
    
    6: """
    WORKING WITH A CREATIVE CATALYST:
    This person brings energy and innovation to everything they touch. They love experimenting with new approaches and inspiring others. Encourage their creative experiments and bold ideas, help them channel their enthusiasm into focused action, and celebrate the unique energy they bring to their work. When they have too many ideas, help them choose which ones to pursue first while keeping space for creative exploration.
    """
}

# Default style guidance when no archetype is found
DEFAULT_ARCHETYPE_STYLE = """
WORKING WITH A CREATIVE INDIVIDUAL:
Adapt your approach based on what you observe about their working style and preferences. Pay attention to whether they prefer big-picture thinking or step-by-step progress, whether they like to work independently or collaboratively, and what kinds of support energize them most. Let their responses guide how you can best support their creative process.
"""

async def get_personalized_prompt_and_temperature(user_id: str, memory: SimpleMemory) -> Tuple[str, float]:
    """
    Get personalized system prompt and temperature based on user's archetype
    
    Args:
        user_id: User's ID to look up archetype for
        memory: SimpleMemory instance for database access
        
    Returns:
        tuple: (personalized_prompt, temperature)
    """
    try:
        # Import here to avoid circular imports
        from src.prompts import main_prompt
        
        # Get user's archetype
        archetype = await memory.get_user_archetype(user_id)
        
        # Get appropriate style guidance
        if archetype and archetype in ARCHETYPE_STYLES:
            archetype_guidance = ARCHETYPE_STYLES[archetype]
            logger.info(f"Using archetype {archetype} personalization for user {user_id}")
        else:
            archetype_guidance = DEFAULT_ARCHETYPE_STYLE
            logger.info(f"Using default archetype style for user {user_id}")
        
        # Format the main prompt with archetype guidance
        personalized_prompt = main_prompt.format(archetype_guidance=archetype_guidance)
        
        return personalized_prompt, CONSISTENT_TEMPERATURE
        
    except Exception as e:
        logger.error(f"Error getting personalized prompt for user {user_id}: {e}")
        # Fallback to default prompt
        from src.prompts import main_prompt
        fallback_prompt = main_prompt.format(archetype_guidance=DEFAULT_ARCHETYPE_STYLE)
        return fallback_prompt, CONSISTENT_TEMPERATURE 