# WingmanMatch - Environment Baselines & Setup

## Project Status
**Current State**: Initial setup phase - Task Master configured, PRD documented, no application codebase yet

## Verified Runtime Baselines

### ✅ Runtime Versions (Exceeds Requirements)
- **Node.js**: v22.13.0 ✅ (Required: 20 LTS)
- **Python**: 3.13.5 ✅ (Required: 3.11+)
- **PNPM**: 10.8.0 ✅ (Required: 9+ or npm)

### 📋 Reference Architecture (From Fridays at Four)

#### Frontend Stack
```json
{
  "framework": "Next.js 14.2.16",
  "language": "TypeScript", 
  "ui_library": "Chakra UI 2.6.0",
  "styling": "Emotion + Tailwind CSS 3.4.17",
  "state_management": "React Hooks + Supabase Client",
  "package_manager": "npm"
}
```

#### Backend Stack
```json
{
  "backend_api": "FastAPI (Python)",
  "database": "Supabase (PostgreSQL + Auth + Real-time)",
  "ai_provider": "Claude (Anthropic) via FastAPI backend",
  "deployment": "Vercel (Frontend) + Heroku (Backend)"
}
```

#### Required Environment Variables
```bash
# Frontend (.env.local)
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
NEXT_PUBLIC_BACKEND_API_URL=https://your-backend.herokuapp.com
NEXT_PUBLIC_SITE_URL=https://your-domain.co

# Backend (.env) 
ANTHROPIC_API_KEY=sk-ant-api03-...
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key
SUPABASE_ANON_KEY=your-anon-key
RESEND_API_KEY=your-resend-key
```

## Current Project Structure

```
/Applications/wingman/
├── .taskmaster/              # Task Master configuration & tasks
│   ├── tasks/               # Individual task files (task_001_wingman-match.txt, etc.)
│   └── docs/                # PRD and documentation
├── reference_files/         # READ-ONLY reference patterns from F@4
│   ├── frontend_reference/  # Complete Next.js app reference
│   ├── src/                # FastAPI backend reference  
│   └── memory-bank/        # Project context documentation
├── docs/                   # Project planning documents
├── tasks/                  # Task Master task list (JSON)
├── CLAUDE.md              # Claude Code instructions
└── README.md              # This file
```

## Development Commands (Reference Patterns)

### Frontend Commands (When Implemented)
```bash
# Development
npm run dev       # Start development server (localhost:3000)
npm run build     # Build for production
npm run lint      # Run Next.js ESLint

# Testing  
npm test          # Run Vitest unit tests
npx playwright test # Run E2E tests
```

### Backend Commands (When Implemented)
```bash
# Development
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Production
gunicorn -w 4 -k uvicorn.workers.UvicornWorker src.main:app

# Dependencies
pip install -r requirements.txt
```

## Task Master Integration

### Current Task Status
- **Task 1**: ✅ Environment baselines verified
- **Task 2**: 📋 Basic Database Migrations (pending)
- **Task 3**: 📋 Backend config: Supabase, Redis, Resend (pending)
- **Task 4**: 📋 Transform AI coach: Hai→Connell prompts (pending)

### Task Master Commands
```bash
task-master list    # List all tasks
task-master next    # Get next task to work on
task-master set-status --id=1 --status=done  # Mark task complete
```

## Delta Analysis: Current vs Reference

### ❌ Missing Components (To Be Created)
1. **No Frontend Codebase**: Next.js app not initialized
2. **No Backend Source**: FastAPI application not created
3. **No package.json**: Frontend dependencies not configured
4. **No Environment Files**: .env.local and .env not set up
5. **No CI/CD Pipeline**: GitHub Actions not configured
6. **No Database Schema**: Supabase migrations not created

### ✅ Available References
- Complete working FastAPI backend in `reference_files/src/`
- Full Next.js frontend in `reference_files/frontend_reference/FAF_website/`
- Environment structure documented in `reference_files/src/config.py`
- Development commands in `reference_files/frontend_reference/FAF_website/CLAUDE.md`

## Next Steps

1. **Task 2**: Create database migrations for WingmanMatch tables
2. **Task 3**: Set up backend configuration with Supabase/Redis/Resend
3. **Task 4**: Transform AI prompts from Hai to Connell personality
4. Copy and adapt reference implementations to create working WingmanMatch app

## Team Notes

- **Architecture Foundation**: Proven F@4 infrastructure provides solid foundation
- **Runtime Environment**: System exceeds all version requirements
- **Reference Quality**: High-quality reference implementation available
- **Task Management**: Task Master properly configured with 29 defined tasks
- **Documentation**: Comprehensive PRD defines clear product direction

---

*Last Updated: 2025-08-13*  
*Environment Verification Status: ✅ Complete*