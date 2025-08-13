# 🌊 Complete Streaming Implementation Template

*Based on Fridays at Four production-ready streaming architecture*

This document provides a complete, battle-tested streaming implementation that you can use as a template for any project requiring real-time AI responses. The architecture supports Claude API streaming with proper error handling, memory management, and frontend integration.

## 🏗️ Architecture Overview

```
Frontend (React/Next.js) → FastAPI Backend → Claude API → Streaming Response → Frontend Updates
```

**Key Components:**
1. **FastAPI Streaming Endpoint** - Server-Sent Events (SSE) with proper async handling
2. **Claude Client** - Direct Anthropic SDK integration with streaming support
3. **Memory System** - Conversation persistence with context optimization
4. **Frontend Client** - ReadableStream processing with accumulation logic
5. **Error Handling** - Comprehensive error recovery and graceful degradation

---

## 🔧 Backend Implementation

### 1. FastAPI Streaming Endpoint

```python
# main.py
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
import json
import logging

app = FastAPI()

# Enable CORS for streaming
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://yourapp.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    question: str
    user_id: str
    user_timezone: str = "UTC"
    thread_id: str = None

class QueryResponse(BaseModel):
    answer: str
    sources: list = []

logger = logging.getLogger(__name__)

# Memory handler storage (singleton pattern)
memory_handlers = {}

def get_memory_handler(user_id: str):
    """Get or create memory handler for user"""
    if user_id not in memory_handlers:
        from src.simple_memory import SimpleMemory
        memory_handlers[user_id] = SimpleMemory(supabase_client, user_id)
    return memory_handlers[user_id]

@app.post("/query_stream")
async def query_knowledge_base_stream(request: Request, query_request: QueryRequest):
    """
    Streaming endpoint using Server-Sent Events (SSE)
    
    Response format:
    data: {"chunk": "text"}
    
    data: {"done": true}
    """
    try:
        logger.info(f"Received streaming query request for user {query_request.user_id}")
        
        # Get or create memory handler
        memory_handler = get_memory_handler(query_request.user_id)
        logger.info(f"Created/retrieved memory handler for thread {query_request.thread_id}")
        
        # Get context
        context = await memory_handler.get_context(query_request.thread_id)
        logger.info(f"Retrieved context with {len(context['messages'])} messages")
        
        # Set up streaming response
        async def generate_stream():
            full_response = ""
            
            try:
                # Get streaming generator - NO await needed, returns AsyncGenerator directly
                stream_gen = interact_with_agent_stream(
                    user_input=query_request.question,
                    user_id=query_request.user_id,
                    user_timezone=query_request.user_timezone,
                    thread_id=query_request.thread_id,
                    supabase_client=supabase,
                    context=context
                )
                
                # Stream each chunk - interact_with_agent_stream yields simple strings
                async for chunk in stream_gen:
                    if isinstance(chunk, str) and chunk.strip():
                        full_response += chunk
                        yield f"data: {json.dumps({'chunk': chunk})}\n\n"
                
                # Store both user message and complete response after streaming is done
                await memory_handler.add_message(
                    thread_id=query_request.thread_id,
                    message=query_request.question,
                    role="user"
                )
                await memory_handler.add_message(
                    thread_id=query_request.thread_id,
                    message=full_response,
                    role="assistant"
                )
                
                # End the stream
                yield f"data: {json.dumps({'done': True})}\n\n"
                
            except Exception as e:
                logger.error(f"Streaming error: {str(e)}", exc_info=True)
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
        
        # Return streaming response
        return StreamingResponse(
            generate_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Cache-Control"
            }
        )
        
    except Exception as e:
        logger.error(f"Error in query_knowledge_base_stream: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# Non-streaming endpoint for fallback
@app.post("/query", response_model=QueryResponse)
async def query_knowledge_base(request: Request, query_request: QueryRequest):
    """Non-streaming fallback endpoint"""
    try:
        # Get or create memory handler
        memory_handler = get_memory_handler(query_request.user_id)
        
        # Get context
        context = await memory_handler.get_context(query_request.thread_id)
        
        # Get response from agent
        response = await interact_with_agent(
            user_input=query_request.question,
            user_id=query_request.user_id,
            user_timezone=query_request.user_timezone,
            thread_id=query_request.thread_id,
            supabase_client=supabase,
            context=context
        )
        
        # Store the interaction
        await memory_handler.add_message(
            thread_id=query_request.thread_id,
            message=query_request.question,
            role="user"
        )
        await memory_handler.add_message(
            thread_id=query_request.thread_id,
            message=response,
            role="assistant"
        )
        
        return QueryResponse(
            answer=response,
            sources=[]
        )
    except Exception as e:
        logger.error(f"Error in query_knowledge_base: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
```

