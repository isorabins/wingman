#!/usr/bin/env python3
"""
Base Agent Class for Fridays at Four

Provides common functionality for Claude agents including:
- Session management
- Progress tracking 
- Database operations
- LLM Router integration with fallback protection
"""

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Tuple
from supabase import Client

from src.simple_memory import SimpleMemory

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    """Base class for all Claude agents with common functionality"""
    
    def __init__(self, supabase_client: Client, user_id: str, agent_type: str):
        self.supabase = supabase_client
        self.user_id = user_id
        self.agent_type = agent_type
        self.memory = SimpleMemory(supabase_client, user_id)
        
    async def start_session(self, thread_id: str) -> Dict[str, Any]:
        """Start a new agent session"""
        try:
            # Ensure creator profile exists
            await self.memory.ensure_creator_profile(self.user_id)
            
            # Create or get existing session
            session_data = {
                'user_id': self.user_id,
                'agent_type': self.agent_type,
                'thread_id': thread_id,
                'session_context': {},
                'is_active': True,
                'expires_at': (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()
            }
            
            # Check if session already exists
            existing = self.supabase.table('agent_sessions')\
                .select('*')\
                .eq('user_id', self.user_id)\
                .eq('agent_type', self.agent_type)\
                .eq('thread_id', thread_id)\
                .eq('is_active', True)\
                .execute()
            
            if existing.data:
                session = existing.data[0]
                logger.info(f"Resuming existing {self.agent_type} session for user {self.user_id}")
            else:
                session = self.supabase.table('agent_sessions')\
                    .insert(session_data)\
                    .execute()
                session = session.data[0]
                logger.info(f"Created new {self.agent_type} session for user {self.user_id}")
            
            return session
            
        except Exception as e:
            logger.error(f"Error starting agent session: {e}")
            raise
    
    async def end_session(self, thread_id: str):
        """End the current agent session"""
        try:
            self.supabase.table('agent_sessions')\
                .update({'is_active': False})\
                .eq('user_id', self.user_id)\
                .eq('agent_type', self.agent_type)\
                .eq('thread_id', thread_id)\
                .execute()
            
            logger.info(f"Ended {self.agent_type} session for user {self.user_id}")
            
        except Exception as e:
            logger.error(f"Error ending agent session: {e}")
    
    async def get_session_context(self, thread_id: str) -> Dict[str, Any]:
        """Get current session context"""
        try:
            result = self.supabase.table('agent_sessions')\
                .select('session_context')\
                .eq('user_id', self.user_id)\
                .eq('agent_type', self.agent_type)\
                .eq('thread_id', thread_id)\
                .eq('is_active', True)\
                .single()\
                .execute()
            
            return result.data.get('session_context', {}) if result.data else {}
            
        except Exception as e:
            logger.error(f"Error getting session context: {e}")
            return {}
    
    async def update_session_context(self, thread_id: str, context: Dict[str, Any]):
        """Update session context"""
        try:
            self.supabase.table('agent_sessions')\
                .update({'session_context': context})\
                .eq('user_id', self.user_id)\
                .eq('agent_type', self.agent_type)\
                .eq('thread_id', thread_id)\
                .eq('is_active', True)\
                .execute()
            
        except Exception as e:
            logger.error(f"Error updating session context: {e}")
    
    async def call_claude_with_router(self, messages: List[Dict[str, str]], system_prompt: str = "") -> str:
        """Make a call to Claude via LLM Router with automatic fallback protection"""
        try:
            from src.llm_router import get_router
            
            # Get router instance
            router = await get_router()
            
            # Call through router for automatic fallback
            response = await router.send_message(
                messages=messages,
                system=system_prompt,
                model="claude-3-5-sonnet-20241022",
                max_tokens=2000,
                temperature=0.7,
                stream=False
            )
            
            logger.info(f"LLM Router call successful, provider: {router.get_last_provider()}")
            return response
            
        except Exception as e:
            logger.error(f"Error calling Claude via LLM Router: {e}")
            return "I apologize, but I'm having trouble processing your request right now. Please try again."
    
    async def store_conversation(self, thread_id: str, user_message: str, ai_response: str):
        """Store conversation in memory system"""
        try:
            await self.memory.add_message(thread_id, user_message, "user")
            await self.memory.add_message(thread_id, ai_response, "assistant")
        except Exception as e:
            logger.error(f"Error storing conversation: {e}")
    
    # Abstract methods that must be implemented by subclasses
    @abstractmethod
    async def process_message(self, thread_id: str, user_message: str) -> str:
        """Process a user message and return AI response"""
        pass
    
    @abstractmethod
    async def get_progress(self) -> Dict[str, Any]:
        """Get current progress for this agent type"""
        pass
    
    @abstractmethod
    async def save_progress(self, progress_data: Dict[str, Any]):
        """Save progress data"""
        pass
    
    @abstractmethod
    async def is_flow_complete(self) -> bool:
        """Check if the agent flow is complete"""
        pass

