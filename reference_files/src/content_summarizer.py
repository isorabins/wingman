#!/usr/bin/env python3
"""
Content Summarization System

UPDATED: Now uses claude_client_simple instead of LangChain while preserving all functionality.

Architecture:
1. ContentSummarizer:
   - Core map-reduce summarization using Claude API directly
   - Text chunking and parallel processing
   - No LangChain dependencies

2. DailySummaryHandler:
   - Daily conversation analysis and quality scoring
   - Uses ContentSummarizer for processing

3. BufferSummaryHandler:
   - Thread-based conversation summarization
   - Memory management and cleanup

4. TranscriptSummaryHandler:
   - Meeting transcript processing
   - Structured output for transcript data

Operational Flow (Claude-Based):
1. **Real-time Conversations**: User conversations are stored in the `conversations` table as they happen
2. **Buffer Management**: BufferSummaryHandler monitors conversation buffer size (15 messages) per thread
3. **Buffer Summarization**: When buffer fills, ContentSummarizer uses Claude API to:
   - Split conversations into chunks (map phase)
   - Process each chunk with Claude (parallel processing)
   - Combine results into final summary (reduce phase)
   - Store summary in `memory` table and clear buffer messages
4. **Nightly Processing**: DailySummaryHandler runs via Heroku scheduler to:
   - Fetch all conversations from previous day per user
   - Generate daily summary using Claude map-reduce
   - Analyze conversation quality using Claude
   - Store results in `longterm_memory` table
   - Generate project updates and store in `project_updates` table
5. **Context Retrieval**: SimpleMemory pulls summaries + recent messages for conversation context

Claude Integration Details:
- Uses official Anthropic SDK through claude_client_simple.py
- Maintains map-reduce pattern for processing large conversations
- Parallel chunk processing for performance
- Error handling and graceful degradation
- Temperature 0.3 for consistent summarization
- Custom prompts for different use cases (daily, buffer, transcript, project updates)

All handlers maintain existing interfaces and database schemas while using Claude instead of LangChain.
"""

import asyncio
import json
import logging
import operator
from typing import Dict, List, Any, Optional, TypedDict, Annotated
from datetime import datetime, timedelta, timezone, date
from dataclasses import dataclass
from supabase import Client

# Replace LangChain imports with our Claude client
from src.claude_client_simple import SimpleClaudeClient, ClaudeCredentials
from src.config import Config

# Import prompts (these are just strings, no LangChain needed)
from src.prompts import (
    MAP_PROMPT, 
    REDUCE_PROMPT, 
    QUALITY_ANALYSIS_PROMPT,
    PROJECT_UPDATE_PROMPT,
    TRANSCRIPT_PROMPT,
    CONVERSATION_PROMPT
)

logger = logging.getLogger(__name__)