### 2. Claude Agent with Streaming Support

```python
# claude_agent.py
import asyncio
import logging
from typing import Dict, Any, AsyncGenerator
from anthropic import AsyncAnthropic
from src.config import Config
from src.simple_memory import SimpleMemory
from src.model_selector import get_chat_model

logger = logging.getLogger(__name__)

# Global client instance (singleton pattern)
_anthropic_client = None

async def get_anthropic_client():
    """Get or create Anthropic client"""
    global _anthropic_client
    if _anthropic_client is None:
        _anthropic_client = AsyncAnthropic(api_key=Config.ANTHROPIC_API_KEY)
    return _anthropic_client

def get_cache_control_header():
    """Get cache control headers for prompt caching"""
    return {
        "anthropic-beta": "prompt-caching-2024-07-31"
    }

def format_static_context_for_caching(static_context: str) -> str:
    """Format static context for optimal caching"""
    return f"""# PROJECT CONTEXT & MEMORY
{static_context}

# CONVERSATION CONTINUES BELOW
Remember to reference the above context when responding to the user's messages."""

async def get_personalized_system_prompt(user_id: str, user_timezone: str, memory) -> tuple[str, float]:
    """Get personalized system prompt based on user's archetype"""
    # Get user's creativity archetype for personalized prompts
    archetype = await memory.get_user_archetype(user_id)
    
    base_prompt = """You are Hai, a creative partner helping with personal creative projects. 
Be direct, confident, warm, and supportive. You understand the creative process and its challenges."""
    
    # Adjust temperature based on archetype
    temperature = 0.6  # Default balanced temperature
    
    if archetype:
        # Customize based on archetype
        if archetype.get('type') == 'structured':
            temperature = 0.4  # More focused for structured types
        elif archetype.get('type') == 'experimental':
            temperature = 0.8  # More creative for experimental types
    
    return base_prompt, temperature

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
            # Use cost-optimized model selection
            chat_model = get_chat_model()
            
            stream = await anthropic_client.messages.create(
                model=chat_model,
                max_tokens=4000,
                temperature=temperature,  # Use archetype-specific temperature
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

# Non-streaming version for fallback
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
            # Use cost-optimized model selection
            chat_model = get_chat_model()
            
            response = await anthropic_client.messages.create(
                model=chat_model,
                max_tokens=4000,
                temperature=temperature,  # Use archetype-specific temperature
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
```

### 3. Simple Claude Client

```python
# claude_client_simple.py
import logging
from typing import List, Dict, AsyncGenerator, Union
from anthropic import AsyncAnthropic
from src.config import Config

logger = logging.getLogger(__name__)

class ClaudeCredentials:
    """Simple credential holder for Claude API"""
    def __init__(self, api_key: str):
        self.api_key = api_key

class SimpleClaudeClient:
    """Simple Claude API client using official Anthropic SDK."""
    
    def __init__(self, credentials: ClaudeCredentials):
        self.credentials = credentials
        self.client = AsyncAnthropic(api_key=credentials.api_key)
        
    async def send_message(
        self, 
        messages: List[Dict[str, str]], 
        model: str = "claude-3-5-sonnet-20241022",
        max_tokens: int = 4000,
        temperature: float = 0.7,
        stream: bool = False
    ) -> Union[str, AsyncGenerator[str, None]]:
        """
        Send a message to Claude.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Claude model to use
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            stream: Whether to stream the response
            
        Returns:
            String response or async generator for streaming
        """
        try:
            if stream:
                # Return the async generator directly
                return self._stream_message(messages, model, max_tokens, temperature)
            else:
                message = await self.client.messages.create(
                    model=model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    messages=messages
                )
                return message.content[0].text
                
        except Exception as e:
            logger.error(f"Claude API error: {e}")
            raise
    
    async def _stream_message(
        self, 
        messages: List[Dict[str, str]], 
        model: str,
        max_tokens: int,
        temperature: float
    ) -> AsyncGenerator[str, None]:
        """Stream a message response from Claude."""
        try:
            async with self.client.messages.stream(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=messages,
            ) as stream:
                async for text in stream.text_stream:
                    yield text
                    
        except Exception as e:
            logger.error(f"Claude streaming error: {e}")
            raise

# Global client instance
_claude_client = None

async def create_claude_client() -> SimpleClaudeClient:
    """Create or get Claude client"""
    global _claude_client
    if _claude_client is None:
        credentials = ClaudeCredentials(api_key=Config.ANTHROPIC_API_KEY)
        _claude_client = SimpleClaudeClient(credentials)
    return _claude_client

async def send_claude_message(
    messages: List[Dict[str, str]], 
    stream: bool = False,
    **kwargs
) -> Union[str, AsyncGenerator[str, None]]:
    """Convenience function to send a message to Claude."""
    client = await create_claude_client()
    return await client.send_message(messages, stream=stream, **kwargs)
```

