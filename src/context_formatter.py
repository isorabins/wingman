#!/usr/bin/env python3
"""
Context Formatter for WingmanMatch - Connell Barrett Coaching System

Optimizes coaching context for Claude API prompt caching by:
- Formatting coaching context for prompt caching efficiency
- Integrating assessment results, attempts, triggers, session history
- Optimizing context size and structure for caching
- Handling missing context gracefully
"""

import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timezone
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ContextCacheInfo:
    """Information about context caching optimization"""
    cache_key: str
    context_size: int
    compression_ratio: float
    cacheable: bool
    cache_ttl: int = 1800  # 30 minutes default

class CoachingContextFormatter:
    """Formats and optimizes coaching context for Claude API prompt caching"""
    
    def __init__(self, max_context_size: int = 8000, enable_compression: bool = True):
        self.max_context_size = max_context_size
        self.enable_compression = enable_compression
        
        # Context section priorities (higher = more important)
        self.section_priorities = {
            'user_profile': 9,
            'assessment_results': 10,
            'recent_attempts': 8,
            'confidence_triggers': 7,
            'conversation_history': 6,
            'session_history': 5,
            'coaching_notes': 4,
            'available_challenges': 3
        }
    
    def format_coaching_context(
        self, 
        context: Dict[str, Any], 
        archetype: Optional[int] = None
    ) -> Tuple[str, ContextCacheInfo]:
        """
        Format comprehensive coaching context optimized for prompt caching
        
        Args:
            context: Raw context data from memory system
            archetype: User's dating confidence archetype (1-6)
            
        Returns:
            Tuple of (formatted_context_string, cache_info)
        """
        try:
            # Start with structured context sections
            context_sections = []
            original_size = 0
            
            # 1. User Profile (Core Identity - Always Cached)
            if context.get('user_profile'):
                profile_section = self._format_user_profile(context['user_profile'])
                context_sections.append(profile_section)
                original_size += len(profile_section)
            
            # 2. Assessment Results (Archetype Context - Cache Priority)
            if context.get('assessment_results'):
                assessment_section = self._format_assessment_results(
                    context['assessment_results'], 
                    archetype
                )
                context_sections.append(assessment_section)
                original_size += len(assessment_section)
            
            # 3. Recent Approach Attempts (Behavioral Context)
            if context.get('recent_attempts'):
                attempts_section = self._format_recent_attempts(context['recent_attempts'])
                context_sections.append(attempts_section)
                original_size += len(attempts_section)
            
            # 4. Confidence Triggers (Fear/Growth Patterns)
            if context.get('confidence_triggers'):
                triggers_section = self._format_confidence_triggers(context['confidence_triggers'])
                context_sections.append(triggers_section)
                original_size += len(triggers_section)
            
            # 5. Session History (Coaching Continuity)
            if context.get('session_history'):
                session_section = self._format_session_history(context['session_history'])
                context_sections.append(session_section)
                original_size += len(session_section)
            
            # 6. Conversation History (Recent Context - Dynamic)
            if context.get('conversation_history'):
                conversation_section = self._format_conversation_history(
                    context['conversation_history']
                )
                context_sections.append(conversation_section)
                original_size += len(conversation_section)
            
            # 7. Coaching Notes (Insights and Breakthroughs)
            if context.get('coaching_notes'):
                notes_section = self._format_coaching_notes(context['coaching_notes'])
                context_sections.append(notes_section)
                original_size += len(notes_section)
            
            # Join sections with clear separators
            full_context = "\\n\\n".join(context_sections)
            
            # Apply compression if needed
            if self.enable_compression and len(full_context) > self.max_context_size:
                compressed_context = self._compress_context(context_sections)
                compression_ratio = len(compressed_context) / len(full_context)
                final_context = compressed_context
            else:
                compression_ratio = 1.0
                final_context = full_context
            
            # Generate cache info
            cache_key = self._generate_cache_key(context, archetype)
            cache_info = ContextCacheInfo(
                cache_key=cache_key,
                context_size=len(final_context),
                compression_ratio=compression_ratio,
                cacheable=self._is_cacheable(context),
                cache_ttl=self._get_cache_ttl(context)
            )
            
            logger.info(f"Formatted context: {len(final_context)} chars, compression: {compression_ratio:.2f}")
            
            return final_context, cache_info
            
        except Exception as e:
            logger.error(f"Error formatting coaching context: {e}")
            return self._get_fallback_context(), ContextCacheInfo(
                cache_key="fallback",
                context_size=0,
                compression_ratio=1.0,
                cacheable=False
            )
    
    def _format_user_profile(self, profile: Dict[str, Any]) -> str:
        """Format user profile for context injection"""
        if not profile:
            return ""
        
        lines = ["=== USER PROFILE ==="]
        
        # Core identity info
        if profile.get('first_name'):
            lines.append(f"Name: {profile['first_name']}")
        
        if profile.get('age'):
            lines.append(f"Age: {profile['age']}")
        
        if profile.get('location'):
            lines.append(f"Location: {profile['location']}")
        
        # Dating context
        if profile.get('bio'):
            lines.append(f"Bio: {profile['bio'][:200]}...")  # Truncate for context efficiency
        
        if profile.get('preferences'):
            prefs = profile['preferences']
            if isinstance(prefs, dict) and prefs:
                pref_summary = ", ".join([f"{k}: {v}" for k, v in prefs.items()][:3])
                lines.append(f"Dating Preferences: {pref_summary}")
        
        return "\\n".join(lines)
    
    def _format_assessment_results(
        self, 
        assessment: Dict[str, Any], 
        archetype: Optional[int]
    ) -> str:
        """Format confidence assessment results"""
        if not assessment:
            return ""
        
        lines = ["=== CONFIDENCE ASSESSMENT ==="]
        
        # Archetype information
        if archetype:
            archetype_names = {
                1: "Strategic Dater",
                2: "Confidence Sprinter", 
                3: "Steady Builder",
                4: "Social Connector",
                5: "Independent Learner",
                6: "Authentic Heart"
            }
            lines.append(f"Dating Archetype: {archetype_names.get(archetype, 'Unknown')} (Type {archetype})")
        
        # Confidence level
        if assessment.get('confidence_level'):
            lines.append(f"Confidence Level: {assessment['confidence_level']}/10")
        
        # Primary fears (key for coaching)
        if assessment.get('primary_fears'):
            fears = assessment['primary_fears']
            if isinstance(fears, list):
                lines.append(f"Primary Fears: {', '.join(fears[:3])}")  # Top 3 fears
            else:
                lines.append(f"Primary Fears: {fears}")
        
        # Dating goals
        if assessment.get('dating_goals'):
            goals = assessment['dating_goals']
            if isinstance(goals, list):
                lines.append(f"Dating Goals: {', '.join(goals[:2])}")  # Top 2 goals
            else:
                lines.append(f"Dating Goals: {goals}")
        
        # Assessment date for context freshness
        if assessment.get('created_at'):
            lines.append(f"Assessment Date: {assessment['created_at'][:10]}")
        
        return "\\n".join(lines)
    
    def _format_recent_attempts(self, attempts: List[Dict[str, Any]]) -> str:
        """Format recent approach attempts"""
        if not attempts:
            return ""
        
        lines = ["=== RECENT APPROACH ATTEMPTS ==="]
        
        # Show last 3 attempts for context
        for attempt in attempts[:3]:
            attempt_line = []
            
            if attempt.get('outcome'):
                attempt_line.append(f"Outcome: {attempt['outcome']}")
            
            if attempt.get('confidence_rating'):
                attempt_line.append(f"Confidence: {attempt['confidence_rating']}/10")
            
            if attempt.get('notes'):
                notes = attempt['notes'][:100]  # Truncate for context efficiency
                attempt_line.append(f"Notes: {notes}")
            
            if attempt.get('created_at'):
                date = attempt['created_at'][:10]
                attempt_line.append(f"Date: {date}")
            
            if attempt_line:
                lines.append("• " + " | ".join(attempt_line))
        
        return "\\n".join(lines)
    
    def _format_confidence_triggers(self, triggers: List[Dict[str, Any]]) -> str:
        """Format confidence triggers and fears"""
        if not triggers:
            return ""
        
        lines = ["=== CONFIDENCE TRIGGERS ==="]
        
        # Group triggers by type
        trigger_groups = {}
        for trigger in triggers:
            trigger_type = trigger.get('trigger_type', 'general')
            if trigger_type not in trigger_groups:
                trigger_groups[trigger_type] = []
            trigger_groups[trigger_type].append(trigger)
        
        # Format each group
        for trigger_type, group_triggers in trigger_groups.items():
            lines.append(f"{trigger_type.title()} Triggers:")
            for trigger in group_triggers[:2]:  # Max 2 per type
                description = trigger.get('description', '')
                intensity = trigger.get('intensity', 5)
                lines.append(f"  • {description} (Intensity: {intensity}/10)")
        
        return "\\n".join(lines)
    
    def _format_session_history(self, sessions: List[Dict[str, Any]]) -> str:
        """Format coaching session history"""
        if not sessions:
            return ""
        
        lines = ["=== COACHING SESSION HISTORY ==="]
        
        # Show last 3 sessions
        for session in sessions[:3]:
            session_line = []
            
            if session.get('summary'):
                summary = session['summary'][:150]  # Truncate for context
                session_line.append(f"Summary: {summary}")
            
            if session.get('message_count'):
                session_line.append(f"Messages: {session['message_count']}")
            
            if session.get('date'):
                date = session['date'][:10]
                session_line.append(f"Date: {date}")
            
            if session_line:
                lines.append("• " + " | ".join(session_line))
        
        return "\\n".join(lines)
    
    def _format_conversation_history(self, conversation: List[Dict[str, Any]]) -> str:
        """Format recent conversation history"""
        if not conversation:
            return ""
        
        lines = ["=== RECENT CONVERSATION ==="]
        
        # Show last 6 messages for immediate context
        for msg in conversation[-6:]:
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')
            
            # Truncate long messages
            if len(content) > 200:
                content = content[:200] + "..."
            
            lines.append(f"{role.title()}: {content}")
        
        return "\\n".join(lines)
    
    def _format_coaching_notes(self, notes: List[Dict[str, Any]]) -> str:
        """Format coaching insights and notes"""
        if not notes:
            return ""
        
        lines = ["=== COACHING INSIGHTS ==="]
        
        # Show recent insights
        for note in notes[:3]:
            if note.get('notes'):
                note_text = note['notes'][:100]  # Truncate
                note_type = note.get('note_type', 'general')
                lines.append(f"• {note_type.title()}: {note_text}")
        
        return "\\n".join(lines)
    
    def _compress_context(self, sections: List[str]) -> str:
        """Compress context sections based on priority"""
        # Calculate current size
        total_size = sum(len(section) for section in sections)
        
        if total_size <= self.max_context_size:
            return "\\n\\n".join(sections)
        
        # Apply compression strategies
        compressed_sections = []
        current_size = 0
        
        for section in sections:
            if current_size + len(section) <= self.max_context_size:
                compressed_sections.append(section)
                current_size += len(section)
            else:
                # Truncate section to fit
                remaining_space = self.max_context_size - current_size - 50  # Buffer
                if remaining_space > 100:  # Only include if meaningful space left
                    truncated_section = section[:remaining_space] + "\\n[TRUNCATED]"
                    compressed_sections.append(truncated_section)
                break
        
        return "\\n\\n".join(compressed_sections)
    
    def _generate_cache_key(self, context: Dict[str, Any], archetype: Optional[int]) -> str:
        """Generate cache key for context"""
        # Create key from stable context elements
        key_elements = []
        
        # User profile contributes to cache key
        if context.get('user_profile', {}).get('id'):
            key_elements.append(f"user_{context['user_profile']['id']}")
        
        # Archetype affects caching
        if archetype:
            key_elements.append(f"arch_{archetype}")
        
        # Assessment date affects cache validity
        if context.get('assessment_results', {}).get('created_at'):
            assessment_date = context['assessment_results']['created_at'][:10]
            key_elements.append(f"assess_{assessment_date}")
        
        # Session count affects cache
        session_count = len(context.get('session_history', []))
        key_elements.append(f"sessions_{session_count}")
        
        return "_".join(key_elements) if key_elements else "default"
    
    def _is_cacheable(self, context: Dict[str, Any]) -> bool:
        """Determine if context is suitable for caching"""
        # Cache if user has stable assessment results
        has_assessment = bool(context.get('assessment_results'))
        has_profile = bool(context.get('user_profile'))
        
        return has_assessment and has_profile
    
    def _get_cache_ttl(self, context: Dict[str, Any]) -> int:
        """Get appropriate cache TTL based on context stability"""
        # Stable user data can be cached longer
        has_recent_activity = len(context.get('conversation_history', [])) > 0
        
        if has_recent_activity:
            return 900   # 15 minutes for active users
        else:
            return 1800  # 30 minutes for stable context
    
    def _get_fallback_context(self) -> str:
        """Provide minimal fallback context when formatting fails"""
        return """=== COACHING SESSION ===
New coaching session - building context as we talk.
Ready to help with dating confidence and authentic connection."""

# Integration helper functions

def format_context_for_prompt_caching(
    context: Dict[str, Any], 
    archetype: Optional[int] = None,
    max_size: int = 8000
) -> Tuple[str, ContextCacheInfo]:
    """
    Convenience function for formatting context with prompt caching optimization
    
    Args:
        context: Raw context from memory system
        archetype: User's dating archetype
        max_size: Maximum context size
        
    Returns:
        Tuple of (formatted_context, cache_info)
    """
    formatter = CoachingContextFormatter(max_context_size=max_size)
    return formatter.format_coaching_context(context, archetype)

def create_context_formatter(enable_compression: bool = True) -> CoachingContextFormatter:
    """Create and return a configured context formatter"""
    return CoachingContextFormatter(enable_compression=enable_compression)

# Export key classes and functions
__all__ = [
    'CoachingContextFormatter',
    'ContextCacheInfo',
    'format_context_for_prompt_caching',
    'create_context_formatter'
]