# Simple text splitter (replacing LangChain's RecursiveCharacterTextSplitter)
class SimpleTextSplitter:
    def __init__(self, chunk_size: int = 4000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def split_text(self, text: str) -> List[str]:
        """Split text into overlapping chunks"""
        if len(text) <= self.chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.chunk_size
            
            # If this isn't the last chunk, try to break at a sentence or word boundary
            if end < len(text):
                # Look for sentence endings first
                last_period = text.rfind('.', start, end)
                last_exclamation = text.rfind('!', start, end)
                last_question = text.rfind('?', start, end)
                
                sentence_end = max(last_period, last_exclamation, last_question)
                if sentence_end > start:
                    end = sentence_end + 1
                else:
                    # Fall back to word boundary
                    last_space = text.rfind(' ', start, end)
                    if last_space > start:
                        end = last_space
            
            # Extract chunk
            chunk = text[start:end].strip()
            if chunk:  # Only add non-empty chunks
                chunks.append(chunk)
            
            # Calculate next start position with safety checks
            if end >= len(text):
                # We've reached the end, break out
                break
            else:
                # Move start position forward, ensuring we always advance
                next_start = end - self.chunk_overlap
                # Ensure we always advance by at least 1 character to prevent infinite loops
                start = max(next_start, start + 1)
            
        return chunks

@dataclass
class SummaryResult:
    """Structured result from summarization process"""
    summary: str
    metadata: Dict[str, Any]
    error: Optional[str] = None

# Simplified state management (no more LangChain graph dependencies)
class MeetingInfo(TypedDict):
    id: str
    topic: str
    duration_minutes: int
    zoom_user_id: str

class TranscriptMetadata(TypedDict):
    meeting_info: MeetingInfo
    generated_at: str  # ISO format datetime
    team_id: Optional[str]

class DateRange(TypedDict):
    start: str  # ISO format date
    end: str    # ISO format date

class ConversationMetadata(TypedDict):
    date_range: DateRange
    conversation_count: int
    generated_at: str  # ISO format datetime
    quality_analysis: Dict[str, Any]

class BufferMetadata(TypedDict):
    thread_id: str
    source: Dict[str, str]
    generated_at: str  # ISO format datetime

class ContentSummarizer:
    def __init__(self, model: str = None, map_prompt=None, reduce_prompt=None):
        # Use our Claude client instead of ChatOpenAI
        self.claude_client = None  # Will be initialized on first use (lazy loading)
        
        # Use cost-optimized model selection if no model specified
        if model is None:
            from src.model_selector import get_summarization_model
            model = get_summarization_model()
        
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
    
    def setup_chain(self):
        """Compatibility method - no longer needed but kept for existing code"""
        pass
    
    async def ainvoke(self, content: str) -> Dict[str, str]:
        """Main entry point for summarization - implements map/reduce pattern"""
        try:
            # Step 1: Split content into chunks
            chunks = self.text_splitter.split_text(content)
            logger.info(f"Split content into {len(chunks)} chunks")
            
            # Step 2: Process chunks in parallel (MAP phase)
            map_tasks = [self._map_chunk(chunk) for chunk in chunks]
            summaries = await asyncio.gather(*map_tasks)
            
            # Step 3: Combine summaries (REDUCE phase)
            final_summary = await self._reduce_summaries(summaries)
            
            return {
                "final_summary": final_summary,
                "summaries": summaries  # Include intermediate summaries for debugging
            }
            
        except Exception as e:
            logger.error(f"Error in summarization: {e}")
            return {
                "final_summary": f"Error in summarization: {str(e)}",
                "summaries": []
            }

class DailySummaryHandler:
    """Handles daily conversation summaries and quality analysis"""
    def __init__(self, summarizer: ContentSummarizer):
        self.summarizer = summarizer
        self.daily_summarizer = ContentSummarizer()  # Default prompts
        self.project_summarizer = ContentSummarizer(reduce_prompt=PROJECT_UPDATE_PROMPT)

    def _validate_and_format_dates(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> tuple[date, date]:
        """Validate and standardize date inputs"""
        if start_date is None:
            start_date = datetime.now(timezone.utc).date()
        elif isinstance(start_date, datetime):
            start_date = start_date.date()
        elif not isinstance(start_date, date):
            raise ValueError("start_date must be a datetime or date object")

        if end_date is None:
            end_date = start_date
        elif isinstance(end_date, datetime):
            end_date = end_date.date()
        elif not isinstance(end_date, date):
            raise ValueError("end_date must be a datetime or date object")

        return start_date, end_date

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
            
            # Use cost-optimized model for quality analysis
            from src.model_selector import get_analysis_model
            analysis_model = get_analysis_model()
            
            result = await claude_client.send_message(
                messages=messages,
                model=analysis_model,
                max_tokens=4000,
                temperature=0.1,
                stream=False
            )
            
            # Parse and validate the JSON response
            metrics = json.loads(result.strip())
            
            # Validate required fields and score ranges
            required_fields = [
                "understanding_score", 
                "helpfulness_score",
                "context_maintenance_score", 
                "support_effectiveness_score",
                "analysis_notes"
            ]
            
            if not all(field in metrics for field in required_fields):
                raise ValueError("Missing required fields in quality metrics")
                
            scores = [v for k, v in metrics.items() if k.endswith('_score')]
            if not all(0 <= score <= 1 for score in scores):
                raise ValueError("Quality scores must be between 0 and 1")
                
            return metrics

        except Exception as e:
            logger.error(f"Quality analysis failed: {e}")
            raise  # Let the caller handle the error

    def _format_conversation_text(self, conversations: List[Dict]) -> str:
        """Format conversations into analyzable text"""
        return "\n\n".join([
            f"{conv['role'].upper()}: {conv['message_text']} [{conv['created_at']}]"
            for conv in conversations.data
        ])

    def _create_memory_data(
        self,
        user_id: str,
        end_date: date,
        summary: str,
        metadata: ConversationMetadata
    ) -> Dict[str, Any]:
        """Create structured memory data for storage"""
        return {
            'user_id': user_id,
            'summary_date': end_date.isoformat(),
            'content': summary,
            'metadata': metadata,
            'created_at': datetime.now(timezone.utc).isoformat()
        }
    
    async def generate_daily_summary(
        self,
        user_id: str,
        supabase_client,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Optional[Dict[str, Any]]:
        """Generate summary of daily conversations with quality analysis"""
        try:
            # this is so the streamlit backend can track token cost
            start_tokens = 0  # We'll track this
            total_cost = 0    # And this
            
            logger.info(f"Starting daily summary for user {user_id}")
            # Validate and format dates
            start_date, end_date = self._validate_and_format_dates(start_date, end_date)
            logger.info(f"Generating daily summary for {user_id} from {start_date} to {end_date}")

#this works in tandem with an RPC function that only returns users from today that HAVE NOT 
#had a summary done. Uses heroku scheduler to run nightly
            #we've changed that logic to not use the RPC now

            # Fetch conversations
            conversations = supabase_client.table('conversations')\
                .select('*')\
                .eq('user_id', user_id)\
                .gte('created_at', f'{start_date.isoformat()}T00:00:00Z')\
                .lt('created_at', f'{(end_date + timedelta(days=1)).isoformat()}T00:00:00Z')\
                .order('created_at')\
                .execute()
#start_date and end_date are defined in nightly_ with base_date, which seems like its today
            if not conversations.data:
                logger.info(f"No conversations found for user {user_id} in date range")
                return None

            # Process conversations
            conversation_text = self._format_conversation_text(conversations)
            logger.debug(f"Processing {len(conversations.data)} conversations")


            # Generate daily summary (using default REDUCE_PROMPT)
            daily_result = await self.summarizer.ainvoke(conversation_text)

            # Temporarily swap prompt for project update
            self.summarizer.reduce_prompt = PROJECT_UPDATE_PROMPT
            self.summarizer.setup_chain()

            # Generate project update using same summarizer
            project_result = await self.summarizer.ainvoke(conversation_text)

            # Reset to original prompt
            self.summarizer.reduce_prompt = REDUCE_PROMPT
            self.summarizer.setup_chain()

            # Try to generate quality analysis
            try:
                quality_metrics = await self.analyze_quality(conversation_text)
                logger.debug("Generated quality metrics for conversations")
            except Exception as e:
                logger.error(f"Quality analysis failed but continuing: {e}")
                quality_metrics = None

            # Create metadata once
            metadata: ConversationMetadata = {
                'date_range': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat()
                },
                'conversation_count': len(conversations.data),
                'generated_at': datetime.now(timezone.utc).isoformat(),
            }

            # Only add quality_analysis if we got metrics
            if quality_metrics:
                metadata['quality_analysis'] = quality_metrics

            # Prepare storage data
            memory_data = self._create_memory_data(
                user_id,
                end_date,
                daily_result["final_summary"],
                metadata
            )
            #output project_updates summary to the logs for testing
            logger.info("=== PROJECT STATUS UPDATE ===")
            logger.info(f"Project Update Content:\n{project_result['final_summary']}")
            logger.info("===========================")
                        # Store summary with upsert logic
            try:
                supabase_client.table('longterm_memory')\
                    .upsert(memory_data, on_conflict='user_id,summary_date')\
                    .execute()
                logger.info(f"Successfully stored daily summary for {user_id}")
            except Exception as e:
                logger.error(f"Failed to store daily summary: {e}", exc_info=True)
                raise

            logger.info(f"Starting project update generation for user {user_id}")

            # Parse and store project update with structured JSON data
            try:
                import json
                import re
                
                # Try to parse the JSON from the progress summary
                progress_summary = project_result["final_summary"]
                parsed_data = {}
                
                def extract_json_from_text(text: str) -> dict:
                    """
                    Robustly extract JSON from text that may contain multiple objects,
                    nested braces, or braces within string values.
                    
                    Returns the first valid JSON object found, or empty dict if none.
                    
                    FIXED: Improved brace counting and regex patterns to handle nested JSON properly.
                    """
                    if not text or '{' not in text:
                        return {}
                    
                    # Strategy 1: Look for JSON blocks wrapped in code fences
                    json_block_pattern = r'```(?:json)?\s*(\{.*?\})\s*```'
                    json_blocks = re.findall(json_block_pattern, text, re.DOTALL | re.IGNORECASE)
                    
                    for block in json_blocks:
                        try:
                            return json.loads(block.strip())
                        except json.JSONDecodeError:
                            continue
                    
                    # Strategy 2: Find complete JSON objects by counting braces (FIXED)
                    # Process text in segments to avoid negative brace_count issues
                    text_len = len(text)
                    search_start = 0
                    
                    while search_start < text_len:
                        brace_count = 0
                        start_idx = None
                        in_string = False
                        escape_next = False
                    
                        for i in range(search_start, text_len):
                            char = text[i]
                            
                            if escape_next:
                                escape_next = False
                                continue
                                
                            if char == '\\':
                                escape_next = True
                                continue
                                
                            if char == '"' and not escape_next:
                                in_string = not in_string
                                continue
                                
                            if in_string:
                                continue
                                
                            if char == '{':
                                if start_idx is None:
                                    start_idx = i
                                brace_count += 1
                            elif char == '}':
                                if brace_count > 0:  # Only decrement if we have open braces
                                    brace_count -= 1
                                
                                # Found complete JSON object
                                if brace_count == 0 and start_idx is not None:
                                    json_candidate = text[start_idx:i+1]
                                    try:
                                        return json.loads(json_candidate)
                                    except json.JSONDecodeError:
                                        # Continue searching from after this failed attempt
                                        search_start = start_idx + 1
                                        break
                            
                        # If we get here, we had a parsing error and need to continue from search_start
                        if search_start >= text_len - 1:
                            break
                    
                    # Strategy 3: Fallback - try common JSON patterns (FIXED: allow nested braces)
                    json_patterns = [
                        # Specific field patterns that allow nested structures
                        r'\{[^{}]*"milestones_hit"[^{}]*(?:\{[^{}]*\}[^{}]*)*\}',
                        r'\{[^{}]*"blockers"[^{}]*(?:\{[^{}]*\}[^{}]*)*\}',
                        r'\{[^{}]*"next_steps"[^{}]*(?:\{[^{}]*\}[^{}]*)*\}',
                        # Greedy pattern that matches balanced braces
                        r'\{(?:[^{}]|(?:\{[^{}]*\}))*\}',
                        # Last resort - simple pattern
                        r'\{.*?\}'
                    ]
                    
                    for pattern in json_patterns:
                        matches = re.findall(pattern, text, re.DOTALL)
                        for match in matches:
                            try:
                                return json.loads(match)
                            except json.JSONDecodeError:
                                continue
                    
                    return {}
                
                try:
                    parsed_data = extract_json_from_text(progress_summary)
                    if parsed_data:
                        logger.info(f"Successfully parsed project update JSON for {user_id}")
                    else:
                        logger.info(f"No valid JSON found in project update for {user_id}")
                except Exception as e:
                    logger.warning(f"Error during JSON extraction from project update: {e}")
                    parsed_data = {}
                
                project_update = {
                    'user_id': user_id,
                    'update_date': end_date.isoformat(),
                    'progress_summary': parsed_data.get('progress_summary', progress_summary[:200]),
                    'milestones_hit': parsed_data.get('milestones_hit', []),
                    'blockers': parsed_data.get('blockers', []),
                    'next_steps': parsed_data.get('next_steps', []),
                    'mood_rating': parsed_data.get('mood_rating')
                }
                
                supabase_client.table('project_updates')\
                    .upsert(project_update, on_conflict='user_id,update_date')\
                    .execute()
                logger.info(f"Successfully stored project update for {user_id} with {len(parsed_data.get('next_steps', []))} next steps")
            except Exception as e:
                logger.error(f"Failed to store project update: {e}", exc_info=True)
                # Don't fail the whole process if project update fails
            
            # Return SummaryResult with properly structured data
            return SummaryResult(
                summary=daily_result["final_summary"],
                metadata={
                    'date_range': {
                        'start': start_date.isoformat(),
                        'end': end_date.isoformat()
                    },
                    'conversation_count': len(conversations.data),
                    'generated_at': datetime.now(timezone.utc).isoformat(),
                    'quality_analysis': quality_metrics or {}
                },
                error=None
            )
            
        except Exception as e:
            logger.error(f"Failed to generate daily summary: {e}", exc_info=True)
            return SummaryResult(
                summary="",
                metadata={},
                error=str(e)
            )

    #this is finding users that have had conversations within the start and end dates
    #but Im not sure this is being used because base_date is filling in these variables in nightly_..
    #and it seems finding users logic is doubled in nightly_...
    
    def get_users_needing_summaries(
        self,
        supabase_client,
        start_date: date,
        end_date: date
    ) -> List[str]:
        """Get list of unique user_ids that have conversations in the date range"""
        conversations = supabase_client.table('conversations')\
            .select('user_id')\
            .gte('created_at', f'{start_date.isoformat()}T00:00:00Z')\
            .lt('created_at', f'{end_date.isoformat()}T00:00:00Z')\
            .execute()
        
        # Get unique user_ids
        #but user_id is called in nightly
        return list(set(conv['user_id'] for conv in conversations.data))

class BufferSummaryHandler:
    """Handles conversation buffer summaries"""
    def __init__(self, summarizer: ContentSummarizer):
        self.summarizer = summarizer

    def _format_messages(self, messages: List[Dict]) -> str:
        """Format messages into analyzable text"""
        formatted_messages = []
        for msg in messages:
            # Handle both message formats (from memory table)
            content = msg.get('content', '')
            if ': ' in content:
                # Content already has role prefix
                formatted_messages.append(content)
            else:
                role = msg.get('role', 'unknown')
                message_text = msg.get('message_text', content)
                formatted_messages.append(f"{role}: {message_text}")
                
        return "\n\n".join(formatted_messages)

    def _create_summary_data(
        self,
        user_id: str,
        thread_id: str,
        summary: str
    ) -> Dict[str, Any]:
        """Create structured summary data for storage"""
        now = datetime.now(timezone.utc)
        return {
            'user_id': user_id,
            'memory_type': 'buffer_summary',
            'content': summary,
            'relevance_score': 1.0,
            'summary_date': now.date().isoformat(),
            'metadata': {
                'thread_id': thread_id,
                'source': {
                    'type': 'conversation',
                    'timestamp': now.isoformat()
                },
                'processing': {
                    'generated_at': now.isoformat(),
                    'version': '2.0'
                }
            },
            'created_at': now.isoformat()
        }
    

    async def create_buffer_summary(
        self,
        thread_id: str,
        messages: List[Dict],
        user_id: str,
        supabase_client
    ) -> SummaryResult:
        """Create summary of buffered messages"""
        try:
            logger.info(f"Creating buffer summary for thread {thread_id}")

            # Ensure creator profile exists before creating buffer summary
            from src.simple_memory import SimpleMemory
            memory = SimpleMemory(supabase_client, user_id)
            await memory.ensure_creator_profile(user_id)

            # Format messages
            conversation_text = self._format_messages(messages)
            
            # Generate summary
            summary_result = await self.summarizer.ainvoke(conversation_text)

            # Prepare storage data
            summary_data = self._create_summary_data(
                user_id,
                thread_id,
                summary_result["final_summary"]
            )

            # output structured summary in logs for testing
            logger.info("\n=== BUFFER SUMMARY ===")
            logger.info(f"Thread ID: {thread_id}")
            logger.info(f"User ID: {user_id}")
            logger.info("Metadata:")
            logger.info(f"  Memory Type: {summary_data['memory_type']}")
            logger.info(f"  Relevance Score: {summary_data['relevance_score']}")
            logger.info(f"  Generated: {summary_data['created_at']}")
            logger.info("\nSummary Content:")
            logger.info(f"{summary_result['final_summary']}")
            logger.info("====================")
            # Database operations with error handling
            try:
                # Store new summary
                supabase_client.table('memory').insert(summary_data).execute()
                logger.debug(f"Stored buffer summary for thread {thread_id}")

                # Check messages before deletion
                before_delete = supabase_client.table('memory')\
                    .select('*')\
                    .eq('user_id', user_id)\
                    .eq('metadata->>thread_id', thread_id)\
                    .eq('memory_type', 'message')\
                    .execute()

                logger.info(f"[DEBUG] Before deletion in thread {thread_id}: {len(before_delete.data) if before_delete.data else 0} messages found.")

                # Clear old messages
                delete_response = supabase_client.table('memory')\
                    .delete()\
                    .eq('user_id', user_id)\
                    .eq('metadata->>thread_id', thread_id)\
                    .eq('memory_type', 'message')\
                    .execute()
                
                logger.info(f"[DEBUG] Delete operation response for thread {thread_id}: {delete_response.data}")

                # Verify deletion was successful
                after_delete = supabase_client.table('memory')\
                    .select('*')\
                    .eq('user_id', user_id)\
                    .eq('metadata->>thread_id', thread_id)\
                    .eq('memory_type', 'message')\
                    .execute()

                logger.info(f"[DEBUG] After deletion in thread {thread_id}: {len(after_delete.data) if after_delete.data else 0} messages remain.")

                if len(after_delete.data) > 0:
                    logger.warning(f"Some messages remain after deletion for thread {thread_id}")



                return SummaryResult(
                    summary=summary_result["final_summary"],
                    metadata=summary_data["metadata"]
                )

            except Exception as e:
                logger.error(f"Database operation failed for thread {thread_id}: {e}", exc_info=True)
                raise

        except Exception as e:
            logger.error(f"Buffer summary creation failed for thread {thread_id}: {e}", exc_info=True)
            return SummaryResult("", {}, str(e))
        
class TranscriptSummaryHandler:
    """Specialized handler for transcript processing and summarization.
    
    This class is responsible for transcript-specific processing, including:
    1. Normalizing transcript format (cleaning speaker/message structure)
    2. Configuring the shared ContentSummarizer for transcript processing
    3. Generating and storing transcript summaries
    
    Important architectural note:
    This class does NOT own the ContentSummarizer instance. Instead, it:
    1. Receives a reference to the shared instance from TranscriptManager
    2. Temporarily configures it for transcript processing
    3. Can reset it back to default settings when done
    
    This design ensures:
    - Efficient resource usage (no duplicate model instances)
    - Consistent summarization behavior
    - Clear separation between general and transcript-specific logic
    """
    
    def __init__(self, summarizer: ContentSummarizer):
        """Initialize with a shared ContentSummarizer instance.
        
        This handler receives (not creates) a ContentSummarizer instance from
        TranscriptManager. It will configure this instance for transcript processing
        by setting the appropriate prompt.
        
        Flow:
        1. Store reference to shared summarizer
        2. Configure it with transcript-specific prompt
        3. Rebuild the processing chain with new prompt
        
        Args:
            summarizer: Shared ContentSummarizer instance from TranscriptManager.
                       Will be configured for transcript processing.
        """

        self.summarizer = summarizer
        # Configure the shared summarizer for transcript processing
        self.summarizer.map_prompt = TRANSCRIPT_PROMPT
        self.summarizer.setup_chain()
        
    @staticmethod
    def normalize_transcript(content: str) -> str:
        """Normalize transcript content to consistent format."""
        try:
            segments = content.split("\n\n")
            clean_messages = []
            current_speaker = None
            current_message = []
            
            for segment in segments:
                lines = segment.strip().split("\n")
                if not lines:
                    continue
                    
                for line in lines:
                    if ": " in line:
                        speaker, message = line.split(": ", 1)
                        
                        if speaker == current_speaker:
                            current_message.append(message)
                        else:
                            if current_speaker and current_message:
                                clean_messages.append(f"{current_speaker}: {' '.join(current_message)}")
                            current_speaker = speaker
                            current_message = [message]
                    else:
                        if current_speaker and line.strip():
                            current_message.append(line.strip())
            
            if current_speaker and current_message:
                clean_messages.append(f"{current_speaker}: {' '.join(current_message)}")
            
            return "\n\n".join(clean_messages)
            
        except Exception as e:
            logger.error(f"Error normalizing transcript: {str(e)}", exc_info=True)
            return content
        
    async def generate_meeting_summary(
        self,
        transcript: str,
        meeting_id: str,
        user_id: str,
        team_id: str,
        supabase_client,
        metadata: Dict[str, Any]
    ) -> SummaryResult:
        """Generate meeting summary using the configured summarizer."""
        try:
            logger.info(f"Generating summary for meeting {meeting_id}")
            
            # Use the map-reduce summarizer 
            result = await self.summarizer.ainvoke(transcript)

            # Create structured result
            summary_data = {
                "meeting_id": meeting_id,
                "team_id": team_id,
                "summary": result["final_summary"],
                "metadata": {
                    "meeting_info": {
                        "id": meeting_id,
                        "topic": metadata.get("topic", ""),
                        "duration_minutes": metadata.get("duration", 0),
                        "zoom_user_id": user_id
                    },
                    "generated_at": datetime.now(timezone.utc).isoformat()
                }
            }
            
            # Enhanced logging to show structured data
            logger.info("\n=== TRANSCRIPT SUMMARY ===")
            logger.info(f"Meeting ID: {meeting_id}")
            logger.info(f"Team ID: {team_id}")
            logger.info("Metadata:")
            logger.info(f"  Topic: {metadata.get('topic', '')}")
            logger.info(f"  Duration: {metadata.get('duration', 0)} minutes")
            logger.info(f"  Generated: {datetime.now(timezone.utc).isoformat()}")
            logger.info("\nSummary Content:")
            logger.info(f"{result['final_summary']}")
            logger.info("========================")
            # Store the summary
            supabase_client.table("transcripts").insert(summary_data).execute()
            
            return SummaryResult(
                summary=result["final_summary"],
                metadata=summary_data["metadata"]
            )

        except Exception as e:
            logger.error(f"Error generating meeting summary: {str(e)}", exc_info=True)
            return SummaryResult("", {}, str(e))


class ProjectUpdateHandler:
    def __init__(self, summarizer: ContentSummarizer):
        self.summarizer = summarizer
        # Configure the shared summarizer for transcript processing
        self.summarizer.reduce_prompt = PROJECT_UPDATE_PROMPT
        self.summarizer.setup_chain()

    def _validate_and_format_dates(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> tuple[date, date]:
        """Validate and standardize date inputs"""
        if start_date is None:
            start_date = datetime.now(timezone.utc).date()
        elif isinstance(start_date, datetime):
            start_date = start_date.date()
        elif not isinstance(start_date, date):
            raise ValueError("start_date must be a datetime or date object")

        if end_date is None:
            end_date = start_date
        elif isinstance(end_date, datetime):
            end_date = end_date.date()
        elif not isinstance(end_date, date):
            raise ValueError("end_date must be a datetime or date object")

        return start_date, end_date

    def _format_conversation_text(self, conversations) -> str:
        """Format conversations into analyzable text"""
        return "\n\n".join([
            f"{conv['role'].upper()}: {conv['message_text']} [{conv['created_at']}]"
            for conv in conversations.data
        ])

    async def generate_project_update(
        self,
        user_id: str,
        supabase_client,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Optional[SummaryResult]:
        """Generate summary of daily project status from conversations"""
        try:
            # Validate and format dates
            start_date, end_date = self._validate_and_format_dates(start_date, end_date)
            logger.info(f"Generating project update for {user_id} from {start_date} to {end_date}")

            #get user project ID from overview table
            project_result = supabase_client.table('project_overview')\
                .select('id')\
                .eq('user_id', user_id)\
                .limit(1)\
                .execute()

            if project_result.data:
                project_id = project_result.data[0]['id']
            else:
                logger.error(f"No project found for user {user_id}")
                return None
            
            # Fetch conversations
            conversations = supabase_client.table('conversations')\
                .select('*')\
                .eq('user_id', user_id)\
                .gte('created_at', f'{start_date.isoformat()}T00:00:00Z')\
                .lt('created_at', f'{(end_date + timedelta(days=1)).isoformat()}T00:00:00Z')\
                .order('created_at')\
                .execute()
        except Exception as e:
            logger.error(f"Failed to fetch conversations for user {user_id}: {e}", exc_info=True)
            return None

        if not conversations.data:
            logger.info(f"No conversations found for user {user_id} in date range")
            return None

        # Process conversations
        conversation_text = self._format_conversation_text(conversations)
        logger.debug(f"Processing {len(conversations.data)} conversations")

        # Generate summary
        summary_result = await self.summarizer.ainvoke(conversation_text)

        # Parse summary into project update format
        try:
            # Parse the JSON result
            project_update = json.loads(summary_result["final_summary"])
            

        ###### seems we're not actually formatting the info to match the schema#####
        
            # Add required fields
            project_update.update({
                'project_id': project_id,
                'user_id': user_id,
                'update_date': end_date.isoformat()
            })
            
            # Store with upsert
            supabase_client.table('project_updates')\
                .upsert(project_update, on_conflict='project_id,update_date')\
                .execute()
            logger.info(f"Successfully stored project update for {user_id}")
            
            return SummaryResult(
                summary=summary_result["final_summary"]
            )

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse project update JSON: {e}", exc_info=True)
            return None