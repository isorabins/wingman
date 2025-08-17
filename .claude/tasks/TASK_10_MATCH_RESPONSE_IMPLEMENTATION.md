# Task 10: Match Response Endpoint and State Machine Implementation Plan

## Project Context
- **Application**: Wingman - Dating confidence assessment and buddy matching app
- **Architecture**: FastAPI backend with Supabase PostgreSQL
- **Current Status**: Tasks 5-9 completed (confidence assessment, profile setup, email service, geolocation, auto-matching)
- **Objective**: Implement POST /api/buddy/respond endpoint for match accept/decline functionality

## Technical Requirements Analysis

### Core Functionality
1. **Match Response Endpoint**: POST /api/buddy/respond
2. **State Machine**: pending → accepted/declined/expired (48h timeout)
3. **Participant Validation**: Ensure caller is authorized to respond to match
4. **Mutual Accept Logic**: Create chat channel and send email notifications
5. **Decline Logic**: Find and return next best match immediately
6. **Auto-Expiration**: Background job for 48-hour timeout handling
7. **Analytics Events**: Emit tracking events for all state transitions
8. **Testing**: TDD approach with comprehensive test coverage

### Existing Patterns to Follow
- FastAPI route structure from `src/main.py`
- Authentication patterns from existing endpoints
- Service class pattern (WingmanMatcher, EmailService)
- Auto-dependency creation for database integrity
- Pydantic models for request/response validation
- BackgroundTasks for async operations

## Implementation Plan

### Phase 1: Codebase Analysis and Pattern Understanding
**Agent: @code-archaeologist**
- [ ] Analyze existing FastAPI route patterns in `src/main.py`
- [ ] Review database schema for matches table structure
- [ ] Examine authentication/authorization patterns
- [ ] Study EmailService implementation for notification patterns
- [ ] Review WingmanMatcher for existing matching logic
- [ ] Document current service architecture patterns

### Phase 2: API Design and Contract Definition
**Agent: @api-architect**
- [ ] Design POST /api/buddy/respond endpoint contract
- [ ] Define Pydantic models for request/response
- [ ] Specify error handling and status codes
- [ ] Plan state machine transitions and validation rules
- [ ] Design analytics event schema
- [ ] Create OpenAPI documentation structure

### Phase 3: Core Implementation
**Agent: @backend-developer**
- [ ] Create `src/services/match_response_service.py`
- [ ] Implement MatchResponseService class
- [ ] Add POST /api/buddy/respond endpoint to FastAPI app
- [ ] Implement participant validation logic
- [ ] Build state machine transition logic
- [ ] Add mutual accept flow with chat channel creation
- [ ] Implement decline flow with next-match finding
- [ ] Integrate email notifications via EmailService
- [ ] Add analytics event emission

### Phase 4: Performance and Database Optimization
**Agent: @performance-optimizer**
- [ ] Optimize database queries for match state updates
- [ ] Implement proper transaction handling
- [ ] Add database indexes for performance
- [ ] Review caching strategies for match data
- [ ] Optimize next-match finding query performance

### Phase 5: Security and Quality Review
**Agent: @code-reviewer**
- [ ] Review authentication and authorization implementation
- [ ] Validate input sanitization and error handling
- [ ] Check for SQL injection and security vulnerabilities
- [ ] Review transaction safety and data consistency
- [ ] Validate idempotency implementation
- [ ] Ensure proper logging and monitoring

### Phase 6: Testing Implementation
**Agent: @backend-developer**
- [ ] Create `tests/backend/test_match_response.py`
- [ ] Implement accept-first scenario tests
- [ ] Implement accept-second (mutual accept) scenario tests
- [ ] Implement decline flow tests
- [ ] Implement unauthorized access tests
- [ ] Add auto-expiration logic tests
- [ ] Create integration tests for email notifications
- [ ] Add analytics event verification tests

### Phase 7: Auto-Expiration Background Job
**Agent: @backend-developer**
- [ ] Create match expiration background job
- [ ] Implement 48-hour timeout logic
- [ ] Add job scheduling mechanism
- [ ] Test expiration scenarios

### Phase 8: Documentation
**Agent: @documentation-specialist**
- [ ] Update API documentation with new endpoint
- [ ] Document state machine transitions
- [ ] Create integration guide for frontend
- [ ] Update deployment notes
- [ ] Document testing procedures

## Technical Implementation Details

### Database Schema Extensions
```sql
-- Add columns to matches table if not present
ALTER TABLE matches ADD COLUMN IF NOT EXISTS user1_response VARCHAR(20) DEFAULT 'pending';
ALTER TABLE matches ADD COLUMN IF NOT EXISTS user2_response VARCHAR(20) DEFAULT 'pending';
ALTER TABLE matches ADD COLUMN IF NOT EXISTS user1_response_at TIMESTAMPTZ;
ALTER TABLE matches ADD COLUMN IF NOT EXISTS user2_response_at TIMESTAMPTZ;
ALTER TABLE matches ADD COLUMN IF NOT EXISTS chat_channel_id UUID;
ALTER TABLE matches ADD COLUMN IF NOT EXISTS expires_at TIMESTAMPTZ DEFAULT (created_at + INTERVAL '48 hours');
```

### API Endpoint Structure
```python
@app.post("/api/buddy/respond")
async def respond_to_match(
    request: MatchResponseRequest,
    current_user: User = Depends(get_current_user),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    # Implementation following existing patterns
```

### Service Class Pattern
```python
class MatchResponseService:
    def __init__(self, db_client, email_service, wingman_matcher):
        # Initialize dependencies
    
    async def respond_to_match(self, match_id, user_id, response, background_tasks):
        # Core logic implementation
```

### State Machine Logic
```
pending + accept → partial_accept (waiting for other user)
partial_accept + accept → accepted (mutual accept - create chat, send emails)
pending/partial_accept + decline → declined (find next match)
pending/partial_accept + 48h timeout → expired
```

## Success Criteria
- [ ] POST /api/buddy/respond endpoint functional
- [ ] All state transitions working correctly
- [ ] Mutual accept creates chat channel and sends emails
- [ ] Decline flow returns next best match
- [ ] Auto-expiration after 48 hours works
- [ ] Comprehensive test coverage (>95%)
- [ ] Security validation passed
- [ ] Performance requirements met (<500ms response time)
- [ ] Analytics events properly emitted
- [ ] Documentation complete

## Risk Mitigation
1. **Database Consistency**: Use transactions for all state updates
2. **Race Conditions**: Implement proper locking mechanisms
3. **Email Failures**: Graceful degradation if email service unavailable
4. **Performance**: Optimize queries and implement caching where needed
5. **Security**: Validate all inputs and ensure proper authorization

## Next Steps After Approval
1. Begin with codebase analysis using @code-archaeologist
2. Design API contract with @api-architect
3. Implement core functionality with @backend-developer
4. Optimize and review with @performance-optimizer and @code-reviewer
5. Complete with documentation using @documentation-specialist

---

*This plan follows the established patterns from the Wingman codebase and ensures a robust, secure, and performant implementation of the match response functionality.*