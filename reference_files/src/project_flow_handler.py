#!/usr/bin/env python3
"""
Project Overview Flow Handler - Structured 8-topic conversation
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class ProjectFlowHandler:
    """Handles structured project overview flow"""
    
    TOPICS = [
        {
            "number": 1,
            "name": "Project Vision & Core Concept",
            "key_questions": [
                "What's the core concept or story you want to bring to life?",
                "What drew you to this particular project?",
                "What feelings or impact do you want your audience to have?"
            ],
            "data_keys": ["project_concept", "personal_connection", "audience_impact"]
        },
        {
            "number": 2,
            "name": "Project Type & Format",
            "key_questions": [
                "What type of project is this? (book, film, podcast, app, etc.)",
                "What format or medium feels right for your vision?",
                "Have you considered alternative formats?"
            ],
            "data_keys": ["project_type", "format_decision", "format_reasoning"]
        },
        {
            "number": 3,
            "name": "Target Audience & Community",
            "key_questions": [
                "Who is your ideal audience for this project?",
                "What problems or needs does your project address for them?",
                "How do you want to connect with and serve this community?"
            ],
            "data_keys": ["target_audience", "audience_needs", "community_connection"]
        },
        {
            "number": 4,
            "name": "Personal Goals & Success Vision",
            "key_questions": [
                "What are your personal goals for this project?",
                "How will you know when this project is successful?",
                "What would achieving this mean for your creative journey?"
            ],
            "data_keys": ["personal_goals", "success_metrics", "creative_significance"]
        },
        {
            "number": 5,
            "name": "Current Challenges & Obstacles",
            "key_questions": [
                "What's the biggest challenge you're facing right now?",
                "What obstacles have you encountered so far?",
                "What support or resources do you feel you need most?"
            ],
            "data_keys": ["main_challenges", "encountered_obstacles", "needed_support"]
        },
        {
            "number": 6,
            "name": "Timeline & Project Scope",
            "key_questions": [
                "What's your ideal timeline for completing this project?",
                "How do you want to break this down into manageable phases?",
                "What's the minimum viable version vs. your dream vision?"
            ],
            "data_keys": ["target_timeline", "project_phases", "scope_definition"]
        },
        {
            "number": 7,
            "name": "Resources & Support System",
            "key_questions": [
                "What skills, tools, or resources do you already have?",
                "What do you need to learn or acquire?",
                "Who could be part of your support system for this project?"
            ],
            "data_keys": ["existing_resources", "needed_resources", "support_network"]
        },
        {
            "number": 8,
            "name": "Next Steps & Commitment",
            "key_questions": [
                "What's the very first step you want to take?",
                "How do you want to maintain momentum on this project?",
                "What kind of ongoing support would be most helpful?"
            ],
            "data_keys": ["first_steps", "momentum_plan", "ongoing_support"]
        }
    ]
    
    def __init__(self, supabase, user_id: str):
        self.supabase = supabase
        self.user_id = user_id
    
    async def handle_message(self, message: str, flow_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process project overview message"""
        try:
            current_topic = flow_data.get('current_topic', 1)
            project_data = flow_data.get('data', {})
            topic_progress = flow_data.get('topic_progress', {})
            
            # Process user input for current topic
            if current_topic > 1:
                topic_key = f"topic_{current_topic - 1}"
                insights = await self._extract_topic_insights(
                    message, 
                    self.TOPICS[current_topic - 2]
                )
                
                # Update topic progress
                if topic_key not in topic_progress:
                    topic_progress[topic_key] = {}
                topic_progress[topic_key].update(insights)
                
                # Update overall project data
                project_data.update(insights)
                
                # Save progress
                await self._save_progress(current_topic, project_data, topic_progress)
            
            # Check if all topics complete
            if current_topic > 8:
                # Save final project overview
                await self._save_final_project(project_data)
                
                return {
                    'response': self._generate_completion_message(project_data),
                    'flow_complete': True,
                    'next_flow': 'main_chat'
                }
            
            # Get current topic
            if current_topic <= 8:
                topic = self.TOPICS[current_topic - 1]
                response = await self._generate_topic_response(
                    topic, 
                    current_topic,
                    project_data
                )
                
                # Update progress for next topic
                await self._save_progress(current_topic + 1, project_data, topic_progress)
                
                return {
                    'response': response,
                    'flow_complete': False,
                    'progress': self._calculate_progress(current_topic, 8)
                }
            
            return {
                'response': "Let's continue planning your project.",
                'flow_complete': False
            }
            
        except Exception as e:
            logger.error(f"Error in project flow: {e}")
            return {
                'response': "Let's continue planning your project. What were you saying?",
                'flow_complete': False
            }
    
    async def _extract_topic_insights(self, message: str, topic: Dict) -> Dict[str, Any]:
        """Extract structured data from user message"""
        from src.llm_router import get_router
        
        # Use Claude to extract structured data
        system_prompt = f"""Extract relevant information from the user's message for project planning.

Current topic: {topic['name']}
Expected information: {', '.join(topic['data_keys'])}

Return a JSON object with keys matching the data_keys where you find relevant information.
Only include keys where you found clear information. Be concise but complete.
"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message}
        ]
        
        router = await get_router()
        response = await router.send_message(
            messages=messages,
            model="claude-3-5-sonnet-20241022",
            max_tokens=300,
            temperature=0.3
        )
        
        # Try to parse JSON response
        try:
            import json
            return json.loads(response)
        except:
            # Fallback: store raw message
            return {"user_input": message[:500]}
    
    async def _generate_topic_response(self, topic: Dict, topic_num: int, project_data: Dict) -> str:
        """Generate response for current topic"""
        from src.llm_router import get_router
        
        # Get user's creativity archetype if available
        archetype = await self._get_user_archetype()
        
        system_prompt = f"""You are Hai, guiding a creative professional through project planning.

