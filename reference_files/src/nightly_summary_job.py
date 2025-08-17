# nightly_summary_job.py

## Purpose and Function
# This script is run nightly by the Heroku scheduler to generate daily conversation summaries.
# 
# Flow:
# 1. Gets triggered automatically by Heroku scheduler (runs after midnight UTC)
# 2. By default, processes YESTERDAY's conversations (since it runs after midnight)
# 3. For each user who had conversations yesterday:
#    - Generates a summary of their conversations
#    - Stores these summaries in the database
# 
# Usage:
# - Automatic: Runs nightly via Heroku scheduler (processes yesterday)
# - Manual: Can be run with --date YYYY-MM-DD to generate summaries for a specific date
# - Debug: Use --test flag for detailed logging
# 
# FIXED: Changed default behavior to process yesterday's conversations instead of today's

import logging
from supabase.client import create_client
from src.config import Config
import os
from slack_bolt.async_app import AsyncApp
import supabase
from datetime import timedelta, datetime, timezone
from src.content_summarizer import ContentSummarizer, DailySummaryHandler
from typing import Optional
import asyncio
import argparse

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_nightly_summaries(target_date: Optional[datetime] = None, test_mode: bool = False):
    """Scheduled job to generate daily summaries for all users.
    This is the entry point called by Heroku scheduler."""
    try:
        start_time = datetime.now()
        logger.info(f"Starting nightly summary job at {start_time}")
        
        try:
            supabase_client = create_client(Config.SUPABASE_URL, Config.SUPABASE_SERVICE_KEY)
        except Exception as e:
            logger.error(f"Failed to create Supabase client: {str(e)}")
            raise RuntimeError("Database connection failed") from e
            
        try:
            summarizer = ContentSummarizer()
            handler = DailySummaryHandler(summarizer)
        except Exception as e:
            logger.error(f"Failed to initialize summarizer components: {str(e)}")
            raise RuntimeError("Summarizer initialization failed") from e
    
        # Calculate date range
        # FIXED: Default to YESTERDAY when no target_date specified (for scheduled runs)
        if target_date is None:
            # When run by scheduler after midnight, we want yesterday's data
            base_date = (datetime.now(timezone.utc) - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            logger.info("No target date specified, defaulting to YESTERDAY for scheduled run")
        else:
            base_date = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
        next_date = base_date + timedelta(days=1)

        logger.info(f"Running summaries for date: {base_date.date().isoformat()}")
        logger.info(f"Processing conversations from {base_date.isoformat()} to {next_date.isoformat()}")
        
        if test_mode:
            logger.info("🧪 RUNNING IN TEST MODE 🧪")
            logger.info(f"Date: {target_date or 'Today'}")
            # Debug query to see data format
            debug_query = supabase_client.table('conversations')\
                .select('*')\
                .limit(5)\
                .execute()
            logger.info(f"Debug: Recent conversations format: {debug_query.data if debug_query.data else 'No data found'}")

        # Get all conversations for the date range and process each user
        users = handler.get_users_needing_summaries(
            supabase_client, 
            start_date=base_date.date(),
            end_date=next_date.date()
        )
        
        if test_mode:
            logger.info(f"\n👥 Found {len(users)} users with conversations")
            if users:  # Only try to get sample conversations if we have users
                # Get a sample of conversations for debugging
                sample_convos = supabase_client.table('conversations')\
                    .select('*')\
                    .eq('user_id', users[0])\
                    .gte('created_at', base_date.isoformat())\
                    .lt('created_at', next_date.isoformat())\
                    .execute()
                                
                logger.info(f"\nFound {len(sample_convos.data)} conversations for first user")
                if sample_convos.data:
                    logger.info(f"Sample conversation timestamps:")
                    for conv in sample_convos.data[:3]:  # Show first 3 conversations
                        logger.info(f"- {conv['created_at']}: {conv['message_text'][:50]}...")
        
        async def has_conversations_in_range(supabase_client, user_id, start_date, end_date):
            conversations = supabase_client.table('conversations')\
                .select('id')\
                .eq('user_id', user_id)\
                .gte('created_at', start_date.isoformat())\
                .lt('created_at', end_date.isoformat())\
                .execute()
            return len(conversations.data) > 0

        async def clear_user_memory(supabase_client, user_id: str, test_mode: bool = False):
            """Clear all memory entries for a user after daily summary is generated"""
            try:
                if test_mode:
                    logger.info(f"\n🧹 Clearing memory table for user {user_id}")
                    
                # Get count before deletion for logging
                before_count = supabase_client.table('memory')\
                    .select('*', count='exact')\
                    .eq('user_id', user_id)\
                    .execute()
                    
                # Perform deletion
                result = supabase_client.table('memory')\
                    .delete()\
                    .eq('user_id', user_id)\
                    .execute()
                    
                if test_mode:
                    logger.info(f"Cleared {before_count.count if before_count.data else 0} entries from memory table")
                
                return result
                
            except Exception as e:
                logger.error(f"Error clearing memory table for user {user_id}: {str(e)}")
                raise

        #Process each user
        for user_id in users:
            if test_mode:
                logger.info(f"\n=== Processing User {user_id} ===")
                logger.info(f"Date range: {base_date.date().isoformat()} to {next_date.date().isoformat()}")
            
            # Check if user has conversations before processing
            if not await has_conversations_in_range(supabase_client, user_id, base_date, next_date):
                if test_mode:
                    logger.info(f"Skipping user {user_id} - no conversations in date range")
                continue

            # Generate summary
            success = await handler.generate_daily_summary(
                user_id=user_id,
                supabase_client=supabase_client,
                start_date=base_date,
                end_date=next_date 
            )
            
            # Clear memory table after successful summary generation
            if success and success.error is None:
                await clear_user_memory(supabase_client, user_id, test_mode)
            
            if test_mode:
                # Get the generated summary to verify
                recent_summaries = supabase_client.table('longterm_memory')\
                    .select('*')\
                    .eq('user_id', user_id)\
                    .eq('summary_date', base_date.date().isoformat())\
                    .execute()
                
                if recent_summaries.data:
                    summary = recent_summaries.data[0]  # Get most recent if multiple
                    logger.info(f"\nGenerated Summary Preview:")
                    logger.info(f"Content: {summary['content'][:200]}...")
                    logger.info(f"Metadata: {summary['metadata']}")
                    
                status = "✅ Success" if success and success.error is None else "❌ Failed"
                logger.info(f"Summary generation: {status}")
                
            if test_mode:
                duration = datetime.now() - start_time
                logger.info(f"\n🏁 Test run completed in {duration.total_seconds():.2f} seconds")
                logger.info(f"Total users processed: {len(users)}")

    except Exception as e:
        logger.error(f"Nightly summary job failed: {str(e)}", exc_info=True)
        raise

async def check_summary_stats():
    """Check summary statistics for yesterday"""
    yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).date()
    today = datetime.now(timezone.utc).date()
    
    supabase_client = create_client(Config.SUPABASE_URL, Config.SUPABASE_SERVICE_KEY)
    
    # Get summaries created for yesterday's date
    summaries = supabase_client.table('longterm_memory')\
        .select('*')\
        .eq('summary_date', yesterday.isoformat())\
        .execute()
    
    # Get conversations from yesterday
    conversations = supabase_client.table('conversations')\
        .select('user_id')\
        .gte('created_at', f'{yesterday.isoformat()}T00:00:00Z')\
        .lt('created_at', f'{today.isoformat()}T00:00:00Z')\
        .execute()
    
    # Count unique users with conversations
    unique_users = set()
    if conversations.data:
        unique_users = set(conv['user_id'] for conv in conversations.data)
        
    logger.info(f"\n=== Summary Stats for {yesterday.isoformat()} ===")
    logger.info(f"Date processed: {yesterday}")
    logger.info(f"Summaries generated: {len(summaries.data)}")
    logger.info(f"Unique users with conversations: {len(unique_users)}")
    logger.info(f"Total conversations: {len(conversations.data)}")
    
    if len(unique_users) > len(summaries.data):
        missing_count = len(unique_users) - len(summaries.data)
        logger.warning(f"⚠️  {missing_count} users are missing summaries!")
        
        # Find which users are missing
        summarized_users = {s['user_id'] for s in summaries.data} if summaries.data else set()
        missing_users = unique_users - summarized_users
        
        logger.info("\nUsers missing summaries:")
        for user_id in list(missing_users)[:5]:  # Show first 5
            logger.info(f"  - {user_id}")
        if len(missing_users) > 5:
            logger.info(f"  ... and {len(missing_users) - 5} more")

if __name__ == "__main__":
    def parse_date(date_str: str) -> datetime:
        try:
            return datetime.strptime(date_str, '%Y-%m-%d').replace(tzinfo=timezone.utc)
        except ValueError as e:
            raise argparse.ArgumentTypeError(f"Invalid date format. Use YYYY-MM-DD: {e}")
    
    parser = argparse.ArgumentParser(description='Run nightly summaries for YESTERDAY by default')
    parser.add_argument('--date', type=parse_date, help='Optional: Date to run summaries for (YYYY-MM-DD). If not specified, processes yesterday.')
    parser.add_argument('--test', action='store_true', help='Run in test mode with extra logging')
    parser.add_argument('--check', action='store_true', help='Check summary stats for yesterday')
    
    args = parser.parse_args()
    
    try:
        if args.check:
            asyncio.run(check_summary_stats())
        else:
            asyncio.run(run_nightly_summaries(target_date=args.date, test_mode=args.test))
    except Exception as e:
        logger.error(f"Nightly summary job failed: {str(e)}")
        raise  # Re-raise the exception for proper error handling