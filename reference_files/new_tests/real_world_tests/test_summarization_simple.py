#!/usr/bin/env python3
"""
Simple Summarization Test

Tests basic summarization functionality against the live dev environment.
"""

import os
import sys
import asyncio
import uuid
from datetime import datetime, timezone, timedelta

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from supabase import create_client
from src.content_summarizer import ContentSummarizer, DailySummaryHandler
from src.simple_memory import SimpleMemory
from src.config import Config

async def test_summarization():
    """Test the summarization system"""
    print("🧪 Testing Summarization System")
    
    # Create test user with proper UUID format
    test_user_id = str(uuid.uuid4())
    supabase_client = create_client(Config.SUPABASE_URL, Config.SUPABASE_SERVICE_KEY)
    
    try:
        # Test 1: Basic ContentSummarizer
        print("\n1. Testing ContentSummarizer...")
        summarizer = ContentSummarizer()
        
        test_content = """
        User: I'm working on a children's book about a young astronaut named Luna.
        Assistant: That sounds wonderful! Tell me more about Luna's adventures.
        User: Luna discovers a planet where all the colors have disappeared.
        Assistant: What an imaginative concept! How does Luna help restore the colors?
        User: She meets friendly alien creatures who each hold a piece of the color spectrum.
        """
        
        summary_result = await summarizer.ainvoke(test_content)
        print(f"✅ Summary generated: {summary_result['final_summary'][:100]}...")
        
        # Test 2: Daily Summary Handler
        print("\n2. Testing Daily Summary Handler...")
        
        # First, create creator profile (required for foreign key constraint)
        print("👤 Creating creator profile...")
        memory_handler = SimpleMemory(supabase_client, test_user_id)
        await memory_handler.ensure_creator_profile(test_user_id)
        
        # Create some conversation data from yesterday
        yesterday = datetime.now(timezone.utc) - timedelta(days=1)
        
        conversation_data = [
            {
                'user_id': test_user_id,  # Now using proper UUID
                'message_text': "I've been working on my novel and made great progress today.",
                'role': 'user',
                'context': {'session_type': 'writing'},
                'metadata': {},
                'created_at': yesterday.isoformat()
            },
            {
                'user_id': test_user_id,
                'message_text': "That's wonderful! Tell me about the progress you made.",
                'role': 'assistant',
                'context': {'session_type': 'writing'},
                'metadata': {},
                'created_at': yesterday.isoformat()
            },
            {
                'user_id': test_user_id,
                'message_text': "I finished chapter 3 and outlined chapter 4. My protagonist is really developing.",
                'role': 'user',
                'context': {'session_type': 'writing'},
                'metadata': {},
                'created_at': yesterday.isoformat()
            }
        ]
        
        # Insert conversation data
        print("📝 Creating conversation data...")
        for conv in conversation_data:
            supabase_client.table('conversations').insert(conv).execute()
        
        # Run daily summarization
        print("🔄 Running daily summarization...")
        daily_handler = DailySummaryHandler(summarizer)
        
        result = await daily_handler.generate_daily_summary(
            user_id=test_user_id,
            supabase_client=supabase_client,
            start_date=yesterday,
            end_date=yesterday + timedelta(hours=23, minutes=59)
        )
        
        if result:
            print("✅ Daily Summary Generated:")
            print(f"   Summary: {result.summary[:200]}...")
            print(f"   Metadata: {result.metadata}")
            
            # Check if summary was stored in longterm_memory
            longterm_summaries = supabase_client.table('longterm_memory')\
                .select('*')\
                .eq('user_id', test_user_id)\
                .execute()
            
            print(f"📊 Found {len(longterm_summaries.data)} longterm memory entries")
            
            if longterm_summaries.data:
                print("✅ Summary successfully stored in database")
                
                # Show some details of the stored summary
                summary_entry = longterm_summaries.data[0]
                print(f"   Stored summary content: {summary_entry['content'][:150]}...")
                print(f"   Memory type: {summary_entry.get('memory_type', 'N/A')}")
            else:
                print("⚠️  Summary not found in database")
        else:
            print("⚠️  No daily summary generated")
        
        print("\n🎉 Summarization test completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Cleanup test data - use proper table names and column names
        print("\n🧹 Cleaning up test data...")
        cleanup_tables = [
            ('memory', 'user_id'),
            ('conversations', 'user_id'), 
            ('longterm_memory', 'user_id'),
            ('project_updates', 'user_id'),
            ('creator_profiles', 'id')  # creator_profiles uses 'id' not 'user_id'
        ]
        
        for table, id_column in cleanup_tables:
            try:
                result = supabase_client.table(table).delete().eq(id_column, test_user_id).execute()
                print(f"✅ Cleaned up {table}")
            except Exception as e:
                print(f"Cleanup error for {table}: {e}")

if __name__ == "__main__":
    asyncio.run(test_summarization())
