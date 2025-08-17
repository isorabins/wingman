-- Migration: Create chat_messages table for buddy chat functionality
-- File: 004_add_chat_messages.sql
-- Dependencies: 001_add_wingman_tables.sql (for wingman_matches and user_profiles)
-- Description: Creates chat_messages table with proper indexing and RLS policies

BEGIN;

-- Create chat_messages table
CREATE TABLE IF NOT EXISTS "public"."chat_messages" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "match_id" "uuid" NOT NULL,
    "sender_id" "uuid" NOT NULL,
    "message_text" "text" NOT NULL,
    "created_at" TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT "chat_messages_pkey" PRIMARY KEY ("id"),
    CONSTRAINT "chat_messages_match_id_fkey" FOREIGN KEY ("match_id") REFERENCES "public"."wingman_matches"("id") ON DELETE CASCADE,
    CONSTRAINT "chat_messages_sender_id_fkey" FOREIGN KEY ("sender_id") REFERENCES "public"."user_profiles"("id") ON DELETE CASCADE,
    CONSTRAINT "chat_messages_text_length_check" CHECK (length("message_text") BETWEEN 2 AND 2000)
);

-- Create table for tracking last read timestamps
CREATE TABLE IF NOT EXISTS "public"."chat_read_timestamps" (
    "match_id" "uuid" NOT NULL,
    "user_id" "uuid" NOT NULL,
    "last_read_at" TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    "updated_at" TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT "chat_read_timestamps_pkey" PRIMARY KEY ("match_id", "user_id"),
    CONSTRAINT "chat_read_timestamps_match_id_fkey" FOREIGN KEY ("match_id") REFERENCES "public"."wingman_matches"("id") ON DELETE CASCADE,
    CONSTRAINT "chat_read_timestamps_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "public"."user_profiles"("id") ON DELETE CASCADE
);

-- Create indexes for performance optimization
CREATE INDEX IF NOT EXISTS "idx_chat_messages_match_id_created_at" ON "public"."chat_messages"("match_id", "created_at");
CREATE INDEX IF NOT EXISTS "idx_chat_messages_sender_id" ON "public"."chat_messages"("sender_id");
CREATE INDEX IF NOT EXISTS "idx_chat_read_timestamps_user_id" ON "public"."chat_read_timestamps"("user_id");

-- Enable Row Level Security
ALTER TABLE "public"."chat_messages" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "public"."chat_read_timestamps" ENABLE ROW LEVEL SECURITY;

-- RLS Policies for chat_messages
-- Users can view messages for matches they participate in
CREATE POLICY "Users can view messages for their matches" ON "public"."chat_messages"
    FOR SELECT TO authenticated
    USING (
        (SELECT auth.uid()) IN (
            SELECT user1_id FROM wingman_matches WHERE id = match_id
            UNION
            SELECT user2_id FROM wingman_matches WHERE id = match_id
        )
    );

-- Users can send messages to matches they participate in
CREATE POLICY "Users can send messages to their matches" ON "public"."chat_messages"
    FOR INSERT TO authenticated
    WITH CHECK (
        (SELECT auth.uid()) = sender_id AND
        (SELECT auth.uid()) IN (
            SELECT user1_id FROM wingman_matches WHERE id = match_id
            UNION
            SELECT user2_id FROM wingman_matches WHERE id = match_id
        )
    );

-- RLS Policies for chat_read_timestamps
-- Users can view their own read timestamps
CREATE POLICY "Users can view their own read timestamps" ON "public"."chat_read_timestamps"
    FOR SELECT TO authenticated
    USING ((SELECT auth.uid()) = user_id);

-- Users can insert/update their own read timestamps
CREATE POLICY "Users can update their own read timestamps" ON "public"."chat_read_timestamps"
    FOR INSERT TO authenticated
    WITH CHECK ((SELECT auth.uid()) = user_id);

CREATE POLICY "Users can modify their own read timestamps" ON "public"."chat_read_timestamps"
    FOR UPDATE TO authenticated
    USING ((SELECT auth.uid()) = user_id)
    WITH CHECK ((SELECT auth.uid()) = user_id);

COMMIT;