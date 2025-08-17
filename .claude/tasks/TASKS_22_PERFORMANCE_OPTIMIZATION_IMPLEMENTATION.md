# Tasks 22.1 & 22.2: WingmanMatch Performance Optimization Implementation Plan

## Mission
Implement Redis caching for hot reads (Task 22.1) and AI content summarization with model routing (Task 22.2) for the WingmanMatch dating confidence coaching platform.

## Stack Analysis
**Detected Stack**: Python FastAPI + Supabase PostgreSQL + Direct Claude API + Redis Cache Infrastructure
- **Backend Framework**: FastAPI with async-first architecture
- **Database**: Supabase PostgreSQL with dating confidence tables (approach_challenges, wingman_matches, user_locations, confidence_test_results)
- **AI Integration**: Direct Anthropic Claude API (migrated from LangChain for 40-60% performance improvement)
- **Memory System**: Advanced conversation memory with summarization via content_summarizer.py
- **Caching**: Currently uses in-memory project cache (project_cache dict with 30-minute TTL)

## Architecture Insights from Codebase Analysis

### Current Caching Patterns (src/main.py)
```python
# Simple in-memory cache for project data
project_cache = {}
cache_timestamps = {}
CACHE_DURATION = timedelta(minutes=30)  # Cache for 30 mins
```

### Existing Summarization Architecture (src/content_summarizer.py)
- **ContentSummarizer**: Map-reduce pattern using Claude API directly
- **Model Selection**: Already has model optimization via src/model_selector.py
- **Memory Management**: BufferSummaryHandler with 100-message buffer size
- **Cost Optimization**: get_summarization_model() and get_analysis_model() functions exist

### Database Tables for Caching
- `approach_challenges`: Dating challenge content
- `wingman_matches`: User matching and reputation data  
- `user_locations`: Geographic data for match discovery
- `confidence_test_results`: User assessment results

## Implementation Plan

### Phase 1: Redis Infrastructure Setup
**Target**: Replace in-memory caching with Redis for horizontal scaling and persistence

**Implementation Strategy**:
1. **Redis Connection Pool**: Use connection pooling similar to Supabase pattern
2. **Cache Key Strategy**: Hierarchical keys with TTL management
3. **ETag Headers**: Implement ETag middleware for static content caching
4. **Graceful Fallback**: Redis failures shouldn't break the application

### Phase 2: AI Model Routing & Cost Optimization
**Target**: Route conversations to appropriate models based on content type and implement memory compression

**Implementation Strategy**:
1. **Conversation Classification**: Detect small talk vs coaching requests
2. **Model Router**: Use cheaper models (Haiku) for simple responses, Claude Sonnet for complex coaching
3. **Memory Compression**: Summarize old conversations and truncate context
4. **Context Window Management**: Implement sliding window with summary preservation

## Technical Implementation

### Task 22.1: Redis Caching for Hot Reads

#### Files to Create/Modify:
1. **src/redis_client.py** - Redis connection and helper functions
2. **src/cache_middleware.py** - FastAPI middleware for caching
3. **src/main.py** - Integration with existing endpoints
4. **src/config.py** - Redis configuration

#### Redis Cache Strategy:
```python
# Cache Keys Pattern
cache_keys = {
    "challenges": "wingman:challenges:{challenge_id}",
    "user_reputation": "wingman:reputation:{user_id}",
    "user_location": "wingman:location:{user_id}",
    "match_candidates": "wingman:matches:{user_id}:{radius}",
    "static_content": "wingman:static:{content_hash}"
}

# TTL Strategy
ttl_settings = {
    "challenges": 3600,      # 1 hour (semi-static content)
    "reputation": 300,       # 5 minutes (dynamic but not real-time)
    "location": 1800,        # 30 minutes (location updates)
    "matches": 600,          # 10 minutes (match discovery)
    "static_content": 86400  # 24 hours (truly static)
}
```

### Task 22.2: AI Model Routing & Memory Optimization

