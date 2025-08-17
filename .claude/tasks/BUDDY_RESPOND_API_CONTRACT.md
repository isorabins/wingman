# POST /api/buddy/respond API Contract Design

## Task Overview
Design the API contract for handling user responses to buddy match requests, following the exact patterns found in the Wingman codebase.

## Existing Patterns Analysis

### 1. Pydantic Model Patterns
From analyzing `src/main.py`, the codebase uses consistent patterns:
- Field descriptions with ellipsis (...) for required fields
- Optional fields with default values
- Clear descriptive naming
- Response models with `success`, `message`, and `data` structure

### 2. Database Schema
From `src/services/wingman_matcher.py` and schema analysis:
- `wingman_matches` table structure:
  - `id` (UUID primary key)
  - `user1_id`, `user2_id` (deterministic ordering: user1_id < user2_id)
  - `status` (pending, accepted, declined, expired)
  - `user1_reputation`, `user2_reputation` (integers)
  - `created_at`, `updated_at` (timestamps)

### 3. Response Format Pattern
Consistent format across all endpoints:
```python
{
    "success": bool,
    "message": str,
    "data": Optional[Dict] = None
}
```

### 4. Error Handling Pattern
- HTTPException with appropriate status codes
- Descriptive error messages
- Logging with context information

## API Contract Design

### 1. Request Model

```python
class MatchResponseRequest(BaseModel):
    """Request model for responding to buddy match"""
    user_id: str = Field(..., description="User ID responding to the match")
    match_id: str = Field(..., description="ID of the wingman match to respond to")
    action: str = Field(..., description="User action: 'accept' or 'decline'", pattern="^(accept|decline)$")
```

### 2. Response Model

```python
class MatchResponseResponse(BaseModel):
    """Response model for buddy match response"""
    success: bool = Field(..., description="Whether the response was processed successfully")
    message: str = Field(..., description="Success or error message")
    match_status: Optional[str] = Field(None, description="Current status of the match after response")
    next_match: Optional[Dict[str, Any]] = Field(None, description="Next available match if declined")
```

### 3. API Endpoint Signature

```python
@app.post("/api/buddy/respond", response_model=MatchResponseResponse)
async def respond_to_buddy_match(request: MatchResponseRequest):
    """
    Respond to a buddy match request with accept or decline
    
    Features:
    - Validates match_id and user participation
    - Updates match status based on user action
    - Returns next match immediately on decline
    - Handles state machine transitions properly
    
    State Transitions:
    - pending + accept by either user → accepted
    - pending + decline by either user → declined  
    - accepted (no further transitions)
    - declined (no further transitions)
    
    Request Body:
    - user_id: User responding to the match
    - match_id: ID of the wingman match
    - action: "accept" or "decline"
    
    Response:
    - success: Whether operation completed successfully
    - message: Descriptive message about the outcome
    - match_status: Current status after the response
    - next_match: Available match if user declined (auto-match behavior)
    """
```

### 4. Response Status Codes

- **200 OK**: Successful response processing
- **400 Bad Request**: Invalid request data (invalid action, malformed IDs)
- **403 Forbidden**: User is not a participant in the match
- **404 Not Found**: Match not found or already resolved
- **500 Internal Server Error**: Database or system error

### 5. State Machine Specification

```python
# Valid status transitions
STATUS_TRANSITIONS = {
    'pending': ['accepted', 'declined'],
    'accepted': [],  # Terminal state
    'declined': [],  # Terminal state
    'expired': []    # Terminal state
}

# Action to status mapping for pending matches
ACTION_TO_STATUS = {
    'accept': 'accepted',
    'decline': 'declined'
}
```

## Implementation Logic Flow

### 1. Validation Phase
1. Validate request data (user_id, match_id, action)
2. Verify match exists and is in 'pending' status
3. Confirm user is a participant (user1_id or user2_id)
4. Check match hasn't already been resolved

### 2. State Update Phase
1. Update match status based on action
2. Record which user responded
3. Update timestamps appropriately

### 3. Response Phase
1. For ACCEPT: Return success with match_status="accepted"
2. For DECLINE: 
   - Return success with match_status="declined"
   - Immediately trigger auto-match for next buddy
   - Include next_match in response if available

### 4. Auto-Match on Decline
Following task requirements, when a user declines:
```python
if request.action == "decline":
    # Find next match using existing WingmanMatcher
    from src.services.wingman_matcher import WingmanMatcher
    matcher = WingmanMatcher(db_client)
    next_match_result = await matcher.create_automatic_match(request.user_id)
    
    if next_match_result["success"]:
        next_match = {
            "match_id": next_match_result["match_id"],
            "buddy_user_id": next_match_result["buddy_user_id"],
            "buddy_profile": next_match_result["buddy_profile"]
        }
```

## Error Cases Specification

### 1. Validation Errors (400)
- Invalid action (not "accept" or "decline")
- Malformed UUIDs for user_id or match_id
- Missing required fields

### 2. Authorization Errors (403)
- User is not a participant in the specified match
- User attempting to respond to already resolved match

### 3. Not Found Errors (404)
- Match ID doesn't exist
- Match exists but is expired/deleted

### 4. Business Logic Errors (400)
- Match is not in 'pending' status
- User has already responded to this match

## Database Operations

### 1. Match Validation Query
```sql
SELECT id, user1_id, user2_id, status, created_at 
FROM wingman_matches 
WHERE id = ? AND status = 'pending'
```

### 2. Status Update Query
```sql
UPDATE wingman_matches 
SET status = ?, updated_at = NOW()
WHERE id = ? AND status = 'pending'
```

### 3. User Participation Check
```python
is_participant = (
    match_record['user1_id'] == request.user_id or 
    match_record['user2_id'] == request.user_id
)
```

## Integration with Existing Services

### 1. Use WingmanMatcher for Next Match
- Leverage existing `create_automatic_match` method
- Consistent with established auto-matching behavior
- Maintains throttling and compatibility rules

### 2. Follow SupabaseFactory Pattern
- Use `SupabaseFactory.get_service_client()` for database access
- Consistent with other endpoints in the codebase

### 3. Error Logging Pattern
```python
logger.error(f"Error responding to match {request.match_id} by user {request.user_id}: {str(e)}")
```

## Security Considerations

### 1. User Authorization
- Verify user can only respond to their own matches
- No cross-user manipulation allowed

### 2. Idempotency
- Multiple requests with same parameters should be safe
- Already resolved matches should return appropriate status

### 3. Race Condition Prevention
- Use database transactions for atomic updates
- Check status before updating to prevent double-processing

## Testing Strategy

### 1. Unit Tests
- Test all validation scenarios
- Test state transitions
- Test error handling

### 2. Integration Tests
- Test with real database
- Test auto-match triggering on decline
- Test concurrent response scenarios

### 3. Edge Cases
- Expired matches
- Non-existent matches
- Non-participant users
- Invalid actions

## Summary

This API contract follows the established Wingman codebase patterns exactly:
- Consistent Pydantic models with Field descriptions
- Standard success/message/data response format
- User ID in request body (no auth middleware)
- HTTPException error handling pattern
- Integration with existing WingmanMatcher service
- Simple, focused functionality without over-engineering

The design ensures immediate next match delivery on decline per task requirements while maintaining compatibility with existing auto-matching algorithms and database patterns.