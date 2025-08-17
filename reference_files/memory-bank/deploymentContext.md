# 🚀 Fridays at Four - Deployment & CI/CD Context

## 🏗️ Dual-Environment Architecture

### Complete Environment Separation
**🎯 PRODUCTION READY**: Full dual-environment setup deployed and operational

**Architecture**: Independent frontend + backend for both environments
- **Production**: Real users, stable, production data
- **Development**: Safe testing, isolated dev data, full feature parity

### Environment URLs
| Environment | Frontend | Backend |
|-------------|----------|---------|
| **Production** | `https://fridaysatfour.co` | `https://fridays-at-four-c9c6b7a513be.herokuapp.com` |
| **Development** | `https://dev.fridaysatfour.co` | `https://fridays-at-four-dev-434b1a68908b.herokuapp.com` |
| **Local** | `http://localhost:3000` | `http://localhost:8000` |

---

## 🔄 Deployment Workflows

### ✅ **GitHub Actions CI/CD Pipeline (OPERATIONAL)**
**Status**: 🎉 **FIXED AND FULLY OPERATIONAL** (Dec 2024)

**Automated Deployment**:
- **Dev branch push** → GitHub Actions → `fridays-at-four-dev.herokuapp.com`
- **Main branch push** → GitHub Actions → `fridays-at-four.herokuapp.com`
- **Frontend**: Auto-deploys from respective branches to Vercel

**Workflow File**: `.github/workflows/deploy.yml`
- ✅ Environment-specific logic working
- ✅ `HEROKU_API_KEY` configured in repository secrets
- ✅ App targeting correct (`fridays-at-four` vs `fridays-at-four-dev`)
- ✅ Full environment variable injection

### 🚨 **Manual Deployment DISABLED (Security)**
```bash
# ❌ These commands no longer work (remotes removed):
# git push dev dev:main  
# git push heroku main:main

# ✅ Only deployment method now:
git push origin dev    # → Triggers GitHub Actions → Dev deployment
git push origin main   # → Triggers GitHub Actions → Prod deployment
```

**Safety Measures**:
- ✅ All local Heroku remotes removed
- ✅ Manual deployment impossible 
- ✅ All deployments go through GitHub Actions only
- ✅ Full audit trail and approval workflow

---

## 🛠️ Git Remotes Configuration

**Current Setup**: ✅ **SECURITY-OPTIMIZED** (Dec 2024)
```bash
git remote -v
# origin  https://github.com/fridays-at-four/fridays-at-four.git (fetch)
# origin  https://github.com/fridays-at-four/fridays-at-four.git (push)

# ✅ REMOVED FOR SECURITY:
# dev     https://git.heroku.com/fridays-at-four-dev.git (REMOVED)
# heroku  https://git.heroku.com/fridays-at-four.git (REMOVED)
```

**Why Remotes Were Removed**:
- 🛡️ **Prevents accidental production deployments**
- 🔒 **Forces all deployments through GitHub Actions**
- 📊 **Ensures audit trail and review process**
- ⚡ **Eliminates "oops" factor in deployment**

---

## 🔧 Environment Variables & Configuration

### Backend Environment Variables
**Both environments share**:
- Database credentials (Supabase)
- AI API keys (Anthropic)
- Integration credentials (Slack, Zoom)

**Environment-specific**:
- Frontend uses `NEXT_PUBLIC_BACKEND_API_URL` to connect to correct backend
- Each frontend automatically connects to its paired backend

### CORS Configuration
**Current**: ✅ Both domains properly configured
```python
ALLOWED_ORIGINS = [
    "https://app.fridaysatfour.co",  # Production frontend
    "https://dev.fridaysatfour.co",  # Development frontend ← RECENTLY ADDED
    "http://localhost:3000"          # Local development
    # ... other domains
]
```

---

## 🧪 Testing & Validation

### Backend Health Monitoring
```bash
# Development environment
curl https://fridays-at-four-dev-434b1a68908b.herokuapp.com/health
# {"status":"healthy","components":{"supabase":"connected","memory":"working","agent":"responding"}}

# Production environment  
curl https://fridays-at-four-c9c6b7a513be.herokuapp.com/health
```

### Real-time Log Monitoring
```bash
# Development logs
heroku logs --tail --app fridays-at-four-dev-434b1a68908b

# Production logs
heroku logs --tail --app fridays-at-four-c9c6b7a513be
```

---

## 🔒 Data Isolation & Safety

### Development Environment Benefits
- **Safe experimentation**: No risk to production users
- **Full feature testing**: Complete backend functionality
- **Real data structures**: Same database schema as production
- **Integration testing**: End-to-end frontend ↔ backend validation

### Production Environment Protection
- **Stable service**: Development changes don't affect production
- **User data safety**: No cross-contamination between environments
- **Controlled deployments**: Tested features only reach production

---

## 🎯 Current Development Status

### ✅ Recently Completed
- **Dual-environment setup**: Both backends operational
- **CORS fix deployed**: dev.fridaysatfour.co can access dev backend
- **Claude migration**: Latest backend code deployed to dev environment
- **Health monitoring**: All components verified working

