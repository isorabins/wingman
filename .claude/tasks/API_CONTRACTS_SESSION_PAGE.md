# API Contracts for Active Session Page Functionality - Task 14

## Plan Overview

Based on Task 14 requirements and the existing codebase analysis, I need to design clean RESTful API contracts for the active session page functionality. The system already has:

- Complete database schema with `wingman_sessions` table
- Session creation endpoint (POST /api/session/create) 
- FastAPI backend with Pydantic models and established patterns
- Row-Level Security (RLS) policies for participant-only access
- Email service integration and Redis caching

## Required API Endpoints

### 1. Session Data Retrieval
**GET /api/session/{session_id}**
- Fetch complete session details for the active session page
- Include match participants, challenges, confirmation states, notes, reputation preview
- Implement caching with proper cache tags for Next.js
- Enforce participant-only access via existing RLS policies

### 2. Session Confirmation
**POST /api/session/{session_id}/confirm**
- Allow participants to confirm their buddy completed the challenge
- Validate scheduled_time has passed OR user is marked present
- Update confirmation status and recalculate reputation impact
- Include business logic for completion detection

### 3. Notes Management
**PATCH /api/session/{session_id}/notes**
- Update session notes field with real-time persistence
- Support debouncing from frontend with idempotency
- Validate content length and sanitization

## Design Principles

1. **Consistency**: Follow existing FastAPI patterns from `src/main.py`
2. **Security**: Leverage existing RLS policies for participant-only access
3. **Caching**: Design for Next.js cache-friendly operations
4. **Real-time**: Support optimistic UI with proper state reconciliation
5. **Standards**: OpenAPI 3.1 compliance with comprehensive documentation

## Technical Approach

- **Request/Response Models**: Pydantic v2 with Field constraints and validation
- **Error Handling**: RFC 9457 problem+json format consistent with existing patterns
- **Authentication**: JWT tokens via Supabase Auth (existing pattern)
- **Caching**: Cache-Control headers and Next.js revalidation patterns
- **Validation**: Input sanitization and business rule enforcement

## Implementation Strategy

1. Analyze existing patterns from session creation endpoint
2. Design Pydantic models following established conventions
3. Create OpenAPI specification with proper schemas
4. Include example requests/responses for clarity
5. Document security considerations and cache behavior

## Cache Strategy

- **GET Operations**: 5-minute TTL with revalidation tags
- **Mutation Operations**: Immediate cache invalidation
- **Optimistic UI**: Support local state with server reconciliation

## Next Steps

1. Design complete OpenAPI specification
2. Include comprehensive request/response examples
3. Document authentication and authorization patterns
4. Specify cache behavior and invalidation strategy
5. Provide implementation guidelines for FastAPI backend

This plan ensures the API contracts will integrate seamlessly with the existing FastAPI backend and support both Server and Client Components in the Next.js frontend.