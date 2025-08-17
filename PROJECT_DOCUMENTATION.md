# Wingman - Dating Confidence Platform Documentation

*Last Updated: August 16, 2025*

## Table of Contents
1. [Project Overview](#project-overview)
2. [Architecture Overview](#architecture-overview)
3. [Core Systems](#core-systems)
4. [API Documentation](#api-documentation)
5. [Database Schema](#database-schema)
6. [Development Setup](#development-setup)
7. [Deployment Guide](#deployment-guide)
8. [Security & Authentication](#security--authentication)
9. [Testing Strategy](#testing-strategy)
10. [Performance & Monitoring](#performance--monitoring)
11. [Known Issues & Limitations](#known-issues--limitations)

## Project Overview

**Wingman** is an AI-powered dating confidence platform that pairs men for mutual accountability and authentic confidence building. Based on Connell Barrett's proven dating methodology, it connects users with "wingman" partners for real-world practice sessions and challenges.

### Key Features
- **AI-Powered Confidence Assessment**: 12-question evaluation determining user archetypes
- **Geographic Buddy Matching**: Pairs users within 25-mile radius with similar experience levels  
- **Real-time Chat System**: In-app messaging for coordination and support
- **Challenge Catalog**: Structured approach exercises with difficulty progression
- **Session Scheduling**: Calendar integration for in-person meetups
- **Progress Tracking**: Analytics and achievement systems

### Tech Stack Summary
- **Frontend**: Next.js 14, React 18, Chakra UI, TypeScript
- **Backend**: FastAPI, Python 3.10+, async/await patterns
- **Database**: Supabase (PostgreSQL) with Row-Level Security
- **AI Integration**: Direct Anthropic Claude API (no LangChain wrapper)
- **Caching**: Redis for sessions and API responses
- **Email**: Resend API for notifications
- **Authentication**: Supabase Auth with JWT tokens
- **File Storage**: Supabase Storage for profile photos

## Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend API   │    │   Database      │
│   (Next.js)     │────│   (FastAPI)     │────│   (Supabase)    │
│                 │    │                 │    │                 │
│ • Auth Context  │    │ • Agent System  │    │ • PostgreSQL    │
│ • UI Components │    │ • Match Service │    │ • RLS Policies  │
│ • Form Handling │    │ • Rate Limiting │    │ • File Storage  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌─────────────────┐              │
         │              │   External APIs │              │
         └──────────────│                 │──────────────┘
                        │ • Claude AI     │
                        │ • Resend Email  │
                        │ • Redis Cache   │
                        └─────────────────┘
```

### Request Flow
1. **User Authentication**: Magic link or test mode → JWT token
2. **API Request**: Frontend → FastAPI with auth headers
3. **Business Logic**: Route handler → Service layer → Database
4. **AI Integration**: Assessment/coaching requests → Claude API
5. **Response**: JSON data → Frontend rendering → User interface

## Core Systems

### 1. Authentication System
**Location**: `lib/auth-context.tsx`, `app/auth/`

- **Magic Link Authentication**: Passwordless login via email
- **Test Mode**: Development bypass with mock users
- **JWT Tokens**: Supabase-managed session tokens
- **Route Protection**: Auth guards on sensitive pages
- **Row-Level Security**: Database-enforced user isolation

### 2. Confidence Assessment System
**Location**: `src/agents/`, `app/confidence-test/`

- **12-Question Flow**: Scenario-based dating confidence evaluation
- **AI-Powered Scoring**: Claude API analyzes responses
- **6 Archetypes**: Analyzer, Sprinter, Ghost, Scholar, Naturalist, Protector
- **Experience Levels**: Beginner (<60%), Intermediate (60-85%), Advanced (>85%)
- **Progress Tracking**: Resume capability for interrupted sessions

### 3. Buddy Matching System
**Location**: `src/services/wingman_matcher.py`

- **Geographic Filtering**: 25-mile radius using haversine distance
- **Experience Compatibility**: Same or ±1 experience level
- **Recency Protection**: 7-day exclusion prevents re-pairing
- **Throttling**: One active pending match per user
- **State Machine**: pending → accepted/declined → active

### 4. Chat & Communication System
**Location**: `app/buddy-chat/`, API endpoints in `src/main.py`

- **Real-time Messaging**: 5-second polling for message updates
- **Rate Limiting**: 1 message per 0.5 seconds using Redis
- **Message Validation**: 2-2000 character limits, HTML sanitization
- **Venue Suggestions**: Static panels for Coffee, Bookstores, Malls, Parks
- **System Messages**: Automated notifications for session scheduling

### 5. Session Management System
**Location**: `src/main.py` (latest addition)

- **Session Scheduling**: POST /api/session/create for wingman meetups
- **Challenge Integration**: Links to approach_challenges for structured practice
- **Email Notifications**: Automatic session reminders via Resend
- **Status Tracking**: scheduled → in_progress → completed → reviewed

### 6. Challenges Catalog System
**Location**: `src/main.py`, `approach_challenges` table

- **Difficulty Levels**: Beginner, Intermediate, Advanced challenges
- **Caching Layer**: 10-minute Redis TTL with tag-based invalidation
- **Feature Flags**: ENABLE_CHALLENGES_CATALOG for runtime control
- **Admin Tools**: Cache invalidation endpoints

## API Documentation

### Authentication Endpoints
```http
POST /api/auth/signin
POST /api/auth/callback
GET  /api/auth/user
POST /api/auth/signout
```

### Assessment Endpoints
```http
POST /api/confidence-test/start
POST /api/confidence-test/submit-answer
GET  /api/confidence-test/progress/{user_id}
GET  /api/confidence-test/results/{user_id}
```

### Profile & Matching Endpoints
```http
POST /api/profile/complete
GET  /api/matches/candidates/{user_id}
GET  /api/matches/distance/{user1_id}/{user2_id}
POST /api/matches/auto/{user_id}
POST /api/buddy/respond
```

### Chat Endpoints
```http
GET  /api/chat/messages/{match_id}
POST /api/chat/send
```

### Session Management Endpoints
```http
POST /api/session/create
GET  /api/sessions/{match_id}
POST /api/sessions/{session_id}/status
```

### Challenges Endpoints
```http
GET  /api/challenges
GET  /api/challenges?difficulty=beginner
POST /api/challenges/cache/invalidate
```

### Response Formats

**Success Response**:
```json
{
  "success": true,
  "data": {...},
  "message": "Operation completed successfully"
}
```

**Error Response**:
```json
{
  "detail": "Error description",
  "status_code": 400,
  "error_type": "validation_error"
}
```

## Database Schema

### Core Tables

**user_profiles**
- Primary user data (name, bio, archetype, experience level)
- RLS: Users can only access their own profile

**user_locations** 
- Geographic data with privacy controls (precise vs city-only)
- Indexed for efficient distance queries

**confidence_test_results**
- Assessment scores and archetype assignments
- Links to user_profiles for personalization

**wingman_matches**
- Buddy partnerships with status tracking
- Foreign keys to user_profiles with CASCADE deletes

**chat_messages**
- Real-time messaging between matched users
- RLS ensures only match participants can access

**chat_read_timestamps**
- Track last read times for unread message counts

**wingman_sessions**
- Scheduled in-person meetups
- Links challenges to execution sessions

**approach_challenges**
- Catalog of structured confidence-building exercises
- Categorized by difficulty and topic

### Key Relationships
```sql
user_profiles (1) ←→ (M) wingman_matches
wingman_matches (1) ←→ (M) chat_messages
wingman_matches (1) ←→ (M) wingman_sessions
wingman_sessions (M) ←→ (1) approach_challenges
```

### Security Policies
- **Row-Level Security (RLS)** enabled on all user tables
- **Authentication Required** for all data access
- **Participant Validation** for match-related operations
- **Cascade Deletes** maintain referential integrity

## Development Setup

### Prerequisites
- **Python 3.10+** with conda/pip
- **Node.js 18+** with npm/yarn
- **Supabase CLI** for database migrations
- **Redis** for caching (optional for development)

### Backend Setup
```bash
# Activate conda environment
conda activate wingman

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export ANTHROPIC_API_KEY=your_claude_key
export SUPABASE_URL=your_supabase_url
export SUPABASE_SERVICE_KEY=your_service_key
export RESEND_API_KEY=your_resend_key

# Start development server
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup
```bash
# Install dependencies
npm install

# Set environment variables
cp .env.example .env.local
# Edit .env.local with your Supabase keys

# Start development server
npm run dev
```

### Database Setup
```bash
# Install Supabase CLI
npm install -g supabase

# Run migrations
supabase db reset

# Check migration status
supabase migration list
```

### Testing
```bash
# Backend tests
python -m pytest reference_files/test-suite/ -v

# Integration tests
python reference_files/real_world_tests/run_all_tests.py

# Frontend E2E tests
npx playwright test
```

## Deployment Guide

### Environment Configuration

**Required Environment Variables**:
```bash
# AI Integration
ANTHROPIC_API_KEY=sk-ant-...

# Database
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_KEY=eyJ...
SUPABASE_ANON_KEY=eyJ...

# Email Service
RESEND_API_KEY=re_...

# Feature Flags
ENABLE_CHALLENGES_CATALOG=true
ENABLE_RATE_LIMITING=true
DEVELOPMENT_MODE=false
```

### Production Deployment

**Backend (Heroku)**:
```bash
# Deploy to Heroku
git push heroku main

# Set environment variables
heroku config:set ANTHROPIC_API_KEY=sk-ant-...
heroku config:set SUPABASE_URL=https://xxx.supabase.co
```

**Frontend (Vercel)**:
```bash
# Deploy to Vercel
vercel --prod

# Environment variables set via Vercel dashboard
```

**Database Migrations**:
```bash
# Apply migrations to production
supabase db push --linked
```

### Health Checks
- **Backend Health**: `GET /api/health`
- **Database Health**: `GET /api/health/db`
- **AI Service Health**: `GET /api/health/claude`

## Security & Authentication

### Authentication Flow
1. **Magic Link**: Email-based passwordless authentication
2. **JWT Validation**: Supabase handles token verification
3. **Session Management**: Automatic token refresh
4. **Route Protection**: Auth guards prevent unauthorized access

### Security Measures
- **Row-Level Security**: Database-enforced user isolation
- **Input Validation**: Comprehensive sanitization and validation
- **Rate Limiting**: Redis-based throttling for API endpoints
- **File Upload Security**: MIME type validation, size limits
- **CORS Configuration**: Restricted origins for API access

### Privacy Controls
- **Location Privacy**: Precise coordinates vs city-only sharing
- **Photo Storage**: Secure Supabase Storage with RLS
- **Chat History**: Participant-only access with encryption
- **Data Retention**: Configurable cleanup policies

## Testing Strategy

### Test Categories
1. **Unit Tests**: Core business logic and utilities
2. **Integration Tests**: API endpoints and database operations
3. **E2E Tests**: Complete user journeys with Playwright
4. **Performance Tests**: Load testing and optimization validation

### Test Coverage
- **Backend**: ~75% coverage with pytest
- **Frontend**: Component testing with React Testing Library
- **API**: Comprehensive endpoint validation
- **Database**: Schema integrity and RLS policy testing

### Test Patterns
```python
# API endpoint testing
def test_match_response_accept():
    response = client.post("/api/buddy/respond", json={
        "user_id": "test-user-id",
        "match_id": "test-match-id", 
        "action": "accept"
    })
    assert response.status_code == 200
    assert response.json()["success"] is True
```

## Performance & Monitoring

### Caching Strategy
- **Redis Caching**: Challenge catalog, session data
- **API Response Caching**: 10-minute TTL for frequently accessed data
- **Database Query Optimization**: Efficient indexing and joins

### Performance Metrics
- **API Response Time**: <200ms for cached endpoints
- **Database Query Time**: <50ms average
- **AI Response Time**: 2-5 seconds for assessments
- **Frontend Load Time**: <3 seconds initial load

### Monitoring
- **Logging**: Structured logging with context information
- **Error Tracking**: Comprehensive exception handling
- **Health Checks**: Automated service availability monitoring
- **Performance Metrics**: Response time and throughput tracking

## Known Issues & Limitations

### Current Limitations
1. **Geographic Scope**: Limited to locations with coordinates
2. **Real-time Chat**: Uses polling instead of WebSockets
3. **Mobile Experience**: Web-only, no native mobile apps
4. **Scale Constraints**: Claude API rate limits affect capacity
5. **Single Language**: English-only interface and content

### Technical Debt
1. **Mixed Authentication**: Multiple auth patterns create complexity
2. **Agent Inheritance**: BaseAgent pattern could be simplified
3. **Configuration Management**: Large number of feature flags
4. **Database Queries**: Some N+1 query patterns remain

### Security Considerations
1. **Test Auth Bypass**: Ensure disabled in production
2. **Rate Limiting**: Inconsistent application across endpoints
3. **Input Validation**: Some endpoints lack comprehensive validation
4. **Logging Practices**: Review for PII exposure

### Roadmap Items
1. **WebSocket Integration**: Real-time chat and notifications
2. **Mobile App**: React Native or native development
3. **Advanced Matching**: ML-powered compatibility algorithms
4. **Analytics Dashboard**: User progress and platform metrics
5. **Internationalization**: Multi-language support

---

*This documentation is maintained by the development team. For questions or updates, please contact the project maintainers.*