Current topic: {topic['name']} (Topic {topic_num} of 8)
Key areas to explore: {', '.join(topic['key_questions'])}

User's creative archetype: {archetype or 'Unknown'}
Project data so far: {self._summarize_project_data(project_data)}

Generate a warm, conversational response that:
1. Acknowledges what they've shared so far (if applicable)
2. Introduces the current topic naturally
3. Asks 1-2 focused questions from the key areas
4. Includes "Topic {topic_num} of 8" for progress clarity
5. Keeps the tone supportive and collaborative

Be concise but thoughtful. This is a conversation, not an interview.
"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Let's discuss {topic['name']}"}
        ]
        
        router = await get_router()
        response = await router.send_message(
            messages=messages,
            model="claude-3-5-sonnet-20241022",
            max_tokens=400,
            temperature=0.7
        )
        
        return response
    
    def _calculate_progress(self, current: int, total: int) -> Dict[str, Any]:
        """Calculate progress metrics"""
        return {
            'current_step': current,
            'total_steps': total,
            'completion_percentage': ((current - 1) / total) * 100,
            'display_text': f"Topic {current} of {total}"
        }
    
    def _summarize_project_data(self, project_data: Dict) -> str:
        """Create brief summary of project data for context"""
        if not project_data:
            return "No project details yet"
        
        summary_parts = []
        if 'project_concept' in project_data:
            summary_parts.append(f"Concept: {project_data['project_concept'][:100]}")
        if 'project_type' in project_data:
            summary_parts.append(f"Type: {project_data['project_type']}")
        if 'target_audience' in project_data:
            summary_parts.append(f"Audience: {project_data['target_audience'][:50]}")
        
        return " | ".join(summary_parts) if summary_parts else "Initial project details shared"
    
    async def _get_user_archetype(self) -> Optional[str]:
        """Get user's creativity archetype if available"""
        try:
            result = self.supabase.table('creator_creativity_profiles')\
                .select('archetype')\
                .eq('user_id', self.user_id)\
                .execute()
            
            if result.data:
                return result.data[0].get('archetype')
            return None
            
        except Exception as e:
            logger.error(f"Error getting user archetype: {e}")
            return None
    
    async def _save_progress(self, next_topic: int, project_data: Dict, topic_progress: Dict):
        """Save project planning progress"""
        try:
            progress_data = {
                'flow_step': next_topic,
                'current_data': project_data,
                'topic_progress': topic_progress,
                'completion_percentage': ((next_topic - 1) / 8) * 100,
                'is_completed': False
            }
            
            # Check if record exists
            existing = self.supabase.table('project_overview_progress')\
                .select('id')\
                .eq('user_id', self.user_id)\
                .execute()
            
            if existing.data:
                self.supabase.table('project_overview_progress')\
                    .update(progress_data)\
                    .eq('user_id', self.user_id)\
                    .execute()
            else:
                progress_data['user_id'] = self.user_id
                self.supabase.table('project_overview_progress')\
                    .insert(progress_data)\
                    .execute()
                    
        except Exception as e:
            logger.error(f"Error saving project progress: {e}")
    
    async def _save_final_project(self, project_data: Dict):
        """Save final project overview"""
        try:
            # Extract key fields for project_overview table
            overview_data = {
                'user_id': self.user_id,
                'project_name': project_data.get('project_concept', 'Untitled Project')[:100],
                'project_type': project_data.get('project_type', 'Creative Project'),
                'description': project_data.get('project_concept', ''),
                'current_phase': 'Planning',
                'goals': self._extract_goals(project_data),
                'challenges': self._extract_challenges(project_data),
                'success_metrics': {
                    'timeline': project_data.get('target_timeline', 'Not specified'),
                    'success_definition': project_data.get('success_metrics', 'Not specified')
                },
                'creation_date': datetime.now(timezone.utc).isoformat()
            }
            
            # Check if project exists
            existing = self.supabase.table('project_overview')\
                .select('id')\
                .eq('user_id', self.user_id)\
                .execute()
            
            if existing.data:
                self.supabase.table('project_overview')\
                    .update(overview_data)\
                    .eq('user_id', self.user_id)\
                    .execute()
            else:
                self.supabase.table('project_overview')\
                    .insert(overview_data)\
                    .execute()
            
            # Mark progress as complete
            self.supabase.table('project_overview_progress')\
                .update({
                    'is_completed': True,
                    'completion_percentage': 100.0
                })\
                .eq('user_id', self.user_id)\
                .execute()
                
        except Exception as e:
            logger.error(f"Error saving final project: {e}")
    
    def _extract_goals(self, project_data: Dict) -> List[Dict]:
        """Extract goals from project data"""
        goals = []
        
        if 'personal_goals' in project_data:
            goals.append({
                'type': 'personal',
                'description': project_data['personal_goals']
            })
        
        if 'audience_impact' in project_data:
            goals.append({
                'type': 'impact',
                'description': project_data['audience_impact']
            })
        
        if 'creative_significance' in project_data:
            goals.append({
                'type': 'creative',
                'description': project_data['creative_significance']
            })
        
        return goals
    
    def _extract_challenges(self, project_data: Dict) -> List[Dict]:
        """Extract challenges from project data"""
        challenges = []
        
        if 'main_challenges' in project_data:
            challenges.append({
                'type': 'current',
                'description': project_data['main_challenges']
            })
        
        if 'encountered_obstacles' in project_data:
            challenges.append({
                'type': 'past',
                'description': project_data['encountered_obstacles']
            })
        
        if 'needed_support' in project_data:
            challenges.append({
                'type': 'resources',
                'description': project_data['needed_support']
            })
        
        return challenges
    
    def _generate_completion_message(self, project_data: Dict) -> str:
        """Generate project planning completion message"""
        project_name = project_data.get('project_concept', 'your project')[:50]
        
        return f"""🎉 **Excellent! We've mapped out your complete project plan!**

I now have a clear understanding of {project_name} and what you want to achieve. Here's what makes me excited about your project:

- Your vision is clear and compelling
- You've identified both the challenges and the resources you need
- You have a realistic timeline and concrete next steps

I'll use everything we've discussed to provide personalized support as you bring this project to life. Remember, I'll remember all these details, so you never have to explain your project from scratch again.

Ready to take that first step? Let's make this happen! 🚀

What would you like to focus on first?"""
    
    def get_start_message(self) -> str:
        """Get project planning start message"""
        return """Perfect! Now let's create a comprehensive plan for your creative project. 

I'll guide you through 8 key topics that will help us understand your vision, goals, and what you need to succeed. This usually takes about 10-15 minutes.

**Topic 1 of 8: Project Vision & Core Concept**

Let's start with the heart of it all - what's the creative project you want to bring to life? Tell me about your core concept or idea.""" 