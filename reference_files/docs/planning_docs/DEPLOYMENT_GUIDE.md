# Development & Production Environment Setup

## 🏗️ Architecture Overview

Fridays at Four uses a dual-environment setup to ensure safe development and stable production deployments:

- **Production Environment**: Serves real users with production data
- **Development Environment**: Safe testing environment with shared database but isolated backend

## 🌐 Frontend Deployment (Vercel)

### Domain Structure
- **Production**: `app.fridaysatfour.co` (from `main` branch)
- **Development**: `dev.fridaysatfour.co` (from `dev` branch)

### Branch Configuration
- **Production Branch**: `main` → Auto-deploys to production domain
- **Development Branch**: `dev` → Auto-deploys to dev subdomain
- **Branch Tracking**: Enabled for both environments in Vercel settings

### Critical Frontend Configuration

**⚠️ IMPORTANT**: Frontend code must use environment variables, NOT hardcoded URLs.

#### ✅ Correct Frontend API Configuration
```javascript
// In frontend code (e.g., /app/chat/page.tsx)
const API_BASE = process.env.NEXT_PUBLIC_BACKEND_API_URL || 'http://localhost:8000';
```

#### ❌ Common Mistake to Avoid
```javascript
// DON'T DO THIS - Bypasses environment variables!
const API_BASE = process.env.NODE_ENV === 'production' 
  ? 'https://fridays-at-four-c9c6b7a513be.herokuapp.com'
  : 'http://localhost:8000';
```

## 🚀 Backend Deployment (Heroku)

### Heroku Apps
- **Production**: `fridays-at-four-c9c6b7a513be.herokuapp.com`
- **Development**: `fridays-at-four-dev-434b1a68908b.herokuapp.com`

### Git Remotes Configuration
```bash
# Verify current remotes
git remote -v

# Expected output:
# dev     https://git.heroku.com/fridays-at-four-dev.git (fetch)
# dev     https://git.heroku.com/fridays-at-four-dev.git (push)
# heroku  https://git.heroku.com/fridays-at-four.git (fetch)
# heroku  https://git.heroku.com/fridays-at-four.git (push)
# origin  https://github.com/fridays-at-four/fridays-at-four.git (fetch)
# origin  https://github.com/fridays-at-four/fridays-at-four.git (push)
```

### Backend Deployment Process
```bash
# Deploy to development backend (from dev branch)
git push dev dev:main

# Deploy to production backend (from main branch)
git push heroku main:main
```

## 🔧 Environment Variables

### Shared Variables (All Environments)
All environments use the same values for:
- `NEXT_PUBLIC_SUPABASE_REFERENCE_ID`
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`
- `SUPABASE_URI_CONNECTION`
- `SUPABASE_SERVICE_KEY`
- `NEXT_PUBLIC_SUPABASE_URL`
- `ANTHROPIC_API_KEY`

### Environment-Specific Variables

#### Vercel Frontend Environment Variables

**Production Environment** (app.fridaysatfour.co):
```
NEXT_PUBLIC_BACKEND_API_URL = https://fridays-at-four-c9c6b7a513be.herokuapp.com
```

**Development Environment** (dev.fridaysatfour.co):
```
NEXT_PUBLIC_BACKEND_API_URL = https://fridays-at-four-dev-434b1a68908b.herokuapp.com
```

#### How to Set Vercel Environment Variables
1. Go to Vercel dashboard → Your project → Settings → Environment Variables
2. Create `NEXT_PUBLIC_BACKEND_API_URL` variable
3. **Critical**: Set different values for Production vs Development environments
4. Redeploy frontend after changing environment variables

## 🔄 Complete Deployment Workflow

### Development Workflow
1. **Make changes** on `dev` branch
2. **Frontend**: Push to GitHub → Vercel auto-deploys to `dev.fridaysatfour.co`
3. **Backend**: `git push dev dev:main` → Deploys to dev Heroku instance
4. **Test**: Verify functionality on dev environment
5. **Frontend connects to**: Development backend automatically via `NEXT_PUBLIC_BACKEND_API_URL`

### Production Workflow
1. **Merge** `dev` → `main` branch (after testing)
2. **Frontend**: Auto-deploys to production domain
3. **Backend**: `git push heroku main:main` → Deploys to production Heroku
4. **Frontend connects to**: Production backend automatically via environment variables

### Verification Steps After Deployment
```bash
# 1. Test dev backend health
curl https://fridays-at-four-dev-434b1a68908b.herokuapp.com/health

# 2. Test production backend health  
curl https://fridays-at-four-c9c6b7a513be.herokuapp.com/health

# 3. Check frontend is hitting correct backend
# - Visit dev.fridaysatfour.co
# - Open browser Network tab
# - Make API call (e.g., send chat message)
# - Verify API calls go to dev backend URL

