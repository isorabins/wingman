# Active Session Pages Implementation Plan

## Task Overview
Implement Next.js 13+ App Router pages for active session functionality based on Task 14. Create Server Component route `/session/[id]` that fetches session data server-side with proper Next.js patterns including Suspense boundaries, cache optimization, and separation of concerns between Server and Client Components.

## System Context Analysis

**Current Architecture:**
- **Frontend**: Next.js 13+ App Router with Chakra UI + TypeScript
- **Backend**: FastAPI with session creation API (Task 13 complete)
- **Database**: Supabase with wingman_sessions table operational
- **Authentication**: Supabase Auth with test mode support via AuthProvider
- **Existing Patterns**: Buddy chat implementation shows established patterns

**API Integration Points:**
- Task 13 delivered: POST /api/session/create (session creation)
- Task 14 needs: GET /api/session/{id} (session retrieval)
- Existing: Chat system with real-time polling patterns

## Implementation Plan

### Phase 1: Core Page Structure and Server Components

#### 1.1 Session Data Fetching Utility
**File**: `lib/sessions/getSession.ts`
```typescript
// Server-side data fetching with cache tags
// Implements fetch with cache: 'force-cache', tags: ['session', `session:${id}`]
// Error handling for 404, 403, 500 responses
// Returns typed SessionData interface
```

#### 1.2 Main Session Page (Server Component)
**File**: `app/session/[id]/page.tsx`
```typescript
// Server Component for session metadata rendering
// Fetches session data server-side using getSession utility
// Implements Suspense boundary for progressive loading
// Renders session info: time, venue, participants, challenges
// Includes Client Component slot for interactive actions
// Follows existing auth patterns from buddy-chat
```

#### 1.3 Loading and Error Boundaries
**Files**: 
- `app/session/[id]/loading.tsx` - Skeleton loading state
- `app/session/[id]/error.tsx` - Error boundary with retry capability

#### 1.4 Session Metadata Server Component
**File**: `app/session/[id]/SessionMetadata.tsx`
```typescript
// Pure Server Component for displaying session information
// Renders participant info, challenge details, venue/time
// Uses Chakra UI components following established patterns
// Accessibility features: ARIA regions, proper headings
// Mobile-first responsive design
```

### Phase 2: Client Components and Interactivity

#### 2.1 Client Actions Component
**File**: `app/session/[id]/ClientActions.tsx`
```typescript
// Client Component for user interactions
// Session confirmation buttons, challenge updates
// Uses useAuth hook for user context
// Integrates with existing toast patterns from buddy-chat
// Rate limiting and optimistic UI updates
```

#### 2.2 API Route Implementation
**File**: `app/api/session/[id]/route.ts`
```typescript
// GET endpoint for session retrieval
// Validates user authorization (participant only)
// Returns SessionData with proper typing
// Error handling: 404 (not found), 403 (unauthorized)
// Follows FastAPI backend patterns but Next.js API routes
```

### Phase 3: Data Types and Integration

#### 3.1 Session Data Interface
```typescript
interface SessionData {
  id: string;
  match_id: string;
  venue_name: string;
  scheduled_time: string;
  status: 'scheduled' | 'in_progress' | 'completed' | 'cancelled';
  notes?: string;
  participants: {
    user1: { id: string; name: string; challenge: Challenge; confirmed: boolean };
    user2: { id: string; name: string; challenge: Challenge; confirmed: boolean };
  };
  reputation_preview: {
    user1_delta: number;
    user2_delta: number;
  };
}

interface Challenge {
  id: string;
  title: string;
  description: string;
  difficulty: 'beginner' | 'intermediate' | 'advanced';
  points: number;
}
```

## Technical Implementation Details

### Server Component Optimizations
- **Cache Strategy**: `fetch` with `cache: 'force-cache'` and cache tags for revalidation
- **No Client-Side JavaScript**: Pure Server Components for metadata display
- **SEO Optimization**: Proper meta tags, structured data
- **Performance**: Minimal bundle size, server-side rendering benefits

### Client Component Strategy
- **Minimal Client Code**: Only interactive elements marked 'use client'
- **Progressive Enhancement**: Works without JavaScript for basic viewing
- **State Management**: Local state for form interactions, global auth context
- **Error Boundaries**: Graceful degradation for failed interactions

