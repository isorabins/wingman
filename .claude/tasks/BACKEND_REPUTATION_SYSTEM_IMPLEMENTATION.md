# Backend Reputation System Implementation Plan

## 📋 **COMPLETE BACKEND DOMAIN OWNERSHIP**

**Domain Scope**: ALL backend aspects of the reputation system from calculation to API to caching
**Frontend Integration**: Provide standardized API contract for frontend consumption

---

## 🎯 **REQUIREMENTS ANALYSIS**

### **Core Business Logic**
- **Score Calculation**: `completed_sessions - no_shows` with bounds [-5, +20]
- **Data Source**: Query wingman_sessions table for user session history
- **Badge Logic**: Color coding based on score ranges
- **Caching Strategy**: 5-minute Redis TTL with graceful fallback
- **Performance**: Efficient database queries and optimized caching

### **API Contract Requirements**
```typescript
// Frontend will receive this exact structure:
{
  score: integer (-5 to 20),
  badge_color: "green" | "gold" | "red",
  completed_sessions: integer,
  no_shows: integer,
  cache_timestamp: ISO string
}
```

---

## 🏗️ **TECHNICAL ARCHITECTURE**

### **1. Reputation Service Layer** (`src/services/reputation_service.py`)
- **ReputationCalculator**: Core business logic for score computation
- **ReputationData**: Data class for reputation metrics
- **Database Integration**: Query wingman_sessions with user participation filtering
- **Caching Logic**: Redis integration with TTL and fallback patterns

### **2. API Integration** (`src/main.py`)
- **Endpoint**: `GET /api/user/reputation/{user_id}`
- **FastAPI Patterns**: Follow existing endpoint conventions
- **Error Handling**: Comprehensive validation and HTTP status codes
- **Response Models**: Pydantic models for type safety

### **3. Redis Caching Layer**
- **Cache Keys**: `reputation:user:{user_id}` pattern
- **TTL Strategy**: 5-minute cache with background refresh
- **Fallback**: Direct database query when Redis unavailable
- **Invalidation**: Manual cache busting for testing/admin

---

## 📊 **DATABASE QUERY STRATEGY**

### **Session Status Classification**
```sql
-- Completed sessions (user participated successfully)
status IN ('completed') 
AND (user1_completed_confirmed_by_user2 = true OR user2_completed_confirmed_by_user1 = true)

-- No-show sessions (user failed to participate)  
status IN ('no_show', 'cancelled') 
AND user was the cause of no-show
```

### **User Participation Detection**
```sql
-- Find sessions where user_id is a participant
SELECT ws.* FROM wingman_sessions ws
JOIN wingman_matches wm ON ws.match_id = wm.id
WHERE wm.user1_id = $user_id OR wm.user2_id = $user_id
```

---

## 🎨 **BADGE COLOR LOGIC**

### **Score Ranges**
- **🥇 Gold Badge**: Score ≥ 10 (excellent reputation)
- **🟢 Green Badge**: Score ≥ 0 (good reputation)  
- **🔴 Red Badge**: Score < 0 (needs improvement)

### **Business Rules**
- New users start at score 0 (green badge)
- Minimum bound: -5 (prevents infinite negative scores)
- Maximum bound: +20 (caps positive scores)
- Badge updates in real-time as sessions complete

---

## 🚀 **IMPLEMENTATION TASKS**

### ✅ **Task 1: Reputation Service Foundation**
- [ ] Create `src/services/reputation_service.py`
- [ ] Implement ReputationData dataclass
- [ ] Implement ReputationCalculator with score logic
- [ ] Add database query methods for session history
- [ ] Implement badge color calculation
- [ ] Add comprehensive error handling

### ✅ **Task 2: Redis Caching Integration** 
- [ ] Implement reputation-specific Redis cache functions
- [ ] Add cache key patterns: `reputation:user:{user_id}`
- [ ] Implement 5-minute TTL with graceful fallback
- [ ] Add cache invalidation for testing/admin use
- [ ] Follow existing Redis patterns from challenges system

### ✅ **Task 3: FastAPI Endpoint Implementation**
- [ ] Add reputation endpoint to `src/main.py`
- [ ] Create Pydantic response models
- [ ] Implement user validation and error handling
- [ ] Add comprehensive logging for debugging
- [ ] Follow established FastAPI patterns

### ✅ **Task 4: Database Integration**
- [ ] Implement efficient wingman_sessions queries
- [ ] Add user participation filtering logic
- [ ] Optimize queries for performance
- [ ] Handle edge cases (new users, no sessions)
- [ ] Add database error handling

### ✅ **Task 5: Testing & Validation**
- [ ] Unit tests for ReputationCalculator
- [ ] Integration tests for database queries
- [ ] Cache behavior validation
- [ ] API endpoint testing
- [ ] Edge case validation

---

## 🔒 **SECURITY & VALIDATION**

### **Input Validation**
- UUID format validation for user_id
- User existence validation
- Rate limiting consideration
- Authentication bypass for development

### **Data Privacy**
- Return aggregated scores only (no sensitive session details)
- Respect user privacy in session data access
- Follow existing RLS patterns if applicable

---

## ⚡ **PERFORMANCE CONSIDERATIONS**

### **Database Optimization**
- Use existing indexes on wingman_sessions
- Minimize JOIN operations where possible
- Consider query result caching for heavy users
- Implement pagination if session history is large

### **Redis Strategy**
- 5-minute TTL balances freshness with performance
- Background refresh prevents cache stampede
- Graceful fallback ensures reliability
- Monitor cache hit rates for optimization

---

## 🧪 **TESTING STRATEGY**

### **Unit Testing**
- ReputationCalculator score computation
- Badge color logic validation  
- Edge cases (bounds checking, new users)
- Error handling scenarios

### **Integration Testing**
- Database query accuracy
- Redis caching behavior
- API endpoint responses
- Cache invalidation workflows

### **Performance Testing**
- Query execution time measurement
- Cache performance validation
- Concurrent request handling
- Memory usage monitoring

---

## 🔄 **DEPLOYMENT CONSIDERATIONS**

### **Feature Rollout**
- Create new service without modifying existing code
- Add endpoint following established patterns
- Enable gradual testing with cache warming
- Monitor performance impact

### **Monitoring**
- Track API response times
- Monitor cache hit/miss rates
- Log reputation calculation patterns
- Alert on database query performance

---

## 📝 **SUCCESS CRITERIA**

### **Functional Requirements**
- ✅ Accurate reputation score calculation
- ✅ Proper badge color assignment
- ✅ 5-minute Redis caching with fallback
- ✅ Complete API endpoint with validation
- ✅ Comprehensive error handling

### **Performance Requirements**
- API response time < 100ms (with cache)
- Database fallback < 500ms
- Cache hit rate > 80%
- No impact on existing endpoint performance

### **Integration Requirements**
- Frontend can consume API without modification
- Follows existing FastAPI patterns
- Compatible with current Redis infrastructure
- Maintains existing security patterns

---

## 🔄 **TASK STATUS TRACKING**

**Created**: 2025-08-17  
**Status**: PLANNING COMPLETE - READY FOR IMPLEMENTATION  
**Next Step**: Task 1 - Reputation Service Foundation

**Estimated Implementation Time**: 2-3 hours  
**Risk Level**: LOW (new feature, no existing code modification)  
**Dependencies**: Existing Redis infrastructure, wingman_sessions table