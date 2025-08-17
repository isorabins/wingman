# Session Confirm Completion API Design Plan

## Overview
Design API contract for `POST /api/session/confirm-completion` endpoint that validates session/match membership, toggles confirmation flags, updates session status, and manages reputation.

## Current System Analysis

### Existing Infrastructure
- **Current endpoint**: `POST /api/session/{session_id}/confirm` - confirms buddy completion
- **Database schema**: `wingman_sessions` table with confirmation fields:
  - `user1_completed_confirmed_by_user2` (boolean)
  - `user2_completed_confirmed_by_user1` (boolean)
  - `status` field with values: scheduled, in_progress, completed, cancelled, no_show
  - `completed_at` timestamp
- **Authentication**: Uses auth_service with get_current_user_id and require_authentication
- **RLS policies**: Participant-only access to sessions via match_id relationship

### Business Logic Requirements
1. **Session Membership Validation**: Verify user is participant in the session
2. **Confirmation Toggle**: Update appropriate userX_completed_confirmed_by_userY field
3. **Mutual Completion Detection**: When both confirmations true → set status=completed + completed_at
4. **Reputation Update**: Increment completed_sessions counter for both users
5. **Idempotency**: Handle double-submit scenarios gracefully
6. **Response**: Return both_confirmed and reputation_updated status

## API Design Specification

### Request/Response Models

#### Request Model
```python
class SessionConfirmCompletionRequest(BaseModel):
    """Request model for confirming session completion"""
    session_id: UUID = Field(..., description="UUID of the session to confirm completion")
```

#### Response Model
```python
class SessionConfirmCompletionResponse(BaseModel):
    """Response model for session completion confirmation"""
    success: bool = Field(..., description="Whether completion confirmation was successful")
    message: str = Field(..., description="Success or error message")
    session_status: str = Field(..., description="Updated session status")
    both_confirmed: bool = Field(..., description="Whether both participants have confirmed completion")
    reputation_updated: bool = Field(..., description="Whether reputation was updated for both users")
    user_reputation_delta: int = Field(..., description="Reputation points gained by current user")
```

### HTTP Status Codes
- **200 OK**: Successful completion confirmation
- **400 Bad Request**: Invalid session state, timing issues, or business logic violations
- **401 Unauthorized**: User not authenticated
- **403 Forbidden**: User not authorized to confirm this session
- **404 Not Found**: Session not found
- **409 Conflict**: Session already confirmed by this user (idempotency)
- **422 Unprocessable Entity**: Invalid UUID format
- **500 Internal Server Error**: Database or system errors

### Business Logic Validation

#### Pre-conditions
1. **Authentication Required**: User must be authenticated
2. **Session Exists**: Session ID must exist in database
3. **Participant Validation**: User must be participant in the session (via match relationship)
4. **Session Status**: Session must be 'scheduled' or 'in_progress' (not 'completed', 'cancelled', 'no_show')
5. **Timing Validation**: Session scheduled_time must have passed
6. **Not Self-Confirmation**: User cannot confirm their own completion

#### Processing Logic
1. **Idempotency Check**: If user already confirmed their buddy, return current state
2. **Confirmation Toggle**: Set appropriate userX_completed_confirmed_by_userY = true
3. **Mutual Completion Check**: If both confirmations true → update status + completed_at
4. **Reputation Update**: On mutual completion → increment completed_sessions for both users
5. **Response Generation**: Return confirmation status and reputation update result

### Security Considerations

#### Authentication & Authorization
- **JWT Token Validation**: Use existing auth_service patterns
- **RLS Policy Integration**: Leverage existing participant-only access policies
- **Input Validation**: UUID format validation, SQL injection prevention
- **Rate Limiting**: Consider implementing rate limiting for completion confirmations

#### Data Integrity
- **Transaction Safety**: Use database transactions for atomic updates
- **Idempotency Keys**: Handle duplicate requests gracefully
- **Audit Trail**: Log all completion confirmations for monitoring
- **Rollback Capability**: Ensure reputation updates can be rolled back if needed

### Error Handling Scenarios

