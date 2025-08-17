# 🚀 Deployment Guide

Complete guide to deploying Fridays at Four. This covers both frontend and backend deployment processes, environment management, and rollback procedures.

## 🏗️ Deployment Architecture

```
Frontend (Vercel) → Backend (Heroku) → Database (Supabase)
Next.js              FastAPI            PostgreSQL
Auto-deploy          Manual deploy      Auto-migrate
```

## 🎯 Current Deployment Status

### ✅ What's Automated
- **Frontend**: Auto-deploys from `main` branch to Vercel
- **Database**: Migrations run automatically via Supabase
- **Environment**: Variables managed through platform dashboards

### ⚠️ What's Manual
- **Backend**: Requires manual `git push heroku main`
- **Testing**: Manual verification after deployments
- **Rollbacks**: Manual process if issues occur

## 🌐 Frontend Deployment (Vercel)

### Current Setup
- **Platform**: Vercel
- **Domain**: `app.fridaysatfour.co`
- **Repository**: Connected to GitHub main branch
- **Build Command**: `npm run build`
- **Framework**: Next.js

### Automatic Deployment Process
1. **Push to main branch** → Vercel automatically detects changes
2. **Build process starts** → Vercel runs `npm run build`
3. **Deployment completes** → New version goes live automatically
4. **Verification** → Check `app.fridaysatfour.co` is working

### Frontend Environment Variables
Set in Vercel dashboard under **Settings > Environment Variables**:

```env
# Required for production
NEXT_PUBLIC_API_BASE_URL=https://fridays-at-four-c9c6b7a513be.herokuapp.com
NEXT_PUBLIC_SUPABASE_URL=https://ipvxxsthulsysbkwbitu.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Optional analytics/monitoring
NEXT_PUBLIC_ANALYTICS_ID=your-analytics-id
```

### Frontend Deployment Checklist
- [ ] Changes tested locally with `npm run dev`
- [ ] Build succeeds locally with `npm run build`
- [ ] TypeScript errors resolved
- [ ] Environment variables updated if needed
- [ ] Changes merged to main branch
- [ ] Vercel deployment completes successfully
- [ ] Production site tested manually

### Troubleshooting Frontend Deployments

#### Build Failures
```bash
# Common issues and fixes:

# 1. TypeScript errors
npm run type-check

# 2. Missing dependencies
npm install

# 3. Environment variable issues
# Check Vercel dashboard for missing variables

# 4. Import path issues
# Ensure all imports use correct relative paths
```

#### Rollback Process
1. **Identify last working deployment** in Vercel dashboard
2. **Click "Promote to Production"** on that deployment
3. **Verify rollback** by testing the site

## ⚙️ Backend Deployment (Heroku)

### Current Setup
- **Platform**: Heroku
- **App Name**: `fridays-at-four-c9c6b7a513be`
- **Domain**: `fridays-at-four-c9c6b7a513be.herokuapp.com`
- **Repository**: Manual deployment from local machine
- **Runtime**: Python 3.11

### Manual Deployment Process

#### Prerequisites
```bash
# Install Heroku CLI
brew install heroku/brew/heroku

# Login to Heroku
heroku login

# Add Heroku remote (one-time setup)
git remote add heroku https://git.heroku.com/fridays-at-four-c9c6b7a513be.git
```

#### Deployment Steps
```bash
# 1. Ensure you're on the main branch
git checkout main
git pull origin main

# 2. Run local tests (optional but recommended)
python -m pytest new_tests/real_world_tests/test_live_endpoints.py

# 3. Deploy to Heroku
git push heroku main

# 4. Monitor deployment logs
heroku logs --tail --app fridays-at-four-c9c6b7a513be

# 5. Verify deployment
curl https://fridays-at-four-c9c6b7a513be.herokuapp.com/health
```

### Backend Environment Variables
Set in Heroku dashboard under **Settings > Config Vars**:

```env
# Required API keys
ANTHROPIC_API_KEY=sk-ant-...
SUPABASE_URL=https://ipvxxsthulsysbkwbitu.supabase.co
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Optional integrations
PERPLEXITY_API_KEY=your-perplexity-key-here
SLACK_BOT_TOKEN=your-slack-token-here
ZOOM_CLIENT_ID=your-zoom-client-id
ZOOM_CLIENT_SECRET=your-zoom-client-secret

# Application settings
ENVIRONMENT=production
LOG_LEVEL=INFO
```

### Backend Deployment Checklist
- [ ] Code tested locally with real API calls
- [ ] All tests passing in `new_tests/real_world_tests/`
- [ ] Environment variables updated if needed
- [ ] No sensitive data in code (use environment variables)
- [ ] Requirements.txt updated if dependencies changed
- [ ] Database migrations tested (if any)
- [ ] Changes committed to main branch
- [ ] Heroku deployment completes successfully
- [ ] Health endpoint responds correctly
- [ ] Core functionality tested with real API calls

### Troubleshooting Backend Deployments

