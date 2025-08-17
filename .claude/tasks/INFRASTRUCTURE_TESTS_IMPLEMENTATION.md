# Infrastructure Tests Implementation Plan

## Objective
Create a comprehensive infrastructure test module that validates all foundational components of the WingmanMatch platform including database connections, Redis functionality, email service, environment configuration, and security policies.

## Technical Analysis
Based on examination of the codebase:
- **Database**: Supabase PostgreSQL with `database.py` factory pattern
- **Redis**: Async Redis client with fallback in `redis_client.py` 
- **Email**: Resend API service in `email_service.py`
- **Configuration**: Environment variables managed in `config.py`
- **Rate Limiting**: Token bucket with Redis backend in `rate_limiter.py`

## Implementation Plan

### 1. Core Infrastructure Test Class
- **File**: `/Applications/wingman/tests/system_health/infrastructure.py`
- **Class**: `InfrastructureTests` with async methods
- **Pattern**: Following existing test patterns from `test_matcher_service.py`

### 2. Test Categories

#### A. Database Connection Tests
- Supabase service and anon client connectivity
- Basic query execution validation
- Connection pool health checks

#### B. Database Schema Tests
- Table existence verification for core tables:
  - `user_profiles`, `wingman_matches`, `chat_messages`, `wingman_sessions`
  - `approach_challenges`, `confidence_test_results`, `user_locations`
- Schema structure validation
- Foreign key constraints verification

#### C. RLS (Row Level Security) Tests
- Policy existence verification
- User isolation enforcement testing
- Security policy activation status

#### D. Redis Connection Tests
- Redis connectivity and health checks
- Token bucket functionality for rate limiting
- Cache operations (set/get/delete)
- Fallback mode validation

#### E. Email Service Tests
- Resend API configuration validation
- Connection testing (without sending)
- Template availability verification
- Fallback mode testing

#### F. Environment Configuration Tests
- Required environment variables presence
- Configuration object initialization
- Feature flags validation
- Database URL and API key validation

### 3. Test Method Structure
Each test method will return a standardized result dictionary:
```python
{
    "success": bool,
    "message": str,
    "details": dict,
    "error": str | None
}
```

### 4. Implementation Details

#### Dependencies
- Import existing modules: `database.py`, `redis_client.py`, `email_service.py`, `config.py`
- Use async/await patterns consistent with codebase
- Leverage existing factory patterns and service instances

#### Error Handling
- Comprehensive exception catching
- Detailed error reporting for troubleshooting
- Graceful degradation testing
- Timeout handling for network operations

#### Security Considerations
- Test mode operations only (no data modification)
- RLS policy validation without bypassing security
- API key validation without exposing secrets
- Safe connection testing

### 5. Test Execution Patterns
- Individual test methods for each component
- Batch testing capabilities
- Health check summary functionality
- Performance baseline establishment

## Implementation Steps

1. **Create base infrastructure test class**
2. **Implement database connection tests**
3. **Add schema validation tests**
4. **Implement RLS policy tests**
5. **Add Redis connectivity tests**
6. **Implement email service tests**
7. **Add environment configuration tests**
8. **Create comprehensive health check method**
9. **Add performance benchmarking**
10. **Document usage and integration**

## Integration Points
- **Memory Bank Updates**: Document infrastructure testing capabilities
- **CI/CD Integration**: Suitable for automated deployment validation
- **Monitoring Integration**: Can be used for production health checks
- **Development Workflow**: Pre-deployment infrastructure validation

## Success Criteria
- All foundational infrastructure components tested
- Detailed error reporting for troubleshooting
- Async operation support
- Production-safe testing (no side effects)
- Comprehensive schema and security validation
- Redis and email service fallback testing
- Environment configuration validation

## Architecture Alignment
- Follows existing async patterns from codebase
- Uses established factory patterns for database connections
- Leverages existing service instances (redis_service, email_service)
- Consistent with current error handling approaches
- Maintains security-first design principles