### 4. Memory System with Context Optimization

```python
# simple_memory.py
import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
import json

logger = logging.getLogger(__name__)

class SimpleMemory:
    """Simple memory system with context optimization for streaming"""
    
    def __init__(self, supabase_client, user_id: str):
        self.supabase = supabase_client
        self.user_id = user_id
        
    async def ensure_creator_profile(self, user_id: str):
        """Ensure creator profile exists before database operations"""
        try:
            # Check if profile exists
            result = self.supabase.table('creator_profiles').select('id').eq('id', user_id).execute()
            
            if not result.data:
                # Create profile if it doesn't exist
                profile_data = {
                    'id': user_id,
                    'slack_email': f"{user_id}@auto-created.local",
                    'zoom_email': f"{user_id}@auto-created.local",
                    'first_name': 'New',
                    'last_name': 'User'
                }
                
                self.supabase.table('creator_profiles').insert(profile_data).execute()
                logger.info(f"Created creator profile for user {user_id}")
                
        except Exception as e:
            logger.error(f"Error ensuring creator profile: {e}")
            # Continue anyway - don't block the conversation
    
    async def add_message(self, thread_id: str, message: str, role: str):
        """Add a message to conversation history"""
        try:
            # Ensure profile exists
            await self.ensure_creator_profile(self.user_id)
            
            # Store message
            message_data = {
                'user_id': self.user_id,
                'thread_id': thread_id,
                'content': message,
                'role': role,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
            self.supabase.table('conversations').insert(message_data).execute()
            logger.info(f"Stored {role} message for user {self.user_id}")
            
        except Exception as e:
            logger.error(f"Error storing message: {e}")
            # Don't raise - message storage shouldn't block streaming
    
    async def get_context(self, thread_id: str) -> Dict[str, Any]:
        """Get conversation context for thread"""
        try:
            # Get recent messages
            messages = self.supabase.table('conversations')\
                .select('*')\
                .eq('user_id', self.user_id)\
                .eq('thread_id', thread_id)\
                .order('timestamp', desc=False)\
                .limit(50)\
                .execute()
            
            formatted_messages = []
            for msg in messages.data:
                formatted_messages.append({
                    'role': msg['role'],
                    'content': msg['content'],
                    'timestamp': msg['timestamp']
                })
            
            return {
                'messages': formatted_messages,
                'thread_id': thread_id,
                'user_id': self.user_id
            }
            
        except Exception as e:
            logger.error(f"Error getting context: {e}")
            return {'messages': [], 'thread_id': thread_id, 'user_id': self.user_id}
    
    async def get_caching_optimized_context(self, thread_id: str) -> Dict[str, Any]:
        """Get context optimized for prompt caching"""
        try:
            # Get user's project context (static - good for caching)
            project_context = await self.get_user_project_context()
            
            # Get recent conversation (dynamic - not cached)
            recent_messages = self.supabase.table('conversations')\
                .select('*')\
                .eq('user_id', self.user_id)\
                .eq('thread_id', thread_id)\
                .order('timestamp', desc=False)\
                .limit(20)\
                .execute()
            
            conversation_messages = []
            for msg in recent_messages.data:
                conversation_messages.append({
                    'role': msg['role'],
                    'content': msg['content']
                })
            
            return {
                'static_context': project_context,
                'dynamic_context': {
                    'conversation_messages': conversation_messages,
                    'thread_id': thread_id
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting caching context: {e}")
            return {
                'static_context': "",
                'dynamic_context': {
                    'conversation_messages': [],
                    'thread_id': thread_id
                }
            }
    
    async def get_user_project_context(self) -> str:
        """Get user's project context for prompt caching"""
        try:
            # Get project overview
            project = self.supabase.table('project_overview')\
                .select('*')\
                .eq('user_id', self.user_id)\
                .execute()
            
            if project.data:
                p = project.data[0]
                return f"""
PROJECT: {p.get('project_name', 'Unknown')}
TYPE: {p.get('project_type', 'Unknown')}
GOALS: {', '.join(p.get('goals', []))}
CHALLENGES: {', '.join(p.get('challenges', []))}
"""
            
            return ""
            
        except Exception as e:
            logger.error(f"Error getting project context: {e}")
            return ""
    
    async def get_user_archetype(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user's creativity archetype for personalization"""
        try:
            result = self.supabase.table('creator_profiles')\
                .select('creativity_archetype')\
                .eq('id', user_id)\
                .execute()
            
            if result.data and result.data[0].get('creativity_archetype'):
                return result.data[0]['creativity_archetype']
                
            return None
            
        except Exception as e:
            logger.error(f"Error getting user archetype: {e}")
            return None
```

