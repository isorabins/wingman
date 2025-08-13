#!/usr/bin/env python3
"""
WingmanMatch Memory System

Manages conversation history, context, and dating confidence coaching data.
Provides memory hooks for assessment results, attempts, triggers, and session history.
Built for Connell Barrett coaching continuity across sessions.
"""

import asyncio
import json
import logging
import hashlib
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta, timezone
from supabase import Client

from src.config import Config
from src.database import get_db_service

logger = logging.getLogger(__name__)

class WingmanMemory:
    """Memory system for WingmanMatch dating confidence coaching"""
    
    def __init__(self, supabase_client: Client, user_id: str, buffer_size: int = 100):
        self.supabase = supabase_client
        self.user_id = user_id
        self.buffer_size = buffer_size

    def _generate_message_hash(self, thread_id: str, content: str, role: str) -> str:
        """Generate hash for message deduplication"""
        message_data = f"{self.user_id}:{thread_id}:{role}:{content.strip()}"
        return hashlib.md5(message_data.encode()).hexdigest()

    async def _is_message_duplicate(self, message_hash: str, thread_id: str, content: str) -> bool:
        """Check if message already exists in recent memory"""
        try:
            # Check last 10 minutes for duplicates
            recent_cutoff = datetime.now(timezone.utc) - timedelta(minutes=10)
            
            result = self.supabase.table('conversations')\
                .select('id, message_text, context')\
                .eq('user_id', self.user_id)\
                .gte('created_at', recent_cutoff.isoformat())\
                .execute()
            
            for record in result.data:
                existing_content = record.get('message_text', '')
                existing_context = record.get('context', {})
                existing_thread = existing_context.get('thread_id')
                
                # Check content match and thread match
                if (existing_content == content and existing_thread == thread_id):
                    logger.info(f"Duplicate message detected for thread {thread_id}")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking message duplication: {e}")
            return False

    async def ensure_user_profile(self, user_id: str):
        """Ensure user profile exists to prevent foreign key constraint violations"""
        try:
            # Check if user profile exists
            result = self.supabase.table('user_profiles')\
                .select('id')\
                .eq('id', user_id)\
                .execute()
            
            if not result.data:
                # Create minimal user profile
                profile_data = {
                    "id": user_id,
                    "email": f"user_{user_id[:8]}@wingmanmatch.temp",
                    "first_name": "User",
                    "last_name": "Temp",
                    "bio": "New WingmanMatch user",
                    "experience_level": "beginner",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
                
                self.supabase.table('user_profiles').insert(profile_data).execute()
                logger.info(f"Auto-created user profile for {user_id}")
            
        except Exception as e:
            logger.error(f"Error ensuring user profile for {user_id}: {str(e)}")

    async def add_message(self, thread_id: str, message: str, role: str):
        """Add message to conversation history with deduplication"""
        try:
            # Ensure user profile exists
            await self.ensure_user_profile(self.user_id)
            
            # Sanitize message content
            sanitized_message = str(message).strip()
            if not sanitized_message:
                logger.warning("Empty message content, skipping storage")
                return
            
            # Check for duplicates
            message_hash = self._generate_message_hash(thread_id, sanitized_message, role)
            if await self._is_message_duplicate(message_hash, thread_id, sanitized_message):
                logger.info(f"Skipping duplicate message for thread {thread_id}")
                return
            
            # Store in conversations table
            conversation_data = {
                'user_id': self.user_id,
                'message_text': sanitized_message,
                'role': role,
                'context': {
                    'thread_id': thread_id,
                    'message_hash': message_hash,
                    'coaching_session': True
                },
                'metadata': {},
                'created_at': datetime.now(timezone.utc).isoformat()
            }
            
            result = self.supabase.table('conversations').insert(conversation_data).execute()
            logger.info(f"Stored message for thread {thread_id}, role: {role}")
            
            # Check if we need session summarization
            await self._check_session_buffer(thread_id)
            
        except Exception as e:
            logger.error(f"Error adding message: {e}", exc_info=True)
            raise

    async def _check_session_buffer(self, thread_id: str):
        """Check if session needs summarization based on message count"""
        try:
            # Count messages in current thread
            result = self.supabase.table('conversations')\
                .select('id', count='exact')\
                .eq('user_id', self.user_id)\
                .eq('context->>thread_id', thread_id)\
                .execute()
            
            message_count = result.count or 0
            
            if message_count >= self.buffer_size:
                # Trigger session summarization in background
                asyncio.create_task(self._summarize_session(thread_id))
                logger.info(f"Triggered session summarization for thread {thread_id}")
                
        except Exception as e:
            logger.error(f"Error checking session buffer: {e}")

    async def _summarize_session(self, thread_id: str):
        """Create session summary for coaching continuity"""
        try:
            # Get messages from current thread
            messages = self.supabase.table('conversations')\
                .select('*')\
                .eq('user_id', self.user_id)\
                .eq('context->>thread_id', thread_id)\
                .order('created_at')\
                .execute()
            
            if not messages.data:
                logger.warning(f"No messages found for session {thread_id}")
                return
            
            # Create session summary
            session_content = []
            for msg in messages.data:
                role = msg.get('role', 'unknown')
                content = msg.get('message_text', '')
                session_content.append(f"{role}: {content}")
            
            # Store session summary
            summary_data = {
                'user_id': self.user_id,
                'session_id': thread_id,
                'summary': "\\n".join(session_content[-20:]),  # Last 20 messages
                'message_count': len(messages.data),
                'session_type': 'coaching',
                'metadata': {
                    'thread_id': thread_id,
                    'auto_generated': True
                },
                'created_at': datetime.now(timezone.utc).isoformat()
            }
            
            self.supabase.table('coaching_sessions').insert(summary_data).execute()
            logger.info(f"Created session summary for thread {thread_id}")
            
        except Exception as e:
            logger.error(f"Error summarizing session: {e}")

    async def get_conversation_history(self, thread_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get conversation history for current thread"""
        try:
            result = self.supabase.table('conversations')\
                .select('*')\
                .eq('user_id', self.user_id)\
                .eq('context->>thread_id', thread_id)\
                .order('created_at')\
                .limit(limit)\
                .execute()
            
            messages = []
            for msg in result.data:
                messages.append({
                    'role': msg.get('role'),
                    'content': msg.get('message_text'),
                    'timestamp': msg.get('created_at')
                })
            
            return messages
            
        except Exception as e:
            logger.error(f"Error getting conversation history: {e}")
            return []

    async def get_coaching_context(self, thread_id: str) -> Dict[str, Any]:
        """Get comprehensive coaching context including memory hooks"""
        try:
            context = {
                'conversation_history': [],
                'session_history': [],
                'assessment_results': None,
                'recent_attempts': [],
                'confidence_triggers': [],
                'coaching_notes': []
            }
            
            # Get conversation history
            context['conversation_history'] = await self.get_conversation_history(thread_id)
            
            # Get session history (memory hook)
            session_result = self.supabase.table('coaching_sessions')\
                .select('*')\
                .eq('user_id', self.user_id)\
                .order('created_at', desc=True)\
                .limit(5)\
                .execute()
            
            context['session_history'] = [
                {
                    'session_id': s.get('session_id'),
                    'summary': s.get('summary'),
                    'date': s.get('created_at'),
                    'message_count': s.get('message_count', 0)
                }
                for s in session_result.data
            ]
            
            # Get assessment results (memory hook)
            assessment_result = self.supabase.table('confidence_assessments')\
                .select('*')\
                .eq('user_id', self.user_id)\
                .order('created_at', desc=True)\
                .limit(1)\
                .execute()
            
            if assessment_result.data:
                context['assessment_results'] = assessment_result.data[0]
            
            # Get recent attempts (memory hook)
            attempts_result = self.supabase.table('approach_attempts')\
                .select('*')\
                .eq('user_id', self.user_id)\
                .order('created_at', desc=True)\
                .limit(10)\
                .execute()
            
            context['recent_attempts'] = attempts_result.data or []
            
            # Get confidence triggers (memory hook)
            triggers_result = self.supabase.table('confidence_triggers')\
                .select('*')\
                .eq('user_id', self.user_id)\
                .eq('is_active', True)\
                .execute()
            
            context['confidence_triggers'] = triggers_result.data or []
            
            # Get coaching notes (memory hook)
            notes_result = self.supabase.table('coaching_notes')\
                .select('*')\
                .eq('user_id', self.user_id)\
                .order('created_at', desc=True)\
                .limit(5)\
                .execute()
            
            context['coaching_notes'] = notes_result.data or []
            
            return context
            
        except Exception as e:
            logger.error(f"Error getting coaching context: {e}")
            return {
                'conversation_history': [],
                'session_history': [],
                'assessment_results': None,
                'recent_attempts': [],
                'confidence_triggers': [],
                'coaching_notes': []
            }

    # Memory hook methods for dating confidence coaching
    
    async def store_assessment_results(self, assessment_data: Dict[str, Any]) -> bool:
        """Store confidence assessment results (memory hook)"""
        try:
            await self.ensure_user_profile(self.user_id)
            
            assessment_record = {
                'user_id': self.user_id,
                'confidence_level': assessment_data.get('confidence_level'),
                'archetype': assessment_data.get('archetype'),
                'primary_fears': assessment_data.get('primary_fears', []),
                'dating_goals': assessment_data.get('dating_goals', []),
                'responses': assessment_data.get('responses', {}),
                'created_at': datetime.now(timezone.utc).isoformat()
            }
            
            self.supabase.table('confidence_assessments').insert(assessment_record).execute()
            logger.info(f"Stored assessment results for user {self.user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing assessment results: {e}")
            return False

    async def record_approach_attempt(self, attempt_data: Dict[str, Any]) -> bool:
        """Record approach attempt outcome (memory hook)"""
        try:
            await self.ensure_user_profile(self.user_id)
            
            attempt_record = {
                'user_id': self.user_id,
                'challenge_id': attempt_data.get('challenge_id'),
                'outcome': attempt_data.get('outcome'),
                'confidence_rating': attempt_data.get('confidence_rating'),
                'notes': attempt_data.get('notes', ''),
                'lessons_learned': attempt_data.get('lessons_learned', []),
                'created_at': datetime.now(timezone.utc).isoformat()
            }
            
            self.supabase.table('approach_attempts').insert(attempt_record).execute()
            logger.info(f"Recorded approach attempt for user {self.user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error recording approach attempt: {e}")
            return False

    async def update_confidence_triggers(self, triggers: List[Dict[str, Any]]) -> bool:
        """Update confidence triggers and fears (memory hook)"""
        try:
            await self.ensure_user_profile(self.user_id)
            
            # Deactivate existing triggers
            self.supabase.table('confidence_triggers')\
                .update({'is_active': False})\
                .eq('user_id', self.user_id)\
                .execute()
            
            # Insert new triggers
            for trigger in triggers:
                trigger_record = {
                    'user_id': self.user_id,
                    'trigger_type': trigger.get('type'),
                    'description': trigger.get('description'),
                    'intensity': trigger.get('intensity', 5),
                    'is_active': True,
                    'created_at': datetime.now(timezone.utc).isoformat()
                }
                
                self.supabase.table('confidence_triggers').insert(trigger_record).execute()
            
            logger.info(f"Updated confidence triggers for user {self.user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating confidence triggers: {e}")
            return False

    async def save_coaching_notes(self, notes: str, session_id: str) -> bool:
        """Save coaching insights and breakthroughs (memory hook)"""
        try:
            await self.ensure_user_profile(self.user_id)
            
            notes_record = {
                'user_id': self.user_id,
                'session_id': session_id,
                'notes': notes,
                'note_type': 'coaching_insight',
                'metadata': {
                    'auto_generated': False,
                    'coach': 'connell_barrett'
                },
                'created_at': datetime.now(timezone.utc).isoformat()
            }
            
            self.supabase.table('coaching_notes').insert(notes_record).execute()
            logger.info(f"Saved coaching notes for user {self.user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving coaching notes: {e}")
            return False

    async def get_user_archetype(self, user_id: str) -> Optional[int]:
        """Get user's dating confidence archetype"""
        try:
            result = self.supabase.table('confidence_assessments')\
                .select('archetype')\
                .eq('user_id', user_id)\
                .order('created_at', desc=True)\
                .limit(1)\
                .execute()
            
            if result.data and result.data[0].get('archetype'):
                archetype = result.data[0]['archetype']
                logger.info(f"Found archetype {archetype} for user {user_id}")
                return archetype
            else:
                logger.info(f"No archetype found for user {user_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting user archetype: {e}")
            return None

    async def health_check(self) -> Dict[str, Any]:
        """Check memory system health"""
        health = {
            "memory_system": False,
            "database_connection": False,
            "user_profile_access": False,
            "errors": []
        }
        
        try:
            # Test database connection
            result = self.supabase.table('user_profiles').select('id').limit(1).execute()
            health["database_connection"] = True
            
            # Test user profile access
            await self.ensure_user_profile("health_check_user")
            health["user_profile_access"] = True
            
            health["memory_system"] = True
            
        except Exception as e:
            health["errors"].append(f"Memory system error: {str(e)}")
        
        return health

# Export for API integration
__all__ = [
    'WingmanMemory'
]