### 🔄 Next Steps
1. **Frontend integration testing**: Verify dev.fridaysatfour.co ↔ dev backend
2. **Feature development**: Use dev environment for new features
3. **Production promotion**: Deploy tested features from dev → production

---

## 📊 Deployment History

### Latest Deployments
- **Dev Backend**: Latest commit with Claude migration + CORS fix
- **Production Backend**: Previous stable version (pre-Claude migration)
- **Both Frontends**: Auto-deploying from respective branches

### Deployment Strategy
- **Development-first**: All changes tested in dev environment
- **Merge promotion**: dev branch → main branch → production deployment
- **Zero-downtime**: Both environments can be updated independently

---

## 🚨 Troubleshooting Quick Reference

### Common Issues & Solutions

**CORS Errors**
- Check `ALLOWED_ORIGINS` includes correct frontend domain
- Verify deployment picked up CORS changes

**Frontend → Backend Connection**
- Check `NEXT_PUBLIC_BACKEND_API_URL` environment variable
- Verify frontend builds with correct environment configuration

**Backend Not Responding**  
- Check Heroku logs for errors
- Verify health endpoint returns 200 status
- Confirm all environment variables set

### Environment Validation Checklist
- [ ] Backend health endpoint returns "healthy"
- [ ] Frontend connects to correct backend (check Network tab)
- [ ] CORS allows frontend domain
- [ ] Chat functionality works end-to-end
- [ ] Logs show incoming requests from frontend

---

*This dual-environment setup ensures safe development iteration while maintaining stable production service for real users.* 

## 🎯 Current Production Environment Status

### 🌐 **Production URLs & Status**
- **Backend API**: `fridays-at-four-c9c6b7a513be.herokuapp.com` ✅ STABLE
- **Frontend**: `app.fridaysatfour.co` ✅ STABLE 
- **Database**: Supabase (auto-scaling) ✅ STABLE
- **Monitoring**: Heroku logs + database dashboard ✅ ACTIVE

### 🚨 **Critical Production Issue (June 4, 2025)**
**Issue**: Frontend authentication bug causing conversation data to save under wrong user accounts
**Status**: Root cause confirmed, fix in progress
**Impact**: Real users affected - conversations saved but not visible in their accounts

---

## 🏗️ Development & Deployment Workflow

### 🔄 **Development Workflow**
- **Branch Protection**: dev and main branches protected, PR reviews required
- **Commit Conventions**: feat/fix/chore/docs with task IDs  
- **Environment Variables**: GitHub secrets/vars (main source), never commit .env
- **Database Changes**: Always generate migrations with `supabase db diff`

### 📁 **Repository Structure**
```
fridays-at-four/
├── src/                 # Backend FastAPI application
├── docs/FAF_website/    # Frontend Next.js 14 application
├── memory-bank/         # Project intelligence and context
├── supabase/           # Database schema and migrations
├── test-suite/         # Comprehensive testing framework
└── scripts/            # Utility scripts and tools
```

### 💻 **Critical Development Commands**
```bash
# Development cycle
git checkout dev && git pull origin dev
git checkout -b feat/[task-id]-description
# ... make changes ...
git push origin feat/[task-id]-description

# Database migration  
supabase db diff [migration-name]
supabase db reset  # Test locally

# Production deployment
git push heroku main
```

---

## 🏗️ Integration Architecture

### 🎨 **Frontend Deployment (Vercel)**
- **Framework**: Next.js 14 with TypeScript
- **Deployment**: Auto-deploy from main branch
- **Environment**: Production environment variables in Vercel dashboard
- **Domain**: `app.fridaysatfour.co`
- **Status**: ✅ Stable streaming integration

### ⚙️ **Backend Deployment (Heroku)** 
- **Framework**: FastAPI with Python 3.11
- **Deployment**: Manual `git push heroku main`
- **Environment**: Heroku config vars for API keys
- **Scaling**: Standard dyno, can scale horizontally
- **Status**: ✅ Production-ready, 175 conversations handled successfully

### 💾 **Database (Supabase)**
- **Type**: PostgreSQL with auto-scaling
- **Migrations**: Automated on deployment
- **Backups**: Automated daily backups
- **Access**: Direct admin access + API integration
- **Status**: ✅ 100% uptime, zero data corruption

### 🧪 **Testing & CI/CD (GitHub Actions)**
- **Backend Tests**: 49/49 passing
- **Integration Tests**: Production API validation
- **Deployment Gates**: Tests must pass before merge
- **Status**: ✅ Comprehensive coverage

---

## 🔧 Production Debugging & Investigation Tools

### 🛠️ **Database Investigation Tools** (Created June 4, 2025)
**Created during authentication bug investigation**

#### `db_debug.py` - Production Database Inspector
```bash
# Check specific user data
python db_debug.py check <user_id>

# List recent conversations  
python db_debug.py conversations --recent

# Verify user profiles
python db_debug.py profiles --all

# Clean test data
python db_debug.py cleanup <test_user_id>
```

**Features**:
- ✅ Direct production database access
- ✅ User conversation analysis
- ✅ Profile verification
- ✅ Data cleanup utilities
- ✅ Real-time investigation during production issues

