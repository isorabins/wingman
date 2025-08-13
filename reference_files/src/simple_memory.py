#!/usr/bin/env python3
"""
Simple Memory Manager

DOESNT USE LANGCHAIN ANYMORE - NOW JUST USES MEMORY TABLE AS BUFFER STORAGE
Manages conversation history, context, and summary storage in Supabase.
Provides auto-dependency creation for creator profiles.
"""

import asyncio
import json
import logging
import hashlib
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta, timezone
from supabase import Client

# ContentSummarizer now uses claude_client_simple (no more LangChain)
from src.content_summarizer import ContentSummarizer, BufferSummaryHandler
from src.config import Config

logger = logging.getLogger(__name__)

class SimpleMemory:
    def __init__(self, supabase_client, user_id: str, buffer_size: int = 100): 
        self.supabase = supabase_client
        self.user_id = user_id
        self.buffer_size = buffer_size
        
        # Initialize summarizer for buffer management (now using Claude)
        self.content_summarizer = ContentSummarizer()
        self.summarizer = BufferSummaryHandler(self.content_summarizer)

    def _generate_message_hash(self, thread_id: str, formatted_content: str, role: str) -> str:
        """Generate a hash for message deduplication based on content, not time"""
        # Create a consistent hash from the message components WITHOUT timestamp
        # Use the formatted content directly since it already includes the role
        message_data = f"{self.user_id}:{thread_id}:{formatted_content.strip()}"
        return hashlib.md5(message_data.encode()).hexdigest()
    
    async def _is_message_duplicate(self, message_hash: str, thread_id: str, formatted_content: str) -> bool:
        """Check if this message hash already exists in recent memory (last 10 minutes)"""
        try:
            # Check for recent messages with same hash (within last 10 minutes to handle quick retries)
            recent_cutoff = datetime.now(timezone.utc) - timedelta(minutes=10)
            
            result = self.supabase.table('memory')\
                .select('id, metadata, content')\
                .eq('user_id', self.user_id)\
                .eq('memory_type', 'message')\
                .eq('metadata->>thread_id', thread_id)\
                .gte('created_at', recent_cutoff.isoformat())\
                .execute()
            
            # Check if any existing message has the same hash OR same content (double protection)
            for record in result.data:
                existing_metadata = record.get('metadata', {})
                existing_content = record.get('content', '')
                
                # Check both hash match AND content match for robust deduplication
                if (existing_metadata.get('message_hash') == message_hash or 
                    existing_content == formatted_content):
                    logger.info(f"Duplicate message detected - hash: {message_hash}, content match: {existing_content == formatted_content}")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking message duplication: {e}")
            # If we can't check, assume not duplicate to avoid blocking messages
            return False

    def _sanitize_message(self, message: Any) -> str:
        """Ensure message is in string format and sanitized for storage"""
        try:
            # Handle TextBlock or other response types
            if hasattr(message, 'text'):
                return str(message.text)
            elif hasattr(message, 'content'):
                return str(message.content)
            # Convert to string if it's not already
            return str(message)
        except Exception as e:
            logger.error(f"Error sanitizing message: {e}")
            # Return empty string if conversion fails
            return ""

    async def add_message(self, thread_id: str, message: str, role: str):
        """Add a message with deduplication and trigger summarization if buffer is full"""
        try:
            # Ensure creator profile exists before adding message to prevent foreign key constraints
            await self.ensure_creator_profile(self.user_id)
            
            # Sanitize message (to str from json for claude API before storage)
            sanitized_message = self._sanitize_message(message)
            
            # Generate message hash for deduplication - use consistent formatting
            # Use the same format as stored content for accurate deduplication
            formatted_content = f"{role}: {sanitized_message}"
            message_hash = self._generate_message_hash(thread_id, formatted_content, role)

            # Always store in conversations table (this can have duplicates or handle them differently)
            conversation_data = {
                'user_id': self.user_id,
                'message_text': sanitized_message,  # Use sanitized message for consistency
                'role': role,
                'context': {'thread_id': thread_id},
                'metadata': {},  # Empty JSONB field as per schema
                'created_at': datetime.now(timezone.utc).isoformat()
            }
            self.supabase.table('conversations').insert(conversation_data).execute()
            
            # Check for duplicates in memory table specifically (not conversations table)
            # Use a more robust duplicate check that looks for content match as well
            if await self._is_message_duplicate(message_hash, thread_id, formatted_content):
                logger.info(f"Skipping duplicate memory insert for thread {thread_id}, hash: {message_hash}")
                return  # Skip only the memory table insert, conversations was already inserted

            # Store in memory table with correct schema and message hash for deduplication
            memory_data = {
                'user_id': self.user_id,
                'memory_type': 'message',
                'content': formatted_content,  # Use the same formatted content as hash generation
                'metadata': {
                    'thread_id': thread_id,
                    'message_hash': message_hash  # Store hash for future deduplication checks
                },
                'created_at': datetime.now(timezone.utc).isoformat()
            }

            # Add logging and insert once
            logger.info(f"Adding new message to memory for thread {thread_id}, hash: {message_hash}")
            result = self.supabase.table('memory').insert(memory_data).execute()
            try:
                logger.info(f"Memory insert result: {result.data if result else 'No data'}")
            except:
                pass

            # Check buffer size
            messages = self.supabase.table('memory')\
                .select('*')\
                .eq('metadata->>thread_id', thread_id)\
                .eq('memory_type', 'message')\
                .execute()

            if len(messages.data) >= self.buffer_size:
                # Run summarization as a background task to avoid blocking
                asyncio.create_task(self.summarize_thread(thread_id))
                logger.info(f"Started background summarization for thread {thread_id}")

        except Exception as e:
            logger.error(f"Error adding message: {e}", exc_info=True)
            raise

    async def summarize_thread(self, thread_id: str):
        """Generate summary and update memory state"""
        try:
            # Get messages from memory table
            messages = self.supabase.table('memory')\
                .select('*')\
                .eq('metadata->>thread_id', thread_id)\
                .eq('memory_type', 'message')\
                .order('created_at')\
                .execute()

            if not messages.data:
                logger.warning(f"No messages found for thread {thread_id}")
                return

            # Pass all required arguments to create_buffer_summary
            summary_result = await self.summarizer.create_buffer_summary(
                thread_id=thread_id,
                messages=messages.data,
                user_id=self.user_id,
                supabase_client=self.supabase
            )

            logger.info(f"Successfully summarized thread {thread_id}")

        except Exception as e:
            logger.error(f"Error summarizing thread: {str(e)}")
            raise
    async def get_context(self, thread_id: str):
        """Get current messages and summaries from memory table - ALL USER MEMORY across threads"""
        try:
            # Get recent messages from ALL user threads (not just current thread_id)
            # This fixes the memory continuity bug where new thread_ids broke memory access
            messages = self.supabase.table('memory')\
                .select('*')\
                .eq('user_id', self.user_id)\
                .eq('memory_type', 'message')\
                .order('created_at')\
                .limit(50)\
                .execute()

            # Get recent summaries from ALL user threads
            summaries = self.supabase.table('memory')\
                .select('*')\
                .eq('user_id', self.user_id)\
                .eq('memory_type', 'buffer_summary')\
                .order('created_at', desc=True)\
                .limit(5)\
                .execute()

            return {
                "messages": [{"role": m.get('content', '').split(':', 1)[0],
                            "content": m.get('content', '').split(':', 1)[1].strip()}
                            for m in messages.data if ':' in m.get('content', '')],
                "summaries": [s['content'] for s in summaries.data] if summaries.data else []
            }

        except Exception as e:
            logger.error(f"Error getting context: {e}")
            raise

    async def get_caching_optimized_context(self, thread_id: str) -> Dict[str, Any]:
        """
        Get user context optimized for Claude prompt caching.
        Separates static (cacheable) from dynamic (non-cacheable) content.
        """
        try:
            # === STATIC DATA (Good for caching - changes rarely) ===
            
            # Get creator profile (changes rarely)
            profile_result = self.supabase.table('creator_profiles')\
                .select('*')\
                .eq('id', self.user_id)\
                .execute()
            
            # Get creativity profile (changes rarely - usually set once)
            creativity_result = self.supabase.table('creator_creativity_profiles')\
                .select('*')\
                .eq('user_id', self.user_id)\
                .execute()
            
            # Get project overview (changes rarely)
            project_result = self.supabase.table('project_overview')\
                .select('*')\
                .eq('user_id', self.user_id)\
                .execute()
            
            # Get project updates (updated nightly, stable during conversations)
            updates_result = self.supabase.table('project_updates')\
                .select('*')\
                .eq('user_id', self.user_id)\
                .order('created_at', desc=True)\
                .limit(5)\
                .execute()
            
            # Get long-term memory summaries (updated nightly, stable during conversations)
            longterm_result = self.supabase.table('longterm_memory')\
                .select('*')\
                .eq('user_id', self.user_id)\
                .order('created_at', desc=True)\
                .limit(10)\
                .execute()
            
            # === DYNAMIC DATA (Changes every message - don't cache) ===
            
            # Get current conversation messages (changes every turn)
            # IMPORTANT: Preserve existing get_context() behavior that pulls from ALL user threads
            # This was a critical fix for memory continuity across different thread_ids
            current_memory = await self.get_context(thread_id)
            
            return {
                "static_context": {  # This gets cached!
                    "user_profile": profile_result.data[0] if profile_result.data else None,
                    "creativity_profile": creativity_result.data[0] if creativity_result.data else None,
                    "project_overview": project_result.data[0] if project_result.data else None,
                    "project_updates": updates_result.data or [],
                    "longterm_summaries": longterm_result.data or [],
                    "has_complete_profile": bool(profile_result.data),
                    "has_creativity_profile": bool(creativity_result.data),
                    "has_project": bool(project_result.data)
                },
                "dynamic_context": {  # This doesn't get cached
                    "conversation_messages": current_memory["messages"],
                    "buffer_summaries": current_memory["summaries"],
                    "thread_id": thread_id,
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting caching optimized context: {e}")
            # Return safe defaults on error
            return {
                "static_context": {
                    "user_profile": None,
                    "creativity_profile": None,
                    "project_overview": None,
                    "project_updates": [],
                    "longterm_summaries": [],
                    "has_complete_profile": False,
                    "has_creativity_profile": False,
                    "has_project": False
                },
                "dynamic_context": {
                    "conversation_messages": [],
                    "buffer_summaries": [],
                    "thread_id": thread_id,
                }
            }

    async def ensure_creator_profile(self, user_id: str):
        """Ensure creator profile exists for user to prevent foreign key constraint violations"""
        try:
            # Check if creator profile exists
            result = self.supabase.table('creator_profiles')\
                .select('id')\
                .eq('id', user_id)\
                .execute()
            
            if not result.data:
                # Create creator profile with minimal data using correct schema
                profile_data = {
                    "id": user_id,
                    "slack_id": None,
                    "slack_email": f"user_{user_id[:8]}@temp.com",  # Temporary email
                    "zoom_email": f"user_{user_id[:8]}@temp.com",   # Temporary email
                    "first_name": "User",
                    "last_name": "Temp",
                    "preferences": {},
                    "interaction_count": 0,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
                
                self.supabase.table('creator_profiles').insert(profile_data).execute()
                logger.info(f"Auto-created creator profile for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error ensuring creator profile for {user_id}: {str(e)}")
            # Don't fail the main operation if profile creation fails

    async def get_user_archetype(self, user_id: str, supabase_client=None) -> Optional[int]:
        """
        Look up user's creativity archetype from the database
        
        Args:
            user_id: User's ID to look up archetype for
            supabase_client: Supabase client instance (optional, will create if needed)
            
        Returns:
            User's archetype number (1-6) or None if not found
        """
        try:
            if not supabase_client:
                from src.config import Config
                config = Config()
                supabase_client = config.get_supabase_client()
            
            # Query the creator_creativity_profiles table
            result = supabase_client.table('creator_creativity_profiles') \
                .select('archetype') \
                .eq('user_id', user_id) \
                .execute()
            
            if result.data and len(result.data) > 0:
                archetype = result.data[0]['archetype']
                logger.info(f"Found archetype {archetype} for user {user_id}")
                return archetype
            else:
                logger.info(f"No archetype found for user {user_id}")
                return None
            
        except Exception as e:
            logger.error(f"Error getting user archetype: {e}")
            return None