### 5. Configuration Management

```python
# config.py
import os
from typing import List, Optional
from dotenv import load_dotenv

# Only load .env in development
if os.getenv('ENVIRONMENT') != 'production':
    load_dotenv()

class Config:
    # API Configurations
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY")
    ANTHROPIC_MODEL: str = "claude-3-5-sonnet-20241022"
    
    # Cost Optimization: Model selection by operation type
    CHAT_MODEL: str = os.getenv("CHAT_MODEL", "claude-3-5-sonnet-20241022")
    BACKGROUND_MODEL: str = os.getenv("BACKGROUND_MODEL", "claude-3-haiku-20240307")
    TEST_MODEL: str = os.getenv("TEST_MODEL", "claude-3-haiku-20240307")
    
    # Development overrides
    DEV_MODEL: str = os.getenv("DEV_MODEL", "claude-3-haiku-20240307")
    DEV_CHAT_MODEL: str = os.getenv("DEV_CHAT_MODEL", "claude-3-haiku-20240307")
    
    # Cost optimization flags
    ENABLE_COST_OPTIMIZATION: bool = os.getenv("ENABLE_COST_OPTIMIZATION", "true").lower() in ("true", "1", "yes")
    DEVELOPMENT_MODE: bool = os.getenv("DEVELOPMENT_MODE", "false").lower() in ("true", "1", "yes")
    
    # Database Configuration
    SUPABASE_URL: str = os.getenv("SUPABASE_URL")
    SUPABASE_ANON_KEY: str = os.getenv("SUPABASE_ANON_KEY")
    SUPABASE_SERVICE_KEY: str = os.getenv("SUPABASE_SERVICE_KEY")
    
    # Feature Flags
    ENABLE_DETAILED_LOGGING: bool = os.getenv("ENABLE_DETAILED_LOGGING", "False").lower() in ("true", "1", "yes")
    
    @classmethod
    def get_environment(cls) -> str:
        """Returns the current environment (development/production)"""
        return os.getenv('ENVIRONMENT', 'development')
```

---

## 🎨 Frontend Implementation

### 1. React Hook for Streaming

