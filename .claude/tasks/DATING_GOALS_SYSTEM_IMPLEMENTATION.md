# Dating Goals System Implementation Plan

**BACKEND DOMAIN: Complete Dating Goals System**
**Task**: Transform project planning flow into dating confidence coaching
**Domain Owner**: backend-developer

## 📋 DOMAIN ANALYSIS

### Current System Architecture
- **Stack Detected**: FastAPI with Python 3.10+, async-first architecture
- **Database**: Supabase PostgreSQL with auto-dependency creation patterns  
- **AI Integration**: Direct Anthropic Claude API (Connell Barrett coaching persona)
- **Memory System**: WingmanMemory class with conversation context
- **Agent Pattern**: BaseAgent → specialized agent inheritance

### Target Transformation
- **Source**: `reference_files/src/agents/project_overview_agent.py` (8-topic creative project flow)
- **Target**: Dating goals agent for confidence building context
- **New Table**: `dating_goals` (already exists in schema!)
- **New Route**: `/api/dating-goals` (separate from existing project-overview route)

## 🎯 IMPLEMENTATION PLAN

### Phase 1: Agent Creation & Adaptation
**Files to Create/Modify:**
- `src/agents/wingman_profile_agent.py` - Copy and adapt from project_overview_agent.py
- Simplify 8 topics → 3-4 dating confidence topics
- Transform project planning prompts → dating coaching prompts

**Topic Transformation:**
```python
DATING_TOPICS = [
    {
        "topic_number": 1,
        "title": "Dating Confidence Goals & Targets",
        "description": "Understanding your dating confidence building objectives",
        "key_questions": [
            "What specific areas of dating confidence do you want to improve?",
            "What situations make you feel most nervous when meeting someone new?",
            "What would success look like for your dating confidence?"
        ],
        "completion_indicators": ["confidence_targets", "anxiety_triggers", "success_definition"]
    },
    {
        "topic_number": 2, 
        "title": "Past Attempts & Learning",
        "description": "Understanding your dating experience and previous efforts",
        "key_questions": [
            "What have you tried before to build dating confidence?",
            "What worked well and what didn't?",
            "What patterns do you notice in your dating experiences?"
        ],
        "completion_indicators": ["past_attempts", "successful_strategies", "identified_patterns"]
    },
    {
        "topic_number": 3,
        "title": "Triggers & Comfort Zones", 
        "description": "Identifying specific situations and comfort levels",
        "key_questions": [
            "What situations trigger your dating anxiety most?",
            "Where do you feel most comfortable meeting new people?",
            "What venues or activities feel approachable to you?"
        ],
        "completion_indicators": ["anxiety_triggers", "comfort_venues", "preferred_activities"]
    },
    {
        "topic_number": 4,
        "title": "Support & Accountability Goals",
        "description": "Planning your wingman partnership approach",
        "key_questions": [
            "What kind of support would help you most?", 
            "How do you want your wingman to hold you accountable?",
            "What would be a good first challenge to try together?"
        ],
        "completion_indicators": ["support_needs", "accountability_style", "first_challenges"]
    }
]
```

### Phase 2: Database Integration
**Existing Schema** (from migrations_wm/001_add_wingman_tables.sql):
```sql
CREATE TABLE "public"."dating_goals" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "user_id" "uuid" NOT NULL,
    "goals" "text",
    "preferred_venues" "text"[],
    "comfort_level" VARCHAR(50) DEFAULT 'moderate',
    "created_at" TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    "updated_at" TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

**Enhancement Needed:**
- Add JSON fields for structured goals data (targets, triggers, past_attempts)
- Match project_overview table structure for consistency

### Phase 3: FastAPI Route Implementation  
**New Endpoint**: `/api/dating-goals`
- GET `/api/dating-goals/{user_id}` - Retrieve user's dating goals
- POST `/api/dating-goals` - Create/update dating goals
- Follow existing patterns from src/main.py

**Pydantic Models:**
```python
class DatingGoalsRequest(BaseModel):
    user_id: UUID
    goals: Dict[str, Any]
    preferred_venues: List[str] = []
    comfort_level: str = "moderate"

class DatingGoalsResponse(BaseModel):
    success: bool
    dating_goals_id: Optional[UUID] = None
    message: str
```

### Phase 4: Memory Integration
**WingmanMemory Enhancement:**
- Add method: `get_dating_goals_context(user_id)` 
- Integrate goals data into AI coaching context
- Update context formatting to include confidence targets and triggers

**Context Integration:**
```python
async def format_coaching_context(self, user_id: str) -> str:
    """Format context including dating goals for AI coaching"""
    base_context = await self.get_conversation_context(user_id)
    goals_context = await self.get_dating_goals_context(user_id)
    
    return f"""
    {base_context}
    
    Dating Goals Context:
    {goals_context}
    """
```

### Phase 5: AI Coaching Integration
**Claude Agent Updates:**
- Modify prompts to reference stored dating goals
- Enable Connell Barrett coaching to use goals context
- Personalize coaching based on triggers and comfort levels

## 📋 TODOWRITE TASK LIST

### ✅ COMPLETED TASKS
- [x] Domain analysis and architecture review
- [x] Implementation plan creation
- [x] Topic structure design for dating confidence

### 🔄 IN PROGRESS TASKS  
- [ ] Create wingman_profile_agent.py from project_overview_agent.py
- [ ] Transform 8 project topics → 4 dating confidence topics
- [ ] Update prompts for Connell Barrett dating coaching context

### 📋 PENDING TASKS
- [ ] Enhance dating_goals table schema with JSON fields
- [ ] Create FastAPI /api/dating-goals endpoint
- [ ] Add Pydantic models for request/response validation
- [ ] Update WingmanMemory with goals context methods
- [ ] Integrate goals data into AI coaching prompts
- [ ] Test complete goals capture → coaching context flow
- [ ] Create comprehensive test suite
- [ ] Update memory-bank documentation

## 🚀 SUCCESS CRITERIA

### Technical Deliverables
- [x] Complete wingman profile agent implementation
- [ ] Functional /api/dating-goals API endpoint
- [ ] Enhanced dating_goals database schema  
- [ ] Memory integration for coaching context
- [ ] AI coaching personalization based on goals

### Quality Metrics
- [ ] 100% test coverage for new functionality
- [ ] All endpoints follow established FastAPI patterns
- [ ] Database operations use auto-dependency creation
- [ ] Memory integration seamless with existing conversation flow
- [ ] AI coaching references user goals naturally

### Integration Contract
**API Endpoint**: `/api/dating-goals`
**Data Format**: JSON with targets, triggers, past_attempts
**Response Format**: Standard success/error with goal IDs
**Memory Integration**: Goals automatically available in coaching context

## ⚡ NEXT IMMEDIATE ACTION
Start with Phase 1: Copy reference_files/src/agents/project_overview_agent.py → src/agents/wingman_profile_agent.py and begin topic transformation for dating confidence coaching.