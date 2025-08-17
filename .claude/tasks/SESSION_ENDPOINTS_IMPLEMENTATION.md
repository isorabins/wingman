# Session Endpoints Implementation Plan

## Overview
Implement FastAPI endpoints for session functionality following established patterns to work with Next.js frontend.

## Stack Analysis
- **Backend**: FastAPI with Python, existing patterns in `src/main.py`
- **Database**: Supabase PostgreSQL with `wingman_sessions` table
- **Authentication**: Development patterns from `src/services/auth_service.py`
- **Error Handling**: HTTP exceptions with detailed messages
- **Validation**: Pydantic v2 models with Field constraints

## Database Schema (Confirmed)
`wingman_sessions` table structure:
```sql
- id (UUID, PK)
- match_id (UUID, FK to wingman_matches)
- user1_challenge_id (UUID, FK to approach_challenges)
- user2_challenge_id (UUID, FK to approach_challenges)
- venue_name (VARCHAR(200))
- scheduled_time (TIMESTAMP WITH TIME ZONE)
- status (VARCHAR(50), DEFAULT 'scheduled')
- completed_at (TIMESTAMP WITH TIME ZONE)
- user1_completed_confirmed_by_user2 (BOOLEAN, DEFAULT FALSE)
- user2_completed_confirmed_by_user1 (BOOLEAN, DEFAULT FALSE)
- notes (TEXT)
- created_at (TIMESTAMP WITH TIME ZONE, DEFAULT NOW())
```

## Implementation Plan

### 1. GET /api/session/{session_id} - Fetch Session Details
**Purpose**: Get complete session data including participant info and challenges

**Features**:
- Fetch session with related data (match participants, challenges)
- Calculate reputation preview deltas based on challenge points
- Authenticate and authorize only match participants
- Return structured session data for frontend

**Implementation**:
- Add Pydantic response model `SessionDataResponse`
- Join query to get participant names and challenge details
- Calculate reputation deltas (placeholder logic: ±challenge_points)
- Use existing auth patterns from chat endpoints

### 2. POST /api/session/{session_id}/confirm - Confirm Buddy Completion
**Purpose**: Allow participants to confirm each other completed their challenges

**Features**:
- Only allow confirmation after scheduled_time has passed
- Update appropriate confirmation field (user1_confirmed_by_user2 or user2_confirmed_by_user1)
- Mark session as 'completed' when both sides confirm
- Update completed_at timestamp
- Return updated session status

**Implementation**:
- Add Pydantic request model `SessionConfirmRequest`
- Validate session timing and participant authorization
- Update confirmation fields based on which user is confirming whom
- Transaction-safe updates with proper error handling

### 3. PATCH /api/session/{session_id}/notes - Update Session Notes
**Purpose**: Allow participants to update session notes

**Features**:
- Validate user is session participant
- Update notes field in wingman_sessions table
- Sanitize input for XSS prevention
- Return success confirmation

**Implementation**:
- Add Pydantic request model `SessionNotesRequest`
- Use existing sanitization patterns from profile completion
- Simple update operation with validation

## Technical Decisions

### Authentication Strategy
- Follow existing auth service patterns from chat endpoints
- Use `get_current_user_id()` from `src/services/auth_service.py`
- Support X-Test-User-ID header for development testing
- Validate user is participant in the session

### Authorization Logic
```python
# Check user is participant
participant_ids = [match_data['user1_id'], match_data['user2_id']]
if user_id not in participant_ids:
    raise HTTPException(status_code=403, detail="Access denied")
```

### Reputation Calculation
- Simple logic: ±challenge_points for completion
- Preview only - actual reputation updates happen elsewhere
- Return deltas in response for UI display

### Error Handling
- 401: Authentication required
- 403: Not a session participant
- 404: Session not found
- 400: Business logic violations (timing, already confirmed, etc.)
- 422: Validation errors
- 500: Server errors

### Data Models
```python
class SessionDataResponse(BaseModel):
    id: str
    match_id: str
    venue_name: str
    scheduled_time: datetime
    status: str
    notes: Optional[str]
    participants: SessionParticipants
    reputation_preview: ReputationPreview

class SessionParticipants(BaseModel):
    user1: ParticipantInfo
    user2: ParticipantInfo

class ParticipantInfo(BaseModel):
    id: str
    name: str
    challenge: ChallengeInfo
    confirmed: bool

class ReputationPreview(BaseModel):
    user1_delta: int
    user2_delta: int
```

## File Modifications

### src/main.py (Add new endpoints)
- Import necessary models and utilities
- Add 3 new endpoint functions
- Follow existing patterns for error handling and database operations
- Use established Supabase client patterns

### No new files needed
- All functionality fits within existing FastAPI patterns
- Use existing auth service and database utilities
- Follow established Pydantic model conventions

## Testing Strategy
- Use existing test patterns from session creation tests
- Test authentication and authorization scenarios
- Validate business logic (timing restrictions, confirmation logic)
- Test error conditions and edge cases

## Integration with Frontend
Endpoints designed to match frontend SessionData interface:
- GET returns complete session data structure
- POST confirm returns updated status
- PATCH notes returns success confirmation
- Consistent error response format

## Success Criteria
- All endpoints follow established FastAPI patterns
- Authentication and authorization working correctly
- Business logic properly implemented (timing, confirmations)
- Error handling comprehensive and informative
- Data models match frontend expectations
- No breaking changes to existing functionality