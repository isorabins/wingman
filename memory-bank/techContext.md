# Technical Context: WingmanMatch

## Technology Stack

### Backend Architecture
- **Framework**: FastAPI (Python)
- **AI Engine**: Anthropic Claude 3.5 Sonnet via direct API integration
- **Database**: Supabase PostgreSQL with real-time capabilities
- **Assessment System**: ConfidenceTestAgent with archetype scoring
- **Agent Framework**: BaseAgent inheritance pattern for conversational agents

### Frontend Architecture (Planned)
- **Framework**: Next.js with React
- **API Integration**: REST API calls to FastAPI backend
- **Assessment UI**: Interactive confidence assessment interface
- **User Dashboard**: Profile management and progress tracking

### Infrastructure
- **Backend Hosting**: TBD (Development on local/cloud)
- **Database**: Supabase with WingmanMatch schema
- **Authentication**: Supabase Auth with user profile management
- **AI Integration**: Direct Claude API for coaching and assessment

## Development Setup

### Environment Setup

#### Project Structure (Post-Task 5)
```
/Applications/wingman/
├── src/
│   ├── agents/
│   │   ├── base_agent.py           # Shared agent functionality
│   │   └── confidence_agent.py     # Dating confidence assessment
│   ├── assessment/
│   │   └── confidence_scoring.py   # Pure scoring functions
│   ├── main.py                     # FastAPI application
│   ├── database.py                 # Database utilities
│   ├── prompts.py                  # AI prompts and templates
│   └── simple_memory.py           # Conversation memory system
├── supabase/
│   └── migrations_wm/
│       ├── 001_add_wingman_tables.sql
│       └── 002_add_confidence_test_progress.sql
├── tests/
│   ├── test_confidence_agent_basic.py
│   ├── test_confidence_scoring.py
│   └── test_prompts.py
└── memory-bank/                   # Project documentation
```

#### Quick Setup
```bash
# 1. Environment setup
cd /Applications/wingman
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# 2. Database setup
supabase db reset  # Apply all migrations

# 3. Environment variables (.env)
ANTHROPIC_API_KEY=sk-ant-...
SUPABASE_URL=your-supabase-url
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-key

# 4. Run tests
python -m pytest tests/ -v

# 5. Start development server
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

#### Testing Commands
```bash
# Assessment system tests
python -m pytest tests/test_confidence_scoring.py -v
python -m pytest tests/test_confidence_agent_basic.py -v

# Quick validation
python test_confidence_simple.py

# All tests
python -m pytest tests/ -v
```

### Backend Development Commands

#### Development Server
```bash
# Development with auto-reload
uvicorn src.main:app --reload --port 8000

# Production server (when ready)
uvicorn src.main:app --host 0.0.0.0 --port 8000
```

#### Database Operations
```bash
# Apply migrations
supabase db reset

# Check migration status
supabase migration list

# Generate new migration
supabase migration new migration_name

# Verify schema
python scripts/db/verify_wm_schema.sql
```

#### Assessment Testing
```bash
# Test confidence scoring
python -c "
from src.assessment.confidence_scoring import *
responses = {'question_1': 'A', 'question_2': 'B'}
scores = score_responses(responses)
print('Scores:', scores)
print('Primary:', determine_primary_archetype(scores))
"

# Test agent flow
python test_confidence_simple.py
```

## Database Schema

### Core Tables (Task 5 Complete)

#### User Management
```sql
-- User profiles (base table)
user_profiles (
    id UUID PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    first_name TEXT,
    last_name TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
)
```

#### Assessment System
```sql
-- Confidence test results
confidence_test_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES user_profiles(id) ON DELETE CASCADE,
    test_responses JSONB NOT NULL,        -- {"question_1": "A", "question_2": "B", ...}
    archetype_scores JSONB NOT NULL,      -- {"Analyzer": 0.8, "Sprinter": 0.3, ...}
    assigned_archetype TEXT NOT NULL,     -- Primary archetype name
    experience_level TEXT NOT NULL,       -- beginner/intermediate/advanced
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
)

-- Assessment progress tracking
confidence_test_progress (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES user_profiles(id) ON DELETE CASCADE,
    thread_id TEXT NOT NULL,
    flow_step TEXT NOT NULL DEFAULT 'start',
    current_responses JSONB DEFAULT '{}',
    completion_percentage INTEGER DEFAULT 0,
    is_completed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
)
```

#### Buddy System (Planned)
```sql
-- Buddy matches (future implementation)
buddy_matches (
    id UUID PRIMARY KEY,
    user1_id UUID REFERENCES user_profiles(id),
    user2_id UUID REFERENCES user_profiles(id),
    match_score FLOAT,
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
)

-- Challenges and progress (future implementation)
challenges (
    id UUID PRIMARY KEY,
    challenge_name TEXT NOT NULL,
    difficulty_level TEXT NOT NULL,
    description TEXT
)
```

### Key Relationships
```sql
user_profiles (1) -> (many) confidence_test_results
user_profiles (1) -> (many) confidence_test_progress
user_profiles (1) -> (many) buddy_matches (as user1 or user2)
```

## API Endpoints (Current & Planned)

### Current Endpoints (Task 5 Ready)
```python
# Health check
GET /health

