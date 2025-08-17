#!/usr/bin/env python3
"""
Wingman Profile Agent for WingmanMatch

Implements the 4-topic dating confidence goals flow using Claude:
- Dating confidence conversation across 4 structured topics
- Progress tracking with "Topic X of 4" format  
- Results storage in dating_goals table
- Connell Barrett coaching methodology integration
"""

import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

class WingmanProfileAgent(BaseAgent):
    """Agent for conducting dating confidence goals onboarding"""
    
    # 4 structured topics for dating confidence coaching
    TOPICS = [
        {
            "topic_number": 1,
            "title": "Dating Confidence Goals & Targets",
            "description": "Understanding your dating confidence building objectives",
            "key_questions": [
                "What specific areas of dating confidence do you want to improve?",
                "What situations make you feel most nervous when meeting someone new?",
                "What would success look like for your dating confidence?"
            ],
            "completion_indicators": ["confidence_targets", "anxiety_triggers", "success_definition"]
        },
        {
            "topic_number": 2,
            "title": "Past Attempts & Learning",
            "description": "Understanding your dating experience and previous efforts", 
            "key_questions": [
                "What have you tried before to build dating confidence?",
                "What worked well and what didn't work for you?",
                "What patterns do you notice in your dating experiences?"
            ],
            "completion_indicators": ["past_attempts", "successful_strategies", "identified_patterns"]
        },
        {
            "topic_number": 3,
            "title": "Triggers & Comfort Zones",
            "description": "Identifying specific situations and comfort levels",
            "key_questions": [
                "What situations trigger your dating anxiety most?",
                "Where do you feel most comfortable meeting new people?",
                "What venues or activities feel approachable to you?"
            ],
            "completion_indicators": ["anxiety_triggers", "comfort_venues", "preferred_activities"]
        },
        {
            "topic_number": 4,
            "title": "Support & Accountability Goals",
            "description": "Planning your wingman partnership approach",
            "key_questions": [
                "What kind of support would help you most in building confidence?",
                "How do you want your wingman to hold you accountable?",
                "What would be a good first challenge to try together?"
            ],
            "completion_indicators": ["support_needs", "accountability_style", "first_challenges"]
        }
    ]
    
    def __init__(self, supabase_client, user_id: str):
        super().__init__(supabase_client, user_id, "dating_goals")
        
    async def process_message(self, thread_id: str, user_message: str) -> str:
        """Process user message and advance dating goals flow"""
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
                            await self._save_final_goals(current_data)
                            await self.end_session(thread_id)
                    else:
                        # Continue current topic conversation
                        response = await self._generate_topic_response(topic, current_data, topic_progress.get(topic_key, {}))
                else:
                    # Shouldn't reach here, but handle gracefully
                    response = "Thank you for sharing your dating confidence goals with me! Let me help you create a comprehensive plan."
            else:
                # Flow is complete
                response = await self._generate_completion_response(current_data)
            
            await self.store_conversation(thread_id, user_message, response)
            return response
            
        except Exception as e:
            logger.error(f"Error processing dating goals message: {e}")
            return "I'm sorry, there was an issue with our conversation. Let me try again to help you with your dating confidence goals."
    
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
            You are Connell, a dating confidence coach analyzing user input for dating goals planning. The current topic is:
            
            Topic: {topic['title']}
            Description: {topic['description']}
            Key areas to explore: {', '.join(topic['completion_indicators'])}
            
            User message: "{user_message}"
            
            Extract relevant information about dating confidence goals and return a JSON object with keys matching the completion indicators:
            {', '.join(topic['completion_indicators'])}
            
            Only include keys where you found relevant information. Values should be concise summaries of what the user shared about their dating confidence.
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
        """Generate welcome message for dating goals"""
        prompt = """
        You are Connell, a dating confidence coach using authentic, respectful dating approaches. You're about to guide someone through a comprehensive dating confidence goals conversation.

        Create a welcoming message that:
        1. Explains you'll be exploring their dating confidence goals together through 4 key topics
        2. Mentions this will take about 8-10 minutes of thoughtful conversation
        3. Emphasizes this is collaborative coaching, not an interview
        4. Sets an encouraging, supportive tone focused on authentic confidence building
        5. Asks them to start by sharing what dating confidence goals they'd like to work on

        Keep it warm but professional. Remember you're helping someone build genuine dating confidence using respectful, authentic approaches. Avoid any pickup artist language or manipulative tactics.
        """
        
        messages = [{"role": "user", "content": "I'd like to work on my dating confidence goals."}]
        return await self.call_claude_with_router(messages, prompt)
    
    async def _generate_topic_response(self, topic: Dict, current_data: Dict, topic_data: Dict) -> str:
        """Generate response for continuing conversation on current topic"""
        topic_num = topic['topic_number']
        total_topics = len(self.TOPICS)
        
        # Gather context about what's been discussed
        discussed_points = list(topic_data.keys())
        remaining_points = [point for point in topic['completion_indicators'] if point not in discussed_points]
        
        prompt = f"""
        You are Connell, having a collaborative dating confidence coaching conversation.
        
        Current topic: {topic['title']} (Topic {topic_num} of {total_topics})
        Description: {topic['description']}
        
        Key areas to explore: {', '.join(topic['completion_indicators'])}
        Already discussed: {', '.join(discussed_points) if discussed_points else 'None yet'}
        Still to explore: {', '.join(remaining_points) if remaining_points else 'All key areas covered'}
        
        Context from previous conversation: {json.dumps(current_data, indent=2)}
        
        Generate a thoughtful follow-up question or comment that:
        1. Builds on what they've shared about their dating confidence
        2. Explores remaining areas naturally (don't force it)
        3. Uses "Topic {topic_num} of {total_topics}" format
        4. Feels conversational and supportive, not like an interview
        5. Shows you're listening and understanding their dating confidence journey
        6. Uses authentic, respectful dating confidence approaches (no pickup artist tactics)
        
        If all key areas are covered, you can explore deeper or validate your understanding before moving on.
        """
        
        messages = [{"role": "user", "content": f"Continue exploring {topic['title']}"}]
        return await self.call_claude_with_router(messages, prompt)
    
    async def _generate_topic_transition(self, completed_topic: Dict, next_topic: Dict) -> str:
        """Generate transition message between topics"""
        next_num = next_topic['topic_number']
        total_topics = len(self.TOPICS)
        
        prompt = f"""
        You are Connell, transitioning between topics in a dating confidence goals conversation.
        
        Just completed: {completed_topic['title']}
        Moving to: {next_topic['title']} (Topic {next_num} of {total_topics})
        Next topic description: {next_topic['description']}
        
        Create a smooth transition that:
        1. Briefly acknowledges what you learned about their dating confidence from the previous topic
        2. Naturally introduces the next topic
        3. Uses "Topic {next_num} of {total_topics}" format
        4. Maintains conversational flow
        5. Asks an engaging opening question for the new topic
        6. Stays focused on authentic confidence building approaches
        
        Keep it concise but thoughtful. Show connection between topics when relevant.
        """
        
        messages = [{"role": "user", "content": f"Transition to {next_topic['title']}"}]
        return await self.call_claude_with_router(messages, prompt)
    
    async def _generate_completion_response(self, goals_data: Dict) -> str:
        """Generate completion message with dating goals summary"""
        prompt = f"""
        You are Connell, completing a comprehensive dating confidence goals conversation.
        
        Dating goals data gathered: {json.dumps(goals_data, indent=2)}
        
        Create a thoughtful completion message that:
        1. Celebrates the comprehensive goals planning they've done
        2. Summarizes the key insights about their dating confidence journey
        3. Highlights the clarity they've gained about their goals and triggers
        4. Mentions that this goals profile will help guide their confidence building
        5. Ends on an encouraging note about their potential for authentic connection
        6. References how their wingman partner will help them achieve these goals
        
        Make it feel like a meaningful conclusion to a productive coaching session.
        Be specific about their goals where possible, showing you understand their confidence journey.
        Focus on authentic, respectful dating approaches.
        """
        
        messages = [{"role": "user", "content": "Complete the dating confidence goals session"}]
        return await self.call_claude_with_router(messages, prompt)
    
    async def _save_final_goals(self, goals_data: Dict):
        """Save final dating goals to database"""
        try:
            # Extract key components from goals_data
            confidence_targets = goals_data.get('confidence_targets', 'General confidence building')
            
            # Build goals text from various goal-related fields
            goals_text_parts = []
            for key, value in goals_data.items():
                if 'goal' in key.lower() or 'target' in key.lower() or 'success' in key.lower():
                    if isinstance(value, str) and value.strip():
                        goals_text_parts.append(value)
            
            goals_text = '; '.join(goals_text_parts) if goals_text_parts else confidence_targets
            
            # Build preferred venues array
            preferred_venues = []
            for key, value in goals_data.items():
                if 'venue' in key.lower() or 'activity' in key.lower() or 'comfort' in key.lower():
                    if isinstance(value, str) and value.strip():
                        # Split venue mentions and clean them
                        venues = [v.strip() for v in value.replace(',', ';').split(';') if v.strip()]
                        preferred_venues.extend(venues)
            
            # Determine comfort level from anxiety triggers
            comfort_level = 'moderate'  # default
            anxiety_data = str(goals_data.get('anxiety_triggers', '')).lower()
            if any(word in anxiety_data for word in ['very', 'extremely', 'terrified', 'panic']):
                comfort_level = 'low'
            elif any(word in anxiety_data for word in ['little', 'minimal', 'comfortable', 'easy']):
                comfort_level = 'high'
            
            goals_record = {
                'user_id': self.user_id,
                'goals': goals_text,
                'preferred_venues': preferred_venues[:10],  # Limit to 10 venues
                'comfort_level': comfort_level,
                'goals_data': goals_data,  # Store full JSON data
                'created_at': datetime.now(timezone.utc).isoformat()
            }
            
            # Check if goals already exist
            existing = self.supabase.table('dating_goals')\
                .select('id')\
                .eq('user_id', self.user_id)\
                .execute()
            
            if existing.data:
                # Update existing goals
                goals_record['updated_at'] = datetime.now(timezone.utc).isoformat()
                self.supabase.table('dating_goals')\
                    .update(goals_record)\
                    .eq('user_id', self.user_id)\
                    .execute()
            else:
                # Create new goals
                self.supabase.table('dating_goals')\
                    .insert(goals_record)\
                    .execute()
            
            # Mark progress as completed
            await self.save_progress({
                'flow_step': len(self.TOPICS) + 2,
                'current_data': goals_data,
                'completion_percentage': 100.0,
                'is_completed': True
            })
            
            logger.info(f"Saved dating goals for user {self.user_id}: {confidence_targets}")
            
        except Exception as e:
            logger.error(f"Error saving dating goals: {e}")
            raise
    
    async def get_progress(self) -> Dict[str, Any]:
        """Get current progress for dating goals"""
        try:
            result = self.supabase.table('dating_goals_progress')\
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
            logger.error(f"Error getting dating goals progress: {e}")
            return {
                'flow_step': 1, 
                'current_data': {}, 
                'topic_progress': {},
                'completion_percentage': 0.0, 
                'is_completed': False
            }
    
    async def save_progress(self, progress_data: Dict[str, Any]):
        """Save progress to dating_goals_progress table"""
        try:
            # Check if progress record exists
            existing = self.supabase.table('dating_goals_progress')\
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
                self.supabase.table('dating_goals_progress')\
                    .update(save_data)\
                    .eq('user_id', self.user_id)\
                    .execute()
            else:
                # Create new record
                self.supabase.table('dating_goals_progress')\
                    .insert(save_data)\
                    .execute()
                    
        except Exception as e:
            logger.error(f"Error saving dating goals progress: {e}")
    
    async def is_flow_complete(self) -> bool:
        """Check if dating goals flow is complete"""
        progress = await self.get_progress()
        return progress.get('is_completed', False)