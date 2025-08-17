# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Essential First Steps

**CRITICAL**: Always read the Memory Bank files in `/reference_files/memory-bank/` at the beginning of each session:
- Start with `projectbrief.md` for foundation understanding
- Check `activeContext.md` for current priorities
- Review `progress.md` for recent accomplishments
- Reference other files as needed for complete context

## **DOMAIN-BASED AGENT WORKFLOW** ⚡

**MANDATORY**: Always use specialized agents for development tasks. Never implement features directly.

### Core Principle
Use **domain-based agent assignment** instead of task-by-task handoffs for maximum efficiency and parallel execution.

### Agent Assignment Strategy

**For ANY development work, you MUST use agents:**

1. **Analysis Phase**: Use `tech-lead-orchestrator` to analyze requirements and assign domains
2. **Domain Assignment**: Assign complete domains to specialized agents:
   - **Frontend Domain** → `frontend-developer` or framework specialists (`react-component-architect`, `react-nextjs-expert`)
   - **Backend Domain** → `backend-developer` or framework specialists (`rails-backend-expert`, `django-backend-expert`)
   - **Database Domain** → Usually handled by backend specialists
   - **Infrastructure Domain** → `performance-optimizer` or backend specialists

3. **Parallel Execution**: Frontend and Backend domains execute simultaneously (40-60% faster)
4. **Integration Validation**: Use `code-reviewer` for cross-domain integration testing

### Domain-Based Benefits
- **Parallel Development**: Frontend + Backend domains work simultaneously
- **Complete Context**: Each agent understands their entire domain scope
- **Consistent Patterns**: Domain ownership ensures architectural consistency
- **Faster Delivery**: No context switching between agents
- **Better Quality**: Domain experts optimize across complete functionality

### Implementation Rules

**✅ ALWAYS DO:**
- Use `tech-lead-orchestrator` first to analyze and assign domains
- Assign complete domains to agents, not individual tasks
- Let domain agents manage their own TodoWrite task lists
- Run Frontend + Backend domains in parallel when possible
- Use `code-reviewer` for final integration validation

**❌ NEVER DO:**
- Implement features directly without using agents
- Assign isolated tasks without domain context
- Modify existing implementation files when agents specify "create new files only"
- Skip the domain analysis phase

### Example Workflow
```
Feature Request: User Authentication System

1. tech-lead-orchestrator → Analyzes requirements, assigns domains
2. backend-developer → Complete auth API, JWT handling, validation
3. frontend-developer → Complete auth UI, forms, state management
   (Steps 2-3 run in parallel)
4. code-reviewer → Integration testing and validation
```

### Agent Delegation Pattern
Always delegate to agents using this format:
```
Task Agent: @agent-name
Description: Complete [Domain] implementation
Prompt: [Detailed domain requirements and context]
```

## Development Commands

### Backend Development
```bash
# Start development server
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Production server
gunicorn -w 4 -k uvicorn.workers.UvicornWorker src.main:app

# Install dependencies
pip install -r requirements.txt
```

### Testing
```bash
# Run all tests
python -m pytest reference_files/test-suite/ -v

# Run real-world integration tests
python reference_files/real_world_tests/run_all_tests.py

# Run specific test categories
python reference_files/real_world_tests/test_onboarding_conversation.py
python reference_files/real_world_tests/test_claude_agent_integration.py
python reference_files/real_world_tests/test_database_integration.py

# Run comprehensive user journey test
python reference_files/real_world_tests/test_full_user_journey.py
```

### Database Operations
```bash
# Install Supabase CLI
npm install -g supabase

# Run migrations
supabase db reset

# Check migration status
supabase migration list

# Generate new migration
supabase migration new migration_name
```

### Design Iteration Tool
```bash
# Initialize design iteration tool
python reference_files/scripts/design_iteration_tool.py --init

# Start development with automatic screenshots
python reference_files/scripts/design_iteration_tool.py --serve

# Capture design iterations
python reference_files/scripts/design_iteration_tool.py --screenshot "feature-name"
```

### Task Management (Task Master AI)
```bash
# View current tasks
task-master list

# Get next task to work on
task-master next

# Start working on a task
task-master set-status --id=15 --status=in-progress

# Mark task complete
task-master set-status --id=15 --status=done
```

## Architecture Overview

### Tech Stack
- **Backend**: FastAPI with Python 3.10+, async-first architecture
- **Database**: Supabase PostgreSQL with auto-dependency creation patterns
- **AI Integration**: Direct Anthropic Claude API (migrated from LangChain for 40-60% performance improvement)
- **Authentication**: JWT with Supabase Auth
- **Streaming**: Server-Sent Events (SSE) for real-time chat
- **Testing**: Pytest with comprehensive real-world test coverage

### Core System Patterns

#### Memory System (`src/simple_memory.py`)
- Persistent conversation storage in Supabase `memory` table
- Context retrieval for AI conversations
- Thread-based organization for user interactions

#### Claude Integration (`src/claude_agent.py`)
- Direct Anthropic SDK implementation (no LangChain abstraction)
- Archetype-based personalization system
- Streaming and non-streaming response modes
- Context formatting with caching optimization

#### Project Management System
- `project_overview` table: Structured project data from onboarding
- `project_updates` table: Progress tracking with JSON arrays for tasks
- Background caching system for performance optimization
- Auto-dependency creation to prevent foreign key errors

