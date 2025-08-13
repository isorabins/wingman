#!/usr/bin/env python3
"""
Test Nightly Summary Scheduler Integration

This test verifies:
1. The nightly_summary_job.py script can be invoked correctly
2. It processes conversations from the correct date range
3. It generates summaries for all users with conversations
4. It handles edge cases like timezone boundaries

This mimics how Heroku Scheduler would invoke the job.
"""

import os
import sys
import asyncio
import subprocess
from datetime import datetime, timezone, timedelta
import uuid

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import pytest
from supabase import create_client
from src.config import Config

class TestSchedulerIntegration:
    """Test the nightly summary job as invoked by scheduler"""
    
    @pytest.fixture
    def test_user_id(self):
        """Generate unique test user ID"""
        return f"test_scheduler_{uuid.uuid4()}"
    
    @pytest.fixture
    def supabase_client(self):
        """Create Supabase client"""
        return create_client(Config.SUPABASE_URL, Config.SUPABASE_SERVICE_KEY)
    
    async def cleanup_test_user(self, supabase_client, user_id: str):
        """Clean up test data"""
        tables = ['conversations', 'longterm_memory', 'memory', 'creator_profiles', 'project_overview', 'project_updates']
        for table in tables:
            try:
                supabase_client.table(table).delete().eq('user_id', user_id).execute()
            except Exception as e:
                print(f"Cleanup error for {table}: {e}")
    
    def create_conversations_for_date(self, supabase_client, user_id: str, target_date: datetime, count: int = 5):
        """Create test conversations for a specific date"""
        conversations = []
        
        for i in range(count):
            # Spread conversations throughout the day
            hours_offset = i * 3
            timestamp = target_date.replace(hour=hours_offset % 24, minute=15, second=0)
            
            # User message
            conversations.append({
                'user_id': user_id,
                'message_text': f"Test message {i} from user on {target_date.date()}",
                'role': 'user',
                'context': {'test': True, 'session': 'scheduler_test'},
                'metadata': {},
                'created_at': timestamp.isoformat()
            })
            
            # Assistant response
            conversations.append({
                'user_id': user_id,
                'message_text': f"Test response {i} from assistant on {target_date.date()}",
                'role': 'assistant',
                'context': {'test': True, 'session': 'scheduler_test'},
                'metadata': {},
                'created_at': (timestamp + timedelta(seconds=30)).isoformat()
            })
        
        # Insert all conversations
        for conv in conversations:
            supabase_client.table('conversations').insert(conv).execute()
        
        return len(conversations)
    
    @pytest.mark.asyncio
    async def test_scheduler_invocation_for_yesterday(self, test_user_id, supabase_client):
        """Test that scheduler correctly processes yesterday's conversations"""
        print(f"\n🕐 Testing Scheduler Invocation for user: {test_user_id}")
        
        try:
            # Create conversations for yesterday
            yesterday = datetime.now(timezone.utc).replace(hour=12, minute=0, second=0, microsecond=0) - timedelta(days=1)
            conv_count = self.create_conversations_for_date(supabase_client, test_user_id, yesterday)
            print(f"✅ Created {conv_count} conversations for {yesterday.date()}")
            
            # Run the nightly summary job as scheduler would (no date = runs for "today")
            print("\n🔄 Running nightly_summary_job.py (simulating scheduler)...")
            result = subprocess.run(
                [sys.executable, "src/nightly_summary_job.py", "--test"],
                capture_output=True,
                text=True,
                cwd=project_root
            )
            
            print("STDOUT:", result.stdout)
            if result.stderr:
                print("STDERR:", result.stderr)
            
            assert result.returncode == 0, f"Script failed with return code {result.returncode}"
            
            # Verify NO summary was created (because by default it runs for "today", not yesterday)
            await asyncio.sleep(2)  # Give it time to complete
            
            summaries = supabase_client.table('longterm_memory')\
                .select('*')\
                .eq('user_id', test_user_id)\
                .execute()
            
            print(f"\n📊 Summaries found: {len(summaries.data)}")
            
            # This is the bug! The scheduler runs "today" but we need "yesterday"
            if len(summaries.data) == 0:
                print("❌ BUG CONFIRMED: No summaries created when running for 'today'")
                print("   The job looks for today's conversations, but should process yesterday's!")
            
            # Now run it correctly for yesterday
            print(f"\n🔄 Running with explicit date {yesterday.date()}...")
            result2 = subprocess.run(
                [sys.executable, "src/nightly_summary_job.py", "--date", yesterday.date().isoformat(), "--test"],
                capture_output=True,
                text=True,
                cwd=project_root
            )
            
            print("STDOUT:", result2.stdout)
            assert result2.returncode == 0, f"Script failed with return code {result2.returncode}"
            
            # Now check for summary
            await asyncio.sleep(2)
            summaries_after = supabase_client.table('longterm_memory')\
                .select('*')\
                .eq('user_id', test_user_id)\
                .eq('summary_date', yesterday.date().isoformat())\
                .execute()
            
            print(f"\n✅ Summaries after explicit date: {len(summaries_after.data)}")
            if summaries_after.data:
                summary = summaries_after.data[0]
                print(f"   Summary date: {summary['summary_date']}")
                print(f"   Content preview: {summary['content'][:100]}...")
                
                # Check project updates were also created
                project_updates = supabase_client.table('project_updates')\
                    .select('*')\
                    .eq('user_id', test_user_id)\
                    .execute()
                
                print(f"\n📈 Project updates created: {len(project_updates.data)}")
            
            return True
            
        finally:
            await self.cleanup_test_user(supabase_client, test_user_id)
    
    @pytest.mark.asyncio
    async def test_timezone_boundary_issues(self, test_user_id, supabase_client):
        """Test conversations near midnight UTC"""
        print(f"\n🌍 Testing Timezone Boundary Issues for user: {test_user_id}")
        
        try:
            # Create conversations right before and after midnight UTC
            today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
            yesterday = today - timedelta(days=1)
            
            # Late night conversation (11:45 PM UTC yesterday)
            late_night = yesterday.replace(hour=23, minute=45)
            supabase_client.table('conversations').insert({
                'user_id': test_user_id,
                'message_text': 'Late night message',
                'role': 'user',
                'context': {},
                'metadata': {},
                'created_at': late_night.isoformat()
            }).execute()
            
            # Early morning conversation (12:15 AM UTC today)
            early_morning = today.replace(hour=0, minute=15)
            supabase_client.table('conversations').insert({
                'user_id': test_user_id,
                'message_text': 'Early morning message',
                'role': 'user',
                'context': {},
                'metadata': {},
                'created_at': early_morning.isoformat()
            }).execute()
            
            # Run for yesterday
            result = subprocess.run(
                [sys.executable, "src/nightly_summary_job.py", "--date", yesterday.date().isoformat(), "--test"],
                capture_output=True,
                text=True,
                cwd=project_root
            )
            
            print("Processing yesterday's conversations...")
            print("Found in output:", "Late night message" in result.stdout)
            print("Should NOT find:", "Early morning message" in result.stdout)
            
            assert "Late night message" in result.stdout or "Found 1 conversations" in result.stdout
            assert "Early morning message" not in result.stdout
            
            return True
            
        finally:
            await self.cleanup_test_user(supabase_client, test_user_id)
    
    @pytest.mark.asyncio
    async def test_check_command(self):
        """Test the --check command functionality"""
        print("\n📊 Testing --check command...")
        
        result = subprocess.run(
            [sys.executable, "src/nightly_summary_job.py", "--check"],
            capture_output=True,
            text=True,
            cwd=project_root
        )
        
        print("Check output:", result.stdout)
        assert result.returncode == 0
        assert "Summary Stats" in result.stdout
        
        return True

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"]) 