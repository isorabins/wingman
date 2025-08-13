#!/usr/bin/env python3
"""
Simple Claude API Client using Official Anthropic SDK
Pure API client - no app logic, just API calls.
"""
import os
from typing import List, Dict, AsyncGenerator, Optional
from anthropic import AsyncAnthropic
from anthropic.types import Message
import logging

logger = logging.getLogger(__name__)


class ClaudeCredentials:
    """Handle Claude API credentials."""
    
    def __init__(self):
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is required")


class SimpleClaudeClient:
    """Simple Claude API client using official Anthropic SDK."""
    
    def __init__(self, credentials: ClaudeCredentials):
        self.credentials = credentials
        self.client = AsyncAnthropic(api_key=credentials.api_key)
        
    async def send_message(
        self, 
        messages: List[Dict[str, str]], 
        model: str = "claude-sonnet-4-20250514",
        max_tokens: int = 4000,
        temperature: float = 0.7,
        stream: bool = False
    ) -> str | AsyncGenerator[str, None]:
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


# Convenience functions for easy integration
async def create_claude_client() -> SimpleClaudeClient:
    """Create and return a configured Claude client."""
    credentials = ClaudeCredentials()
    return SimpleClaudeClient(credentials)


async def send_claude_message(
    messages: List[Dict[str, str]], 
    stream: bool = False,
    **kwargs
) -> str | AsyncGenerator[str, None]:
    """Convenience function to send a message to Claude."""
    client = await create_claude_client()
    return await client.send_message(messages, stream=stream, **kwargs) 