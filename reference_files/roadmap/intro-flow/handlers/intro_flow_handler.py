#!/usr/bin/env python3
"""
Intro Flow Handler - Natural conversation about platform value
"""

import logging
from typing import Dict, Any, List
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class IntroFlowHandler:
    """Handles conversational intro flow"""
    
    REQUIRED_CONCEPTS = [
        'persistent_memory',
        'adaptive_partnership', 
        'creative_support'
    ]
    
    CONCEPT_EXPLANATIONS = {
        'persistent_memory': "I remember everything we discuss, even across different sessions. You never have to start from scratch explaining your project or where you left off.",
        'adaptive_partnership': "After you take our creativity test, I'll understand your unique working style and creative archetype. I'll adapt how I communicate and support you without you having to explain every detail.",
        'creative_support': "I'm here to help bring out YOUR creativity and keep you moving forward on your projects. I won't do the work for you, but I'll provide guidance, feedback, and accountability."
    }
    
    def __init__(self, supabase, user_id: str):
        self.supabase = supabase
        self.user_id = user_id
    
    async def handle_message(self, message: str, flow_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process intro conversation message"""
        try:
            intro_data = flow_data.get('data', {})
            concepts_covered = intro_data.get('concepts_covered', [])
            
            # Check if user is ready to move on
            if self._check_ready_to_proceed(message, concepts_covered):
                # Mark intro complete
                await self._mark_intro_complete()
                
                return {
                    'response': "Perfect! Let's discover your creative archetype with a quick personality test. This helps me understand how to best support your unique creative process.\n\nI'll ask you 11 questions - just choose the option that feels most natural to you. Ready to begin?",
                    'flow_complete': True,
                    'next_flow': 'creativity'
                }
            
            # Generate contextual response
            response = await self._generate_intro_response(message, concepts_covered)
            
            # Update concepts covered based on response
            new_concepts = self._extract_covered_concepts(response)
            for concept in new_concepts:
                if concept not in concepts_covered:
                    concepts_covered.append(concept)
            
            # Save progress
            await self._save_intro_progress(concepts_covered)
            
            return {
                'response': response,
                'flow_complete': False,
                'concepts_covered': concepts_covered
            }
            
        except Exception as e:
            logger.error(f"Error in intro flow: {e}")
            return {
                'response': "Let me tell you what makes Fridays at Four special for creative professionals like yourself.",
                'flow_complete': False
            }
    
    def _check_ready_to_proceed(self, message: str, concepts_covered: List[str]) -> bool:
        """Check if user is ready to move to creativity test"""
        # Must have covered all concepts
        if len(concepts_covered) < len(self.REQUIRED_CONCEPTS):
            return False
        
        # Check for ready signals
        ready_phrases = [
            'ready', 'yes', 'sure', 'sounds good', "let's go",
            'okay', 'great', 'awesome', 'perfect', 'start',
            'begin', 'move on', 'next', 'continue'
        ]
        
        message_lower = message.lower()
        return any(phrase in message_lower for phrase in ready_phrases)
    
    async def _generate_intro_response(self, message: str, concepts_covered: List[str]) -> str:
        """Generate natural intro response using LLM"""
        from src.llm_router import get_router
        
        # Determine what still needs to be covered
        missing_concepts = [c for c in self.REQUIRED_CONCEPTS if c not in concepts_covered]
        
        # Build context
        covered_explanations = [self.CONCEPT_EXPLANATIONS[c] for c in concepts_covered]
        missing_explanations = [self.CONCEPT_EXPLANATIONS[c] for c in missing_concepts]
        
        system_prompt = f"""You are Hai, a warm and supportive AI partner introducing Fridays at Four.

Already explained concepts:
{chr(10).join(f'- {exp}' for exp in covered_explanations) if covered_explanations else 'None yet'}

Concepts still to explain naturally:
{chr(10).join(f'- {exp}' for exp in missing_explanations) if missing_explanations else 'All concepts covered'}

Guidelines:
- Be conversational and warm, not scripted
- If they ask questions, answer them thoroughly
- Naturally weave in missing concepts if any remain
- If all concepts are covered, ask if they're ready for the creativity test
- Keep responses concise but meaningful
"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message}
        ]
        
        router = await get_router()
        response = await router.send_message(
            messages=messages,
            model="claude-3-5-sonnet-20241022",
            max_tokens=500,
            temperature=0.7
        )
        
        return response
    
    def _extract_covered_concepts(self, response: str) -> List[str]:
        """Extract which concepts were covered in the response"""
        covered = []
        response_lower = response.lower()
        
        # Check for key phrases indicating each concept
        if any(phrase in response_lower for phrase in ['remember everything', 'persistent memory', 'never start from scratch', 'pick up where']):
            covered.append('persistent_memory')
        
        if any(phrase in response_lower for phrase in ['creativity test', 'creative archetype', 'adapt how i', 'working style', 'unique approach']):
            covered.append('adaptive_partnership')
        
        if any(phrase in response_lower for phrase in ['your creativity', 'bring out your', 'guidance', 'accountability', 'support your']):
            covered.append('creative_support')
        
        return covered
    
    async def _save_intro_progress(self, concepts_covered: List[str]):
        """Save intro progress to database"""
        try:
            intro_data = {
                'concepts_covered': concepts_covered,
                'last_updated': datetime.now(timezone.utc).isoformat()
            }
            
            # Update or create record
            existing = self.supabase.table('creativity_test_progress')\
                .select('id')\
                .eq('user_id', self.user_id)\
                .execute()
            
            if existing.data:
                self.supabase.table('creativity_test_progress')\
                    .update({'intro_data': intro_data})\
                    .eq('user_id', self.user_id)\
                    .execute()
            else:
                self.supabase.table('creativity_test_progress')\
                    .insert({
                        'user_id': self.user_id,
                        'intro_data': intro_data,
                        'intro_stage': 1,
                        'has_seen_intro': False,
                        'flow_step': 1,
                        'current_responses': {},
                        'completion_percentage': 0.0
                    })\
                    .execute()
                    
        except Exception as e:
            logger.error(f"Error saving intro progress: {e}")
    
    async def _mark_intro_complete(self):
        """Mark intro as complete in database"""
        try:
            self.supabase.table('creativity_test_progress')\
                .update({
                    'has_seen_intro': True,
                    'intro_stage': 99  # Completed marker
                })\
                .eq('user_id', self.user_id)\
                .execute()
                
        except Exception as e:
            logger.error(f"Error marking intro complete: {e}")
    
    def get_welcome_message(self) -> str:
        """Get initial welcome message for new users"""
        return """Hi! I'm Hai, your creative partner here at Fridays at Four. 

I'm excited to tell you about what makes our platform special for creative professionals like yourself. We've built something different here - a space where your creative projects actually get completed, not just planned.

What kind of creative work are you passionate about?""" 