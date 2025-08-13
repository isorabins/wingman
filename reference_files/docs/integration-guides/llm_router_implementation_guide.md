# Universal LLM Router Implementation Guide

## Overview
This guide implements a universal LLM router that provides automatic fallback from Anthropic Claude to OpenAI GPT when rate limits are hit. The router preserves all existing functionality including Claude's prompt caching while adding resilience and usage monitoring for Streamlit dashboards.

## Key Benefits
- ✅ **Preserves 82% cost savings** from Claude caching when available
- ✅ **Zero downtime** during Anthropic rate limits 
- ✅ **Seamless fallback** to OpenAI GPT-4o
- ✅ **Usage monitoring** for Streamlit alerts
- ✅ **Same API interface** - minimal code changes

---

## Step 1: Install Dependencies

Add these to your `requirements.txt`:

```txt
# Existing dependencies remain
anthropic>=0.39.0
openai>=1.0.0
python-dotenv>=1.0.0
```

Run: `pip install openai>=1.0.0`

---

## Step 2: Environment Variables

Add to your `.env` file:

```bash
# Existing
ANTHROPIC_API_KEY=sk-ant-...
SUPABASE_URL=https://...
SUPABASE_KEY=...

# NEW - Add this
OPENAI_API_KEY=sk-...
```

**Important**: Get your OpenAI API key from https://platform.openai.com/api-keys

---

## Step 3: Create New File - `src/llm_router.py`

Create this exact file at `src/llm_router.py`:

```python
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
            "claude-3-5-sonnet-20241022": "gpt-4o",
            "claude-3-5-sonnet-20241010": "gpt-4o", 
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
```

---

## Step 4: Update `src/claude_agent.py`

### Change 1: Add Import
**Location**: Top of file, around line 14
**Find**: `from anthropic import AsyncAnthropic`
**Add after**:
```python
from src.llm_router import get_router
```

### Change 2: Replace Non-Streaming API Call
**Location**: Around lines 289-301
**Find**:
```python
# Get Anthropic client and send message with prompt caching
anthropic_client = await get_anthropic_client()
        
# Get cache headers and log them
cache_headers = get_cache_control_header()
logger.info(f"🔄 [CACHE DEBUG] Cache control headers being sent: {cache_headers}")
logger.info(f"🔄 [CACHE DEBUG] System prompt size: {len(system_prompt)} characters")
logger.info(f"🔄 [CACHE DEBUG] This system prompt should be cached by Claude")

response = await anthropic_client.messages.create(
    model=Config.ANTHROPIC_MODEL or "claude-3-5-sonnet-20241022",
    system=system_prompt,           # ← This gets cached!
    messages=conversation_messages,  # ← This is dynamic (not cached)
    max_tokens=4000,
    temperature=0.5,
    extra_headers=cache_headers  # ← Enable prompt caching
)

# Log cache usage information from response
logger.info(f"✅ [CACHE DEBUG] Response received from Claude")
logger.info(f"✅ [CACHE DEBUG] Response ID: {response.id}")
logger.info(f"✅ [CACHE DEBUG] Model used: {response.model}")

# Check if usage information is available (includes cache metrics)
if hasattr(response, 'usage') and response.usage:
    usage = response.usage
    logger.info(f"📊 [CACHE METRICS] Input tokens: {usage.input_tokens}")
    logger.info(f"📊 [CACHE METRICS] Output tokens: {usage.output_tokens}")
    
    # Check for cache creation/hits
    if hasattr(usage, 'cache_creation_input_tokens'):
        logger.info(f"🆕 [CACHE METRICS] Cache creation tokens: {usage.cache_creation_input_tokens}")
    if hasattr(usage, 'cache_read_input_tokens'):
        logger.info(f"⚡ [CACHE METRICS] Cache read tokens: {usage.cache_read_input_tokens}")
else:
    logger.info(f"📊 [CACHE METRICS] No usage information available in response")

# Extract response content
response_content = response.content[0].text if response.content else "No response"
```

**Replace with**:
```python
# Get router and send message with prompt caching
router = await get_router()
        
# Get cache headers and log them
cache_headers = get_cache_control_header()
logger.info(f"🔄 [CACHE DEBUG] Cache control headers being sent: {cache_headers}")
logger.info(f"🔄 [CACHE DEBUG] System prompt size: {len(system_prompt)} characters")
logger.info(f"🔄 [CACHE DEBUG] This system prompt should be cached by Claude")

response_content = await router.send_message(
    messages=conversation_messages,
    system=system_prompt,           # ← This gets cached when using Anthropic!
    model=Config.ANTHROPIC_MODEL or "claude-3-5-sonnet-20241022",
    max_tokens=4000,
    temperature=0.5,
    extra_headers=cache_headers  # ← Enable prompt caching for Anthropic
)

logger.info(f"✅ [CACHE DEBUG] Response received from {router.get_last_provider()}")
logger.info(f"✅ [CACHE DEBUG] Response length: {len(response_content)} characters")
```

