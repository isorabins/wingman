# Wingman Development Guide

*Last Updated: August 16, 2025*

## Quick Start

### Prerequisites
- **Python 3.10+** with conda environment management
- **Node.js 18+** with npm
- **Git** for version control
- **Supabase CLI** for database operations
- **Redis** (optional for development, required for production)

### Initial Setup
```bash
# Clone the repository
git clone <repository-url>
cd wingman

# Activate the wingman conda environment
conda activate wingman

# Backend setup
pip install -r requirements.txt

# Frontend setup
npm install

# Environment configuration
cp .env.example .env.local
# Edit .env.local with your API keys
```

### Development Servers
```bash
# Backend (Terminal 1)
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Frontend (Terminal 2) 
npm run dev
```

**Access URLs**:
- Frontend: `http://localhost:3002`
- Backend API: `http://localhost:8000`
- API Docs: `http://localhost:8000/docs`

## Project Structure

```
wingman/
├── app/                          # Next.js frontend application
│   ├── auth/                     # Authentication pages
│   ├── buddy-chat/               # Chat interface
│   ├── confidence-test/          # Assessment UI
│   ├── profile-setup/            # Profile completion
│   └── page.tsx                  # Landing page
├── components/                   # Reusable React components
│   ├── LocationCapture.tsx       # Location services
│   └── ui/                       # Base UI components
├── lib/                          # Frontend utilities
│   ├── auth-context.tsx          # Authentication state
│   └── supabase.ts               # Database client
├── src/                          # Backend FastAPI application
│   ├── agents/                   # AI conversation agents
│   ├── services/                 # Business logic services
│   ├── main.py                   # API routes and application
│   ├── config.py                 # Configuration management
│   └── database.py               # Database client factory
├── supabase/                     # Database schema and migrations
│   └── migrations_wm/            # Migration files
├── tests/                        # Test suites
│   ├── backend/                  # Python tests
│   └── e2e/                      # Playwright E2E tests
├── memory-bank/                  # Project context and documentation
└── reference_files/              # Historical files and documentation
```

## Development Workflow

