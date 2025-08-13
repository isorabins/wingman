#!/usr/bin/env python3
"""
Creativity Test Flow Handler - Structured 11-question test
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class CreativityFlowHandler:
    """Handles structured creativity test flow"""
    
    # Test questions with A/B/C/D options
    QUESTIONS = [
        {
            "number": 1,
            "question": "You wake up with the perfect idea. What actually happens?",
            "options": {
                "A": "Frantically write/sketch on whatever's nearby",
                "B": "Immediately google if someone already did this",
                "C": "Map out the entire project before getting dressed",
                "D": "Text someone way too early to share the excitement"
            }
        },
        {
            "number": 2,
            "question": "It's 2am and you just had an amazing breakthrough. What do you do?",
            "options": {
                "A": "Stay up all night exploring where it leads",
                "B": "Write it down and go back to sleep",
                "C": "Immediately start planning how to execute it",
                "D": "Wake up your partner to share the excitement"
            }
        },
        {
            "number": 3,
            "question": "Your friend asks to see your work-in-progress. Your reaction?",
            "options": {
                "A": "\"It's not ready yet!\" (hide it away)",
                "B": "\"Yes! Tell me what you think!\"",
                "C": "Show it but ask for specific feedback only",
                "D": "Share it but explain all the flaws first"
            }
        },
        {
            "number": 4,
            "question": "You're at a coffee shop and overhear someone describing your exact creative vision. How do you feel?",
            "options": {
                "A": "Panicked - they're going to steal my idea!",
                "B": "Excited - we should collaborate!",
                "C": "Motivated - time to execute faster",
                "D": "Curious - I want to hear their take"
            }
        },
        {
            "number": 5,
            "question": "Your project hits a wall and you're completely stuck. What's your survival strategy?",
            "options": {
                "A": "Step away and let your subconscious work on it",
                "B": "Break it into smaller, manageable pieces",
                "C": "Talk through it with someone who gets it",
                "D": "See how others tackled similar problems"
            }
        },
        {
            "number": 6,
            "question": "You're sharing your finished work for the first time. What's running through your head?",
            "options": {
                "A": "\"Please love it as much as I do!\"",
                "B": "\"I hope this helps someone\"",
                "C": "\"Here are all the things I'd change next time\"",
                "D": "\"Done is better than perfect - let's see what happens!\""
            }
        },
        {
            "number": 7,
            "question": "Your creative workspace is a disaster. What happens next?",
            "options": {
                "A": "Can't focus until everything has a place",
                "B": "Know exactly where everything is in the chaos",
                "C": "Take a photo because it actually looks pretty cool",
                "D": "Grab your laptop and work literally anywhere else"
            }
        },
        {
            "number": 8,
            "question": "Someone gives you harsh but honest feedback. Your first instinct?",
            "options": {
                "A": "They don't understand what I'm trying to do",
                "B": "This is exactly what I needed to hear",
                "C": "Overwhelmed - where do I even start with all this?",
                "D": "Game on - I'll show them what's possible"
            }
        },
        {
            "number": 9,
            "question": "You stumble across someone doing exactly what you want to do, but they're already successful at it. What's your honest reaction?",
            "options": {
                "A": "\"Well, that idea is ruined for me now\"",
                "B": "\"Amazing! Now I know it's possible\"",
                "C": "\"Time to study everything they did\"",
                "D": "\"I need to find my unique angle on this\""
            }
        },
        {
            "number": 10,
            "question": "You have one hour of unexpected free time. What's your creative move?",
            "options": {
                "A": "Finally tackle that project I've been planning",
                "B": "Experiment with something completely new",
                "C": "Organize my creative space and materials",
                "D": "Catch up on that creative course I started"
            }
        },
        {
            "number": 11,
            "question": "Your biggest creative fear whispers in your ear. What does it say?",
            "options": {
                "A": "\"What if no one cares about this?\"",
                "B": "\"What if I can't pull this off?\"",
                "C": "\"What if it's not perfect?\"",
                "D": "\"What if I'm just fooling myself?\""
            }
        }
    ]
    
    # Archetype mapping based on answer patterns - COMPLETE SCORING SYSTEM
    ARCHETYPE_SCORING = {
        "Big Picture Visionary": {
            "A": [1, 5, 9],              # Questions 1, 5, 9 - intuitive, stepping back, protective
            "B": [3, 6, 10],             # Questions 3, 6, 10 - sharing, helping others, experimentation
            "C": [2, 4, 7, 8, 11],       # Questions 2, 4, 7, 8, 11 - planning, strategic, perfectionist
            "D": []                      # No primary D associations
        },
        "Creative Sprinter": {
            "A": [1, 2, 7, 10],          # Questions 1, 2, 7, 10 - immediate action, intense focus, organizing
            "B": [8, 9],                 # Questions 8, 9 - learning from feedback, optimism about others' success
            "C": [4, 11],                # Questions 4, 11 - competitive execution, perfectionist fears
            "D": [6, 8]                  # Questions 6, 8 - action-oriented, confident responses
        },
        "Steady Builder": {
            "A": [3, 7, 11],             # Questions 3, 7, 11 - careful protection, need for order, validation seeking
            "B": [2, 5, 9],              # Questions 2, 5, 9 - methodical approach, systematic breakdown
            "C": [6, 8, 10],             # Questions 6, 8, 10 - structured feedback, overwhelm, organization
            "D": [4]                     # Question 4 - curious but measured approach
        },
        "Collaborative Creator": {
            "A": [4, 6],                 # Questions 4, 6 - protective but seeking validation
            "B": [3, 4, 7, 10],          # Questions 3, 4, 7, 10 - sharing, collaboration, comfortable with chaos
            "C": [5, 9],                 # Questions 5, 9 - talking through problems, studying others
            "D": [1, 2, 8, 11]           # Questions 1, 2, 8, 11 - sharing excitement, confident responses
        },
        "Independent Maker": {
            "A": [8, 9, 10],             # Questions 8, 9, 10 - self-reliant, protective, focused execution
            "B": [11],                   # Question 11 - capability concerns but self-driven
            "C": [3, 4, 5, 9],           # Questions 3, 4, 5, 9 - focused execution, analytical
            "D": [5, 7]                  # Questions 5, 7 - research-oriented, adaptable workspace
        },
        "Intuitive Artist": {
            "A": [1, 5, 6, 7],           # Questions 1, 5, 6, 7 - intuitive responses, perfectionist environment
            "B": [6, 9, 10, 11],         # Questions 6, 9, 10, 11 - authentic sharing, optimism, experimentation
            "C": [2, 10, 11],            # Questions 2, 10, 11 - perfectionist tendencies, organized creativity
            "D": [3, 8]                  # Questions 3, 8 - expressive sharing, game-on attitude
        }
    }
    
    def __init__(self, supabase, user_id: str):
        self.supabase = supabase
        self.user_id = user_id
    
    async def handle_message(self, message: str, flow_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process creativity test message"""
        try:
            current_q = flow_data.get('current_question', 1)
            responses = flow_data.get('responses', {})
            
            # If not first question, extract answer from previous
            if current_q > 1 and current_q <= 12:  # 11 questions + 1
                answer = self._extract_answer(message)
                
                if not answer:
                    return {
                        'response': f"Please choose A, B, C, or D for question {current_q - 1}.",
                        'flow_complete': False,
                        'progress': self._calculate_progress(current_q - 1, 11)
                    }
                
                # Store answer
                responses[f'question_{current_q - 1}'] = answer
                await self._save_progress(current_q, responses)
            
            # Check if test complete
            if len(responses) >= 11:
                # Calculate and save results
                archetype_result = self._calculate_archetype(responses)
                await self._save_final_results(archetype_result)
                
                return {
                    'response': self._generate_results_message(archetype_result),
                    'flow_complete': True,
                    'next_flow': 'project',
                    'archetype': archetype_result['primary_archetype']
                }
            
            # Get next question
            if current_q <= 11:
                question_data = self.QUESTIONS[current_q - 1]
                response = self._format_question(question_data, current_q)
                
                # Update progress
                await self._save_progress(current_q + 1, responses)
                
                return {
                    'response': response,
                    'flow_complete': False,
                    'progress': self._calculate_progress(current_q, 11)
                }
            
            # Shouldn't reach here
            return {
                'response': "Let's continue with your creativity test.",
                'flow_complete': False
            }
            
        except Exception as e:
            logger.error(f"Error in creativity flow: {e}")
            return {
                'response': "Let's continue with your creativity test. What was your answer?",
                'flow_complete': False
            }
    
    def _extract_answer(self, message: str) -> Optional[str]:
        """Extract A, B, C, or D from user message"""
        message_upper = message.upper().strip()
        
        # Direct single letter
        if message_upper in ['A', 'B', 'C', 'D']:
            return message_upper
        
        # Look for patterns like "A)" or "A."
        for letter in ['A', 'B', 'C', 'D']:
            if message_upper.startswith(letter) and len(message_upper) < 10:
                return letter
        
        # Look for letter anywhere in short message
        if len(message_upper) < 20:
            for letter in ['A', 'B', 'C', 'D']:
                if letter in message_upper:
                    return letter
        
        return None
    
    def _format_question(self, question_data: Dict, question_num: int) -> str:
        """Format question for display"""
        options_text = "\n".join([
            f"{letter}. {text}" 
            for letter, text in question_data['options'].items()
        ])
        
        return f"""**Question {question_num} of 11**

{question_data['question']}

{options_text}

Please respond with A, B, C, or D."""
    
    def _calculate_progress(self, current: int, total: int) -> Dict[str, Any]:
        """Calculate progress metrics"""
        return {
            'current_step': current,
            'total_steps': total,
            'completion_percentage': ((current - 1) / total) * 100,
            'display_text': f"Question {current} of {total}"
        }
    
    def _calculate_archetype(self, responses: Dict[str, str]) -> Dict[str, Any]:
        """Calculate primary and secondary archetypes from responses"""
        archetype_scores = {arch: 0 for arch in self.ARCHETYPE_SCORING.keys()}
        
        # Score each response
        for q_key, answer in responses.items():
            # Handle both integer keys (from tests) and string keys (from actual usage)
            if isinstance(q_key, int):
                q_num = q_key
            else:
                q_num = int(q_key.split('_')[1])
            
            for archetype, scoring in self.ARCHETYPE_SCORING.items():
                for ans_letter, question_nums in scoring.items():
                    if answer == ans_letter and q_num in question_nums:
                        archetype_scores[archetype] += 1
        
        # Sort by score
        sorted_archetypes = sorted(
            archetype_scores.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        
        return {
            'primary_archetype': sorted_archetypes[0][0],
            'primary_score': sorted_archetypes[0][1],
            'secondary_archetype': sorted_archetypes[1][0] if len(sorted_archetypes) > 1 else None,
            'secondary_score': sorted_archetypes[1][1] if len(sorted_archetypes) > 1 else 0,
            'all_scores': archetype_scores,
            'responses': responses
        }
    
    async def _save_progress(self, next_question: int, responses: Dict[str, str]):
        """Save test progress to database"""
        try:
            progress_data = {
                'user_id': self.user_id,  # Added user_id for INSERT
                'flow_step': next_question,
                'current_responses': responses,
                'completion_percentage': ((len(responses) / 11) * 100),
                'is_completed': False
            }
            
            # Check if record exists first
            existing = self.supabase.table('creativity_test_progress')\
                .select('id')\
                .eq('user_id', self.user_id)\
                .execute()
            
            if existing.data:
                # Update existing record
                self.supabase.table('creativity_test_progress')\
                    .update(progress_data)\
                    .eq('user_id', self.user_id)\
                    .execute()
            else:
                # Create new record (first time)
                self.supabase.table('creativity_test_progress')\
                    .insert(progress_data)\
                    .execute()
                
        except Exception as e:
            logger.error(f"Error saving creativity progress: {e}")
    
    async def _save_final_results(self, archetype_result: Dict[str, Any]):
        """Save final results to creator_creativity_profiles"""
        try:
            profile_data = {
                'user_id': self.user_id,
                'archetype': archetype_result['primary_archetype'],
                'archetype_score': archetype_result['primary_score'],
                'secondary_archetype': archetype_result['secondary_archetype'],
                'secondary_score': archetype_result['secondary_score'],
                'test_responses': archetype_result['responses'],
                'date_taken': datetime.now(timezone.utc).isoformat()
            }
            
            # Check if profile exists
            existing = self.supabase.table('creator_creativity_profiles')\
                .select('id')\
                .eq('user_id', self.user_id)\
                .execute()
            
            if existing.data:
                # Update existing
                self.supabase.table('creator_creativity_profiles')\
                    .update(profile_data)\
                    .eq('user_id', self.user_id)\
                    .execute()
            else:
                # Create new
                self.supabase.table('creator_creativity_profiles')\
                    .insert(profile_data)\
                    .execute()
            
            # Mark test as completed
            self.supabase.table('creativity_test_progress')\
                .update({
                    'is_completed': True,
                    'completion_percentage': 100.0
                })\
                .eq('user_id', self.user_id)\
                .execute()
                
        except Exception as e:
            logger.error(f"Error saving creativity results: {e}")
    
    def _generate_results_message(self, archetype_result: Dict[str, Any]) -> str:
        """Generate personalized results message"""
        primary = archetype_result['primary_archetype']
        secondary = archetype_result.get('secondary_archetype')
        
        archetype_descriptions = {
            "Big Picture Visionary": "You see entire worlds where others see single ideas. Your strength is connecting dots and envisioning what's possible.",
            "Creative Sprinter": "You work in powerful bursts of creative energy. Your intensity creates amazing work when you honor your natural rhythms.",
            "Steady Builder": "You turn dreams into reality through consistent, methodical progress. Your superpower is making steady progress every day.",
            "Collaborative Creator": "You shine brightest when bouncing ideas off others. Your gift is bringing out the best in creative partnerships.",
            "Independent Maker": "You do your best work with deep focus and autonomy. Your strength is the unique vision you bring to every project.",
            "Intuitive Artist": "You trust your instincts and create from the heart. Your authenticity and emotional depth make your work resonate."
        }
        
        message = f"""🎉 **Wonderful! You're {primary}!**

{archetype_descriptions.get(primary, 'You have a unique creative style that sets you apart.')}
"""
        
        if secondary:
            message += f"\n\nYou also have strong {secondary} tendencies, which adds depth to your creative approach."
        
        message += "\n\nNow that I understand your creative style, let's plan out your project together. I'll adapt how I work with you based on what we just learned."
        
        return message
    
    def get_start_message(self) -> str:
        """Get creativity test start message"""
        return """Great! Let's discover your creative archetype. 

I'll ask you 11 questions about how you approach creative work. There are no right or wrong answers - just choose what feels most natural to you.

**Question 1 of 11**

You wake up with the perfect idea. What actually happens?

A. Frantically write/sketch on whatever's nearby
B. Immediately google if someone already did this
C. Map out the entire project before getting dressed
D. Text someone way too early to share the excitement

Please respond with A, B, C, or D.""" 