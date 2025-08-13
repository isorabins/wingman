#!/usr/bin/env python3
"""
Project Overview Agent for Fridays at Four

Implements the 8-topic onboarding flow using Claude:
- Project planning conversation across 8 structured topics
- Progress tracking with "Topic X of 8" format
- Results storage in project_overview table
"""

import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

class ProjectOverviewAgent(BaseAgent):
    """Agent for conducting project overview onboarding"""
    
    # 8 structured topics for project planning
    TOPICS = [
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
    
    def __init__(self, supabase_client, user_id: str):
        super().__init__(supabase_client, user_id, "project_overview")
        
    async def process_message(self, thread_id: str, user_message: str) -> str:
        """Process user message and advance project overview flow"""
        try:
            # Start session if needed
            await self.start_session(thread_id)
            
            # Get current progress
            progress = await self.get_progress()
            current_step = progress.get('flow_step', 1)
            current_data = progress.get('current_data', {})
            topic_progress = progress.get('topic_progress', {})
            
            # Store user input if we're in conversation
            if current_step > 1:
                await self._process_user_input(user_message, current_step, current_data, topic_progress)
            
            # Determine response based on current step
            if current_step == 1:
                # Welcome and start conversation
                response = await self._generate_welcome_message()
                await self.save_progress({
                    'flow_step': 2,
                    'current_data': current_data,
                    'topic_progress': topic_progress,
                    'completion_percentage': 0.0
                })
            elif current_step <= len(self.TOPICS) + 1:
                # Handle topic conversations
                topic_index = current_step - 2
                if topic_index < len(self.TOPICS):
                    topic = self.TOPICS[topic_index]
                    
                    # Check if topic is complete
                    topic_key = f"topic_{topic['topic_number']}"
                    if self._is_topic_complete(topic, topic_progress.get(topic_key, {})):
                        # Move to next topic
                        if topic_index + 1 < len(self.TOPICS):
                            next_topic = self.TOPICS[topic_index + 1]
                            response = await self._generate_topic_transition(topic, next_topic)
                            await self.save_progress({
                                'flow_step': current_step + 1,
                                'current_data': current_data,
                                'topic_progress': topic_progress,
                                'completion_percentage': ((topic_index + 1) / len(self.TOPICS)) * 100
                            })
                        else:
                            # All topics complete, generate overview
                            response = await self._generate_completion_response(current_data)
                            await self._save_final_overview(current_data)
                            await self.end_session(thread_id)
                    else:
                        # Continue current topic conversation
                        response = await self._generate_topic_response(topic, current_data, topic_progress.get(topic_key, {}))
                else:
                    # Shouldn't reach here, but handle gracefully
                    response = "Thank you for sharing your project vision with me! Let me help you create a comprehensive overview."
            else:
                # Flow is complete
                response = await self._generate_completion_response(current_data)
            
            await self.store_conversation(thread_id, user_message, response)
            return response
            
        except Exception as e:
            logger.error(f"Error processing project overview message: {e}")
            return "I'm sorry, there was an issue with our conversation. Let me try again to help you plan your project."
    
    async def _process_user_input(self, user_message: str, current_step: int, current_data: Dict, topic_progress: Dict):
        """Process and store user input for current topic"""
        try:
            # Determine current topic
            topic_index = current_step - 2
            if topic_index >= 0 and topic_index < len(self.TOPICS):
                topic = self.TOPICS[topic_index]
                topic_key = f"topic_{topic['topic_number']}"
                
                # Extract insights from user message using Claude
                insights = await self._extract_insights(user_message, topic)
                
                # Update topic progress
                if topic_key not in topic_progress:
                    topic_progress[topic_key] = {}
                
                topic_progress[topic_key].update(insights)
                
                # Update current_data with extracted information
                current_data.update(insights)
                
                # Save progress
                await self.save_progress({
                    'flow_step': current_step,
                    'current_data': current_data,
                    'topic_progress': topic_progress,
                    'completion_percentage': (topic_index / len(self.TOPICS)) * 100
                })
                
        except Exception as e:
            logger.error(f"Error processing user input: {e}")
    
    async def _extract_insights(self, user_message: str, topic: Dict) -> Dict[str, Any]:
        """Use Claude to extract structured insights from user message"""
        try:
            prompt = f"""
            You are analyzing user input for project planning. The current topic is:
            
            Topic: {topic['title']}
            Description: {topic['description']}
            Key areas to explore: {', '.join(topic['completion_indicators'])}
            
            User message: "{user_message}"
            
            Extract relevant information and return a JSON object with keys matching the completion indicators:
            {', '.join(topic['completion_indicators'])}
            
            Only include keys where you found relevant information. Values should be concise summaries of what the user shared.
            Return ONLY valid JSON, no additional text.
            """
            
            messages = [{"role": "user", "content": user_message}]
            response = await self.call_claude_with_router(messages, prompt)
            
            # Try to parse JSON response
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                # If JSON parsing fails, create a simple summary
                return {"user_input": user_message[:200]}
                
        except Exception as e:
            logger.error(f"Error extracting insights: {e}")
            return {"user_input": user_message[:200]}
    
    def _is_topic_complete(self, topic: Dict, topic_data: Dict) -> bool:
        """Check if a topic has sufficient information to move on"""
        # A topic is complete if we have information for at least 2 of 3 completion indicators
        # or if there's substantial conversation (more than 100 characters of content)
        indicators_met = sum(1 for indicator in topic['completion_indicators'] if indicator in topic_data)
        total_content = sum(len(str(value)) for value in topic_data.values())
        
        return indicators_met >= 2 or total_content > 100
    
    async def _generate_welcome_message(self) -> str:
        """Generate welcome message for project overview"""
        prompt = """
        You are Hai, a warm and supportive AI partner for creative professionals. You're about to guide someone through a comprehensive project planning conversation.

        Create a welcoming message that:
        1. Explains you'll be exploring their project together through 8 key topics
        2. Mentions this will take about 10-15 minutes of thoughtful conversation
        3. Emphasizes this is collaborative planning, not an interview
        4. Sets an encouraging, professional tone
        5. Asks them to start by sharing what project they'd like to work on

        Keep it warm but professional. Remember you're helping someone turn their creative vision into reality.
        """
        
        messages = [{"role": "user", "content": "I'd like to plan my creative project."}]
        return await self.call_claude_with_router(messages, prompt)
    
    async def _generate_topic_response(self, topic: Dict, current_data: Dict, topic_data: Dict) -> str:
        """Generate response for continuing conversation on current topic"""
        topic_num = topic['topic_number']
        total_topics = len(self.TOPICS)
        
        # Gather context about what's been discussed
        discussed_points = list(topic_data.keys())
        remaining_points = [point for point in topic['completion_indicators'] if point not in discussed_points]
        
        prompt = f"""
        You are Hai, having a collaborative planning conversation about a creative project.
        
        Current topic: {topic['title']} (Topic {topic_num} of {total_topics})
        Description: {topic['description']}
        
        Key areas to explore: {', '.join(topic['completion_indicators'])}
        Already discussed: {', '.join(discussed_points) if discussed_points else 'None yet'}
        Still to explore: {', '.join(remaining_points) if remaining_points else 'All key areas covered'}
        
        Context from previous conversation: {json.dumps(current_data, indent=2)}
        
        Generate a thoughtful follow-up question or comment that:
        1. Builds on what they've shared
        2. Explores remaining areas naturally (don't force it)
        3. Uses "Topic {topic_num} of {total_topics}" format
        4. Feels conversational, not like an interview
        5. Shows you're listening and understanding their vision
        
        If all key areas are covered, you can explore deeper or validate your understanding before moving on.
        """
        
        messages = [{"role": "user", "content": f"Continue exploring {topic['title']}"}]
        return await self.call_claude_with_router(messages, prompt)
    
    async def _generate_topic_transition(self, completed_topic: Dict, next_topic: Dict) -> str:
        """Generate transition message between topics"""
        next_num = next_topic['topic_number']
        total_topics = len(self.TOPICS)
        
        prompt = f"""
        You are Hai, transitioning between topics in a project planning conversation.
        
        Just completed: {completed_topic['title']}
        Moving to: {next_topic['title']} (Topic {next_num} of {total_topics})
        Next topic description: {next_topic['description']}
        
        Create a smooth transition that:
        1. Briefly acknowledges what you learned from the previous topic
        2. Naturally introduces the next topic
        3. Uses "Topic {next_num} of {total_topics}" format
        4. Maintains conversational flow
        5. Asks an engaging opening question for the new topic
        
        Keep it concise but thoughtful. Show connection between topics when relevant.
        """
        
        messages = [{"role": "user", "content": f"Transition to {next_topic['title']}"}]
        return await self.call_claude_with_router(messages, prompt)
    
    async def _generate_completion_response(self, project_data: Dict) -> str:
        """Generate completion message with project summary"""
        prompt = f"""
        You are Hai, completing a comprehensive project planning conversation.
        
        Project data gathered: {json.dumps(project_data, indent=2)}
        
        Create a thoughtful completion message that:
        1. Celebrates the comprehensive planning they've done
        2. Summarizes the key insights about their project
        3. Highlights the clarity they've gained
        4. Mentions that this overview will help guide their creative journey
        5. Ends on an encouraging note about their project's potential
        
        Make it feel like a meaningful conclusion to a productive planning session.
        Be specific about their project where possible, showing you understand their vision.
        """
        
        messages = [{"role": "user", "content": "Complete the project planning session"}]
        return await self.call_claude_with_router(messages, prompt)
    
    async def _save_final_overview(self, project_data: Dict):
        """Save final project overview to database"""
        try:
            # Extract key components from project_data
            project_name = project_data.get('project_concept', 'Untitled Project')
            project_type = project_data.get('project_type', 'Creative Project')
            
            # Build goals array from various goal-related fields
            goals = []
            for key, value in project_data.items():
                if 'goal' in key.lower() or 'success' in key.lower() or 'vision' in key.lower():
                    if isinstance(value, str) and value.strip():
                        goals.append(value)
            
            # Build challenges array
            challenges = []
            for key, value in project_data.items():
                if 'challenge' in key.lower() or 'obstacle' in key.lower() or 'barrier' in key.lower():
                    if isinstance(value, str) and value.strip():
                        challenges.append(value)
            
            # Build success metrics
            success_metrics = {}
            for key, value in project_data.items():
                if 'metric' in key.lower() or 'measure' in key.lower() or 'timeline' in key.lower():
                    success_metrics[key] = value
            
            overview_data = {
                'user_id': self.user_id,
                'project_name': project_name,
                'project_type': project_type,
                'description': project_data.get('project_concept', ''),
                'current_phase': 'Planning',
                'goals': goals,
                'challenges': challenges,
                'success_metrics': success_metrics,
                'creation_date': datetime.now(timezone.utc).isoformat()
            }
            
            # Check if overview already exists
            existing = self.supabase.table('project_overview')\
                .select('id')\
                .eq('user_id', self.user_id)\
                .execute()
            
            if existing.data:
                # Update existing overview
                self.supabase.table('project_overview')\
                    .update(overview_data)\
                    .eq('user_id', self.user_id)\
                    .execute()
            else:
                # Create new overview
                self.supabase.table('project_overview')\
                    .insert(overview_data)\
                    .execute()
            
            # Mark progress as completed
            await self.save_progress({
                'flow_step': len(self.TOPICS) + 2,
                'current_data': project_data,
                'completion_percentage': 100.0,
                'is_completed': True
            })
            
            logger.info(f"Saved project overview for user {self.user_id}: {project_name}")
            
        except Exception as e:
            logger.error(f"Error saving project overview: {e}")
            raise
    
    async def get_progress(self) -> Dict[str, Any]:
        """Get current progress for project overview"""
        try:
            result = self.supabase.table('project_overview_progress')\
                .select('*')\
                .eq('user_id', self.user_id)\
                .order('created_at', desc=True)\
                .limit(1)\
                .execute()
            
            if result.data:
                return result.data[0]
            else:
                return {
                    'flow_step': 1, 
                    'current_data': {}, 
                    'topic_progress': {},
                    'completion_percentage': 0.0, 
                    'is_completed': False
                }
                
        except Exception as e:
            logger.error(f"Error getting project overview progress: {e}")
            return {
                'flow_step': 1, 
                'current_data': {}, 
                'topic_progress': {},
                'completion_percentage': 0.0, 
                'is_completed': False
            }
    
    async def save_progress(self, progress_data: Dict[str, Any]):
        """Save progress to project_overview_progress table"""
        try:
            # Check if progress record exists
            existing = self.supabase.table('project_overview_progress')\
                .select('id')\
                .eq('user_id', self.user_id)\
                .execute()
            
            save_data = {
                'user_id': self.user_id,
                'flow_step': progress_data.get('flow_step', 1),
                'current_data': progress_data.get('current_data', {}),
                'flow_state': progress_data.get('flow_state', {}),
                'topic_progress': progress_data.get('topic_progress', {}),
                'completion_percentage': progress_data.get('completion_percentage', 0.0),
                'is_completed': progress_data.get('is_completed', False)
            }
            
            if existing.data:
                # Update existing record
                self.supabase.table('project_overview_progress')\
                    .update(save_data)\
                    .eq('user_id', self.user_id)\
                    .execute()
            else:
                # Create new record
                self.supabase.table('project_overview_progress')\
                    .insert(save_data)\
                    .execute()
                    
        except Exception as e:
            logger.error(f"Error saving project overview progress: {e}")
    
    async def is_flow_complete(self) -> bool:
        """Check if project overview flow is complete"""
        progress = await self.get_progress()
        return progress.get('is_completed', False) 