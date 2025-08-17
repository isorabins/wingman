#!/usr/bin/env python3
"""
Memory Compression System for WingmanMatch AI Optimization

Implements intelligent context compression and management for efficient
Claude API usage while maintaining conversation quality and continuity.

Features:
- Conversation summarization with context preservation
- Sliding window context management
- Token usage optimization
- Memory compression with quality preservation
- Context reconstruction from summaries
"""

import logging
import json
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass
from enum import Enum

from src.content_summarizer import ContentSummarizer
from src.model_router import ModelRouter, ModelTier

logger = logging.getLogger(__name__)

class CompressionStrategy(Enum):
    """Different compression strategies for memory management"""
    AGGRESSIVE = "aggressive"      # Maximum compression, minimal context
    BALANCED = "balanced"         # Balance between compression and context
    CONSERVATIVE = "conservative" # Minimal compression, maximum context

@dataclass
class CompressionResult:
    """Result of memory compression operation"""
    compressed_messages: List[Dict[str, Any]]
    summary: str
    original_token_count: int
    compressed_token_count: int
    compression_ratio: float
    quality_score: float
    metadata: Dict[str, Any]

@dataclass
class ContextWindow:
    """Represents a managed context window for conversation"""
    recent_messages: List[Dict[str, Any]]
    summary: str
    total_tokens: int
    window_size: int
    last_compression: datetime
    compression_count: int

