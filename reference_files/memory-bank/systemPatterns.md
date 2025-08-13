# ⚙️ System Patterns - Architecture & Design Intelligence

## 🚨 **CRITICAL DEVELOPMENT RULES - READ FIRST**

### 🛑 **DEPLOYMENT SAFETY RULES**
**PRODUCTION DEPLOYMENT FORBIDDEN**: Never deploy to production under any circumstances
- ❌ **NEVER**: `git push heroku main` or any production deployment commands
- ❌ **NEVER**: Manual Heroku deployments to production apps
- ✅ **DEV ONLY**: Only deploy to development with explicit user permission
- 🤝 Always ask: "Should I deploy this to dev?" before any deployment
- 🔒 **SAFETY**: All production deployments go through GitHub Actions only

### 🛑 **DATABASE SAFETY RULES**
**PRODUCTION DATABASE FORBIDDEN**: Never test or modify production data
- ❌ **NEVER**: Test code against production database (ipvxxsthulsysbkwbitu.supabase.co)
- ❌ **NEVER**: Write, modify, or delete production data during development
- ❌ **NEVER**: Use production database for debugging or experimentation
- ✅ **DEV ONLY**: Always use development database (mxlmadjuauugvlukgrla.supabase.co)
- 🧪 **TESTING**: All code testing must use dev database with proper cleanup
- 🔒 **SAFETY**: Production data is sacred - never touch it during development

### 📚 **TECHNICAL DOCUMENTATION PATTERNS**
**DEVELOPER-FIRST COMMUNICATION**: Technical documentation should respect expertise
- ✅ **CONCISE**: Remove verbose explanations and hand-holding language
- ✅ **PRACTICAL**: Provide copy-paste ready commands and code examples
- ✅ **ACCURATE**: Verify all URLs, credentials, and technical details
- ✅ **STRUCTURED**: Use consistent formatting with clear sections
- ✅ **COMPLETE**: Include both setup and troubleshooting information
- ❌ **AVOID**: Emoji, cheerful language, or beginner-level explanations
- ❌ **AVOID**: Theoretical examples when practical ones exist
- 🎯 **TARGET**: Experienced Python/AI developers who want immediate productivity

