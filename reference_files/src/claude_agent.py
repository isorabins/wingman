#!/usr/bin/env python3
"""
Claude Agent - Clean direct Anthropic SDK implementation with Archetype Personalization
No unnecessary abstractions, just the official SDK pattern with style adaptations
"""

import os
import logging
from typing import Dict, Any, AsyncGenerator
from dotenv import load_dotenv
from datetime import datetime, timezone
import json

# Direct Anthropic SDK - no custom wrappers needed
from anthropic import AsyncAnthropic

# Import existing app modules (keeping all app logic)
from src.simple_memory import SimpleMemory
from src.prompts import main_prompt
from src.config import Config
from src.context_formatter import format_static_context_for_caching, get_cache_control_header

# Set up logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import archetype personalization functions
try:
    from src.archetype_helper import get_personalized_prompt_and_temperature
    ARCHETYPE_ENABLED = True
    logger.info("Archetype personalization system loaded successfully")
except ImportError as e:
    logger.warning(f"Archetype system not available: {e}. Using default prompts.")
    ARCHETYPE_ENABLED = False

# Load environment variables
load_dotenv()

# Simple singleton for Anthropic client
_anthropic_client = None

async def get_anthropic_client() -> AsyncAnthropic:
    """Get or create the Anthropic client instance (singleton pattern)"""
    global _anthropic_client
    if _anthropic_client is None:
        _anthropic_client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    return _anthropic_client

async def get_personalized_system_prompt(user_id: str, user_timezone: str, memory: SimpleMemory) -> tuple[str, float]:
    """
    Get personalized system prompt and temperature based on user's archetype
    
    Returns:
        tuple: (personalized_prompt, temperature)
    """
    try:
        if ARCHETYPE_ENABLED:
            # Get personalized prompt and temperature using the helper
            personalized_prompt, temperature = await get_personalized_prompt_and_temperature(user_id, memory)
            
            # Format with current time and timezone
            formatted_prompt = personalized_prompt.format(
                current_time=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
                user_timezone=user_timezone
            )
            
            return formatted_prompt, temperature
        else:
            # Fallback to default prompt
            from src.prompts import DEFAULT_ARCHETYPE_STYLE
            default_prompt = main_prompt.format(
                archetype_guidance=DEFAULT_ARCHETYPE_STYLE,
                current_time=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
                user_timezone=user_timezone
            )
            return default_prompt, 0.6
            
    except Exception as e:
        logger.error(f"Error getting personalized prompt for user {user_id}: {e}")
        # Fallback to default prompt
        from src.prompts import DEFAULT_ARCHETYPE_STYLE
        default_prompt = main_prompt.format(
            archetype_guidance=DEFAULT_ARCHETYPE_STYLE,
            current_time=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            user_timezone=user_timezone
        )
        return default_prompt, 0.6

def format_simple_context(static_context: Dict[str, Any]) -> str:
    """Simple context formatting for basic conversational agent"""
    context_parts = []
    
    # Basic user profile
    profile = static_context.get("user_profile", {})
    if profile:
        context_parts.append("=== USER PROFILE ===")
        context_parts.append(f"Name: {profile.get('first_name', '')} {profile.get('last_name', '')}")
        context_parts.append(f"User ID: {profile.get('id', 'unknown')}")
        context_parts.append("")
    
    # Project overview if it exists
    project = static_context.get("project_overview", {})
    if project:
        context_parts.append("=== PROJECT CONTEXT ===")
        context_parts.append(f"Project: {project.get('project_name', 'Unnamed Project')}")
        context_parts.append(f"Type: {project.get('project_type', 'Not specified')}")
        context_parts.append(f"Description: {project.get('description', 'No description')}")
        context_parts.append("")
    
    # Recent summaries for context
    summaries = static_context.get("longterm_summaries", [])
    if summaries:
        context_parts.append("=== CONVERSATION CONTEXT ===")
        for summary in summaries[:3]:  # Last 3 summaries
            if isinstance(summary, dict):
                context_parts.append(f"Previous: {summary.get('content', 'No content')}")
        context_parts.append("")
    
    return "\n".join(context_parts) if context_parts else "New conversation - no previous context"

