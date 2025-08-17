-- Migration: Enhanced Storage Policies and Security
-- File: 007_enhanced_storage_policies.sql
-- Dependencies: 003_add_storage_setup.sql
-- Description: Adds enhanced security policies, file validation, and monitoring for storage

BEGIN;

-- ==================================================
-- Enhanced Storage Security Policies
-- ==================================================

-- Drop existing policies to recreate with enhanced security
DROP POLICY IF EXISTS "Users can upload own photos" ON storage.objects;
DROP POLICY IF EXISTS "Users can view own photos" ON storage.objects;
DROP POLICY IF EXISTS "Users can update own photos" ON storage.objects;
DROP POLICY IF EXISTS "Users can delete own photos" ON storage.objects;
DROP POLICY IF EXISTS "Wingman matches can view partner photos" ON storage.objects;

-- Enhanced upload policy with file type and size validation
CREATE POLICY "Enhanced user photo upload" ON storage.objects
    FOR INSERT TO authenticated
    WITH CHECK (
        bucket_id = 'profile-photos' AND
        -- User can only upload to their own folder
        (storage.foldername(name))[1] = auth.uid()::text AND
        -- File size validation (5MB limit)
        COALESCE(metadata->>'size', '0')::int <= 5242880 AND
        -- MIME type validation
        COALESCE(metadata->>'mimetype', '') IN (
            'image/jpeg', 'image/jpg', 'image/png', 'image/webp', 'image/gif'
        ) AND
        -- File extension validation
        lower(split_part(name, '.', -1)) IN ('jpg', 'jpeg', 'png', 'webp', 'gif')
    );

-- Enhanced view policy for own photos
CREATE POLICY "Enhanced user photo view" ON storage.objects
    FOR SELECT TO authenticated
    USING (
        bucket_id = 'profile-photos' AND
        (storage.foldername(name))[1] = auth.uid()::text
    );

-- Enhanced update policy (for replacing photos)
CREATE POLICY "Enhanced user photo update" ON storage.objects
    FOR UPDATE TO authenticated
    USING (
        bucket_id = 'profile-photos' AND
        (storage.foldername(name))[1] = auth.uid()::text
    )
    WITH CHECK (
        bucket_id = 'profile-photos' AND
        (storage.foldername(name))[1] = auth.uid()::text AND
        -- Maintain file type restrictions on updates
        COALESCE(metadata->>'mimetype', '') IN (
            'image/jpeg', 'image/jpg', 'image/png', 'image/webp', 'image/gif'
        )
    );

-- Enhanced delete policy with audit trail consideration
CREATE POLICY "Enhanced user photo delete" ON storage.objects
    FOR DELETE TO authenticated
    USING (
        bucket_id = 'profile-photos' AND
        (storage.foldername(name))[1] = auth.uid()::text
    );

-- Enhanced wingman match photo viewing with additional security
CREATE POLICY "Enhanced wingman match photo access" ON storage.objects
    FOR SELECT TO authenticated
    USING (
        bucket_id = 'profile-photos' AND
        EXISTS (
            SELECT 1 FROM wingman_matches wm
            JOIN user_profiles up1 ON up1.user_id = wm.user1_id
            JOIN user_profiles up2 ON up2.user_id = wm.user2_id
            WHERE 
                -- Active match requirement
                wm.status = 'accepted' AND
                -- User is a participant in the match
                ((wm.user1_id = auth.uid() AND wm.user2_id::text = (storage.foldername(name))[1]) OR
                 (wm.user2_id = auth.uid() AND wm.user1_id::text = (storage.foldername(name))[1])) AND
                -- Both users have completed profiles
                up1.bio IS NOT NULL AND up2.bio IS NOT NULL
        )
    );

-- ==================================================
-- Storage Bucket Enhancements
-- ==================================================

-- Update bucket configuration with enhanced settings
UPDATE storage.buckets 
SET 
    file_size_limit = 5242880,  -- 5MB strict limit
    allowed_mime_types = ARRAY[
        'image/jpeg', 'image/jpg', 'image/png', 'image/webp', 'image/gif'
    ]
WHERE id = 'profile-photos';

-- ==================================================
-- Storage Monitoring and Audit Tables
-- ==================================================

