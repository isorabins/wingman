# System Architecture

## Stack
**FastAPI** + **Claude API** + **Supabase PostgreSQL** + **Next.js** frontend  
**Deployment:** Heroku (backend) + Vercel (frontend)

## Core Components

### API Layer (`src/main.py`)
```python
@app.post("/query")         # Non-streaming chat
@app.post("/query_stream")  # SSE streaming
@app.get("/health")         # Health check
@app.get("/project-overview/{user_id}")  # Project data
```

### Agent (`src/claude_agent.py`)
Direct Anthropic SDK, no LangGraph:
```python
async def chat(message, context):
    response = await anthropic.messages.create(
        model="claude-3-5-sonnet-20241022",
        messages=[
            {"role": "system", "content": context},
            {"role": "user", "content": message}
        ]
    )
```

### Memory System (`src/simple_memory.py`)
User-scoped queries for cross-session continuity:
```python
async def get_context(self, thread_id):
    # Key pattern: Query by user_id, not thread_id
    messages = self.supabase.table('memory')\
        .select('*')\
        .eq('user_id', self.user_id)\
        .order('created_at')\
        .execute()
```

### Auto-Dependency Creation
Prevents foreign key violations:
```python
async def ensure_creator_profile(self, user_id):
    if not profile_exists:
        create_default_profile(user_id)
```

## Database Schema

```sql
creator_profiles (id, first_name, last_name, slack_email, zoom_email)
conversations (id, user_id, thread_id, created_at)
memory (id, user_id, thread_id, content, memory_type, created_at)
project_overview (user_id, project_name, project_type, goals, challenges)
longterm_memory (user_id, summary_date, content, metadata)
```

## Request Flow

```
User → Frontend → /query → Memory.get_context() → Claude API → Response
                                ↓
                        Memory.save_message()
```

## Key Patterns

1. **Singleton Agent**: Single Claude instance reused across requests
2. **Memory Injection**: Context via SystemMessages, no persistent state
3. **User-scoped Memory**: Query by `user_id` for cross-session continuity
4. **Auto-Dependencies**: Ensure FK relationships before operations
5. **Direct Claude API**: Removed LangGraph for production stability

## Performance

- **Prompt Caching**: 18% speed improvement
- **Async Operations**: All I/O is async
- **Efficient Queries**: Select specific fields
- **Nightly Summarization**: Prevents memory bloat

## Production Constraints

- **Memory Management**: Conversations summarized nightly
- **Rate Limiting**: Claude limits handled by LLM router + fallbacks
- **Database Safety**: DEV-only testing, production read-only
- **Error Handling**: Graceful degradation, no internal error exposure