# 4. Monitor backend logs during testing
heroku logs --tail --app fridays-at-four-dev
```

## 🧪 Testing Backend Connectivity

### Monitor Dev Backend Logs
```bash
heroku logs --tail --app fridays-at-four-dev
```

### Monitor Production Backend Logs
```bash
heroku logs --tail --app fridays-at-four-c9c6b7a513be
```

### Test Frontend → Backend Connection
1. Visit `dev.fridaysatfour.co`
2. Open browser Developer Tools → Network tab
3. Use any feature that calls the backend (chat, forms, etc.)
4. Verify API calls go to correct Heroku instance URL
5. Check backend logs show incoming requests

### Expected API Calls
- **Dev Frontend**: Calls `fridays-at-four-dev-434b1a68908b.herokuapp.com`
- **Production Frontend**: Calls `fridays-at-four-c9c6b7a513be.herokuapp.com`

## 🔒 Data Configuration

### Database Strategy
- **Shared Database**: Both environments use the same Supabase production database
- **Isolated Processing**: Different backend instances handle requests separately
- **Auto-Dependency Creation**: Both backends auto-create creator profiles when needed

### Why Shared Database Works
- User authentication data remains consistent
- Test users can be easily identified and cleaned up
- Production data integrity maintained through backend isolation

## 🚨 Troubleshooting

### Frontend Not Connecting to Correct Backend

**Problem**: Dev frontend calling wrong backend URL

**Root Cause**: Usually hardcoded URLs in frontend code instead of environment variables

**Solution**: 
1. Check frontend code uses `process.env.NEXT_PUBLIC_BACKEND_API_URL`
2. Verify environment variable is set correctly in Vercel for both environments
3. Check browser Network tab to see actual API URLs being called
4. Redeploy frontend after environment variable changes

### Auto-Deployment Not Working

**Problem**: Push to dev branch doesn't trigger deployment

**Solution**:
1. Verify branch tracking enabled in Vercel settings
2. Check Vercel "Git" settings for correct repository and branch mapping
3. Force deployment: Make small change + push
4. Use manual "Deploy" button in Vercel dashboard if needed

### Backend Not Receiving Requests

**Problem**: No logs in Heroku when testing frontend

**Solution**:
1. Check frontend Network tab for actual API URLs
2. Verify environment variable deployment in Vercel
3. Test backend directly: `curl https://your-backend-url.herokuapp.com/health`
4. Check for typos in environment variable URLs
5. Ensure frontend code is using environment variables correctly

### Environment Variables Not Taking Effect

**Problem**: Changed environment variables but frontend still hitting wrong backend

**Solution**:
1. Redeploy frontend from Vercel dashboard
2. Check environment variable is set for correct environment (Production vs Development)
3. Clear browser cache
4. Verify variable name is exactly `NEXT_PUBLIC_BACKEND_API_URL`

### CORS Issues

**Problem**: CORS blocking between frontend and backend

**Current CORS Configuration** (in `src/main.py`):
```python
ALLOWED_ORIGINS = [
    "https://*.squarespace.com",
    "https://*.slack.com", 
    "https://zoom.us",
    "https://fridays-at-four-c9c6b7a513be.herokuapp.com",
    "https://app.fridaysatfour.co",  # Production frontend
    "https://dev.fridaysatfour.co",  # Dev frontend
    "http://localhost:3000"          # Local development
]
```

**Solution**: Ensure both frontend domains are in CORS allowed origins on both backend deployments

## 🛠️ Setup Commands

### Initial Setup (One-time)
```bash
# Add Heroku remotes if not already configured
heroku git:remote -a fridays-at-four-c9c6b7a513be  # Production
heroku git:remote -a fridays-at-four-dev-434b1a68908b --remote dev  # Development

# Verify remotes
git remote -v
```

### Daily Development
```bash
# Work on dev branch
git checkout dev

# Make changes, commit
git add .
git commit -m "feat: description of changes"

# Deploy backend to dev environment
git push dev dev:main

# Frontend auto-deploys when you push to GitHub dev branch
git push origin dev

# Test on dev.fridaysatfour.co
# Verify correct backend is being called in Network tab

# When ready, merge to main and deploy to production
git checkout main
git merge dev
git push origin main      # Triggers frontend production deployment
git push heroku main:main # Deploys backend to production
```

## 🎯 Success Criteria

✅ **Working Setup Indicators**:
- Dev frontend hits dev backend (verified in browser Network tab + Heroku logs)
- Production frontend hits production backend
- Environment variables correctly configured in Vercel
- Auto-deployment working for both environments  
- CORS properly configured for both domains
- Frontend code uses `process.env.NEXT_PUBLIC_BACKEND_API_URL` instead of hardcoded URLs

## 📊 Environment URLs Reference

| Environment | Frontend URL | Backend URL | Environment Variable |
|-------------|-------------|-------------|---------------------|
| **Production** | `https://app.fridaysatfour.co` | `https://fridays-at-four-c9c6b7a513be.herokuapp.com` | Set in Vercel Production |
| **Development** | `https://dev.fridaysatfour.co` | `https://fridays-at-four-dev-434b1a68908b.herokuapp.com` | Set in Vercel Development |
| **Local** | `http://localhost:3000` | `http://localhost:8000` | Fallback in code |

## 🔑 Key Lessons Learned

1. **Environment variables are only effective if the code actually uses them** - Hardcoded URLs will bypass all Vercel configuration
2. **Browser Network tab is your best friend** - Always verify which backend URL is actually being called
3. **Shared database with isolated backends works well** - Provides consistency while enabling safe testing
4. **Deployment order matters** - Deploy backend first, then test frontend connection
5. **Environment-specific configuration in Vercel is critical** - Same variable name, different values per environment

This setup ensures safe development iteration while maintaining stable production service for real users. 