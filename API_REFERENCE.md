# Wingman API Reference

*Last Updated: August 16, 2025 - Includes session management system*

## Base URL
- **Development**: `http://localhost:8000`
- **Production**: `https://wingman-backend.herokuapp.com`

## Authentication
All endpoints require authentication via JWT token in the Authorization header:
```http
Authorization: Bearer {jwt_token}
```

For development testing, you can use the test user header:
```http
X-Test-User-ID: test-user-12345
```

## Response Format

### Success Response
```json
{
  "success": true,
  "data": {...},
  "message": "Operation completed successfully"
}
```

### Error Response
```json
{
  "detail": "Error description",
  "status_code": 400,
  "error_type": "validation_error"
}
```

## Endpoints

### Health Check

#### Get API Health Status
```http
GET /api/health
```

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2025-08-16T10:30:00Z",
  "services": {
    "database": "healthy",
    "redis": "healthy",
    "claude_api": "healthy"
  }
}
```

---

## Authentication

### Sign In with Magic Link
```http
POST /api/auth/signin
Content-Type: application/json

{
  "email": "user@example.com"
}
```

**Response**:
```json
{
  "success": true,
  "message": "Magic link sent to your email"
}
```

### Get Current User
```http
GET /api/auth/user
Authorization: Bearer {jwt_token}
```

**Response**:
```json
{
  "id": "user-uuid",
  "email": "user@example.com",
  "profile_complete": true,
  "created_at": "2025-08-16T10:30:00Z"
}
```

---

## Confidence Assessment

### Start Confidence Test
```http
POST /api/confidence-test/start
Authorization: Bearer {jwt_token}

{
  "user_id": "user-uuid"
}
```

**Response**:
```json
{
  "success": true,
  "session_id": "test-session-uuid",
  "current_question": 1,
  "total_questions": 12,
  "question": {
    "text": "You see an attractive woman at a coffee shop...",
    "options": ["A) Approach immediately", "B) Wait for the right moment", ...]
  }
}
```

### Submit Answer
```http
POST /api/confidence-test/submit-answer
Authorization: Bearer {jwt_token}

{
  "session_id": "test-session-uuid",
  "question_number": 1,
  "selected_option": "A"
}
```

**Response**:
```json
{
  "success": true,
  "question_number": 2,
  "completed": false,
  "next_question": {...}
}
```

### Get Test Results
```http
GET /api/confidence-test/results/{user_id}
Authorization: Bearer {jwt_token}
```

**Response**:
```json
{
  "archetype": "Analyzer",
  "experience_level": "Intermediate",
  "confidence_score": 72,
  "completed_at": "2025-08-16T10:30:00Z",
  "strengths": ["Thoughtful approach", "Good listener"],
  "growth_areas": ["Initiative taking", "Physical escalation"]
}
```

---

## Profile Management

### Complete Profile Setup
```http
POST /api/profile/complete
Authorization: Bearer {jwt_token}
Content-Type: application/json

{
  "user_id": "user-uuid",
  "first_name": "John",
  "last_name": "Doe",
  "age": 28,
  "bio": "Looking to build genuine confidence...",
  "photo_url": "https://storage.supabase.co/...",
  "location_data": {
    "latitude": 37.7749,
    "longitude": -122.4194,
    "city": "San Francisco",
    "state": "CA",
    "privacy_mode": "precise"
  }
}
```

**Response**:
```json
{
  "success": true,
  "profile_id": "profile-uuid",
  "message": "Profile completed successfully"
}
```

---

## Buddy Matching

### Find Buddy Candidates
```http
GET /api/matches/candidates/{user_id}?radius_miles=25
Authorization: Bearer {jwt_token}
```

**Response**:
```json
{
  "candidates": [
    {
      "user_id": "candidate-uuid",
      "first_name": "Mike",
      "age": 26,
      "bio": "Building confidence through action...",
      "distance_miles": 12.3,
      "experience_level": "Intermediate",
      "archetype": "Sprinter"
    }
  ],
  "total_count": 5
}
```

### Calculate Distance Between Users
```http
GET /api/matches/distance/{user1_id}/{user2_id}
Authorization: Bearer {jwt_token}
```

**Response**:
```json
{
  "distance_miles": 12.3,
  "within_20_miles": true,
  "user1_location": "San Francisco, CA",
  "user2_location": "Oakland, CA"
}
```

### Create Automatic Match
```http
POST /api/matches/auto/{user_id}
Authorization: Bearer {jwt_token}
```

**Response**:
```json
{
  "success": true,
  "match_id": "match-uuid",
  "buddy_user_id": "buddy-uuid",
  "buddy_profile": {
    "first_name": "Alex",
    "age": 27,
    "bio": "Ready to level up together",
    "distance_miles": 8.5
  },
  "message": "Wingman match created successfully"
}
```

### Respond to Match Invitation
```http
POST /api/buddy/respond
Authorization: Bearer {jwt_token}
Content-Type: application/json

