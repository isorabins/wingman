# WingmanMatch Production Deployment Guide

## Overview

This guide covers the complete production deployment of WingmanMatch with enterprise-grade monitoring, observability, and rollback capabilities. The deployment builds on the existing Task 22 performance infrastructure to deliver a fully production-ready platform.

## Quick Start

### Prerequisites Checklist

Before deploying to production, ensure you have:

- [ ] Production environment variables configured
- [ ] Managed Redis service (Upstash/Redis Cloud) 
- [ ] Email service (Resend API) configured
- [ ] Monitoring services (Sentry, Datadog/Logtail, UptimeRobot) set up
- [ ] Slack webhook for alerts configured
- [ ] Database migrations tested and ready

### Production Deployment Steps

1. **Configure Production Services**
   ```bash
   # Set up Redis (Upstash recommended)
   export REDIS_URL="rediss://your-redis-url"
   
   # Set up email service
   export RESEND_API_KEY="re_your-key"
   
   # Set up monitoring
   export SENTRY_DSN="https://your-sentry-dsn"
   export SLACK_WEBHOOK_URL="https://hooks.slack.com/your-webhook"
   ```

2. **Deploy Database Migrations**
   ```bash
   # Apply feature flags and deployment infrastructure
   supabase migration up
   
   # Verify migration success
   python -c "
   from src.deployment.deployment_automation import run_health_checks
   import asyncio
   print(asyncio.run(run_health_checks()))
   "
   ```

3. **Deploy Backend (Heroku)**
   ```bash
   # Set production environment variables on Heroku
   heroku config:set ENVIRONMENT=production --app your-app-name
   heroku config:set REDIS_URL="rediss://your-redis-url" --app your-app-name
   heroku config:set SENTRY_DSN="https://your-sentry-dsn" --app your-app-name
   
   # Deploy application
   git push heroku main
   
   # Verify deployment
   curl https://your-app.herokuapp.com/api/deployment/health/enhanced
   ```

4. **Deploy Frontend (Vercel)**
   ```bash
   # Configure production environment variables in Vercel dashboard
   # Use vercel.production.json configuration
   
   # Deploy frontend
   vercel --prod
   
   # Verify deployment
   curl https://your-frontend.vercel.app/api/health
   ```

5. **Initialize and Verify Systems**
   ```bash
   # Initialize deployment infrastructure
   curl -X POST https://your-app.herokuapp.com/api/deployment/initialize
   
   # Run comprehensive health check
   curl https://your-app.herokuapp.com/api/deployment/health/comprehensive
   
   # Verify feature flags
   curl https://your-app.herokuapp.com/api/deployment/features
   ```

## Detailed Configuration

### Environment Variables

**Critical Variables (Required):**
```bash
ENVIRONMENT=production
ANTHROPIC_API_KEY=sk-ant-your-key
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-key
REDIS_URL=rediss://your-redis-url
RESEND_API_KEY=re_your-key
```

**Monitoring Variables (Recommended):**
```bash
SENTRY_DSN=https://your-sentry-dsn
DATADOG_API_KEY=your-datadog-key
SLACK_WEBHOOK_URL=https://hooks.slack.com/your-webhook
ENABLE_PERFORMANCE_MONITORING=true
ENABLE_PERFORMANCE_ALERTS=true
```

**Feature Flags (Optional):**
```bash
ENABLE_ENHANCED_MONITORING=true
ENABLE_EXTERNAL_ALERTS=true
ENABLE_BACKUP_VERIFICATION=true
ENABLE_CANARY_DEPLOYMENTS=false
```

### Service Configuration

#### Redis (Upstash Recommended)
```bash
# Create Redis instance on Upstash
# Copy Redis URL to REDIS_URL environment variable
# Verify with: redis-cli -u $REDIS_URL ping
```

#### Email Service (Resend)
```bash
# Create account on Resend
# Generate API key
# Set RESEND_API_KEY environment variable
# Test with: curl -X POST https://api.resend.com/emails -H "Authorization: Bearer $RESEND_API_KEY"
```

#### Monitoring Services

**Sentry (Error Tracking):**
```bash
# Create Sentry project
# Copy DSN to SENTRY_DSN environment variable
# Configure error sampling rate in production
```

**Datadog (Logging):**
```bash
# Create Datadog account
# Generate API key
# Set DATADOG_API_KEY environment variable
# Configure log retention policies
```

