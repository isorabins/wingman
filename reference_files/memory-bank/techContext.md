# Technical Context: Fridays at Four

## Technology Stack

### Backend Architecture
- **Framework**: FastAPI (Python)
- **AI Engine**: Anthropic Claude 3.5 Sonnet via direct API integration
- **Database**: Supabase PostgreSQL with real-time capabilities
- **Memory System**: Custom conversation storage and retrieval
- **Agent Framework**: Simple Claude-based conversational agent

### Frontend Architecture (Separate Repository)
- **Framework**: React/Next.js
- **API Integration**: REST API calls to backend
- **Domain**: `app.fridaysatfour.co`
- **Local Development**: Configurable API endpoints

### Infrastructure
- **Backend Hosting**: Heroku (`fridays-at-four-c9c6b7a513be.herokuapp.com`)
- **Database**: Supabase (`ipvxxsthulsysbkwbitu.supabase.co`)
- **Authentication**: Supabase Auth with email verification
- **CORS**: Configured for frontend domain + localhost:3000

## Development Setup

### Environment Setup (CRITICAL - READ FIRST)

**🚨 IMPORTANT**: This project uses conda environment `faf` for dependency management. Always use the provided activation script to avoid import errors.

#### Quick Setup
```bash
# 1. Activate environment (REQUIRED for all development)
source activate-env.sh

# 2. Run tests
faf-test                    # Test simple chat functionality
faf-pytest                  # Full test suite

# 3. Start development server
faf-dev                     # Auto-reload server
faf-server                  # Basic server
```

#### First-Time Setup
```bash
# Create conda environment
conda create -n faf python=3.11
conda activate faf
pip install -r requirements.txt

# Test environment
source activate-env.sh
```

#### Environment Troubleshooting

**Problem**: `ImportError: cannot import name 'create_client' from 'supabase'`
**Solution**: Environment not properly activated
```bash
# Check current environment
conda info --envs

# Reactivate if needed
source activate-env.sh

# Verify imports work
python -c "from supabase import create_client; print('✅ Working')"
```

**Problem**: `ModuleNotFoundError: No module named 'src'`
**Solution**: Run from project root with proper environment
```bash
cd /Applications/fridays-at-four
source activate-env.sh
```

**Problem**: Database UUID errors in tests
**Solution**: Use proper UUID format, not strings
```python
# ❌ Wrong
test_user_id = "test_user_001"

# ✅ Correct  
test_user_id = str(uuid.uuid4())
```

### Backend Local Development
```bash
# Environment setup (use conda, not venv)
source activate-env.sh

# Environment variables (.env)
ANTHROPIC_API_KEY=sk-ant-...
SUPABASE_URL=https://ipvxxsthulsysbkwbitu.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Run locally
uvicorn src.main:app --reload --port 8000
```

### Frontend Integration
- Local backend: `http://localhost:8000`
- Production backend: `https://fridays-at-four-c9c6b7a513be.herokuapp.com`
- Documentation: `FRONTEND_LOCAL_SETUP.md`

### Testing Infrastructure
```bash
# ALWAYS activate environment first
source activate-env.sh

# Run backend tests
faf-pytest                 # Full test suite
faf-test                   # Simple chat test

# Run specific tests
python test_specific_functionality.py
python cleanup_test_user.py
```

## Database Schema

### Core Tables
- **creator_profiles**: User accounts and authentication
- **project_overview**: Structured project data from onboarding
- **memory**: Conversation history and context
- **conversations**: Session metadata
- **project_updates**: Daily AI-generated project summaries with task tracking
- **longterm_memory**: Historical conversation summaries

### Key Relationships
```sql
creator_profiles (1) -> (many) project_overview
creator_profiles (1) -> (many) memory
creator_profiles (1) -> (many) conversations
creator_profiles (1) -> (many) project_updates
```

### Critical Fields
- **creator_profiles**: `id`, `slack_email`, `zoom_email`, `first_name`, `last_name`
- **project_overview**: `user_id`, `project_name`, `project_type`, `goals`, `challenges`
- **memory**: `user_id`, `content`, `memory_type`, `metadata`, `thread_id`
- **project_updates**: `user_id`, `update_date`, `progress_summary`, `milestones_hit`, `blockers`, `next_steps`, `mood_rating`

## API Endpoints

### Main Endpoints
- `POST /chat` - Main conversation endpoint (uses Claude agent)
- `POST /query_stream` - Streaming conversation with real-time responses
- `GET /project-overview/{user_id}` - Enhanced project data with task tracking
- `GET /project-status/{user_id}` - Lightweight status for dashboard polling
- `GET /health` - Health check

### Authentication
- JWT tokens via Supabase Auth
- User ID extraction from authentication headers
- Auto-creation of creator profiles for new users

## Technical Constraints

### Performance Requirements
- API response time: <2 seconds
- Database queries: Optimized with proper indexing
- Memory usage: Efficient conversation storage with summarization
- Uptime: 99%+ reliability target

### Scale Considerations
- Heroku auto-scaling enabled
- Database connection pooling
- Efficient memory summarization via daily processing
- Rate limiting for API calls

### Security Requirements
- Environment variables for all secrets
- Database row-level security
- CORS restrictions
- Input validation and sanitization

## Dependencies

### Core Python Packages
```
fastapi==0.112.2
uvicorn==0.30.6
supabase==2.10.0
anthropic==0.39.0
psycopg2-binary==2.9.9
python-dotenv==1.0.0
```

### Development Tools
```
pytest
python-dotenv
gunicorn (production)
```

## Architecture Changes (January 2025)

### Simplified System Architecture
**MAJOR CHANGE**: Removed complex LangGraph/LangChain dependencies in favor of direct Claude API integration:

**Old System (Removed)**:
- LangChain framework with complex agent routing
- LangGraph state management
- Multiple agent types with flow-based routing
- Complex onboarding flows

**New System (Current)**:
- Direct Anthropic Claude API integration via `claude_client_simple.py`
- Simple conversational agent in `claude_agent.py`
- Streamlined memory system
- Content summarization for project updates

### Content Summarization System
**NEW COMPONENT**: `src/content_summarizer.py` handles:
- Daily conversation summarization using map-reduce pattern
- Project update generation with structured JSON extraction
- Buffer management for conversation memory
- Meeting transcript processing

**Key Features**:
- Parallel chunk processing for large conversations
- Robust JSON extraction with multiple fallback strategies
- Automatic task tracking (milestones, blockers, next steps)
- Integration with nightly processing jobs

### Recent Critical Fixes (January 2025)
**JSON Extraction Bug Fixes**:
- Fixed negative brace count issues in JSON parsing
- Updated regex patterns to handle nested JSON structures
- Improved error recovery for malformed JSON
- Enhanced production stability for project updates

## Known Technical Limitations

### Current Constraints
- Single backend instance (Heroku considerations)
- Memory storage with daily summarization (no real-time vector search)
- No real-time WebSocket connections (uses streaming responses)
- Simplified conversation flows (complex onboarding moved to roadmap)

### Development Database
- **Development**: `mxlmadjuauugvlukgrla.supabase.co` (for testing)
- **Production**: `ipvxxsthulsysbkwbitu.supabase.co` (never test against this)

### Testing Requirements
- Always use proper UUID format for user IDs
- Test against development database only
- Comprehensive cleanup after tests
- Real API integration testing preferred over mocking

---

*Built on foundation: [projectbrief.md](./projectbrief.md)* 