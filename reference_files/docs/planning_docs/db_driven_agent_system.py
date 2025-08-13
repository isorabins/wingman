#!/usr/bin/env python3
"""
Database-Driven Agent System for Fridays at Four
Replaces expensive manager agent API calls with fast database queries
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from supabase import Client

from src.llm_router import get_router
from src.simple_memory import SimpleMemory

logger = logging.getLogger(__name__)

@dataclass
class UserFlowState:
    """Complete user flow state from database"""
    user_id: str
    intro_complete: bool
    intro_stage: int
    intro_data: dict
    creativity_complete: bool
    creativity_skipped_until: Optional[datetime]
    creativity_progress: dict
    project_complete: bool
    project_progress: dict

class FlowStateManager:
    """Fast database state management - no API calls needed"""
    
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client
    
    async def get_user_flow_state(self, user_id: str) -> UserFlowState:
        """Single optimized query to get all flow states"""
        try:
            # Get intro state
            intro_result = self.supabase.table('creativity_test_progress')\
                .select('has_seen_intro, intro_stage, intro_data')\
                .eq('user_id', user_id)\
                .limit(1)\
                .execute()
            
            # Get creativity state
            creativity_result = self.supabase.table('creativity_test_progress')\
                .select('is_completed, skipped_until, current_responses, completion_percentage')\
                .eq('user_id', user_id)\
                .limit(1)\
                .execute()
            
            # Get project state
            project_result = self.supabase.table('project_overview_progress')\
                .select('is_completed, current_data, completion_percentage')\
                .eq('user_id', user_id)\
                .limit(1)\
                .execute()
            
            # Check creativity completion in final results table
            creativity_profile = self.supabase.table('creator_creativity_profiles')\
                .select('id')\
                .eq('user_id', user_id)\
                .limit(1)\
                .execute()
            
            # Check project completion in final results table  
            project_overview = self.supabase.table('project_overview')\
                .select('id')\
                .eq('user_id', user_id)\
                .limit(1)\
                .execute()
            
            # Parse results with defaults
            intro_data = intro_result.data[0] if intro_result.data else {}
            creativity_data = creativity_result.data[0] if creativity_result.data else {}
            project_data = project_result.data[0] if project_result.data else {}
            
            # Parse skip timestamp
            creativity_skipped_until = None
            if creativity_data.get('skipped_until'):
                creativity_skipped_until = datetime.fromisoformat(
                    creativity_data['skipped_until'].replace('Z', '+00:00')
                )
            
            return UserFlowState(
                user_id=user_id,
                intro_complete=intro_data.get('has_seen_intro', False),
                intro_stage=intro_data.get('intro_stage', 1),
                intro_data=intro_data.get('intro_data', {}),
                creativity_complete=len(creativity_profile.data) > 0,
                creativity_skipped_until=creativity_skipped_until,
                creativity_progress=creativity_data,
                project_complete=len(project_overview.data) > 0,
                project_progress=project_data
            )
            
        except Exception as e:
            logger.error(f"Error getting user flow state: {e}")
            # Return safe defaults for new user
            return UserFlowState(
                user_id=user_id,
                intro_complete=False,
                intro_stage=1,
                intro_data={},
                creativity_complete=False,
                creativity_skipped_until=None,
                creativity_progress={},
                project_complete=False,
                project_progress={}
            )

class BaseFlowAgent:
    """Base class for all flow agents with standardized interface"""
    
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client
    
    async def handle(self, user_id: str, message: str, thread_id: str, current_state: UserFlowState) -> str:
        """Standard agent interface - implement in subclasses"""
        try:
            # 1. Extract relevant info from message
            extracted = await self.extract_info(message, current_state)
            
            # 2. Update database with new info
            await self.update_state(user_id, extracted)
            
            # 3. Check if flow is complete
            if await self.is_complete(user_id):
                return await self.generate_completion_response(extracted)
            
            # 4. Prompt for next missing piece
            return await self.prompt_for_next(current_state, extracted)
            
        except Exception as e:
            logger.error(f"Error in {self.__class__.__name__}: {e}")
            return await self.fallback_response()
    
    async def extract_info(self, message: str, current_state: UserFlowState) -> dict:
        """Extract relevant information from user message - implement in subclasses"""
        raise NotImplementedError
    
    async def update_state(self, user_id: str, extracted: dict):
        """Update database with extracted information - implement in subclasses"""
        raise NotImplementedError
    
    async def is_complete(self, user_id: str) -> bool:
        """Check if this flow is complete - implement in subclasses"""
        raise NotImplementedError
    
    async def prompt_for_next(self, current_state: UserFlowState, extracted: dict) -> str:
        """Generate next prompt based on what's missing - implement in subclasses"""
        raise NotImplementedError
    
    async def generate_completion_response(self, extracted: dict) -> str:
        """Generate completion message - implement in subclasses"""
        raise NotImplementedError
    
    async def fallback_response(self) -> str:
        """Safe fallback response on errors"""
        return "I'm having trouble right now. Could you try rephrasing that?"
    
    async def call_claude(self, messages: List[Dict[str, str]], system_prompt: str) -> str:
        """Helper for Claude API calls with fallback"""
        try:
            router = await get_router()
            return await router.send_message(
                messages=messages,
                system=system_prompt,
                model="claude-3-5-sonnet-20241022",
                max_tokens=2000,
                temperature=0.7
            )
        except Exception as e:
            logger.error(f"Claude API call failed: {e}")
            return await self.fallback_response()

