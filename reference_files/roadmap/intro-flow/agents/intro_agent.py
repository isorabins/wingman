#!/usr/bin/env python3
"""
IntroAgent - Natural intro conversation for new users
Part of the DB-driven agent system for Fridays at Four
"""

import logging
from typing import Optional, Dict, Any
from supabase import Client

logger = logging.getLogger(__name__)

class IntroAgent:
    """Handles natural intro conversation using memory and AI"""
    
    def __init__(self, supabase: Client, user_id: str):
        self.supabase = supabase
        self.user_id = user_id
    
    async def get_intro_state(self) -> Dict[str, Any]:
        """Get current intro state from database"""
        try:
            result = self.supabase.table('creativity_test_progress')\
                .select('has_seen_intro')\
                .eq('user_id', self.user_id)\
                .execute()
            
            if not result.data:
                return {
                    'has_seen_intro': False,
                    'is_new_user': True
                }
            
            return {
                'has_seen_intro': result.data[0].get('has_seen_intro', False),
                'is_new_user': False
            }
        except Exception as e:
            logger.error(f"Error getting intro state: {e}")
            return {
                'has_seen_intro': False,
                'is_new_user': True
            }
    
    async def mark_intro_complete(self):
        """Mark intro as complete in database"""
        try:
            # Check if record exists
            result = self.supabase.table('creativity_test_progress')\
                .select('id')\
                .eq('user_id', self.user_id)\
                .execute()
            
            if result.data:
                # Update existing record
                self.supabase.table('creativity_test_progress')\
                    .update({'has_seen_intro': True})\
                    .eq('user_id', self.user_id)\
                    .execute()
            else:
                # Create new record
                self.supabase.table('creativity_test_progress')\
                    .insert({
                        'user_id': self.user_id,
                        'has_seen_intro': True,
                        'flow_step': 1,
                        'current_responses': {},
                        'completion_percentage': 0.0,
                        'is_completed': False
                    })\
                    .execute()
                    
            logger.info(f"Marked intro complete for user {self.user_id}")
        except Exception as e:
            logger.error(f"Error marking intro complete: {e}")
    
    def _intro_seems_complete(self, context: dict, ai_response: str, user_message: str) -> bool:
        """Check if intro conversation has covered key topics and user seems ready to proceed"""
        try:
            # Get all conversation content
            all_content = ""
            for msg in context.get('messages', []):
                all_content += msg.get('content', '') + " "
            all_content += ai_response + " " + user_message
            
            content_lower = all_content.lower()
            
            # Check if key intro topics have been covered
            topics_covered = {
                'name_discussed': any(phrase in content_lower for phrase in ['name', "i'm ", 'call you', 'call me']),
                'fridays_explained': any(phrase in content_lower for phrase in ['fridays at four', 'creative project', 'support', 'partner']),
                'how_it_works': any(phrase in content_lower for phrase in ['remember', 'advice', 'help', 'work with you']),
                'ready_signals': any(phrase in content_lower for phrase in ['ready', "let's start", 'sounds good', 'yes', 'sure', 'okay'])
            }
            
            # Need at least 3 topics covered and ready signals
            covered_count = sum(topics_covered.values())
            
            # Also check message count - don't complete too early
            message_count = len(context.get('messages', []))
            
            return covered_count >= 3 and topics_covered['ready_signals'] and message_count >= 4
            
        except Exception as e:
            logger.error(f"Error checking intro completion: {e}")
            return False
    
    async def process_message(self, thread_id: str, message: str) -> str:
        """Process intro message using natural conversation with memory and AI"""
        try:
            from ..simple_memory import SimpleMemory
            from ..llm_router import get_router
            
            # Get conversation memory
            memory = SimpleMemory(self.supabase, self.user_id)
            context = await memory.get_context(thread_id)
            
            # Build conversation history
            messages = []
            
            # Add intro system prompt
            intro_prompt = """You are Hai, a creative partner at Fridays at Four. You're having an introductory conversation with a new user.

Your goals for this intro conversation:
1. Introduce yourself warmly as Hai, their creative partner
2. Explain what Fridays at Four does (helps people track creative projects and get support to finish them)
3. Learn their name and what creative project they're interested in
4. Explain how you work (remember everything, provide advice, keep them moving forward)
5. Mention the creativity test and project planning you'll do together
6. Keep it conversational and natural - don't rush through topics

Once you've covered these key points naturally and they seem ready, you can transition them to the creativity test by saying something like "Ready to start that creativity test?" and then begin with the first creativity question.

Be warm, professional, and genuinely interested in their creative work. This is their first impression of the app."""

            messages.append({"role": "system", "content": intro_prompt})
            
            # Add conversation history
            for msg in context.get('messages', []):
                role = msg.get('role', 'user')
                content = msg.get('content', '')
                if content.strip():
                    messages.append({"role": role, "content": content})
            
            # Add current message
            messages.append({"role": "user", "content": message})
            
            # Get AI response
            router = await get_router()
            response = await router.send_message(messages=messages)
            
            # Check if intro seems complete and user is ready for creativity test
            if self._intro_seems_complete(context, response, message):
                # Mark intro as complete
                await self.mark_intro_complete()
                
                # If response mentions starting creativity test, begin it
                if any(phrase in response.lower() for phrase in ["creativity test", "first question", "question 1"]):
                    return response + "\n\nQuestion 1 of 12: When starting a new creative project, what excites you most?\n\nA. The unknown possibilities and what I might discover\nB. Creating something beautiful that moves people\nC. Solving a problem in a completely new way\nD. Bringing together different perspectives or ideas\nE. The process of making something real with my hands\nF. Sharing a meaningful story or message\n\nJust respond with A, B, C, D, E, or F."
            
            return response
            
        except Exception as e:
            logger.error(f"Error in intro flow: {e}")
            return "Hi! I'm Hai, your creative partner here at Fridays at Four. What's your name? I'd love to know what to call you."
    
    async def is_complete(self) -> bool:
        """Check if intro flow is complete"""
        try:
            result = self.supabase.table('creativity_test_progress')\
                .select('has_seen_intro')\
                .eq('user_id', self.user_id)\
                .execute()
            
            if not result.data:
                return False
            
            return result.data[0].get('has_seen_intro', False)
        except Exception as e:
            logger.error(f"Error checking intro completion: {e}")
            return False 