```typescript
// hooks/useStreamingChat.ts
import { useState, useCallback } from 'react';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

interface UseStreamingChatReturn {
  messages: Message[];
  isStreaming: boolean;
  sendMessage: (message: string) => Promise<void>;
  streamingMessage: string;
}

export const useStreamingChat = (
  userId: string,
  threadId: string,
  apiUrl: string
): UseStreamingChatReturn => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingMessage, setStreamingMessage] = useState('');

  const sendMessage = useCallback(async (message: string) => {
    try {
      // Add user message immediately
      const userMessage: Message = {
        id: Date.now().toString(),
        role: 'user',
        content: message,
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, userMessage]);

      // Start streaming
      setIsStreaming(true);
      setStreamingMessage(''); // CRITICAL: Reset accumulator

      const response = await fetch(`${apiUrl}/query_stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question: message,
          user_id: userId,
          user_timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
          thread_id: threadId
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      if (!reader) {
        throw new Error('No response body reader available');
      }

      try {
        while (true) {
          const { done, value } = await reader.read();
          
          if (done) break;
          
          const chunk = decoder.decode(value, { stream: true });
          buffer += chunk;
          
          // Process complete lines (ending with \n\n)
          const lines = buffer.split('\n\n');
          buffer = lines.pop() || '';
          
          for (const line of lines) {
            if (line.trim()) {
              processStreamChunk(line.trim());
            }
          }
        }
      } finally {
        reader.releaseLock();
      }
    } catch (error) {
      console.error('Streaming error:', error);
      setIsStreaming(false);
    }
  }, [userId, threadId, apiUrl]);

  const processStreamChunk = useCallback((line: string) => {
    // Remove 'data: ' prefix if present
    const jsonStr = line.startsWith('data: ') ? line.slice(6) : line;
    
    try {
      const data = JSON.parse(jsonStr);
      
      if (data.chunk) {
        // KEY FIX: Accumulate chunks into streamingMessage state
        setStreamingMessage(prev => prev + data.chunk);
      } else if (data.done) {
        // KEY FIX: Move complete message to messages array
        setMessages(prev => [...prev, {
          id: Date.now().toString(),
          role: 'assistant',
          content: streamingMessage,
          timestamp: new Date().toISOString()
        }]);
        
        // Reset streaming state
        setIsStreaming(false);
        setStreamingMessage('');
      } else if (data.error) {
        console.error('Streaming error:', data.error);
        setIsStreaming(false);
        setStreamingMessage('');
      }
    } catch (error) {
      console.error('Error parsing stream chunk:', error, 'Line:', line);
    }
  }, [streamingMessage]);

  return {
    messages,
    isStreaming,
    sendMessage,
    streamingMessage
  };
};
```

### 2. React Chat Component

```typescript
// components/ChatComponent.tsx
import React, { useState, useEffect, useRef } from 'react';
import { useStreamingChat } from '../hooks/useStreamingChat';

interface ChatComponentProps {
  userId: string;
  threadId: string;
  apiUrl: string;
}

