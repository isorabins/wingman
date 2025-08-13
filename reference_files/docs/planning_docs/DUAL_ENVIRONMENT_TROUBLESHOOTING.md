# 🚨 Dual Environment Setup - Troubleshooting Log

## 🎯 Original Problem
**Date**: January 20, 2025  
**Issue**: Dev frontend (dev.fridaysatfour.co) cannot communicate properly with backend, experiencing CORS errors and authentication failures.

## 🏗️ Environment Architecture Goals
```
Production:  fridaysatfour.co → fridays-at-four-c9c6b7a513be.herokuapp.com
Development: dev.fridaysatfour.co → fridays-at-four-dev-434b1a68908b.herokuapp.com
Database:    Shared production Supabase (ipvxxsthulsysbkwbitu.supabase.co)
```

## 🔍 Issues Identified

### 1. CORS Configuration Missing
**Problem**: dev.fridaysatfour.co was not in ALLOWED_ORIGINS  
**Status**: ✅ FIXED  
**Solution**: Added dev.fridaysatfour.co to CORS configuration in both environments

### 2. Database Mismatch
**Problem**: Frontend and dev backend using different Supabase databases  
**Frontend**: ipvxxsthulsysbkwbitu.supabase.co (production)  
**Dev Backend**: mxlmadjuauugvlukgrla.supabase.co (dev-specific)  
**Status**: 🔄 IN PROGRESS  
**Solution**: Unifying both to use production database

### 3. Authentication Credentials Mismatch
**Problem**: "Invalid login credentials" despite correct user auth  
**Root Cause**: Dev backend pointing to different database than frontend auth  
**Status**: 🔄 IN PROGRESS

## 🛠️ Solutions Attempted

### ✅ Completed Actions

1. **CORS Fix on Production**
   ```bash
   # Added dev.fridaysatfour.co to ALLOWED_ORIGINS
   git push heroku main
   ```

2. **Created Development Heroku App**
   ```bash
   heroku create fridays-at-four-dev
   git remote add dev https://git.heroku.com/fridays-at-four-dev.git
   ```

3. **Updated Dev Backend Database URL**
   ```bash
   heroku config:set SUPABASE_URL=https://ipvxxsthulsysbkwbitu.supabase.co --app fridays-at-four-dev
   ```

4. **Verified Dev Backend Health**
   ```bash
   curl https://fridays-at-four-dev-434b1a68908b.herokuapp.com/health
   # Response: {"status":"healthy","environment":"development"}
   ```

### 🔄 In Progress Actions

1. **Synchronizing Supabase Credentials**
   ```bash
   # Started updating SUPABASE_ANON_KEY
   heroku config:set SUPABASE_ANON_KEY=[PRODUCTION_KEY] --app fridays-at-four-dev
   ```

2. **Complete Environment Variable Sync**
   - Need to copy all Supabase-related env vars from production to dev
   - Verify SUPABASE_SERVICE_ROLE_KEY alignment
   - Ensure JWT_SECRET matches if used

## 🎉 **ISSUE RESOLVED!** 

### Root Cause Identified
The problem was **NOT** in Vercel environment variables or backend configuration. The issue was in the frontend JavaScript code itself:

**Frontend chat page** (`/chat/page.tsx`) had **hardcoded API endpoints**:
```javascript
// ❌ PROBLEM CODE
const API_BASE = process.env.NODE_ENV === 'production' 
  ? 'https://fridays-at-four-c9c6b7a513be.herokuapp.com'  // Always production!
  : 'http://localhost:8000';
```

This meant the dev frontend was **completely bypassing** Vercel environment variables and hitting production backend directly.

### Solution Applied
```javascript
// ✅ FIXED CODE  
const API_BASE = process.env.NEXT_PUBLIC_BACKEND_API_URL || 'http://localhost:8000';
```

Now environment variables properly control which backend each frontend environment hits.

### Environment Flow Confirmed Working
- **Dev**: `dev.fridaysatfour.co` → `fridays-at-four-dev-434b1a68908b.herokuapp.com` ✅
- **Prod**: `app.fridaysatfour.co` → `fridays-at-four-c9c6b7a513be.herokuapp.com` ✅

