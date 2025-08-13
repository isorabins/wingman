#!/usr/bin/env python3
"""
Claude Agent for WingmanMatch - Connell Barrett Dating Confidence Coach

Direct Anthropic SDK implementation optimized for authentic dating confidence coaching.
Integrates with WingmanMatch infrastructure for memory persistence and tool calling.
"""

import os
import logging
from typing import Dict, Any, AsyncGenerator, Optional, List
from dotenv import load_dotenv
from datetime import datetime, timezone
import json
import asyncio

# Direct Anthropic SDK - no abstractions needed
from anthropic import AsyncAnthropic

# WingmanMatch imports
from src.simple_memory import WingmanMemory
from src.prompts import main_prompt, get_personalized_prompt, get_archetype_temperature
from src.config import Config
from src.database import get_db_service
from src.retry_utils import with_anthropic_retry
from src.safety_filters import create_safety_filter, SafetySeverity
from src.context_formatter import format_context_for_prompt_caching
import src.tools as wingman_tools

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Singleton Anthropic client
_anthropic_client = None

# Global safety filter instance
_safety_filter = None

def get_safety_filter():
    """Get or create the safety filter instance (singleton pattern)"""
    global _safety_filter
    if _safety_filter is None:
        _safety_filter = create_safety_filter()
        logger.info("Safety filter initialized for WingmanMatch")
    return _safety_filter

async def get_anthropic_client() -> AsyncAnthropic:
    """Get or create the Anthropic client instance (singleton pattern)"""
    global _anthropic_client
    if _anthropic_client is None:
        _anthropic_client = AsyncAnthropic(api_key=Config.ANTHROPIC_API_KEY)
        logger.info("Anthropic client initialized for WingmanMatch")
    return _anthropic_client

def get_wingman_model() -> str:
    """Get appropriate Claude model for WingmanMatch coaching"""
    if Config.DEVELOPMENT_MODE or Config.FORCE_TESTING_MODE:
        return Config.DEV_CHAT_MODEL
    elif Config.ENABLE_COST_OPTIMIZATION:
        # Use cost-effective model for high volume
        return "claude-3-haiku-20240307"
    else:
        # Premium model for best coaching quality
        return Config.CHAT_MODEL

async def get_user_context(user_id: str, thread_id: str) -> Dict[str, Any]:
    """Get comprehensive user context for dating confidence coaching"""
    try:
        memory = WingmanMemory(get_db_service(), user_id)
        context = await memory.get_coaching_context(thread_id)
        
        # Add WingmanMatch-specific context
        db = get_db_service()
        
        # Get user profile
        user_result = db.table('user_profiles').select('*').eq('id', user_id).execute()
        user_profile = user_result.data[0] if user_result.data else None
        
        # Get assessment results  
        assessment_result = db.table('confidence_assessments').select('*').eq('user_id', user_id).order('created_at', desc=True).limit(1).execute()
        assessment_data = assessment_result.data[0] if assessment_result.data else None
        
        # Get recent attempts
        attempts_result = db.table('approach_attempts').select('*').eq('user_id', user_id).order('created_at', desc=True).limit(10).execute()
        attempts_data = attempts_result.data or []
        
        # Get challenges
        challenges_result = db.table('approach_challenges').select('*').order('difficulty').execute()
        challenges_data = challenges_result.data or []
        
        context.update({
            'user_profile': user_profile,
            'assessment_results': assessment_data,
            'recent_attempts': attempts_data,
            'available_challenges': challenges_data,
        })
        
        return context
        
    except Exception as e:
        logger.error(f"Error getting user context: {e}")
        return {
            'conversation_history': [],
            'session_history': [],
            'user_profile': None,
            'assessment_results': None,
            'recent_attempts': [],
            'available_challenges': [],
        }

def format_coaching_context(context: Dict[str, Any], archetype: Optional[int] = None) -> str:
    """
    Format context for dating confidence coaching prompt injection
    Uses optimized context formatter if enabled, falls back to legacy format
    """
    try:
        if Config.ENABLE_CONTEXT_OPTIMIZATION:
            # Use new optimized context formatter
            formatted_context, cache_info = format_context_for_prompt_caching(context, archetype)
            
            # Log cache optimization info
            if Config.ENABLE_DETAILED_LOGGING:
                logger.info(f"Context formatting: size={cache_info.context_size}, "
                          f"cacheable={cache_info.cacheable}, compression={cache_info.compression_ratio:.2f}")
            
            return formatted_context
        else:
            # Use legacy context formatting
            return _format_coaching_context_legacy(context)
            
    except Exception as e:
        logger.error(f"Error in context formatting: {e}")
        return _format_coaching_context_legacy(context)

