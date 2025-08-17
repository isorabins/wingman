# POST /api/buddy/respond Endpoint Implementation Plan

## Task Overview
Implement the POST /api/buddy/respond endpoint to handle match responses (accept/decline) following exact patterns from the Wingman codebase.

## Requirements Analysis
- Create POST /api/buddy/respond endpoint in src/main.py
- Validate match_id and user is a participant
- Handle accept/decline with proper state transitions
- On mutual accept: update status to 'accepted'
- On decline: find next match and return it
- Follow existing FastAPI patterns
- Use WingmanMatcher service for finding next matches
- Don't modify reference_files/* - create new code only

## Database Schema Understanding
From analysis:
- wingman_matches table: id, user1_id, user2_id, status, user1_reputation, user2_reputation
- Status values: 'pending', 'accepted', 'declined'
- Users ordered alphabetically (user1_id < user2_id)

## Implementation Plan

### 1. Pydantic Models (Add to src/main.py)
Following existing patterns around line 1440:

```python
class BuddyResponseRequest(BaseModel):
    """Request model for responding to a buddy match"""
    user_id: str = Field(..., description="User ID responding to the match")
    match_id: str = Field(..., description="Match ID being responded to")
    response: str = Field(..., description="Response type", pattern="^(accept|decline)$")

class BuddyResponseResponse(BaseModel):
    """Response model for buddy match response"""
    success: bool = Field(..., description="Whether the response was processed successfully")
    message: str = Field(..., description="Response message")
    match_status: Optional[str] = Field(None, description="Current match status")
    next_match: Optional[Dict[str, Any]] = Field(None, description="Next available match if declined")
```

### 2. Endpoint Implementation
Add after existing buddy matching endpoints around line 1563:

```python
@app.post("/api/buddy/respond", response_model=BuddyResponseResponse)
async def respond_to_buddy_match(request: BuddyResponseRequest):
    """
    Respond to a buddy match request with accept or decline
    
    Features:
    - Validates match exists and user is a participant
    - Handles accept/decline state transitions
    - On mutual accept: updates status to 'accepted'
    - On decline: finds next available match
    - Uses WingmanMatcher service for next match finding
    
    Request Body:
    - user_id: User responding to the match
    - match_id: ID of the match being responded to
    - response: "accept" or "decline"
    
    Response:
    - success: Whether operation completed successfully
    - message: Success or error message
    - match_status: Current status of the match
    - next_match: Next available match (only if declined)
    """
```

### 3. Implementation Logic
1. **Validation Phase**:
   - Validate match exists
   - Validate user is a participant (user1_id or user2_id)
   - Validate match is in 'pending' status

2. **Accept Logic**:
   - If other user already accepted: update to 'accepted'
   - If other user hasn't responded: update user's response field
   - Return appropriate status

3. **Decline Logic**:
   - Update match status to 'declined'
   - Use WingmanMatcher.create_automatic_match() to find next match
   - Return next match in response

4. **Error Handling**:
   - HTTPException for client errors (400, 404)
   - Logger for error logging
   - Consistent response format

### 4. Database Operations Pattern
Following existing patterns:
- Use SupabaseFactory.get_service_client()
- Auto-dependency creation if needed
- Proper error handling and logging
- Atomic operations where possible

### 5. Integration Points
- Use existing WingmanMatcher service from src/services/wingman_matcher.py
- Follow existing endpoint patterns from src/main.py
- Use existing Pydantic model conventions
- Follow existing error handling patterns

## Technical Implementation Details

### Database Field Updates
Need to determine how accept/decline responses are stored:
- Option 1: Use status field transitions (pending → accepted/declined)
- Option 2: Add response fields (user1_response, user2_response)
- Option 3: Create separate responses table

Based on existing code analysis, using status field transitions seems most consistent.

### Next Match Logic
On decline, use existing create_automatic_match:
```python
from src.services.wingman_matcher import WingmanMatcher
matcher = WingmanMatcher(client)
next_match_result = await matcher.create_automatic_match(request.user_id)
```

### Response Format Consistency
Follow existing API response patterns:
- success: bool
- message: str  
- data: Optional[Dict]

## Testing Approach
1. **Unit Tests**: Validate logic with mock data
2. **Integration Tests**: Test with real database
3. **Error Cases**: Invalid match_id, unauthorized user, etc.
4. **State Transitions**: Verify all accept/decline scenarios

## Implementation Sequence
1. Add Pydantic models to src/main.py
2. Implement endpoint handler function
3. Add database validation logic
4. Implement accept/decline logic
5. Integrate WingmanMatcher for next matches
6. Add comprehensive error handling
7. Test all scenarios
8. Update documentation

## Success Criteria
- Endpoint accepts accept/decline responses
- Validates user authorization correctly
- Updates match status appropriately
- Returns next match on decline
- Follows existing code patterns exactly
- Handles all error scenarios gracefully
- Maintains database consistency

This implementation will complete Task 10's match response functionality and enable the full buddy matching flow.