### Branch Strategy
- **main**: Production-ready code
- **development**: Integration branch for testing
- **feature/***: Individual feature development
- **hotfix/***: Critical production fixes

### Code Changes Process
1. **Create Feature Branch**:
   ```bash
   git checkout -b feature/session-management
   ```

2. **Make Changes**: Follow coding standards and patterns

3. **Run Tests**:
   ```bash
   # Backend tests
   python -m pytest tests/backend/ -v
   
   # Frontend tests  
   npm run test
   
   # E2E tests
   npx playwright test
   ```

4. **Code Review**: Create pull request with description

5. **Merge**: Squash merge to main after approval

### Coding Standards

#### Python (Backend)
```python
# Use type hints
def create_match(user_id: str, candidate_id: str) -> Dict[str, Any]:
    """Create wingman match with validation."""
    
# Follow PEP 8 formatting
# Use descriptive variable names
# Add docstrings for functions
# Handle exceptions gracefully
```

#### TypeScript (Frontend)
```typescript
// Use interfaces for type safety
interface MatchData {
  id: string;
  status: 'pending' | 'accepted' | 'declined';
  createdAt: Date;
}

// Use async/await for API calls
const handleMatchResponse = async (action: string) => {
  try {
    const response = await api.post('/buddy/respond', { action });
    // Handle success
  } catch (error) {
    // Handle error
  }
};
```

### Environment Variables

#### Required for Development
```bash
# .env.local (Frontend)
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_anon_key

# Backend environment
ANTHROPIC_API_KEY=sk-ant-your-claude-key
SUPABASE_URL=your_supabase_url  
SUPABASE_SERVICE_KEY=your_service_key
RESEND_API_KEY=re_your-resend-key
DEVELOPMENT_MODE=true
```

#### Optional for Development
```bash
# Redis (if running locally)
REDIS_URL=redis://localhost:6379

# Feature flags
ENABLE_CHALLENGES_CATALOG=true
ENABLE_RATE_LIMITING=false
```

### Database Development

#### Migration Management
```bash
# Create new migration
supabase migration new add_new_feature

# Apply migrations locally
supabase db reset

# Check migration status
supabase migration list

# Generate types for frontend
supabase gen types typescript --local > types/supabase.ts
```

#### Schema Changes
1. **Create Migration File**: Add SQL in `supabase/migrations_wm/`
2. **Include RLS Policies**: Ensure proper security policies
3. **Add Indexes**: For performance on query columns
4. **Test Locally**: Verify migration works correctly
5. **Update Types**: Regenerate TypeScript types

#### Sample Migration
```sql
-- 005_add_session_feedback.sql
BEGIN;

CREATE TABLE IF NOT EXISTS "public"."session_feedback" (
    "id" uuid DEFAULT extensions.uuid_generate_v4() NOT NULL,
    "session_id" uuid NOT NULL,
    "user_id" uuid NOT NULL, 
    "rating" integer CHECK (rating BETWEEN 1 AND 5),
    "comments" text,
    "created_at" timestamp with time zone DEFAULT now(),
    CONSTRAINT "session_feedback_pkey" PRIMARY KEY ("id"),
    CONSTRAINT "session_feedback_session_id_fkey" 
        FOREIGN KEY ("session_id") REFERENCES "wingman_sessions"("id") ON DELETE CASCADE
);

-- Enable RLS
ALTER TABLE "public"."session_feedback" ENABLE ROW LEVEL SECURITY;

-- RLS Policy
CREATE POLICY "Users can manage their own feedback" ON "public"."session_feedback"
    FOR ALL TO authenticated
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

COMMIT;
```

### Testing Strategy

#### Backend Testing
```python
# Unit tests (tests/backend/test_services.py)
def test_wingman_matcher_service():
    """Test wingman matching algorithm."""
    matcher = WingmanMatcher()
    result = matcher.find_candidates("user-id", radius_miles=25)
    assert len(result) > 0
    assert result[0].distance_miles <= 25

# Integration tests
@pytest.mark.asyncio
async def test_match_response_api():
    """Test match response endpoint."""
    response = await client.post("/api/buddy/respond", json={
        "user_id": "test-user",
        "match_id": "test-match", 
        "action": "accept"
    })
    assert response.status_code == 200
```

#### Frontend Testing
```typescript
// Component tests (components/__tests__/LocationCapture.test.tsx)
import { render, screen, fireEvent } from '@testing-library/react';
import LocationCapture from '../LocationCapture';

test('allows location permission request', async () => {
  render(<LocationCapture onLocationUpdate={jest.fn()} />);
  
  const button = screen.getByText('Get My Location');
  fireEvent.click(button);
  
  expect(screen.getByText('Requesting location...')).toBeInTheDocument();
});
```

#### E2E Testing
```typescript
// tests/e2e/user-journey.spec.ts
import { test, expect } from '@playwright/test';

test('complete user onboarding journey', async ({ page }) => {
  // Navigate to sign-in
  await page.goto('/auth/signin');
  
  // Sign in with test user
  await page.fill('[data-testid=email-input]', 'test@wingman.dev');
  await page.click('[data-testid=signin-button]');
  
  // Complete profile
  await page.goto('/profile-setup?test=true');
  await page.fill('[data-testid=first-name]', 'Test');
  await page.fill('[data-testid=bio]', 'Building confidence together');
  
  // Take confidence test
  await page.goto('/confidence-test');
  // Continue with test flow...
  
  expect(page.url()).toContain('/buddy-matching');
});
```

### API Development

#### Adding New Endpoints
1. **Define Pydantic Models**:
```python
# In src/main.py
class SessionCreateRequest(BaseModel):
    match_id: str = Field(..., pattern=r'^[0-9a-f-]{36}$')
    venue_name: str = Field(..., min_length=2, max_length=100)
    time: datetime
```

2. **Implement Route Handler**:
```python
@app.post("/api/session/create", response_model=SessionCreateResponse)
async def create_wingman_session(request: SessionCreateRequest):
    """Create scheduled wingman session."""
    try:
        # Validation
        # Business logic
        # Database operations
        # Return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating session: {e}")
        raise HTTPException(status_code=500, detail="Failed to create session")
```

3. **Add Tests**:
```python
def test_session_create_endpoint():
    response = client.post("/api/session/create", json={
        "match_id": "valid-uuid",
        "venue_name": "Coffee Shop",
        "time": "2025-08-20T15:00:00Z"
    })
    assert response.status_code == 200
```

#### API Best Practices
- **Input Validation**: Use Pydantic models with constraints
- **Error Handling**: Consistent HTTP status codes and messages  
- **Authentication**: Validate JWT tokens and user permissions
- **Rate Limiting**: Apply appropriate throttling
- **Logging**: Include context for debugging
- **Documentation**: Auto-generated with FastAPI

### Frontend Development

#### Component Development
```typescript
// components/SessionScheduler.tsx
import { useState } from 'react';
import { Button, Input, VStack } from '@chakra-ui/react';

interface SessionSchedulerProps {
  matchId: string;
  onSessionCreated: (session: Session) => void;
}

export default function SessionScheduler({ matchId, onSessionCreated }: SessionSchedulerProps) {
  const [venue, setVenue] = useState('');
  const [loading, setLoading] = useState(false);
  
  const handleCreateSession = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/session/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ match_id: matchId, venue_name: venue })
      });
      
      if (response.ok) {
        const session = await response.json();
        onSessionCreated(session);
      }
    } catch (error) {
      console.error('Failed to create session:', error);
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <VStack spacing={4}>
      <Input 
        placeholder="Venue name"
        value={venue}
        onChange={(e) => setVenue(e.target.value)}
      />
      <Button 
        onClick={handleCreateSession}
        loading={loading}
        disabled={!venue}
      >
        Schedule Session
      </Button>
    </VStack>
  );
}
```

#### State Management
```typescript
// lib/auth-context.tsx
import { createContext, useContext, useEffect, useState } from 'react';
import { supabase } from './supabase';

interface AuthContextType {
  user: User | null;
  loading: boolean;
  signIn: (email: string) => Promise<void>;
  signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
}
```

### Performance Optimization

#### Backend Optimization
```python
# Efficient database queries
from asyncio import gather

async def get_user_dashboard_data(user_id: str):
    """Get all dashboard data concurrently."""
    tasks = [
        get_user_profile(user_id),
        get_active_matches(user_id), 
        get_recent_messages(user_id),
        get_upcoming_sessions(user_id)
    ]
    
    profile, matches, messages, sessions = await gather(*tasks)
    
    return {
        "profile": profile,
        "matches": matches,
        "messages": messages,
        "sessions": sessions
    }
```

#### Frontend Optimization
```typescript
// Optimistic updates for better UX
const sendMessage = async (message: string) => {
  const optimisticMessage = {
    id: 'temp-' + Date.now(),
    text: message,
    sender_id: user.id,
    created_at: new Date()
  };
  
  // Add to UI immediately
  setMessages(prev => [...prev, optimisticMessage]);
  
  try {
    // Send to server
    const response = await api.post('/chat/send', { message });
    
    // Replace optimistic message with server response
    setMessages(prev => prev.map(msg => 
      msg.id === optimisticMessage.id ? response.data : msg
    ));
  } catch (error) {
    // Remove optimistic message on error
    setMessages(prev => prev.filter(msg => msg.id !== optimisticMessage.id));
    showError('Failed to send message');
  }
};
```

### Debugging

#### Backend Debugging
```python
# Add detailed logging
import logging

logger = logging.getLogger(__name__)

async def process_match_response(request: MatchResponseRequest):
    logger.info(f"Processing match response: {request.action} for match {request.match_id}")
    
    try:
        # Business logic
        logger.debug(f"Match validation successful for {request.match_id}")
    except Exception as e:
        logger.error(f"Match response failed: {e}", exc_info=True)
        raise
```

#### Frontend Debugging
```typescript
// Use React DevTools and browser debugging
useEffect(() => {
  console.log('Match data updated:', matchData);
  
  // Debug authentication state
  if (process.env.NODE_ENV === 'development') {
    console.log('Auth state:', { user, loading });
  }
}, [matchData, user, loading]);
```

### Common Issues and Solutions

#### Database Connection Issues
```bash
# Check environment variables
echo $SUPABASE_URL
echo $SUPABASE_SERVICE_KEY

# Test database connection
supabase status

# Reset local database
supabase db reset
```

#### Authentication Problems
```typescript
// Clear auth state and retry
const handleAuthError = async () => {
  await supabase.auth.signOut();
  localStorage.clear();
  window.location.reload();
};
```

#### Performance Issues
```python
# Profile slow queries
import time

start_time = time.time()
result = db_client.table('wingman_matches').select('*').execute()
end_time = time.time()

if end_time - start_time > 1.0:
    logger.warning(f"Slow query detected: {end_time - start_time:.2f}s")
```

## Deployment

### Pre-deployment Checklist
- [ ] All tests passing
- [ ] Environment variables configured
- [ ] Database migrations applied
- [ ] Feature flags set appropriately
- [ ] Security review completed
- [ ] Performance testing done

### Local Production Testing
```bash
# Build and test production frontend
npm run build
npm run start

# Test production backend
gunicorn -w 4 -k uvicorn.workers.UvicornWorker src.main:app

# Run full test suite
python reference_files/real_world_tests/run_all_tests.py
```

---

*This guide is updated regularly. For questions or suggestions, please contact the development team.*