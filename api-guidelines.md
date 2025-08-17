# API Guidelines - WingmanMatch Session Management

## Overview

This document provides implementation guidelines for the WingmanMatch Session Management API, designed for the active session page functionality (Task 14). The API follows REST principles, OpenAPI 3.1 standards, and RFC 9457 for error handling.

## Core Endpoints

### 1. GET /api/session/{session_id}
**Purpose**: Retrieve complete session details for the active session page

**Key Features**:
- Participant-only access via Supabase RLS policies
- 5-minute caching with ETag support
- Comprehensive session data including challenges, confirmation states, reputation preview

**Required Headers**:
```
Authorization: Bearer {jwt_token}
```

**Optional Headers**:
```
If-None-Match: "{etag_value}"  # For conditional requests
```

**Cache Behavior**:
- Response cached for 5 minutes (`max-age=300`)
- Supports `stale-while-revalidate` for better UX
- ETag-based conditional requests
- Cache invalidated on mutations

### 2. POST /api/session/{session_id}/confirm
**Purpose**: Confirm buddy challenge completion

**Business Rules**:
- Only available after `scheduled_time` OR when user marked present
- Updates confirmation status and reputation calculations
- Triggers cache invalidation

**Required Headers**:
```
Authorization: Bearer {jwt_token}
Content-Type: application/json
```

**Request Body**:
```json
{
  "buddy_user_id": "uuid",
  "notes": "Optional performance notes"
}
```

### 3. PATCH /api/session/{session_id}/notes
**Purpose**: Update session notes with real-time persistence

**Features**:
- Supports idempotency via `Idempotency-Key` header
- Content validation (2000 char limit)
- HTML sanitization
- Immediate cache invalidation

**Required Headers**:
```
Authorization: Bearer {jwt_token}
Content-Type: application/json
```

**Optional Headers**:
```
Idempotency-Key: "notes-update-{timestamp}"  # For debouncing
```

## Authentication & Authorization

### JWT Token Requirements
- **Source**: Supabase Auth tokens
- **Format**: `Bearer {token}` in Authorization header
- **Validation**: Token must contain valid `user_id` that matches session participant
- **Scope**: Participant-only access enforced via Row-Level Security

### Access Control Pattern
```sql
-- RLS Policy Example
(SELECT auth.uid()) IN (
    SELECT user1_id FROM wingman_matches WHERE id = match_id
    UNION
    SELECT user2_id FROM wingman_matches WHERE id = match_id
)
```

## Error Handling (RFC 9457)

### Standard Error Format
```json
{
  "type": "https://wingmanmatch.com/problems/{error-type}",
  "title": "Human Readable Error Title",
  "status": 400,
  "detail": "Specific error details for this occurrence",
  "instance": "/api/session/{session_id}",
  // Additional error-specific fields
}
```

### Content Type
```
Content-Type: application/problem+json
```

### Common Error Types

| Status | Type | Description |
|--------|------|-------------|
| 400 | `confirmation-too-early` | Confirmation attempted before scheduled time |
| 400 | `already-confirmed` | Buddy already confirmed |
| 400 | `notes-too-long` | Notes exceed 2000 characters |
| 403 | `access-denied` | User not a session participant |
| 404 | `session-not-found` | Session doesn't exist |
| 422 | `validation-error` | Invalid request data format |

## Caching Strategy

### GET Responses
- **TTL**: 5 minutes (`Cache-Control: public, max-age=300`)
- **Revalidation**: `stale-while-revalidate=60`
- **ETags**: Entity tags for conditional requests
- **Tags**: Next.js cache tags `['session', 'session:{id}']`

### Cache Invalidation
```javascript
// Next.js Route Handler Example
import { revalidateTag, revalidatePath } from 'next/cache'

// After mutation
await revalidateTag(`session:${session_id}`)
await revalidatePath(`/session/${session_id}`)
```

### Headers for Caching
```
# Successful GET Response
Cache-Control: public, max-age=300, stale-while-revalidate=60
ETag: "session-{id}-v{version}"

# POST/PATCH Response
Cache-Control: no-cache
```

## Validation Rules

### Session ID
- **Format**: UUID v4
- **Pattern**: `^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$`

### Notes Field
- **Max Length**: 2000 characters
- **HTML Sanitization**: Strip potentially dangerous HTML
- **Empty Values**: Allowed (clears field)

### Confirmation Rules
- **Timing**: Only after `scheduled_time` OR `present_status = true`
- **Participants**: Only valid participants can confirm
- **Idempotency**: Multiple confirmations of same user are prevented

## Response Patterns

### Success Response Structure
```json
{
  "success": true,
  "message": "Operation completed successfully",
  // Operation-specific data
}
```

### Pagination (Future)
```json
{
  "data": [...],
  "pagination": {
    "cursor": "next_page_token",
    "has_more": true,
    "total_count": 42
  }
}
```

## Integration with FastAPI

### Pydantic Models
```python
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime

class SessionDetailResponse(BaseModel):
    session_id: UUID
    match_id: UUID
    venue_name: str = Field(..., max_length=200)
    scheduled_time: datetime
    # ... other fields
```

### Error Handling
```python
from fastapi import HTTPException

# Custom exception for problem+json
class ProblemDetailException(HTTPException):
    def __init__(self, status_code: int, type_uri: str, title: str, detail: str, **kwargs):
        self.type_uri = type_uri
        self.title = title
        self.detail = detail
        self.extra_fields = kwargs
        super().__init__(status_code=status_code, detail=detail)
```

### Route Implementation Pattern
```python
@app.get("/api/session/{session_id}", response_model=SessionDetailResponse)
async def get_session(
    session_id: UUID,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    # Validate participant access
    # Check cache
    # Fetch data with RLS
    # Return with cache headers
```

## Rate Limiting

### Current Limits
- **GET /api/session/{id}**: 60 requests/minute per user
- **POST /api/session/{id}/confirm**: 10 requests/minute per user  
- **PATCH /api/session/{id}/notes**: 30 requests/minute per user

### Headers
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1692123456
```

## Security Considerations

### Input Validation
- All UUID parameters validated for format
- Notes content sanitized for XSS prevention
- Request size limits enforced

### Access Control
- Participant-only access via RLS policies
- JWT token validation on every request
- No data leakage between different sessions

### Audit Trail
- All confirmations logged with timestamps
- Notes changes tracked with user attribution
- Session state transitions recorded

## Testing Strategy

### Unit Tests
- Pydantic model validation
- Business logic functions
- Error handling scenarios

### Integration Tests
- Database RLS policy enforcement
- Cache behavior validation
- JWT token verification

### E2E Tests
- Complete user confirmation flow
- Notes update with debouncing
- Error response format validation

## Implementation Checklist

### Backend (FastAPI)
- [ ] Implement Pydantic request/response models
- [ ] Add route handlers with proper error handling
- [ ] Implement RLS policy validation
- [ ] Add cache headers and ETag support
- [ ] Configure rate limiting
- [ ] Add comprehensive logging

### Frontend (Next.js)
- [ ] Create Server Component for initial data load
- [ ] Implement Client Components for interactivity
- [ ] Add cache revalidation after mutations
- [ ] Handle error states with proper UX
- [ ] Implement optimistic UI updates
- [ ] Add offline queue for actions

### Database
- [ ] Verify RLS policies are active
- [ ] Add performance indexes
- [ ] Test participant-only access
- [ ] Validate constraint enforcement

This API design ensures scalable, secure, and cache-friendly session management that integrates seamlessly with both FastAPI backend and Next.js frontend patterns.