#### Deployment Failures
```bash
# Check deployment logs
heroku logs --tail --app fridays-at-four-c9c6b7a513be

# Common issues:

# 1. Build pack detection failure
# Ensure requirements.txt is in root directory

# 2. Python version issues
# Check runtime.txt specifies correct Python version

# 3. Missing dependencies
# Update requirements.txt with all needed packages

# 4. Environment variable issues
# Verify all required env vars are set in Heroku config
```

#### Application Crashes
```bash
# Check application logs
heroku logs --app fridays-at-four-c9c6b7a513be

# Restart application
heroku restart --app fridays-at-four-c9c6b7a513be

# Check dyno status
heroku ps --app fridays-at-four-c9c6b7a513be
```

#### Rollback Process
```bash
# View recent releases
heroku releases --app fridays-at-four-c9c6b7a513be

# Rollback to previous release
heroku rollback v123 --app fridays-at-four-c9c6b7a513be

# Verify rollback
curl https://fridays-at-four-c9c6b7a513be.herokuapp.com/health
```

## 🗄️ Database Deployment (Supabase)

### Current Setup
- **Platform**: Supabase (managed PostgreSQL)
- **Migrations**: Automatic via Supabase CLI
- **Backups**: Automatic daily backups
- **Monitoring**: Built-in Supabase dashboard

### Migration Process
```bash
# 1. Create migration (when schema changes)
supabase db diff create_new_feature

# 2. Test migration locally
supabase db reset

# 3. Push to production (auto-applies)
git push origin main  # Migrations auto-apply via GitHub integration
```

### Database Deployment Checklist
- [ ] Migration tested locally with `supabase db reset`
- [ ] Migration file committed to repository
- [ ] No data loss risk assessed
- [ ] Backup verified before major changes
- [ ] Migration applied successfully
- [ ] Application still works with new schema

## 🔄 Complete Deployment Workflow

### For Feature Releases
```bash
# 1. Development and testing
git checkout -b feature/new-feature
# ... develop and test ...
git push origin feature/new-feature

# 2. Create pull request
# Review code, run tests, get approval

# 3. Merge to main
git checkout main
git pull origin main

# 4. Deploy backend (manual)
git push heroku main

# 5. Verify deployment
curl https://fridays-at-four-c9c6b7a513be.herokuapp.com/health

# 6. Frontend auto-deploys from main
# Verify at app.fridaysatfour.co

# 7. Run integration tests
python new_tests/real_world_tests/test_live_endpoints.py
```

### For Hotfixes
```bash
# 1. Create hotfix branch from main
git checkout main
git checkout -b hotfix/critical-fix

# 2. Make minimal fix
# ... fix the issue ...

# 3. Test fix locally
python -m pytest

# 4. Deploy immediately
git checkout main
git merge hotfix/critical-fix
git push origin main
git push heroku main

# 5. Verify fix
curl https://fridays-at-four-c9c6b7a513be.herokuapp.com/health
```

## 🧪 Testing Deployments

### Pre-Deployment Testing
```bash
# Backend tests
python new_tests/real_world_tests/test_live_endpoints.py

# Frontend build test
npm run build

# Integration test
curl -X POST localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question":"test","user_id":"test","user_timezone":"UTC","thread_id":"test"}'
```

### Post-Deployment Verification
```bash
# Health checks
curl https://fridays-at-four-c9c6b7a513be.herokuapp.com/health
curl https://app.fridaysatfour.co/api/health

# Core functionality
curl -X POST https://fridays-at-four-c9c6b7a513be.herokuapp.com/query \
  -H "Content-Type: application/json" \
  -d '{"question":"Hello","user_id":"test-deploy","user_timezone":"UTC","thread_id":"deploy-test"}'

# Database connectivity
python -c "
from supabase import create_client
from src.config import Config
supabase = create_client(Config.SUPABASE_URL, Config.SUPABASE_SERVICE_KEY)
result = supabase.table('creator_profiles').select('id').limit(1).execute()
print(f'Database OK: {len(result.data)} profiles')
"
```

## 🚨 Emergency Procedures

### Complete System Outage
1. **Check status pages**:
   - Heroku: status.heroku.com
   - Vercel: vercel-status.com
   - Supabase: status.supabase.com

2. **Quick diagnostics**:
   ```bash
   # Backend health
   curl https://fridays-at-four-c9c6b7a513be.herokuapp.com/health
   
   # Frontend health
   curl https://app.fridaysatfour.co
   
   # Check Heroku app status
   heroku ps --app fridays-at-four-c9c6b7a513be
   ```

3. **Emergency rollback**:
   ```bash
   # Backend rollback
   heroku rollback --app fridays-at-four-c9c6b7a513be
   
   # Frontend rollback (via Vercel dashboard)
   # Go to deployments, find last working version, promote to production
   ```

### Partial Service Degradation
1. **Identify affected component** (frontend, backend, database)
2. **Check recent deployments** for correlation
3. **Review error logs** for specific issues
4. **Apply targeted fix** or rollback affected component

