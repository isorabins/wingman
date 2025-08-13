#!/usr/bin/env python3
"""
Creativity Test Agent for Fridays at Four

Implements the creativity assessment flow using Claude:
- 12-question creativity archetype assessment
- Progress tracking and mid-flow saves
- Results storage in creator_creativity_profiles table
"""

import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

class CreativityTestAgent(BaseAgent):
    """Agent for conducting creativity assessments"""
    
    # Creativity archetypes and their characteristics
    ARCHETYPES = {
        "The Explorer": {
            "description": "Driven by curiosity and discovery",
            "traits": ["experimental", "adventurous", "open-minded", "curious"]
        },
        "The Artist": {
            "description": "Focused on aesthetic expression and beauty", 
            "traits": ["aesthetic", "expressive", "intuitive", "emotional"]
        },
        "The Innovator": {
            "description": "Creates new solutions and disrupts the status quo",
            "traits": ["disruptive", "solution-oriented", "forward-thinking", "pragmatic"]
        },
        "The Connector": {
            "description": "Builds bridges between ideas and people",
            "traits": ["collaborative", "synthesizing", "networking", "integrative"]
        },
        "The Maker": {
            "description": "Brings ideas into tangible reality",
            "traits": ["hands-on", "practical", "craftsmanship", "detail-oriented"]
        },
        "The Storyteller": {
            "description": "Communicates through narrative and meaning",
            "traits": ["narrative", "meaningful", "communicative", "inspiring"]
        }
    }
    
    # Assessment questions designed to identify creativity archetype
    QUESTIONS = [
        {
            "question": "When starting a new creative project, what excites you most?",
            "options": {
                "A": "The unknown possibilities and what I might discover",
                "B": "Creating something beautiful that moves people",
                "C": "Solving a problem in a completely new way", 
                "D": "Bringing together different perspectives or ideas",
                "E": "The process of making something real with my hands",
                "F": "Sharing a meaningful story or message"
            },
            "scoring": {
                "A": "The Explorer", "B": "The Artist", "C": "The Innovator",
                "D": "The Connector", "E": "The Maker", "F": "The Storyteller"
            }
        },
        {
            "question": "When you hit a creative block, what's your go-to strategy?",
            "options": {
                "A": "Explore completely different fields for inspiration",
                "B": "Surround myself with beauty and artistic inspiration",
                "C": "Look for constraints or limitations to spark innovation",
                "D": "Talk it through with others and gather different viewpoints", 
                "E": "Start making something, anything, with my hands",
                "F": "Think about the deeper meaning or story I want to tell"
            },
            "scoring": {
                "A": "The Explorer", "B": "The Artist", "C": "The Innovator",
                "D": "The Connector", "E": "The Maker", "F": "The Storyteller"
            }
        },
        {
            "question": "What type of feedback energizes you most?",
            "options": {
                "A": "Questions that open up new directions to explore",
                "B": "Recognition of the emotional impact of my work",
                "C": "Acknowledgment of the originality of my approach",
                "D": "Seeing how my work connects people or ideas",
                "E": "Appreciation for the craft and skill in execution",
                "F": "Understanding of the message or story I'm conveying"
            },
            "scoring": {
                "A": "The Explorer", "B": "The Artist", "C": "The Innovator",
                "D": "The Connector", "E": "The Maker", "F": "The Storyteller"
            }
        },
        {
            "question": "In a team creative session, you naturally tend to:",
            "options": {
                "A": "Suggest unexplored angles and 'what if' scenarios",
                "B": "Focus on the aesthetic and emotional qualities",
                "C": "Challenge assumptions and propose radical alternatives",
                "D": "Help synthesize different ideas into something cohesive",
                "E": "Think through practical implementation details",
                "F": "Ensure the work has a clear narrative or purpose"
            },
            "scoring": {
                "A": "The Explorer", "B": "The Artist", "C": "The Innovator",
                "D": "The Connector", "E": "The Maker", "F": "The Storyteller"
            }
        },
        {
            "question": "Your ideal creative workspace would have:",
            "options": {
                "A": "Easy access to research materials and inspiration from many fields",
                "B": "Beautiful objects, artwork, and inspiring aesthetics",
                "C": "Whiteboards, prototyping tools, and space for experimentation",
                "D": "Comfortable areas for collaboration and discussion",
                "E": "High-quality tools and materials for hands-on creation",
                "F": "A quiet space for reflection and deep thinking about meaning"
            },
            "scoring": {
                "A": "The Explorer", "B": "The Artist", "C": "The Innovator",
                "D": "The Connector", "E": "The Maker", "F": "The Storyteller"
            }
        },
        {
            "question": "When you share your work, you most hope people will:",
            "options": {
                "A": "Be curious and want to explore the ideas further",
                "B": "Feel moved or emotionally connected to it",
                "C": "See new possibilities they hadn't considered before",
                "D": "Find connections to their own experiences or other ideas",
                "E": "Appreciate the quality and craftsmanship",
                "F": "Understand and be inspired by the deeper message"
            },
            "scoring": {
                "A": "The Explorer", "B": "The Artist", "C": "The Innovator",
                "D": "The Connector", "E": "The Maker", "F": "The Storyteller"
            }
        },
        {
            "question": "Your creative process is most energized by:",
            "options": {
                "A": "Research, investigation, and discovery",
                "B": "Intuition, emotion, and aesthetic sensibility", 
                "C": "Problem-solving and systematic innovation",
                "D": "Collaboration and building on others' ideas",
                "E": "Experimentation with materials and techniques",
                "F": "Reflection on meaning and human experience"
            },
            "scoring": {
                "A": "The Explorer", "B": "The Artist", "C": "The Innovator",
                "D": "The Connector", "E": "The Maker", "F": "The Storyteller"
            }
        },
        {
            "question": "You feel most creative when:",
            "options": {
                "A": "Diving deep into subjects that fascinate you",
                "B": "Expressing something deeply personal or emotional",
                "C": "Tackling challenges that seem impossible to others",
                "D": "Working with diverse, inspiring people",
                "E": "Working with your hands and quality materials",
                "F": "Creating work that has personal or cultural significance"
            },
            "scoring": {
                "A": "The Explorer", "B": "The Artist", "C": "The Innovator",
                "D": "The Connector", "E": "The Maker", "F": "The Storyteller"
            }
        },
        {
            "question": "The creative projects that excite you most are:",
            "options": {
                "A": "Those that let you investigate new territories",
                "B": "Those focused on beauty, emotion, or aesthetic experience",
                "C": "Those that solve real problems in breakthrough ways",
                "D": "Those that bring people together around shared goals",
                "E": "Those where you can create something tangible and lasting",
                "F": "Those that communicate important ideas or stories"
            },
            "scoring": {
                "A": "The Explorer", "B": "The Artist", "C": "The Innovator",
                "D": "The Connector", "E": "The Maker", "F": "The Storyteller"
            }
        },
        {
            "question": "When evaluating your own creative work, you focus on:",
            "options": {
                "A": "How much it expanded your understanding",
                "B": "Whether it captures the right feeling or aesthetic",
                "C": "How novel and effective the solution is",
                "D": "How well it resonates with and connects others",
                "E": "The quality of execution and attention to detail",
                "F": "Whether it successfully conveys your intended meaning"
            },
            "scoring": {
                "A": "The Explorer", "B": "The Artist", "C": "The Innovator",
                "D": "The Connector", "E": "The Maker", "F": "The Storyteller"
            }
        },
        {
            "question": "Your biggest creative fear is:",
            "options": {
                "A": "Running out of new things to discover or explore",
                "B": "Creating work that lacks beauty or emotional resonance",
                "C": "Being seen as conventional or following the crowd",
                "D": "Working in isolation without meaningful collaboration",
                "E": "Producing work that lacks quality or craftsmanship",
                "F": "Creating work that has no deeper meaning or impact"
            },
            "scoring": {
                "A": "The Explorer", "B": "The Artist", "C": "The Innovator",
                "D": "The Connector", "E": "The Maker", "F": "The Storyteller"
            }
        },
        {
            "question": "The legacy you'd want your creative work to have is:",
            "options": {
                "A": "Inspiring others to explore and discover new possibilities",
                "B": "Creating beauty that enriches people's lives",
                "C": "Pioneering approaches that change how things are done",
                "D": "Building bridges and fostering deeper connections",
                "E": "Setting a standard for excellence in craft and quality",
                "F": "Telling stories that matter and inspire positive change"
            },
            "scoring": {
                "A": "The Explorer", "B": "The Artist", "C": "The Innovator",
                "D": "The Connector", "E": "The Maker", "F": "The Storyteller"
            }
        }
    ]
    
    def __init__(self, supabase_client, user_id: str):
        super().__init__(supabase_client, user_id, "creativity_test")
        
    async def process_message(self, thread_id: str, user_message: str) -> str:
        """Process user message and advance creativity test flow"""
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
                    response = "Thank you for completing the creativity assessment! Let me calculate your results..."
            
            await self.store_conversation(thread_id, user_message, response)
            return response
            
        except Exception as e:
            logger.error(f"Error processing creativity test message: {e}")
            return "I'm sorry, there was an issue with the creativity assessment. Let me try again."
    
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
        """Generate welcome message for creativity assessment"""
        prompt = """
        You are Hai, a warm and supportive AI partner for creative professionals. You're about to guide someone through a creativity archetype assessment.

        Create a welcoming message that:
        1. Explains this is a creativity assessment to understand their creative style
        2. Mentions it takes about 5-10 minutes with 12 questions
        3. Emphasizes there are no right or wrong answers
        4. Sets an encouraging, supportive tone
        5. Asks if they're ready to begin

        Keep it warm, professional, and encouraging. Remember you're speaking to someone who might be unsure about their creativity.
        """
        
        messages = [{"role": "user", "content": "I'd like to take the creativity assessment."}]
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
        You are Hai, guiding someone through a creativity assessment. Present question {question_num} of {total_questions}.

        Question: {question_data['question']}

        Options:
        {options_text}

        Present this in a warm, conversational way. Include:
        1. Progress indicator (Question {question_num} of {total_questions})
        2. The question
        3. The options clearly formatted
        4. Ask them to respond with their choice (A, B, C, D, E, or F)

        Keep it encouraging and remind them there's no wrong answer.
        """
        
        messages = [{"role": "user", "content": f"Present question {question_num}"}]
        return await self.call_claude_with_router(messages, prompt)
    
    async def _calculate_results(self, responses: Dict[str, str]) -> Dict[str, Any]:
        """Calculate creativity archetype from responses"""
        # Count votes for each archetype
        archetype_scores = {archetype: 0 for archetype in self.ARCHETYPES.keys()}
        
        for question_key, answer in responses.items():
            question_index = int(question_key.split('_')[1]) - 1
            if question_index < len(self.QUESTIONS):
                question_data = self.QUESTIONS[question_index]
                if answer in question_data["scoring"]:
                    archetype = question_data["scoring"][answer]
                    archetype_scores[archetype] += 1
        
        # Find primary and secondary archetypes
        sorted_scores = sorted(archetype_scores.items(), key=lambda x: x[1], reverse=True)
        primary_archetype = sorted_scores[0][0]
        primary_score = sorted_scores[0][1]
        secondary_archetype = sorted_scores[1][0] if len(sorted_scores) > 1 else None
        secondary_score = sorted_scores[1][1] if len(sorted_scores) > 1 else 0
        
        return {
            'archetype': primary_archetype,
            'archetype_score': primary_score,
            'secondary_archetype': secondary_archetype,
            'secondary_score': secondary_score,
            'test_responses': responses,
            'all_scores': archetype_scores
        }
    
    async def _save_final_results(self, result: Dict[str, Any]):
        """Save final results to creator_creativity_profiles table"""
        try:
            # Check if profile already exists
            existing = self.supabase.table('creator_creativity_profiles')\
                .select('id')\
                .eq('user_id', self.user_id)\
                .execute()
            
            profile_data = {
                'user_id': self.user_id,
                'archetype': result['archetype'],
                'archetype_score': result['archetype_score'],
                'secondary_archetype': result['secondary_archetype'],
                'secondary_score': result['secondary_score'],
                'test_responses': result['test_responses'],
                'date_taken': datetime.now(timezone.utc).isoformat()
            }
            
            if existing.data:
                # Update existing profile
                self.supabase.table('creator_creativity_profiles')\
                    .update(profile_data)\
                    .eq('user_id', self.user_id)\
                    .execute()
            else:
                # Create new profile
                self.supabase.table('creator_creativity_profiles')\
                    .insert(profile_data)\
                    .execute()
            
            # Mark progress as completed
            await self.save_progress({
                'flow_step': len(self.QUESTIONS) + 2,
                'current_responses': result['test_responses'],
                'completion_percentage': 100.0,
                'is_completed': True
            })
            
            logger.info(f"Saved creativity profile for user {self.user_id}: {result['archetype']}")
            
        except Exception as e:
            logger.error(f"Error saving creativity results: {e}")
            raise
    
    async def _generate_results_message(self, result: Dict[str, Any]) -> str:
        """Generate personalized results message"""
        archetype = result['archetype']
        archetype_info = self.ARCHETYPES[archetype]
        secondary = result.get('secondary_archetype')
        
        prompt = f"""
        You are Hai, delivering creativity assessment results to someone who just completed the test.

        Their primary creativity archetype is: {archetype}
        Description: {archetype_info['description']}
        Key traits: {', '.join(archetype_info['traits'])}
        
        {f"Secondary archetype: {secondary}" if secondary else ""}

        Create a warm, personalized message that:
        1. Celebrates their completion of the assessment
        2. Introduces their primary archetype with enthusiasm
        3. Explains what this means for their creative approach
        4. Mentions their secondary archetype if they have one
        5. Provides 2-3 specific insights about how they can leverage this knowledge
        6. Ends on an encouraging note about their creative journey

        Make it feel personal and insightful, not generic. Use "you" language and be encouraging about their creative potential.
        """
        
        messages = [{"role": "user", "content": "Please give me my creativity assessment results."}]
        return await self.call_claude_with_router(messages, prompt)
    
    async def get_progress(self) -> Dict[str, Any]:
        """Get current progress for creativity test"""
        try:
            result = self.supabase.table('creativity_test_progress')\
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
            logger.error(f"Error getting creativity test progress: {e}")
            return {'flow_step': 1, 'current_responses': {}, 'completion_percentage': 0.0, 'is_completed': False}
    
    async def save_progress(self, progress_data: Dict[str, Any]):
        """Save progress to creativity_test_progress table"""
        try:
            # Check if progress record exists
            existing = self.supabase.table('creativity_test_progress')\
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
                self.supabase.table('creativity_test_progress')\
                    .update(save_data)\
                    .eq('user_id', self.user_id)\
                    .execute()
            else:
                # Create new record
                self.supabase.table('creativity_test_progress')\
                    .insert(save_data)\
                    .execute()
                    
        except Exception as e:
            logger.error(f"Error saving creativity test progress: {e}")
    
    async def is_flow_complete(self) -> bool:
        """Check if creativity test flow is complete"""
        progress = await self.get_progress()
        return progress.get('is_completed', False) 