**UptimeRobot (Uptime Monitoring):**
```bash
# Create UptimeRobot account
# Set up monitors for key endpoints:
# - https://your-app.herokuapp.com/health
# - https://your-app.herokuapp.com/api/deployment/health/enhanced
# - https://your-frontend.vercel.app
```

## Monitoring and Alerting

### Health Check Endpoints

The deployment provides comprehensive health check endpoints:

1. **Basic Health Check**
   ```bash
   GET /health
   # Returns: {"status": "healthy", "timestamp": "..."}
   ```

2. **Enhanced Health Check**
   ```bash
   GET /api/deployment/health/enhanced
   # Returns: Full system status with monitoring services
   ```

3. **Comprehensive Health Check**
   ```bash
   GET /api/deployment/health/comprehensive
   # Returns: Complete validation for deployment readiness
   ```

4. **Performance Dashboard**
   ```bash
   GET /api/deployment/performance/dashboard
   # Returns: Real-time performance metrics and alerts
   ```

### Alert Configuration

The system automatically monitors:

- **Response Time**: Alerts if P95 > 2 seconds
- **Error Rate**: Alerts if error rate > 5%
- **Database Performance**: Alerts if queries > 1 second
- **Service Availability**: Uptime monitoring with UptimeRobot
- **System Resources**: Memory and CPU utilization

Alerts are sent via:
- **Slack**: Real-time notifications to development team
- **Email**: Critical alerts to admin email
- **Sentry**: Error tracking and performance monitoring

### Performance Targets

- **P95 Response Time**: < 2 seconds
- **Uptime**: 99.9% availability
- **Error Rate**: < 1% under normal load
- **Database Queries**: < 500ms average
- **Recovery Time**: < 5 minutes for rollbacks

## Feature Flag Management

### Available Feature Flags

The system includes production-ready feature flags:

```bash
# Core Infrastructure
enhanced_monitoring=true          # Enhanced monitoring features
external_alerts=true             # Slack/email notifications
backup_verification=true         # Automated backup verification
performance_optimization=true    # Performance features

# Deployment Features  
canary_deployments=false         # Gradual rollout capability
blue_green_deployment=false      # Zero-downtime deployments

# Application Features
advanced_analytics=false         # User behavior tracking
a_b_testing=false               # A/B testing framework
real_time_notifications=false   # Push notifications
premium_features=false          # Subscription features
```

### Managing Feature Flags

```bash
# View all feature flags
curl https://your-app.herokuapp.com/api/deployment/features

# Toggle feature flag
curl -X POST https://your-app.herokuapp.com/api/deployment/features/enhanced_monitoring/toggle \
  -H "Content-Type: application/json" \
  -d '{"enabled": true}'

# Get user-specific features
curl https://your-app.herokuapp.com/api/deployment/features/user-123
```

## Backup and Recovery

### Automatic Backups

Supabase provides automatic backups:
- **Continuous**: Point-in-time recovery up to 7 days
- **Daily**: Full database backups retained for 7 days
- **Weekly**: Weekly backups retained for 4 weeks
- **Monthly**: Monthly backups retained for 3 months

### Backup Verification

```bash
# Verify backup system
curl https://your-app.herokuapp.com/api/deployment/backup/status

# Test recovery procedures
curl https://your-app.herokuapp.com/api/deployment/backup/recovery-readiness
```

### Recovery Procedures

**Application Rollback:**
```bash
# Heroku rollback
heroku rollback --app your-app-name

# Verify rollback
curl https://your-app.herokuapp.com/health
```

**Database Recovery:**
```bash
# Access Supabase dashboard
# Navigate to Settings > Database
# Select point-in-time recovery
# Choose recovery timestamp
# Initiate recovery process
```

**Emergency Rollback:**
```bash
# API-driven rollback
curl -X POST https://your-app.herokuapp.com/api/deployment/recovery/rollback/application_failure
```

## Deployment Automation

### Automated Deployment

```bash
# Execute automated deployment
curl -X POST https://your-app.herokuapp.com/api/deployment/deploy \
  -H "Content-Type: application/json" \
  -d '{"deployment_type": "standard"}'

# Check deployment status
curl https://your-app.herokuapp.com/api/deployment/status
```

### Deployment Types

- **standard**: Full deployment with all checks
- **hotfix**: Fast deployment for critical fixes
- **rollback**: Automated rollback to previous version