## 🔮 Future Automation Plans

### Planned CI/CD Improvements
1. **GitHub Actions**: Automated testing on pull requests
2. **Automated backend deployment**: Deploy on merge to main
3. **Staging environment**: Test deployments before production
4. **Automated rollbacks**: Revert on health check failures
5. **Deployment notifications**: Slack/email alerts for deployments

### Monitoring and Alerting
1. **Uptime monitoring**: Automated health checks
2. **Error tracking**: Sentry or similar for error monitoring
3. **Performance monitoring**: Response time tracking
4. **Database monitoring**: Query performance and connection health

## 📊 Deployment Metrics

### Current Performance Targets
- **Backend deployment time**: < 5 minutes
- **Frontend deployment time**: < 3 minutes
- **Zero-downtime deployments**: 99% success rate
- **Rollback time**: < 2 minutes when needed

### Success Criteria
- **Health endpoints**: Return 200 status
- **Core functionality**: Chat API responds within 5 seconds
- **Database**: Queries complete within 1 second
- **Frontend**: Pages load within 2 seconds

## 📚 Additional Resources

- **Heroku Documentation**: [devcenter.heroku.com](https://devcenter.heroku.com)
- **Vercel Documentation**: [vercel.com/docs](https://vercel.com/docs)
- **Supabase Documentation**: [supabase.com/docs](https://supabase.com/docs)
- **GitHub Actions**: [docs.github.com/actions](https://docs.github.com/actions)

## 🎯 Deployment Best Practices

1. **Test everything locally first** - Never deploy untested code
2. **Use feature flags** for risky changes
3. **Deploy during low-traffic periods** when possible
4. **Monitor deployments actively** - Don't deploy and disappear
5. **Have rollback plan ready** before deploying
6. **Document all changes** in commit messages and PR descriptions
7. **Coordinate with team** for major deployments

## 📝 Deployment Checklist Template

Copy this for each deployment:

```markdown
## Pre-Deployment
- [ ] Code reviewed and approved
- [ ] Tests passing locally
- [ ] Environment variables updated
- [ ] Database migrations tested
- [ ] Rollback plan identified

## Deployment
- [ ] Backend deployed successfully
- [ ] Frontend deployed successfully
- [ ] Health checks passing
- [ ] Core functionality verified

## Post-Deployment
- [ ] Integration tests run
- [ ] Error logs checked
- [ ] Performance metrics normal
- [ ] Team notified of deployment
```

Remember: **Deployments should be boring and predictable. If it's exciting, something went wrong!** 🚀 

# Deployment

## Backend (Heroku)

### Current Setup
- **Production**: `fridays-at-four-c9c6b7a513be.herokuapp.com`  
- **Git Remote**: `heroku` (manual deployment)
- **Environment**: All config vars set in Heroku dashboard

### Deployment Process
```bash
# ⚠️ PRODUCTION DEPLOYMENT FORBIDDEN without explicit permission
# Only dev deployments allowed

git push heroku main  # Production (FORBIDDEN)
git push origin dev   # Development (with permission only)
```

### Environment Variables (Heroku Config)
```bash
# Required
ANTHROPIC_API_KEY=sk-ant-...
SUPABASE_URL=https://ipvxxsthulsysbkwbitu.supabase.co  # Production DB
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Optional
SLACK_BOT_TOKEN=xoxb-...
ZOOM_CLIENT_ID=...
ZOOM_CLIENT_SECRET=...
```

### Deployment Checklist
- [ ] Tests pass locally: `faf-pytest`
- [ ] Health endpoint working: `curl /health`
- [ ] Database migrations applied automatically
- [ ] Environment variables set in Heroku
- [ ] **Get explicit permission before deploying**

## Frontend (Vercel)

**Repository**: Separate frontend repo  
**Domain**: `app.fridaysatfour.co`  
**Process**: Auto-deploy from main branch

## Database (Supabase)

**Production**: `ipvxxsthulsysbkwbitu.supabase.co`  
**Development**: `mxlmadjuauugvlukgrla.supabase.co`

### Migrations
```bash
# Generate migration
supabase db diff migration_name

# Test locally (against dev DB)
supabase db reset

# Production migrations applied automatically on Heroku deploy
```

## Monitoring

### Health Check
```bash
curl https://fridays-at-four-c9c6b7a513be.herokuapp.com/health
```

### Logs
```bash
heroku logs --tail -a fridays-at-four-c9c6b7a513be
```

### Key Metrics
- Response time < 5 seconds
- Health endpoint returns 200
- No 5xx errors in logs

## Rollback

```bash
# If deployment breaks production
heroku rollback -a fridays-at-four-c9c6b7a513be
```

## Emergency Procedures

1. **Complete outage**: Check [status.heroku.com](https://status.heroku.com)
2. **Database issues**: Check [status.supabase.com](https://status.supabase.com)  
3. **Claude API issues**: Check [status.anthropic.com](https://status.anthropic.com)
4. **Critical bug**: Rollback immediately, fix in dev, redeploy 