class MemoryCompressor:
    """
    Manages conversation memory compression for optimal AI model usage.
    
    Provides intelligent compression strategies that maintain conversation
    quality while reducing token usage and API costs.
    """
    
    def __init__(self):
        self.content_summarizer = ContentSummarizer()
        self.model_router = ModelRouter()
        
        # Compression configuration
        self.config = {
            "max_context_tokens": 8000,      # Maximum tokens in context
            "target_compression_ratio": 0.3,  # Target 30% of original size
            "min_messages_for_compression": 20, # Minimum messages before compression
            "summary_token_target": 500,      # Target tokens for summaries
            "recent_message_count": 10,       # Always keep last N messages
            "compression_trigger_ratio": 0.8, # Compress when 80% of max tokens
        }
        
        # Strategy-specific settings
        self.strategy_config = {
            CompressionStrategy.AGGRESSIVE: {
                "compression_ratio": 0.2,     # 20% of original
                "recent_messages": 5,         # Keep last 5 messages
                "summary_detail": "brief"
            },
            CompressionStrategy.BALANCED: {
                "compression_ratio": 0.3,     # 30% of original
                "recent_messages": 10,        # Keep last 10 messages
                "summary_detail": "moderate"
            },
            CompressionStrategy.CONSERVATIVE: {
                "compression_ratio": 0.5,     # 50% of original
                "recent_messages": 15,        # Keep last 15 messages
                "summary_detail": "detailed"
            }
        }
    
    def estimate_token_count(self, text: str) -> int:
        """
        Estimate token count for text (rough approximation).
        
        Args:
            text: Text to estimate tokens for
            
        Returns:
            Estimated token count
        """
        # Rough approximation: 1 token ≈ 0.75 words for English
        word_count = len(text.split())
        return int(word_count * 1.33)
    
    def estimate_messages_tokens(self, messages: List[Dict[str, Any]]) -> int:
        """
        Estimate total token count for a list of messages.
        
        Args:
            messages: List of message dictionaries
            
        Returns:
            Estimated total token count
        """
        total_tokens = 0
        for message in messages:
            content = message.get('content', '')
            role = message.get('role', '')
            # Include role in token count (role + content + formatting)
            message_text = f"{role}: {content}"
            total_tokens += self.estimate_token_count(message_text)
        
        return total_tokens
    
    def should_compress(self, messages: List[Dict[str, Any]], 
                       current_tokens: Optional[int] = None) -> bool:
        """
        Determine if messages should be compressed based on size and configuration.
        
        Args:
            messages: List of conversation messages
            current_tokens: Current token count (estimated if not provided)
            
        Returns:
            True if compression is recommended
        """
        if len(messages) < self.config["min_messages_for_compression"]:
            return False
        
        if current_tokens is None:
            current_tokens = self.estimate_messages_tokens(messages)
        
        # Check if we're approaching token limit
        max_tokens = self.config["max_context_tokens"]
        trigger_threshold = max_tokens * self.config["compression_trigger_ratio"]
        
        return current_tokens > trigger_threshold
    
    def select_compression_strategy(self, messages: List[Dict[str, Any]], 
                                   user_preferences: Optional[Dict[str, Any]] = None) -> CompressionStrategy:
        """
        Select appropriate compression strategy based on context and preferences.
        
        Args:
            messages: Conversation messages
            user_preferences: User-specific preferences
            
        Returns:
            Selected compression strategy
        """
        # Check user preferences
        if user_preferences:
            if user_preferences.get("preserve_context", False):
                return CompressionStrategy.CONSERVATIVE
            elif user_preferences.get("optimize_cost", False):
                return CompressionStrategy.AGGRESSIVE
        
        # Analyze conversation complexity
        total_tokens = self.estimate_messages_tokens(messages)
        
        # Use aggressive compression for long conversations
        if total_tokens > 12000:
            return CompressionStrategy.AGGRESSIVE
        elif total_tokens > 8000:
            return CompressionStrategy.BALANCED
        else:
            return CompressionStrategy.CONSERVATIVE
    
    async def compress_conversation(self, messages: List[Dict[str, Any]],
                                   strategy: Optional[CompressionStrategy] = None,
                                   preserve_recent: Optional[int] = None) -> CompressionResult:
        """
        Compress conversation messages while preserving context quality.
        
        Args:
            messages: List of conversation messages
            strategy: Compression strategy to use
            preserve_recent: Number of recent messages to preserve
            
        Returns:
            CompressionResult with compressed messages and metadata
        """
        start_time = datetime.now()
        
        # Select strategy if not provided
        if strategy is None:
            strategy = self.select_compression_strategy(messages)
        
        strategy_config = self.strategy_config[strategy]
        
        # Determine how many recent messages to preserve
        if preserve_recent is None:
            preserve_recent = strategy_config["recent_messages"]
        
        # Calculate original token count
        original_tokens = self.estimate_messages_tokens(messages)
        
        # Split messages into compression candidates and recent messages
        if len(messages) <= preserve_recent:
            # Not enough messages to compress meaningfully
            return CompressionResult(
                compressed_messages=messages,
                summary="",
                original_token_count=original_tokens,
                compressed_token_count=original_tokens,
                compression_ratio=1.0,
                quality_score=1.0,
                metadata={
                    "strategy": strategy.value,
                    "reason": "insufficient_messages",
                    "processing_time": (datetime.now() - start_time).total_seconds()
                }
            )
        
        # Messages to compress (all except recent)
        messages_to_compress = messages[:-preserve_recent]
        recent_messages = messages[-preserve_recent:]
        
        # Generate summary of older messages
        summary = await self._generate_conversation_summary(
            messages_to_compress, 
            strategy_config["summary_detail"]
        )
        
        # Create compressed message list
        compressed_messages = recent_messages.copy()
        
        # Add summary as a system message if we generated one
        if summary:
            summary_message = {
                "role": "system",
                "content": f"Previous conversation summary: {summary}",
                "metadata": {
                    "type": "compression_summary",
                    "strategy": strategy.value,
                    "compressed_count": len(messages_to_compress),
                    "generated_at": datetime.now().isoformat()
                }
            }
            compressed_messages.insert(0, summary_message)
        
        # Calculate compression metrics
        compressed_tokens = self.estimate_messages_tokens(compressed_messages)
        compression_ratio = compressed_tokens / original_tokens if original_tokens > 0 else 1.0
        
        # Estimate quality score based on compression ratio and strategy
        quality_score = self._calculate_quality_score(compression_ratio, strategy)
        
        # Build metadata
        metadata = {
            "strategy": strategy.value,
            "original_message_count": len(messages),
            "compressed_message_count": len(compressed_messages),
            "messages_summarized": len(messages_to_compress),
            "recent_messages_preserved": preserve_recent,
            "processing_time": (datetime.now() - start_time).total_seconds(),
            "summary_length": len(summary) if summary else 0
        }
        
        logger.info(
            f"Compressed conversation: {len(messages)} -> {len(compressed_messages)} messages, "
            f"{original_tokens} -> {compressed_tokens} tokens ({compression_ratio:.2%} ratio)"
        )
        
        return CompressionResult(
            compressed_messages=compressed_messages,
            summary=summary,
            original_token_count=original_tokens,
            compressed_token_count=compressed_tokens,
            compression_ratio=compression_ratio,
            quality_score=quality_score,
            metadata=metadata
        )
    
    async def _generate_conversation_summary(self, messages: List[Dict[str, Any]], 
                                           detail_level: str) -> str:
        """
        Generate a summary of conversation messages.
        
        Args:
            messages: Messages to summarize
            detail_level: Level of detail (brief, moderate, detailed)
            
        Returns:
            Conversation summary
        """
        if not messages:
            return ""
        
        try:
            # Format messages for summarization
            conversation_text = self._format_messages_for_summary(messages)
            
            # Use economy model for summarization to reduce costs
            summary_prompt = self._build_summary_prompt(detail_level)
            
            # Use the content summarizer with custom prompt
            original_prompt = self.content_summarizer.reduce_prompt
            self.content_summarizer.reduce_prompt = summary_prompt
            
            # Generate summary
            result = await self.content_summarizer.ainvoke(conversation_text)
            summary = result.get("final_summary", "")
            
            # Restore original prompt
            self.content_summarizer.reduce_prompt = original_prompt
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating conversation summary: {e}")
            return f"Summary unavailable due to processing error: {str(e)}"
    
    def _format_messages_for_summary(self, messages: List[Dict[str, Any]]) -> str:
        """Format messages into text suitable for summarization"""
        formatted_lines = []
        
        for message in messages:
            role = message.get('role', 'unknown')
            content = message.get('content', '')
            timestamp = message.get('timestamp', '')
            
            # Format with role and content
            if timestamp:
                formatted_lines.append(f"[{timestamp}] {role.upper()}: {content}")
            else:
                formatted_lines.append(f"{role.upper()}: {content}")
        
        return "\n\n".join(formatted_lines)
    
    def _build_summary_prompt(self, detail_level: str) -> str:
        """Build summary prompt based on detail level"""
        base_prompt = """Summarize this conversation focusing on key topics, decisions, and important context that should be preserved for future interactions. """
        
        if detail_level == "brief":
            return base_prompt + "Provide a concise summary in 2-3 sentences highlighting only the most critical points."
        elif detail_level == "moderate":
            return base_prompt + "Provide a balanced summary covering main topics, user preferences, and important context in 1-2 paragraphs."
        else:  # detailed
            return base_prompt + "Provide a comprehensive summary preserving important details, user insights, preferences, and context that aids future conversations."
    
    def _calculate_quality_score(self, compression_ratio: float, 
                                strategy: CompressionStrategy) -> float:
        """
        Calculate estimated quality score for compression result.
        
        Args:
            compression_ratio: Actual compression ratio achieved
            strategy: Compression strategy used
            
        Returns:
            Quality score between 0.0 and 1.0
        """
        # Base quality score based on strategy
        base_scores = {
            CompressionStrategy.AGGRESSIVE: 0.7,
            CompressionStrategy.BALANCED: 0.8,
            CompressionStrategy.CONSERVATIVE: 0.9
        }
        
        base_score = base_scores[strategy]
        
        # Adjust based on compression ratio
        # Lower compression ratio (more compression) may reduce quality
        if compression_ratio < 0.2:
            quality_adjustment = -0.2
        elif compression_ratio < 0.3:
            quality_adjustment = -0.1
        elif compression_ratio > 0.7:
            quality_adjustment = 0.1
        else:
            quality_adjustment = 0.0
        
        return max(0.0, min(1.0, base_score + quality_adjustment))
    
    def create_context_window(self, messages: List[Dict[str, Any]], 
                             max_tokens: Optional[int] = None) -> ContextWindow:
        """
        Create a managed context window for conversation.
        
        Args:
            messages: Conversation messages
            max_tokens: Maximum tokens allowed in window
            
        Returns:
            ContextWindow object with managed context
        """
        if max_tokens is None:
            max_tokens = self.config["max_context_tokens"]
        
        current_tokens = self.estimate_messages_tokens(messages)
        
        # If within limits, return all messages
        if current_tokens <= max_tokens:
            return ContextWindow(
                recent_messages=messages,
                summary="",
                total_tokens=current_tokens,
                window_size=len(messages),
                last_compression=datetime.now(),
                compression_count=0
            )
        
        # Need to compress - use balanced strategy by default
        compression_result = self.compress_conversation(
            messages, 
            CompressionStrategy.BALANCED
        )
        
        return ContextWindow(
            recent_messages=compression_result.compressed_messages,
            summary=compression_result.summary,
            total_tokens=compression_result.compressed_token_count,
            window_size=len(compression_result.compressed_messages),
            last_compression=datetime.now(),
            compression_count=1
        )
    
    async def update_context_window(self, window: ContextWindow, 
                                   new_messages: List[Dict[str, Any]]) -> ContextWindow:
        """
        Update existing context window with new messages.
        
        Args:
            window: Existing context window
            new_messages: New messages to add
            
        Returns:
            Updated context window
        """
        # Add new messages to window
        all_messages = window.recent_messages + new_messages
        total_tokens = self.estimate_messages_tokens(all_messages)
        
        # Check if compression is needed
        if not self.should_compress(all_messages, total_tokens):
            # No compression needed, just update window
            window.recent_messages = all_messages
            window.total_tokens = total_tokens
            window.window_size = len(all_messages)
            return window
        
        # Compression needed
        compression_result = await self.compress_conversation(
            all_messages,
            CompressionStrategy.BALANCED
        )
        
        return ContextWindow(
            recent_messages=compression_result.compressed_messages,
            summary=compression_result.summary,
            total_tokens=compression_result.compressed_token_count,
            window_size=len(compression_result.compressed_messages),
            last_compression=datetime.now(),
            compression_count=window.compression_count + 1
        )
    
    def get_compression_stats(self) -> Dict[str, Any]:
        """Get compression performance statistics"""
        return {
            "max_context_tokens": self.config["max_context_tokens"],
            "target_compression_ratio": self.config["target_compression_ratio"],
            "min_messages_for_compression": self.config["min_messages_for_compression"],
            "recent_message_count": self.config["recent_message_count"],
            "strategies_available": [strategy.value for strategy in CompressionStrategy],
            "compression_trigger_ratio": self.config["compression_trigger_ratio"]
        }

# Global memory compressor instance
memory_compressor = MemoryCompressor()

async def compress_messages(messages: List[Dict[str, Any]], 
                           strategy: Optional[CompressionStrategy] = None) -> CompressionResult:
    """
    Convenience function to compress conversation messages.
    
    Args:
        messages: Messages to compress
        strategy: Compression strategy (auto-selected if None)
        
    Returns:
        CompressionResult with compressed messages
    """
    return await memory_compressor.compress_conversation(messages, strategy)

def create_managed_context(messages: List[Dict[str, Any]], 
                         max_tokens: Optional[int] = None) -> ContextWindow:
    """
    Convenience function to create a managed context window.
    
    Args:
        messages: Conversation messages
        max_tokens: Maximum tokens in context
        
    Returns:
        Managed context window
    """
    return memory_compressor.create_context_window(messages, max_tokens)