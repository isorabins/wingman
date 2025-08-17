# Task 16: Reputation System Implementation Plan

## Executive Summary

Implementation of a comprehensive reputation system for WingmanMatch with GET /api/user/reputation/[userId] endpoint, Redis caching, and UI badges. Uses domain-based approach for optimal parallel execution.

## Technology Stack Analysis

- **Backend**: FastAPI with async patterns, existing src/main.py structure
- **Database**: Supabase PostgreSQL with wingman_sessions table
- **Caching**: Redis with existing RedisSession infrastructure
- **Frontend**: Next.js with Chakra UI, existing Badge component patterns
- **Testing**: Pytest backend, Vitest frontend

## Domain-Based Architecture Strategy

### Backend Domain (API & Business Logic)
- **Scope**: Reputation calculation, caching, API endpoint
- **Files**: `src/services/reputation_service.py`, `src/main.py` (new endpoint)
- **Dependencies**: wingman_sessions table, Redis infrastructure

### Frontend Domain (UI Components & Integration)  
- **Scope**: Badge components, integration in match cards/chat headers
- **Files**: `components/ReputationBadge.tsx`, updated pages
- **Dependencies**: Chakra UI Badge, API client patterns

### Testing Domain (Quality Assurance)
- **Scope**: API tests, UI tests, integration tests
- **Files**: Test files for both domains
- **Dependencies**: Existing test infrastructure

## Implementation Plan

### Phase 1: Backend Foundation (Domain: API & Business Logic)
**Agent**: @backend-developer
**Estimated Time**: 2-3 hours

#### 1.1 Create Reputation Service
**File**: `src/services/reputation_service.py`
```python
class ReputationService:
    @staticmethod
    async def calculate_reputation_score(user_id: str) -> ReputationData
    @staticmethod 
    async def get_reputation_with_cache(user_id: str) -> ReputationData
    @staticmethod
    async def invalidate_reputation_cache(user_id: str) -> None
```

**Business Logic**:
- Query wingman_sessions for completed_sessions and no_shows by user
- Calculate: score = completed_sessions - no_shows
- Apply bounds: max(min(score, 20), -5)
- Include totals for transparency

#### 1.2 Add API Endpoint  
**File**: `src/main.py` (new endpoint)
```python
@app.get("/api/user/reputation/{user_id}")
async def get_user_reputation(user_id: str) -> ReputationResponse
```

**Patterns to Follow**:
- Use existing async patterns from src/main.py
- Follow auth middleware patterns
- Error handling consistent with existing endpoints
- Response models using Pydantic

#### 1.3 Redis Caching Integration
**Implementation**:
- Use existing RedisSession class from src/redis_session.py
- 5-minute TTL per requirement
- Cache key pattern: `reputation:{user_id}`
- Graceful fallback when Redis unavailable

### Phase 2: Frontend Components (Domain: UI & UX)
**Agent**: @frontend-developer 
**Estimated Time**: 2-3 hours

#### 2.1 Create Reputation Badge Component
**File**: `components/ReputationBadge.tsx`
```typescript
interface ReputationBadgeProps {
  score: number;
  completedSessions: number;
  noShows: number;
  size?: 'sm' | 'md' | 'lg';
  showDetails?: boolean;
}
```

**Badge Color Logic**:
- Green (colorScheme="green"): score >= 5
- Gold (colorScheme="yellow"): score 1-4  
- Red (colorScheme="red"): score <= 0

**Design Requirements**:
- Follow existing Chakra Badge patterns from find-buddy/page.tsx
- Responsive design with size variants
- Tooltip with detailed stats
- Accessibility compliant (ARIA labels)

#### 2.2 Integration Points
**Files to Update**:
- `app/find-buddy/page.tsx`: Add badges to match cards
- `app/buddy-chat/[matchId]/page.tsx`: Add badge to chat header

**Integration Pattern**:
- Fetch reputation data via API call
- Show loading state during fetch
- Graceful error handling with fallback UI
- Follow existing async data patterns

### Phase 3: Testing & Quality Assurance (Domain: Validation)
**Agent**: @code-reviewer
**Estimated Time**: 1-2 hours

#### 3.1 Backend API Tests
**File**: `tests/backend/test_reputation_api.py`
- Test users with different session histories
- Cache hit/miss scenarios  
- Error cases (user not found, Redis down)
- Score calculation accuracy
- Boundary conditions (-5, +20 limits)

#### 3.2 Frontend UI Tests  
**File**: `tests/unit/reputation-badge.test.tsx`
- Badge color logic for all score ranges
- Component rendering with different props
- Tooltip functionality
- Accessibility compliance (screen readers)

#### 3.3 Integration Tests
**File**: `tests/e2e/reputation-integration.spec.ts`
- End-to-end reputation display flow
- Cache invalidation on session updates
- Real API integration testing

## Execution Strategy

### Parallel Execution Plan (Maximum 2 Agents)

