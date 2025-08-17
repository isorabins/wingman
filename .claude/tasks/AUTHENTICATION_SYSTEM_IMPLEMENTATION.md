# Authentication System Implementation Plan

## Current Problem Analysis

### Critical Issues Discovered:
1. **RLS Policy Violations**: Photo uploads failing with "new row violates row-level security policy"
2. **Hardcoded User IDs**: Lines 188 and 272 in `/app/profile-setup/page.tsx` use "demo-user-id"
3. **No Authentication Context**: No React context for managing Supabase auth state
4. **Missing Auth Guards**: Profile setup page is accessible without authentication
5. **No Sign-in Flow**: No authentication UI or flow implementation

### Root Cause:
The application is trying to perform database operations (photo uploads, profile creation) without proper user authentication, causing Supabase RLS policies to reject the operations since they expect an authenticated user context.

## Implementation Plan

### Phase 1: Authentication Context & Infrastructure
**Goal**: Create React context for Supabase auth management

#### 1.1 Create Authentication Context (`lib/auth-context.tsx`)
- **Purpose**: Centralized auth state management with Supabase
- **Features**:
  - User session management
  - Loading states
  - Authentication status
  - Sign in/out methods
  - Session persistence
- **Pattern**: React Context + useAuth hook
- **Integration**: Supabase auth with automatic session refresh

#### 1.2 Update App Providers (`app/providers.tsx`)
- **Purpose**: Wrap application with AuthProvider
- **Changes**: Add AuthProvider to existing ChakraProvider wrapper
- **Order**: ChakraProvider wraps AuthProvider for theme access in auth components

### Phase 2: Authentication UI Implementation
**Goal**: Create sign-in flow and callback handling

#### 2.1 Create Sign-in Page (`app/auth/signin/page.tsx`)
- **Purpose**: Magic link authentication UI
- **Features**:
  - Email input with validation
  - Magic link sending
  - Loading states
  - Error handling
  - Redirect after sign-in
- **Design**: Chakra UI components with brand theme
- **UX**: Clear instructions and feedback

#### 2.2 Create Auth Callback Route (`app/auth/callback/route.ts`)
- **Purpose**: Handle Supabase auth callbacks
- **Features**:
  - Session establishment
  - URL parameter handling
  - Redirect to intended destination
  - Error handling for failed auth

### Phase 3: Profile Setup Authentication Integration
**Goal**: Replace hardcoded user IDs with real authentication

#### 3.1 Update Profile Setup Page (`app/profile-setup/page.tsx`)
- **Changes**:
  - Replace lines 188 and 272: `"demo-user-id"` → `user?.id`
  - Add useAuth hook integration
  - Add authentication guards
  - Handle loading states
  - Redirect to sign-in if not authenticated
- **Security**: Ensure all user operations use authenticated user ID

#### 3.2 Add Authentication Guards
- **Purpose**: Protect profile setup and other authenticated routes
- **Implementation**: Check auth status and redirect to sign-in if needed
- **UX**: Show loading spinner during auth check

### Phase 4: Photo Upload Security Fix
**Goal**: Fix RLS policy violations in photo uploads

#### 4.1 Update Photo Upload Service (`storage/photo_upload.ts`)
- **Changes**: Ensure uploads use authenticated user context
- **Integration**: Pass authenticated user ID to all storage operations
- **Security**: Validate user permissions before upload operations

#### 4.2 Supabase Storage Configuration
- **Verification**: Confirm RLS policies allow authenticated users to upload photos
- **Testing**: Verify photo upload works with real authenticated users

### Phase 5: Testing & Validation
**Goal**: Ensure authentication system works correctly

#### 5.1 Authentication Flow Testing
- **Test Cases**:
  - Magic link sign-in flow
  - Session persistence
  - Sign-out functionality
  - Auth guards on protected routes
  - Profile setup with authenticated user

#### 5.2 RLS Policy Validation
- **Test Cases**:
  - Photo upload with authenticated user
  - Profile creation with authenticated user
  - Data isolation between users
  - Unauthorized access prevention

## Technical Implementation Details

### Authentication Context Architecture
```typescript
interface AuthContext {
  user: User | null
  session: Session | null
  isLoading: boolean
  signIn: (email: string) => Promise<{ error?: string }>
  signOut: () => Promise<void>
  isAuthenticated: boolean
}
```

### Key Dependencies
- **Existing**: @supabase/supabase-js, @supabase/auth-helpers-nextjs
- **Required**: No new dependencies needed
- **Integration**: React Hook Form, Chakra UI, Zod validation

### Security Considerations
1. **Session Management**: Automatic token refresh and secure storage
2. **RLS Compliance**: All database operations use authenticated user context
3. **Route Protection**: Authentication guards on sensitive pages
4. **Data Isolation**: User-scoped operations only
5. **Error Handling**: Graceful degradation and clear error messages

### Performance Optimizations
1. **Session Persistence**: Local storage for faster authentication checks
2. **Loading States**: Prevent UI flicker during auth verification
3. **Lazy Loading**: Auth checks only when needed
4. **Caching**: Session state caching to reduce Supabase calls

## Success Criteria

### Primary Goals Achieved:
- ✅ Photo uploads work with authenticated users
- ✅ No more "demo-user-id" hardcoded values
- ✅ RLS policies properly enforce user isolation
- ✅ Profile data saved with correct authenticated user ID
- ✅ Complete sign-in/sign-out flow functional

### Secondary Goals:
- ✅ Responsive design for authentication UI
- ✅ Accessible authentication forms
- ✅ Clear error messages and user feedback
- ✅ Session persistence across browser refreshes

### Technical Quality:
- ✅ TypeScript type safety throughout
- ✅ Proper error handling and loading states
- ✅ Integration with existing Chakra UI theme
- ✅ Follows React best practices and patterns
- ✅ Security-first approach with proper RLS compliance

## Risk Assessment

### Low Risk:
- Authentication context implementation (well-established pattern)
- Magic link integration (Supabase built-in feature)
- UI component creation (existing Chakra UI components)

### Medium Risk:
- RLS policy compatibility (requires testing with real users)
- Session management edge cases (token refresh, network issues)
- Callback URL handling (production vs development environments)

### Mitigation Strategies:
- Comprehensive testing with real authentication flows
- Fallback error handling for all auth operations
- Clear user feedback for all error states
- Development environment testing before production deployment

## Implementation Timeline

### Phase 1 (Authentication Context): 30 minutes
- Create auth context and provider
- Integrate with app providers

### Phase 2 (Authentication UI): 45 minutes  
- Create sign-in page with magic link
- Implement auth callback handling

### Phase 3 (Profile Integration): 30 minutes
- Update profile setup with real auth
- Add authentication guards

### Phase 4 (Testing & Validation): 30 minutes
- Test complete authentication flow
- Validate RLS policy compliance
- Verify photo upload functionality

**Total Estimated Time: 2 hours 15 minutes**

## Files to Create/Modify

### New Files:
1. `/lib/auth-context.tsx` - Authentication context and provider
2. `/app/auth/signin/page.tsx` - Magic link sign-in page
3. `/app/auth/callback/route.ts` - Authentication callback handler

### Modified Files:
1. `/app/providers.tsx` - Add AuthProvider wrapper
2. `/app/profile-setup/page.tsx` - Replace hardcoded user IDs with authenticated user

### Files to Review:
1. `/lib/supabase-client.ts` - Verify auth helpers are properly configured
2. `/storage/photo_upload.ts` - Ensure compatibility with authenticated uploads

This plan provides a complete, secure authentication system that will resolve all RLS policy violations while maintaining the existing user experience and design patterns.