const ChatComponent: React.FC<ChatComponentProps> = ({ userId, threadId, apiUrl }) => {
  const { messages, isStreaming, sendMessage, streamingMessage } = useStreamingChat(
    userId,
    threadId,
    apiUrl
  );
  const [inputMessage, setInputMessage] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamingMessage]);

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputMessage.trim() || isStreaming) return;

    await sendMessage(inputMessage);
    setInputMessage('');
  };

  return (
    <div className="chat-container">
      <div className="messages-container">
        {/* Display message history */}
        {messages.map(message => (
          <div key={message.id} className={`message ${message.role}`}>
            <div className="message-content">{message.content}</div>
            <div className="message-timestamp">
              {new Date(message.timestamp).toLocaleTimeString()}
            </div>
          </div>
        ))}
        
        {/* Display streaming message while it builds */}
        {isStreaming && streamingMessage && (
          <div className="message assistant streaming">
            <div className="message-content">
              {streamingMessage}
              <span className="cursor">|</span>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>
      
      <form onSubmit={handleSendMessage} className="input-form">
        <input
          type="text"
          value={inputMessage}
          onChange={(e) => setInputMessage(e.target.value)}
          placeholder="Type your message..."
          disabled={isStreaming}
          className="message-input"
        />
        <button 
          type="submit" 
          disabled={isStreaming || !inputMessage.trim()}
          className="send-button"
        >
          {isStreaming ? 'Sending...' : 'Send'}
        </button>
      </form>
    </div>
  );
};

export default ChatComponent;
```

### 3. Alternative: Pure JavaScript Implementation

```javascript
// streamingClient.js
class StreamingChatClient {
  constructor(apiUrl, userId, threadId) {
    this.apiUrl = apiUrl;
    this.userId = userId;
    this.threadId = threadId;
  }

  async sendMessageWithStreaming(
    message,
    onChunk,
    onComplete,
    onError
  ) {
    try {
      const response = await fetch(`${this.apiUrl}/query_stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question: message,
          user_id: this.userId,
          user_timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
          thread_id: this.threadId
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      if (!reader) {
        throw new Error('No response body reader available');
      }

      try {
        while (true) {
          const { done, value } = await reader.read();
          
          if (done) break;
          
          const chunk = decoder.decode(value, { stream: true });
          buffer += chunk;
          
          // Process complete lines (ending with \n\n)
          const lines = buffer.split('\n\n');
          buffer = lines.pop() || '';
          
          for (const line of lines) {
            if (line.trim()) {
              this.processStreamChunk(line.trim(), onChunk, onComplete, onError);
            }
          }
        }
      } finally {
        reader.releaseLock();
      }
    } catch (error) {
      onError(error);
    }
  }

  processStreamChunk(line, onChunk, onComplete, onError) {
    // Remove 'data: ' prefix if present
    const jsonStr = line.startsWith('data: ') ? line.slice(6) : line;
    
    try {
      const data = JSON.parse(jsonStr);
      
      if (data.chunk) {
        onChunk(data.chunk);
      } else if (data.done) {
        onComplete();
      } else if (data.error) {
        onError(new Error(data.error));
      }
    } catch (error) {
      console.error('Error parsing stream chunk:', error, 'Line:', line);
      onError(new Error('Failed to parse stream response'));
    }
  }
}

// Usage example
const client = new StreamingChatClient(
  'https://your-api.com',
  'user-123',
  'thread-456'
);

let fullMessage = '';

client.sendMessageWithStreaming(
  'Hello, how are you?',
  (chunk) => {
    // Handle each chunk
    fullMessage += chunk;
    document.getElementById('streaming-message').textContent = fullMessage;
  },
  () => {
    // Handle completion
    console.log('Streaming complete:', fullMessage);
    document.getElementById('streaming-message').classList.remove('streaming');
  },
  (error) => {
    // Handle errors
    console.error('Streaming error:', error);
  }
);
```

### 4. Next.js API Route (Optional Proxy)

```typescript
// pages/api/chat/stream.ts
import { NextApiRequest, NextApiResponse } from 'next';

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const { question, user_id, user_timezone, thread_id } = req.body;

  // Set up SSE headers
  res.writeHead(200, {
    'Content-Type': 'text/event-stream',
    'Cache-Control': 'no-cache',
    'Connection': 'keep-alive',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Cache-Control'
  });

  try {
    // Forward to FastAPI backend
    const response = await fetch(`${process.env.BACKEND_URL}/query_stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        question,
        user_id,
        user_timezone,
        thread_id
      })
    });

    if (!response.ok) {
      throw new Error(`Backend error: ${response.status}`);
    }

    const reader = response.body?.getReader();
    const decoder = new TextDecoder();

    if (!reader) {
      throw new Error('No response body reader available');
    }

    try {
      while (true) {
        const { done, value } = await reader.read();
        
        if (done) break;
        
        const chunk = decoder.decode(value, { stream: true });
        res.write(chunk);
      }
    } finally {
      reader.releaseLock();
    }
  } catch (error) {
    console.error('Streaming error:', error);
    res.write(`data: ${JSON.stringify({ error: error.message })}\n\n`);
  }

  res.end();
}
```

---

## 🔧 Environment Configuration

### 1. Environment Variables

```bash
# .env (Development)
ENVIRONMENT=development
ANTHROPIC_API_KEY=your_anthropic_api_key_here
SUPABASE_URL=your_supabase_url_here
SUPABASE_SERVICE_KEY=your_supabase_service_key_here

# Model Configuration
CHAT_MODEL=claude-3-5-sonnet-20241022
BACKGROUND_MODEL=claude-3-haiku-20240307
DEV_MODEL=claude-3-haiku-20240307

# Cost Optimization
ENABLE_COST_OPTIMIZATION=true
DEVELOPMENT_MODE=true
ENABLE_DETAILED_LOGGING=true
```

```bash
# .env.production
ENVIRONMENT=production
ANTHROPIC_API_KEY=your_production_anthropic_api_key
SUPABASE_URL=your_production_supabase_url
SUPABASE_SERVICE_KEY=your_production_supabase_service_key

# Production Models
CHAT_MODEL=claude-3-5-sonnet-20241022
BACKGROUND_MODEL=claude-3-haiku-20240307

# Production Optimization
ENABLE_COST_OPTIMIZATION=true
DEVELOPMENT_MODE=false
ENABLE_DETAILED_LOGGING=false
```

### 2. Frontend Environment Variables

```bash
# .env.local (Next.js)
NEXT_PUBLIC_BACKEND_API_URL=http://localhost:8000
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
```

```bash
# .env.production
NEXT_PUBLIC_BACKEND_API_URL=https://your-api.herokuapp.com
NEXT_PUBLIC_SUPABASE_URL=your_production_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_production_supabase_anon_key
```

---

## 🧪 Testing Implementation

### 1. Backend Testing

```python
# test_streaming.py
import pytest
import asyncio
from httpx import AsyncClient
from src.main import app

