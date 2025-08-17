# Creativity Archetype Integration Guide

## Overview
This guide walks through integrating the creativity personality test and archetype-based AI personalization into the Fridays at Four backend. The system allows users to take a personality test that determines their creative working style, then personalizes Hai's responses accordingly.

**🎯 APPROACH**: This integration uses **prompt-based personalization** with consistent temperature across all archetypes. This maintains Hai's core personality while adapting her working style guidance to match each user's creative preferences.

## Database Schema
The archetype data is stored in the existing `creator_creativity_profiles` table:

```sql
-- Table structure (already exists)
creator_creativity_profiles (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES creator_profiles(id),
  archetype INTEGER,  -- 1-6 corresponding to personality types
  test_responses JSONB,
  archetype_score JSONB,
  secondary_archetype INTEGER,
  secondary_score FLOAT,
  date_taken TIMESTAMP,
  created_at TIMESTAMP,
  updated_at TIMESTAMP
)
```

## Step 1: Update Prompts Module

### File: `src/prompts.py`
- ✅ **Updated for temperature consistency** - The prompts module includes:
  - 6 archetype-specific style adaptations (prompt-based only)
  - Single consistent temperature for all archetypes
  - Helper functions for prompt personalization

### Key Functions Added:
- `get_personalized_prompt(base_prompt, archetype, context)` - Combines main prompt with archetype style guidance
- `get_archetype_temperature()` - Returns consistent temperature (0.6) for all archetypes

## Step 2: Add Database Helper Function

### File: `main.py`
Add this function near the other helper functions (around line 165, after cache functions):

```python
async def get_user_archetype(user_id: str) -> int | None:
    """Get user's creativity archetype from database"""
    try:
        result = supabase.table('creator_creativity_profiles')\
            .select('archetype')\
            .eq('user_id', user_id)\
            .single()
        return result.data.get('archetype') if result.data else None
    except Exception as e:
        logger.debug(f"No archetype found for user {user_id}: {e}")
        return None  # Graceful fallback - no archetype means default behavior
```

## Step 3: Update Claude Agent Integration

### File: `src/claude_agent.py`

#### A. Add Imports
```python
from src.prompts import get_personalized_prompt, get_archetype_temperature, main_prompt
```

#### B. Update Function Signatures
Modify both `interact_with_agent` and `interact_with_agent_stream` to accept archetype:

```python
async def interact_with_agent(
    user_input: str,
    user_id: str,
    user_timezone: str,
    thread_id: str,
    supabase_client,
    context: dict,
    user_archetype: int = None  # Add this parameter
) -> str:
```

#### C. Replace System Prompt Creation
Find where the system prompt is currently created and replace with:

```python
# Get personalized prompt (temperature stays consistent)
personalized_system_prompt = get_personalized_prompt(
    main_prompt, 
    user_archetype, 
    formatted_context  # Your existing context formatting
)
# Use consistent temperature for all archetypes
temperature = get_archetype_temperature()  # Returns 0.6 for all users
```

#### D. Update Claude API Calls
When calling Claude, use the personalized prompt with consistent temperature:

```python
# Use existing Claude API call structure but with personalized prompt
# Temperature remains consistent at 0.6 for all archetypes
response = await client.messages.create(
    model=model_name,
    max_tokens=max_tokens,
    temperature=temperature,  # Consistent 0.6 for all users
    system=personalized_system_prompt,  # Archetype-specific guidance
    messages=conversation_messages
)
```

## Step 4: Update API Endpoints

### File: `main.py`

#### A. Update Query Endpoint
In `query_knowledge_base` function (around line 400):

```python
@app.post("/query", response_model=QueryResponse)
async def query_knowledge_base(request: Request, query_request: QueryRequest):
    try:
        logger.info(f"Received query request for user {query_request.user_id}")
        
        # Get user's archetype
        user_archetype = await get_user_archetype(query_request.user_id)
        
        # ... existing memory handler code ...
        
        # Get response from agent with archetype
        response = await interact_with_agent(
            user_input=query_request.question,
            user_id=query_request.user_id,
            user_timezone=query_request.user_timezone,
            thread_id=query_request.thread_id,
            supabase_client=supabase,
            context=context,
            user_archetype=user_archetype  # Add this
        )
        
        # ... rest of existing code ...
```

#### B. Update Streaming Endpoint
Make the same changes to `query_knowledge_base_stream` function:

