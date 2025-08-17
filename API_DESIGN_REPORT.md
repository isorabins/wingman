# API Design Report - WingmanMatch Session Management

## Executive Summary

I have designed comprehensive API contracts for the active session page functionality (Task 14) following OpenAPI 3.1 standards and RFC 9457 error handling. The design leverages existing system patterns and provides clean, RESTful endpoints for session management with participant-only access control.

## Spec Files

- **`/Applications/wingman/openapi.yaml`** → 3 core endpoints, comprehensive schemas
- **`/Applications/wingman/api-guidelines.md`** → Implementation patterns and conventions

## Core API Endpoints

### 1. GET /api/session/{session_id}
**Purpose**: Session data retrieval for active session page

**Key Features**:
- Complete session details including participants, challenges, confirmation states
- Reputation preview deltas for each potential action
- 5-minute caching with ETag support for performance
- Participant-only access via existing RLS policies

**Response Example**:
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "participants": {
    "user1": {
      "challenge": {"title": "Start a conversation with someone reading"},
      "completed_confirmed_by_buddy": false
    },
    "user2": {...}
  },
  "can_confirm": {"user1": false, "user2": false},
  "reputation_preview": {"user1_delta": 0, "user2_delta": 0}
}
```

### 2. POST /api/session/{session_id}/confirm
**Purpose**: Buddy completion confirmation

**Business Logic**:
- Disabled until `scheduled_time` passes OR user marked present
- Updates confirmation status and recalculates reputation impact
- Triggers cache invalidation and potential session completion

**Request Example**:
```json
{
  "buddy_user_id": "456e7890-e89b-12d3-a456-426614174001",
  "notes": "Great job! Very confident approach."
}
```

### 3. PATCH /api/session/{session_id}/notes
**Purpose**: Real-time notes management

**Features**:
- Idempotency support for debouncing (`Idempotency-Key` header)
- 2000 character limit with HTML sanitization
- Immediate cache invalidation for real-time updates

## Core Design Decisions

### 1. RESTful Resource Design
- **Choice**: Resource-based URLs (`/api/session/{id}` vs `/api/getSessonData`)
- **Rationale**: Follows REST principles and existing FastAPI patterns in codebase
- **Pattern**: Collections and sub-resources for related operations

### 2. Authentication Strategy
- **Choice**: JWT Bearer tokens via Supabase Auth (existing pattern)
- **Security**: Participant-only access enforced via Row-Level Security policies
- **Implementation**: Leverage existing RLS policies from `wingman_sessions` table

### 3. Error Handling Standard
- **Choice**: RFC 9457 Problem Details for HTTP APIs
- **Format**: `application/problem+json` with structured error objects
- **Benefits**: Consistent, machine-readable error responses with actionable information

**Example Error Response**:
```json
{
  "type": "https://wingmanmatch.com/problems/confirmation-too-early",
  "title": "Confirmation Not Allowed",
  "status": 400,
  "detail": "Confirmation only allowed after scheduled time",
  "scheduled_time": "2025-08-17T15:00:00Z",
  "time_remaining_seconds": 3600
}
```

### 4. Caching Strategy
- **Choice**: Cache-friendly GET operations with 5-minute TTL
- **Implementation**: ETags for conditional requests, Next.js revalidation tags
- **Performance**: `stale-while-revalidate` for better user experience
- **Invalidation**: Immediate cache clearing on mutations

### 5. Validation Approach
- **Choice**: Pydantic v2 models with Field constraints
- **Patterns**: UUID validation, content length limits, enum constraints
- **Security**: Input sanitization and XSS prevention for notes field

## Integration Patterns

### FastAPI Backend
```python
# Pydantic Model Example
class SessionDetailResponse(BaseModel):
    session_id: UUID
    participants: Dict[str, SessionParticipant]
    can_confirm: Dict[str, bool]
    reputation_preview: ReputationPreview
