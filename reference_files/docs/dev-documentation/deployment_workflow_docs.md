# Fridays at Four - Deployment Workflow Documentation

## 🏗️ Architecture Overview

### Repository Structure
- **Backend Repository**: `fridays-at-four` - FastAPI + Python
- **Frontend Repository**: `FAF_website` - Next.js + TypeScript  
- **Independent deployments** with environment-specific integrations

### Environment Flow
```
Feature Branch → Dev Branch → Main Branch
      ↓              ↓           ↓
   (Testing)    Dev Environment  Production
                      ↓              ↓
                 Dev Heroku     Prod Heroku
                      ↓              ↓
                 Dev Supabase   Prod Supabase
                      ↓              ↓
                 Dev Vercel     Prod Vercel
                      ↓              ↓
              dev.fridaysatfour.co  fridaysatfour.co
```

---

## 🚀 Current Deployment Process

### 1. Development Workflow
```bash
# Developer creates feature branch
git checkout -b feat/task-123-new-feature

# Work on feature, commit changes
git add .
git commit -m "Add new feature functionality"

# Push feature branch and create Pull Request
git push origin feat/task-123-new-feature
# Creates PR → triggers automated testing
```

### 2. Code Review & Dev Deployment
```bash
# Pull Request Process:
# ✅ Automated test suite runs
# ✅ Required reviewer approval (minimum 1 signature)
# ✅ PR can only be merged after approval
# ✅ Direct pushes to dev/main are blocked

# After PR approval, merge triggers dev deployment:
# ✅ Automatic deployment to Dev Heroku
# ✅ Updates Dev Vercel site (dev.fridaysatfour.co)
# ✅ Uses Dev Supabase database
```

### 3. Production Deployment
```bash
# Create Pull Request: dev → main
# ✅ Production test suite runs
# ✅ Required reviewer approval (minimum 1 signature)  
# ✅ Direct pushes to main are blocked

# After PR approval, merge triggers production deployment:
# ✅ Deploys to Prod Heroku
# ✅ Updates Prod Vercel site (fridaysatfour.co)
# ✅ Uses Prod Supabase database
```

---

## 🎯 GitHub Actions Automation

### Test Workflow (Pull Requests)
- **Trigger**: Any pull request created
- **Environment**: Matches target branch (dev or prod)
- **Actions**: 
  - Complete test suite execution
  - Dependencies validation
  - Environment-specific testing
- **Result**: Must pass before merge allowed

### Deploy Workflow (Branch Pushes)
- **Trigger**: Push to `dev` or `main` branch
- **Environment**: Auto-selected based on branch
- **Actions**:
  - Install dependencies
  - Deploy to appropriate Heroku app
  - Update environment variables
  - Verify deployment success

---

## 🌐 Environment Configuration

### Development Environment
- **Backend**: Dev Heroku app
- **Frontend**: dev.fridaysatfour.co (Vercel)
- **Database**: Dev Supabase instance
- **Purpose**: Feature testing and integration validation

### Production Environment  
- **Backend**: Prod Heroku app
- **Frontend**: fridaysatfour.co (Vercel)
- **Database**: Prod Supabase instance
- **Purpose**: Live user traffic

## 🔒 Code Quality & Security Controls

### Branch Protection Rules
- **Direct pushes blocked** to `dev` and `main` branches
- **Pull Request required** for all changes
- **Minimum 1 reviewer approval** required before merge
- **Automated tests must pass** before merge allowed
- **Branch up-to-date requirement** ensures latest code integration

---

## 🔐 Security & Secrets Management

### Environment Variables
- **GitHub Secrets**: API keys, database credentials
- **Heroku Config Vars**: Runtime environment variables
- **Vercel Environment Variables**: Frontend-specific settings

### Key Integrations
- **AI Services**: Anthropic Claude, OpenAI
- **Communication**: Slack, Zoom
- **Infrastructure**: Redis, Heroku, Vercel
- **Authentication**: Supabase Auth

---

## ⚡ Deployment Speed & Reliability

### Current Performance
- **Feature → Dev**: ~5-8 minutes (automated)
- **Dev → Production**: ~5-8 minutes (automated)  
- **Test Suite**: 49/49 tests passing (~3-5 minute execution)
- **Backend Response**: <2s API response time
- **Success Rate**: 95%+ deployment success
- **Rollback**: Manual git revert + redeploy if needed

### Success Metrics
- **Deployment Success Rate**: 95%+ (based on workflow history)
- **Automated Testing**: 100% required passage before deployment
- **Environment Isolation**: Complete separation between dev/prod

---

## 🛠️ Manual Interventions (Rare)

### When Manual Steps Are Needed
1. **Database Migrations**: Supabase schema changes (commented out in workflow)
2. **New Environment Variables**: Adding new API keys or configuration
3. **Infrastructure Changes**: Scaling Heroku dynos or Supabase resources
4. **Rollback Scenarios**: Reverting problematic releases

### Emergency Procedures
- **Quick Rollback**: Revert git commit + automatic redeploy
- **Database Issues**: Direct Supabase dashboard access
- **Service Outages**: Heroku status monitoring and manual scaling

---

## 📊 Monitoring & Observability

### Current Monitoring
- **Heroku Metrics**: Application performance and resource usage
- **Supabase Dashboard**: Database performance and query analytics
- **GitHub Actions**: Deployment success/failure notifications
- **Streamlit backend**: user and API monitoring

### Areas for Enhancement
- **User Analytics**: Frontend usage patterns
- **Error Tracking**: Automated error reporting (Sentry)
- **Performance Monitoring**: API response times and database query optimization
- **Business Metrics**: User engagement and conversion tracking


---

*This documentation represents the current state as of July 2025. The deployment infrastructure supports rapid, safe iterations while maintaining production stability.*