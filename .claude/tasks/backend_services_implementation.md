# Backend Services Implementation Plan - WingmanMatch

## Mission
Implement the remaining backend services for WingmanMatch following exact task specifications: Supabase client factory, Redis connection pool, Resend email service, rate limiter, and retry policies.

## Task Analysis

**Current State:**
- FastAPI backend with basic structure exists in `/Applications/wingman/src/`
- Requirements.txt already includes redis, resend dependencies
- Basic email service and rate limiter modules already exist but need enhancement
- Need to implement: database client factory, Redis session management, email templates, rate limiting improvements, retry utilities

**Task Requirements:**
1. **Database Client Factory** (`src/database.py`) - Centralized Supabase client management
2. **Redis Session Management** (`src/redis_session.py`) - Redis connection pool with health checks
3. **Email Templates Service** (`src/email_templates.py`) - Resend integration with match templates
4. **Rate Limiter Enhancement** (`src/rate_limiting.py`) - Token bucket algorithm with Redis persistence
5. **Retry Utilities** (`src/retry_utils.py`) - Exponential backoff for IO operations
6. **Requirements Update** - Add tenacity for retry policies

## Implementation Plan

### Phase 1: Database Client Factory (`src/database.py`)
- **Purpose**: Centralize Supabase client creation with service/anon role separation
- **Features**:
  - Service role client for server routes (admin operations)
  - Anonymous client for edge functions (user operations)
  - Connection pooling and error handling
  - Client caching and reuse
- **Integration**: Replace direct supabase client usage in main.py

### Phase 2: Redis Session Management (`src/redis_session.py`)
- **Purpose**: Redis connection pool with health monitoring
- **Features**:
  - Connection pool configuration
  - Health ping functionality
  - Session data management utilities
  - Graceful fallback when Redis unavailable
  - Memory fallback for development
- **Integration**: Replace current redis_client.py with enhanced version

### Phase 3: Email Templates (`src/email_templates.py`)
- **Purpose**: Resend email service with match-specific templates
- **Features**:
  - Match invitation email template
  - Match acceptance/decline templates
  - Template variables and styling
  - Error handling and retry logic
- **Integration**: Extend current email_service.py functionality

### Phase 4: Rate Limiter Enhancement (`src/rate_limiting.py`)
- **Purpose**: Token bucket algorithm with Redis persistence
- **Features**:
  - Token bucket implementation
  - Redis-backed persistence
  - Public endpoint protection
  - Multiple limit types (per-user, per-IP, global)
- **Integration**: Enhance existing rate_limiter.py

### Phase 5: Retry Utilities (`src/retry_utils.py`)
- **Purpose**: Exponential backoff for IO operations
- **Features**:
  - Retry decorators for different operation types
  - Exponential backoff with jitter
  - Circuit breaker pattern
  - Specific policies for email, database, external APIs
- **Integration**: Use throughout codebase for resilience

### Phase 6: Requirements & Integration
- **Update requirements.txt** with tenacity
- **Update main.py** to use new services
- **Testing** of all integrated services

## Technical Implementation Details

### Database Client Patterns
```python
# Service role for admin operations
service_client = get_service_client()

# Anonymous role for user operations  
anon_client = get_anon_client()

# Automatic role selection based on operation type
client = get_client_for_operation(operation_type)
```

### Redis Session Architecture
```python
# Connection pool with health monitoring
redis_pool = create_connection_pool()

# Session management utilities
await redis_session.store_user_session(user_id, session_data)
session_data = await redis_session.get_user_session(user_id)

# Graceful fallback to memory when Redis unavailable
```

### Email Template System
```python
# Match-specific templates
await send_match_invitation(user_email, wingman_data)
await send_match_acceptance(user_email, match_data)
await send_match_decline(user_email, reason)

# Template variables and styling
template_vars = {
    'user_name': user.name,
    'wingman_name': wingman.name,
    'challenge_type': challenge.type
}
```

### Token Bucket Rate Limiter
```python
# Redis-backed token bucket
bucket = await rate_limiter.get_bucket(user_id, limit_type)
allowed = await bucket.consume_tokens(request_cost)

# Multiple limit types
limits = {
    'per_user': {'requests': 100, 'window': 3600},
    'per_ip': {'requests': 1000, 'window': 3600},
    'global': {'requests': 10000, 'window': 60}
}
```

### Retry Policy Patterns
```python
# Database operations
@with_supabase_retry()
async def create_user_record():
    pass

# Email operations
@with_email_retry()
async def send_notification():
    pass

# External API calls
@with_api_retry()
async def call_external_service():
    pass
```

## Quality Assurance

### Testing Strategy
- Unit tests for each service module
- Integration tests with actual Redis/Supabase
- Email template validation
- Rate limiting performance tests
- Retry policy edge case testing

### Error Handling
- Graceful degradation when services unavailable
- Comprehensive logging for debugging
- User-friendly error messages
- Service health monitoring

### Performance Considerations
- Connection pooling for Redis
- Client caching for Supabase
- Efficient token bucket algorithms
- Minimal retry overhead

## Dependencies

### New Dependencies (requirements.txt)
```
tenacity==8.2.3  # For retry policies
```

### Existing Dependencies (already in requirements.txt)
- redis==5.0.1 (Redis client)
- resend==0.6.0 (Email service)
- supabase==2.0.2 (Database client)

## Success Criteria

1. **Database Factory**: Centralized client management with role separation
2. **Redis Sessions**: Connection pool with health monitoring and fallback
3. **Email Templates**: Match-specific templates with error handling
4. **Rate Limiting**: Token bucket algorithm with Redis persistence
5. **Retry Policies**: Exponential backoff for all IO operations
6. **Integration**: All services working together in main.py
7. **Testing**: Comprehensive test coverage for new functionality

## Implementation Order

1. `src/database.py` - Foundation for other services
2. `src/redis_session.py` - Required for rate limiting
3. `src/retry_utils.py` - Required for email and database operations
4. `src/email_templates.py` - Builds on retry utilities
5. `src/rate_limiting.py` - Uses Redis sessions and retry utilities
6. Update `requirements.txt` with tenacity
7. Integration testing and main.py updates

This plan creates a robust, production-ready backend infrastructure for WingmanMatch with proper separation of concerns, error handling, and performance optimization.