#### Files to Create/Modify:
1. **src/model_router.py** - Smart model selection logic
2. **src/memory_compressor.py** - Context compression and summarization
3. **src/conversation_classifier.py** - Content-based routing decisions
4. **src/claude_agent.py** - Integration with new routing logic

#### Model Routing Strategy:
```python
# Model Selection Logic
routing_rules = {
    "small_talk": "claude-3-haiku-20240307",      # Cheap for greetings, confirmations
    "coaching": "claude-3-5-sonnet-20241022",     # Premium for dating advice
    "assessment": "claude-3-5-sonnet-20241022",   # Premium for personality analysis
    "summarization": "claude-3-haiku-20240307"     # Cheap for content compression
}

# Content Classification
content_types = {
    "greeting": ["hi", "hello", "hey", "good morning"],
    "confirmation": ["yes", "no", "ok", "thanks", "got it"],
    "coaching_request": ["help", "advice", "how do i", "what should"],
    "assessment": ["test", "quiz", "evaluate", "analyze"]
}
```

#### Memory Compression Strategy:
```python
# Context Management
context_limits = {
    "max_recent_messages": 15,     # Keep last 15 messages in full
    "max_total_tokens": 8000,      # Claude's context window management
    "summary_threshold": 30,       # Summarize when >30 messages
    "compression_ratio": 0.3       # Target 30% of original length
}
```

## Quality Standards & Security

### Performance Targets:
- **Cache Hit Rate**: >85% for frequently accessed data
- **Response Time**: <200ms for cached endpoints
- **Cost Reduction**: 40-60% reduction in AI API costs
- **Memory Efficiency**: 70% reduction in context token usage

### Security Considerations:
- **Cache Key Isolation**: User-scoped keys prevent data leakage
- **Redis AUTH**: Authentication for production deployment
- **PII Protection**: Never cache sensitive personal information
- **Cache Invalidation**: Proper cleanup on user data changes

### Error Handling:
- **Redis Failover**: Graceful degradation to database queries
- **Model Fallback**: Default to reliable model if routing fails
- **Context Recovery**: Reconstruct context from summaries if needed
- **Monitoring**: Comprehensive logging for cache performance

## Testing Strategy

### Integration Tests:
1. **Cache Performance**: Measure hit rates and response times
2. **Model Routing**: Validate correct model selection for different content types
3. **Memory Compression**: Ensure conversation continuity after summarization
4. **Failover Testing**: Verify graceful degradation when Redis is unavailable

### Load Testing:
1. **Concurrent Users**: Test cache performance under load
2. **Memory Pressure**: Validate compression effectiveness
3. **Cost Analysis**: Measure actual AI cost savings

## Implementation Priority

### Phase 1 (High Priority - Task 22.1):
1. ✅ Redis connection infrastructure
2. ✅ Cache helper functions with TTL management
3. ✅ ETag middleware for static content
4. ✅ Hot data caching for challenges, reputation, locations

### Phase 2 (High Priority - Task 22.2):
1. ✅ Conversation classifier for model routing
2. ✅ AI model router with cost optimization
3. ✅ Memory compression system
4. ✅ Integration with existing claude_agent.py

### Phase 3 (Integration & Testing):
1. ✅ End-to-end testing with real data
2. ✅ Performance benchmarking
3. ✅ Production deployment preparation

## Expected Deliverables

### Redis Caching Infrastructure:
- **Production-ready Redis client** with connection pooling
- **Cached API endpoints** for challenges, reputation, and location data
- **ETag middleware** for static content optimization
- **Monitoring and metrics** for cache performance

### AI Model Routing System:
- **Intelligent model selection** based on conversation content
- **Cost-optimized Claude API usage** with 40-60% cost reduction target
- **Memory compression system** maintaining conversation quality
- **Context window management** for efficient token usage

### Integration & Performance:
- **Seamless integration** with existing FastAPI patterns
- **Comprehensive error handling** and graceful degradation
- **Production monitoring** and observability
- **Load testing validation** under realistic traffic patterns

---

**Next Steps**: Begin implementation with Redis infrastructure setup, followed by AI model routing integration.