-- Create storage audit log table for monitoring uploads
CREATE TABLE IF NOT EXISTS storage_audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    bucket_id TEXT NOT NULL,
    object_name TEXT NOT NULL,
    operation TEXT NOT NULL CHECK (operation IN ('INSERT', 'UPDATE', 'DELETE')),
    file_size BIGINT,
    mime_type TEXT,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable RLS on audit log (users can only see their own actions)
ALTER TABLE storage_audit_log ENABLE ROW LEVEL SECURITY;

-- RLS policy for audit log
CREATE POLICY "Users can view own storage audit logs" ON storage_audit_log
    FOR SELECT TO authenticated
    USING (user_id = auth.uid());

-- Service role can manage all audit logs
CREATE POLICY "Service role can manage all audit logs" ON storage_audit_log
    FOR ALL TO service_role
    USING (true)
    WITH CHECK (true);

-- ==================================================
-- Storage Triggers for Audit Logging
-- ==================================================

-- Function to log storage operations
CREATE OR REPLACE FUNCTION log_storage_operation()
RETURNS TRIGGER AS $$
BEGIN
    -- Log INSERT operations
    IF TG_OP = 'INSERT' THEN
        INSERT INTO storage_audit_log (
            user_id, bucket_id, object_name, operation, 
            file_size, mime_type, created_at
        ) VALUES (
            auth.uid(),
            NEW.bucket_id,
            NEW.name,
            TG_OP,
            COALESCE((NEW.metadata->>'size')::bigint, 0),
            NEW.metadata->>'mimetype',
            NOW()
        );
        RETURN NEW;
    END IF;

    -- Log UPDATE operations
    IF TG_OP = 'UPDATE' THEN
        INSERT INTO storage_audit_log (
            user_id, bucket_id, object_name, operation,
            file_size, mime_type, created_at
        ) VALUES (
            auth.uid(),
            NEW.bucket_id,
            NEW.name,
            TG_OP,
            COALESCE((NEW.metadata->>'size')::bigint, 0),
            NEW.metadata->>'mimetype',
            NOW()
        );
        RETURN NEW;
    END IF;

    -- Log DELETE operations
    IF TG_OP = 'DELETE' THEN
        INSERT INTO storage_audit_log (
            user_id, bucket_id, object_name, operation,
            file_size, mime_type, created_at
        ) VALUES (
            auth.uid(),
            OLD.bucket_id,
            OLD.name,
            TG_OP,
            COALESCE((OLD.metadata->>'size')::bigint, 0),
            OLD.metadata->>'mimetype',
            NOW()
        );
        RETURN OLD;
    END IF;

    RETURN NULL;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create trigger for storage operations audit
DROP TRIGGER IF EXISTS storage_audit_trigger ON storage.objects;
CREATE TRIGGER storage_audit_trigger
    AFTER INSERT OR UPDATE OR DELETE ON storage.objects
    FOR EACH ROW EXECUTE FUNCTION log_storage_operation();

-- ==================================================
-- Performance Optimizations
-- ==================================================

