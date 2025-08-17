#!/usr/bin/env python3
"""
Confidence Test Agent for WingmanMatch

Implements the dating confidence assessment flow using Claude:
- 12-question dating confidence archetype assessment
- Progress tracking and mid-flow saves
- Results storage in confidence_test_results table
- Integration with 6 dating confidence archetypes
"""

import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone

from .base_agent import BaseAgent
try:
    from src.assessment.confidence_scoring import (
        calculate_confidence_assessment,
        get_archetype_info,
        CONFIDENCE_ARCHETYPES
    )
except ImportError:
    # For testing purposes
    from assessment.confidence_scoring import (
        calculate_confidence_assessment,
        get_archetype_info,
        CONFIDENCE_ARCHETYPES
    )

logger = logging.getLogger(__name__)

class ConfidenceTestAgent(BaseAgent):
    """Agent for conducting dating confidence assessments"""
    
    # Dating confidence questions designed to identify archetype
    QUESTIONS = [
        {
            "question": "When you see someone attractive, what's your first instinct?",
            "options": {
                "A": "Research their interests before approaching",
                "B": "Go talk to them immediately", 
                "C": "Wait for the right moment",
                "D": "Think about what to say first",
                "E": "Be myself and see what happens",
                "F": "Consider how to make them comfortable"
            },
            "scoring": {
                "A": "Analyzer", "B": "Sprinter", "C": "Ghost",
                "D": "Scholar", "E": "Naturalist", "F": "Protector"
            }
        },
        {
            "question": "When facing rejection in dating, your typical response is:",
            "options": {
                "A": "Analyze what went wrong to improve next time",
                "B": "Move on quickly to the next opportunity",
                "C": "Take time to process it quietly",
                "D": "Learn from it to become better",
                "E": "Accept it as part of being authentic",
                "F": "Consider their feelings and respect their choice"
            },
            "scoring": {
                "A": "Analyzer", "B": "Sprinter", "C": "Ghost",
                "D": "Scholar", "E": "Naturalist", "F": "Protector"
            }
        },
        {
            "question": "Before a first date, you usually:",
            "options": {
                "A": "Research the venue and plan conversation topics",
                "B": "Get excited and don't overthink it",
                "C": "Feel nervous but push through",
                "D": "Study dating advice and tips",
                "E": "Trust your instincts and be yourself",
                "F": "Think about how to make them feel comfortable"
            },
            "scoring": {
                "A": "Analyzer", "B": "Sprinter", "C": "Ghost",
                "D": "Scholar", "E": "Naturalist", "F": "Protector"
            }
        },
        {
            "question": "Your conversation style on dates tends to be:",
            "options": {
                "A": "Strategic questions to learn about them",
                "B": "High energy and spontaneous",
                "C": "Deep and meaningful when I feel comfortable",
                "D": "Well-informed about interesting topics",
                "E": "Natural and flowing with the moment",
                "F": "Focused on making them feel heard"
            },
            "scoring": {
                "A": "Analyzer", "B": "Sprinter", "C": "Ghost",
                "D": "Scholar", "E": "Naturalist", "F": "Protector"
            }
        },
        {
            "question": "When using dating apps, you typically:",
            "options": {
                "A": "Carefully craft messages based on their profile",
                "B": "Send messages quickly without overthinking",
                "C": "Take time to find quality matches",
                "D": "Research the best strategies and techniques",
                "E": "Keep messages genuine and authentic",
                "F": "Focus on respectful, thoughtful communication"
            },
            "scoring": {
                "A": "Analyzer", "B": "Sprinter", "C": "Ghost",
                "D": "Scholar", "E": "Naturalist", "F": "Protector"
            }
        },
        {
            "question": "When expressing romantic interest, you prefer to:",
            "options": {
                "A": "Wait for clear signals before making a move",
                "B": "Be direct and upfront about your feelings",
                "C": "Drop subtle hints and see how they respond",
                "D": "Use proven techniques for showing interest",
                "E": "Let it happen naturally through connection",
                "F": "Make sure they feel safe and respected"
            },
            "scoring": {
                "A": "Analyzer", "B": "Sprinter", "C": "Ghost",
                "D": "Scholar", "E": "Naturalist", "F": "Protector"
            }
        },
        {
            "question": "In social dating situations (parties, events), you:",
            "options": {
                "A": "Observe first to understand the social dynamics",
                "B": "Jump in and start meeting people immediately",
                "C": "Prefer smaller group conversations",
                "D": "Use social skills you've learned and practiced",
                "E": "Go with the flow and be yourself",
                "F": "Look out for people who seem left out"
            },
            "scoring": {
                "A": "Analyzer", "B": "Sprinter", "C": "Ghost",
                "D": "Scholar", "E": "Naturalist", "F": "Protector"
            }
        },
        {
            "question": "When planning dates, you tend to:",
            "options": {
                "A": "Research the perfect activity based on their interests",
                "B": "Suggest something fun on the spot",
                "C": "Choose quiet places where you can talk deeply",
                "D": "Pick activities you've learned work well",
                "E": "Suggest something that feels right in the moment",
                "F": "Plan something you know they'll enjoy"
            },
            "scoring": {
                "A": "Analyzer", "B": "Sprinter", "C": "Ghost",
                "D": "Scholar", "E": "Naturalist", "F": "Protector"
            }
        },
        {
            "question": "When dating gets serious, your approach is:",
            "options": {
                "A": "Carefully evaluate compatibility and future potential",
                "B": "Dive in headfirst when you feel it",
                "C": "Take time to really get to know them deeply",
                "D": "Apply relationship principles you've studied",
                "E": "Follow your heart and intuition",
                "F": "Focus on building trust and emotional safety"
            },
            "scoring": {
                "A": "Analyzer", "B": "Sprinter", "C": "Ghost",
                "D": "Scholar", "E": "Naturalist", "F": "Protector"
            }
        },
        {
            "question": "When conflicts arise in dating/relationships, you:",
            "options": {
                "A": "Analyze the problem logically to find solutions",
                "B": "Address it head-on and resolve it quickly",
                "C": "Need space to think before discussing",
                "D": "Use communication techniques you've learned",
                "E": "Trust that honest conversation will work",
                "F": "Prioritize their emotional needs and feelings"
            },
            "scoring": {
                "A": "Analyzer", "B": "Sprinter", "C": "Ghost",
                "D": "Scholar", "E": "Naturalist", "F": "Protector"
            }
        },
        {
            "question": "Your biggest dating challenge tends to be:",
            "options": {
                "A": "Overthinking situations and missing opportunities",
                "B": "Being too impulsive and moving too fast",
                "C": "Opening up and putting yourself out there",
                "D": "Balancing knowledge with natural connection",
                "E": "Staying true to yourself while adapting to others",
                "F": "Setting boundaries while being caring"
            },
            "scoring": {
                "A": "Analyzer", "B": "Sprinter", "C": "Ghost",
                "D": "Scholar", "E": "Naturalist", "F": "Protector"
            }
        },
        {
            "question": "Your ideal dating confidence would involve:",
            "options": {
                "A": "Having a clear strategy for every situation",
                "B": "Feeling bold and fearless in all interactions",
                "C": "Being comfortable with quality over quantity",
                "D": "Mastering the skills to connect with anyone",
                "E": "Feeling completely authentic in all dating scenarios",
                "F": "Creating safe, caring connections with potential partners"
            },
            "scoring": {
                "A": "Analyzer", "B": "Sprinter", "C": "Ghost",
                "D": "Scholar", "E": "Naturalist", "F": "Protector"
            }
        }
    ]
    
    def __init__(self, supabase_client, user_id: str):
        super().__init__(supabase_client, user_id, "confidence_test")
        
    async def process_message(self, thread_id: str, user_message: str) -> str:
        """Process user message and advance confidence test flow"""
        try:
            # Start session if needed
            await self.start_session(thread_id)
            
            # Get current progress
            progress = await self.get_progress()
            current_step = progress.get('flow_step', 1)
            responses = progress.get('current_responses', {})
            
            # Parse user response if we're in the middle of questions
            if current_step > 1 and current_step <= len(self.QUESTIONS) + 1:
                # Process the answer to the previous question
                question_index = current_step - 2  # Adjust for 1-based indexing
                if question_index >= 0 and question_index < len(self.QUESTIONS):
                    # Extract answer from user message (look for A, B, C, D, E, F)
                    answer = self._extract_answer(user_message)
                    if answer:
                        responses[f"question_{question_index + 1}"] = answer
                        await self.save_progress({
                            'flow_step': current_step,
                            'current_responses': responses,
                            'completion_percentage': (len(responses) / len(self.QUESTIONS)) * 100
                        })
            
            # Check if we're done with questions
            if len(responses) >= len(self.QUESTIONS):
                # Calculate results and complete the assessment
                result = await self._calculate_results(responses)
                await self._save_final_results(result)
                await self.end_session(thread_id)
                
                response = await self._generate_results_message(result)
                await self.store_conversation(thread_id, user_message, response)
                return response
            
            # Present next question or start the assessment
            if current_step == 1:
                # Welcome message
                response = await self._generate_welcome_message()
                await self.save_progress({'flow_step': 2, 'current_responses': {}, 'completion_percentage': 0.0})
            else:
                # Present next question
                question_index = len(responses)
                if question_index < len(self.QUESTIONS):
                    response = await self._generate_question_message(question_index)
                    await self.save_progress({
                        'flow_step': current_step + 1,
                        'current_responses': responses,
                        'completion_percentage': (len(responses) / len(self.QUESTIONS)) * 100
                    })
                else:
                    # This shouldn't happen, but handle gracefully
                    response = "Thank you for completing the confidence assessment! Let me calculate your results..."
            
            await self.store_conversation(thread_id, user_message, response)
            return response
            
        except Exception as e:
            logger.error(f"Error processing confidence test message: {e}")
            return "I'm sorry, there was an issue with the confidence assessment. Let me try again."
    
    def _extract_answer(self, message: str) -> Optional[str]:
        """Extract A, B, C, D, E, or F from user message"""
        message_upper = message.upper().strip()
        
        # Look for single letter answers
        for letter in ['A', 'B', 'C', 'D', 'E', 'F']:
            if letter in message_upper:
                # Verify it's not part of a larger word
                if len(message_upper) == 1 or message_upper.startswith(letter + ' ') or message_upper.startswith(letter + ')') or message_upper.startswith(letter + '.'):
                    return letter
        
        return None
    
    async def _generate_welcome_message(self) -> str:
        """Generate welcome message for confidence assessment"""
        prompt = """
        You are Connell, a warm and supportive AI partner for dating confidence. You're about to guide someone through a dating confidence assessment.

        Create a welcoming message that:
        1. Explains this is a dating confidence assessment to understand their dating style
        2. Mentions it takes about 5-10 minutes with 12 questions
        3. Emphasizes there are no right or wrong answers
        4. Sets an encouraging, supportive tone
        5. Asks if they're ready to begin

        Keep it warm, professional, and encouraging. Remember you're speaking to someone who might be working on their dating confidence.
        """
        
        messages = [{"role": "user", "content": "I'd like to take the dating confidence assessment."}]
        return await self.call_claude_with_router(messages, prompt)
    
    async def _generate_question_message(self, question_index: int) -> str:
        """Generate message presenting the next question"""
        if question_index >= len(self.QUESTIONS):
            return "Thank you for completing all the questions!"
        
        question_data = self.QUESTIONS[question_index]
        question_num = question_index + 1
        total_questions = len(self.QUESTIONS)
        
        # Format the question with options
        options_text = "\n".join([f"{key}. {value}" for key, value in question_data["options"].items()])
        
        prompt = f"""
        You are Connell, guiding someone through a dating confidence assessment. Present question {question_num} of {total_questions}.

        Question: {question_data['question']}

        Options:
        {options_text}

        Present this in a warm, conversational way. Include:
        1. Progress indicator (Question {question_num} of {total_questions})
        2. The question
        3. The options clearly formatted
        4. Ask them to respond with their choice (A, B, C, D, E, or F)

        Keep it encouraging and remind them there's no wrong answer. This is about understanding their dating confidence style.
        """
        
        messages = [{"role": "user", "content": f"Present question {question_num}"}]
        return await self.call_claude_with_router(messages, prompt)
    
    async def _calculate_results(self, responses: Dict[str, str]) -> Dict[str, Any]:
        """Calculate dating confidence archetype from responses"""
        try:
            # Use the pure scoring functions
            result = calculate_confidence_assessment(responses, total_questions=len(self.QUESTIONS))
            
            logger.info(f"Calculated confidence assessment: {result['assigned_archetype']}/{result['experience_level']}")
            return result
            
        except Exception as e:
            logger.error(f"Error calculating confidence results: {e}")
            # Return safe defaults
            return {
                'archetype_scores': {archetype: 0.0 for archetype in CONFIDENCE_ARCHETYPES.keys()},
                'assigned_archetype': 'Naturalist',
                'experience_level': 'beginner',
                'test_responses': responses
            }
    
    async def _save_final_results(self, result: Dict[str, Any]):
        """Save final results to confidence_test_results table"""
        try:
            # Check if profile already exists
            existing = self.supabase.table('confidence_test_results')\
                .select('id')\
                .eq('user_id', self.user_id)\
                .execute()
            
            profile_data = {
                'user_id': self.user_id,
                'test_responses': result['test_responses'],
                'archetype_scores': result['archetype_scores'],
                'assigned_archetype': result['assigned_archetype'],
                'experience_level': result['experience_level'],
                'created_at': datetime.now(timezone.utc).isoformat()
            }
            
            if existing.data:
                # Update existing profile
                self.supabase.table('confidence_test_results')\
                    .update(profile_data)\
                    .eq('user_id', self.user_id)\
                    .execute()
                logger.info(f"Updated confidence profile for user {self.user_id}")
            else:
                # Create new profile
                self.supabase.table('confidence_test_results')\
                    .insert(profile_data)\
                    .execute()
                logger.info(f"Created confidence profile for user {self.user_id}")
            
            # Also update user_profiles table with archetype and experience level
            try:
                self.supabase.table('user_profiles')\
                    .update({
                        'confidence_archetype': result['assigned_archetype'],
                        'experience_level': result['experience_level'],
                        'updated_at': datetime.now(timezone.utc).isoformat()
                    })\
                    .eq('id', self.user_id)\
                    .execute()
                logger.info(f"Updated user profile with archetype: {result['assigned_archetype']}")
            except Exception as e:
                logger.warning(f"Could not update user_profiles table: {e}")
            
            # Mark progress as completed
            await self.save_progress({
                'flow_step': len(self.QUESTIONS) + 2,
                'current_responses': result['test_responses'],
                'completion_percentage': 100.0,
                'is_completed': True
            })
            
            logger.info(f"Saved confidence profile for user {self.user_id}: {result['assigned_archetype']}")
            
        except Exception as e:
            logger.error(f"Error saving confidence results: {e}")
            raise
    
    async def _generate_results_message(self, result: Dict[str, Any]) -> str:
        """Generate personalized results message"""
        archetype = result['assigned_archetype']
        archetype_info = get_archetype_info(archetype)
        experience_level = result['experience_level']
        
        if not archetype_info:
            archetype_info = {"description": "A balanced dating approach", "traits": ["authentic", "genuine"]}
        
        prompt = f"""
        You are Connell, delivering dating confidence assessment results to someone who just completed the test.

        Their primary dating confidence archetype is: {archetype}
        Description: {archetype_info['description']}
        Key traits: {', '.join(archetype_info['traits'])}
        Experience level: {experience_level}

        Create a warm, personalized message that:
        1. Celebrates their completion of the assessment
        2. Introduces their archetype with enthusiasm
        3. Explains what this means for their dating approach and confidence
        4. Provides 2-3 specific insights about how they can leverage this knowledge in dating
        5. Mentions their experience level and what it means
        6. Ends on an encouraging note about their dating journey

        Make it feel personal and insightful, not generic. Use "you" language and be encouraging about their dating potential.
        Focus on dating confidence, dating scenarios, and relationship building.
        """
        
        messages = [{"role": "user", "content": "Please give me my dating confidence assessment results."}]
        return await self.call_claude_with_router(messages, prompt)
    
    async def get_progress(self) -> Dict[str, Any]:
        """Get current progress for confidence test"""
        try:
            result = self.supabase.table('confidence_test_progress')\
                .select('*')\
                .eq('user_id', self.user_id)\
                .order('created_at', desc=True)\
                .limit(1)\
                .execute()
            
            if result.data:
                return result.data[0]
            else:
                return {'flow_step': 1, 'current_responses': {}, 'completion_percentage': 0.0, 'is_completed': False}
                
        except Exception as e:
            logger.error(f"Error getting confidence test progress: {e}")
            return {'flow_step': 1, 'current_responses': {}, 'completion_percentage': 0.0, 'is_completed': False}
    
    async def save_progress(self, progress_data: Dict[str, Any]):
        """Save progress to confidence_test_progress table"""
        try:
            # Check if progress record exists
            existing = self.supabase.table('confidence_test_progress')\
                .select('id')\
                .eq('user_id', self.user_id)\
                .execute()
            
            save_data = {
                'user_id': self.user_id,
                'flow_step': progress_data.get('flow_step', 1),
                'current_responses': progress_data.get('current_responses', {}),
                'flow_state': progress_data.get('flow_state', {}),
                'completion_percentage': progress_data.get('completion_percentage', 0.0),
                'is_completed': progress_data.get('is_completed', False)
            }
            
            if existing.data:
                # Update existing record
                self.supabase.table('confidence_test_progress')\
                    .update(save_data)\
                    .eq('user_id', self.user_id)\
                    .execute()
            else:
                # Create new record
                self.supabase.table('confidence_test_progress')\
                    .insert(save_data)\
                    .execute()
                    
        except Exception as e:
            logger.error(f"Error saving confidence test progress: {e}")
    
    async def is_flow_complete(self) -> bool:
        """Check if confidence test flow is complete"""
        progress = await self.get_progress()
        return progress.get('is_completed', False)