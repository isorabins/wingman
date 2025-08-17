# WingmanMatch Supabase Infrastructure Guide

## Overview

This guide provides comprehensive procedures for setting up, maintaining, and managing WingmanMatch Supabase infrastructure across staging and production environments.

**Critical Security Note:** This setup implements enterprise-grade security with RLS policies, proper JWT configuration, and storage security. Follow all procedures exactly as documented.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Staging Environment Setup](#staging-environment-setup)
3. [Production Environment Setup](#production-environment-setup)
4. [Security Configuration](#security-configuration)
5. [Storage Bucket Setup](#storage-bucket-setup)
6. [Migration Management](#migration-management)
7. [Backup and Recovery](#backup-and-recovery)
8. [Monitoring and Maintenance](#monitoring-and-maintenance)
9. [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Tools
```bash
# Install Supabase CLI
npm install -g supabase

# Verify installation
supabase --version  # Should be v1.0.0 or higher

# Install PostgreSQL client (for direct database access)
# macOS
brew install postgresql

# Ubuntu/Debian
sudo apt-get install postgresql-client
```

### Required Accounts and Access
- [ ] Supabase organization admin access
- [ ] Access to billing/subscription management
- [ ] GitHub repository admin access (for CI/CD integration)
- [ ] Domain management access (for CORS configuration)

## Staging Environment Setup

### Step 1: Create Staging Project

1. **Navigate to Supabase Dashboard**
   - Go to https://supabase.com/dashboard
   - Click "New Project" in your organization

2. **Project Configuration**
   ```
   Project Name: wingman-staging
   Database Password: Generate strong password (save to 1Password/secure vault)
   Region: us-west-1 (or closest to your users)
   Plan: Pro (required for PITR and advanced features)
   ```

3. **Save Critical Information**
   ```bash
   # Save these values securely - you'll need them for environment configuration
   SUPABASE_STAGING_URL=https://[project-ref].supabase.co
   SUPABASE_STAGING_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   SUPABASE_STAGING_SERVICE_ROLE=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   SUPABASE_STAGING_DB_PASSWORD=[your-generated-password]
   ```

### Step 2: Configure Staging Security

1. **Authentication Settings**
   - Navigate to Authentication > Settings
   - Configure the following:
   ```
   Site URL: https://wingman-staging.vercel.app
   Redirect URLs: 
     - https://wingman-staging.vercel.app/auth/callback
     - http://localhost:3000/auth/callback  (for local testing)
   ```

2. **JWT Settings**
   - Navigate to Settings > API
   - JWT expiry: 3600 (1 hour) for staging
   - Refresh token expiry: 604800 (1 week)

3. **Enable RLS Globally**
   ```sql
   -- Execute in SQL Editor
   ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public GRANT ALL ON TABLES TO authenticated;
   ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public GRANT ALL ON SEQUENCES TO authenticated;
   ```

### Step 3: Link CLI to Staging
```bash
# Navigate to project directory
cd /Applications/wingman

# Initialize Supabase (if not already done)
supabase init

# Link to staging project
supabase link --project-ref [staging-project-ref]

# Verify connection
supabase status
```

## Production Environment Setup

### Step 1: Create Production Project

⚠️ **CRITICAL:** Production setup requires additional security measures and backup configurations.

1. **Project Configuration**
   ```
   Project Name: wingman-production
   Database Password: Generate strong password (different from staging)
   Region: us-west-1 (same as staging for consistency)
   Plan: Pro with Add-ons:
     - Point-in-Time Recovery (PITR)
     - Custom Domain (if needed)
     - Additional Compute (if required)
   ```

2. **Enhanced Security Settings**
   ```
   Site URL: https://wingman.app (production domain)
   Redirect URLs:
     - https://wingman.app/auth/callback
     - https://www.wingman.app/auth/callback
   ```

### Step 2: Production Security Hardening

1. **Network Security**
   - Configure IP allowlisting if required
   - Enable SSL enforcement
   - Configure WAF rules (if available)

2. **Advanced Authentication**
   ```
   JWT Settings:
     - JWT expiry: 1800 (30 minutes) for production
     - Refresh token expiry: 86400 (24 hours)
     - Enable JWT verification
   ```

3. **Audit Configuration**
   - Enable audit logging
   - Configure retention policies
   - Set up log forwarding (if required)

## Security Configuration

### JWT Secret Management

```bash
# Generate new JWT secret for production (if needed)
openssl rand -base64 32

# Update JWT secret in Supabase Dashboard:
# Settings > API > JWT Settings > JWT Secret
```

### Row Level Security (RLS) Policies

The following RLS policies are applied via migrations:

```sql
-- Core table policies (already implemented in migrations)
-- user_profiles: Users can only access their own profile
-- user_locations: Users can only access their own location
-- wingman_matches: Users can only see matches they're part of
-- chat_messages: Users can only see messages from their matches
```

### CORS Configuration

Configure CORS for all environments:

```javascript
// Settings > API > CORS
{
  "allowedOrigins": [
    "http://localhost:3000",
    "http://localhost:3002", 
    "https://wingman-staging.vercel.app",
    "https://wingman.app",
    "https://www.wingman.app"
  ],
  "allowedMethods": ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
  "allowedHeaders": ["*"],
  "exposedHeaders": ["*"],
  "maxAge": 86400,
  "preflightContinue": false,
  "optionsSuccessStatus": 204
}
```

## Storage Bucket Setup

### Profile Photos Bucket Configuration

The storage bucket is automatically created via migration `004_storage_policies.sql`, but verify the following:

1. **Bucket Settings**
   ```
   Bucket Name: profile-photos
   Public Access: Disabled (private bucket)
   File Size Limit: 5MB (5,242,880 bytes)
   Allowed MIME Types: 
     - image/jpeg
     - image/png  
     - image/webp
     - image/gif
   ```

2. **Folder Structure**
   ```
   profile-photos/
   ├── [user-uuid-1]/
   │   ├── avatar.jpg
   │   └── profile-pic.png
   ├── [user-uuid-2]/
   │   └── avatar.webp
   └── ...
   ```

3. **Storage Policies Verification**
   ```sql
   -- Verify policies exist (run in SQL Editor)
   SELECT policyname, cmd, roles 
   FROM pg_policies 
   WHERE schemaname = 'storage' AND tablename = 'objects';
   ```

### CDN Configuration (Optional)

For production performance optimization:

1. Enable Supabase CDN for storage bucket
2. Configure custom domain for assets (if needed)
3. Set up cache headers for optimal performance

## Migration Management

### Applying Migrations

1. **To Staging Environment**
   ```bash
   # Link to staging
   supabase link --project-ref [staging-project-ref]
   
   # Apply all migrations
   supabase db push
   
   # Verify migration status
   supabase migration list
   ```

2. **To Production Environment**
   ```bash
   # CRITICAL: Always test in staging first
   
   # Link to production
   supabase link --project-ref [production-project-ref]
   
   # Apply migrations (preferably during maintenance window)
   supabase db push
   
   # Verify application
   supabase migration list
   ```

### Migration Rollback Procedures

```bash
# View migration history
supabase migration list

# Rollback to specific migration
supabase migration repair [migration-timestamp] --status reverted

# Re-apply if needed
supabase db push
```

### Creating New Migrations

```bash
# Generate new migration file
supabase migration new [migration_name]

# Edit the generated file in supabase/migrations/
# Test in staging before applying to production
```

## Backup and Recovery

### Point-in-Time Recovery (PITR) Setup

1. **Enable PITR** (Production only)
   - Navigate to Settings > Database
   - Enable "Point in time recovery"
   - Set retention to 7 days minimum

2. **Backup Validation Schedule**
   ```bash
   # Weekly backup validation (automate via CI/CD)
   # This script should be run every Sunday
   ./scripts/validate-backup-recovery.sh
   ```

### Manual Backup Procedures

```bash
# Create manual backup
supabase db dump --db-url [database-url] > backup-$(date +%Y%m%d).sql

# Restore from backup
supabase db reset --db-url [database-url] < backup-20241215.sql
```

### Disaster Recovery Runbook

**Recovery Time Objective (RTO):** 4 hours  
**Recovery Point Objective (RPO):** 1 hour

1. **Assess Impact and Scope**
   - Identify affected systems
   - Estimate downtime impact
   - Activate incident response team

2. **Immediate Actions**
   ```bash
   # Check service status
   curl -f https://[project-ref].supabase.co/rest/v1/ || echo "API DOWN"
   
   # Check database connectivity
   psql [connection-string] -c "SELECT 1;" || echo "DB DOWN"
   ```

3. **Recovery Procedures**
   - PITR recovery via Supabase Dashboard
   - Migration re-application if needed
   - Data validation and integrity checks
   - Service restoration verification

## Monitoring and Maintenance

### Health Checks

Implement the following automated health checks:

```bash
# API Health Check
curl -f https://[project-ref].supabase.co/rest/v1/health

# Database Connection Check  
psql [connection-string] -c "SELECT current_database(), current_user, version();"

# Storage Bucket Check
curl -f https://[project-ref].supabase.co/storage/v1/bucket/profile-photos
```

### Performance Monitoring

1. **Database Performance**
   - Monitor connection pool usage
   - Track slow query performance
   - Set up alerts for connection limits

2. **Storage Performance**
   - Monitor upload/download latencies
   - Track storage usage and costs
   - Set up alerts for unusual activity

### Maintenance Windows

**Staging:** Rolling updates (no downtime required)  
**Production:** Saturday 2-4 AM PST (low traffic window)

```bash
# Pre-maintenance checklist
□ Backup verification complete
□ Migration testing in staging successful  
□ Rollback procedures validated
□ Team notification sent
□ Monitoring alerts configured

# Post-maintenance verification
□ All services responding
□ Performance metrics within normal range
□ No error rate increases
□ User authentication working
□ File uploads functional
```

## Troubleshooting

### Common Issues and Solutions

#### 1. Migration Failures

**Symptom:** Migration fails with foreign key constraint errors

**Solution:**
```sql
-- Check for orphaned data
SELECT * FROM [child_table] 
WHERE [foreign_key] NOT IN (SELECT id FROM [parent_table]);

-- Clean up orphaned records or create missing parent records
-- Then retry migration
```

#### 2. RLS Policy Errors

**Symptom:** "new row violates row-level security policy"

**Solution:**
```sql
-- Check policy configuration
SELECT * FROM pg_policies WHERE tablename = '[table_name]';

-- Temporarily disable RLS for debugging (staging only!)
ALTER TABLE [table_name] DISABLE ROW LEVEL SECURITY;

-- Re-enable after fixing
ALTER TABLE [table_name] ENABLE ROW LEVEL SECURITY;
```

#### 3. Storage Upload Failures

**Symptom:** 413 Request Entity Too Large or 415 Unsupported Media Type

**Solution:**
```javascript
// Verify file size and type before upload
const maxSize = 5 * 1024 * 1024; // 5MB
const allowedTypes = ['image/jpeg', 'image/png', 'image/webp', 'image/gif'];

if (file.size > maxSize) {
  throw new Error('File too large. Maximum size is 5MB.');
}

if (!allowedTypes.includes(file.type)) {
  throw new Error('Invalid file type. Only images are allowed.');
}
```

#### 4. Authentication Issues

**Symptom:** JWT token validation failures

**Solution:**
```bash
# Verify JWT secret configuration
# Check Settings > API > JWT Settings in Supabase Dashboard

# Test JWT manually
curl -H "Authorization: Bearer [jwt-token]" \
     https://[project-ref].supabase.co/rest/v1/user_profiles
```

### Support and Escalation

**Level 1 - Development Team:**
- Environment configuration issues
- Migration troubleshooting
- Performance optimization

**Level 2 - Infrastructure Team:**
- Network connectivity issues
- Security policy configuration
- Backup/recovery operations

**Level 3 - Supabase Support:**
- Platform-level issues
- Service degradation
- Critical security incidents

**Emergency Contacts:**
```
Development Lead: [contact-info]
Infrastructure Lead: [contact-info]  
Supabase Support: support@supabase.io
Incident Response: [emergency-contact]
```

## Environment Variable Templates

See the following files for complete environment configuration:
- `.env.example` - Complete reference with all variables
- `.env.local.example` - Local development template
- `ops/supabase/env-staging.example` - Staging environment template
- `ops/supabase/env-production.example` - Production environment template

## Compliance and Security Auditing

### Security Checklist

- [ ] RLS enabled on all tables with user data
- [ ] Storage bucket properly configured with access controls
- [ ] JWT secrets properly secured and rotated
- [ ] CORS configured for approved domains only
- [ ] Audit logging enabled for production
- [ ] Backup and recovery procedures tested
- [ ] Security policies documented and reviewed

### Regular Security Reviews

Conduct monthly security reviews covering:
1. Access control effectiveness
2. RLS policy validation
3. Storage security verification
4. Authentication flow security
5. Backup and recovery testing

---

**Last Updated:** [Current Date]  
**Version:** 1.0  
**Next Review:** [Date + 1 month]

For questions or issues with this guide, please contact the development team or create an issue in the project repository.
