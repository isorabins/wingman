#!/usr/bin/env python3
"""
Agent Manager for Fridays at Four

Handles routing between different Claude agents:
- CreativityTestAgent for creativity assessments
- ProjectOverviewAgent for project planning
- Determines which agent should handle each request
"""

import logging
from typing import Dict, Any, Optional, Tuple, List
from supabase import Client

from .creativity_agent import CreativityTestAgent
from .project_overview_agent import ProjectOverviewAgent

logger = logging.getLogger(__name__)

class AgentManager:
    """Manages multiple Claude agents and routes requests appropriately"""
    
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client
        self._agents = {}  # Cache agents per user
        
    def _get_agent(self, user_id: str, agent_type: str):
        """Get or create agent instance for user"""
        agent_key = f"{user_id}_{agent_type}"
        
        if agent_key not in self._agents:
            if agent_type == "creativity_test":
                self._agents[agent_key] = CreativityTestAgent(self.supabase, user_id)
            elif agent_type == "project_overview":
                self._agents[agent_key] = ProjectOverviewAgent(self.supabase, user_id)
            else:
                raise ValueError(f"Unknown agent type: {agent_type}")
        
        return self._agents[agent_key]
    
    async def determine_agent_needed(self, user_id: str, user_message: str, thread_id: str) -> Tuple[str, str]:
        """
        Determine which agent should handle this request
        Returns (agent_type, reasoning)
        """
        try:
            # FIRST: Check prerequisites - creativity test must come before project overview
            has_creativity_test = await self._has_completed_creativity_test(user_id)
            
            if not has_creativity_test:
                # Force creativity test first regardless of active sessions
                return "creativity_test", "Creativity test required before project planning"
            
            # Check if there are active sessions (only after prerequisites are met)
            active_sessions = await self._get_active_sessions(user_id, thread_id)
            
            if active_sessions:
                # Continue with existing session
                agent_type = active_sessions[0]['agent_type']
                return agent_type, f"Continuing active {agent_type} session"
            
            # Check for incomplete flows
            incomplete_flows = await self._check_incomplete_flows(user_id)
            
            if incomplete_flows:
                agent_type = incomplete_flows[0]
                return agent_type, f"Resuming incomplete {agent_type} flow"
            
            # Analyze message content to determine intent
            message_lower = user_message.lower()
            
            # Keywords for creativity test
            creativity_keywords = [
                'creativity', 'creative', 'archetype', 'test', 'assessment', 
                'type of creator', 'creative style', 'creative type'
            ]
            
            # Keywords for project overview
            project_keywords = [
                'project', 'planning', 'plan', 'overview', 'onboarding',
                'goal', 'vision', 'idea', 'concept', 'work on'
            ]
            
            creativity_score = sum(1 for keyword in creativity_keywords if keyword in message_lower)
            project_score = sum(1 for keyword in project_keywords if keyword in message_lower)
            
            if creativity_score > project_score:
                return "creativity_test", "Message content suggests creativity assessment"
            elif project_score > creativity_score:
                return "project_overview", "Message content suggests project planning"
            else:
                # Default to project overview for general inquiries
                return "project_overview", "Default to project planning for general inquiry"
                
        except Exception as e:
            logger.error(f"Error determining agent: {e}")
            return "project_overview", "Fallback to project planning due to error"
    
    async def _get_active_sessions(self, user_id: str, thread_id: str) -> List[Dict]:
        """Get active agent sessions for user and thread"""
        try:
            result = self.supabase.table('agent_sessions')\
                .select('*')\
                .eq('user_id', user_id)\
                .eq('thread_id', thread_id)\
                .eq('is_active', True)\
                .execute()
            
            return result.data or []
            
        except Exception as e:
            logger.error(f"Error getting active sessions: {e}")
            return []
    
    async def _has_completed_creativity_test(self, user_id: str) -> bool:
        """Check if user has completed creativity test"""
        try:
            result = self.supabase.table('creativity_test_progress')\
                .select('is_completed')\
                .eq('user_id', user_id)\
                .eq('is_completed', True)\
                .limit(1)\
                .execute()
            
            return len(result.data) > 0
            
        except Exception as e:
            logger.error(f"Error checking creativity test completion: {e}")
            return False
    
    async def _check_incomplete_flows(self, user_id: str) -> List[str]:
        """Check for incomplete flows and return agent types in priority order"""
        incomplete = []
        
        try:
            # Check creativity test progress
            creativity_result = self.supabase.table('creativity_test_progress')\
                .select('is_completed')\
                .eq('user_id', user_id)\
                .order('created_at', desc=True)\
                .limit(1)\
                .execute()
            
            if creativity_result.data and not creativity_result.data[0].get('is_completed', False):
                incomplete.append('creativity_test')
            
            # Check project overview progress
            project_result = self.supabase.table('project_overview_progress')\
                .select('is_completed')\
                .eq('user_id', user_id)\
                .order('created_at', desc=True)\
                .limit(1)\
                .execute()
            
            if project_result.data and not project_result.data[0].get('is_completed', False):
                incomplete.append('project_overview')
            
            return incomplete
            
        except Exception as e:
            logger.error(f"Error checking incomplete flows: {e}")
            return []
    
    async def process_message(self, user_id: str, user_message: str, thread_id: str) -> Tuple[str, str]:
        """
        Process message with appropriate agent
        Returns (response, agent_type_used)
        """
        try:
            # Determine which agent to use
            agent_type, reasoning = await self.determine_agent_needed(user_id, user_message, thread_id)
            
            logger.info(f"Using {agent_type} agent for user {user_id}: {reasoning}")
            
            # Get the appropriate agent
            agent = self._get_agent(user_id, agent_type)
            
            # Process message with agent
            response = await agent.process_message(thread_id, user_message)
            
            return response, agent_type
            
        except Exception as e:
            logger.error(f"Error processing message with agent: {e}")
            return "I'm sorry, I'm having trouble processing your request right now. Please try again.", "error"
    
    async def get_user_status(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive status for user across all agents"""
        try:
            status = {
                'user_id': user_id,
                'active_sessions': [],
                'completed_flows': [],
                'incomplete_flows': [],
                'recommendations': []
            }
            
            # Check active sessions
            active_sessions = self.supabase.table('agent_sessions')\
                .select('*')\
                .eq('user_id', user_id)\
                .eq('is_active', True)\
                .execute()
            
            status['active_sessions'] = active_sessions.data or []
            
            # Check creativity test completion
            creativity_agent = self._get_agent(user_id, 'creativity_test')
            if await creativity_agent.is_flow_complete():
                status['completed_flows'].append('creativity_test')
            else:
                creativity_progress = await creativity_agent.get_progress()
                if creativity_progress.get('flow_step', 1) > 1:
                    status['incomplete_flows'].append('creativity_test')
            
            # Check project overview completion
            project_agent = self._get_agent(user_id, 'project_overview')
            if await project_agent.is_flow_complete():
                status['completed_flows'].append('project_overview')
            else:
                project_progress = await project_agent.get_progress()
                if project_progress.get('flow_step', 1) > 1:
                    status['incomplete_flows'].append('project_overview')
            
            # Generate recommendations
            if 'creativity_test' not in status['completed_flows'] and 'creativity_test' not in status['incomplete_flows']:
                status['recommendations'].append('Take the creativity assessment to understand your creative style')
            
            if 'project_overview' not in status['completed_flows'] and 'project_overview' not in status['incomplete_flows']:
                status['recommendations'].append('Create a comprehensive project plan through our guided conversation')
            
            return status
            
        except Exception as e:
            logger.error(f"Error getting user status: {e}")
            return {'user_id': user_id, 'error': str(e)}
    
    async def cleanup_expired_sessions(self):
        """Clean up expired agent sessions"""
        try:
            # Update expired sessions to inactive
            self.supabase.table('agent_sessions')\
                .update({'is_active': False})\
                .lt('expires_at', 'now()')\
                .execute()
            
            logger.info("Cleaned up expired agent sessions")
            
        except Exception as e:
            logger.error(f"Error cleaning up expired sessions: {e}")
    
    async def force_end_session(self, user_id: str, thread_id: str, agent_type: Optional[str] = None):
        """Force end a session (useful for testing or user-requested resets)"""
        try:
            query = self.supabase.table('agent_sessions')\
                .update({'is_active': False})\
                .eq('user_id', user_id)\
                .eq('thread_id', thread_id)
            
            if agent_type:
                query = query.eq('agent_type', agent_type)
            
            query.execute()
            
            logger.info(f"Force ended session for user {user_id}, thread {thread_id}, agent {agent_type}")
            
        except Exception as e:
            logger.error(f"Error force ending session: {e}") 