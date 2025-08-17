#!/usr/bin/env python3
"""
Universal LLM Router
Provides fallback between Anthropic Claude and OpenAI GPT APIs
"""

import os
import logging
import json
from typing import Dict, List, Any, Optional, AsyncGenerator, Union
from datetime import datetime, timezone
from anthropic import AsyncAnthropic, RateLimitError as AnthropicRateLimitError
from openai import AsyncOpenAI, RateLimitError as OpenAIRateLimitError
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
load_dotenv()

class UsageTracker:
    """Track LLM provider usage for Streamlit monitoring"""
    
    def __init__(self):
        self.usage_stats = {
            "anthropic_calls": 0,
            "openai_calls": 0,
            "anthropic_failures": 0,
            "openai_failures": 0,
            "last_fallback": None,
            "total_calls": 0,
            "session_start": datetime.now(timezone.utc).isoformat()
        }
        
    def record_anthropic_success(self):
        """Record successful Anthropic call"""
        self.usage_stats["anthropic_calls"] += 1
        self.usage_stats["total_calls"] += 1
        
    def record_openai_success(self):
        """Record successful OpenAI call (fallback)"""
        self.usage_stats["openai_calls"] += 1
        self.usage_stats["total_calls"] += 1
        self.usage_stats["last_fallback"] = datetime.now(timezone.utc).isoformat()
        
    def record_anthropic_failure(self, error_type: str):
        """Record Anthropic failure"""
        self.usage_stats["anthropic_failures"] += 1
        
    def record_openai_failure(self):
        """Record OpenAI failure"""  
        self.usage_stats["openai_failures"] += 1
        
    def get_stats(self) -> Dict[str, Any]:
        """Get current usage statistics for Streamlit"""
        stats = self.usage_stats.copy()
        stats["anthropic_success_rate"] = (
            stats["anthropic_calls"] / max(1, stats["anthropic_calls"] + stats["anthropic_failures"])
        )
        stats["openai_usage_percentage"] = (
            stats["openai_calls"] / max(1, stats["total_calls"]) * 100
        )
        return stats
        
    def should_alert(self) -> bool:
        """Check if Streamlit should send an alert"""
        # Alert if OpenAI usage > 10% or recent fallback
        recent_fallback = False
        if self.usage_stats["last_fallback"]:
            fallback_time = datetime.fromisoformat(self.usage_stats["last_fallback"].replace('Z', '+00:00'))
            recent_fallback = (datetime.now(timezone.utc) - fallback_time).seconds < 300  # 5 minutes
            
        high_openai_usage = (self.usage_stats["openai_calls"] / max(1, self.usage_stats["total_calls"])) > 0.1
        
        return recent_fallback or high_openai_usage

