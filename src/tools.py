#!/usr/bin/env python3
"""
WingmanMatch Function Calling Tools

Tools for dating confidence coaching with Connell Barrett persona.
Provides functions for challenge management, attempt tracking, and session history.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone, timedelta

from src.config import Config
from src.database import get_db_service
from src.retry_utils import with_supabase_retry

logger = logging.getLogger(__name__)

@with_supabase_retry()
async def get_approach_challenges(
    user_id: str,
    difficulty: Optional[str] = None,
    challenge_type: Optional[str] = None,
    limit: int = 10
) -> Dict[str, Any]:
    """
    Fetch approach challenges filtered by difficulty and type
    
    Args:
        user_id: User identifier
        difficulty: Challenge difficulty (beginner, intermediate, advanced)
        challenge_type: Type of challenge (conversation, social, direct_approach)
        limit: Maximum number of challenges to return
        
    Returns:
        Dictionary with challenges list and metadata
    """
    try:
        db = get_db_service()
        
        # Build query with filters
        query = db.table('approach_challenges').select('*')
        
        if difficulty:
            query = query.eq('difficulty', difficulty)
        
        if challenge_type:
            query = query.eq('challenge_type', challenge_type)
        
        # Order by difficulty and limit results
        result = query.order('difficulty').limit(limit).execute()
        
        challenges = result.data or []
        
        # Get user's completed challenges for context
        completed_result = db.table('approach_attempts')\
            .select('challenge_id')\
            .eq('user_id', user_id)\
            .eq('outcome', 'completed')\
            .execute()
        
        completed_ids = [attempt['challenge_id'] for attempt in completed_result.data]
        
        # Mark completed challenges
        for challenge in challenges:
            challenge['is_completed'] = challenge['id'] in completed_ids
        
        logger.info(f"Retrieved {len(challenges)} challenges for user {user_id}")
        
        return {
            "challenges": challenges,
            "total_count": len(challenges),
            "completed_count": len(completed_ids),
            "filters": {
                "difficulty": difficulty,
                "challenge_type": challenge_type
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting approach challenges: {e}")
        return {
            "challenges": [],
            "total_count": 0,
            "completed_count": 0,
            "error": str(e)
        }

@with_supabase_retry()
async def record_attempt_outcome(
    user_id: str,
    challenge_id: str,
    outcome: str,
    confidence_rating: int,
    notes: str = "",
    lessons_learned: List[str] = None
) -> Dict[str, Any]:
    """
    Record the outcome of an approach attempt
    
    Args:
        user_id: User identifier
        challenge_id: ID of the challenge attempted
        outcome: Result of attempt (completed, partial, failed, skipped)
        confidence_rating: User's confidence level after attempt (1-10)
        notes: User's notes about the attempt
        lessons_learned: List of insights from the attempt
        
    Returns:
        Dictionary with attempt record and success status
    """
    try:
        db = get_db_service()
        
        # Validate confidence rating
        if not 1 <= confidence_rating <= 10:
            return {"error": "Confidence rating must be between 1 and 10"}
        
        # Validate outcome
        valid_outcomes = ['completed', 'partial', 'failed', 'skipped']
        if outcome not in valid_outcomes:
            return {"error": f"Outcome must be one of: {valid_outcomes}"}
        
        # Create attempt record
        attempt_data = {
            'user_id': user_id,
            'challenge_id': challenge_id,
            'outcome': outcome,
            'confidence_rating': confidence_rating,
            'notes': notes,
            'lessons_learned': lessons_learned or [],
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        
        result = db.table('approach_attempts').insert(attempt_data).execute()
        
        if result.data:
            attempt_id = result.data[0]['id']
            
            # Update user statistics
            await _update_user_stats(user_id, outcome, confidence_rating)
            
            logger.info(f"Recorded attempt {attempt_id} for user {user_id}")
            
            return {
                "success": True,
                "attempt_id": attempt_id,
                "attempt": result.data[0],
                "message": f"Successfully recorded {outcome} attempt"
            }
        else:
            return {"error": "Failed to create attempt record"}
        
    except Exception as e:
        logger.error(f"Error recording attempt outcome: {e}")
        return {"error": str(e)}

@with_supabase_retry()
async def get_session_history(
    user_id: str,
    limit: int = 10,
    include_details: bool = False
) -> Dict[str, Any]:
    """
    Retrieve past wingman coaching sessions
    
    Args:
        user_id: User identifier
        limit: Maximum number of sessions to return
        include_details: Whether to include full session details
        
    Returns:
        Dictionary with session history and metadata
    """
    try:
        db = get_db_service()
        
        # Get coaching sessions
        query = db.table('coaching_sessions')\
            .select('*')\
            .eq('user_id', user_id)\
            .order('created_at', desc=True)\
            .limit(limit)
        
        result = query.execute()
        sessions = result.data or []
        
        # Get session statistics
        total_sessions_result = db.table('coaching_sessions')\
            .select('id', count='exact')\
            .eq('user_id', user_id)\
            .execute()
        
        total_sessions = total_sessions_result.count or 0
        
        # Calculate session metrics
        session_data = []
        for session in sessions:
            session_info = {
                'session_id': session['session_id'],
                'date': session['created_at'],
                'message_count': session.get('message_count', 0),
                'session_type': session.get('session_type', 'coaching')
            }
            
            if include_details:
                session_info['summary'] = session.get('summary', '')
                session_info['metadata'] = session.get('metadata', {})
            
            session_data.append(session_info)
        
        # Get recent activity metrics
        recent_cutoff = datetime.now(timezone.utc) - timedelta(days=30)
        recent_sessions_result = db.table('coaching_sessions')\
            .select('id', count='exact')\
            .eq('user_id', user_id)\
            .gte('created_at', recent_cutoff.isoformat())\
            .execute()
        
        recent_sessions = recent_sessions_result.count or 0
        
        logger.info(f"Retrieved {len(sessions)} sessions for user {user_id}")
        
        return {
            "sessions": session_data,
            "total_sessions": total_sessions,
            "recent_sessions": recent_sessions,
            "average_messages_per_session": sum(s.get('message_count', 0) for s in sessions) / len(sessions) if sessions else 0
        }
        
    except Exception as e:
        logger.error(f"Error getting session history: {e}")
        return {
            "sessions": [],
            "total_sessions": 0,
            "recent_sessions": 0,
            "error": str(e)
        }

@with_supabase_retry()
async def update_confidence_notes(
    user_id: str,
    session_id: str,
    notes: str,
    insights: List[str] = None,
    breakthroughs: List[str] = None
) -> Dict[str, Any]:
    """
    Save coaching insights and breakthroughs
    
    Args:
        user_id: User identifier
        session_id: Current session identifier
        notes: General coaching notes
        insights: List of coaching insights discovered
        breakthroughs: List of confidence breakthroughs
        
    Returns:
        Dictionary with save status and note ID
    """
    try:
        db = get_db_service()
        
        # Create notes record
        notes_data = {
            'user_id': user_id,
            'session_id': session_id,
            'notes': notes,
            'note_type': 'coaching_insight',
            'metadata': {
                'insights': insights or [],
                'breakthroughs': breakthroughs or [],
                'coach': 'connell_barrett',
                'auto_generated': False
            },
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        
        result = db.table('coaching_notes').insert(notes_data).execute()
        
        if result.data:
            note_id = result.data[0]['id']
            
            # Update confidence triggers if breakthroughs were identified
            if breakthroughs:
                await _process_breakthroughs(user_id, breakthroughs)
            
            logger.info(f"Saved coaching notes {note_id} for user {user_id}")
            
            return {
                "success": True,
                "note_id": note_id,
                "notes": result.data[0],
                "message": "Successfully saved coaching insights"
            }
        else:
            return {"error": "Failed to save coaching notes"}
        
    except Exception as e:
        logger.error(f"Error updating confidence notes: {e}")
        return {"error": str(e)}

@with_supabase_retry()
async def get_user_progress(
    user_id: str,
    timeframe: str = "30days"
) -> Dict[str, Any]:
    """
    Get user's dating confidence progress over time
    
    Args:
        user_id: User identifier
        timeframe: Time period for progress (7days, 30days, 90days)
        
    Returns:
        Dictionary with progress metrics and trends
    """
    try:
        db = get_db_service()
        
        # Calculate date range
        days_map = {"7days": 7, "30days": 30, "90days": 90}
        days = days_map.get(timeframe, 30)
        start_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        # Get attempts in timeframe
        attempts_result = db.table('approach_attempts')\
            .select('*')\
            .eq('user_id', user_id)\
            .gte('created_at', start_date.isoformat())\
            .order('created_at')\
            .execute()
        
        attempts = attempts_result.data or []
        
        # Calculate progress metrics
        total_attempts = len(attempts)
        successful_attempts = len([a for a in attempts if a['outcome'] == 'completed'])
        average_confidence = sum(a['confidence_rating'] for a in attempts) / total_attempts if attempts else 0
        
        # Get confidence trend
        confidence_trend = [a['confidence_rating'] for a in attempts[-10:]]  # Last 10 attempts
        
        # Get session count
        sessions_result = db.table('coaching_sessions')\
            .select('id', count='exact')\
            .eq('user_id', user_id)\
            .gte('created_at', start_date.isoformat())\
            .execute()
        
        session_count = sessions_result.count or 0
        
        logger.info(f"Retrieved progress data for user {user_id} ({timeframe})")
        
        return {
            "timeframe": timeframe,
            "total_attempts": total_attempts,
            "successful_attempts": successful_attempts,
            "success_rate": successful_attempts / total_attempts if total_attempts > 0 else 0,
            "average_confidence": round(average_confidence, 1),
            "confidence_trend": confidence_trend,
            "coaching_sessions": session_count,
            "most_recent_attempt": attempts[-1] if attempts else None
        }
        
    except Exception as e:
        logger.error(f"Error getting user progress: {e}")
        return {
            "timeframe": timeframe,
            "total_attempts": 0,
            "successful_attempts": 0,
            "success_rate": 0,
            "average_confidence": 0,
            "confidence_trend": [],
            "coaching_sessions": 0,
            "error": str(e)
        }

# Helper functions

async def _update_user_stats(user_id: str, outcome: str, confidence_rating: int):
    """Update user statistics after attempt"""
    try:
        db = get_db_service()
        
        # Get current stats
        stats_result = db.table('user_stats')\
            .select('*')\
            .eq('user_id', user_id)\
            .execute()
        
        if stats_result.data:
            # Update existing stats
            current_stats = stats_result.data[0]
            updated_stats = {
                'total_attempts': current_stats.get('total_attempts', 0) + 1,
                'successful_attempts': current_stats.get('successful_attempts', 0) + (1 if outcome == 'completed' else 0),
                'average_confidence': (current_stats.get('average_confidence', 0) * current_stats.get('total_attempts', 0) + confidence_rating) / (current_stats.get('total_attempts', 0) + 1),
                'last_attempt_date': datetime.now(timezone.utc).isoformat(),
                'updated_at': datetime.now(timezone.utc).isoformat()
            }
            
            db.table('user_stats').update(updated_stats).eq('user_id', user_id).execute()
        else:
            # Create new stats record
            new_stats = {
                'user_id': user_id,
                'total_attempts': 1,
                'successful_attempts': 1 if outcome == 'completed' else 0,
                'average_confidence': confidence_rating,
                'last_attempt_date': datetime.now(timezone.utc).isoformat(),
                'created_at': datetime.now(timezone.utc).isoformat(),
                'updated_at': datetime.now(timezone.utc).isoformat()
            }
            
            db.table('user_stats').insert(new_stats).execute()
        
        logger.info(f"Updated stats for user {user_id}")
        
    except Exception as e:
        logger.error(f"Error updating user stats: {e}")

async def _process_breakthroughs(user_id: str, breakthroughs: List[str]):
    """Process confidence breakthroughs and update triggers"""
    try:
        db = get_db_service()
        
        # Mark related triggers as resolved
        for breakthrough in breakthroughs:
            # Simple keyword matching to identify related triggers
            triggers_result = db.table('confidence_triggers')\
                .select('*')\
                .eq('user_id', user_id)\
                .eq('is_active', True)\
                .execute()
            
            for trigger in triggers_result.data:
                trigger_desc = trigger.get('description', '').lower()
                if any(word in trigger_desc for word in breakthrough.lower().split()):
                    # Mark trigger as resolved
                    db.table('confidence_triggers')\
                        .update({'is_active': False, 'resolved_date': datetime.now(timezone.utc).isoformat()})\
                        .eq('id', trigger['id'])\
                        .execute()
        
        logger.info(f"Processed breakthroughs for user {user_id}")
        
    except Exception as e:
        logger.error(f"Error processing breakthroughs: {e}")

# Tool registry for function calling
AVAILABLE_TOOLS = {
    "get_approach_challenges": get_approach_challenges,
    "record_attempt_outcome": record_attempt_outcome,
    "get_session_history": get_session_history,
    "update_confidence_notes": update_confidence_notes,
    "get_user_progress": get_user_progress
}

# Export for API integration
__all__ = [
    'get_approach_challenges',
    'record_attempt_outcome', 
    'get_session_history',
    'update_confidence_notes',
    'get_user_progress',
    'AVAILABLE_TOOLS'
]