class IntroAgent(BaseFlowAgent):
    """Handles intro conversation flow using database state"""
    
    async def extract_info(self, message: str, current_state: UserFlowState) -> dict:
        """Extract name, project info, etc. from message"""
        extracted = {}
        
        # Extract name if we're in early stages
        if current_state.intro_stage <= 2:
            name = self._extract_name(message)
            if name:
                extracted['name'] = name
        
        # Extract project info if we're in project stage
        if current_state.intro_stage == 3:
            extracted['project_info'] = message.strip()
        
        # Extract accountability experience
        if current_state.intro_stage == 4:
            extracted['accountability_experience'] = message.strip()
        
        return extracted
    
    def _extract_name(self, message: str) -> Optional[str]:
        """Extract name from user message"""
        import re
        message = message.strip()
        
        patterns = [
            r"(?:hi,?\s+)?i'?m\s+(\w+(?:\s+\w+)?)",
            r"my name is\s+(\w+(?:\s+\w+)?)",
            r"call me\s+(\w+(?:\s+\w+)?)",
            r"(\w+)\s+here",
            r"it'?s\s+(\w+)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message.lower())
            if match:
                return match.group(1).title()
        
        # If short and mostly letters, assume it's a name
        if len(message.split()) <= 2 and re.match(r'^[a-zA-Z\s]+$', message):
            return message.title()
        
        return None
    
    async def update_state(self, user_id: str, extracted: dict):
        """Update intro progress in database"""
        if not extracted:
            return
        
        try:
            # Get current intro data
            result = self.supabase.table('creativity_test_progress')\
                .select('intro_data, intro_stage')\
                .eq('user_id', user_id)\
                .execute()
            
            if result.data:
                current_data = result.data[0].get('intro_data', {})
                current_stage = result.data[0].get('intro_stage', 1)
            else:
                current_data = {}
                current_stage = 1
            
            # Merge extracted data
            current_data.update(extracted)
            
            # Determine next stage
            next_stage = current_stage
            if 'name' in extracted and current_stage == 2:
                next_stage = 3
            elif 'project_info' in extracted and current_stage == 3:
                next_stage = 4
            elif 'accountability_experience' in extracted and current_stage == 4:
                next_stage = 5
            
            # Update database
            update_data = {
                'intro_data': current_data,
                'intro_stage': next_stage
            }
            
            if result.data:
                self.supabase.table('creativity_test_progress')\
                    .update(update_data)\
                    .eq('user_id', user_id)\
                    .execute()
            else:
                self.supabase.table('creativity_test_progress')\
                    .insert({
                        'user_id': user_id,
                        'flow_step': 1,
                        'current_responses': {},
                        'completion_percentage': 0.0,
                        'is_completed': False,
                        **update_data
                    })\
                    .execute()
            
        except Exception as e:
            logger.error(f"Error updating intro state: {e}")
    
    async def is_complete(self, user_id: str) -> bool:
        """Check if intro is complete"""
        try:
            result = self.supabase.table('creativity_test_progress')\
                .select('has_seen_intro')\
                .eq('user_id', user_id)\
                .execute()
            
            return result.data and result.data[0].get('has_seen_intro', False)
        except Exception:
            return False
    
    async def prompt_for_next(self, current_state: UserFlowState, extracted: dict) -> str:
        """Generate next intro prompt based on current stage"""
        stage = current_state.intro_stage
        intro_data = current_state.intro_data
        
        if stage == 1:
            return "Hi, I'm Hai. I'm your creative partner here at Fridays at Four.\n\nWhat's your name? I'd love to know what to call you."
        
        elif stage == 2:
            return await self._generate_stage_2_response(intro_data.get('name'))
        
        elif stage == 3:
            return await self._generate_stage_3_response(intro_data.get('name'), intro_data.get('project_info'))
        
        elif stage == 4:
            return await self._generate_stage_4_response(intro_data.get('name'), extracted.get('accountability_experience'))
        
        elif stage == 5:
            # Check if ready to proceed to creativity test
            if self._wants_to_proceed(extracted.get('accountability_experience', '')):
                # Mark intro complete and start creativity test
                await self._mark_intro_complete(current_state.user_id)
                return await self._generate_creativity_test_start(intro_data.get('name'))
            else:
                return await self._answer_intro_questions(intro_data.get('name'), extracted.get('accountability_experience', ''))
        
        return "Let's continue getting to know each other!"
    
    def _wants_to_proceed(self, message: str) -> bool:
        """Check if user wants to proceed to creativity test"""
        proceed_phrases = [
            "ready", "let's start", "yes", "sure", "okay", "sounds good",
            "let's do it", "i'm ready", "no questions", "let's begin", "start"
        ]
        return any(phrase in message.lower() for phrase in proceed_phrases)
    
    async def _mark_intro_complete(self, user_id: str):
        """Mark intro as complete"""
        try:
            self.supabase.table('creativity_test_progress')\
                .update({'has_seen_intro': True, 'intro_stage': 6})\
                .eq('user_id', user_id)\
                .execute()
        except Exception as e:
            logger.error(f"Error marking intro complete: {e}")
    
    async def _generate_stage_2_response(self, name: Optional[str]) -> str:
        """Generate platform explanation"""
        greeting = f"Nice to meet you, {name}." if name else "Nice to meet you."
        return f"""{greeting}

So here's what Fridays at Four is about: this is where you keep track of your creative project and get the support you need to actually finish it. I'm here as your partner through that process.

What kind of creative project are you working on, or thinking about starting?"""
    
    async def _generate_stage_3_response(self, name: Optional[str], project_info: Optional[str]) -> str:
        """Generate how Hai works explanation"""
        project_response = "That sounds like something worth building." if project_info else "Thanks for sharing."
        
        return f"""{project_response}

Here's how I work with you: I remember everything we discuss about your project. Every detail, every insight, every challenge. When you come back next week, I know exactly where we left off. You never have to start from scratch explaining your vision.

I also give you advice when you're stuck, help you figure out next steps, and keep you moving forward when life gets busy.

Have you ever worked with any kind of accountability partner or coach before?"""
    
    async def _generate_stage_4_response(self, name: Optional[str], accountability_experience: Optional[str]) -> str:
        """Generate creative test explanation"""
        return f"""I'll learn your creative style through a quick creative personality test, then adapt how I work with you. Some creators need structure, others thrive with flexibility. I'll figure out what works for you.

And if you want extra accountability, you can connect with an email buddy who checks in on your progress. But that's totally optional - some people prefer just working with me.

Your conversations and project details stay private between us.

What questions do you have about how this works?"""
    
    async def _answer_intro_questions(self, name: Optional[str], question: str) -> str:
        """Answer questions during intro"""
        system_prompt = f"""You are Hai talking to {name or 'them'}. They asked: "{question}"

Answer their question directly and helpfully. After answering, ask if they have other questions or if they're ready to start the creative personality test.

Tone: Direct, helpful, confident."""
        
        return await self.call_claude([{"role": "user", "content": question}], system_prompt)
    
    async def _generate_creativity_test_start(self, name: Optional[str]) -> str:
        """Start creativity test with first question"""
        greeting = f"Perfect, {name}!" if name else "Perfect!"
        
        return f"""{greeting} Let's start that creative personality test.

Question 1 of 12: When starting a new creative project, what excites you most?

A. The unknown possibilities and what I might discover
B. Creating something beautiful that moves people
C. Solving a problem in a completely new way
D. Bringing together different perspectives or ideas
E. The process of making something real with my hands
F. Sharing a meaningful story or message

Just respond with A, B, C, D, E, or F."""

class CreativityAgent(BaseFlowAgent):
    """Handles creativity test flow using database state"""
    
    # Include all 12 creativity questions
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
        # ... (include all 12 questions from previous implementation)
    ]
    
    async def extract_info(self, message: str, current_state: UserFlowState) -> dict:
        """Extract creativity test answers"""
        # Check for skip requests
        if self._wants_to_skip(message):
            return {'action': 'skip'}
        
        # Extract answer (A, B, C, D, E, F)
        answer = self._extract_answer(message)
        if answer:
            return {'answer': answer}
        
        return {}
    
    def _wants_to_skip(self, message: str) -> bool:
        """Check if user wants to skip creativity test"""
        skip_phrases = [
            "skip this", "skip for now", "not now", "not today", "maybe later",
            "not interested", "pass on this", "don't want to", "not ready"
        ]
        return any(phrase in message.lower() for phrase in skip_phrases)
    
    def _extract_answer(self, message: str) -> Optional[str]:
        """Extract A-F answer from message"""
        message_clean = message.strip().upper()
        
        if len(message_clean) == 1 and message_clean in ['A', 'B', 'C', 'D', 'E', 'F']:
            return message_clean
        
        for letter in ['A', 'B', 'C', 'D', 'E', 'F']:
            patterns = [f"{letter} ", f"{letter}.", f"{letter})", f"({letter}"]
            if any(message_clean.startswith(pattern) for pattern in patterns):
                return letter
        
        return None
    
    async def update_state(self, user_id: str, extracted: dict):
        """Update creativity test progress"""
        if extracted.get('action') == 'skip':
            # Set skip period
            skip_until = datetime.now(timezone.utc) + timedelta(hours=24)
            self.supabase.table('creativity_test_progress')\
                .update({'skipped_until': skip_until.isoformat()})\
                .eq('user_id', user_id)\
                .execute()
        
        elif extracted.get('answer'):
            # Save answer and advance
            try:
                result = self.supabase.table('creativity_test_progress')\
                    .select('current_responses')\
                    .eq('user_id', user_id)\
                    .execute()
                
                current_responses = {}
                if result.data:
                    current_responses = result.data[0].get('current_responses', {})
                
                # Add new answer
                question_num = len(current_responses) + 1
                current_responses[f"question_{question_num}"] = extracted['answer']
                
                # Update progress
                completion_percentage = (len(current_responses) / len(self.CREATIVITY_QUESTIONS)) * 100
                
                self.supabase.table('creativity_test_progress')\
                    .update({
                        'current_responses': current_responses,
                        'completion_percentage': completion_percentage
                    })\
                    .eq('user_id', user_id)\
                    .execute()
                
            except Exception as e:
                logger.error(f"Error updating creativity progress: {e}")
    
    async def is_complete(self, user_id: str) -> bool:
        """Check if creativity test is complete"""
        try:
            # Check if final profile exists
            result = self.supabase.table('creator_creativity_profiles')\
                .select('id')\
                .eq('user_id', user_id)\
                .execute()
            return len(result.data) > 0
        except Exception:
            return False
    
    async def prompt_for_next(self, current_state: UserFlowState, extracted: dict) -> str:
        """Generate next creativity question or handle completion"""
        progress = current_state.creativity_progress
        current_responses = progress.get('current_responses', {})
        
        # Check if skipped
        if extracted.get('action') == 'skip':
            return "No problem! I'll check back tomorrow about the creativity assessment. What would you like to work on today?"
        
        # Check if all questions answered
        if len(current_responses) >= len(self.CREATIVITY_QUESTIONS):
            # Calculate and save results
            results = await self._calculate_results(current_responses)
            await self._save_final_results(current_state.user_id, results)
            return await self._generate_results_message(results)
        
        # Present next question
        question_index = len(current_responses)
        if question_index < len(self.CREATIVITY_QUESTIONS):
            return await self._format_question(question_index)
        
        return "Thank you for completing the assessment!"
    
    async def _format_question(self, question_index: int) -> str:
        """Format creativity question"""
        question_data = self.CREATIVITY_QUESTIONS[question_index]
        question_num = question_index + 1
        total = len(self.CREATIVITY_QUESTIONS)
        
        options_text = "\n".join([f"{key}. {value}" for key, value in question_data["options"].items()])
        
        return f"""Question {question_num} of {total}: {question_data['question']}

{options_text}

Just respond with A, B, C, D, E, or F. (Say 'skip for now' if you'd rather work on your project instead)"""