# Assessment endpoints (ready for implementation)
POST /api/assessment/confidence/start     # Start new assessment
POST /api/assessment/confidence/answer    # Submit answer and get next question
GET /api/assessment/confidence/results/{user_id}  # Get results

# User management
POST /api/users/register                  # Create user profile
GET /api/users/profile/{user_id}         # Get user profile
```

### Planned Endpoints (Future Tasks)
```python
# Buddy matching
GET /api/buddies/matches/{user_id}       # Get potential matches
POST /api/buddies/request                # Request buddy partnership
POST /api/buddies/accept/{match_id}      # Accept buddy request

# Challenges
GET /api/challenges/available/{user_id}  # Get appropriate challenges
POST /api/challenges/complete            # Mark challenge complete

# Coaching
POST /api/coaching/chat                  # AI coaching conversation
GET /api/coaching/history/{user_id}      # Coaching conversation history
```

## Dependencies

### Core Python Packages
```
fastapi==0.104.1
uvicorn==0.24.0
supabase==2.3.0
anthropic==0.7.7
python-dotenv==1.0.0
pytest==7.4.3
python-multipart==0.0.6
```

### Assessment System Dependencies
```
# Already included in core packages
- fastapi (for API endpoints)
- supabase (for database operations)
- anthropic (for Claude API integration)
- pytest (for testing framework)
```

### Development Tools
```
python-dotenv==1.0.0
pytest==7.4.3
black==23.11.0
flake8==6.1.0
```

## Architecture Overview (Post-Task 5)

### Implemented Components ✅
1. **BaseAgent Pattern**: Shared functionality for all conversational agents
2. **ConfidenceTestAgent**: 12-question dating confidence assessment
3. **Scoring System**: Pure functions for archetype calculation
4. **Database Schema**: Assessment results and progress tracking
5. **Testing Framework**: Unit and integration tests

### Ready for Implementation 🟡
1. **FastAPI Endpoints**: Assessment API integration
2. **Frontend Interface**: Next.js UI for assessment flow
3. **User Authentication**: Supabase Auth integration

### Future Development 🔴
1. **Buddy Matching Algorithm**: Geographic and compatibility-based pairing
2. **Challenge System**: Structured confidence-building exercises
3. **Session Coordination**: Meetup planning and tracking
4. **Advanced Analytics**: User progress and system performance

## Technical Constraints

### Performance Requirements
- API response time: <2 seconds for assessment questions
- Database queries: Optimized with proper indexing on user_id and thread_id
- Memory usage: Efficient JSONB storage for assessment data
- Scalability: Pure functions enable easy caching and parallelization

### Security Requirements
- Environment variables for all secrets (ANTHROPIC_API_KEY, Supabase keys)
- Database row-level security for user data
- Input validation for assessment answers (A-F validation)
- PII protection in assessment responses

### Assessment System Constraints
- 12 questions maximum per assessment
- 6 archetype options (A-F) per question
- Progress tracking for session resume capability
- Experience level calculation based on engagement scores

## Development Patterns

### Agent Development Pattern
```python
# 1. Inherit from BaseAgent
class NewAgent(BaseAgent):
    def __init__(self, supabase_client, user_id: str):
        super().__init__(supabase_client, user_id)
        self.agent_specific_config = {}

# 2. Implement process_message
async def process_message(self, thread_id: str, message: str):
    # Agent-specific logic
    pass

# 3. Add to main.py endpoints
agent = NewAgent(supabase_client, user_id)
response = await agent.process_message(thread_id, message)
```

### Testing Pattern
```python
# 1. Unit tests for pure functions
def test_scoring_function():
    result = score_responses(sample_responses)
    assert isinstance(result, dict)

# 2. Integration tests for agents
async def test_agent_flow():
    agent = ConfidenceTestAgent(supabase_client, test_user_id)
    response = await agent.process_message(thread_id, "start")
    assert "Question 1" in response
```

### Database Pattern
```python
# 1. Auto-dependency creation
await self.ensure_user_profile()

# 2. JSONB for flexible data
current_responses = {'question_1': 'A', 'question_2': 'B'}

# 3. Upsert for progress tracking
.upsert(progress_data, on_conflict='user_id,thread_id')
```

## Known Technical Limitations

### Current Constraints (Post-Task 7)
- Single-threaded assessment processing (acceptable for MVP)
- No real-time progress updates (polling-based for now)
- Buddy matching algorithm not yet implemented
- No real-time chat features (future Task 11)

### Development Environment
- Local development only (no staging/production environments yet)
- Supabase for database and storage (development instance)
- Manual testing against development database
- E2E testing framework operational with Playwright

### Future Considerations
- Geographic buddy matching algorithm needs implementation
- Real-time chat features may need WebSocket implementation
- Mobile app considerations for on-the-go challenge completion
- Cost optimization for Claude API usage at scale
- Machine learning compatibility algorithms (advanced feature)

---

**🎯 STATUS: PROFILE SETUP COMPLETE - READY FOR BUDDY MATCHING DEVELOPMENT**

*Task 7 complete: Full profile setup system operational with photo upload, location privacy, comprehensive form validation, and security measures. Users can now complete profiles and are ready for buddy matching implementation.*