**Phase 1 (Parallel)**: 
- Agent 1: @backend-developer - Reputation service + API endpoint
- Agent 2: @frontend-developer - Badge component creation

**Phase 2 (Sequential)**:
- Agent 1: @backend-developer - Complete API integration  
- Agent 2: @frontend-developer - Page integrations

**Phase 3 (Parallel)**:
- Agent 1: @code-reviewer - Backend testing
- Agent 2: @frontend-developer - Frontend testing

### Dependencies Management

**Backend Dependencies**:
- ✅ wingman_sessions table exists
- ✅ Redis infrastructure available
- ✅ FastAPI patterns established

**Frontend Dependencies**:  
- ✅ Chakra UI Badge component available
- ✅ Next.js API client patterns established
- ✅ Existing page structures for integration

**No Blocking Dependencies**: All domains can work in parallel

## Data Models

### Database Query
```sql
SELECT 
  user_id,
  COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_sessions,
  COUNT(CASE WHEN status = 'no_show' THEN 1 END) as no_shows
FROM wingman_sessions ws
JOIN wingman_matches wm ON ws.match_id = wm.id
WHERE wm.user1_id = $1 OR wm.user2_id = $1
GROUP BY user_id;
```

### API Response Model
```python
class ReputationResponse(BaseModel):
    user_id: str
    score: int  # -5 to +20
    completed_sessions: int
    no_shows: int
    last_updated: datetime
    cache_hit: bool
```

### Frontend Badge Props
```typescript
interface ReputationData {
  score: number;
  completedSessions: number; 
  noShows: number;
  lastUpdated: string;
}
```

## Performance Considerations

### Caching Strategy
- **TTL**: 5 minutes as specified
- **Cache Key**: `reputation:{user_id}`
- **Invalidation**: Manual trigger on session status updates
- **Fallback**: Direct DB query if Redis unavailable

### Database Optimization
- **Existing Indexes**: Leverage wingman_sessions indexes on match_id, status
- **Query Efficiency**: Single aggregation query per user
- **Connection Pooling**: Use existing Supabase client patterns

## Security & Privacy

### Data Access
- **RLS Policies**: Leverage existing wingman_sessions RLS policies
- **Authentication**: Require valid JWT for reputation access
- **Authorization**: Users can only view public reputation data

### Privacy Protection
- **Public Data**: Score and session counts only
- **No Personal Info**: No session details or personal identifiers
- **Anonymization**: Aggregate statistics only

## Testing Strategy

### Backend Testing
1. **Unit Tests**: Reputation calculation logic
2. **Integration Tests**: Database queries with test data
3. **Performance Tests**: Cache hit rates and query speed
4. **Error Handling**: Redis failures, DB connection issues

### Frontend Testing  
1. **Component Tests**: Badge rendering and color logic
2. **Integration Tests**: API data fetching and display
3. **Accessibility Tests**: Screen reader compatibility
4. **Visual Tests**: Badge appearance across different scores

### End-to-End Testing
1. **User Journey**: Complete reputation display flow
2. **Cache Behavior**: Verify 5-minute TTL and invalidation
3. **Real Data**: Test with various user reputation scenarios

## Deployment Checklist

### Backend Deployment
- [ ] Environment variables for Redis configured
- [ ] Database indexes verified on wingman_sessions
- [ ] API endpoint documented and tested
- [ ] Monitoring and logging added

### Frontend Deployment  
- [ ] Component exported and documented
- [ ] Integration points tested
- [ ] Responsive design verified
- [ ] Accessibility compliance confirmed

## Success Metrics

### Functional Requirements
- ✅ GET /api/user/reputation/[userId] responds in <200ms
- ✅ Score calculation: completed_sessions - no_shows  
- ✅ Score bounds: [-5, +20] enforced
- ✅ 5-minute Redis caching operational
- ✅ UI badges display correct colors (green/gold/red)

### Quality Requirements
- ✅ 100% test coverage for reputation logic
- ✅ Zero breaking changes to existing code
- ✅ WCAG 2.1 AA accessibility compliance
- ✅ Mobile responsive badge display

## Risk Mitigation

### Technical Risks
- **Redis Downtime**: Graceful fallback to direct DB queries
- **Database Load**: Efficient queries with existing indexes  
- **Cache Inconsistency**: Manual invalidation triggers

### Business Risks
- **Score Manipulation**: Validate session status updates
- **Privacy Concerns**: Only expose aggregate public data
- **Performance Impact**: Monitor query performance

## Future Enhancements

### Phase 2 Features (Out of Scope)
- Reputation trend analysis
- Detailed session history
- Reputation-based matching weights
- Community feedback integration

### Scalability Considerations
- Redis cluster for high availability
- Database read replicas for reputation queries
- CDN caching for static badge assets
- Real-time reputation updates via WebSockets

---

**Next Steps**: Execute Phase 1 with @backend-developer and @frontend-developer in parallel, followed by sequential Phase 2 integration and Phase 3 testing.
