# WingmanMatch Backend Implementation Guide

## Overview

This document explains how the WingmanMatch backend services were implemented, following patterns from the reference Fridays at Four implementation while being specifically adapted for wingman matching functionality.

## Implementation Summary

### Task 3: Backend config: Supabase, Redis, Resend wiring ✅

**Completion Date**: 2025-08-13
**Status**: All subtasks completed successfully

## Service Architecture

### 1. Database Service (`src/database.py`)

**Implementation Pattern**: Centralized Supabase client factory
- **Service Role Client**: For server-side operations with full database access
- **Anonymous Client**: For edge functions and public operations
- **Health Monitoring**: Automatic connection testing with detailed error reporting

```python
# Usage examples
from src.database import get_db_service, get_db_anon

# Server operations (full access)
service_client = get_db_service()
user = service_client.table('user_profiles').select('*').eq('id', user_id).execute()

# Public operations (RLS enforced)
anon_client = get_db_anon()
challenges = anon_client.table('approach_challenges').select('*').execute()
```

**Reference Patterns Used**:
- Connection management from `reference_files/src/main.py`
- Configuration structure from `reference_files/src/config.py`

### 2. Redis Session Management (`src/redis_session.py`)

**Implementation Pattern**: Connection pool with health monitoring and graceful fallback
- **Connection Pool**: Redis connection pool with 20 max connections
- **Health Checks**: Automatic ping monitoring with timing metrics
- **Graceful Fallback**: Continues operation when Redis unavailable
- **Session Management**: User session storage with TTL

```python
# Usage examples
from src.redis_session import store_user_session, get_user_session

# Store user session (1 hour TTL)
await store_user_session("user123", {"match_preferences": {...}})

# Retrieve user session
session_data = await get_user_session("user123")
```

**Technical Specifications**:
- Redis connection timeout: 5 seconds
- Max connections: 20
- Automatic retry on timeout enabled
- UTF-8 encoding with decoded responses

### 3. Email Service (`src/email_templates.py`)

**Implementation Pattern**: Resend-based transactional email system
- **Match Invitation Templates**: HTML templates for wingman match invitations
- **Match Response Templates**: Acceptance/decline notification emails
- **Session Reminders**: Automated reminder emails for scheduled sessions
- **Error Handling**: Comprehensive logging and graceful failure handling

```python
# Usage examples
from src.email_templates import email_service

# Send match invitation
await email_service.send_match_invitation(
    to_email="user@example.com",
    inviter_name="John",
    venue_suggestion="Central Park"
)

# Send match acceptance
await email_service.send_match_acceptance(
    to_email="inviter@example.com", 
    accepter_name="Jane",
    venue_name="Central Park",
    scheduled_time="Tomorrow at 3 PM"
)
```

**Email Templates Implemented**:
- Match invitation with venue suggestions
- Match acceptance with session details
- Match decline with encouragement
- Session reminders with details

### 4. Rate Limiting (`src/rate_limiting.py`)

**Implementation Pattern**: Token bucket algorithm with Redis persistence
- **Token Bucket Algorithm**: Configurable capacity and refill rates
- **Redis Persistence**: Rate limit state stored in Redis for scalability
- **Endpoint-Specific Limits**: Different limits for different operations
- **Graceful Degradation**: Falls open when Redis unavailable

```python
# Usage examples
from src.rate_limiting import rate_limiter

# Check rate limit for API endpoint
result = await rate_limiter.check_ip_limit("/wingman/request", "192.168.1.1")
if not result["allowed"]:
    # Rate limit exceeded
    retry_after = result["retry_after"]
```

**Configured Limits**:
- Public API: 100 requests, 1 per second refill
- Auth endpoints: 10 requests, 1 per 10 seconds refill  
- Match requests: 5 requests, 1 per 20 seconds refill
- Email sending: 3 requests, 1 per 100 seconds refill
- Challenge submission: 20 requests, 1 per 5 seconds refill

### 5. Retry Policies (`src/retry_utils.py`)

**Implementation Pattern**: Exponential backoff with circuit breaker
- **Exponential Backoff**: Configurable delays with jitter
- **Circuit Breaker**: Automatic service protection during failures
- **Service-Specific Policies**: Different retry strategies per service
- **Comprehensive Logging**: Detailed failure and recovery tracking

