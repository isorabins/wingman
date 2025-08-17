#!/usr/bin/env python3
"""
Enhanced Claude Agent with Performance Optimization

Integrates model routing, memory compression, and Redis caching for optimal
WingmanMatch dating confidence coaching performance.

Features:
- Intelligent model routing based on conversation type
- Memory compression for context window management
- Cost optimization with cheaper models for simple interactions
- Conversation continuity preservation
- Comprehensive performance monitoring
"""

import os
import logging
from typing import Dict, Any, AsyncGenerator, Optional, List
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

# Import performance optimization modules
from src.model_router import model_router, get_optimal_model, ModelRoutingDecision
from src.memory_compressor import memory_compressor, compress_messages, CompressionStrategy
from src.redis_client import redis_service

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

async def get_optimized_context(memory: SimpleMemory, thread_id: str, 
                               user_preferences: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Get optimized conversation context with compression if needed.
    
    Args:
        memory: SimpleMemory instance
        thread_id: Thread identifier
        user_preferences: User-specific preferences
        
    Returns:
        Optimized context with compressed messages if needed
    """
    try:
        # Get full context from memory
        full_context = await memory.get_caching_optimized_context(thread_id)
        
        # Check if message compression is needed
        messages = full_context["dynamic_context"]["conversation_messages"]
        
        if memory_compressor.should_compress(messages):
            logger.info(f"Compressing {len(messages)} messages for thread {thread_id}")
            
            # Select compression strategy based on user preferences
            strategy = CompressionStrategy.BALANCED
            if user_preferences:
                if user_preferences.get("preserve_context", False):
                    strategy = CompressionStrategy.CONSERVATIVE
                elif user_preferences.get("optimize_cost", False):
                    strategy = CompressionStrategy.AGGRESSIVE
            
            # Compress messages
            compression_result = await memory_compressor.compress_conversation(
                messages, strategy
            )
            
            # Update context with compressed messages
            full_context["dynamic_context"]["conversation_messages"] = compression_result.compressed_messages
            full_context["compression_metadata"] = compression_result.metadata
            
            logger.info(f"Compressed context: {compression_result.compression_ratio:.2%} ratio, "
                       f"quality score: {compression_result.quality_score:.2f}")
        
        return full_context
        
    except Exception as e:
        logger.error(f"Error optimizing context: {e}")
        # Fallback to basic context
        return await memory.get_caching_optimized_context(thread_id)

async def get_cached_response(cache_key: str) -> Optional[str]:
    """
    Attempt to get cached response for identical requests.
    
    Args:
        cache_key: Unique key for the request
        
    Returns:
        Cached response or None if not found
    """
    try:
        if await redis_service.health_check():
            cached_data = await redis_service.get_cache(cache_key)
            if cached_data and isinstance(cached_data, dict):
                response = cached_data.get("response")
                if response:
                    logger.info(f"Cache HIT for request: {cache_key}")
                    return response
    except Exception as e:
        logger.error(f"Error retrieving cached response: {e}")
    
    return None

async def cache_response(cache_key: str, response: str, ttl: int = 300) -> None:
    """
    Cache response for future identical requests.
    
    Args:
        cache_key: Unique key for the request
        response: Response to cache
        ttl: Time to live in seconds
    """
    try:
        if await redis_service.health_check():
            cache_data = {
                "response": response,
                "cached_at": datetime.now().isoformat(),
                "ttl": ttl
            }
            await redis_service.set_cache(cache_key, cache_data, ttl)
            logger.debug(f"Cached response: {cache_key}")
    except Exception as e:
        logger.error(f"Error caching response: {e}")

def generate_cache_key(user_input: str, user_id: str, context_hash: str) -> str:
    """
    Generate cache key for request caching.
    
    Args:
        user_input: User's input message
        user_id: User identifier
        context_hash: Hash of conversation context
        
    Returns:
        Unique cache key
    """
    import hashlib
    
    # Create hash from input and context
    content = f"{user_input}:{user_id}:{context_hash}"
    hash_object = hashlib.md5(content.encode())
    return f"wingman:response:{hash_object.hexdigest()}"

async def interact_with_agent_optimized(
    user_input: str, 
    user_id: str, 
    user_timezone: str,
    thread_id: str,
    supabase_client,
    context: Dict[str, Any],
    user_preferences: Optional[Dict[str, Any]] = None
) -> str:
    """
    Process user input using optimized Claude client with model routing and caching.
    
    Args:
        user_input: User's message
        user_id: User identifier
        user_timezone: User's timezone
        thread_id: Thread identifier
        supabase_client: Supabase client instance
        context: Conversation context
        user_preferences: User-specific preferences
        
    Returns:
        Assistant response
    """
    try:
        logger.info(f"Processing optimized input for user {user_id}")
        logger.info(f"User Input: {user_input}")
        
        # Get memory instance
        memory = SimpleMemory(supabase_client, user_id)
        
        # Get optimized context with compression
        optimized_context = await get_optimized_context(memory, thread_id, user_preferences)
        
        # Generate cache key for response caching
        context_hash = str(hash(str(optimized_context)))
        cache_key = generate_cache_key(user_input, user_id, context_hash)
        
        # Try to get cached response first
        cached_response = await get_cached_response(cache_key)
        if cached_response:
            return cached_response
        
        # Get conversation history for model routing
        conversation_messages = optimized_context["dynamic_context"]["conversation_messages"]
        recent_messages = [msg.get("content", "") for msg in conversation_messages[-5:]]
        
        # Route to optimal model based on conversation type
        routing_decision = get_optimal_model(user_input, recent_messages, user_preferences)
        
        logger.info(f"Model routing: {routing_decision.model_name} ({routing_decision.tier.value}) "
                   f"for {routing_decision.conversation_type.value} "
                   f"(confidence: {routing_decision.confidence:.2f})")
        
        # Get Anthropic client
        anthropic_client = await get_anthropic_client()
        
        # Use optimized context formatter for better caching
        cached_context = format_static_context_for_caching(optimized_context["static_context"])
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
        
        # Add conversation history (potentially compressed)
        for msg in conversation_messages:
            chat_messages.append({
                "role": msg["role"], 
                "content": msg["content"]
            })
        
        # Add current user input
        chat_messages.append({
            "role": "user", 
            "content": user_input
        })
        
        logger.info(f"Sending {len(chat_messages)} messages to {routing_decision.model_name}")
        
        # Get personalized system prompt based on user's archetype
        system_prompt, base_temperature = await get_personalized_system_prompt(
            user_id, user_timezone, memory
        )
        
        # Get model configuration from routing decision
        model_config = model_router.get_model_config(routing_decision.tier)
        
        # Use model-specific temperature or archetype temperature
        temperature = model_config.get("temperature", base_temperature)
        max_tokens = model_config.get("max_tokens", 4000)
        
        # Make request to Claude with optimized model and settings
        try:
            response = await anthropic_client.messages.create(
                model=routing_decision.model_name,
                max_tokens=max_tokens,
                temperature=temperature,
                extra_headers=cache_headers,  # Include cache headers
                system=system_prompt,  # Use personalized system prompt
                messages=chat_messages
            )
            
            # Extract response content
            assistant_response = ""
            for block in response.content:
                if hasattr(block, 'text'):
                    assistant_response += block.text
            
            # Log performance metrics
            if hasattr(response, 'usage'):
                logger.info(f"Model: {routing_decision.model_name}, "
                          f"Tokens: {response.usage.input_tokens + response.usage.output_tokens}, "
                          f"Cost factor: {routing_decision.estimated_cost_factor:.2f}")
                
                # Log cache usage if available
                if hasattr(response.usage, 'cache_creation_input_tokens'):
                    logger.info(f"Cache usage: creation={response.usage.cache_creation_input_tokens}, "
                              f"read={response.usage.cache_read_input_tokens}")
            
            # Cache the response for future identical requests
            await cache_response(cache_key, assistant_response, ttl=300)  # 5 minutes
            
            logger.info(f"Received response from {routing_decision.model_name}: {len(assistant_response)} characters")
            return assistant_response
            
        except Exception as claude_error:
            logger.error(f"Claude API error with {routing_decision.model_name}: {str(claude_error)}")
            
            # Fallback to standard model if routing fails
            if routing_decision.model_name != "claude-3-5-sonnet-20241022":
                logger.info("Falling back to standard model")
                response = await anthropic_client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=4000,
                    temperature=base_temperature,
                    system=system_prompt,
                    messages=chat_messages
                )
                
                assistant_response = ""
                for block in response.content:
                    if hasattr(block, 'text'):
                        assistant_response += block.text
                
                return assistant_response
            else:
                return "I'm experiencing some technical difficulties. Please try again in a moment."
            
    except Exception as e:
        logger.error(f"Error in interact_with_agent_optimized: {str(e)}", exc_info=True)
        return "I apologize, but I'm having trouble processing your request right now. Please try again."

async def interact_with_agent_stream_optimized(
    user_input: str, 
    user_id: str, 
    user_timezone: str,
    thread_id: str,
    supabase_client,
    context: Dict[str, Any],
    user_preferences: Optional[Dict[str, Any]] = None
) -> AsyncGenerator[str, None]:
    """
    Process user input with streaming response using optimized model routing.
    
    Args:
        user_input: User's message
        user_id: User identifier
        user_timezone: User's timezone
        thread_id: Thread identifier
        supabase_client: Supabase client instance
        context: Conversation context
        user_preferences: User-specific preferences
        
    Yields:
        Response chunks as they arrive
    """
    try:
        logger.info(f"Processing optimized streaming input for user {user_id}")
        
        # Get memory instance
        memory = SimpleMemory(supabase_client, user_id)
        
        # Get optimized context with compression
        optimized_context = await get_optimized_context(memory, thread_id, user_preferences)
        
        # Get conversation history for model routing
        conversation_messages = optimized_context["dynamic_context"]["conversation_messages"]
        recent_messages = [msg.get("content", "") for msg in conversation_messages[-5:]]
        
        # Route to optimal model based on conversation type
        routing_decision = get_optimal_model(user_input, recent_messages, user_preferences)
        
        logger.info(f"Streaming with model: {routing_decision.model_name} ({routing_decision.tier.value})")
        
        # Get Anthropic client
        anthropic_client = await get_anthropic_client()
        
        # Use optimized context formatter for better caching
        cached_context = format_static_context_for_caching(optimized_context["static_context"])
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
        
        # Add conversation history (potentially compressed)
        for msg in conversation_messages:
            chat_messages.append({
                "role": msg["role"], 
                "content": msg["content"]
            })
        
        # Add current user input
        chat_messages.append({
            "role": "user", 
            "content": user_input
        })
        
        logger.info(f"Streaming {len(chat_messages)} messages to {routing_decision.model_name}")
        
        # Get personalized system prompt based on user's archetype
        system_prompt, base_temperature = await get_personalized_system_prompt(
            user_id, user_timezone, memory
        )
        
        # Get model configuration from routing decision
        model_config = model_router.get_model_config(routing_decision.tier)
        
        # Use model-specific temperature or archetype temperature
        temperature = model_config.get("temperature", base_temperature)
        max_tokens = model_config.get("max_tokens", 4000)
        
        # Make streaming request to Claude with optimized model
        try:
            stream = await anthropic_client.messages.create(
                model=routing_decision.model_name,
                max_tokens=max_tokens,
                temperature=temperature,
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
            logger.error(f"Claude streaming API error with {routing_decision.model_name}: {str(claude_error)}")
            
            # Fallback to standard model if routing fails
            if routing_decision.model_name != "claude-3-5-sonnet-20241022":
                logger.info("Falling back to standard model for streaming")
                try:
                    stream = await anthropic_client.messages.create(
                        model="claude-3-5-sonnet-20241022",
                        max_tokens=4000,
                        temperature=base_temperature,
                        system=system_prompt,
                        messages=chat_messages,
                        stream=True
                    )
                    
                    async for event in stream:
                        if hasattr(event, 'delta') and hasattr(event.delta, 'text'):
                            yield event.delta.text
                except Exception as fallback_error:
                    logger.error(f"Fallback streaming error: {fallback_error}")
                    yield "I'm experiencing some technical difficulties. Please try again in a moment."
            else:
                yield "I'm experiencing some technical difficulties. Please try again in a moment."
            
    except Exception as e:
        logger.error(f"Error in interact_with_agent_stream_optimized: {str(e)}", exc_info=True)
        yield "I apologize, but I'm having trouble processing your request right now. Please try again."

async def get_performance_stats() -> Dict[str, Any]:
    """
    Get comprehensive performance statistics for monitoring.
    
    Returns:
        Dictionary with performance metrics
    """
    try:
        # Get model router stats
        router_stats = model_router.get_usage_stats()
        
        # Get memory compressor stats
        compressor_stats = memory_compressor.get_compression_stats()
        
        # Get Redis stats
        redis_stats = await redis_service.get_stats()
        
        return {
            "model_routing": router_stats,
            "memory_compression": compressor_stats,
            "redis_cache": redis_stats,
            "optimization_enabled": True,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting performance stats: {e}")
        return {
            "error": str(e),
            "optimization_enabled": False,
            "timestamp": datetime.now().isoformat()
        }

# Backwards compatibility functions

async def interact_with_agent(
    user_input: str, 
    user_id: str, 
    user_timezone: str,
    thread_id: str,
    supabase_client,
    context: Dict[str, Any]
) -> str:
    """Backwards compatible non-streaming interaction (uses optimization)"""
    return await interact_with_agent_optimized(
        user_input, user_id, user_timezone, thread_id, supabase_client, context
    )

async def interact_with_agent_stream(
    user_input: str, 
    user_id: str, 
    user_timezone: str,
    thread_id: str,
    supabase_client,
    context: Dict[str, Any]
) -> AsyncGenerator[str, None]:
    """Backwards compatible streaming interaction (uses optimization)"""
    async for chunk in interact_with_agent_stream_optimized(
        user_input, user_id, user_timezone, thread_id, supabase_client, context
    ):
        yield chunk

async def store_conversation_in_memory(supabase_client, user_id: str, thread_id: str, user_input: str, assistant_response: str):
    """Store completed conversation in memory"""
    try:
        memory = SimpleMemory(supabase_client, user_id)
        logger.info(f"Successfully stored optimized conversation in memory for thread {thread_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to store conversation in memory: {str(e)}")
        return False