{
  "user_id": "user-uuid",
  "match_id": "match-uuid", 
  "action": "accept"
}
```

**Response (Accept)**:
```json
{
  "success": true,
  "match_status": "accepted",
  "message": "Match accepted! You can now start chatting and planning sessions.",
  "next_steps": ["Set up first session", "Start chatting", "Choose challenges"]
}
```

**Response (Decline)**:
```json
{
  "success": true,
  "match_status": "declined", 
  "message": "Match declined. We'll find you another wingman.",
  "next_match": {
    "user_id": "new-candidate-uuid",
    "first_name": "David",
    "distance_miles": 15.2
  }
}
```

---

## Chat System

### Get Chat Messages
```http
GET /api/chat/messages/{match_id}?limit=50&cursor=optional-cursor
Authorization: Bearer {jwt_token}
```

**Response**:
```json
{
  "messages": [
    {
      "id": "message-uuid",
      "sender_id": "user-uuid",
      "message_text": "Hey! Ready for our first session?",
      "created_at": "2025-08-16T10:30:00Z",
      "is_system_message": false
    }
  ],
  "has_more": false,
  "next_cursor": null
}
```

### Send Chat Message
```http
POST /api/chat/send
Authorization: Bearer {jwt_token}
Content-Type: application/json

{
  "match_id": "match-uuid",
  "message": "Looking forward to meeting up!"
}
```

**Response**:
```json
{
  "success": true,
  "message_id": "message-uuid",
  "created_at": "2025-08-16T10:30:00Z",
  "message": "Message sent successfully"
}
```

---

## Session Management

### Create Wingman Session
```http
POST /api/session/create
Authorization: Bearer {jwt_token}
Content-Type: application/json

{
  "match_id": "match-uuid",
  "user1_challenge_id": "challenge-uuid-1",
  "user2_challenge_id": "challenge-uuid-2", 
  "venue_name": "Starbucks on Market Street",
  "time": "2025-08-20T15:00:00Z"
}
```

**Response**:
```json
{
  "success": true,
  "session_id": "session-uuid",
  "message": "Session scheduled successfully at Starbucks on Market Street",
  "scheduled_time": "2025-08-20T15:00:00Z",
  "venue_name": "Starbucks on Market Street",
  "notifications_sent": true
}
```

### Get Sessions for Match
```http
GET /api/sessions/{match_id}
Authorization: Bearer {jwt_token}
```

**Response**:
```json
{
  "sessions": [
    {
      "id": "session-uuid",
      "match_id": "match-uuid",
      "venue_name": "Starbucks on Market Street",
      "scheduled_time": "2025-08-20T15:00:00Z",
      "status": "scheduled",
      "user1_challenge": {
        "id": "challenge-uuid",
        "title": "Coffee Shop Approach",
        "difficulty": "beginner"
      },
      "user2_challenge": {
        "id": "challenge-uuid-2", 
        "title": "Bookstore Conversation",
        "difficulty": "intermediate"
      },
      "created_at": "2025-08-16T10:30:00Z"
    }
  ]
}
```

### Update Session Status
```http
POST /api/sessions/{session_id}/status
Authorization: Bearer {jwt_token}
Content-Type: application/json

