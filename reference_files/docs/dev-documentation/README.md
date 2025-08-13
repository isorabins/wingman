# Developer Documentation

Technical documentation for Fridays at Four development.

## Quick Start
```bash
git clone https://github.com/fridays-at-four/fridays-at-four.git
cd fridays-at-four
source activate-env.sh  # Creates conda env 'faf'
faf-dev                 # Start backend (:8000)
```

## Documentation Structure

### [00-project-overview.md](00-project-overview.md)
Complete system architecture, tech stack, and production metrics.

### [01-quick-setup.md](01-quick-setup.md)
Environment setup, dependencies, and development commands.

### [02-system-architecture.md](02-system-architecture.md)
Core components, patterns, and technical decisions.

### [03-common-tasks.md](03-common-tasks.md)
Practical development scenarios with code examples.

### [04-database-guide.md](04-database-guide.md)
Schema, query patterns, and database operations.

### [05-api-reference.md](05-api-reference.md)
Endpoint documentation and request/response formats.

### [06-troubleshooting.md](06-troubleshooting.md)
Common issues and debugging procedures.

### [07-deployment.md](07-deployment.md)
Production deployment process and safety rules.

### [08-frontend-integration.md](08-frontend-integration.md)
API integration patterns and React components.

## Key Technical Details

**Stack**: FastAPI + Claude API + Supabase PostgreSQL + Next.js  
**Environment**: Conda 'faf' environment required  
**Database**: User-scoped queries for cross-session continuity  
**AI**: Direct Claude SDK with OpenAI fallback  
**Deployment**: Heroku (backend) + Vercel (frontend)

## Critical Patterns
- Always call `ensure_creator_profile()` before database operations
- Query by `user_id` not `thread_id` for memory continuity  
- Use proper UUID format: `str(uuid.uuid4())`
- Test against dev database: `mxlmadjuauugvlukgrla.supabase.co`
- Never write to production database during development

## Development Workflow
1. `source activate-env.sh` - Activate environment
2. `faf-dev` - Start backend server
3. Test endpoints with proper UUIDs
4. Use `python cleanup_test_user.py` for test cleanup
5. Deploy only with permission: "Should I deploy this to dev?"

## Production Status
- **Backend**: 49/49 tests passing, <2s response time
- **Database**: Auto-dependency creation, foreign key safety
- **Memory**: User-scoped context with nightly summarization
- **Testing**: Comprehensive real-world test suite

---
*For immediate setup: Read [01-quick-setup.md](01-quick-setup.md)*  
*For architecture: Read [02-system-architecture.md](02-system-architecture.md)* 