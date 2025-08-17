# Test Authentication Endpoint Implementation Plan

## Objective
Create a test authentication endpoint for integration testing that allows Playwright tests to quickly authenticate users without going through the full magic link flow.

## Problem Analysis
- Current authentication uses Supabase magic link flow
- Integration tests need fast, reliable authentication
- localStorage mocking isn't working properly with Supabase client
- Need development-only endpoint that bypasses production auth flow

## Implementation Plan

### 1. Backend Test Auth Endpoint (`/auth/test-login`)
**Location**: `src/main.py`
**Features**:
- Accept email parameter
- Create valid Supabase session for test user
- Generate JWT token that works with frontend auth context
- Only enabled in development environment
- Security checks to prevent production use

**Request Model**:
```python
class TestAuthRequest(BaseModel):
    email: str = Field(..., description="Email for test user authentication")
    create_user: bool = Field(True, description="Create user if doesn't exist")
```

**Response Model**:
```python
class TestAuthResponse(BaseModel):
    success: bool
    access_token: str
    refresh_token: str
    user_id: str
    session_expires_at: str
    message: str
```

### 2. Frontend Test Helper
**Location**: `lib/test-auth.ts`
**Features**:
- Function to authenticate via test endpoint
- Set session in Supabase client
- Compatible with existing auth context
- Handle token storage

### 3. Playwright Test Integration
**Features**:
- Utility function for test authentication
- Persistent session across test scenarios
- Cleanup after tests

## Security Considerations
- Environment check: only available when `DEVELOPMENT_MODE=true`
- Rate limiting for test endpoint
- Clear warning logs when test auth is used
- No production database modification

## Technical Details

### Backend Implementation
1. Add test auth endpoint with environment protection
2. Use Supabase Admin client to create sessions
3. Return tokens compatible with frontend auth context
4. Implement user creation if needed

### Frontend Integration
1. Create test auth helper function
2. Set session in Supabase client state
3. Trigger auth context update
4. Handle localStorage session storage

### Test Usage
```typescript
// In Playwright tests
await testLogin('test@example.com');
// User is now authenticated for subsequent API calls
```

## Success Criteria
- ✅ Test users can be authenticated quickly (<1 second)
- ✅ Authentication works with existing auth context
- ✅ Protected routes become accessible in tests
- ✅ Only available in development environment
- ✅ Compatible with Playwright browser automation
- ✅ No impact on production security

## Files to Create/Modify
1. `src/main.py` - Add test auth endpoint
2. `lib/test-auth.ts` - Frontend test helper
3. `tests/e2e/auth-helper.ts` - Playwright utilities
4. Update `src/config.py` - Add test auth feature flag

## Environment Variables
```
ENABLE_TEST_AUTH=true  # Only in development
DEVELOPMENT_MODE=true  # Required for test auth
```