### Authentication Integration
- **Existing Patterns**: Use AuthProvider context from lib/auth-context.tsx
- **Test Mode Support**: Compatible with ?test=true development mode
- **Authorization**: Verify user is session participant before showing actions
- **Security**: No sensitive operations in Client Components

### Mobile and Accessibility
- **Responsive Design**: Mobile-first approach using Chakra UI breakpoints
- **ARIA Labels**: Proper accessibility attributes for screen readers
- **Keyboard Navigation**: Tab order, focus management for interactive elements
- **Touch Targets**: Minimum 44px touch targets for mobile interactions

## File Structure Implementation

```
app/session/[id]/
├── page.tsx                 # Main Server Component page
├── loading.tsx              # Loading skeleton
├── error.tsx                # Error boundary
├── SessionMetadata.tsx      # Server Component for session info
└── ClientActions.tsx        # Client Component for interactions

lib/sessions/
└── getSession.ts           # Server-side data fetching utility

app/api/session/[id]/
└── route.ts                # API route for session data (if needed)
```

## Integration Points

### Backend API Integration
- **Session Retrieval**: Integrate with Task 13's session creation system
- **Challenge Data**: Connect to Task 12's challenges catalog API
- **User Profiles**: Leverage existing user data patterns
- **Chat Integration**: Link to existing buddy-chat system

### Frontend Pattern Consistency
- **Chakra UI**: Follow established theme and component patterns
- **Loading States**: Consistent with profile-setup and confidence-test pages
- **Error Handling**: Match buddy-chat error handling patterns
- **Navigation**: Integrate with existing app navigation structure

## Testing Strategy

### Unit Testing
- SessionMetadata component rendering with mock data
- getSession utility function with various response scenarios
- ClientActions component interaction handling

### Integration Testing
- End-to-end session page loading with real API data
- Authentication flow integration with session access
- Error boundary testing with network failures
- Mobile responsive testing across devices

### Performance Testing
- Server Component vs Client Component bundle size comparison
- Cache effectiveness measurement
- Loading time optimization validation

## Success Criteria

### Functional Requirements
✅ Server Component route `/session/[id]` loads session data  
✅ Proper Server/Client Component separation implemented  
✅ Suspense boundaries for progressive loading  
✅ Session metadata displayed with proper formatting  
✅ Client actions placeholder ready for future interactivity  
✅ Mobile-responsive design with accessibility compliance  

### Technical Requirements  
✅ Cache tags implementation for session data  
✅ Error boundaries with retry capability  
✅ Authentication integration with existing patterns  
✅ TypeScript strict typing throughout  
✅ Next.js 13+ App Router best practices followed  
✅ No prefetch on session links (as specified)  

### Performance Requirements
✅ Server Components minimize client-side JavaScript  
✅ Initial page load under 3 seconds  
✅ Proper SEO meta tags and structured data  
✅ Cache strategy optimizes repeat visits  

## Risk Mitigation

### Development Risks
- **Auth Integration**: Test mode support ensures development workflow continuity
- **API Changes**: Interface definitions isolate backend changes
- **Component Boundaries**: Clear separation prevents hydration issues

### Performance Risks  
- **Bundle Size**: Server Components minimize client JavaScript
- **Cache Invalidation**: Granular cache tags prevent stale data
- **Loading States**: Suspense boundaries prevent UI blocking

### User Experience Risks
- **Error States**: Comprehensive error boundaries with recovery options
- **Mobile Performance**: Mobile-first design prevents layout issues
- **Accessibility**: ARIA compliance ensures universal access

## Post-Implementation Tasks

### Documentation Updates
- Update memory-bank with Session page patterns
- Document Server/Client Component architecture decisions
- Add session page to user journey documentation

### Future Enhancement Readiness
- Client Actions component ready for Task 15+ features
- Cache infrastructure prepared for real-time updates
- Authentication patterns support advanced permissions

### Testing and Validation
- E2E test coverage for complete session workflow
- Performance benchmarking against current page load metrics
- Accessibility audit using automated tools

---

## Implementation Notes

This plan focuses on creating a solid foundation for the session system using Next.js 13+ best practices while maintaining consistency with the existing codebase. The Server/Client Component separation ensures optimal performance while the modular architecture supports future feature expansion.

The implementation will integrate seamlessly with existing systems (auth, chat, challenges) while establishing patterns that can be reused for other complex pages in the application.