#### Business Logic Errors
```python
# Session not found
404: {"detail": "Session not found"}

# User not participant
403: {"detail": "Access denied - user is not a participant in this session"}

# Session not ready for completion
400: {"detail": "Session cannot be completed - current status: cancelled"}

# Timing violation
400: {"detail": "Cannot confirm completion before scheduled time (2025-08-17 15:00 UTC)"}

# Already confirmed (idempotency)
409: {"detail": "You have already confirmed completion for this session"}

# Self-confirmation attempt
400: {"detail": "Cannot confirm your own completion - only your buddy can confirm you"}
```

#### System Errors
```python
# Database errors
500: {"detail": "Failed to update session completion status"}

# Reputation update failure
500: {"detail": "Session completed but reputation update failed"}
```

### Database Operations

#### Reputation Schema Requirements
- Add `completed_sessions` integer field to `user_profiles` table (default 0)
- Create index on `completed_sessions` for analytics queries

#### SQL Operations
```sql
-- 1. Validate session membership and status
SELECT s.*, m.user1_id, m.user2_id 
FROM wingman_sessions s 
JOIN wingman_matches m ON s.match_id = m.id 
WHERE s.id = ? AND (m.user1_id = ? OR m.user2_id = ?)

-- 2. Update confirmation flag (idempotent)
UPDATE wingman_sessions 
SET user1_completed_confirmed_by_user2 = true 
WHERE id = ? AND user1_completed_confirmed_by_user2 = false

-- 3. Check mutual completion and update status
UPDATE wingman_sessions 
SET status = 'completed', completed_at = now() 
WHERE id = ? AND user1_completed_confirmed_by_user2 = true 
  AND user2_completed_confirmed_by_user1 = true 
  AND status != 'completed'

-- 4. Update reputation (atomic)
UPDATE user_profiles 
SET completed_sessions = completed_sessions + 1 
WHERE id IN (?, ?)
```

### Implementation Plan

#### Phase 1: Database Schema Update
1. Add `completed_sessions` field to `user_profiles` table
2. Create migration file with proper indexing
3. Update existing user profiles with default value

#### Phase 2: API Endpoint Implementation
1. Create Pydantic models following existing patterns
2. Implement endpoint with comprehensive validation
3. Add reputation update logic with transaction safety
4. Implement comprehensive error handling

#### Phase 3: Testing & Validation
1. Unit tests for business logic validation
2. Integration tests for database operations
3. Error scenario testing (401, 403, 404, 409, 500)
4. Idempotency testing with duplicate requests
5. Performance testing with reputation updates

#### Phase 4: Documentation & Monitoring
1. API documentation with OpenAPI spec
2. Logging for completion confirmations and reputation updates
3. Metrics for completion rates and reputation distribution
4. Error monitoring for failure scenarios

## Integration Points

### Existing System Compatibility
- **Authentication Service**: Reuse auth_service patterns
- **Database Factory**: Use SupabaseFactory.get_service_client()
- **Error Handling**: Follow established HTTPException patterns
- **Logging**: Use existing logger patterns
- **RLS Policies**: Leverage existing session access policies

### Future Enhancements
- **Reputation Leaderboard**: Use completed_sessions for rankings
- **Achievement System**: Trigger badges based on completion milestones
- **Analytics Dashboard**: Track completion rates and user engagement
- **Notification System**: Send completion confirmations via email/push

## Success Criteria

### Functional Requirements
- ✅ Validates session/match membership correctly
- ✅ Toggles appropriate confirmation flags
- ✅ Updates session status on mutual completion
- ✅ Increments reputation counters accurately
- ✅ Handles idempotency properly
- ✅ Returns comprehensive response data

### Non-Functional Requirements
- ✅ Response time < 500ms for typical operations
- ✅ Atomic database operations with rollback capability
- ✅ Comprehensive error handling with clear messages
- ✅ Security compliance with existing authentication patterns
- ✅ Monitoring and logging for operational visibility

This API design provides a robust, secure, and maintainable solution for session completion confirmation that integrates seamlessly with the existing WingmanMatch architecture.