#### API Architecture (`src/main.py`)
- FastAPI with comprehensive CORS configuration
- Background task processing for data loading
- Caching layer with 30-minute TTL
- Concurrent database queries with ThreadPoolExecutor

### Key Data Flows

#### User Onboarding Flow
1. 8-topic guided conversation through `/query_stream` endpoint
2. AI extracts structured data during conversation
3. Project overview automatically created in database
4. Progress tracking initialized

#### Chat System Flow
1. User message → `/query_stream` endpoint
2. Memory handler retrieves conversation context
3. Claude API generates personalized response with archetype styling
4. Response streamed to frontend via SSE
5. Conversation stored in memory system

#### Project Status Flow
1. Frontend requests `/project-data/{user_id}`
2. Check cache → return immediately if valid
3. If no cache → trigger background data loading task
4. Return minimal data immediately for UX
5. Frontend polls `/project-data-status/{user_id}` for completion

## Development Patterns

### Error Handling
- Comprehensive logging with context information
- Graceful degradation for external API failures
- Background task error isolation
- User-friendly error messages

### Performance Optimizations
- Project data caching with background refresh
- Concurrent database queries using ThreadPoolExecutor
- Streaming responses for real-time user experience
- Prompt caching for repeated AI interactions

### Database Conventions
- Auto-dependency creation patterns in all data operations
- JSON arrays for flexible list storage (tasks, milestones, blockers)
- Timezone-aware timestamps throughout
- User-scoped data access patterns

## Important Implementation Notes

### AI Agent Integration
- Uses direct Anthropic SDK, not LangChain wrapper
- Archetype system personalizes AI responses based on user creativity profile
- Context formatting optimized for prompt caching
- Streaming implementation handles both text chunks and completion signals

### Testing Strategy
- All core functionality tested against production APIs
- Real-world user journey simulation (18-message onboarding flow)
- Database operation validation with auto-dependency testing
- Performance regression testing for Claude API migration

### Environment Configuration
Required environment variables:
- `ANTHROPIC_API_KEY`: Claude API access
- `SUPABASE_URL`: Database connection
- `SUPABASE_SERVICE_KEY`: Admin database operations
- `SUPABASE_ANON_KEY`: Public database operations
- `RESEND_API_KEY`: Email notifications

## Memory Bank Auto-Update Protocol

When implementing features or fixing issues, always update relevant Memory Bank files:
- Move completed features from "Future Dreams" to "Production Reality" in `progress.md`
- Update `activeContext.md` with current focus areas
- Document new patterns in `systemPatterns.md`
- Enhance user insights in `userJourney.md` based on discoveries
- Update deployment processes in `deploymentContext.md`

## Quality Standards

- Maintain 100% test coverage for new features
- All database operations must use auto-dependency creation patterns
- Real-world testing against production APIs required
- Memory Bank documentation must be updated after significant changes
- Code should follow async/await patterns throughout

## AI Team Configuration (autogenerated by team-configurator, 2025-08-11)

**Important: YOU MUST USE subagents when available for the task.**

### Detected Technology Stack
- **Backend Framework**: FastAPI with Python 3.10+ and async-first architecture
- **Database**: Supabase PostgreSQL with real-time capabilities and pgvector extensions
- **AI Integration**: Direct Anthropic Claude API (migrated from LangChain for 40-60% performance improvement)
- **Authentication**: Supabase Auth with JWT tokens
- **Streaming**: Server-Sent Events (SSE) for real-time chat responses
- **Testing Framework**: pytest with comprehensive real-world integration tests
- **Background Processing**: APScheduler for automated tasks and caching systems
- **Production Server**: Gunicorn with Uvicorn workers
- **API Architecture**: RESTful with complex async patterns and concurrent database operations

### AI Team Specialist Assignments

| Task | Agent | Notes |
|------|-------|-------|
| **Backend Development & Features** | `@backend-developer` | FastAPI expert for server-side logic, API endpoints, async patterns |
| **API Design & Contracts** | `@api-architect` | REST API design, OpenAPI specs, endpoint architecture |
| **Code Quality & Security Reviews** | `@code-reviewer` | MUST USE before merging - security-aware quality gate |
| **Performance & Optimization** | `@performance-optimizer` | Database queries, streaming performance, caching optimization |
| **Codebase Analysis & Architecture** | `@code-archaeologist` | Complex system exploration, technical debt analysis |
| **Documentation & Guides** | `@documentation-specialist` | API docs, setup guides, architecture documentation |

### Specialized Use Cases

**For AI Agent Development**: Use `@backend-developer` for Claude API integration, conversation memory systems, and archetype personalization features.

**For Database Operations**: Use `@backend-developer` for Supabase integration, complex queries, auto-dependency creation patterns.

**For Streaming & Real-time Features**: Use `@performance-optimizer` for SSE optimization and `@backend-developer` for implementation.

**For Testing & Quality Assurance**: Use `@code-reviewer` proactively before commits, especially for security-sensitive areas like authentication and AI integration.

### Team Collaboration Patterns

- **Always start with** `@code-archaeologist` for unfamiliar or complex legacy code exploration
- **Use** `@api-architect` when designing new endpoints or changing API contracts
- **Delegate to** `@performance-optimizer` for any slowness, scaling, or cost optimization concerns
- **Route security issues** from `@code-reviewer` to specialized security agents when available
- **Coordinate documentation** with `@documentation-specialist` after major feature implementations
EOF < /dev/null