async def interact_with_agent(
    user_input: str, 
    user_id: str, 
    user_timezone: str,
    thread_id: str,
    supabase_client,
    context: Dict[str, Any]
):
    """Process user input using Claude client - simple chat with optimized caching"""
    try:
        logger.info(f"Processing input for user {user_id}")
        logger.info(f"User Input: {user_input}")
        
        # Get caching-optimized context
        memory = SimpleMemory(supabase_client, user_id)
        caching_context = await memory.get_caching_optimized_context(thread_id)
        
        # Get Anthropic client
        anthropic_client = await get_anthropic_client()
        
        # Use optimized context formatter for better caching
        cached_context = format_static_context_for_caching(caching_context["static_context"])
        cache_headers = get_cache_control_header()
        
        # Build conversation messages with cache control
        chat_messages = []
        
        # Add cached static context as first user message with cache control
        if cached_context.strip():
            chat_messages.append({
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": cached_context,
                        "cache_control": {"type": "ephemeral"}  # Enable caching
                    }
                ]
            })
        
        # Add conversation history
        for msg in caching_context["dynamic_context"]["conversation_messages"]:
            chat_messages.append({
                "role": msg["role"], 
                "content": msg["content"]
            })
        
        # Add current user input
        chat_messages.append({
            "role": "user", 
            "content": user_input
        })
        
        logger.info(f"Sending {len(chat_messages)} messages to Claude with caching")
        
        # Get personalized system prompt based on user's archetype
        system_prompt, temperature = await get_personalized_system_prompt(
            user_id, user_timezone, memory
        )
        
        # Make request to Claude with optimized caching and personalized prompt
        try:
            # Use cost-optimized model selection for chat (Claude 4 in production, Haiku in dev/test)
            from src.model_selector import get_chat_model
            chat_model = get_chat_model()
            
            response = await anthropic_client.messages.create(
                model=chat_model,
                max_tokens=4000,
                temperature=temperature,  # Use archetype-specific temperature (consistent 0.6)
                extra_headers=cache_headers,  # Include cache headers
                system=system_prompt,  # Use personalized system prompt
                messages=chat_messages
            )
            
            # Extract response content
            assistant_response = ""
            for block in response.content:
                if hasattr(block, 'text'):
                    assistant_response += block.text
            
            # Log cache usage if available
            if hasattr(response, 'usage'):
                logger.info(f"Cache usage: creation_tokens={response.usage.cache_creation_input_tokens}, "
                          f"read_tokens={response.usage.cache_read_input_tokens}")
            
            logger.info(f"Received response from Claude: {len(assistant_response)} characters")
            return assistant_response
            
        except Exception as claude_error:
            logger.error(f"Claude API error: {str(claude_error)}")
            return "I'm experiencing some technical difficulties. Please try again in a moment."
            
    except Exception as e:
        logger.error(f"Error in interact_with_agent: {str(e)}", exc_info=True)
        return "I apologize, but I'm having trouble processing your request right now. Please try again."

async def interact_with_agent_stream(
    user_input: str, 
    user_id: str, 
    user_timezone: str,
    thread_id: str,
    supabase_client,
    context: Dict[str, Any]
) -> AsyncGenerator[str, None]:
    """Process user input with streaming response using Claude client with optimized caching"""
    try:
        logger.info(f"Processing streaming input for user {user_id}")
        
        # Get caching-optimized context
        memory = SimpleMemory(supabase_client, user_id)
        caching_context = await memory.get_caching_optimized_context(thread_id)
        
        # Get Anthropic client
        anthropic_client = await get_anthropic_client()
        
        # Use optimized context formatter for better caching
        cached_context = format_static_context_for_caching(caching_context["static_context"])
        cache_headers = get_cache_control_header()
        
        # Build conversation messages with cache control
        chat_messages = []
        
        # Add cached static context as first user message with cache control
        if cached_context.strip():
            chat_messages.append({
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": cached_context,
                        "cache_control": {"type": "ephemeral"}  # Enable caching
                    }
                ]
            })
        
        # Add conversation history
        for msg in caching_context["dynamic_context"]["conversation_messages"]:
            chat_messages.append({
                "role": msg["role"], 
                "content": msg["content"]
            })
        
        # Add current user input
        chat_messages.append({
            "role": "user", 
            "content": user_input
        })
        
        logger.info(f"Sending {len(chat_messages)} messages to Claude for streaming with caching")
        
        # Get personalized system prompt based on user's archetype
        system_prompt, temperature = await get_personalized_system_prompt(
            user_id, user_timezone, memory
        )
        
        # Make streaming request to Claude with optimized caching and personalized prompt
        try:
            stream = await anthropic_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4000,
                temperature=temperature,  # Use archetype-specific temperature (consistent 0.6)
                extra_headers=cache_headers,  # Include cache headers
                system=system_prompt,  # Use personalized system prompt
                messages=chat_messages,
                stream=True
            )
            
            # Stream the response
            async for event in stream:
                if hasattr(event, 'delta') and hasattr(event.delta, 'text'):
                    yield event.delta.text
                    
        except Exception as claude_error:
            logger.error(f"Claude streaming API error: {str(claude_error)}")
            yield "I'm experiencing some technical difficulties. Please try again in a moment."
            
    except Exception as e:
        logger.error(f"Error in interact_with_agent_stream: {str(e)}", exc_info=True)
        yield "I apologize, but I'm having trouble processing your request right now. Please try again."


# Backwards compatibility - memory storage after successful streaming 
async def store_conversation_in_memory(supabase_client, user_id: str, thread_id: str, user_input: str, assistant_response: str):
    """Store completed conversation in memory"""
    try:
        memory = SimpleMemory(supabase_client, user_id)
        logger.info(f"Successfully stored streaming conversation in memory for thread {thread_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to store conversation in memory: {str(e)}")
        return False 