def _format_coaching_context_legacy(context: Dict[str, Any]) -> str:
    """Legacy context formatting for fallback"""
    context_parts = []
    
    # User Profile
    if context.get('user_profile'):
        profile = context['user_profile']
        context_parts.append("=== USER PROFILE ===")
        context_parts.append(f"Name: {profile.get('first_name', 'User')}")
        context_parts.append(f"Age: {profile.get('age', 'Not specified')}")
        context_parts.append(f"Location: {profile.get('location', 'Not specified')}")
        context_parts.append("")
    
    # Dating Confidence Assessment
    if context.get('assessment_results'):
        assessment = context['assessment_results']
        context_parts.append("=== CONFIDENCE ASSESSMENT ===")
        context_parts.append(f"Confidence Level: {assessment.get('confidence_level', 'Not assessed')}")
        context_parts.append(f"Primary Fears: {assessment.get('primary_fears', 'Not specified')}")
        context_parts.append(f"Dating Goals: {assessment.get('dating_goals', 'Not specified')}")
        context_parts.append("")
    
    # Recent Approach Attempts
    if context.get('recent_attempts'):
        context_parts.append("=== RECENT APPROACH ATTEMPTS ===")
        for attempt in context['recent_attempts'][:3]:  # Last 3 attempts
            outcome = attempt.get('outcome', 'Unknown')
            notes = attempt.get('notes', 'No notes')
            context_parts.append(f"• {outcome}: {notes}")
        context_parts.append("")
    
    # Session History  
    if context.get('session_history'):
        context_parts.append("=== COACHING SESSION HISTORY ===")
        for session in context['session_history'][:3]:  # Last 3 sessions
            context_parts.append(f"• {session.get('summary', 'No summary')}")
        context_parts.append("")
    
    # Conversation History
    if context.get('conversation_history'):
        context_parts.append("=== RECENT CONVERSATION ===")
        for msg in context['conversation_history'][-6:]:  # Last 6 messages
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')
            context_parts.append(f"{role}: {content}")
        context_parts.append("")
    
    return "\\n".join(context_parts) if context_parts else "New coaching session - no previous context"

@with_anthropic_retry()
async def interact_with_coach(
    user_input: str,
    user_id: str,
    thread_id: str,
    context: Optional[Dict[str, Any]] = None
) -> str:
    """
    Get coaching response from Connell Barrett (non-streaming)
    
    Args:
        user_input: User's message/question
        user_id: User identifier 
        thread_id: Conversation thread identifier
        context: Optional pre-loaded context
        
    Returns:
        Connell's coaching response
    """
    try:
        logger.info(f"Processing coaching request for user {user_id}")
        
        # Step 1: Safety filter user input
        if Config.ENABLE_SAFETY_FILTERS:
            safety_filter = get_safety_filter()
            safety_result = safety_filter.filter_user_input(user_input)
            
            if not safety_result.is_safe:
                logger.warning(f"User input blocked for safety: {safety_result.violations}")
                return safety_result.guidance_message or "I need to make sure our conversation stays focused on respectful dating confidence building."
            
            # Use filtered content and add guidance if needed
            filtered_input = safety_result.filtered_content
            if safety_result.guidance_message and safety_result.severity != SafetySeverity.LOW:
                # Prepend guidance for medium/high severity issues
                filtered_input = f"{safety_result.guidance_message}\n\nNow, regarding your original question: {filtered_input}"
        else:
            filtered_input = user_input
        
        # Step 2: Get context if not provided
        if context is None:
            context = await get_user_context(user_id, thread_id)
        
        # Step 3: Get user's dating archetype if available
        archetype = None
        if context.get('assessment_results'):
            archetype = context['assessment_results'].get('archetype')
        
        # Step 4: Format context for prompt injection
        formatted_context = format_coaching_context(context, archetype)
        
        # Step 5: Get personalized prompt and temperature
        personalized_prompt = get_personalized_prompt(main_prompt, archetype, formatted_context)
        temperature = get_archetype_temperature()
        
        # Step 6: Get Anthropic client
        anthropic_client = await get_anthropic_client()
        
        # Step 7: Build conversation messages
        messages = []
        
        # Add conversation history
        for msg in context.get('conversation_history', [])[-10:]:  # Last 10 messages
            messages.append({
                "role": msg.get('role'),
                "content": msg.get('content')
            })
        
        # Add current user input (filtered)
        messages.append({
            "role": "user",
            "content": filtered_input
        })
        
        logger.info(f"Sending {len(messages)} messages to Claude for coaching")
        
        # Step 8: Get model for current request
        model = get_wingman_model()
        
        # Step 9: Make request to Claude
        response = await anthropic_client.messages.create(
            model=model,
            max_tokens=2048,
            temperature=temperature,  # Use archetype-specific temperature
            top_p=0.9,               # Balanced nucleus sampling  
            system=personalized_prompt,
            messages=messages
        )
        
        # Step 10: Extract response content
        assistant_response = ""
        for block in response.content:
            if hasattr(block, 'text'):
                assistant_response += block.text
        
        # Step 11: Safety filter coach response
        if Config.ENABLE_SAFETY_FILTERS:
            safety_filter = get_safety_filter()
            response_safety_result = safety_filter.filter_coach_response(assistant_response)
            
            if not response_safety_result.is_safe:
                logger.warning(f"Coach response failed safety check: {response_safety_result.violations}")
                final_response = response_safety_result.filtered_content
            else:
                final_response = response_safety_result.filtered_content
        else:
            final_response = assistant_response
        
        logger.info(f"Coaching response completed: {len(final_response)} characters")
        return final_response
        
    except Exception as e:
        logger.error(f"Error in interact_with_coach: {str(e)}", exc_info=True)
        return "I'm having some technical difficulties right now. Let me regroup and we'll continue our coaching session in just a moment."

