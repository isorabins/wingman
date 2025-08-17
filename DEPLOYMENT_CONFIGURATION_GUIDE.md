# Wingman Deployment & Configuration Guide

*Last Updated: August 16, 2025*

## Overview

This guide covers deployment configurations, environment setup, and operational procedures for the Wingman dating confidence platform across development, staging, and production environments.

## Architecture Summary

```
Frontend (Vercel)     Backend (Heroku)      Database (Supabase)
       │                     │                      │
   Next.js App          FastAPI Server         PostgreSQL
   Static Assets        AI Integration         File Storage
   Auth Context         Email Service          Real-time APIs
       │                     │                      │
       └─────────────────────┼──────────────────────┘
                             │
                    External Services
                    ├─ Claude AI (Anthropic)
                    ├─ Email (Resend)
                    └─ Cache (Redis)
```

## Environment Configurations

### Development Environment

**Purpose**: Local development and testing
**Infrastructure**: Local servers, development databases

#### Backend Configuration (.env)
```bash
# Core Application
DEVELOPMENT_MODE=true
DEBUG=true
LOG_LEVEL=DEBUG

# Database
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# AI Integration
ANTHROPIC_API_KEY=sk-ant-api03-your-development-key

# Email Service (Optional in dev)
RESEND_API_KEY=re_your-development-key

# Redis (Optional - will gracefully degrade)
REDIS_URL=redis://localhost:6379

# Feature Flags
ENABLE_CHALLENGES_CATALOG=true
ENABLE_RATE_LIMITING=false
ENABLE_EMAIL_NOTIFICATIONS=false

# Test Configuration
TEST_MODE_ENABLED=true
BYPASS_AUTH_FOR_TESTING=true
```

#### Frontend Configuration (.env.local)
```bash
# Supabase
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# API Endpoints
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000

# Feature Flags
NEXT_PUBLIC_ENABLE_ANALYTICS=false
NEXT_PUBLIC_DEBUG_MODE=true

# Development Tools
NEXT_PUBLIC_SHOW_DEBUG_INFO=true
```

### Staging Environment

**Purpose**: Pre-production testing and QA validation
**Infrastructure**: Heroku staging app, separate Supabase project

#### Backend Configuration (Heroku Config Vars)
```bash
# Core Application
DEVELOPMENT_MODE=false
DEBUG=false
LOG_LEVEL=INFO

# Database
SUPABASE_URL=https://staging-project.supabase.co
SUPABASE_SERVICE_KEY=staging_service_key
SUPABASE_ANON_KEY=staging_anon_key

# AI Integration
ANTHROPIC_API_KEY=sk-ant-api03-staging-key

# Email Service
RESEND_API_KEY=re_staging-key

# Redis
REDIS_URL=redis://staging-redis-url

# Feature Flags
ENABLE_CHALLENGES_CATALOG=true
ENABLE_RATE_LIMITING=true
ENABLE_EMAIL_NOTIFICATIONS=true

# Monitoring
SENTRY_DSN=https://your-sentry-dsn
NEW_RELIC_LICENSE_KEY=your-newrelic-key
```

#### Frontend Configuration (Vercel Environment Variables)
```bash
# Supabase
NEXT_PUBLIC_SUPABASE_URL=https://staging-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=staging_anon_key

# API Endpoints
NEXT_PUBLIC_API_BASE_URL=https://wingman-staging.herokuapp.com

# Analytics
NEXT_PUBLIC_ENABLE_ANALYTICS=true
NEXT_PUBLIC_GOOGLE_ANALYTICS_ID=GA-STAGING-ID

# Feature Flags
NEXT_PUBLIC_DEBUG_MODE=false
```

### Production Environment

**Purpose**: Live user-facing application
**Infrastructure**: Heroku production app, production Supabase project

#### Backend Configuration (Heroku Config Vars)
```bash
# Core Application
DEVELOPMENT_MODE=false
DEBUG=false
LOG_LEVEL=WARNING

# Database
SUPABASE_URL=https://prod-project.supabase.co
SUPABASE_SERVICE_KEY=prod_service_key
SUPABASE_ANON_KEY=prod_anon_key

# AI Integration
ANTHROPIC_API_KEY=sk-ant-api03-production-key

# Email Service
RESEND_API_KEY=re_production-key

# Redis
REDIS_URL=redis://production-redis-url

# Feature Flags
ENABLE_CHALLENGES_CATALOG=true
ENABLE_RATE_LIMITING=true
ENABLE_EMAIL_NOTIFICATIONS=true

# Security
BYPASS_AUTH_FOR_TESTING=false
TEST_MODE_ENABLED=false

# Monitoring & Analytics
SENTRY_DSN=https://production-sentry-dsn
NEW_RELIC_LICENSE_KEY=production-newrelic-key
DATADOG_API_KEY=production-datadog-key

# Performance
MAX_WORKERS=4
WORKER_TIMEOUT=30
```

