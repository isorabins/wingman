#!/usr/bin/env python3
"""
Flow-Based Chat Handler for Fridays at Four
Replaces brittle stage system with natural conversation flows
Uses FlowManager + individual flow handlers for intro/creativity/project
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from supabase import Client

from src.flow_manager import FlowManager
from src.intro_flow_handler import IntroFlowHandler
from src.creativity_flow_handler import CreativityFlowHandler
from src.project_flow_handler import ProjectFlowHandler
from src.simple_memory import SimpleMemory

logger = logging.getLogger(__name__)

class FlowBasedChatHandler:
    """Handles user flow progression through intro → creativity → project → main chat"""
    
    def __init__(self, supabase: Client, user_id: str):
        self.supabase = supabase
        self.user_id = user_id
        self.flow_manager = FlowManager(supabase, user_id)
        self.flow_handlers = {}
    
    def _get_handler(self, flow_type: str):
        """Get or create flow handler"""
        if flow_type not in self.flow_handlers:
            if flow_type == 'intro':
                self.flow_handlers[flow_type] = IntroFlowHandler(self.supabase, self.user_id)
            elif flow_type == 'creativity':
                self.flow_handlers[flow_type] = CreativityFlowHandler(self.supabase, self.user_id)
            elif flow_type == 'project':
                self.flow_handlers[flow_type] = ProjectFlowHandler(self.supabase, self.user_id)
        
        return self.flow_handlers.get(flow_type)
    
    async def chat(self, message: str, thread_id: str) -> str:
        """Main chat method - routes to appropriate flow"""
        try:
            # Check for skip intent
            if self.flow_manager.detect_skip_intent(message):
                return await self._handle_skip_request()
            
            # Determine current flow
            flow_type, flow_data = await self.flow_manager.get_next_flow()
            
            # Route to appropriate handler
            if flow_type == 'main_chat':
                response = await self._handle_main_chat(message, thread_id)
            else:
                response = await self._handle_structured_flow(flow_type, message, flow_data, thread_id)
            
            # Store conversation in memory (following implementation guide)
            memory = SimpleMemory(self.supabase, self.user_id)
            await memory.add_message(thread_id, message, "user")
            await memory.add_message(thread_id, response, "assistant")
            
            return response
        
        except Exception as e:
            logger.error(f"Error in flow-based chat: {e}")
            return "I'm having trouble right now. Could you try again?"
    
    async def _handle_structured_flow(self, flow_type: str, message: str, flow_data: Dict[str, Any], thread_id: str) -> str:
        """Handle structured flows (intro, creativity, project)"""
        try:
            # Route to appropriate handler - following implementation guide exactly
            if flow_type == 'intro':
                handler = IntroFlowHandler(self.supabase, self.user_id)
                
                # Check if this is the very first interaction (no intro_data exists)
                if not flow_data.get('data'):
                    # Very first interaction - show welcome message
                    response = handler.get_welcome_message()
                    
                    # Create initial database record so next message gets processed
                    await handler._save_intro_progress([])
                else:
                    # Process all subsequent messages through the handler
                    result = await handler.handle_message(message, flow_data)
                    response = result['response']
            
            elif flow_type == 'creativity':
                handler = CreativityFlowHandler(self.supabase, self.user_id)
                
                # Only show start message if no responses recorded yet
                responses = flow_data.get('responses', {})
                if not responses:  # No responses yet - truly first interaction
                    response = handler.get_start_message()
                else:
                    # Process the message through handler
                    result = await handler.handle_message(message, flow_data)
                    response = result['response']
            
            elif flow_type == 'project':
                handler = ProjectFlowHandler(self.supabase, self.user_id)
                
                # Only show start message if no project data recorded yet
                project_data = flow_data.get('data', {})
                if not project_data:  # No project data yet - truly first interaction
                    response = handler.get_start_message()
                else:
                    # Process the message through handler
                    result = await handler.handle_message(message, flow_data)
                    response = result['response']
            
            else:
                # Fallback
                response = "Let's continue our conversation. What would you like to discuss?"
            
            return response
        
        except Exception as e:
            logger.error(f"Error in structured flow {flow_type}: {e}")
            return "I'm having trouble processing your request. Let me try again in a moment."
    
    async def _handle_main_chat(self, message: str, thread_id: str) -> str:
        """Handle main conversational chat using existing memory system"""
        try:
            memory = SimpleMemory(self.supabase, self.user_id, thread_id)
            
            # Get conversation context
            context = await memory.get_context(thread_id)
            
            # Use LLM router directly for main chat
            from src.llm_router import get_router
            
            # Build conversation history
            messages = []
            
            # Add system prompt
            system_prompt = """You are Hai, a warm and supportive AI partner at Fridays at Four. 
            You help creative professionals turn their dream projects into reality.
            
            You are having an ongoing conversation with a user who has completed their intro, 
            creativity test, and project planning. Now you're in general conversation mode.
            
            Be supportive, ask thoughtful questions, and help them make progress on their creative project.
            Remember their project details and provide specific, actionable guidance."""
            
            messages.append({"role": "system", "content": system_prompt})
            
            # Add conversation history
            if context.get('messages'):
                for msg in context['messages'][-10:]:  # Last 10 messages for context
                    role = "user" if msg['role'] == 'user' else "assistant"
                    messages.append({"role": role, "content": msg['content']})
            
            # Add current message
            messages.append({"role": "user", "content": message})
            
            router = await get_router()
            response = await router.send_message(
                messages=messages,
                model="claude-3-5-sonnet-20241022",
                max_tokens=1000,
                temperature=0.7
            )
            
            return response
        
        except Exception as e:
            logger.error(f"Error in main chat: {e}")
            return "I'm here to help with your creative project. What would you like to work on?"
    
    async def _handle_skip_request(self) -> str:
        """Handle user request to skip current flow"""
        try:
            # Determine current flow
            flow_type, flow_data = await self.flow_manager.get_next_flow()
            
            if flow_type == 'main_chat':
                return "You're all set up! What would you like to work on with your project?"
            
            # Set cooldown
            await self.flow_manager.set_skip_cooldown(flow_type)
            
            # Return appropriate skip message
            if flow_type == 'intro':
                return "No problem! I'll check back in tomorrow to see if you'd like to learn more about how Fridays at Four works. For now, what would you like to focus on?"
            elif flow_type == 'creativity':
                return "That's fine! The creativity test helps me understand your working style, but we can skip it for now. I'll ask again tomorrow. What would you like to work on with your project?"
            elif flow_type == 'project':
                return "Sure thing! Project planning can wait. I'll check back tomorrow to see if you'd like to map out your project goals. What would you like to discuss today?"
            else:
                return "Understood! What would you like to focus on instead?"
        
        except Exception as e:
            logger.error(f"Error handling skip request: {e}")
            return "Sure, we can skip that for now. What would you like to work on?"
    
    async def get_flow_status(self) -> Dict[str, Any]:
        """Get current flow status for debugging"""
        try:
            flow_type, flow_data = await self.flow_manager.get_next_flow()
            
            return {
                'current_flow': flow_type,
                'flow_data': flow_data,
                'user_id': self.user_id
            }
        
        except Exception as e:
            logger.error(f"Error getting flow status: {e}")
            return {'error': str(e)}
    
    async def reset_flows(self) -> Dict[str, Any]:
        """Reset all flows for testing"""
        try:
            # Delete all flow progress
            tables_to_clear = [
                'creativity_test_progress',
                'creator_creativity_profiles', 
                'project_overview_progress',
                'project_overview'
            ]
            
            for table in tables_to_clear:
                try:
                    self.supabase.table(table)\
                        .delete()\
                        .eq('user_id', self.user_id)\
                        .execute()
                except Exception as e:
                    logger.warning(f"Could not clear {table}: {e}")
            
            return {
                'status': 'success',
                'message': 'All flows reset for user',
                'user_id': self.user_id
            }
        
        except Exception as e:
            logger.error(f"Error resetting flows: {e}")
            return {'status': 'error', 'error': str(e)}

# Convenience functions for backwards compatibility
async def chat(supabase: Client, user_id: str, message: str, thread_id: str) -> str:
    """Main chat function - backwards compatible"""
    handler = FlowBasedChatHandler(supabase, user_id)
    return await handler.chat(message, thread_id)

async def get_flow_status(supabase: Client, user_id: str) -> Dict[str, Any]:
    """Get flow status - backwards compatible"""
    handler = FlowBasedChatHandler(supabase, user_id)
    return await handler.get_flow_status()

async def reset_flows(supabase: Client, user_id: str) -> Dict[str, Any]:
    """Reset flows - backwards compatible"""
    handler = FlowBasedChatHandler(supabase, user_id)
    return await handler.reset_flows() 