@pytest.mark.asyncio
async def test_streaming_endpoint():
    """Test streaming endpoint returns proper SSE format"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/query_stream",
            json={
                "question": "Hello, how are you?",
                "user_id": "test-user-123",
                "user_timezone": "UTC",
                "thread_id": "test-thread"
            }
        )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream"
        
        # Check SSE format
        content = response.text
        assert "data: " in content
        assert '{"chunk":' in content or '{"done":' in content

@pytest.mark.asyncio
async def test_streaming_chunks():
    """Test streaming returns multiple chunks"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/query_stream",
            json={
                "question": "Write a short story",
                "user_id": "test-user-123",
                "user_timezone": "UTC",
                "thread_id": "test-thread"
            }
        )
        
        chunks = []
        lines = response.text.split('\n\n')
        
        for line in lines:
            if line.strip() and line.startswith('data: '):
                import json
                data = json.loads(line[6:])  # Remove 'data: ' prefix
                if 'chunk' in data:
                    chunks.append(data['chunk'])
        
        assert len(chunks) > 1  # Should have multiple chunks
        
        # Verify chunks form coherent response
        full_response = ''.join(chunks)
        assert len(full_response) > 10
```

### 2. Frontend Testing

```javascript
// test/streaming.test.js
import { renderHook, act } from '@testing-library/react';
import { useStreamingChat } from '../hooks/useStreamingChat';

// Mock fetch for testing
global.fetch = jest.fn();

describe('useStreamingChat', () => {
  beforeEach(() => {
    fetch.mockClear();
  });

  test('should handle streaming response correctly', async () => {
    // Mock streaming response
    const mockResponse = {
      ok: true,
      body: {
        getReader: () => ({
          read: jest.fn()
            .mockResolvedValueOnce({
              done: false,
              value: new TextEncoder().encode('data: {"chunk":"Hello"}\n\n')
            })
            .mockResolvedValueOnce({
              done: false,
              value: new TextEncoder().encode('data: {"chunk":" World"}\n\n')
            })
            .mockResolvedValueOnce({
              done: false,
              value: new TextEncoder().encode('data: {"done":true}\n\n')
            })
            .mockResolvedValueOnce({
              done: true,
              value: undefined
            }),
          releaseLock: jest.fn()
        })
      }
    };

    fetch.mockResolvedValue(mockResponse);

    const { result } = renderHook(() => 
      useStreamingChat('user-123', 'thread-456', 'http://test-api')
    );

    await act(async () => {
      await result.current.sendMessage('Test message');
    });

    // Check final state
    expect(result.current.messages).toHaveLength(2); // User + Assistant
    expect(result.current.messages[1].content).toBe('Hello World');
    expect(result.current.isStreaming).toBe(false);
  });
});
```

### 3. Integration Testing

```python
# test_integration.py
import asyncio
import aiohttp
import json

async def test_streaming_integration():
    """Test complete streaming flow"""
    async with aiohttp.ClientSession() as session:
        async with session.post(
            'http://localhost:8000/query_stream',
            json={
                "question": "Tell me a joke",
                "user_id": "test-user-integration",
                "user_timezone": "UTC",
                "thread_id": "test-thread-integration"
            }
        ) as response:
            assert response.status == 200
            
            chunks = []
            async for line in response.content:
                line_str = line.decode('utf-8').strip()
                if line_str and line_str.startswith('data: '):
                    data = json.loads(line_str[6:])
                    if 'chunk' in data:
                        chunks.append(data['chunk'])
                        print(f"Received chunk: {data['chunk']}")
                    elif data.get('done'):
                        print("Streaming complete")
                        break
            
            full_response = ''.join(chunks)
            assert len(full_response) > 0
            print(f"Full response: {full_response}")

if __name__ == "__main__":
    asyncio.run(test_streaming_integration())
```

---

## 🚀 Deployment Configuration

### 1. FastAPI Deployment (Heroku)

```python
# Procfile
web: uvicorn src.main:app --host 0.0.0.0 --port $PORT --workers 1
```

```yaml
# requirements.txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
anthropic==0.7.7
supabase==1.2.0
python-dotenv==1.0.0
pydantic==2.5.0
```

### 2. Next.js Deployment (Vercel)

```json
{
  "name": "streaming-chat-frontend",
  "version": "0.1.0",
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start"
  },
  "dependencies": {
    "next": "14.0.0",
    "react": "18.2.0",
    "react-dom": "18.2.0",
    "@types/react": "18.2.0",
    "typescript": "5.0.0"
  }
}
```

### 3. Docker Configuration

```dockerfile
# Dockerfile (Backend)
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY .env .

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 🛠️ Troubleshooting Guide

