"""
transcript_search.py
------------------
Manages Zoom meeting content processing, storage, and retrieval.

Core Responsibilities:
1. Process and store raw transcripts and video metadata
2. Generate and store transcript summaries
3. Provide transcript search and retrieval capabilities
4. Interface with content_summarizer.py for analysis

Data Flow:
zoom_transcript_retrieval.py -> process_raw_content -> store_raw_transcript -> generate_summary -> store_processed_transcript

Storage:
- transcript_raw: Unprocessed meeting transcripts
- transcripts: Processed transcripts with summaries
- meeting_recordings: Video metadata and storage info
"""
# Standard library imports
import logging
from datetime import datetime, timezone

# Third-party imports
from supabase import Client, create_client
import json

# Local imports
from src.config import Config
# Add these to existing imports
from src.content_summarizer import ContentSummarizer, TranscriptSummaryHandler, SummaryResult
from typing import Dict, List, Optional, Any, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TranscriptManager:
    """Top-level coordinator for all transcript-related operations.
    
    This class serves as the main entry point and coordinator for all transcript processing.
    It owns the core ContentSummarizer instance and delegates specialized processing to
    TranscriptSummaryHandler.
    
    Architecture:
    - TranscriptManager (this class)
      └── Owns ContentSummarizer (single instance for all summarization)
          └── Delegated to TranscriptSummaryHandler for transcript-specific processing
    
    This hierarchy ensures:
    1. Single source of truth for summarization (one ContentSummarizer instance)
    2. Efficient resource usage (no duplicate model instances)
    3. Clear separation of responsibilities
    """
    
    def __init__(self, supabase_client: Client):
        """Initialize the transcript management system.
        
        Creates a single ContentSummarizer instance that will be used for all summarization
        tasks. This instance is then shared with TranscriptSummaryHandler, which will
        temporarily configure it for transcript-specific processing when needed.
        
        Flow:
        1. Create single ContentSummarizer (owned by this class)
        2. Pass that summarizer to TranscriptSummaryHandler
        3. TranscriptHandler configures summarizer with transcript prompt when needed
        
        Args:
            supabase_client: Initialized Supabase client for database operations
        """
        self.supabase = supabase_client
        # Create and own the single summarizer instance - this is the source of truth
        # for all summarization operations across the system
        self.content_summarizer = ContentSummarizer()
        
        # Create transcript handler and pass our summarizer instance
        # The handler will configure the summarizer for transcript processing when needed
        self.transcript_handler = TranscriptSummaryHandler(self.content_summarizer)

        # Raw Content Processing Methods
        # -----------------------------

      
    async def process_raw_meeting_content(
        self,
        content: Dict[str, Any],
        supabase_client
    ) -> Tuple[bool, Optional[str]]:
        """
        Process meeting content received from Zoom webhook and API.
        
        Expected content structure:
        {
            "transcript": str,          # Raw transcript from Zoom
            "recordings": {             # Recording info from Zoom API
                "topic": str,
                "host_id": str,
                "recording_files": []
            },
            "metadata": {
                "meeting_id": str,
                "retrieval_time": str,  # ISO format
                "source": "zoom",
                "user_id": str,
                "recording_count": int,
                "host_id": str,
                "topic": str,
                "start_time": str,
                "duration": int
            }
        }
        
        Args:
            content: Dictionary containing meeting data from Zoom
            supabase_client: Initialized Supabase client
                
        Returns:
            tuple: (success boolean, normalized transcript if successful)
        """
        try:
            meeting_id = content["metadata"]["meeting_id"]
            logger.info(f"=== Processing Zoom Meeting Content for {meeting_id} ===")
            
            # Step 1: Validate and normalize transcript
            if not content.get("transcript"):
                logger.warning(f"No transcript found for meeting {meeting_id}")
                return False, None
                
            normalized_transcript = self.summarizer.normalize_transcript(content["transcript"])
            if not normalized_transcript:
                logger.warning("Normalization produced empty transcript")
                return False, None
                
            # Step 2: Get team_id
            team_id = None  # Initialize to None
            try:
                meeting_info = (supabase_client.table("meetings")
                                .select("team_id")
                                .eq('zoom_meeting_id', meeting_id)
                                .single()
                                .execute())
                
                if meeting_info.data and "team_id" in meeting_info.data:
                    team_id = meeting_info.data["team_id"]
                    logger.info(f"✅ Successfully linked meeting {meeting_id} to team {team_id}")
            except Exception as e:
                logger.warning(f"⚠️ Error linking team for meeting {meeting_id}: {str(e)}")

            # Step 3: Store raw transcript
            raw_transcript_data = {
                "meeting_id": meeting_id,
                "content": normalized_transcript,
                "team_id": team_id,
                "metadata": {
                    "topic": content["metadata"].get("topic", ""),
                    "host_id": content["metadata"].get("host_id", ""),
                    "retrieval_time": content["metadata"].get("retrieval_time"),
                    "source": content["metadata"].get("source")
                }
            }
            if team_id:
                raw_transcript_data["team_id"] = team_id
                
            supabase_client.table("transcript_raw").insert(raw_transcript_data).execute()
            logger.info("✅ Successfully stored raw transcript")
            
            # Step 4: Generate and store summary
            logger.info(f"\n=== Generating Meeting Summary for {meeting_id} ===")
            summary_result = await self.summarizer.generate_meeting_summary(
                transcript=normalized_transcript,
                meeting_id=meeting_id,
                team_id=team_id,
                user_id=content["metadata"].get("user_id"),
                supabase_client=supabase_client,
                metadata={
                    "topic": content["metadata"].get("topic", ""),
                    "duration": content["metadata"].get("duration", 0),
                    "start_time": content["metadata"].get("start_time", ""),
                    "source": content["metadata"].get("source", "zoom")
                }
            )

            # Step 5: Store recordings if present
            if content.get("recordings") and content["recordings"].get("recording_files"):
                recording_count = len(content["recordings"]["recording_files"])
                logger.info(f"Processing {recording_count} recordings")
                
                for idx, recording in enumerate(content["recordings"]["recording_files"], 1):
                    if recording["file_type"] == "MP4":
                        recording_data = {
                            "meeting_id": meeting_id,
                            "video_url": recording.get("download_url", ""),
                            "metadata": {
                                "host_id": content["metadata"].get("host_id"),
                                "source": "zoom",
                                "recorded_at": content["metadata"].get("start_time")
                            }
                        }
                        if team_id:
                            recording_data["team_id"] = team_id
                            
                        supabase_client.table("meeting_recordings").insert(recording_data).execute()
                        logger.info(f"✅ Stored recording {idx}/{recording_count}")

            logger.info(f"\n=== Completed Processing for Meeting {meeting_id} ===")
            return True, normalized_transcript
                    
        except Exception as e:
            logger.error(f"\n❌ Error processing meeting content: {str(e)}")
            logger.error("Detailed error information:", exc_info=True)
            return False, None

    async def store_transcript(
        self,
        meeting_id: str,
        transcript: str,
        metadata: Dict[str, Any]
    ) -> bool:
        """Store processed transcript with generated summary.
        
        Args:
            meeting_id: Unique identifier for the meeting
            transcript: Normalized transcript text
            metadata: Additional meeting metadata
            
        Returns:
            bool: Success status
        """
        try:
            logger.info(f"Storing transcript for meeting ID: {meeting_id}")
            
            # Generate summary
            summary_result = await self.summarizer.generate_meeting_summary(
                transcript=transcript,
                meeting_id=meeting_id,
                user_id=metadata.get('user_id'),
                metadata=metadata,
                supabase_client=self.supabase
            )
            
            if summary_result.error:
                logger.error(f"Summary generation failed: {summary_result.error}")
                return False
            
            # Store transcript and summary
            transcript_data = {
                "meeting_id": meeting_id,
                # Remove transcript_text since it's not in schema
                "summary": summary_result.summary,
                "metadata": {**metadata, **summary_result.metadata},
                # zoom_meeting_id should probably go in metadata since there's no column for it
                #"user_id": metadata.get("user_id"),  # Added as it's required
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            
            result = self.supabase.table("transcripts").insert(transcript_data).execute()
            
            if result.data:
                logger.info(f"Successfully stored transcript for meeting ID: {meeting_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error storing transcript: {str(e)}", exc_info=True)
            return False

    # Retrieval and Search Methods
    # ---------------------------

    def get_transcript(
        self, 
        meeting_id: str, 
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        """Retrieve transcript and summary by meeting ID.
        
        Args:
            meeting_id: Meeting identifier
            user_id: User identifier for access control
            
        Returns:
            Optional[Dict]: Transcript data including summary and metadata, or None if not found
        """
        try:
            logger.info(f"Retrieving transcript for meeting ID: {meeting_id}")
            
            result = self.supabase.table("transcripts")\
                .select("*")\
                .eq("meeting_id", meeting_id)\
                .eq("user_id", user_id)\
                .limit(1)\
                .execute()
                
            if result.data:
                transcript_data = result.data[0]
                return {
                    #"transcript": transcript_data.get("transcript_text"),
                    "summary": transcript_data.get("summary"),
                    "metadata": transcript_data.get("metadata", {})
                }
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving transcript: {str(e)}", exc_info=True)
            return None

    async def search_transcripts(
        self,
        query: str,
        user_id: str = "system",
        limit: int = 4
    ) -> List[Dict[str, Any]]:
        """Search transcripts using full-text search.
        
        Args:
            query: Search query string
            user_id: User identifier for access control
            limit: Maximum number of results to return
            
        Returns:
            List[Dict]: List of matching transcript previews with metadata
        """
        try:
            logger.info(f"Searching transcripts for query: '{query}' (user: {user_id})")
            
            result = self.supabase.rpc(
                'search_all_content',
                {
                    'p_query': query,
                    'p_user_id': user_id
                }
            ).eq('content_type', 'transcript').limit(limit).execute()
            
            if not result.data:
                return []
                
            processed_results = []
            for item in result.data:
                processed_results.append({
                    "content": item.get("content", "")[:200],  # Preview
                    "full_content": item.get("content", ""),
                    "meeting_id": item.get("meeting_id"),
                    "created_at": item.get("created_at"),
                    "metadata": item.get("metadata", {})
                })
            
            return processed_results
            
        except Exception as e:
            logger.error(f"Error searching transcripts: {str(e)}", exc_info=True)
            return []    

# Singleton Instance Management
# ---------------------------

_transcript_manager = None

def get_transcript_manager() -> TranscriptManager:
    """Get or create the singleton TranscriptManager instance.
    
    Creates a new instance with Supabase connection if none exists,
    otherwise returns the existing instance.
    
    Returns:
        TranscriptManager: Singleton instance of TranscriptManager
    """
    global _transcript_manager
    if _transcript_manager is None:
        supabase_client = create_client(Config.SUPABASE_URL, Config.SUPABASE_SERVICE_KEY)
        _transcript_manager = TranscriptManager(supabase_client)
    return _transcript_manager


# Convenience Functions
# -------------------

async def store_transcript(
    meeting_id: str, 
    transcript: str, 
    metadata: Dict[str, Any]
) -> bool:
    """Store transcript using the singleton TranscriptManager.
    
    Args:
        meeting_id: Meeting identifier
        transcript: Transcript content
        metadata: Additional meeting metadata
        
    Returns:
        bool: Success status
    """
    manager = get_transcript_manager()
    return await manager.store_transcript(meeting_id, transcript, metadata)


def get_transcript(
    meeting_id: str, 
    user_id: str
) -> Optional[Dict[str, Any]]:
    """Retrieve transcript using the singleton TranscriptManager.
    
    Args:
        meeting_id: Meeting identifier
        user_id: User identifier for access control
        
    Returns:
        Optional[Dict]: Transcript data or None if not found
    """
    manager = get_transcript_manager()
    return manager.get_transcript(meeting_id, user_id)


async def search_transcripts(
    query: str, 
    user_id: str = "system", 
    limit: int = 4
) -> List[Dict[str, Any]]:
    """Search transcripts using the singleton TranscriptManager.
    
    Args:
        query: Search query string
        user_id: User identifier for access control
        limit: Maximum number of results to return
        
    Returns:
        List[Dict]: List of matching transcript previews
    """
    manager = get_transcript_manager()
    return await manager.search_transcripts(query, user_id, limit)


