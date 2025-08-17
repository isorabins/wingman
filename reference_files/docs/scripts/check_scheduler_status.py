#!/usr/bin/env python3
"""
Check Nightly Summary Job Status

This script checks:
1. Recent longterm_memory entries to see if summaries are being created
2. Conversations that should have been summarized
3. Users who have conversations but no summaries
"""

import os
import sys
from datetime import datetime, timezone, timedelta
from supabase import create_client

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.config import Config

def check_summary_status():
    """Check the status of nightly summaries"""
    
    # Create Supabase client
    supabase_client = create_client(Config.SUPABASE_URL, Config.SUPABASE_SERVICE_KEY)
    
    print("🔍 Checking Nightly Summary Status\n")
    
    # 1. Check recent longterm_memory entries
    print("📊 Recent Longterm Memory Entries (Last 7 Days):")
    seven_days_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    
    recent_summaries = supabase_client.table('longterm_memory')\
        .select('user_id, summary_date, created_at')\
        .gte('created_at', seven_days_ago)\
        .order('created_at', desc=True)\
        .limit(10)\
        .execute()
    
    if recent_summaries.data:
        print(f"Found {len(recent_summaries.data)} summaries:")
        for summary in recent_summaries.data:
            print(f"  - User: {summary['user_id'][:8]}... | Date: {summary['summary_date']} | Created: {summary['created_at']}")
    else:
        print("  ❌ No summaries found in the last 7 days!")
    
    print("\n" + "="*60 + "\n")
    
    # 2. Check conversations from yesterday that should have been summarized
    yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).date()
    today = datetime.now(timezone.utc).date()
    
    print(f"📅 Checking Conversations from {yesterday} that need summaries:")
    
    # Get all conversations from yesterday
    yesterday_convos = supabase_client.table('conversations')\
        .select('user_id', count='exact')\
        .gte('created_at', f'{yesterday.isoformat()}T00:00:00Z')\
        .lt('created_at', f'{today.isoformat()}T00:00:00Z')\
        .execute()
    
    print(f"Total conversations yesterday: {yesterday_convos.count}")
    
    # Get unique users from yesterday's conversations
    if yesterday_convos.data:
        user_ids = list(set([conv['user_id'] for conv in yesterday_convos.data]))
        print(f"Unique users with conversations: {len(user_ids)}")
        
        # Check how many have summaries
        summaries_for_yesterday = supabase_client.table('longterm_memory')\
            .select('user_id')\
            .eq('summary_date', yesterday.isoformat())\
            .execute()
        
        users_with_summaries = [s['user_id'] for s in summaries_for_yesterday.data] if summaries_for_yesterday.data else []
        users_without_summaries = [uid for uid in user_ids if uid not in users_with_summaries]
        
        print(f"Users WITH summaries: {len(users_with_summaries)}")
        print(f"Users WITHOUT summaries: {len(users_without_summaries)} ⚠️")
        
        if users_without_summaries and len(users_without_summaries) <= 5:
            print("\nUsers missing summaries:")
            for uid in users_without_summaries[:5]:
                print(f"  - {uid}")
    
    print("\n" + "="*60 + "\n")
    
    # 3. Check overall summary generation patterns
    print("📈 Summary Generation Pattern (Last 30 Days):")
    thirty_days_ago = (datetime.now(timezone.utc) - timedelta(days=30)).date()
    
    all_summaries = supabase_client.table('longterm_memory')\
        .select('summary_date')\
        .gte('summary_date', thirty_days_ago.isoformat())\
        .order('summary_date', desc=True)\
        .execute()
    
    if all_summaries.data:
        dates_with_summaries = list(set([s['summary_date'] for s in all_summaries.data]))
        dates_with_summaries.sort(reverse=True)
        
        print(f"Days with summaries: {len(dates_with_summaries)}/30")
        print("Recent dates with summaries:")
        for date in dates_with_summaries[:5]:
            count = len([s for s in all_summaries.data if s['summary_date'] == date])
            print(f"  - {date}: {count} summaries")
    else:
        print("  ❌ No summaries found in the last 30 days!")
    
    print("\n" + "="*60 + "\n")
    
    # 4. Manual run command
    print("🛠️ To manually run nightly summaries:")
    print("  python src/nightly_summary_job.py --test")
    print("\nTo run for a specific date:")
    print("  python src/nightly_summary_job.py --date 2024-01-20 --test")
    print("\nTo check summary stats:")
    print("  python src/nightly_summary_job.py --check")

if __name__ == "__main__":
    check_summary_status() 