#### Frontend Configuration (Vercel Environment Variables)
```bash
# Supabase
NEXT_PUBLIC_SUPABASE_URL=https://prod-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=prod_anon_key

# API Endpoints
NEXT_PUBLIC_API_BASE_URL=https://wingman-api.herokuapp.com

# Analytics
NEXT_PUBLIC_ENABLE_ANALYTICS=true
NEXT_PUBLIC_GOOGLE_ANALYTICS_ID=GA-PRODUCTION-ID
NEXT_PUBLIC_MIXPANEL_TOKEN=production-mixpanel-token

# Feature Flags
NEXT_PUBLIC_DEBUG_MODE=false
NEXT_PUBLIC_SHOW_DEBUG_INFO=false

# Performance
NEXT_PUBLIC_CDN_URL=https://cdn.wingmanapp.com
```

## Deployment Procedures

### Backend Deployment (Heroku)

#### Initial Setup
```bash
# Install Heroku CLI
curl https://cli-assets.heroku.com/install.sh | sh

# Login to Heroku
heroku login

# Create Heroku apps
heroku create wingman-staging
heroku create wingman-production

# Add buildpacks
heroku buildpacks:add heroku/python --app wingman-production

# Set up Heroku Postgres (if not using Supabase)
heroku addons:create heroku-postgresql:hobby-dev --app wingman-production
```

#### Deployment Steps
```bash
# 1. Deploy to staging first
git checkout main
git pull origin main

# 2. Deploy to staging
git push heroku-staging main

# 3. Run post-deployment tasks
heroku run python -c "import src.main; print('Health check')" --app wingman-staging

# 4. Run smoke tests
curl https://wingman-staging.herokuapp.com/api/health

# 5. If staging tests pass, deploy to production
git push heroku-production main

# 6. Run production health checks
curl https://wingman-api.herokuapp.com/api/health
```

#### Environment Variable Management
```bash
# Set environment variables
heroku config:set ANTHROPIC_API_KEY=sk-ant-... --app wingman-production
heroku config:set SUPABASE_URL=https://... --app wingman-production

# View current configuration
heroku config --app wingman-production

# Copy staging config to production (carefully!)
heroku config --app wingman-staging | heroku config:set --app wingman-production
```

### Frontend Deployment (Vercel)

#### Initial Setup
```bash
# Install Vercel CLI
npm install -g vercel

# Login to Vercel
vercel login

# Link project
vercel link
```

#### Deployment Steps
```bash
# 1. Deploy to preview (staging)
vercel --prod=false

# 2. Test preview deployment
# Visit provided preview URL and test functionality

# 3. Deploy to production
vercel --prod

# 4. Verify production deployment
curl https://wingmanapp.com/api/health
```

#### Environment Variables (Vercel Dashboard)
```bash
# Navigate to Vercel dashboard
# Go to Project Settings > Environment Variables
# Add production environment variables
# Redeploy if needed
```

### Database Deployment (Supabase)

#### Migration Management
```bash
# Link to remote Supabase project
supabase link --project-ref your-project-id

# Deploy local migrations to remote
supabase db push

# Verify migrations applied
supabase migration list --linked

# Generate and deploy Edge Functions (if any)
supabase functions deploy
```

#### Schema Updates
```bash
# 1. Create migration locally
supabase migration new add_new_feature

# 2. Test migration locally
supabase db reset

# 3. Deploy to staging database
supabase db push --linked --project-ref staging-project-id

# 4. Test staging functionality
python reference_files/real_world_tests/test_database_integration.py

# 5. Deploy to production database
supabase db push --linked --project-ref production-project-id
```

## Monitoring and Health Checks

### Application Health Endpoints

#### Backend Health Check
```http
GET /api/health
```

Response:
```json
{
  "status": "healthy",
  "timestamp": "2025-08-16T10:30:00Z",
  "services": {
    "database": "healthy",
    "redis": "healthy", 
    "claude_api": "healthy",
    "email_service": "healthy"
  },
  "version": "1.0.0",
  "environment": "production"
}
```

#### Database Health Check
```http
GET /api/health/db
```

#### AI Service Health Check
```http
GET /api/health/claude
```

### Monitoring Setup

#### Application Performance Monitoring (APM)
```python
# src/config.py - Add monitoring configuration
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

if Config.SENTRY_DSN:
    sentry_sdk.init(
        dsn=Config.SENTRY_DSN,
        integrations=[FastApiIntegration()],
        traces_sample_rate=1.0,
        environment=Config.ENVIRONMENT
    )
```

#### Logging Configuration
```python
# src/main.py - Structured logging
import logging
import sys

logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('app.log') if Config.LOG_TO_FILE else logging.NullHandler()
    ]
)
```

#### Metrics Collection
```python
# Custom metrics for business logic
from prometheus_client import Counter, Histogram

# Track API requests
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')

# Track business metrics
MATCHES_CREATED = Counter('wingman_matches_created_total', 'Total matches created')
ASSESSMENTS_COMPLETED = Counter('confidence_assessments_completed_total', 'Assessments completed')
```

### Performance Monitoring

#### Backend Performance Metrics
- **Response Time**: < 200ms for cached endpoints, < 2s for AI endpoints
- **Throughput**: > 100 requests/second sustained
- **Error Rate**: < 1% for application errors
- **Uptime**: > 99.9% availability