@with_anthropic_retry()
async def interact_with_coach_stream(
    user_input: str,
    user_id: str, 
    thread_id: str,
    context: Optional[Dict[str, Any]] = None
) -> AsyncGenerator[str, None]:
    """
    Get streaming coaching response from Connell Barrett
    
    Args:
        user_input: User's message/question
        user_id: User identifier
        thread_id: Conversation thread identifier  
        context: Optional pre-loaded context
        
    Yields:
        Streaming response chunks from Connell
    """
    try:
        logger.info(f"Processing streaming coaching request for user {user_id}")
        
        # Step 1: Safety filter user input
        if Config.ENABLE_SAFETY_FILTERS:
            safety_filter = get_safety_filter()
            safety_result = safety_filter.filter_user_input(user_input)
            
            if not safety_result.is_safe:
                logger.warning(f"User input blocked for safety in streaming: {safety_result.violations}")
                yield safety_result.guidance_message or "I need to make sure our conversation stays focused on respectful dating confidence building."
                return
            
            # Use filtered content and add guidance if needed
            filtered_input = safety_result.filtered_content
            if safety_result.guidance_message and safety_result.severity != SafetySeverity.LOW:
                # Stream guidance first for medium/high severity issues
                yield safety_result.guidance_message
                yield "\n\nNow, regarding your original question: "
        else:
            filtered_input = user_input
        
        # Step 2: Get context if not provided
        if context is None:
            context = await get_user_context(user_id, thread_id)
        
        # Step 3: Get user's dating archetype if available
        archetype = None
        if context.get('assessment_results'):
            archetype = context['assessment_results'].get('archetype')
        
        # Step 4: Format context for prompt injection
        formatted_context = format_coaching_context(context, archetype)
        
        # Step 5: Get personalized prompt and temperature
        personalized_prompt = get_personalized_prompt(main_prompt, archetype, formatted_context)
        temperature = get_archetype_temperature()
        
        # Step 6: Get Anthropic client
        anthropic_client = await get_anthropic_client()
        
        # Step 7: Build conversation messages  
        messages = []
        
        # Add conversation history
        for msg in context.get('conversation_history', [])[-10:]:  # Last 10 messages
            messages.append({
                "role": msg.get('role'),
                "content": msg.get('content')
            })
        
        # Add current user input (filtered)
        messages.append({
            "role": "user", 
            "content": filtered_input
        })
        
        logger.info(f"Sending {len(messages)} messages to Claude for streaming coaching")
        
        # Step 8: Get model for current request
        model = get_wingman_model()
        
        # Step 9: Make streaming request to Claude
        stream = await anthropic_client.messages.create(
            model=model,
            max_tokens=2048,
            temperature=temperature,  # Use archetype-specific temperature
            top_p=0.9,               # Balanced nucleus sampling
            system=personalized_prompt,
            messages=messages,
            stream=True
        )
        
        # Step 10: Stream the response with optional safety filtering
        if Config.ENABLE_SAFETY_FILTERS:
            # Collect full response for safety checking
            full_response = ""
            response_chunks = []
            
            async for event in stream:
                if hasattr(event, 'delta') and hasattr(event.delta, 'text'):
                    chunk = event.delta.text
                    full_response += chunk
                    response_chunks.append(chunk)
            
            # Safety check the complete response
            safety_filter = get_safety_filter()
            response_safety_result = safety_filter.filter_coach_response(full_response)
            
            if not response_safety_result.is_safe:
                logger.warning(f"Streaming coach response failed safety check: {response_safety_result.violations}")
                yield response_safety_result.filtered_content
            else:
                # Stream the safe response chunks
                for chunk in response_chunks:
                    yield chunk
        else:
            # Stream directly without safety checking
            async for event in stream:
                if hasattr(event, 'delta') and hasattr(event.delta, 'text'):
                    yield event.delta.text
                
    except Exception as e:
        logger.error(f"Error in interact_with_coach_stream: {str(e)}", exc_info=True)
        yield "I'm experiencing some technical difficulties. Let me regroup and we'll continue our coaching conversation in just a moment."