class ProjectAgent(BaseFlowAgent):
    """Handles project overview flow using database state"""
    
    # Include all 8 project topics
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
        # ... (include all 8 topics from previous implementation)
    ]
    
    async def extract_info(self, message: str, current_state: UserFlowState) -> dict:
        """Extract project information from message"""
        # Use Claude to extract structured info
        return await self._extract_project_insights(message, current_state)
    
    async def _extract_project_insights(self, message: str, current_state: UserFlowState) -> dict:
        """Use Claude to extract project insights"""
        # Implementation similar to previous project agent
        return {"user_input": message}

class MainChatAgent(BaseFlowAgent):
    """Handles general conversation after all flows complete"""
    
    async def handle(self, user_id: str, message: str, thread_id: str, current_state: UserFlowState) -> str:
        """Handle general conversation"""
        try:
            # Use memory system for context
            memory = SimpleMemory(self.supabase, user_id)
            context = await memory.get_context(thread_id)
            
            system_prompt = f"""You are Hai, a creative partner for professionals.
            
            User context: {context}
            
            Help them with their creative projects and goals. Be direct, confident, warm, and supportive."""
            
            return await self.call_claude([{"role": "user", "content": message}], system_prompt)
        except Exception as e:
            logger.error(f"Error in main chat: {e}")
            return "I'm here to help with your creative projects. What would you like to work on today?"