### Change 3: Replace Streaming API Call
**Location**: Around lines 365-395
**Find**:
```python
# Get cache headers and log them for streaming
cache_headers = get_cache_control_header()
logger.info(f"🔄 [STREAM CACHE DEBUG] Cache control headers being sent: {cache_headers}")
logger.info(f"🔄 [STREAM CACHE DEBUG] System prompt size: {len(system_prompt)} characters")
logger.info(f"🔄 [STREAM CACHE DEBUG] This system prompt should be cached by Claude")

async with anthropic_client.messages.stream(
    model=Config.ANTHROPIC_MODEL or "claude-3-5-sonnet-20241022",
    system=system_prompt,           # ← Cached!
    messages=conversation_messages,  # ← Not cached
    max_tokens=4000,
    temperature=0.5,
    extra_headers=cache_headers  # ← Enable caching
) as stream:
    # Log streaming response details
    logger.info(f"✅ [STREAM CACHE DEBUG] Streaming response started")
    
    async for text in stream.text_stream:
        full_response += text
        yield text
    
    # Log final stream information if available
    if hasattr(stream, '_response') and stream._response:
        response = stream._response
        logger.info(f"✅ [STREAM CACHE DEBUG] Stream completed, Response ID: {response.id}")
        
        # Check for cache usage in streaming response
        if hasattr(response, 'usage') and response.usage:
            usage = response.usage
            logger.info(f"📊 [STREAM CACHE METRICS] Input tokens: {usage.input_tokens}")
            logger.info(f"📊 [STREAM CACHE METRICS] Output tokens: {usage.output_tokens}")
            
            if hasattr(usage, 'cache_creation_input_tokens'):
                logger.info(f"🆕 [STREAM CACHE METRICS] Cache creation tokens: {usage.cache_creation_input_tokens}")
            if hasattr(usage, 'cache_read_input_tokens'):
                logger.info(f"⚡ [STREAM CACHE METRICS] Cache read tokens: {usage.cache_read_input_tokens}")
        else:
            logger.info(f"📊 [STREAM CACHE METRICS] No usage information available")
    else:
        logger.info(f"📊 [STREAM CACHE METRICS] Stream response object not accessible")
```

**Replace with**:
```python
# Get router and send streaming message with prompt caching
router = await get_router()

# Get cache headers and log them for streaming
cache_headers = get_cache_control_header()
logger.info(f"🔄 [STREAM CACHE DEBUG] Cache control headers being sent: {cache_headers}")
logger.info(f"🔄 [STREAM CACHE DEBUG] System prompt size: {len(system_prompt)} characters")
logger.info(f"🔄 [STREAM CACHE DEBUG] This system prompt should be cached by Claude")

# Stream response using router
stream_generator = await router.send_message(
    messages=conversation_messages,
    system=system_prompt,           # ← Cached when using Anthropic!
    model=Config.ANTHROPIC_MODEL or "claude-3-5-sonnet-20241022",
    max_tokens=4000,
    temperature=0.5,
    extra_headers=cache_headers,  # ← Enable caching for Anthropic
    stream=True
)

logger.info(f"✅ [STREAM CACHE DEBUG] Streaming response started using {router.get_last_provider()}")

async for text in stream_generator:
    full_response += text
    yield text

logger.info(f"✅ [STREAM CACHE DEBUG] Stream completed using {router.get_last_provider()}")
```

---

## Step 5: Update `src/content_summarizer.py`

### Change 1: Add Import  
**Location**: Top of file, around line 33
**Find**: `from src.claude_client_simple import SimpleClaudeClient, ClaudeCredentials`
**Replace with**:
```python
from src.llm_router import get_router
```

### Change 2: Update ContentSummarizer Class
**Location**: Around line 104
**Find**:
```python
class ContentSummarizer:
    def __init__(self, model: str = "claude-3-5-sonnet-20241022", map_prompt=None, reduce_prompt=None):
        # Use our Claude client instead of ChatOpenAI
        self.claude_client = None  # Will be initialized on first use (lazy loading)
        self.model_name = model
        
        # Use our simple text splitter instead of LangChain's
        self.text_splitter = SimpleTextSplitter(
            chunk_size=4000,
            chunk_overlap=200
        )
        
        self.map_prompt = map_prompt or MAP_PROMPT
        self.reduce_prompt = reduce_prompt or REDUCE_PROMPT
        
        # No need for setup_chain since we'll use direct async functions
    
    async def _get_claude_client(self) -> SimpleClaudeClient:
        """Get Claude client (lazy initialization)"""
        if self.claude_client is None:
            credentials = ClaudeCredentials()
            self.claude_client = SimpleClaudeClient(credentials)
        return self.claude_client
```