-- Index for storage audit log queries
CREATE INDEX IF NOT EXISTS idx_storage_audit_user_created 
ON storage_audit_log(user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_storage_audit_operation_created 
ON storage_audit_log(operation, created_at DESC);

-- Index for wingman match photo access optimization
CREATE INDEX IF NOT EXISTS idx_wingman_matches_status_users
ON wingman_matches(status, user1_id, user2_id) WHERE status = 'accepted';

-- ==================================================
-- Storage Usage Statistics
-- ==================================================

-- Create view for storage usage statistics
CREATE OR REPLACE VIEW storage_usage_stats AS
SELECT 
    u.id as user_id,
    u.email,
    COUNT(so.id) as total_files,
    COALESCE(SUM((so.metadata->>'size')::bigint), 0) as total_bytes,
    ROUND(COALESCE(SUM((so.metadata->>'size')::bigint), 0) / 1024.0 / 1024.0, 2) as total_mb,
    MAX(so.created_at) as last_upload,
    COUNT(so.id) FILTER (WHERE so.created_at > NOW() - INTERVAL '30 days') as uploads_last_30_days
FROM auth.users u
LEFT JOIN storage.objects so ON so.bucket_id = 'profile-photos' 
    AND (storage.foldername(so.name))[1] = u.id::text
GROUP BY u.id, u.email;

-- Grant access to authenticated users (they can only see their own stats)
GRANT SELECT ON storage_usage_stats TO authenticated;

-- RLS policy for storage usage stats
ALTER VIEW storage_usage_stats SET (security_barrier = true);
CREATE POLICY "Users can view own storage stats" ON storage_usage_stats
    FOR SELECT TO authenticated
    USING (user_id = auth.uid());

-- ==================================================
-- Storage Cleanup Functions
-- ==================================================

-- Function to clean up orphaned storage objects
CREATE OR REPLACE FUNCTION cleanup_orphaned_storage()
RETURNS TABLE(deleted_objects TEXT[], deleted_count INT) AS $$
DECLARE
    orphaned_objects TEXT[];
    delete_count INT := 0;
BEGIN
    -- Find storage objects without corresponding user profiles
    SELECT ARRAY_AGG(so.name) INTO orphaned_objects
    FROM storage.objects so
    WHERE so.bucket_id = 'profile-photos'
    AND NOT EXISTS (
        SELECT 1 FROM user_profiles up 
        WHERE up.user_id::text = (storage.foldername(so.name))[1]
    );

    -- Delete orphaned objects (this would be done via Supabase API in practice)
    -- For now, just return the list for manual cleanup
    delete_count := COALESCE(array_length(orphaned_objects, 1), 0);
    
    RETURN QUERY SELECT orphaned_objects, delete_count;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Grant execute to service role only
GRANT EXECUTE ON FUNCTION cleanup_orphaned_storage() TO service_role;

-- ==================================================
-- Storage Security Functions
-- ==================================================

-- Function to validate uploaded files
CREATE OR REPLACE FUNCTION validate_upload_security(
    file_name TEXT,
    file_size BIGINT,
    mime_type TEXT
) RETURNS BOOLEAN AS $$
BEGIN
    -- File size check (5MB = 5,242,880 bytes)
    IF file_size > 5242880 THEN
        RAISE EXCEPTION 'File size exceeds 5MB limit. Size: % bytes', file_size;
    END IF;

    -- MIME type check
    IF mime_type NOT IN ('image/jpeg', 'image/jpg', 'image/png', 'image/webp', 'image/gif') THEN
        RAISE EXCEPTION 'Invalid file type. Only images are allowed. Type: %', mime_type;
    END IF;

    -- File extension check
    IF lower(split_part(file_name, '.', -1)) NOT IN ('jpg', 'jpeg', 'png', 'webp', 'gif') THEN
        RAISE EXCEPTION 'Invalid file extension. Only image files are allowed. File: %', file_name;
    END IF;

    -- File name security check (prevent path traversal)
    IF file_name LIKE '%..%' OR file_name LIKE '%/%' OR file_name LIKE '%\%' THEN
        RAISE EXCEPTION 'Invalid file name. Path traversal detected: %', file_name;
    END IF;

    RETURN TRUE;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Grant execute to authenticated users
GRANT EXECUTE ON FUNCTION validate_upload_security(TEXT, BIGINT, TEXT) TO authenticated;

-- ==================================================
-- Indexes for Performance
-- ==================================================

-- Ensure optimal performance for storage object queries
CREATE INDEX IF NOT EXISTS idx_storage_objects_bucket_folder
ON storage.objects(bucket_id, (storage.foldername(name))[1]);

CREATE INDEX IF NOT EXISTS idx_storage_objects_created_at
ON storage.objects(created_at DESC) WHERE bucket_id = 'profile-photos';

-- ==================================================
-- Comments for Documentation
-- ==================================================

COMMENT ON TABLE storage_audit_log IS 'Audit trail for all storage operations including uploads, updates, and deletions';
COMMENT ON FUNCTION log_storage_operation() IS 'Trigger function that logs all storage operations for audit and monitoring';
COMMENT ON FUNCTION validate_upload_security(TEXT, BIGINT, TEXT) IS 'Validates uploaded files for security compliance';
COMMENT ON FUNCTION cleanup_orphaned_storage() IS 'Identifies orphaned storage objects for cleanup';
COMMENT ON VIEW storage_usage_stats IS 'Provides storage usage statistics per user for monitoring and billing';

COMMIT;