### 📊 **Production Monitoring Patterns**

#### Frontend Debugging
```javascript
// Browser dev tools investigation
console.log("Authentication response:", signInResponse);
console.log("User ID being used:", userId);
console.log("API call user ID:", apiClient.getUserId());
```

#### Backend Log Analysis
```bash
# Real-time Heroku logs
heroku logs --tail --app fridays-at-four

# Search for specific user activity
heroku logs --app fridays-at-four | grep "user_id: 22243ba0"

# Check authentication endpoints
heroku logs --app fridays-at-four | grep "/chat"
```

#### Database Investigation
```python
# Check conversation storage by user
supabase.table('conversations').select('*').eq('user_id', user_id).execute()

# Verify user profiles exist
supabase.table('creator_profiles').select('*').eq('id', user_id).execute()

# Find conversations by content
supabase.table('conversations').select('*').ilike('messages', '%Hey, remember%').execute()
```

---

## 🚨 Production Crisis Response Protocols

### 🔍 **Investigation Process** (Proven June 4, 2025)
1. **User Report**: Real user (Krystal) reports missing conversations
2. **Cross-System Check**: Frontend logs + backend logs + database state
3. **Data Verification**: Use `db_debug.py` to check conversation storage
4. **Pattern Analysis**: Look for systematic vs isolated issues
5. **Root Cause**: Multi-source evidence to confirm diagnosis

### 🛡️ **Evidence Collection**
- **Frontend**: Browser dev tools (Console + Network tabs)
- **Backend**: Heroku logs with user ID filtering
- **Database**: Direct queries with investigation tools
- **User Experience**: Screen recordings and step-by-step reproduction

### 🔧 **Fix Implementation**
1. **Confirm root cause** with multiple evidence sources
2. **Create isolated test case** reproducing the issue
3. **Implement fix** with comprehensive testing
4. **Validate fix** across all systems (frontend → backend → database)
5. **Deploy** with monitoring for regression

---

## 🔐 Environment Configuration

### 🔧 **Environment Variables (API Keys Only)**
**Backend (.env / Heroku Config)**:
```bash
ANTHROPIC_API_KEY=sk-ant-...
SUPABASE_URL=https://...
SUPABASE_ANON_KEY=eyJ...
SUPABASE_SERVICE_ROLE_KEY=eyJ... # For admin operations
```

**Frontend (Vercel Environment)**:
```bash
NEXT_PUBLIC_SUPABASE_URL=https://...
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ...
```

### ⚠️ **Security Considerations**
- **✅ API keys**: Environment variables only, never committed
- **✅ Database access**: Service role key restricted to backend
- **✅ CORS**: Configured for specific domains only
- **❌ User ID validation**: **CRITICAL GAP** - Need frontend validation

---

## 📈 Performance & Monitoring

### 🚀 **Current Performance Metrics**
- **Backend Response**: <3 seconds for streaming responses
- **Database Queries**: <100ms for typical operations
- **Conversation Storage**: 175/175 successful (100% backend reliability)
- **Frontend Loading**: <2 seconds initial page load

### 📊 **Monitoring Tools**
- **Heroku Metrics**: Resource usage and response times
- **Supabase Dashboard**: Database performance and query analysis
- **Browser Dev Tools**: Frontend error tracking and network analysis
- **Custom Scripts**: `db_debug.py` for production investigation

### 🔍 **Alerting & Detection**
- **Missing**: Automated alerting for authentication failures
- **Missing**: User session validation monitoring
- **Missing**: Cross-system user ID consistency checks
- **Need**: Frontend error tracking service (Sentry/LogRocket)

---

## 🏆 Production Lessons Learned (June 4, 2025)

### ✅ **What Works Well**
- **Backend Reliability**: 175 conversations stored successfully without any backend failures
- **Database Integrity**: Zero foreign key violations or data corruption
- **Investigation Tools**: `db_debug.py` enabled rapid production diagnosis
- **Cross-System Debugging**: Frontend logs + backend logs + database state = complete picture

### ⚠️ **Critical Gaps Identified**
- **Frontend Error Visibility**: Silent authentication failures not caught
- **User ID Validation**: No consistency checks between frontend display and API calls
- **Production Monitoring**: Need automated alerts for authentication issues
- **User Session Tracking**: Missing visibility into real user authentication flows

### 🔧 **Immediate Improvements Needed**
1. **Frontend Error Tracking**: Implement Sentry or LogRocket
2. **Authentication Monitoring**: Alert on null authentication responses
3. **User ID Validation**: Add consistency checks across all API calls
4. **Session Management**: Better visibility into user authentication state

### 📚 **Documentation Improvements**
- **✅ Created**: Comprehensive production debugging guide
- **✅ Created**: Database investigation utility with full documentation
- **✅ Created**: Cross-system debugging workflow
- **Need**: Frontend error handling best practices guide

---

**Last Updated**: June 4, 2025 - Added production debugging tools and crisis response protocols  
**Status**: 🎯 **Production debugging capabilities enhanced** - Tools created during real crisis  
**Next Update**: After authentication fix deployment - document solution implementation patterns 