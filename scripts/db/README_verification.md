# WingmanMatch Database Schema Verification

## Overview

The `verify_wm_schema.sql` script provides comprehensive verification of all WingmanMatch database migrations. It ensures that all tables, indexes, constraints, functions, and security policies are properly configured.

## Usage

### Prerequisites
- PostgreSQL database with WingmanMatch migrations applied
- Database connection with appropriate permissions
- Both migration files applied:
  - `001_add_wingman_tables.sql`
  - `002_rename_creator_contexts.sql`

### Running the Verification

```bash
# Connect to your database and run the verification script
psql -d your_database_name -f scripts/db/verify_wm_schema.sql

# Or with connection parameters
psql -h localhost -U username -d database_name -f scripts/db/verify_wm_schema.sql

# For Supabase (replace with your project details)
psql "postgresql://postgres:[password]@db.[project-ref].supabase.co:5432/postgres" -f scripts/db/verify_wm_schema.sql
```

## What Gets Verified

### 1. Table Existence ✅
- **New Tables**: `user_locations`, `wingman_matches`, `approach_challenges`, `wingman_sessions`
- **Renamed Tables**: `user_profiles` (from `creator_profiles`), `dating_goals` (from `project_overview`), `confidence_test_results` (from `creativity_test_results`)

### 2. Column Structure ✅
- Verifies all required columns exist in each table
- Checks critical data types (UUID, DECIMAL, TIMESTAMP, etc.)
- Validates column naming consistency

### 3. Performance Indexes ✅
- Geographic indexes for location-based queries
- User relationship indexes for matching
- Status and timestamp indexes for filtering
- All 11 expected performance indexes

### 4. Table Constraints ✅
- **Primary Keys**: All tables have proper primary key constraints
- **Foreign Keys**: Proper relationships between tables maintained
- **Check Constraints**: Data validation rules enforced
- **Unique Constraints**: Prevents duplicate matches and conflicts

### 5. haversine_miles Function ✅
- **Existence Check**: Function is properly created
- **Functionality Test**: Calculates distance between known coordinates
- **Edge Case Test**: Returns 0 for identical coordinates
- **Accuracy Validation**: Returns reasonable distances (~0.1 miles for close points)

### 6. Row Level Security (RLS) ✅
- **RLS Enabled**: All tables have RLS activated
- **Security Policies**: User-specific access policies in place
- **Permission Verification**: Proper read/write access controls

### 7. Sample Data Verification ✅
- **Challenge Data**: Checks if `approach_challenges` has been seeded
- **Data Distribution**: Validates challenges across all difficulty levels
- **Recommendation**: Suggests running `seed_challenges.sql` if needed

### 8. Functional Testing ✅
- **Query Validation**: All tables are queryable without errors
- **Join Compatibility**: Foreign key relationships work properly
- **Basic Operations**: CRUD operations are possible

## Expected Output

### Success Example
```
🎉 SCHEMA VERIFICATION SUCCESSFUL
Database is ready for WingmanMatch application!

VERIFICATION RESULTS:
====================

New WingmanMatch Tables: 4/4 (✅ PASS)
Renamed Tables: 2/2 (✅ PASS)
Performance Indexes: 11/11 (✅ PASS)
Table Constraints: 12+ (✅ PASS)
Haversine Function: ✅ PASS
Row Level Security: 4/4 (✅ PASS)
```

### Failure Example
```
⚠️  SCHEMA VERIFICATION ISSUES DETECTED
Please review the failed checks above and re-run migrations as needed.

VERIFICATION RESULTS:
====================

New WingmanMatch Tables: 3/4 (❌ FAIL)
❌ MISSING TABLE: "wingman_sessions"
```

## Troubleshooting

### Common Issues

1. **Missing Tables**
   - **Problem**: Migration files not applied
   - **Solution**: Run migration files in order: `001_add_wingman_tables.sql`, then `002_rename_creator_contexts.sql`

2. **Missing Indexes**
   - **Problem**: Index creation failed during migration
   - **Solution**: Re-run the `001_add_wingman_tables.sql` migration

3. **Function Not Found**
   - **Problem**: `haversine_miles` function not created
   - **Solution**: Check migration logs, ensure extensions are enabled

4. **RLS Policies Missing**
   - **Problem**: Row Level Security policies not applied
   - **Solution**: Re-run migration with proper database permissions

5. **Foreign Key Failures**
   - **Problem**: Referenced tables don't exist or were not renamed properly
   - **Solution**: Ensure all previous migrations are applied, especially table renames

### Re-running Verification

The script is safe to run multiple times. After fixing any issues, simply run the verification script again to confirm all problems are resolved.

## Database Requirements

- PostgreSQL 12+ (for UUID extension support)
- `uuid-ossp` extension enabled
- Proper user permissions for:
  - Table creation and modification
  - Index creation
  - Function creation
  - RLS policy management

## Integration Testing

After successful verification, you can test the schema with sample data:

```sql
-- Run the challenge seeding script
\i scripts/db/seed_challenges.sql

-- Re-run verification to confirm data loading
\i scripts/db/verify_wm_schema.sql
```

## Next Steps

Once verification passes:

1. **Seed Challenge Data**: Run `seed_challenges.sql` for initial approach challenges
2. **Test Application Integration**: Verify your application can connect and perform operations
3. **Performance Testing**: Test query performance with sample data
4. **Security Testing**: Verify RLS policies work as expected with real user sessions

## Maintenance

Run this verification script:
- After any database migrations
- Before deploying to production
- When troubleshooting database issues
- As part of your CI/CD pipeline for database changes