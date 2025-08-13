#!/usr/bin/env python3
"""
Simple Chat Handler for Fridays at Four
Replaces complex agent system with functional approach
"""

import json
import logging
import re
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
from supabase import Client

from src.llm_router import get_router
from src.simple_memory import SimpleMemory

logger = logging.getLogger(__name__)

class SimpleChatHandler:
    """Simple functional chat handler - replaces entire agent system"""
    
    # Complete creativity archetype definitions
    CREATIVITY_ARCHETYPES = {
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

    # ALL 12 CREATIVITY QUESTIONS (Complete Set)
    CREATIVITY_QUESTIONS = [
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

    # ALL 8 PROJECT OVERVIEW TOPICS (Complete Set)
    PROJECT_TOPICS = [
        {
            "topic_number": 1,
            "title": "Project Vision & Core Concept",
            "description": "Understanding the fundamental idea and vision",
            "key_questions": [
                "What's the core concept or story you want to bring to life?",
                "What drew you to this particular project?",
                "What feelings or impact do you want your audience to have?"
            ],
            "completion_indicators": ["project_concept", "personal_connection", "audience_impact"]
        },
        {
            "topic_number": 2,
            "title": "Project Type & Format",
            "description": "Defining the medium and format",
            "key_questions": [
                "What type of project is this? (book, film, podcast, app, etc.)",
                "What format or medium feels right for your vision?",
                "Have you considered alternative formats?"
            ],
            "completion_indicators": ["project_type", "format_decision", "format_reasoning"]
        },
        {
            "topic_number": 3,
            "title": "Target Audience & Community",
            "description": "Understanding who this is for",
            "key_questions": [
                "Who is your ideal audience for this project?",
                "What problems or needs does your project address for them?",
                "How do you want to connect with and serve this community?"
            ],
            "completion_indicators": ["target_audience", "audience_needs", "community_connection"]
        },
        {
            "topic_number": 4,
            "title": "Personal Goals & Success Vision",
            "description": "Defining what success looks like",
            "key_questions": [
                "What are your personal goals for this project?",
                "How will you know when this project is successful?",
                "What would achieving this mean for your creative journey?"
            ],
            "completion_indicators": ["personal_goals", "success_metrics", "creative_significance"]
        },
        {
            "topic_number": 5,
            "title": "Current Challenges & Obstacles",
            "description": "Identifying what's holding you back",
            "key_questions": [
                "What's the biggest challenge you're facing right now?",
                "What obstacles have you encountered so far?",
                "What support or resources do you feel you need most?"
            ],
            "completion_indicators": ["main_challenges", "encountered_obstacles", "needed_support"]
        },
        {
            "topic_number": 6,
            "title": "Timeline & Project Scope",
            "description": "Planning timeline and defining scope",
            "key_questions": [
                "What's your ideal timeline for completing this project?",
                "How do you want to break this down into manageable phases?",
                "What's the minimum viable version vs. your dream vision?"
            ],
            "completion_indicators": ["target_timeline", "project_phases", "scope_definition"]
        },
        {
            "topic_number": 7,
            "title": "Resources & Support System",
            "description": "Identifying what you need to succeed",
            "key_questions": [
                "What skills, tools, or resources do you already have?",
                "What do you need to learn or acquire?",
                "Who could be part of your support system for this project?"
            ],
            "completion_indicators": ["existing_resources", "needed_resources", "support_network"]
        },
        {
            "topic_number": 8,
            "title": "Next Steps & Commitment",
            "description": "Planning immediate next actions",
            "key_questions": [
                "What's the very first step you want to take?",
                "How do you want to maintain momentum on this project?",
                "What kind of ongoing support would be most helpful?"
            ],
            "completion_indicators": ["first_steps", "momentum_plan", "ongoing_support"]
        }
    ]
    
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client
        
    async def process_message(self, user_id: str, message: str, thread_id: str) -> str:
        """Main chat processing - single entry point"""
        try:
            # Initialize memory
            memory = SimpleMemory(self.supabase, user_id)
            
            # Fast database status checks
            creativity_done = await self._check_creativity_complete(user_id)
            project_done = await self._check_project_complete(user_id)
            needs_intro = await self._needs_intro(user_id)
            
            # Check skip status
            creativity_skip = await self._check_creativity_skip(user_id)
            project_skip = await self._check_project_skip(user_id)
            
            # Route conversation
            response = await self._route_conversation(
                user_id, message, thread_id, 
                creativity_done, project_done, needs_intro,
                creativity_skip, project_skip
            )
            
            # Store conversation in memory
            try:
                await memory.add_message(thread_id, message, "user")
                await memory.add_message(thread_id, response, "assistant")
            except Exception as e:
                logger.error(f"Error storing conversation: {e}")
            
            return response
            
        except Exception as e:
            logger.error(f"Error in chat processing: {e}")
            return "I'm sorry, I'm having trouble right now. Please try again in a moment."

    # === DATABASE STATUS CHECKS ===
    
    async def _check_creativity_complete(self, user_id: str) -> bool:
        """Check if creativity test is complete"""
        try:
            result = self.supabase.table('creator_creativity_profiles')\
                .select('id')\
                .eq('user_id', user_id)\
                .limit(1)\
                .execute()
            
            return len(result.data) > 0
            
        except Exception as e:
            logger.error(f"Error checking creativity completion: {e}")
            return False  # Graceful default
    
    async def _check_project_complete(self, user_id: str) -> bool:
        """Check if project overview is complete"""
        try:
            result = self.supabase.table('project_overview')\
                .select('id')\
                .eq('user_id', user_id)\
                .limit(1)\
                .execute()
            
            return len(result.data) > 0
            
        except Exception as e:
            logger.error(f"Error checking project completion: {e}")
            return False  # Graceful default
    
    async def _needs_intro(self, user_id: str) -> bool:
        """Check if user needs introduction flow"""
        try:
            # Check if user has completed intro
            result = self.supabase.table('creativity_test_progress')\
                .select('has_seen_intro')\
                .eq('user_id', user_id)\
                .order('updated_at', desc=True)\
                .limit(1)\
                .execute()
            
            if not result.data:
                # New user - they need intro
                return True
            
            # Check if intro has been completed
            return not result.data[0].get('has_seen_intro', False)
            
        except Exception as e:
            logger.error(f"Error checking intro needs: {e}")
            return True  # Default to needing intro on error

    # === INTRO FLOW HANDLERS ===
    
    async def _handle_intro_flow(self, user_id: str, message: str, thread_id: str) -> str:
        """Handle natural intro conversation using memory and AI"""
        try:
            from .simple_memory import SimpleMemory
            from .llm_router import get_router
            
            # Get conversation memory
            memory = SimpleMemory(self.supabase, user_id)
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
            router = get_router()
            response = await router.chat_completion(messages=messages)
            
            # Check if intro seems complete and user is ready for creativity test
            if self._intro_seems_complete(context, response, message):
                # Mark intro as complete
                await self._mark_intro_complete(user_id)
                
                # If response mentions starting creativity test, begin it
                if any(phrase in response.lower() for phrase in ["creativity test", "first question", "question 1"]):
                    return response + "\n\nQuestion 1 of 12: When starting a new creative project, what excites you most?\n\nA. The unknown possibilities and what I might discover\nB. Creating something beautiful that moves people\nC. Solving a problem in a completely new way\nD. Bringing together different perspectives or ideas\nE. The process of making something real with my hands\nF. Sharing a meaningful story or message\n\nJust respond with A, B, C, D, E, or F."
            
            return response
            
        except Exception as e:
            logger.error(f"Error in intro flow: {e}")
            return "Hi! I'm Hai, your creative partner here at Fridays at Four. What's your name? I'd love to know what to call you."

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

    # === SKIP FUNCTIONALITY ===
    
    async def _check_creativity_skip(self, user_id: str) -> Optional[datetime]:
        """Check creativity skip status"""
        try:
            result = self.supabase.table('creativity_test_progress')\
                .select('skipped_until')\
                .eq('user_id', user_id)\
                .order('created_at', desc=True)\
                .limit(1)\
                .execute()
            
            if result.data and result.data[0].get('skipped_until'):
                return datetime.fromisoformat(result.data[0]['skipped_until'].replace('Z', '+00:00'))
            
            return None
            
        except Exception as e:
            logger.error(f"Error checking creativity skip: {e}")
            return None
    
    async def _check_project_skip(self, user_id: str) -> Optional[datetime]:
        """Check project skip status"""
        try:
            result = self.supabase.table('project_overview_progress')\
                .select('skipped_until')\
                .eq('user_id', user_id)\
                .order('created_at', desc=True)\
                .limit(1)\
                .execute()
            
            if result.data and result.data[0].get('skipped_until'):
                return datetime.fromisoformat(result.data[0]['skipped_until'].replace('Z', '+00:00'))
            
            return None
            
        except Exception as e:
            logger.error(f"Error checking project skip: {e}")
            return None

    # === CONVERSATION ROUTING ===
    
    async def _route_conversation(self, user_id: str, message: str, thread_id: str,
                                 creativity_done: bool, project_done: bool, needs_intro: bool,
                                 creativity_skip: Optional[datetime], project_skip: Optional[datetime]) -> str:
        """Route conversation with complete logic - intro is mandatory"""
        
        # Handle intro flow first - MANDATORY until complete
        if needs_intro:
            return await self._handle_intro_flow(user_id, message, thread_id)
        
        # Check if creativity skip expired
        if creativity_skip and datetime.now(timezone.utc) >= creativity_skip:
            if not creativity_done:
                return "Hi! I noticed it's been a day since we last talked about the creativity test. Would you like to try it now, or would you prefer to skip it again and focus on other things?"
        
        # Check if in active skip period for creativity 
        if creativity_skip and datetime.now(timezone.utc) < creativity_skip:
            if not creativity_done:
                # In skip period - route to project or general chat
                if not project_done:
                    return await self._handle_project_flow(user_id, message, thread_id)
                else:
                    return await self._handle_general_conversation(user_id, message, thread_id)
        
        # Normal routing after intro complete
        if not creativity_done:
            return await self._handle_creativity_flow(user_id, message, thread_id)
        elif not project_done:
            return await self._handle_project_flow(user_id, message, thread_id)
        else:
            return await self._handle_general_conversation(user_id, message, thread_id)

    # === FLOW HANDLERS (SIMPLIFIED) ===
    
    async def _handle_creativity_flow(self, user_id: str, message: str, thread_id: str) -> str:
        """Handle creativity test flow with complete implementation"""
        try:
            # Get current progress
            progress = await self._get_creativity_progress(user_id)
            current_question = progress.get('current_question', 1)
            responses = progress.get('responses', {})
            
            # Check if user wants to skip
            if self._wants_to_skip(message):
                await self._set_creativity_skip(user_id, 24)
                return "No worries! I've noted that you'd prefer to skip the creativity test for now. We can always come back to it later.\n\nLet's focus on your project instead. What creative project are you working on or thinking about starting?"
            
            # Process response to current question
            if current_question > 1 and current_question <= len(self.CREATIVITY_QUESTIONS):
                letter_response = self._extract_letter_response(message)
                if letter_response:
                    responses[f"q{current_question-1}"] = letter_response
                    await self._save_creativity_progress(user_id, current_question, responses)
                    current_question += 1
            
            # Check if test complete
            if current_question > len(self.CREATIVITY_QUESTIONS):
                return await self._complete_creativity_test(user_id, responses)
            
            # Present next question
            if current_question <= len(self.CREATIVITY_QUESTIONS):
                question_data = self.CREATIVITY_QUESTIONS[current_question - 1]
                response = f"Question {current_question} of {len(self.CREATIVITY_QUESTIONS)}: {question_data['question']}\n\n"
                for letter, option in question_data['options'].items():
                    response += f"{letter}. {option}\n"
                response += f"\nJust respond with {', '.join(question_data['options'].keys())}."
                return response
            
            # Start the test
            return "I'll be guiding you through a creativity archetype assessment that will help us understand your unique creative approach and strengths.\n\nQuestion 1 of 12: When starting a new creative project, what excites you most?\n\nA. The unknown possibilities and what I might discover\nB. Creating something beautiful that moves people\nC. Solving a problem in a completely new way\nD. Bringing together different perspectives or ideas\nE. The process of making something real with my hands\nF. Sharing a meaningful story or message\n\nJust respond with A, B, C, D, E, or F."
            
        except Exception as e:
            logger.error(f"Error in creativity flow: {e}")
            return "Let's start with the creativity test. I'll guide you through understanding your creative archetype."

    async def _handle_project_flow(self, user_id: str, message: str, thread_id: str) -> str:
        """Handle project overview flow with complete implementation"""
        try:
            # Get current progress
            progress = await self._get_project_progress(user_id)
            current_topic = progress.get('current_topic', 1)
            collected_data = progress.get('data', {})
            
            # Check if user wants to skip
            if self._wants_to_skip(message):
                await self._set_project_skip(user_id, 24)
                return "No problem! I've noted that you'd prefer to skip the project planning for now. We can always come back to it when you're ready.\n\nI'm here to help with whatever you'd like to discuss about your creative work."
            
            # Process response and move to next topic
            if current_topic > 1 and current_topic <= len(self.PROJECT_TOPICS):
                # Save response for current topic
                topic_key = f"topic_{current_topic-1}"
                collected_data[topic_key] = message.strip()
                await self._save_project_progress(user_id, current_topic, collected_data)
                current_topic += 1
            
            # Check if project overview complete
            if current_topic > len(self.PROJECT_TOPICS):
                return await self._complete_project_overview(user_id, collected_data)
            
            # Present next topic
            if current_topic <= len(self.PROJECT_TOPICS):
                topic_data = self.PROJECT_TOPICS[current_topic - 1]
                response = f"Great! That's topic {current_topic-1} of {len(self.PROJECT_TOPICS)} complete.\n\n"
                response += f"Now let's move to topic {current_topic} of {len(self.PROJECT_TOPICS)}: {topic_data['title']}\n\n"
                response += f"{topic_data['description']}\n\n"
                response += f"Key question: {topic_data['key_questions'][0]}"
                return response
            
            # Start project overview
            topic_data = self.PROJECT_TOPICS[0]
            return f"Perfect! Let's start the project planning conversation.\n\nTopic 1 of {len(self.PROJECT_TOPICS)}: {topic_data['title']}\n\n{topic_data['description']}\n\n{topic_data['key_questions'][0]}"
            
        except Exception as e:
            logger.error(f"Error in project flow: {e}")
            return "Let's talk about your project. What creative project are you working on?"

    async def _handle_general_conversation(self, user_id: str, message: str, thread_id: str) -> str:
        """Handle general conversation after flows complete"""
        try:
            # Use LLM router for general conversation
            router = get_router()
            memory = SimpleMemory(self.supabase, user_id)
            context = await memory.get_context(thread_id)
            
            # Build conversation history
            messages = []
            if context.get('summaries'):
                messages.append({"role": "system", "content": f"Previous conversation context:\n{context['summaries']}"})
            
            for msg in context.get('messages', [])[-10:]:  # Last 10 messages
                messages.append({"role": msg.get('role', 'user'), "content": msg.get('content', '')})
            
            messages.append({"role": "user", "content": message})
            
            # Get response
            response = await router.chat_completion(
                messages=messages,
                system_message="You are Hai, a supportive creative partner. The user has completed their creativity test and project overview. Help them with their creative project, providing guidance, accountability, and encouragement."
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error in general conversation: {e}")
            return "I'm here to help with your creative project. What would you like to work on today?"

    # === MISSING HELPER METHODS ===
    
    def _wants_to_skip(self, message: str) -> bool:
        """Detect skip requests - improved to avoid false positives"""
        skip_phrases = [
            "skip this", "skip for now", "not now", "not today", "maybe later", 
            "not interested", "pass on this", "don't want to", "not ready"
        ]
        message_lower = message.lower().strip()
        
        # Only trigger on explicit skip phrases, not general conversation
        return any(phrase in message_lower for phrase in skip_phrases)
    
    def _extract_letter_response(self, message: str) -> Optional[str]:
        """Extract A-F letter response from message"""
        message = message.strip().upper()
        if message in ['A', 'B', 'C', 'D', 'E', 'F']:
            return message
        
        # Look for letter in longer responses
        import re
        match = re.search(r'\b([A-F])\b', message)
        if match:
            return match.group(1)
        
        return None
    
    async def _get_creativity_progress(self, user_id: str) -> dict:
        """Get current creativity test progress"""
        try:
            result = self.supabase.table('creativity_test_progress')\
                .select('*')\
                .eq('user_id', user_id)\
                .order('created_at', desc=True)\
                .limit(1)\
                .execute()
            
            if result.data:
                data = result.data[0]
                return {
                    'current_question': data.get('flow_step', 1),
                    'responses': data.get('current_responses', {}),
                    'completion_percentage': data.get('completion_percentage', 0.0),
                    'is_completed': data.get('is_completed', False)
                }
            
            return {'current_question': 1, 'responses': {}, 'completion_percentage': 0.0, 'is_completed': False}
            
        except Exception as e:
            logger.error(f"Error getting creativity progress: {e}")
            return {'current_question': 1, 'responses': {}, 'completion_percentage': 0.0, 'is_completed': False}
    
    async def _save_creativity_progress(self, user_id: str, current_question: int, responses: dict):
        """Save creativity test progress"""
        try:
            progress_data = {
                'user_id': user_id,
                'flow_step': current_question,
                'current_responses': responses,
                'completion_percentage': (len(responses) / len(self.CREATIVITY_QUESTIONS)) * 100,
                'is_completed': len(responses) >= len(self.CREATIVITY_QUESTIONS)
            }
            
            # Check if record exists
            result = self.supabase.table('creativity_test_progress')\
                .select('id')\
                .eq('user_id', user_id)\
                .execute()
            
            if result.data:
                # Update existing
                self.supabase.table('creativity_test_progress')\
                    .update(progress_data)\
                    .eq('user_id', user_id)\
                    .execute()
            else:
                # Insert new
                self.supabase.table('creativity_test_progress')\
                    .insert(progress_data)\
                    .execute()
                    
        except Exception as e:
            logger.error(f"Error saving creativity progress: {e}")
    
    async def _complete_creativity_test(self, user_id: str, responses: dict) -> str:
        """Complete creativity test and determine archetype"""
        try:
            # Calculate archetype scores
            archetype_scores = {}
            for archetype in self.CREATIVITY_ARCHETYPES.keys():
                archetype_scores[archetype] = 0
            
            # Score responses
            for response_key, letter in responses.items():
                question_idx = int(response_key[1:]) - 1
                if question_idx < len(self.CREATIVITY_QUESTIONS):
                    question = self.CREATIVITY_QUESTIONS[question_idx]
                    if letter in question['scoring']:
                        archetype = question['scoring'][letter]
                        archetype_scores[archetype] += 1
            
            # Find primary archetype
            primary_archetype = max(archetype_scores, key=archetype_scores.get)
            primary_score = archetype_scores[primary_archetype]
            
            # Find secondary archetype
            remaining_scores = {k: v for k, v in archetype_scores.items() if k != primary_archetype}
            secondary_archetype = max(remaining_scores, key=remaining_scores.get) if remaining_scores else None
            secondary_score = remaining_scores[secondary_archetype] if secondary_archetype else 0
            
            # Save to creator_creativity_profiles
            profile_data = {
                'user_id': user_id,
                'archetype': primary_archetype,
                'archetype_score': primary_score,
                'secondary_archetype': secondary_archetype,
                'secondary_score': secondary_score,
                'test_responses': responses,
                'date_taken': datetime.now(timezone.utc).isoformat()
            }
            
            self.supabase.table('creator_creativity_profiles')\
                .insert(profile_data)\
                .execute()
            
            # Mark test as complete
            await self._save_creativity_progress(user_id, len(self.CREATIVITY_QUESTIONS) + 1, responses)
            
            # Generate response
            archetype_info = self.CREATIVITY_ARCHETYPES[primary_archetype]
            response = f"🎉 Fantastic! Your creativity test is complete.\n\n"
            response += f"**Your Primary Creative Archetype: {primary_archetype}**\n\n"
            response += f"{archetype_info['description']}\n\n"
            response += f"Key traits: {', '.join(archetype_info['traits'])}\n\n"
            
            if secondary_archetype and secondary_score > 0:
                secondary_info = self.CREATIVITY_ARCHETYPES[secondary_archetype]
                response += f"**Secondary Archetype: {secondary_archetype}** (score: {secondary_score})\n"
                response += f"{secondary_info['description']}\n\n"
            
            response += f"Now that I understand your creative style, let's talk about your specific project! What creative project are you working on or thinking about starting?"
            
            return response
            
        except Exception as e:
            logger.error(f"Error completing creativity test: {e}")
            return "Great job completing the creativity test! Now let's talk about your project. What creative project are you working on?"
    
    async def _get_project_progress(self, user_id: str) -> dict:
        """Get current project overview progress"""
        try:
            result = self.supabase.table('project_overview_progress')\
                .select('*')\
                .eq('user_id', user_id)\
                .order('created_at', desc=True)\
                .limit(1)\
                .execute()
            
            if result.data:
                data = result.data[0]
                return {
                    'current_topic': data.get('flow_step', 1),
                    'data': data.get('current_data', {}),
                    'completion_percentage': data.get('completion_percentage', 0.0),
                    'is_completed': data.get('is_completed', False)
                }
            
            return {'current_topic': 1, 'data': {}, 'completion_percentage': 0.0, 'is_completed': False}
            
        except Exception as e:
            logger.error(f"Error getting project progress: {e}")
            return {'current_topic': 1, 'data': {}, 'completion_percentage': 0.0, 'is_completed': False}
    
    async def _save_project_progress(self, user_id: str, current_topic: int, collected_data: dict):
        """Save project overview progress"""
        try:
            progress_data = {
                'user_id': user_id,
                'flow_step': current_topic,
                'current_data': collected_data,
                'completion_percentage': (len(collected_data) / len(self.PROJECT_TOPICS)) * 100,
                'is_completed': len(collected_data) >= len(self.PROJECT_TOPICS)
            }
            
            # Check if record exists
            result = self.supabase.table('project_overview_progress')\
                .select('id')\
                .eq('user_id', user_id)\
                .execute()
            
            if result.data:
                # Update existing
                self.supabase.table('project_overview_progress')\
                    .update(progress_data)\
                    .eq('user_id', user_id)\
                    .execute()
            else:
                # Insert new
                self.supabase.table('project_overview_progress')\
                    .insert(progress_data)\
                    .execute()
                    
        except Exception as e:
            logger.error(f"Error saving project progress: {e}")
    
    async def _complete_project_overview(self, user_id: str, collected_data: dict) -> str:
        """Complete project overview and save to database"""
        try:
            # Extract structured data
            project_data = {
                'user_id': user_id,
                'project_name': self._extract_project_name(collected_data),
                'project_type': self._extract_project_type(collected_data),
                'description': collected_data.get('topic_1', ''),
                'current_phase': 'planning',
                'goals': self._extract_goals(collected_data),
                'challenges': self._extract_challenges(collected_data),
                'success_metrics': self._extract_success_metrics(collected_data),
                'creation_date': datetime.now(timezone.utc).isoformat(),
                'last_updated': datetime.now(timezone.utc).isoformat()
            }
            
            # Save to project_overview table
            self.supabase.table('project_overview')\
                .insert(project_data)\
                .execute()
            
            # Mark as complete
            await self._save_project_progress(user_id, len(self.PROJECT_TOPICS) + 1, collected_data)
            
            response = f"🎉 Excellent! We've completed your comprehensive project overview.\n\n"
            response += f"**Project: {project_data['project_name']}**\n"
            response += f"Type: {project_data['project_type']}\n\n"
            response += f"I now have a complete understanding of your project vision, goals, challenges, and next steps. "
            response += f"I'm here to support you as you bring this project to life!\n\n"
            response += f"What would you like to work on first?"
            
            return response
            
        except Exception as e:
            logger.error(f"Error completing project overview: {e}")
            return "Great job completing the project overview! I'm here to help you move forward with your creative project."
    
    def _extract_project_name(self, data: dict) -> str:
        """Extract project name from collected data"""
        # Look for project name in first topic or anywhere in responses
        for value in data.values():
            if isinstance(value, str) and len(value) > 5 and len(value) < 100:
                # Simple heuristic for project name
                return value.split('.')[0].split('\n')[0].strip()
        return "Creative Project"
    
    def _extract_project_type(self, data: dict) -> str:
        """Extract project type from collected data"""
        topic_2 = data.get('topic_2', '').lower()
        types = ['book', 'film', 'podcast', 'app', 'website', 'course', 'art', 'music', 'video', 'blog']
        for project_type in types:
            if project_type in topic_2:
                return project_type.title()
        return "Creative Project"
    
    def _extract_goals(self, data: dict) -> list:
        """Extract goals from collected data"""
        goals_text = data.get('topic_4', '')
        if goals_text:
            return [goals_text.strip()]
        return ["Complete creative project"]
    
    def _extract_challenges(self, data: dict) -> list:
        """Extract challenges from collected data"""
        challenges_text = data.get('topic_5', '')
        if challenges_text:
            return [challenges_text.strip()]
        return ["Time management"]
    
    def _extract_success_metrics(self, data: dict) -> dict:
        """Extract success metrics from collected data"""
        metrics_text = data.get('topic_4', '')
        return {"primary_goal": metrics_text.strip() if metrics_text else "Project completion"}
    
    async def _set_creativity_skip(self, user_id: str, hours: int = 24):
        """Set creativity skip period"""
        try:
            skip_until = datetime.now(timezone.utc) + timedelta(hours=hours)
            
            # Upsert into creativity_test_progress table
            result = self.supabase.table('creativity_test_progress')\
                .select('id')\
                .eq('user_id', user_id)\
                .execute()
            
            if result.data:
                # Update existing record
                self.supabase.table('creativity_test_progress')\
                    .update({'skipped_until': skip_until.isoformat()})\
                    .eq('user_id', user_id)\
                    .execute()
            else:
                # Insert new record
                self.supabase.table('creativity_test_progress')\
                    .insert({
                        'user_id': user_id,
                        'flow_step': 1,
                        'current_responses': {},
                        'completion_percentage': 0.0,
                        'is_completed': False,
                        'skipped_until': skip_until.isoformat()
                    })\
                    .execute()
                
            logger.info(f"Set creativity skip for user {user_id} until {skip_until}")
            
        except Exception as e:
            logger.error(f"Error setting creativity skip: {e}")
    
    async def _set_project_skip(self, user_id: str, hours: int = 24):
        """Set project planning skip for specified hours"""
        try:
            skip_until = datetime.now(timezone.utc) + timedelta(hours=hours)
            
            # Check if record exists
            result = self.supabase.table('project_overview_progress')\
                .select('id')\
                .eq('user_id', user_id)\
                .execute()
            
            update_data = {
                'skipped_until': skip_until.isoformat(),
                'updated_at': datetime.now(timezone.utc).isoformat()
            }
            
            if result.data:
                # Update existing record
                self.supabase.table('project_overview_progress')\
                    .update(update_data)\
                    .eq('user_id', user_id)\
                    .execute()
            else:
                # Create new record
                self.supabase.table('project_overview_progress')\
                    .insert({
                        'user_id': user_id,
                        'flow_step': 1,
                        'collected_data': {},
                        'completion_percentage': 0.0,
                        'is_completed': False,
                        **update_data
                    })\
                    .execute()
                    
            logger.info(f"Set project skip for user {user_id} until {skip_until}")
            
        except Exception as e:
            logger.error(f"Error setting project skip: {e}")

    async def _mark_intro_complete(self, user_id: str):
        """Mark intro as complete when user transitions to specific flows"""
        try:
            # Update the intro_progress table
            result = self.supabase.table('creativity_test_progress')\
                .select('id')\
                .eq('user_id', user_id)\
                .execute()
            
            if result.data:
                # Update existing record  
                self.supabase.table('creativity_test_progress')\
                    .update({'has_seen_intro': True})\
                    .eq('user_id', user_id)\
                    .execute()
            else:
                # Create new record marking intro as complete
                self.supabase.table('creativity_test_progress')\
                    .insert({
                        'user_id': user_id,
                        'flow_step': 1,
                        'current_responses': {},
                        'completion_percentage': 0.0,
                        'is_completed': False,
                        'has_seen_intro': True
                    })\
                    .execute()
            
            logger.info(f"Marked intro as complete for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error marking intro as complete: {e}")


# === MAIN ENTRY POINT ===

async def process_chat_message(user_id: str, message: str, thread_id: str, supabase_client: Client) -> str:
    """Main entry point - replaces entire AgentManager system"""
    handler = SimpleChatHandler(supabase_client)
    return await handler.process_message(user_id, message, thread_id) 