**Replace with**:
```python
class ContentSummarizer:
    def __init__(self, model: str = "claude-3-5-sonnet-20241022", map_prompt=None, reduce_prompt=None):
        # Use router instead of direct Claude client
        self.model_name = model
        
        # Use our simple text splitter instead of LangChain's
        self.text_splitter = SimpleTextSplitter(
            chunk_size=4000,
            chunk_overlap=200
        )
        
        self.map_prompt = map_prompt or MAP_PROMPT
        self.reduce_prompt = reduce_prompt or REDUCE_PROMPT
        
        # No need for setup_chain since we'll use direct async functions
```

### Change 3: Update _map_chunk Method
**Location**: Around line 126
**Find**:
```python
async def _map_chunk(self, chunk: str) -> str:
    """Process a single chunk with the map prompt"""
    try:
        claude_client = await self._get_claude_client()
        
        # Replace {content} placeholder in map_prompt
        prompt_with_content = self.map_prompt.replace("{content}", chunk)
        
        messages = [
            {"role": "user", "content": prompt_with_content}
        ]
        
        response = await claude_client.send_message(
            messages=messages,
            model=self.model_name,
            max_tokens=4000,
            temperature=0.3,
            stream=False
        )
        
        logger.info(f"MAP_PROMPT output for chunk: {response[:200]}...")
        return response
        
    except Exception as e:
        logger.error(f"Error processing chunk: {e}")
        return f"Error processing chunk: {str(e)}"
```

**Replace with**:
```python
async def _map_chunk(self, chunk: str) -> str:
    """Process a single chunk with the map prompt"""
    try:
        router = await get_router()
        
        # Replace {content} placeholder in map_prompt
        prompt_with_content = self.map_prompt.replace("{content}", chunk)
        
        messages = [
            {"role": "user", "content": prompt_with_content}
        ]
        
        response = await router.send_message(
            messages=messages,
            model=self.model_name,
            max_tokens=4000,
            temperature=0.3,
            stream=False
        )
        
        logger.info(f"MAP_PROMPT output for chunk: {response[:200]}...")
        return response
        
    except Exception as e:
        logger.error(f"Error processing chunk: {e}")
        return f"Error processing chunk: {str(e)}"
```

### Change 4: Update _reduce_summaries Method
**Location**: Around line 153
**Find**:
```python
async def _reduce_summaries(self, summaries: List[str]) -> str:
    """Combine summaries with the reduce prompt"""
    try:
        claude_client = await self._get_claude_client()
        
        # Combine all summaries
        combined_summaries = "\n\n".join(summaries)
        
        # Replace {content} placeholder in reduce_prompt
        prompt_with_content = self.reduce_prompt.replace("{content}", combined_summaries)
        
        messages = [
            {"role": "user", "content": prompt_with_content}
        ]
        
        response = await claude_client.send_message(
            messages=messages,
            model=self.model_name,
            max_tokens=4000,
            temperature=0.3,
            stream=False
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Error reducing summaries: {e}")
        return f"Error reducing summaries: {str(e)}"
```

**Replace with**:
```python
async def _reduce_summaries(self, summaries: List[str]) -> str:
    """Combine summaries with the reduce prompt"""
    try:
        router = await get_router()
        
        # Combine all summaries
        combined_summaries = "\n\n".join(summaries)
        
        # Replace {content} placeholder in reduce_prompt
        prompt_with_content = self.reduce_prompt.replace("{content}", combined_summaries)
        
        messages = [
            {"role": "user", "content": prompt_with_content}
        ]
        
        response = await router.send_message(
            messages=messages,
            model=self.model_name,
            max_tokens=4000,
            temperature=0.3,
            stream=False
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Error reducing summaries: {e}")
        return f"Error reducing summaries: {str(e)}"
```

### Change 5: Update analyze_quality Method
**Location**: Around line 231
**Find**:
```python
async def analyze_quality(self, content: str) -> Dict[str, Any]:
    """Generate quality metrics for conversation content using Claude"""
    try:
        # Get Claude client directly for quality analysis
        claude_client = await self.summarizer._get_claude_client()
        
        # Replace {content} placeholder in quality analysis prompt
        prompt_with_content = QUALITY_ANALYSIS_PROMPT.replace("{content}", content)
        
        messages = [
            {"role": "user", "content": prompt_with_content}
        ]
        
        result = await claude_client.send_message(
            messages=messages,
            model="claude-3-5-sonnet-20241022",
            max_tokens=4000,
            temperature=0.1,
            stream=False
        )
```