### 1. Common Issues

**Problem**: Streaming endpoint returns only `{"done": true}`
```python
# Solution: Check async generator handling
async def interact_with_agent_stream(...):
    # DON'T await the generator
    stream_gen = claude_client.send_message(..., stream=True)
    
    # DO iterate with async for
    async for chunk in stream_gen:
        if chunk.strip():
            yield chunk
```

**Problem**: Frontend doesn't accumulate chunks properly
```javascript
// Solution: Use proper state accumulation
const [streamingMessage, setStreamingMessage] = useState('');

const processChunk = (chunk) => {
  // CORRECT: Accumulate into state
  setStreamingMessage(prev => prev + chunk);
  
  // WRONG: Direct assignment
  // setStreamingMessage(chunk);
};
```

### 2. Debugging Tips

```python
# Backend debugging
import logging
logging.basicConfig(level=logging.INFO)

# Add debug logs in streaming function
async def interact_with_agent_stream(...):
    logger.info(f"Starting stream for user {user_id}")
    async for chunk in stream_gen:
        logger.info(f"Yielding chunk: {chunk[:50]}...")
        yield chunk
```

```javascript
// Frontend debugging
const processStreamChunk = (line) => {
  console.log('Raw line:', line);
  
  try {
    const data = JSON.parse(jsonStr);
    console.log('Parsed data:', data);
    
    if (data.chunk) {
      console.log('Processing chunk:', data.chunk);
      setStreamingMessage(prev => {
        const newMessage = prev + data.chunk;
        console.log('New accumulated message:', newMessage);
        return newMessage;
      });
    }
  } catch (error) {
    console.error('Parse error:', error, 'Line:', line);
  }
};
```

### 3. Performance Optimization

```python
# Use connection pooling
from anthropic import AsyncAnthropic

# Global client instance
_anthropic_client = None

async def get_anthropic_client():
    global _anthropic_client
    if _anthropic_client is None:
        _anthropic_client = AsyncAnthropic(api_key=Config.ANTHROPIC_API_KEY)
    return _anthropic_client
```

```javascript
// Frontend optimization
const useStreamingChat = (userId, threadId, apiUrl) => {
  // Use useCallback to prevent unnecessary re-renders
  const sendMessage = useCallback(async (message) => {
    // Implementation
  }, [userId, threadId, apiUrl]);

  const processStreamChunk = useCallback((line) => {
    // Implementation
  }, [streamingMessage]);

  return { messages, isStreaming, sendMessage, streamingMessage };
};
```

---

## 📊 Performance Benchmarks

### Expected Performance (Based on Fridays at Four)

- **First Token**: 200-800ms (Claude API dependent)
- **Stream Rate**: 20-50 tokens/second
- **Memory Usage**: <50MB per concurrent user
- **Cost**: ~$0.01-0.03 per conversation with prompt caching

### Monitoring

```python
# Add performance monitoring
import time
import logging

async def interact_with_agent_stream(...):
    start_time = time.time()
    first_token_time = None
    token_count = 0
    
    async for chunk in stream_gen:
        if first_token_time is None:
            first_token_time = time.time()
            logger.info(f"First token time: {first_token_time - start_time:.2f}s")
        
        token_count += len(chunk.split())
        yield chunk
    
    total_time = time.time() - start_time
    logger.info(f"Stream complete: {token_count} tokens in {total_time:.2f}s")
```

---

## 🎉 Success Checklist

- [ ] FastAPI streaming endpoint responds with proper SSE format
- [ ] Claude client yields individual text chunks
- [ ] Frontend accumulates chunks correctly
- [ ] Memory system stores complete responses
- [ ] Error handling gracefully degrades
- [ ] CORS headers allow frontend access
- [ ] Environment variables configured
- [ ] Performance benchmarks met
- [ ] Tests pass for streaming flow
- [ ] Production deployment successful

---

*This template captures the complete streaming implementation from Fridays at Four. Follow these patterns for reliable, performant streaming in your AI applications.* 