async def store_coaching_conversation(
    user_id: str,
    thread_id: str, 
    user_input: str,
    coach_response: str
) -> bool:
    """
    Store completed coaching conversation in memory
    
    Args:
        user_id: User identifier
        thread_id: Conversation thread identifier
        user_input: User's input message
        coach_response: Connell's complete response
        
    Returns:
        True if stored successfully, False otherwise
    """
    try:
        memory = WingmanMemory(get_db_service(), user_id)
        
        # Store user message
        await memory.add_message(thread_id, user_input, "user")
        
        # Store coach response  
        await memory.add_message(thread_id, coach_response, "assistant")
        
        logger.info(f"Successfully stored coaching conversation for user {user_id}, thread {thread_id}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to store coaching conversation: {str(e)}")
        return False

# Function calling tools integration
async def call_wingman_tool(
    tool_name: str,
    user_id: str,
    **kwargs
) -> Dict[str, Any]:
    """
    Call WingmanMatch-specific tools for dating confidence coaching
    
    Args:
        tool_name: Name of the tool to call
        user_id: User identifier
        **kwargs: Tool-specific arguments
        
    Returns:
        Tool execution result
    """
    try:
        if hasattr(wingman_tools, tool_name):
            tool_func = getattr(wingman_tools, tool_name)
            result = await tool_func(user_id=user_id, **kwargs)
            logger.info(f"Successfully called tool {tool_name} for user {user_id}")
            return result
        else:
            logger.error(f"Unknown tool: {tool_name}")
            return {"error": f"Tool {tool_name} not found"}
            
    except Exception as e:
        logger.error(f"Error calling tool {tool_name}: {str(e)}")
        return {"error": str(e)}

# Health check for Claude agent
async def health_check() -> Dict[str, Any]:
    """Check health of Claude agent and dependencies"""
    health = {
        "claude_agent": False,
        "anthropic_client": False,
        "memory_system": False,
        "tools_available": False,
        "errors": []
    }
    
    try:
        # Test Anthropic client
        client = await get_anthropic_client()
        if client:
            health["anthropic_client"] = True
            health["claude_agent"] = True
        
        # Test memory system
        try:
            test_memory = WingmanMemory(get_db_service(), "health_check")
            health["memory_system"] = True
        except Exception as e:
            health["errors"].append(f"Memory system error: {str(e)}")
        
        # Test tools availability
        if hasattr(wingman_tools, 'get_approach_challenges'):
            health["tools_available"] = True
        else:
            health["errors"].append("Wingman tools not available")
            
    except Exception as e:
        health["errors"].append(f"Claude agent error: {str(e)}")
    
    return health

# Export key functions for API integration
__all__ = [
    'interact_with_coach',
    'interact_with_coach_stream', 
    'store_coaching_conversation',
    'call_wingman_tool',
    'health_check',
    'get_user_context'
]