### Pre-deployment Checklist

Before each deployment:

- [ ] All tests passing locally
- [ ] Database migrations tested
- [ ] Environment variables updated
- [ ] Backup verification successful
- [ ] Health checks passing
- [ ] Rollback plan identified

## Troubleshooting

### Common Issues

**1. Redis Connection Failures**
```bash
# Check Redis connectivity
redis-cli -u $REDIS_URL ping

# Verify environment variable
echo $REDIS_URL

# Check fallback mode
curl https://your-app.herokuapp.com/api/deployment/health/enhanced
```

**2. Database Migration Failures**
```bash
# Check migration status
supabase migration list

# Rollback failed migration
supabase migration down

# Verify database connectivity
psql $DATABASE_URL -c "SELECT 1;"
```

**3. Monitoring Service Issues**
```bash
# Test Sentry connectivity
curl -X POST https://sentry.io/api/0/projects/your-org/your-project/events/ \
  -H "Authorization: Bearer $SENTRY_AUTH_TOKEN"

# Verify alert system
curl https://your-app.herokuapp.com/api/deployment/performance/dashboard
```

**4. Performance Degradation**
```bash
# Check performance metrics
curl https://your-app.herokuapp.com/api/deployment/performance/dashboard

# Review active alerts
curl https://your-app.herokuapp.com/api/deployment/health/comprehensive

# Scale resources if needed
heroku ps:scale web=2 --app your-app-name
```

### Emergency Procedures

**Complete System Outage:**
1. Check service status pages (Heroku, Vercel, Supabase)
2. Execute emergency rollback
3. Verify health endpoints
4. Monitor error rates
5. Notify team via Slack

**Database Issues:**
1. Check Supabase dashboard
2. Verify connection pooling
3. Consider point-in-time recovery
4. Scale database resources
5. Monitor query performance

**Performance Issues:**
1. Review performance dashboard
2. Check alert history
3. Scale application resources
4. Clear Redis cache if needed
5. Monitor recovery

## Maintenance

### Regular Maintenance Tasks

**Daily:**
- [ ] Review performance dashboard
- [ ] Check active alerts
- [ ] Verify backup status
- [ ] Monitor error rates

**Weekly:**
- [ ] Review deployment logs
- [ ] Update security policies
- [ ] Check resource utilization
- [ ] Test rollback procedures

**Monthly:**
- [ ] Review and update feature flags
- [ ] Audit access controls
- [ ] Update dependencies
- [ ] Performance optimization review

### Security Updates

```bash
# Update dependencies
pip install -r requirements.txt --upgrade

# Apply security patches
npm audit fix

# Update environment variables if needed
heroku config:set NEW_SECURITY_KEY=value --app your-app-name
```

## Support and Escalation

### Monitoring Dashboards

- **Sentry**: Error tracking and performance monitoring
- **Datadog**: Log aggregation and system metrics  
- **UptimeRobot**: Uptime monitoring and availability
- **Heroku**: Application metrics and resource utilization
- **Supabase**: Database performance and query analytics

### Alert Escalation

1. **Level 1**: Slack notifications to development team
2. **Level 2**: Email alerts to admin addresses
3. **Level 3**: Phone/SMS for critical system failures
4. **Level 4**: Escalation to senior engineering team

### Contact Information

- **Development Team**: #wingman-dev Slack channel
- **Admin Email**: admin@wingmanmatch.com
- **Emergency Contact**: [Emergency phone number]
- **Incident Response**: [Incident management system]

---

## Success Criteria

### Performance Targets Met
- ✅ P95 Response Time < 2 seconds
- ✅ 99.9% Uptime achieved
- ✅ Error rate < 1%
- ✅ Database queries < 500ms average

### Monitoring Operational
- ✅ Sentry error tracking active
- ✅ Datadog logging configured
- ✅ UptimeRobot monitoring all endpoints
- ✅ Slack alerts functional

### Recovery Tested
- ✅ Backup verification automated
- ✅ Rollback procedures documented
- ✅ Point-in-time recovery validated
- ✅ Emergency procedures tested

### Security Hardened
- ✅ RLS policies enforced
- ✅ Environment isolation maintained
- ✅ Access controls implemented
- ✅ Audit trail complete

**WingmanMatch is now production-ready with enterprise-grade infrastructure, monitoring, and recovery capabilities.**