class LLMRouter:
    """Universal router for LLM APIs with automatic fallback and usage tracking"""
    
    def __init__(self):
        """Initialize both Anthropic and OpenAI clients"""
        self.anthropic_client = None
        self.openai_client = None
        self.usage_tracker = UsageTracker()
        
        # Model mapping: Anthropic -> OpenAI
        self.model_mapping = {
            "claude-sonnet-4-20250514": "gpt-4o",
            "claude-sonnet-4-20250514": "gpt-4o", 
            "claude-3-haiku-20240307": "gpt-4o-mini",
            "claude-3-opus-20240229": "gpt-4-turbo"
        }
        
        # Track which provider we're using for logging
        self.last_provider_used = None
        
    async def _get_anthropic_client(self) -> AsyncAnthropic:
        """Get or create Anthropic client (lazy loading)"""
        if self.anthropic_client is None:
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY environment variable required")
            self.anthropic_client = AsyncAnthropic(api_key=api_key)
        return self.anthropic_client
    
    async def _get_openai_client(self) -> AsyncOpenAI:
        """Get or create OpenAI client (lazy loading)"""
        if self.openai_client is None:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable required")
            self.openai_client = AsyncOpenAI(api_key=api_key)
        return self.openai_client
    
    def _prepare_anthropic_request(
        self, 
        messages: List[Dict[str, str]], 
        system: Optional[str] = None,
        model: str = "claude-3-5-sonnet-20241022",
        extra_headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Prepare request for Anthropic API"""
        request = {
            "model": model,
            "messages": messages,
            **kwargs  # max_tokens, temperature, etc.
        }
        
        # Add system prompt if provided
        if system:
            request["system"] = system
            
        # Add extra headers if provided (for caching)
        if extra_headers:
            request["extra_headers"] = extra_headers
            
        return request
    
    def _prepare_openai_request(
        self,
        messages: List[Dict[str, str]],
        system: Optional[str] = None, 
        model: str = "claude-3-5-sonnet-20241022",
        extra_headers: Optional[Dict[str, str]] = None,  # Ignored for OpenAI
        **kwargs
    ) -> Dict[str, Any]:
        """Prepare request for OpenAI API"""
        # Map Claude model to OpenAI model
        openai_model = self.model_mapping.get(model, "gpt-4o")
        
        # Build messages array (OpenAI puts system in messages)
        openai_messages = []
        
        # Add system message first if provided
        if system:
            openai_messages.append({"role": "system", "content": system})
            
        # Add conversation messages
        openai_messages.extend(messages)
        
        request = {
            "model": openai_model,
            "messages": openai_messages,
            **kwargs  # max_tokens, temperature, etc.
        }
        
        return request
    
    async def _anthropic_call(
        self,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        model: str = "claude-3-5-sonnet-20241022", 
        stream: bool = False,
        **kwargs
    ) -> Union[str, AsyncGenerator[str, None]]:
        """Make API call to Anthropic"""
        try:
            client = await self._get_anthropic_client()
            request = self._prepare_anthropic_request(
                messages=messages,
                system=system,
                model=model,
                **kwargs
            )
            
            if stream:
                return self._anthropic_stream(client, request)
            else:
                response = await client.messages.create(**request)
                self.last_provider_used = "anthropic"
                self.usage_tracker.record_anthropic_success()
                logger.info("✅ Anthropic API call successful")
                return response.content[0].text if response.content else ""
                
        except Exception as e:
            self.usage_tracker.record_anthropic_failure(type(e).__name__)
            logger.error(f"Anthropic API call failed: {e}")
            raise
    
    async def _anthropic_stream(self, client: AsyncAnthropic, request: Dict[str, Any]) -> AsyncGenerator[str, None]:
        """Stream response from Anthropic"""
        async with client.messages.stream(**request) as stream:
            async for text in stream.text_stream:
                yield text
        self.last_provider_used = "anthropic"
        self.usage_tracker.record_anthropic_success()
        logger.info("✅ Anthropic streaming call successful")
    
    async def _openai_call(
        self,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        model: str = "claude-3-5-sonnet-20241022",
        stream: bool = False,
        **kwargs
    ) -> Union[str, AsyncGenerator[str, None]]:
        """Make API call to OpenAI"""
        try:
            client = await self._get_openai_client()
            request = self._prepare_openai_request(
                messages=messages,
                system=system,
                model=model,
                **kwargs
            )
            
            if stream:
                return self._openai_stream(client, request)
            else:
                response = await client.chat.completions.create(**request)
                self.last_provider_used = "openai"
                self.usage_tracker.record_openai_success()
                logger.info(f"🔄 OpenAI API call successful (fallback from Anthropic)")
                return response.choices[0].message.content if response.choices else ""
                
        except Exception as e:
            self.usage_tracker.record_openai_failure()
            logger.error(f"OpenAI API call failed: {e}")
            raise
    
    async def _openai_stream(self, client: AsyncOpenAI, request: Dict[str, Any]) -> AsyncGenerator[str, None]:
        """Stream response from OpenAI"""
        stream = await client.chat.completions.create(**request, stream=True)
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
        self.last_provider_used = "openai"
        self.usage_tracker.record_openai_success()
        logger.info("🔄 OpenAI streaming call successful (fallback from Anthropic)")
    
    async def send_message(
        self,
        messages: Optional[List[Dict[str, str]]] = None,
        system: Optional[str] = None,
        model: str = "claude-3-5-sonnet-20241022",
        max_tokens: int = 4000,
        temperature: float = 0.5,
        stream: bool = False,
        extra_headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> Union[str, AsyncGenerator[str, None]]:
        """
        Universal interface for sending messages to LLMs
        
        Args:
            messages: List of conversation messages
            system: System prompt (optional)
            model: Model name (Claude format, will map to OpenAI if needed)
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            stream: Whether to stream response
            extra_headers: Additional headers (Anthropic-specific, ignored for OpenAI)
            **kwargs: Additional parameters passed to API
            
        Returns:
            String response or AsyncGenerator for streaming
        """
        if messages is None:
            messages = []
            
        # Prepare common parameters
        call_params = {
            "messages": messages,
            "system": system,
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": stream,
            "extra_headers": extra_headers,
            **kwargs
        }
        
        try:
            # Always try Anthropic first (preserves caching benefits)
            logger.info("🚀 Attempting Anthropic API call...")
            return await self._anthropic_call(**call_params)
            
        except AnthropicRateLimitError as e:
            # Rate limit hit - fall back to OpenAI
            logger.warning(f"⚠️ Anthropic rate limit hit, falling back to OpenAI: {e}")
            return await self._openai_call(**call_params)
            
        except Exception as e:
            # Other Anthropic errors - try OpenAI as fallback
            logger.warning(f"⚠️ Anthropic API error, trying OpenAI fallback: {e}")
            try:
                return await self._openai_call(**call_params)
            except Exception as openai_error:
                # Both failed - raise the original Anthropic error
                logger.error(f"❌ Both Anthropic and OpenAI failed. Anthropic: {e}, OpenAI: {openai_error}")
                raise e
    
    def get_last_provider(self) -> Optional[str]:
        """Get the last provider used for the API call"""
        return self.last_provider_used
    
    # === STREAMLIT MONITORING INTERFACE ===
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics for Streamlit dashboard"""
        return self.usage_tracker.get_stats()
    
    def should_send_alert(self) -> bool:
        """Check if Streamlit should send an alert"""
        return self.usage_tracker.should_alert()
    
    def reset_stats(self):
        """Reset usage statistics (for testing or daily resets)"""
        self.usage_tracker = UsageTracker()


# === GLOBAL ROUTER INSTANCE ===
_router_instance = None

async def get_router() -> LLMRouter:
    """Get or create router instance (singleton pattern)"""
    global _router_instance
    if _router_instance is None:
        _router_instance = LLMRouter()
    return _router_instance

async def send_llm_message(
    messages: List[Dict[str, str]],
    system: Optional[str] = None,
    **kwargs
) -> Union[str, AsyncGenerator[str, None]]:
    """Convenience function for sending messages"""
    router = await get_router()
    return await router.send_message(messages=messages, system=system, **kwargs)

# === STREAMLIT INTERFACE FUNCTIONS ===

async def get_llm_usage_stats() -> Dict[str, Any]:
    """Get LLM usage statistics for Streamlit monitoring"""
    router = await get_router()
    return router.get_usage_stats()

async def check_llm_alert_needed() -> bool:
    """Check if Streamlit should send an alert about LLM usage"""
    router = await get_router()
    return router.should_send_alert()

async def reset_llm_stats():
    """Reset LLM usage statistics"""
    router = await get_router()
    router.reset_stats() 