**Replace with**:
```python
async def analyze_quality(self, content: str) -> Dict[str, Any]:
    """Generate quality metrics for conversation content using Claude"""
    try:
        # Get router for quality analysis
        router = await get_router()
        
        # Replace {content} placeholder in quality analysis prompt
        prompt_with_content = QUALITY_ANALYSIS_PROMPT.replace("{content}", content)
        
        messages = [
            {"role": "user", "content": prompt_with_content}
        ]
        
        result = await router.send_message(
            messages=messages,
            model="claude-3-5-sonnet-20241022",
            max_tokens=4000,
            temperature=0.1,
            stream=False
        )
```

---

## Step 6: Streamlit Integration (Optional)

If you want to monitor LLM usage in your Streamlit app, add this code:

```python
# In your Streamlit app
import asyncio
from src.llm_router import get_llm_usage_stats, check_llm_alert_needed, reset_llm_stats

# Get usage statistics
async def get_stats():
    return await get_llm_usage_stats()

stats = asyncio.run(get_stats())

# Display in Streamlit
st.metric("Anthropic Calls", stats['anthropic_calls'])
st.metric("OpenAI Calls", stats['openai_calls'])
st.metric("OpenAI Usage %", f"{stats['openai_usage_percentage']:.1f}%")

# Check for alerts
async def check_alert():
    return await check_llm_alert_needed()

if asyncio.run(check_alert()):
    st.error("🚨 High OpenAI usage detected! Check Anthropic API status.")
```

---

## Step 7: Testing Instructions

### Test 1: Verify Normal Operation
```bash
# Run your app normally - should use Anthropic
python -m uvicorn src.main:app --reload

# Check logs for: "✅ Anthropic API call successful"
```

### Test 2: Test Fallback (Simulate Rate Limit)
```python
# Temporarily add to test fallback:
# In llm_router.py, add this to _anthropic_call:
# raise AnthropicRateLimitError("Test rate limit")

# Should see: "🔄 OpenAI API call successful (fallback from Anthropic)"
```

### Test 3: Verify Environment Variables
```python
# Test both API keys work
import os
print("Anthropic key:", os.getenv("ANTHROPIC_API_KEY")[:10] + "...")
print("OpenAI key:", os.getenv("OPENAI_API_KEY")[:10] + "...")
```

### Test 4: Check Usage Tracking
```python
# After a few API calls:
from src.llm_router import get_llm_usage_stats
import asyncio

stats = asyncio.run(get_llm_usage_stats())
print(f"Total calls: {stats['total_calls']}")
print(f"Anthropic: {stats['anthropic_calls']}")
print(f"OpenAI: {stats['openai_calls']}")
```

---

## Step 8: Cleanup (Optional)

After confirming the router works, you can optionally remove:
- `src/claude_client_simple.py` (no longer needed)
- The `get_anthropic_client()` function in `claude_agent.py` (no longer needed)

---

## Critical Success Criteria

✅ **App starts without errors**  
✅ **Normal conversations use Anthropic** (check logs for "✅ Anthropic API call successful")  
✅ **Fallback works during rate limits** (check logs for "🔄 OpenAI API call successful")  
✅ **Streaming still works** in both streaming endpoints  
✅ **Caching preserved** when using Anthropic (82% cost savings maintained)  
✅ **Usage tracking available** for Streamlit monitoring  

---

## Troubleshooting

**Error: "OPENAI_API_KEY not found"**
- Add OpenAI API key to `.env` file

**Error: "ImportError: No module named 'openai'"**  
- Run: `pip install openai>=1.0.0`

**Normal responses but no fallback during rate limits**
- Check that rate limit errors are correctly caught
- Verify OpenAI API key has credits

**Caching not working**
- This only affects Anthropic calls, fallback to OpenAI doesn't have caching
- Check that `extra_headers` are still being passed through

**Performance degradation**
- Should only occur during fallback scenarios (3-4 seconds vs 2 seconds)
- 99% of calls should still be ~2 seconds via Anthropic

---

## Implementation Priority

1. **Step 1-3**: Core setup (dependencies, env vars, router file)
2. **Step 4**: Update claude_agent.py (main conversation endpoint)
3. **Step 5**: Update content_summarizer.py (nightly summaries)
4. **Step 7**: Test thoroughly
5. **Step 6**: Add Streamlit monitoring (optional)
6. **Step 8**: Cleanup old files (optional)

This implementation preserves all existing functionality while adding resilience and monitoring capabilities. The router is designed to be transparent - your existing API interfaces remain unchanged.