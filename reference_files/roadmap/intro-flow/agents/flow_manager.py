#!/usr/bin/env python3
"""
FlowManager - Simple flow routing for intro system
Replaces complex agent orchestration with DB checks
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, Tuple
from supabase import Client

logger = logging.getLogger(__name__)

class FlowManager:
    """Manages user flow progression through intro → creativity → project → main"""
    
    def __init__(self, supabase: Client, user_id: str):
        self.supabase = supabase
        self.user_id = user_id
    
    async def get_next_flow(self) -> Tuple[str, Dict[str, Any]]:
        """
        Determine which flow the user should be in
        Returns: (flow_type, flow_data)
        """
        try:
            # Check intro status
            intro_status = await self._check_intro_status()
            if not intro_status['completed'] and not intro_status['on_cooldown']:
                return 'intro', intro_status
            
            # Check creativity test status
            creativity_status = await self._check_creativity_status()
            if not creativity_status['completed'] and not creativity_status['on_cooldown']:
                return 'creativity', creativity_status
            
            # Check project overview status
            project_status = await self._check_project_status()
            if not project_status['completed'] and not project_status['on_cooldown']:
                return 'project', project_status
            
            # All complete or on cooldown
            return 'main_chat', {}
            
        except Exception as e:
            logger.error(f"Error determining flow: {e}")
            return 'main_chat', {}  # Safe fallback
    
    async def _check_intro_status(self) -> Dict[str, Any]:
        """Check if intro is complete or on cooldown"""
        try:
            result = self.supabase.table('creativity_test_progress')\
                .select('has_seen_intro, intro_stage, intro_data, skipped_until')\
                .eq('user_id', self.user_id)\
                .execute()
            
            if not result.data:
                return {
                    'completed': False,
                    'on_cooldown': False,
                    'stage': 1,
                    'data': {}
                }
            
            record = result.data[0]
            on_cooldown = self._is_on_cooldown(record.get('skipped_until'))
            
            return {
                'completed': record.get('has_seen_intro', False),
                'on_cooldown': on_cooldown,
                'stage': record.get('intro_stage', 1),
                'data': record.get('intro_data', {})
            }
            
        except Exception as e:
            logger.error(f"Error checking intro status: {e}")
            return {'completed': False, 'on_cooldown': False, 'stage': 1, 'data': {}}
    
    async def _check_creativity_status(self) -> Dict[str, Any]:
        """Check if creativity test is complete or on cooldown"""
        try:
            # First check if completed (in final results table)
            final_result = self.supabase.table('creator_creativity_profiles')\
                .select('id')\
                .eq('user_id', self.user_id)\
                .execute()
            
            if final_result.data:
                return {'completed': True, 'on_cooldown': False}
            
            # Check progress
            progress_result = self.supabase.table('creativity_test_progress')\
                .select('flow_step, current_responses, skipped_until')\
                .eq('user_id', self.user_id)\
                .execute()
            
            if not progress_result.data:
                return {
                    'completed': False,
                    'on_cooldown': False,
                    'current_question': 1,
                    'responses': {}
                }
            
            record = progress_result.data[0]
            on_cooldown = self._is_on_cooldown(record.get('skipped_until'))
            
            return {
                'completed': False,
                'on_cooldown': on_cooldown,
                'current_question': record.get('flow_step', 1),
                'responses': record.get('current_responses', {})
            }
            
        except Exception as e:
            logger.error(f"Error checking creativity status: {e}")
            return {'completed': False, 'on_cooldown': False}
    
    async def _check_project_status(self) -> Dict[str, Any]:
        """Check if project overview is complete or on cooldown"""
        try:
            # First check if completed (in final results table)
            final_result = self.supabase.table('project_overview')\
                .select('id')\
                .eq('user_id', self.user_id)\
                .execute()
            
            if final_result.data:
                return {'completed': True, 'on_cooldown': False}
            
            # Check progress
            progress_result = self.supabase.table('project_overview_progress')\
                .select('flow_step, current_data, topic_progress, skipped_until')\
                .eq('user_id', self.user_id)\
                .execute()
            
            if not progress_result.data:
                return {
                    'completed': False,
                    'on_cooldown': False,
                    'current_topic': 1,
                    'data': {},
                    'topic_progress': {}
                }
            
            record = progress_result.data[0]
            on_cooldown = self._is_on_cooldown(record.get('skipped_until'))
            
            return {
                'completed': False,
                'on_cooldown': on_cooldown,
                'current_topic': record.get('flow_step', 1),
                'data': record.get('current_data', {}),
                'topic_progress': record.get('topic_progress', {})
            }
            
        except Exception as e:
            logger.error(f"Error checking project status: {e}")
            return {'completed': False, 'on_cooldown': False}
    
    def _is_on_cooldown(self, skipped_until: Optional[str]) -> bool:
        """Check if flow is on cooldown"""
        if not skipped_until:
            return False
        
        try:
            skip_time = datetime.fromisoformat(skipped_until.replace('Z', '+00:00'))
            return datetime.now(timezone.utc) < skip_time
        except:
            return False
    
    async def set_skip_cooldown(self, flow_type: str) -> str:
        """Set 24-hour cooldown for a flow"""
        try:
            skip_until = (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()
            
            if flow_type in ['intro', 'creativity']:
                table = 'creativity_test_progress'
            else:  # project
                table = 'project_overview_progress'
            
            # Ensure record exists
            existing = self.supabase.table(table)\
                .select('id')\
                .eq('user_id', self.user_id)\
                .execute()
            
            if existing.data:
                self.supabase.table(table)\
                    .update({'skipped_until': skip_until})\
                    .eq('user_id', self.user_id)\
                    .execute()
            else:
                # Create minimal record with skip
                self.supabase.table(table)\
                    .insert({
                        'user_id': self.user_id,
                        'skipped_until': skip_until,
                        'flow_step': 1,
                        'current_responses' if table == 'creativity_test_progress' else 'current_data': {}
                    })\
                    .execute()
            
            return "No problem! I'll ask you again tomorrow. Let me know if there's anything else I can help with!"
            
        except Exception as e:
            logger.error(f"Error setting skip cooldown: {e}")
            return "I'll check back with you later. What else can I help with today?"
    
    def detect_skip_intent(self, message: str) -> bool:
        """Detect if user wants to skip current flow"""
        skip_phrases = [
            'skip', 'later', 'not now', 'maybe later', 
            'not right now', 'another time', 'pass',
            'not interested', 'remind me later'
        ]
        
        message_lower = message.lower()
        return any(phrase in message_lower for phrase in skip_phrases) 