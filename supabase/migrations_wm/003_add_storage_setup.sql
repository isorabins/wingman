-- Migration: Add storage bucket and privacy mode for profile setup
-- File: 003_add_storage_setup.sql
-- Dependencies: 001_add_wingman_tables.sql
-- Description: Creates profile-photos storage bucket with RLS policies
--              Adds privacy_mode to user_locations table for location privacy controls

BEGIN;

-- Add privacy_mode column to user_locations table
ALTER TABLE "public"."user_locations" 
ADD COLUMN IF NOT EXISTS "privacy_mode" VARCHAR(20) DEFAULT 'precise' 
CHECK ("privacy_mode" IN ('precise', 'city_only'));

-- Create storage bucket for profile photos
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
    'profile-photos',
    'profile-photos',
    false,  -- Private bucket, requires auth
    5242880,  -- 5MB limit (5 * 1024 * 1024)
    ARRAY['image/jpeg', 'image/png', 'image/webp', 'image/gif']
) ON CONFLICT (id) DO NOTHING;

-- Storage RLS policies for profile photos

-- Users can upload photos to their own folder
CREATE POLICY "Users can upload own photos" ON storage.objects
    FOR INSERT TO authenticated
    WITH CHECK (
        bucket_id = 'profile-photos' AND
        (storage.foldername(name))[1] = auth.uid()::text
    );

-- Users can view their own photos
CREATE POLICY "Users can view own photos" ON storage.objects
    FOR SELECT TO authenticated
    USING (
        bucket_id = 'profile-photos' AND
        (storage.foldername(name))[1] = auth.uid()::text
    );

-- Users can update their own photos (for replacing profile pictures)
CREATE POLICY "Users can update own photos" ON storage.objects
    FOR UPDATE TO authenticated
    USING (
        bucket_id = 'profile-photos' AND
        (storage.foldername(name))[1] = auth.uid()::text
    )
    WITH CHECK (
        bucket_id = 'profile-photos' AND
        (storage.foldername(name))[1] = auth.uid()::text
    );

-- Users can delete their own photos
CREATE POLICY "Users can delete own photos" ON storage.objects
    FOR DELETE TO authenticated
    USING (
        bucket_id = 'profile-photos' AND
        (storage.foldername(name))[1] = auth.uid()::text
    );

-- Wingman matches can view each other's photos (for buddy matching context)
CREATE POLICY "Wingman matches can view partner photos" ON storage.objects
    FOR SELECT TO authenticated
    USING (
        bucket_id = 'profile-photos' AND
        EXISTS (
            SELECT 1 FROM wingman_matches 
            WHERE 
                ((user1_id = auth.uid() AND user2_id::text = (storage.foldername(name))[1]) OR
                 (user2_id = auth.uid() AND user1_id::text = (storage.foldername(name))[1])) AND
                status = 'active'
        )
    );

-- Create index for privacy_mode queries
CREATE INDEX IF NOT EXISTS "idx_user_locations_privacy_mode" ON "public"."user_locations"("privacy_mode");

-- Update user_locations RLS policies to handle upsert operations
DROP POLICY IF EXISTS "Users can insert their own location" ON "public"."user_locations";
DROP POLICY IF EXISTS "Users can update their own location" ON "public"."user_locations";

-- Combined upsert policy for user_locations
CREATE POLICY "Users can upsert their own location" ON "public"."user_locations"
    FOR ALL TO authenticated
    USING ((SELECT auth.uid()) = user_id)
    WITH CHECK ((SELECT auth.uid()) = user_id);

COMMIT;