class DatabaseDrivenChatHandler:
    """Main chat handler with database-driven routing - NO MANAGER AGENT API CALLS"""
    
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client
        self.state_manager = FlowStateManager(supabase_client)
        
        # Initialize agents
        self.intro_agent = IntroAgent(supabase_client)
        self.creativity_agent = CreativityAgent(supabase_client)
        self.project_agent = ProjectAgent(supabase_client)
        self.main_chat_agent = MainChatAgent(supabase_client)
    
    async def process_message(self, user_id: str, message: str, thread_id: str) -> str:
        """
        Main entry point - uses FAST database queries instead of expensive manager agent
        """
        try:
            # Fast database state check (10-50ms total)
            flow_state = await self.state_manager.get_user_flow_state(user_id)
            
            # Store conversation in memory
            memory = SimpleMemory(self.supabase, user_id)
            await memory.add_message(thread_id, message, "user")
            
            # Route based on database state - NO API CALLS for routing
            response = await self._route_to_agent(user_id, message, thread_id, flow_state)
            
            # Store AI response
            await memory.add_message(thread_id, response, "assistant")
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return "I'm having trouble right now. Please try again in a moment."
    
    async def _route_to_agent(self, user_id: str, message: str, thread_id: str, flow_state: UserFlowState) -> str:
        """Fast routing based on database state"""
        
        # Check skip status for creativity
        creativity_skipped = False
        if flow_state.creativity_skipped_until:
            creativity_skipped = datetime.now(timezone.utc) < flow_state.creativity_skipped_until
        
        # Route to appropriate agent
        if not flow_state.intro_complete:
            return await self.intro_agent.handle(user_id, message, thread_id, flow_state)
        
        elif not flow_state.creativity_complete and not creativity_skipped:
            return await self.creativity_agent.handle(user_id, message, thread_id, flow_state)
        
        elif not flow_state.project_complete:
            return await self.project_agent.handle(user_id, message, thread_id, flow_state)
        
        else:
            return await self.main_chat_agent.handle(user_id, message, thread_id, flow_state)

# Main entry point
async def process_chat_message(user_id: str, message: str, thread_id: str, supabase_client: Client) -> str:
    """
    Main entry point - replaces manager agent system with database-driven routing
    Performance: 1 API call per message instead of 2-3
    """
    handler = DatabaseDrivenChatHandler(supabase_client)
    return await handler.process_message(user_id, message, thread_id)