# Dating Goals Backend System Implementation Plan

## Task 18: Complete Dating Goals System Backend

**Domain**: Backend Development
**Owner**: backend-developer
**Status**: Planning

## Problem Analysis

WingmanMatch needs a dating goals system that transforms the project planning flow into dating confidence coaching. The system must capture user goals for confidence building and integrate them into the AI coach's memory context.

## Requirements Summary

1. **Agent Implementation**: Adapt project planning agent for dating goals context
2. **Database Schema**: Create `dating_goals` table with proper schema
3. **API Endpoints**: Implement `/api/dating-goals` CRUD operations
4. **Memory Integration**: Store goals in AI coach context
5. **Data Transformation**: Convert project fields to dating confidence fields

## Technical Architecture

### 1. Agent Implementation
- **Source**: `reference_files/src/agents/project_overview_agent.py` (8 topics)
- **Target**: `src/agents/wingman_profile_agent.py` (4 topics, dating focused)
- **Pattern**: Keep BaseAgent inheritance, adapt topics and prompts

### 2. Database Schema Design
```sql
-- dating_goals table (matching project_overview structure)
CREATE TABLE dating_goals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES user_profiles(id) ON DELETE CASCADE,
    goals_name TEXT NOT NULL,           -- Primary confidence goal
    goals_type TEXT NOT NULL,           -- Type: approach, conversation, apps, etc.
    description TEXT,                   -- Detailed goal description
    current_phase TEXT DEFAULT 'Planning',
    goals JSONB,                        -- Array of specific goals
    challenges JSONB,                   -- Array of current challenges
    success_metrics JSONB,              -- Success measurement criteria
    creation_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### 3. API Endpoints
```python
# Core CRUD operations
POST /api/dating-goals         # Create/update dating goals
GET /api/dating-goals/{user_id} # Retrieve user's goals
PUT /api/dating-goals/{user_id} # Update existing goals
DELETE /api/dating-goals/{user_id} # Delete goals (admin only)
```

### 4. Memory Integration
- Goals data added to conversation context
- Coach references specific user goals during coaching
- Progress tracking integration with existing memory system

## Implementation Tasks

### Phase 1: Agent Adaptation ✅ (ALREADY EXISTS)
- [x] **Copy and simplify**: `wingman_profile_agent.py` already exists
- [x] **Topic transformation**: 8 project topics → 4 dating confidence topics
- [x] **Prompt adaptation**: Creative project → dating confidence context
- [x] **Field mapping**: Project fields → dating confidence fields

### Phase 2: Database Implementation
- [ ] **Migration creation**: Create dating_goals table
- [ ] **Schema validation**: Ensure proper foreign keys and constraints
- [ ] **Index optimization**: Performance indexes for user_id queries

### Phase 3: API Implementation
- [ ] **FastAPI routes**: Implement CRUD endpoints
- [ ] **Pydantic models**: Request/response validation
- [ ] **Error handling**: Comprehensive validation and error responses
- [ ] **Authentication**: User authorization and access control

### Phase 4: Memory Integration
- [ ] **Context formatter**: Add goals to conversation context
- [ ] **Simple memory**: Integration with existing memory system
- [ ] **Coach awareness**: Ensure AI references user goals appropriately

### Phase 5: Testing & Validation
- [ ] **Unit tests**: Test individual components
- [ ] **Integration tests**: End-to-end workflow testing
- [ ] **API testing**: Comprehensive endpoint validation
- [ ] **Memory testing**: Verify context integration

## Data Transformation Mapping

### Project → Dating Goals Fields
```python
# Field mapping transformation
project_overview → dating_goals:
{
    "project_name" → "goals_name",           # "Approach Confidence" 
    "project_type" → "goals_type",           # "approach", "conversation", "apps"
    "description" → "description",           # Goal description
    "goals" → "goals",                       # Array of specific targets
    "challenges" → "challenges",             # Array of obstacles
    "success_metrics" → "success_metrics"    # Success criteria
}
```

### Topic Structure (4 Topics)
```python
TOPICS = [
    {1: "Dating Confidence Goals & Targets"},     # What to improve
    {2: "Past Attempts & Learning"},               # Previous efforts  
    {3: "Triggers & Comfort Zones"},               # Anxiety situations
    {4: "Next Steps & Action Plan"}                # Immediate actions
]
```

## Integration Points

### 1. Memory System Integration
```python
# Add goals context to conversation memory
memory_context = {
    "dating_goals": user_goals_data,
    "confidence_targets": goals.get("goals", []),
    "known_challenges": goals.get("challenges", [])
}
```

### 2. API Integration
```python
# Frontend integration contract
POST /api/dating-goals:
{
    "goals_name": "Approach Confidence",
    "goals_type": "approach", 
    "description": "Build confidence approaching women in social settings",
    "goals": ["Start conversations", "Overcome approach anxiety"],
    "challenges": ["Fear of rejection", "Social anxiety"],
    "success_metrics": {"weekly_approaches": 3, "comfort_level": 8}
}
```

## Success Criteria

### Functional Requirements
- [ ] Agent conducts 4-topic dating confidence conversation
- [ ] Goals stored in dating_goals table with proper structure
- [ ] API endpoints provide full CRUD functionality
- [ ] Memory system includes goals in conversation context
- [ ] Coach references user goals during conversations

### Technical Requirements
- [ ] Database migration applies cleanly
- [ ] API follows FastAPI patterns from existing codebase
- [ ] Memory integration uses existing SimpleMemory patterns
- [ ] Error handling and validation comprehensive
- [ ] Performance optimized with proper indexing

### Quality Requirements
- [ ] Unit test coverage >90%
- [ ] Integration tests cover complete workflow
- [ ] API documentation complete
- [ ] Security validation (authentication, authorization)
- [ ] Performance acceptable (<2s response times)

## Risk Mitigation

### Technical Risks
1. **Database conflicts**: Ensure proper foreign keys and constraints
2. **Memory integration**: Test context formatting thoroughly
3. **API consistency**: Follow existing FastAPI patterns exactly
4. **Agent behavior**: Validate conversation flow works smoothly

### Implementation Risks  
1. **Existing code conflicts**: Agent file already exists - need to validate current state
2. **Schema conflicts**: Ensure dating_goals table doesn't conflict with existing tables
3. **Memory conflicts**: Verify goals context doesn't interfere with other data

## Implementation Timeline

### Phase 1: Analysis & Setup (30 min)
- Analyze existing wingman_profile_agent.py
- Verify current implementation state
- Plan adaptation strategy

### Phase 2: Database & Migration (45 min)
- Create dating_goals table migration
- Test schema compatibility
- Verify foreign key relationships

### Phase 3: API Implementation (60 min)
- Implement CRUD endpoints
- Add Pydantic models
- Test API functionality

### Phase 4: Memory Integration (30 min)
- Add goals to conversation context
- Test coach awareness
- Validate integration

### Phase 5: Testing & Documentation (45 min)
- Write comprehensive tests
- Document API endpoints
- Validate complete workflow

**Total Estimated Time**: 3.5 hours

## MVP Delivery

**Minimum Viable Product includes:**
1. Working dating goals agent with 4-topic conversation
2. Database table storing goals data
3. Basic API endpoints (POST, GET)
4. Memory integration showing coach awareness of goals
5. Basic test coverage validating functionality

**Future enhancements:**
- Advanced goal tracking and progress measurement
- Goal achievement notifications
- Integration with challenge system
- Analytics and reporting on goal progress