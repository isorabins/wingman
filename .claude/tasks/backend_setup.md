# Backend Setup Implementation Plan

## Overview
Setting up the backend structure for WingmanMatch by copying source files from reference_files and creating proper environment configuration following FastAPI + Claude API + Supabase architecture.

## Technology Stack Detected
- **Backend Framework**: FastAPI with Python 3.11+ and async-first architecture
- **Database**: Supabase PostgreSQL with real-time capabilities
- **AI Integration**: Direct Anthropic Claude API (migrated from LangChain for performance)
- **Authentication**: Supabase Auth with JWT tokens
- **Streaming**: Server-Sent Events (SSE) for real-time chat responses
- **Testing Framework**: pytest with comprehensive real-world integration tests
- **Production Server**: Gunicorn with Uvicorn workers

## Implementation Tasks

### 1. Copy Source Files (Priority: Critical)
- Copy all Python files from `/Applications/wingman/reference_files/src/` to `/Applications/wingman/src/`
- Copy `requirements.txt` from reference_files/ to root
- Copy `pyproject.toml` from reference_files/ to root
- Preserve file structure and permissions

### 2. Environment Configuration (Priority: Critical)
- Create `.env` file with placeholder values for required environment variables
- Update .env.example if needed based on reference files requirements
- Document which environment variables need real values vs placeholders

### 3. Verify Backend Structure (Priority: High)
- Ensure main.py is properly configured for FastAPI
- Verify Claude agent integration is in place
- Check database connection setup (Supabase)
- Validate import paths work correctly

### 4. Create Documentation (Priority: Medium)
- Create README.md with setup instructions
- Document Python version requirement (3.11+)
- Include environment variables documentation
- Add basic commands to run the backend

## Required Environment Variables (Based on Analysis)
From the main.py analysis, these are the critical environment variables:

### Core Application
- `ANTHROPIC_API_KEY`: Claude API access (Required)
- `SUPABASE_URL`: Database connection (Required)
- `SUPABASE_SERVICE_KEY`: Admin database operations (Required)
- `SUPABASE_ANON_KEY`: Public database operations (Required)

### Optional Services
- `RESEND_API_KEY`: Email notifications
- `SLACK_SIGNING_SECRET`: Slack integration
- `OPENAI_API_KEY`: OpenAI models (optional)
- `PERPLEXITY_API_KEY`: Perplexity integration (optional)

## Key Files to Copy
Based on reference_files/src/ analysis:
- `main.py`: FastAPI application with CORS, endpoints, caching
- `claude_agent.py`: Direct Anthropic SDK integration
- `simple_memory.py`: Conversation persistence and retrieval
- `content_summarizer.py`: Map-reduce pattern for daily summaries
- `prompts.py`: Prompt templates for Claude API
- `archetype_helper.py`: User personalization system
- `config.py`: Configuration management
- All supporting modules

## Testing Strategy
- Verify all imports work correctly
- Test FastAPI startup without errors
- Validate environment variable loading
- Ensure database connection can be established (with placeholder values)

## Success Criteria
1. Backend source code copied successfully to main project
2. Environment configuration created with proper placeholders
3. FastAPI application starts without import errors
4. README.md provides clear setup instructions
5. All critical files present and properly structured

## Risks and Mitigation
- **Import Errors**: Fixed by preserving exact file structure from reference_files
- **Environment Issues**: Mitigated by providing comprehensive .env template
- **Missing Dependencies**: Addressed by copying exact requirements.txt

## Notes
- This follows the existing "Fridays at Four" architecture patterns
- Memory Bank context shows system is production-ready and tested
- Focus on preserving working configuration from reference_files