#### Frontend Performance Metrics
- **First Contentful Paint**: < 1.5s
- **Largest Contentful Paint**: < 2.5s
- **Time to Interactive**: < 3.5s
- **Cumulative Layout Shift**: < 0.1

#### Database Performance Metrics
- **Query Response Time**: < 50ms average
- **Connection Pool Usage**: < 80% utilization
- **Slow Query Detection**: > 1s execution time
- **Replication Lag**: < 100ms (if applicable)

## Security Configuration

### SSL/TLS Configuration
```bash
# Heroku automatically provides SSL
# Vercel provides automatic HTTPS

# Force HTTPS redirects in application
# src/main.py
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware

if not Config.DEVELOPMENT_MODE:
    app.add_middleware(HTTPSRedirectMiddleware)
```

### CORS Configuration
```python
# src/main.py - Production CORS settings
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://wingmanapp.com",
        "https://www.wingmanapp.com",
        "https://wingman-staging.vercel.app"
    ] if not Config.DEVELOPMENT_MODE else ["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"]
)
```

### Rate Limiting Configuration
```python
# Production rate limits
RATE_LIMITS = {
    "assessment": "10/minute",
    "matching": "5/minute", 
    "chat": "60/minute",
    "auth": "20/minute"
}
```

### Environment Security
```bash
# Secure environment variable management
# Never commit secrets to version control
# Use Heroku Config Vars / Vercel Environment Variables
# Rotate API keys regularly
# Monitor for credential leaks
```

## Backup and Recovery

### Database Backup Strategy
```bash
# Automated backups via Supabase
# Point-in-time recovery available
# Manual backup creation
supabase db dump --linked --file backup_$(date +%Y%m%d_%H%M%S).sql

# Restore from backup
supabase db reset --linked
psql -h db.supabase.co -p 5432 -U postgres -d postgres < backup_file.sql
```

### Application Backup
```bash
# Code backup via Git
git push origin main
git tag v1.0.$(date +%Y%m%d)

# Configuration backup
heroku config --app wingman-production > config_backup_$(date +%Y%m%d).txt
```

### Disaster Recovery Plan
1. **Database Corruption**: Restore from latest Supabase backup
2. **Application Outage**: Deploy previous known-good version
3. **API Service Down**: Activate maintenance mode, redirect traffic
4. **Complete Failure**: Restore from backups, communicate with users

## Scaling Configuration

### Backend Scaling (Heroku)
```bash
# Scale web dynos
heroku ps:scale web=2 --app wingman-production

# Scale worker dynos (if background tasks)
heroku ps:scale worker=1 --app wingman-production

# Auto-scaling configuration
heroku addons:create autoscale:standard --app wingman-production
heroku autoscale:enable web --app wingman-production
heroku autoscale:range web 1:5 --app wingman-production
```

### Database Scaling (Supabase)
```bash
# Upgrade Supabase plan for more resources
# Enable read replicas for read-heavy workloads
# Implement connection pooling
# Add database indexes for performance
```

### Frontend Scaling (Vercel)
```bash
# Vercel scales automatically
# Configure CDN settings for static assets
# Enable compression and caching headers
# Implement service worker for offline functionality
```

## Troubleshooting

### Common Issues

#### Database Connection Issues
```bash
# Check environment variables
heroku config --app wingman-production | grep SUPABASE

# Test database connectivity
heroku run python -c "from src.database import get_db_service; print(get_db_service().table('user_profiles').select('id').limit(1).execute())" --app wingman-production
```

#### Authentication Problems
```bash
# Verify Supabase configuration
# Check JWT token validation
# Review RLS policies
# Test auth endpoints manually
```

#### Performance Issues
```bash
# Check application metrics
heroku metrics --app wingman-production

# Review slow queries
# Monitor Redis cache hit rates
# Analyze Claude API response times
```

#### Deployment Failures
```bash
# Check build logs
heroku logs --tail --app wingman-production

# Verify environment variables
# Test locally with production config
# Roll back to previous deployment if needed
heroku rollback v123 --app wingman-production
```

### Monitoring Commands
```bash
# Real-time logs
heroku logs --tail --app wingman-production

# Application metrics
heroku metrics --app wingman-production

# Database performance
supabase logs --linked

# Health check automation
curl -f https://wingman-api.herokuapp.com/api/health || echo "Health check failed"
```

## Maintenance Procedures

### Regular Maintenance Tasks
- **Weekly**: Review error logs and performance metrics
- **Monthly**: Update dependencies and security patches
- **Quarterly**: Review and rotate API keys
- **Annually**: Conduct full security audit

### Planned Maintenance
```bash
# 1. Notify users of maintenance window
# 2. Deploy to staging and test
# 3. Create database backup
# 4. Deploy to production during low-traffic period
# 5. Monitor deployment and rollback if issues
# 6. Update status page when complete
```

---

*This deployment guide is maintained by the DevOps team. For questions or issues, please contact the development team or create a support ticket.*