```python
# Add archetype lookup
user_archetype = await get_user_archetype(query_request.user_id)

# Pass to streaming function
stream_gen = interact_with_agent_stream(
    user_input=query_request.question,
    user_id=query_request.user_id,
    user_timezone=query_request.user_timezone,
    thread_id=query_request.thread_id,
    supabase_client=supabase,
    context=context,
    user_archetype=user_archetype  # Add this
)
```

#### C. Update Chat Endpoint
The `/chat` endpoint maps to the query logic, so it should automatically inherit the personalization.

## Step 5: Testing the Integration

### Test Cases
1. **User without archetype**: Should get default Hai experience (no errors)
2. **User with archetype 1 (Big Picture Visionary)**: Should get expansive, strategic guidance (same warm Hai personality)
3. **User with archetype 3 (Steady Builder)**: Should get structured, milestone-focused approach (same warm Hai personality)
4. **User with archetype 6 (Intuitive Artist)**: Should get flowing, intuition-validating style (same warm Hai personality)

### Validation Points
- Check that `get_user_archetype()` returns correct values
- Verify consistent temperature (0.6) for all archetypes
- Confirm **style differences** in conversation approach (not personality changes)
- Ensure graceful fallback when no archetype is found
- Validate that Hai's core warmth and reliability remain constant

## Step 6: Monitoring and Debugging

### Logging
Add debug logging to track archetype usage:

```python
if user_archetype:
    logger.info(f"Using archetype {user_archetype} style adaptation for user {user_id}")
else:
    logger.info(f"No archetype found for user {user_id}, using default style")
```

### Performance Considerations
- The archetype lookup adds one database query per conversation
- Consider caching archetype in memory handlers if needed
- Database query is lightweight (single table, indexed lookup)

## Archetype Style Adaptations Reference

| Archetype | Name | Temperature | Style Focus |
|-----------|------|-------------|-------------|
| 1 | Big Picture Visionary | 0.6 | Strategic connections, systems thinking |
| 2 | Creative Sprinter | 0.6 | Burst planning, flexible timelines |
| 3 | Steady Builder | 0.6 | Step-by-step structure, consistent progress |
| 4 | Collaborative Creator | 0.6 | Feedback loops, partnership approaches |
| 5 | Independent Maker | 0.6 | Autonomous paths, efficient workflows |
| 6 | Intuitive Artist | 0.6 | Flow-based guidance, authentic expression |

**🔑 KEY PRINCIPLE**: Same temperature (0.6), same warm Hai personality, different working style guidance.

## Deployment Checklist

- [ ] Update `src/prompts.py` with temperature-consistent archetype system
- [ ] Add `get_user_archetype()` function to `main.py`
- [ ] Update `src/claude_agent.py` with prompt-based personalization
- [ ] Modify API endpoints to pass archetype
- [ ] Test with users who have archetypes (verify style differences, not personality changes)
- [ ] Test with users who don't have archetypes
- [ ] Verify consistent temperature across all interactions
- [ ] Check performance impact
- [ ] Add monitoring/logging

## Future Enhancements

### Gradual Expansion Strategy
- **Phase 1**: Deploy current prompt-based system, measure user satisfaction
- **Phase 2**: If successful, consider slight temperature variations (0.55-0.65 range)
- **Phase 3**: Expand style differences based on user feedback and data

### Archetype Analytics
- Track which archetypes are most common
- Monitor conversation quality by archetype
- A/B test style adaptation effectiveness

### Advanced Personalization
- Secondary archetype blending
- Evolution of archetype over time
- Context-aware style adjustments

### User Experience
- Allow users to retake personality test
- Show archetype in user profile
- Explain how archetype affects AI working style guidance

## Notes for Frontend Integration

When the personality test is built:
1. Store results in `creator_creativity_profiles` table
2. Set `archetype` field to 1-6 based on test results
3. Backend will automatically start using style personalization
4. No frontend changes needed for personalized conversations

The personality test itself will be a separate implementation that feeds into this system.

## Benefits of Temperature-Consistent Approach

✅ **Maintains trusted partner experience**
✅ **Clean A/B testing capability** 
✅ **Safe rollout with expansion potential**
✅ **Preserves Hai's core personality that users love**
✅ **Measurable impact of archetype matching**
✅ **Easy to iterate and improve**