{
  "status": "in_progress",
  "notes": "Both users checked in, starting challenges"
}
```

**Response**:
```json
{
  "success": true,
  "session_id": "session-uuid",
  "status": "in_progress",
  "message": "Session status updated successfully"
}
```

---

## Challenges Catalog

### Get All Challenges
```http
GET /api/challenges
Authorization: Bearer {jwt_token}
```

**Response**:
```json
{
  "challenges": [
    {
      "id": "challenge-uuid",
      "title": "Coffee Shop Approach",
      "description": "Strike up a natural conversation with someone at a coffee shop",
      "difficulty": "beginner",
      "estimated_time_minutes": 30,
      "points": 10,
      "category": "social_approach"
    }
  ],
  "count": 9,
  "difficulty_filter": null
}
```

### Get Challenges by Difficulty
```http
GET /api/challenges?difficulty=beginner
Authorization: Bearer {jwt_token}
```

**Response**:
```json
{
  "challenges": [
    {
      "id": "challenge-uuid-1",
      "title": "Coffee Shop Approach", 
      "difficulty": "beginner",
      "points": 10
    },
    {
      "id": "challenge-uuid-2",
      "title": "Bookstore Browse",
      "difficulty": "beginner", 
      "points": 15
    }
  ],
  "count": 3,
  "difficulty_filter": "beginner"
}
```

### Invalidate Challenges Cache (Admin)
```http
POST /api/challenges/cache/invalidate
Authorization: Bearer {jwt_token}
```

**Response**:
```json
{
  "success": true,
  "message": "Challenges cache invalidated successfully"
}
```

---

## Error Codes

| Status Code | Error Type | Description |
|-------------|------------|-------------|
| 400 | Bad Request | Invalid request data or parameters |
| 401 | Unauthorized | Missing or invalid authentication |
| 403 | Forbidden | User not authorized for this operation |
| 404 | Not Found | Requested resource does not exist |
| 409 | Conflict | Resource already exists or state conflict |
| 422 | Validation Error | Request data failed validation |
| 429 | Rate Limited | Too many requests, rate limit exceeded |
| 500 | Internal Error | Server error, check logs |

## Rate Limiting

Most endpoints are rate limited to prevent abuse:

- **Authentication**: 5 requests per minute per IP
- **Chat messages**: 1 message per 0.5 seconds per user
- **Match creation**: 1 request per minute per user
- **Assessment submission**: 10 requests per minute per user

Rate limit headers are included in responses:
```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 59
X-RateLimit-Reset: 1692185400
```

## Webhooks (Future)

The API will support webhooks for real-time notifications:

- **Match Created**: When a new match is found
- **Message Received**: When a chat message is sent
- **Session Scheduled**: When a wingman session is created
- **Session Completed**: When users finish a practice session

---

## Example Usage

### Complete User Journey

1. **Authentication**:
```bash
curl -X POST http://localhost:8000/api/auth/signin \
  -H "Content-Type: application/json" \
  -d '{"email": "john@example.com"}'
```

2. **Complete Profile**:
```bash
curl -X POST http://localhost:8000/api/profile/complete \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user-uuid", "first_name": "John", ...}'
```

3. **Take Confidence Test**:
```bash
curl -X POST http://localhost:8000/api/confidence-test/start \
  -H "Authorization: Bearer {token}" \
  -d '{"user_id": "user-uuid"}'
```

4. **Find Buddy**:
```bash
curl -X POST http://localhost:8000/api/matches/auto/user-uuid \
  -H "Authorization: Bearer {token}"
```

5. **Accept Match**:
```bash
curl -X POST http://localhost:8000/api/buddy/respond \
  -H "Authorization: Bearer {token}" \
  -d '{"user_id": "user-uuid", "match_id": "match-uuid", "action": "accept"}'
```

6. **Schedule Session**:
```bash
curl -X POST http://localhost:8000/api/session/create \
  -H "Authorization: Bearer {token}" \
  -d '{"match_id": "match-uuid", "venue_name": "Coffee Shop", ...}'
```

---

*For additional support or questions about the API, please contact the development team.*