#!/usr/bin/env python3
"""
Create missing database tables for WingmanMatch
Tables: dating_goals_progress, conversations (if needed)
"""

import os
import sys
from supabase import create_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_missing_tables():
    """Create the missing tables using Supabase admin client"""
    
    # Get Supabase credentials
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY') or os.getenv('SUPABASE_SERVICE_ROLE')
    
    if not supabase_url or not supabase_key:
        print("❌ Missing Supabase credentials")
        return False
    
    print("🔌 Connecting to Supabase...")
    supabase = create_client(supabase_url, supabase_key)
    
    # Test connection
    try:
        result = supabase.table('user_profiles').select('id').limit(1).execute()
        print("✅ Supabase connection successful")
    except Exception as e:
        print(f"❌ Supabase connection failed: {e}")
        return False
    
    # Check current table status
    print("\n📋 Checking missing tables...")
    
    missing_tables = []
    
    # Check dating_goals_progress
    try:
        supabase.table('dating_goals_progress').select('id').limit(1).execute()
        print("✅ dating_goals_progress table exists")
    except Exception:
        missing_tables.append('dating_goals_progress')
        print("❌ dating_goals_progress table missing")
    
    # Check conversations  
    try:
        supabase.table('conversations').select('id').limit(1).execute()
        print("✅ conversations table exists")
    except Exception:
        missing_tables.append('conversations')
        print("❌ conversations table missing")
    
    if not missing_tables:
        print("\n🎉 All tables exist! No action needed.")
        return True
    
    print(f"\n🔧 Need to create tables: {missing_tables}")
    
    # Create tables via SQL using the existing patterns
    success = True
    
    if 'dating_goals_progress' in missing_tables:
        print("\n📝 Creating dating_goals_progress table...")
        success &= create_dating_goals_progress_table(supabase)
    
    if 'conversations' in missing_tables:
        print("\n📝 Creating conversations table...")
        success &= create_conversations_table(supabase)
    
    return success

def create_dating_goals_progress_table(supabase):
    """Create the dating_goals_progress table"""
    try:
        # We need to use the SQL REST API endpoint directly
        # since Supabase client doesn't have direct SQL execution
        
        print("⚠️  Cannot create tables via Supabase Python client")
        print("📖 Manual creation required via Supabase dashboard or SQL:")
        
        sql = '''
-- Create dating_goals_progress table
CREATE TABLE IF NOT EXISTS "public"."dating_goals_progress" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "user_id" "uuid" NOT NULL,
    "flow_step" INTEGER DEFAULT 1,
    "current_data" "jsonb" DEFAULT '{}'::jsonb,
    "flow_state" "jsonb" DEFAULT '{}'::jsonb,
    "topic_progress" "jsonb" DEFAULT '{}'::jsonb,
    "completion_percentage" DECIMAL(5,2) DEFAULT 0.0,
    "is_completed" BOOLEAN DEFAULT FALSE,
    "created_at" TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    "updated_at" TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT "dating_goals_progress_pkey" PRIMARY KEY ("id"),
    CONSTRAINT "dating_goals_progress_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "public"."user_profiles"("id") ON DELETE CASCADE
);

-- Create indexes
CREATE INDEX IF NOT EXISTS "idx_dating_goals_progress_user_id" ON "public"."dating_goals_progress"("user_id");
CREATE INDEX IF NOT EXISTS "idx_dating_goals_progress_completion" ON "public"."dating_goals_progress"("is_completed");

-- Enable RLS
ALTER TABLE "public"."dating_goals_progress" ENABLE ROW LEVEL SECURITY;

-- RLS Policies
CREATE POLICY "Users can view their own dating goals progress" ON "public"."dating_goals_progress"
    FOR SELECT TO authenticated
    USING ((SELECT auth.uid()) = user_id);

CREATE POLICY "Users can update their own dating goals progress" ON "public"."dating_goals_progress"
    FOR UPDATE TO authenticated
    USING ((SELECT auth.uid()) = user_id)
    WITH CHECK ((SELECT auth.uid()) = user_id);

CREATE POLICY "Users can insert their own dating goals progress" ON "public"."dating_goals_progress"
    FOR INSERT TO authenticated
    WITH CHECK ((SELECT auth.uid()) = user_id);
'''
        
        print(sql)
        return False  # Indicate manual action needed
        
    except Exception as e:
        print(f"❌ Error creating dating_goals_progress: {e}")
        return False

def create_conversations_table(supabase):
    """Create the conversations table"""
    try:
        print("⚠️  Cannot create tables via Supabase Python client")
        print("📖 Manual creation required via Supabase dashboard or SQL:")
        
        sql = '''
-- Create conversations table (memory system)
CREATE TABLE IF NOT EXISTS "public"."conversations" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "user_id" "uuid" NOT NULL,
    "message_text" TEXT NOT NULL,
    "context" "jsonb" DEFAULT '{}'::jsonb,
    "agent_type" TEXT DEFAULT 'general',
    "thread_id" TEXT,
    "role" TEXT DEFAULT 'user',
    "created_at" TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT "conversations_pkey" PRIMARY KEY ("id"),
    CONSTRAINT "conversations_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "public"."user_profiles"("id") ON DELETE CASCADE
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS "idx_conversations_user_id" ON "public"."conversations"("user_id");
CREATE INDEX IF NOT EXISTS "idx_conversations_thread_id" ON "public"."conversations"("thread_id");
CREATE INDEX IF NOT EXISTS "idx_conversations_created_at" ON "public"."conversations"("created_at");

-- Enable RLS
ALTER TABLE "public"."conversations" ENABLE ROW LEVEL SECURITY;

-- RLS Policies
CREATE POLICY "Users can view their own conversations" ON "public"."conversations"
    FOR SELECT TO authenticated
    USING ((SELECT auth.uid()) = user_id);

CREATE POLICY "Users can insert their own conversations" ON "public"."conversations"
    FOR INSERT TO authenticated
    WITH CHECK ((SELECT auth.uid()) = user_id);
'''
        
        print(sql)
        return False  # Indicate manual action needed
        
    except Exception as e:
        print(f"❌ Error creating conversations: {e}")
        return False

if __name__ == "__main__":
    print("🚀 WingmanMatch Database Table Creator")
    print("=====================================")
    
    success = create_missing_tables()
    
    if success:
        print("\n🎉 All tables created successfully!")
        sys.exit(0)
    else:
        print("\n⚠️  Manual table creation required")
        print("   Please execute the SQL above in Supabase SQL Editor")
        sys.exit(1)