**Status**: ✅ **RESOLVED** - Dual environment setup working perfectly  
**Root Cause**: Hardcoded frontend URLs bypassing environment variables  
**Solution**: Use `process.env.NEXT_PUBLIC_BACKEND_API_URL` in frontend code  
**Updated**: January 20, 2025

## 🚨 Current Status: STILL NOT WORKING

### Symptoms Observed
- Dev frontend can reach dev backend (health check works)
- CORS headers properly configured
- Authentication still failing with "Invalid login credentials"
- User auth tokens potentially not valid across database contexts

### Potential Root Causes

1. **Incomplete Environment Variable Sync**
   - Missing or mismatched SUPABASE_SERVICE_ROLE_KEY
   - JWT secret misalignment
   - Other Supabase configuration variables

2. **Frontend Configuration Issue**
   - Dev frontend might not be pointing to dev backend
   - Frontend still using production backend URL
   - Authentication context not properly switching

3. **Supabase Auth Configuration**
   - Auth tokens issued by production Supabase might not work with dev backend
   - Need to verify auth flow end-to-end

4. **Caching Issues**
   - Browser caching old CORS responses
   - Frontend build cache with old API endpoints
   - Heroku app cache with old configurations

## 🔍 Debugging Steps Needed

### 1. Verify Frontend Configuration
```bash
# Check what API endpoint dev frontend is actually hitting
# Look at network tab in browser dev tools
# Verify environment variables in Vercel dev deployment
```

### 2. Complete Environment Variable Audit
```bash
# Production config
heroku config --app fridays-at-four-c9c6b7a513be

# Dev config  
heroku config --app fridays-at-four-dev

# Compare and sync all Supabase-related vars
```

### 3. Test Authentication Flow
```bash
# Test direct API calls to dev backend
curl -X POST https://fridays-at-four-dev-434b1a68908b.herokuapp.com/start_conversation \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer [TOKEN]" \
  -d '{"user_id":"test","message":"hello"}'
```

### 4. Check Frontend Build/Deploy
- Verify dev.fridaysatfour.co is deploying from correct branch
- Check if dev frontend has correct API endpoint configured
- Ensure no environment variable mismatches in Vercel

## 🎯 Next Steps (Priority Order)

1. **🔥 HIGH**: Complete Supabase environment variable sync
2. **🔥 HIGH**: Verify frontend is actually hitting dev backend
3. **🔥 HIGH**: Test authentication flow end-to-end
4. **🟡 MEDIUM**: Check for caching issues
5. **🟡 MEDIUM**: Verify Vercel deployment configuration
6. **🟢 LOW**: Consider alternative database isolation approach

## 📊 Environment Variables Checklist

### Production (Source of Truth)
- [x] SUPABASE_URL
- [x] SUPABASE_ANON_KEY  
- [ ] SUPABASE_SERVICE_ROLE_KEY
- [ ] Any other auth-related variables

### Dev (Target for Sync)
- [x] SUPABASE_URL (updated)
- [x] SUPABASE_ANON_KEY (in progress)
- [ ] SUPABASE_SERVICE_ROLE_KEY (pending)
- [ ] Verify all other variables match

## 🆘 Fallback Options

If unified database approach continues to fail:

1. **Separate Databases**: Accept separate dev/prod databases, sync auth configuration
2. **Local Development**: Use local backend for development instead of Heroku dev
3. **Production Only**: Skip dev environment, use feature branches with production testing

## 📝 Lessons Learned

1. **Database Unity Complexity**: Sharing databases across environments requires perfect credential sync
2. **Frontend-Backend Coupling**: Need to verify frontend is actually hitting intended backend
3. **Authentication State**: Auth tokens might not be portable across different backend instances
4. **Configuration Drift**: Easy for environment variables to get out of sync

---

**Status**: 🚨 BLOCKED - Authentication still failing despite CORS and database configuration  
**Next Action**: Complete environment variable audit and sync  
**Updated**: January 20, 2025 