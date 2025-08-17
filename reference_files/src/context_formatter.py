#!/usr/bin/env python3
"""
Context Formatter for Claude Prompt Caching

Formats user context for optimal Claude prompt caching performance.
Ensures consistent output for identical input to enable caching.
"""

import json
from typing import Dict, Any


def format_static_context_for_caching(static_context: Dict[str, Any]) -> str:
    """
    Format static user context into consistent structure for Claude prompt caching.
    
    CRITICAL: This function MUST produce identical output for identical input
    to enable Claude prompt caching. Order and format must never change.
    """
    
    context_parts = []
    
    # === USER PROFILE SECTION (Always first, consistent order) ===
    context_parts.append("=== USER PROFILE ===")
    
    profile = static_context.get("user_profile")
    if profile and isinstance(profile, dict):
        context_parts.append(f"User ID: {profile.get('id', 'unknown')}")
        context_parts.append(f"Name: {profile.get('first_name', '')} {profile.get('last_name', '')}")
        context_parts.append(f"Email: {profile.get('slack_email', 'not provided')}")
        
        # Add preferences if they exist
        prefs = profile.get('preferences', {})
        if prefs and isinstance(prefs, dict):
            context_parts.append(f"Preferences: {json.dumps(prefs, sort_keys=True)}")
        
        context_parts.append(f"Interaction Count: {profile.get('interaction_count', 0)}")
    else:
        context_parts.append("Profile: Not created yet")
    
    context_parts.append("")  # Blank line separator
    
    # === CREATIVITY PROFILE SECTION (Always second, after user profile) ===
    context_parts.append("=== CREATIVITY PROFILE ===")
    
    creativity_profile = static_context.get("creativity_profile")
    if creativity_profile and isinstance(creativity_profile, dict):
        archetype = creativity_profile.get('archetype', 'unknown')
        context_parts.append(f"Creative Archetype: {archetype.replace('_', ' ').title()}")
        
        secondary = creativity_profile.get('secondary_archetype')
        if secondary:
            context_parts.append(f"Secondary Archetype: {secondary.replace('_', ' ').title()}")
        
        # Add archetype scores for AI understanding
        primary_score = creativity_profile.get('archetype_score', 0)
        secondary_score = creativity_profile.get('secondary_score', 0)
        context_parts.append(f"Primary Score: {primary_score}/5, Secondary Score: {secondary_score}/5")
        
        # Add test date for context
        date_taken = creativity_profile.get('date_taken')
        if date_taken:
            context_parts.append(f"Test Completed: {date_taken}")
            
        # Add brief archetype guidance for AI
        archetype_guidance = {
            'big_picture_visionary': 'Focus on vision, impact, and meaning. Appreciate big-picture discussions.',
            'knowledge_seeker': 'Values research, learning, and thorough understanding. Appreciates detailed explanations.',
            'authentic_creator': 'Values personal expression and authenticity. Appreciates emotional connection.',
            'practical_builder': 'Values structure, clear steps, and practical outcomes. Appreciates actionable advice.',
            'people_connector': 'Values collaboration, feedback, and community. Appreciates social aspects.',
            'innovative_explorer': 'Values novelty, experimentation, and discovery. Appreciates creative approaches.'
        }
        
        guidance = archetype_guidance.get(archetype, 'Personalize approach based on creative preferences.')
        context_parts.append(f"AI Guidance: {guidance}")
    else:
        context_parts.append("Status: Creativity profile not completed yet")
        context_parts.append("Recommendation: Guide user through creativity assessment first")
    
    context_parts.append("")  # Blank line separator
    
    # === PROJECT DATA SECTION (Now third, consistent order) ===
    context_parts.append("=== PROJECT DATA ===")
    
    project = static_context.get("project_overview")
    if project and isinstance(project, dict):
        context_parts.append(f"Project Name: {project.get('project_name', 'Unnamed Project')}")
        context_parts.append(f"Project Type: {project.get('project_type', 'Not specified')}")
        context_parts.append(f"Description: {project.get('description', 'No description')}")
        
        # Goals (formatted consistently)
        goals = project.get('goals', [])
        if goals and isinstance(goals, list):
            context_parts.append("Goals:")
            for i, goal in enumerate(goals, 1):
                context_parts.append(f"  {i}. {goal}")
        
        # Challenges (formatted consistently)  
        challenges = project.get('challenges', [])
        if challenges and isinstance(challenges, list):
            context_parts.append("Challenges:")
            for i, challenge in enumerate(challenges, 1):
                context_parts.append(f"  {i}. {challenge}")
    else:
        context_parts.append("Status: No project overview yet")
        context_parts.append("Recommendation: Guide user through project planning")
    
    context_parts.append("")  # Blank line separator
    
    # === PROJECT UPDATES SECTION ===
    context_parts.append("=== RECENT PROJECT UPDATES ===")
    updates = static_context.get("project_updates", [])
    if updates and isinstance(updates, list):
        for update in updates[:5]:  # Last 5 updates
            if isinstance(update, dict):
                context_parts.append(f"Date: {update.get('created_at', 'Unknown')}")
                context_parts.append(f"Update: {update.get('content', 'No content')}")
                context_parts.append("")
    else:
        context_parts.append("No recent project updates")
    
    context_parts.append("")  # Blank line separator
    
    # === LONG-TERM MEMORY SECTION ===
    context_parts.append("=== LONG-TERM MEMORY CONTEXT ===")
    summaries = static_context.get("longterm_summaries", [])
    if summaries and isinstance(summaries, list):
        for summary in summaries[:5]:  # Last 5 summaries
            if isinstance(summary, dict):
                context_parts.append(f"Date: {summary.get('created_at', 'Unknown')}")
                context_parts.append(f"Summary: {summary.get('content', 'No content')}")
                context_parts.append("")
    else:
        context_parts.append("No long-term memory summaries available")
    
    return "\n".join(context_parts)


def get_cache_control_header() -> Dict[str, str]:
    """
    Return headers required to enable Claude prompt caching.
    """
    return {
        "anthropic-beta": "prompt-caching-2024-07-31"
    } 