### 🛑 **API CONTRACT COMPLETENESS RULE** ✅ **NEWLY DISCOVERED**
**FRONTEND INTEGRATION SAFETY**: Always implement ALL expected endpoints before frontend handoff
- 🚨 **CRITICAL**: Missing endpoints cause cascading UI failures, not just 404s
- 🔍 **DETECTION**: React minified errors (#418/#423) often indicate backend API contract mismatches
- ✅ **VALIDATION**: Verify ALL endpoints referenced in frontend code exist and return expected data structures
- 📋 **TESTING**: Test complete API contract with real frontend integration scenarios
- 🤝 **COORDINATION**: Frontend expectations must match backend implementation exactly
- ❌ **NEVER**: Declare integration ready without implementing complete endpoint set
- 🎯 **PATTERN**: Missing `/project-status/{user_id}` caused complete frontend breakdown

### 🤖 **AI PROMPT QUALITY PATTERNS** ✅ **NEWLY IMPLEMENTED**
**ELIMINATE META-COMMENTARY**: AI responses must be direct and actionable
- 🚨 **CRITICAL**: AI meta-commentary like "I'll analyze..." creates poor user experience
- ✅ **DIRECT OUTPUT**: Prompts must specify "output ONLY the content, no meta-commentary"
- ✅ **STRICT JSON**: For structured data, enforce JSON-only responses with validation
- ✅ **CHARACTER LIMITS**: Specify exact field lengths for frontend integration
- ❌ **NEVER**: Allow AI to narrate its process or explain what it's doing
- 🎯 **PATTERN**: MAP_PROMPT and REDUCE_PROMPT fixed by removing process narration
- 🔧 **VALIDATION**: Test prompts manually to ensure clean, direct output

### 🎨 **ARCHETYPE PERSONALIZATION PATTERNS** ✅ **NEWLY ESTABLISHED**
**TEMPERATURE-CONSISTENT PERSONALIZATION**: Use prompts, not temperature, for personality adaptation
- 🌡️ **TEMPERATURE RULE**: Consistent 0.6 across all user archetypes (no extreme 0.3-0.8 variations)
- 📝 **PERSONALIZATION METHOD**: Style guidance through prompt injection, not AI personality changes
- 🎯 **ARCHETYPE APPROACH**: 6 creativity archetypes (Visionary, Methodical, Collaborative, etc.)
- 🏗️ **CODE SEPARATION**: prompts.py (prompts only), archetype_helper.py (logic), simple_memory.py (database)
- 🔄 **GRACEFUL FALLBACK**: System works without archetype data using default style
- 🧪 **TESTING STRATEGY**: Start with subtle differences, measure impact before expanding
- ❌ **AVOID**: Extreme temperature changes that make tracking effectiveness impossible
- 🎯 **PATTERN**: Prompt-based adaptation maintains Hai's core personality while adapting working style

### 🗃️ **ARCHETYPE DATABASE INTEGRATION PATTERN** ✅ **NEWLY CREATED**
**CLEAN ARCHETYPE LOOKUP**: Simple database integration for user creativity profiles
```python
async def get_user_archetype(user_id: str, supabase_client=None) -> Optional[int]:
    """Look up user's creativity archetype from database"""
    try:
        result = supabase_client.table('creator_creativity_profiles') \
            .select('archetype') \
            .eq('user_id', user_id) \
            .execute()
        
        if result.data and len(result.data) > 0:
            return result.data[0]['archetype']
        return None
    except Exception as e:
        logger.error(f"Error fetching user archetype: {e}")
        return None
```
- 🗃️ **DATABASE TABLE**: Uses existing creator_creativity_profiles table
- 🔍 **LOOKUP PATTERN**: Simple archetype number (1-6) retrieval by user_id
- 🛡️ **ERROR HANDLING**: Graceful fallback to None when archetype not found
- 📍 **LOCATION**: Database functions in simple_memory.py, logic in archetype_helper.py

---

# System Patterns: Fridays at Four

## Architecture Overview

### High-Level System Design
```
Frontend (React) ↔ Backend API (FastAPI) ↔ Database (Supabase) ↔ AI (Claude)
                                         ↕
                                   Memory System
```

### Core Components
1. **API Layer** (`src/main.py`) - FastAPI application handling requests
2. **Claude Agent** (`src/claude_agent.py`) - Direct Anthropic SDK conversation
3. **Memory Management** (`src/simple_memory.py`) - Conversation persistence
4. **Content Summarization** (`src/content_summarizer.py`) - Daily summaries and project updates
5. **Database Tools** (`src/tools/database_tools.py`) - Database interaction utilities

## Key Design Patterns

### 1. Simple Claude Agent Pattern
**Location**: `src/claude_agent.py`

**Pattern**: Direct Claude API integration with memory injection
```python
async def chat(user_id: str, message: str, thread_id: str = None):
    """Simple conversational interface using Claude API directly"""
    
    # Get conversation context
    memory = SimpleMemory(supabase_client, user_id)
    context = await memory.get_context(thread_id)
    
    # Build messages for Claude
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "system", "content": f"Context: {context['summaries']}"},
        *[{"role": msg["role"], "content": msg["content"]} 
          for msg in context["messages"]]
    ]
    
    # Direct Claude API call
    response = await claude_client.create_message(
        model="claude-3-5-sonnet-20241022",
        messages=messages,
        max_tokens=4000
    )
    
    return response.content[0].text
```

**Benefits**: 
- Simple, direct AI integration without complex frameworks
- Fast response times with minimal overhead
- Easy to debug and maintain
- Memory context provided as system messages

### 2. Auto-Dependency Creation Pattern
**Location**: `src/simple_memory.py`

**Pattern**: Ensure foreign key relationships before operations
```python
async def ensure_creator_profile(self, user_id: str):
    """Ensure creator profile exists before saving conversations"""
    try:
        # Check if profile exists
        result = self.supabase_client.table('creator_profiles')\
            .select('id').eq('id', user_id).execute()
        
        if not result.data:
            # Auto-create profile with proper schema
            profile_data = {
                'id': user_id,
                'slack_email': f"{user_id}@auto-created.local",
                'zoom_email': f"{user_id}@auto-created.local", 
                'first_name': 'New',
                'last_name': 'User'
            }
            self.supabase_client.table('creator_profiles')\
                .insert(profile_data).execute()
    except Exception as e:
        logger.error(f"Error ensuring creator profile: {e}")
```

**Benefits**:
- Prevents foreign key constraint violations
- Graceful handling of missing dependencies
- Automatic user profile creation

### 3. Memory Context Assembly Pattern
**Location**: `src/simple_memory.py`

**Pattern**: Hierarchical context building
```python
async def get_context(self, thread_id: str) -> Dict[str, Any]:
    """Assemble conversation context from multiple sources"""
    return {
        "messages": conversation_messages,      # Recent conversation
        "summaries": buffer_summaries,          # Conversation summaries
        "metadata": {
            "total_messages": len(conversation_messages),
            "summary_count": len(buffer_summaries),
            "thread_id": thread_id
        }
    }
```

**Benefits**:
- Structured context for AI agent
- Efficient memory utilization
- Clear separation of recent vs. summarized history

### 4. Content Summarization Pattern
**Location**: `src/content_summarizer.py`

**Pattern**: Map-reduce summarization with Claude API
```python
class ContentSummarizer:
    async def ainvoke(self, content: str) -> Dict[str, str]:
        """Summarize content using map-reduce pattern"""
        
        # Split content into chunks
        chunks = self.text_splitter.split_text(content)
        
        # Map phase: Process each chunk
        summaries = await asyncio.gather(*[
            self._map_chunk(chunk) for chunk in chunks
        ])
        
        # Reduce phase: Combine summaries
        final_summary = await self._reduce_summaries(summaries)
        
        return {"final_summary": final_summary}
```

**Benefits**:
- Handles large conversations efficiently
- Parallel processing for performance
- Structured output for database storage

### 5. Schema Alignment Pattern ✅ **CRITICAL PATTERN DISCOVERED**
**Location**: `src/main.py`

**Pattern**: Always align Pydantic models with actual database schema
```python
# ❌ WRONG: Assuming database stores simple types
class ProjectOverview(BaseModel):
    goals: List[str]  # Assumes simple strings
    challenges: List[str]  # Assumes simple strings

# ✅ CORRECT: Match actual database structure
class Goal(BaseModel):
    title: str
    description: str

class Challenge(BaseModel):
    title: str 
    description: str

class ProjectOverview(BaseModel):
    goals: List[Goal]  # Matches database ARRAY of JSON objects
    challenges: List[Challenge]  # Matches database ARRAY of JSON objects
```

**Critical Discovery**: PostgreSQL ARRAY columns store complex objects, not simple strings
- **Database Reality**: `[{title: "Goal 1", description: "Details"}, ...]`
- **Previous Assumption**: `["Goal 1", "Goal 2", ...]`
- **Impact**: API parsing failures, incomplete frontend data display
- **Testing Method**: Real dev API calls revealed the mismatch vs theoretical testing

### 6. Real-World Testing Pattern ✅ **NEWLY DISCOVERED**
**Location**: Testing approach

**Pattern**: Test against actual endpoints, not mocked data
```python
# ❌ WRONG: Testing against artificial mock data
def test_with_mocks():
    mock_data = {'goals': 'fake_string'}  # Not real database structure
    
# ✅ CORRECT: Test against live dev API with real data
def test_with_real_api():
    response = requests.get('https://fridays-at-four-dev-434b1a68908b.herokuapp.com/project-overview/real-user-id')
    # This reveals actual data structure vs assumptions
```

**Benefits**:
- Discovers real schema mismatches vs theoretical edge cases
- Validates against actual database content structure
- Prevents deployment of code that fails with real data

### 7. Complete API Contract Pattern ✅ **PREVIOUSLY IMPLEMENTED**
**Location**: `src/main.py`

**Pattern**: Implement ALL expected endpoints for frontend integration
```python
# Complete project data API contract
@app.get("/project-overview/{user_id}")
async def get_project_overview(user_id: str):
    """Rich project data with caching and task tracking"""
    return ProjectOverviewResponse(...)

@app.get("/project-status/{user_id}")  # PREVIOUSLY ADDED
async def get_project_status(user_id: str):
    """Lightweight dashboard polling with activity status"""
    return ProjectStatusResponse(...)

@app.get("/project-data-status/{user_id}")
async def check_project_data_status(user_id: str):
    """Cache status checking for progressive loading"""
    return {"ready": True, "data": cached_data}
```

**Critical Lessons Learned**:
- ✅ **Complete Implementation**: All 3 endpoints must exist for frontend stability
- ✅ **Error Prevention**: Missing endpoints cause React errors #418/#423
- ✅ **UI Stability**: Incomplete API contracts break entire frontend experience
- ✅ **Testing Priority**: Always verify complete endpoint set before integration

### 6. Background Caching Pattern ✅ **RECENTLY IMPLEMENTED**
**Location**: `src/main.py`

**Pattern**: Background task loading with progressive UI updates
```python
# In-memory cache with TTL
project_cache = {}
cache_timestamps = {}
CACHE_DURATION = timedelta(hours=1)

@app.get("/project-overview/{user_id}")
async def get_project_overview(user_id: str, background_tasks: BackgroundTasks):
    """Progressive loading with background caching"""
    
    # Check cache first
    cached_data = get_cached_project_data(user_id)
    if cached_data:
        return ProjectOverviewResponse(
            status="cached",
            data=cached_data,
            cache_age_minutes=get_cache_age(user_id)
        )
    
    # Return loading status, trigger background fetch
    background_tasks.add_task(load_project_data_background, user_id)
    return ProjectOverviewResponse(
        status="loading",
        message="Project data is loading in the background..."
    )
```

**Benefits**:
- ✅ **UI Never Blocks**: Users can chat immediately while data loads
- ✅ **Performance**: ~1 second cached response vs slow database queries
- ✅ **Progressive Loading**: Frontend can poll for completion status
- ✅ **User Experience**: No 1-minute UI freezing during project data loading

### 7. JSON Extraction Robustness Pattern ✅ **PREVIOUSLY FIXED**
**Location**: `src/content_summarizer.py`

**Pattern**: Multi-strategy JSON extraction with error recovery
```python
def extract_json_from_text(text: str) -> dict:
    """Robustly extract JSON with multiple fallback strategies"""
    
    # Strategy 1: Code fence wrapped JSON
    json_blocks = re.findall(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
    
    # Strategy 2: Brace counting with segment processing (FIXED)
    # Prevents negative brace_count issues
    while search_start < text_len:
        # Process in segments to avoid negative counts
        if brace_count > 0:  # Only decrement if we have open braces
            brace_count -= 1
    
    # Strategy 3: Regex patterns allowing nested structures (FIXED)
    patterns = [
        r'\{[^{}]*"field"[^{}]*(?:\{[^{}]*\}[^{}]*)*\}',  # Allows nested objects
        r'\{(?:[^{}]|(?:\{[^{}]*\}))*\}'  # Balanced brace matching
    ]
```

**Critical Fixes Applied**:
- ✅ **Negative brace count prevention**: Segmented processing avoids infinite loops
- ✅ **Nested JSON support**: Updated regex patterns handle complex structures
- ✅ **Production stability**: Robust extraction for project updates and summaries

### 6. Memory Continuity Pattern ✅ **IMPLEMENTED**
**Location**: `src/simple_memory.py`

**Pattern**: User-scoped memory queries for cross-session continuity
```python
async def get_context(self, thread_id: str):
    """Get ALL user memory across threads for session continuity"""
    # Query by user_id for cross-session memory
    messages = self.supabase.table('memory')\
        .select('*')\
        .eq('user_id', self.user_id)\
        .eq('memory_type', 'message')\
        .order('created_at')\
        .limit(50)\
        .execute()
```

**Benefits**:
- Cross-session conversation continuity
- User-centric memory model
- Natural conversation flow

### 7. Streaming Response Pattern
**Location**: `src/main.py`

**Pattern**: Server-sent events for real-time responses
```python
@app.post("/query_stream")
async def query_stream_endpoint(request: ChatRequest):
    """Stream Claude responses in real-time"""
    
    async def generate_response():
        async for chunk in claude_client.stream_message(messages):
            if chunk.type == "content_block_delta":
                yield f"data: {json.dumps({'content': chunk.delta.text})}\n\n"
    
    return StreamingResponse(
        generate_response(),
        media_type="text/plain",
        headers={"Cache-Control": "no-cache"}
    )
```

**Benefits**:
- Real-time user feedback
- Improved perceived performance
- Better user experience for long responses

### 8. Enhanced Project Overview Pattern ✅ **RECENTLY IMPLEMENTED**
**Location**: `src/main.py`

**Pattern**: Rich project data with task tracking
```python
@app.get("/project-overview/{user_id}")
async def get_enhanced_project_overview(user_id: str):
    """Enhanced project overview with task tracking"""
    
    # Get base project data
    project = get_project_overview(user_id)
    
    # Enhance with recent updates and task data
    enhanced_data = {
        "project_overview": project,
        "project_status": get_project_status(user_id),
        "top_tasks": extract_top_tasks(user_id)
    }
    
    return enhanced_data
```

**Benefits**:
- Comprehensive project intelligence for frontend
- Real-time task tracking with next steps/blockers
- Optimized data structure for dashboard UI

### 9. Improved AI Summarization Pattern ✅ **NEWLY IMPLEMENTED - JULY 2025**
**Location**: `src/prompts.py`, `src/content_summarizer.py`

**Pattern**: Strict JSON output with eliminated meta-commentary
```python
# ❌ OLD PATTERN: AI meta-commentary caused poor summaries
MAP_PROMPT = "Analyze this conversation and create a summary..."
# Result: "I'll analyze this conversation segment..."

# ✅ NEW PATTERN: Direct output with strict format requirements
MAP_PROMPT = """Analyze this conversation segment and provide a direct summary. 
Output ONLY the summary content - no meta-commentary about your process.

**Project Status:**
- Current tasks, owners, timelines, and status
...

Guidelines:
- Include only information that's explicitly stated
- Use clear, concise language
- No process narration or "I'll analyze" statements"""

# ✅ STRICT JSON FOR PROJECT UPDATES
PROJECT_UPDATE_PROMPT = """You are a JSON-only response bot. 
Your ONLY job is to output a SINGLE valid JSON object.

IMPORTANT: Output ONLY raw JSON - no markdown, no backticks, no explanation.

{
    "progress_summary": "Brief narrative (max 200 chars)",
    "milestones_hit": ["Achievement 1", "Achievement 2"],
    "blockers": ["Blocker 1"],
    "next_steps": ["Action 1", "Action 2"],
    "mood_rating": 4
}

STRICT RULES:
1. Output ONLY the JSON object
2. progress_summary: max 200 characters
3. milestones_hit: max 6 items, 50 chars each
4. blockers: max 4 items, 75 chars each
5. next_steps: max 5 items, 60 chars each
6. mood_rating: integer 1-5
"""
```

**Critical Improvements Made**:
- ✅ **Eliminated Meta-Commentary**: No more "I'll analyze..." responses
- ✅ **Strict JSON Format**: Enforced data types and character limits
- ✅ **Frontend-Ready Structure**: Consistent arrays and integers for UI consumption
- ✅ **Proper Field Extraction**: Fixed progress_summary to extract from parsed JSON
- ✅ **Validation**: Manual testing confirms clean, structured output

**Implementation Details**:
```python
# Fixed JSON field extraction in content_summarizer.py
project_update = {
    'user_id': user_id,
    'update_date': end_date.isoformat(),
    'progress_summary': parsed_data.get('progress_summary', progress_summary[:200]),  # FIXED
    'milestones_hit': parsed_data.get('milestones_hit', []),
    'blockers': parsed_data.get('blockers', []),
    'next_steps': parsed_data.get('next_steps', []),
    'mood_rating': parsed_data.get('mood_rating')
}
```

**Quality Validation Results**:
- ✅ **Clean Summaries**: No meta-commentary, direct narrative format
- ✅ **Structured Project Updates**: Proper JSON with defined field types
- ✅ **Character Limits**: All fields respect frontend display constraints
- ✅ **Data Types**: Arrays properly formatted, mood_rating as integer 1-5
- ✅ **Actionable Content**: Specific milestones, blockers, and next steps

**Testing Approach**:
```bash
# Manual validation of improved prompts
PYTHONPATH=. python src/nightly_summary_job.py --test

# Verify output quality in database
python3 -c "check recent summaries and project updates"
```

**Benefits for Frontend Integration**:
- 🎯 **Predictable Data**: Strict JSON structure enables reliable UI components
- 📊 **Display Optimization**: Character limits prevent UI overflow issues
- 🔄 **Consistent Types**: Arrays and integers work seamlessly with React state
- ⚡ **Performance**: Clean data reduces frontend parsing overhead
- 🎨 **UX Quality**: Professional summaries without AI process narration

### 10. Nightly Summarization Scheduling Pattern ✅ **RECENTLY FIXED**
**Location**: Heroku Scheduler Configuration

**Pattern**: Proper command path configuration for scheduled jobs
```bash
# ❌ OLD HEROKU SCHEDULER COMMAND: Missing path prefix
python nightly_summary_job.py

# ✅ FIXED HEROKU SCHEDULER COMMAND: Correct file path
python src/nightly_summary_job.py
```

**Critical Fix Applied**:
- 🚨 **Root Cause**: Heroku Scheduler was failing due to incorrect file path
- ✅ **Solution**: Added `src/` prefix to match actual file location
- ⏰ **Schedule**: Daily at 12:30 AM UTC for consistent processing
- 🔧 **Validation**: Manual test confirms job runs successfully on Heroku

**Operational Intelligence**:
- 📊 **Processing**: Handles 100+ conversations per day across multiple users
- 🧠 **Memory Management**: Clears old conversation data after summarization
- 📈 **Project Updates**: Generates structured task data alongside summaries
- 🔄 **Reliability**: Automated daily execution with error logging

## Error Handling Patterns

### 1. Graceful Degradation
```python
try:
    result = await ai_operation()
except Exception as e:
    logger.error(f"AI operation failed: {e}")
    return fallback_response()
```

### 2. Auto-Recovery
```python
async def ensure_dependencies():
    """Auto-create missing database dependencies"""
    await ensure_creator_profile(user_id)
    await ensure_thread_exists(thread_id)
```

### 3. Safe Defaults
```python
def get_user_context(user_id: str) -> Dict:
    """Return safe defaults if user data missing"""
    return {
        'name': 'User',
        'project': 'New Project',
        'history': []
    }
```

### 4. Data Type Validation Pattern ✅ **JUST FIXED**
**Location**: `src/main.py` - `get_project_status` endpoint

**Problem**: Database fields expected to be lists could contain strings, numbers, or None, causing TypeError on list operations
```python
# 🚨 DANGEROUS - Assumes data types without validation
next_steps.extend(update['next_steps'][:2])  # Fails if not a list
```

**Solution**: Safe extraction with type validation
```python
def safe_extract_list_items(value, max_items=2):
    """Safely extract items from a value that should be a list"""
    if isinstance(value, list):
        return value[:max_items]
    elif isinstance(value, str) and value.strip():
        # If it's a string, treat it as a single item
        return [value]
    else:
        # For any other type (int, dict, None, etc.), return empty list
        logger.warning(f"Expected list but got {type(value)}: {value}")
        return []

# ✅ SAFE - Validates before list operations
safe_items = safe_extract_list_items(update['next_steps'], 2)
next_steps.extend(safe_items)
```

**Benefits**:
- Prevents TypeError exceptions from list operations
- Graceful handling of unexpected data types
- Logs warnings for debugging database schema issues
- Maintains API functionality even with corrupted data

### 5. Robust Datetime Parsing Pattern ✅ **JUST FIXED**
**Location**: `src/main.py` - `get_project_status` endpoint

**Problem**: Fragile datetime parsing assumptions caused ValueError and TypeError exceptions
```python
# 🚨 DANGEROUS - Multiple failure points
last_activity_date = datetime.fromisoformat(last_activity.replace('Z', '+00:00'))
has_recent_activity = (datetime.now(timezone.utc) - last_activity_date) < timedelta(days=7)
```

**Solution**: Comprehensive datetime parsing with timezone safety
```python
def safe_parse_datetime(datetime_str):
    """Safely parse datetime string with proper timezone handling"""
    if not isinstance(datetime_str, str):
        logger.warning(f"Expected string datetime but got {type(datetime_str)}: {datetime_str}")
        return None, None
    
    try:
        # Handle various ISO formats
        clean_str = datetime_str
        if datetime_str.endswith('Z'):
            clean_str = datetime_str.replace('Z', '+00:00')
        elif '+' not in datetime_str and datetime_str.count(':') >= 2:
            clean_str = datetime_str + '+00:00'
        
        parsed_dt = datetime.fromisoformat(clean_str)
        
        # Ensure timezone-aware datetime
        if parsed_dt.tzinfo is None:
            parsed_dt = parsed_dt.replace(tzinfo=timezone.utc)
        
        return parsed_dt, datetime_str  # Return both parsed datetime and safe string
        
    except (ValueError, AttributeError) as e:
        logger.error(f"Failed to parse datetime '{datetime_str}': {e}")
        return None, None

# ✅ SAFE - Validates input type and handles parsing errors
last_activity_date, safe_activity_string = safe_parse_datetime(raw_activity)
if last_activity_date:
    last_activity = safe_activity_string  # Only set if parsing succeeded
    has_recent_activity = (datetime.now(timezone.utc) - last_activity_date) < timedelta(days=7)
else:
    last_activity = None  # Ensure Pydantic model gets valid type
    has_recent_activity = False
```

**Benefits**:
- Handles non-string datetime values safely
- Supports multiple ISO datetime formats
- Ensures timezone-aware datetime comparisons
- Guarantees Pydantic model receives correct data types
- Comprehensive error logging for debugging

### 6. Pydantic Model Safety Pattern ✅ **JUST FIXED**
**Critical Pattern**: Always ensure data types match Pydantic model expectations

```python
# 🚨 DANGEROUS - Passing invalid types to response model
return ProjectStatusResponse(
    last_activity=12345,  # Should be string or None, not int
    ...
)

# ✅ SAFE - Validate types before model instantiation
last_activity = safe_activity_string if last_activity_date else None
return ProjectStatusResponse(
    last_activity=last_activity,  # Always string or None
    ...
)
```

**Testing Coverage**: Comprehensive test suite validates both fixes
- `test_project_status_bug_fixes.py` - Tests various data types and edge cases
- All tests passing: Validates robustness against corrupted database data

## Performance Patterns

### 1. Async Operations
- All database calls use async/await
- Parallel processing where possible
- Non-blocking I/O throughout

### 2. Efficient Queries
```python
# Specific field selection
.select('id, name, created_at')

# Proper indexing on frequently queried fields
.eq('user_id', user_id)
.order('created_at', desc=True)
.limit(50)
```

### 3. Caching Strategy
- Claude prompt caching for repeated system prompts
- Memory context caching for active sessions
- Database connection pooling

## Testing Patterns

### 1. Development Database Testing
```python
# Always use dev database for testing
SUPABASE_URL = "https://mxlmadjuauugvlukgrla.supabase.co"

# Proper UUID format for test users
test_user_id = str(uuid.uuid4())

# Automatic cleanup after tests
await cleanup_test_data(test_user_id)
```

### 2. Integration Testing
- Test against real database schema
- Validate foreign key relationships
- Comprehensive conversation flows

### 3. Production Safety
- Never test against production database
- Isolated test environments
- Comprehensive error scenario coverage