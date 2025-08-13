# API Reference

## Base URLs
- **Production**: `https://fridays-at-four-c9c6b7a513be.herokuapp.com`
- **Local**: `http://localhost:8000`

## Endpoints

### POST /query
Non-streaming conversation endpoint

**Request:**
```json
{
    "user_input": "Hello, can you help me?",
    "user_id": "uuid-string",      // Required: proper UUID format
    "thread_id": "uuid-string"     // Optional: creates new if not provided
}
```

**Response:**
```json
{
    "response": "Hi! I'm Hai, your creative project coach...",
    "thread_id": "uuid-string",
    "user_id": "uuid-string",
    "processing_time": 1.23
}
```

### POST /query_stream
Server-sent events streaming endpoint

**Request:** Same as `/query`  
**Response:** SSE stream with chunked text

### GET /project-overview/{user_id}
Retrieve user's project data

**Response:**
```json
{
    "project_name": "My Novel",
    "project_type": "Creative Writing", 
    "goals": ["Finish first draft"],
    "challenges": ["Time management"],
    "success_metrics": {...}
}
```

### GET /project-data/{user_id}
**NEW:** Unified endpoint that returns both project overview and status data with caching

**Response (Cached Data Available):**
```json
{
    "status": "cached",
    "overview_data": {
        "profile": {
            "id": "user-123",
            "first_name": "John",
            "last_name": "Doe"
        },
        "project": {
            "id": "project-123",
            "user_id": "user-123",
            "project_name": "My Novel",
            "project_type": "Creative Writing",
            "goals": ["Finish first draft"],
            "challenges": ["Time management"],
            "success_metrics": {...}
        },
        "recent_updates": [...],
        "recent_activity": [...]
    },
    "project_status": {
        "ai_understanding": {
            "knows_your_project": true,
            "tracking_progress": true,
            "has_next_steps": true,
            "project_name": "My Novel",
            "current_phase": "writing",
            "last_activity": "2024-01-01T12:00:00Z"
        },
        "current_tasks": {
            "next_steps": ["Write chapter 3"],
            "blockers": ["Research needed"],
            "recent_wins": ["Completed outline"]
        },
        "project_summary": {
            "name": "My Novel",
            "type": "Creative Writing",
            "phase": "writing",
            "total_updates": 5,
            "last_update": "2024-01-01T12:00:00Z"
        },
        "goals_progress": {
            "primary_goals": ["Finish first draft"],
            "main_challenges": ["Time management"]
        },
        "is_active": true
    },
    "cache_age_minutes": 15
}
```

**Response (Data Loading):**
```json
{
    "status": "loading",
    "overview_data": {
        "project": {
            "project_name": "My Novel",
            "project_type": "Creative Writing"
        },
        "profile": {...},
        "recent_updates": [],
        "recent_activity": []
    },
    "project_status": {
        "ai_understanding": {
            "knows_your_project": true,
            "tracking_progress": false,
            "has_next_steps": false,
            "project_name": "My Novel",
            "current_phase": "writing",
            "last_activity": null
        },
        "current_tasks": {"next_steps": [], "blockers": [], "recent_wins": []},
        "project_summary": {...},
        "goals_progress": {...},
        "is_active": false
    },
    "message": "Full project data is loading in the background..."
}
```

### POST /project-overview/{user_id}
Create/update project overview

**Request:**
```json
{
    "project_name": "My Novel",
    "project_type": "Creative Writing",
    "goals": ["Finish first draft", "Character development"],
    "challenges": ["Plot consistency"],
    "success_metrics": {"word_count": 80000}
}
```

### GET /conversation_history/{user_id}
Get user's chat history

**Query params:** `limit` (default: 50), `offset` (default: 0)

**Response:**
```json
{
    "messages": [
        {
            "content": "Hello",
            "role": "user",
            "created_at": "2024-01-01T12:00:00Z"
        }
    ],
    "total": 150
}
```

### GET /health
System health check

**Response:** `{"status": "healthy"}`

## Models

```python
class QueryRequest(BaseModel):
    user_input: str
    user_id: str                    # UUID format required
    thread_id: Optional[str] = None

class QueryResponse(BaseModel):
    response: str
    thread_id: str
    user_id: str
    processing_time: Optional[float]

class ProjectOverview(BaseModel):
    project_name: str
    project_type: str
    goals: List[str]
    challenges: List[str]
    success_metrics: Dict[str, Any]
```

## Error Responses

**422 Validation Error:**
```json
{
    "detail": [
        {
            "loc": ["body", "user_id"],
            "msg": "Invalid UUID format",
            "type": "value_error"
        }
    ]
}
```

**500 Internal Error:**
```json
{
    "detail": "Internal server error",
    "type": "server_error"
}
```

## Testing

```bash
# Health check
curl http://localhost:8000/health

# Chat request
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "Hello",
    "user_id": "'$(uuidgen)'",
    "thread_id": "'$(uuidgen)'"
  }'

# Project overview
curl -X GET http://localhost:8000/project-overview/$(uuidgen)

# NEW: Unified project data (recommended)
curl -X GET http://localhost:8000/project-data/$(uuidgen)


# Streaming (requires SSE client)
curl -N -X POST http://localhost:8000/query_stream \
  -H "Content-Type: application/json" \
  -d '{"user_input": "Tell me a story", "user_id": "'$(uuidgen)'"}'
```

## Authentication

**Development:** No authentication required  
**Production:** JWT tokens from Supabase Auth (header: `Authorization: Bearer <token>`)

## Rate Limits

No explicit rate limiting. Claude API limits handled internally with OpenAI fallback.

## CORS

Allowed origins:
- `https://app.fridaysatfour.co`
- `http://localhost:3000`
- `https://fridaysatfour.co` 