```python
# Usage examples
from src.retry_utils import retry_supabase_operation, with_retry

# Automatic retry for database operations
result = await retry_supabase_operation(lambda: db.table('users').select('*').execute())

# Custom retry decorator
@with_retry(max_retries=3, circuit_breaker_key="external_api")
async def call_external_api():
    # API call implementation
    pass
```

**Circuit Breaker Configuration**:
- Supabase: 5 failures → 60 second recovery timeout
- Redis: 3 failures → 30 second recovery timeout  
- Email: 3 failures → 120 second recovery timeout
- External APIs: 5 failures → 60 second recovery timeout

## Configuration Management

### Environment Variables

**Required Variables**:
```bash
ANTHROPIC_API_KEY=sk-ant-api03-...
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key
SUPABASE_ANON_KEY=your-anon-key
```

**Optional Variables**:
```bash
REDIS_URL=redis://localhost:6379
RESEND_API_KEY=re_...
ENABLE_RATE_LIMITING=true
ENABLE_AI_COACHING=true
ENABLE_MATCH_SHARING=true
ENABLE_CHALLENGE_SHARING=true
```

**WingmanMatch-Specific Settings**:
```bash
MAX_DAILY_MATCHES=10
CHALLENGE_DURATION_DAYS=7
SESSION_TIMEOUT_HOURS=24
```

### Health Monitoring

**Comprehensive Health Check**: `/health` endpoint monitors all services
- Database connections (service + anonymous clients)
- Redis connection and performance
- Email service status
- Rate limiter functionality  
- Circuit breaker states

```json
{
  "status": "healthy",
  "timestamp": "2025-08-13T...",
  "environment": "development",
  "services": {
    "database": {"service_client": true, "anon_client": true},
    "redis": {"connected": true, "ping_time": "1.23ms"},
    "email": {"enabled": true},
    "rate_limiter": {"enabled": true, "redis_available": true},
    "circuit_breakers": {"supabase": {"state": "closed"}}
  }
}
```

## Reference Pattern Adaptations

### From Fridays at Four Reference (`reference_files/src/`)

**Patterns Adopted**:
- Configuration class structure and validation
- FastAPI app initialization with lifespan management
- CORS configuration for multiple domains
- Logging setup and structured error handling
- Environment-based feature flags

**Patterns Adapted**:
- Removed Zoom/Slack integrations → Added Redis/rate limiting
- Removed LangChain dependencies → Kept direct Claude API patterns
- Modified email templates → WingmanMatch-specific match notifications
- Updated CORS domains → WingmanMatch domains

**New Implementations** (not in reference):
- Redis session management with connection pooling
- Token bucket rate limiting with Redis persistence
- Circuit breaker pattern for service resilience
- Comprehensive retry policies with exponential backoff
- Match notification email templates

## Testing Strategy

### Service Testing Approach

1. **Infrastructure Verification**: Health checks confirm all services operational
2. **Graceful Degradation**: Services continue operating when dependencies unavailable
3. **Rate Limiting Testing**: Confirmed token bucket algorithm works correctly
4. **Email Testing**: Templates render correctly, sandbox sending works
5. **Circuit Breaker Testing**: Automatic failure detection and recovery

### Testing Commands

```bash
# Health check
curl http://localhost:8000/health

# Rate limit test
for i in {1..15}; do curl http://localhost:8000/some-endpoint; done

# Redis fallback test (stop Redis and check logs)
# Email sandbox test (send to test email addresses)
```

## Deployment Considerations

### Production Requirements

1. **Redis**: Configure Redis instance or Redis Cloud
2. **Environment Variables**: All required variables must be set
3. **Monitoring**: Health check endpoint should be monitored
4. **Rate Limiting**: Consider Redis persistence for rate limit state
5. **Email Templates**: Test all templates in production environment

### Security Notes

- Service role key only used server-side
- Anonymous key used for public operations with RLS
- Rate limiting protects against abuse
- Circuit breakers prevent cascade failures
- All secrets loaded via environment variables only

## Performance Optimizations

1. **Connection Pooling**: Redis connection pool prevents connection overhead
2. **Circuit Breakers**: Prevent wasted calls to failing services  
3. **Graceful Degradation**: Core functionality works even when optional services down
4. **Rate Limiting**: Protects against DoS and abuse
5. **Comprehensive Logging**: Enables quick diagnosis of issues

---

**Implementation completed**: 2025-08-13
**All services integrated**: Database, Redis, Email, Rate Limiting, Retry Policies
**Production ready**: All components include error handling and monitoring