```

### Next.js Frontend
```typescript
// Server Component Pattern
async function getSessionData(id: string) {
  const res = await fetch(`/api/session/${id}`, {
    next: { tags: ['session', `session:${id}`] }
  })
  return res.json()
}

// Cache Invalidation
await revalidateTag(`session:${id}`)
```

## Security Implementation

### Access Control
- **RLS Enforcement**: Existing policies ensure participant-only access
- **Token Validation**: JWT tokens validated against session participants
- **Data Isolation**: No cross-session data leakage possible

### Input Security
- **UUID Validation**: All session IDs validated for format
- **Content Sanitization**: Notes field sanitized for XSS prevention
- **Rate Limiting**: Reasonable limits on all endpoints

## Performance Optimizations

### Caching Layer
- **GET Responses**: 5-minute cache with conditional request support
- **Mutation Responses**: Immediate invalidation with optimistic UI support
- **Headers**: Proper Cache-Control and ETag implementation

### Database Efficiency
- **Indexes**: Leverage existing indexes on `wingman_sessions` table
- **RLS Optimization**: Efficient participant validation queries
- **Minimal Data**: Only fetch required fields for each operation

## Open Questions & Design Considerations

### 1. Presence Detection
**Question**: How should "user marked present" be implemented?
**Options**: 
- A. Separate presence endpoint (`POST /api/session/{id}/presence`)
- B. Extension of confirmation endpoint with presence flag
- C. Automatic presence detection via geolocation

**Recommendation**: Separate presence endpoint for cleaner separation of concerns

### 2. Real-time Updates
**Question**: Should we implement WebSocket for real-time updates?
**Current**: 5-second polling as established in Task 11 chat system
**Consideration**: WebSocket could provide instant updates for confirmation states

### 3. Reputation Calculation
**Question**: Where should reputation logic reside?
**Options**:
- A. Database stored procedures for consistency
- B. FastAPI service layer for flexibility
- C. Separate microservice for scalability

**Recommendation**: FastAPI service layer initially, with clear separation for future extraction

### 4. File Attachments
**Question**: Should notes support file attachments (photos of completed challenges)?
**Current Design**: Text-only notes
**Future Enhancement**: Photo upload similar to profile photos

## Next Steps (for implementers)

### Backend Implementation (FastAPI)
1. **Create Pydantic Models**: Implement request/response schemas in `src/models/session.py`
2. **Add Route Handlers**: Implement endpoints in `src/main.py` following existing patterns
3. **RLS Validation**: Ensure participant access checking in all operations
4. **Cache Headers**: Add ETag and Cache-Control header generation
5. **Error Handling**: Implement RFC 9457 problem+json responses

### Frontend Implementation (Next.js)
1. **Server Components**: Create `/app/session/[id]/page.tsx` for initial data load
2. **Client Components**: Implement interactive elements for confirmations and notes
3. **Cache Integration**: Add revalidation calls after mutations
4. **Error Boundaries**: Handle API errors with proper user feedback
5. **Optimistic UI**: Implement local state for responsive interactions

### Database Migration
1. **RLS Policies**: Verify existing policies cover new access patterns
2. **Indexes**: Add performance indexes if needed for new query patterns
3. **Constraints**: Ensure data integrity for confirmation logic

### Testing Strategy
1. **Unit Tests**: Pydantic models and business logic
2. **Integration Tests**: RLS policy enforcement and cache behavior
3. **E2E Tests**: Complete user journey through confirmation flow

## Implementation Priority

### Phase 1: Core Functionality
- [ ] Session data retrieval endpoint
- [ ] Basic confirmation workflow
- [ ] Notes update functionality

### Phase 2: Performance & UX
- [ ] Caching implementation
- [ ] Optimistic UI updates
- [ ] Error handling refinement

### Phase 3: Enhanced Features
- [ ] Presence detection
- [ ] Real-time updates
- [ ] File attachment support

This API design provides a solid foundation for implementing the active session page functionality while maintaining consistency with existing system patterns and supporting future enhancements.