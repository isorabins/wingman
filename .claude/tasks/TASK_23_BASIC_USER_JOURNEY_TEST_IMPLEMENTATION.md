# Task 23: Basic User Journey Test Implementation

## Objective
Create a comprehensive E2E test suite under `tests/e2e/wingmanmatch/` covering the essential user journey: **SIGNUP→PROFILE→MATCH→CHAT**

## Domain Analysis

### Test Architecture Requirements
- **Framework**: Playwright TypeScript (existing framework)
- **Test Isolation**: Worker-scoped fixtures with database cleanup
- **Authentication**: Test mode with synthetic users
- **Geolocation**: Mock location data for match discovery
- **Retry Strategy**: trace: 'on-first-retry', retries=2
- **Screenshots**: Capture on failure for debugging

### API Endpoints to Test
- `/auth/test-login` - Authentication
- `/api/profile/complete` - Profile setup  
- `/api/matches/candidates/{user_id}` - Match discovery
- `/api/buddy/respond` - Match selection
- `/api/chat/send` - Chat functionality

### Frontend Pages to Test
- `/auth/signin` - Signup flow
- `/profile-setup` - Profile creation
- `/matches` or match discovery interface
- `/buddy-chat/[matchId]` - Chat interface

## Implementation Plan

### 1. Test Directory Structure
```
tests/e2e/wingmanmatch/
├── 01-signup-flow.spec.ts
├── 02-profile-creation.spec.ts  
├── 03-match-discovery.spec.ts
├── 04-match-selection.spec.ts
├── 05-chat-initiation.spec.ts
├── 06-full-journey.spec.ts
├── helpers/
│   ├── test-data.ts
│   ├── synthetic-users.ts
│   └── geolocation-mock.ts
└── fixtures/
    ├── user-fixtures.ts
    └── database-cleanup.ts
```

### 2. Subtask Implementation Details

#### Subtask 23.1: Basic Signup Flow Test
- **File**: `01-signup-flow.spec.ts`
- **Coverage**: Magic link authentication, test user creation
- **Validation**: User can complete signup with valid credentials
- **Screenshots**: Successful signup completion
- **Mock Strategy**: Use existing `/auth/test-login` endpoint

#### Subtask 23.2: Basic Profile Creation Test
- **File**: `02-profile-creation.spec.ts`
- **Coverage**: Profile form completion, required fields only
- **Dependencies**: Builds on signup test user
- **Validation**: Profile creation completes successfully
- **Screenshots**: Completed profile verification

#### Subtask 23.3: Basic Match Discovery Test
- **File**: `03-match-discovery.spec.ts`
- **Coverage**: Match discovery interface, location-based filtering
- **Dependencies**: User with completed profile
- **Geolocation**: Mock SF Bay Area coordinates
- **Validation**: Match discovery loads correctly

#### Subtask 23.4: Basic Match Selection Test
- **File**: `04-match-selection.spec.ts`
- **Coverage**: Match selection from discovery interface
- **Dependencies**: Available matches from discovery
- **Validation**: User can select match successfully
- **Screenshots**: Successful match selection

#### Subtask 23.5: Basic Chat Initiation Test
- **File**: `05-chat-initiation.spec.ts`
- **Coverage**: Chat interface, message sending
- **Dependencies**: Matched users from previous test
- **Validation**: Chat opens correctly, simple message sent
- **Rate Limiting**: Respect 1 message per 0.5s limit

#### Subtask 23.6: Full Journey Test Runner
- **File**: `06-full-journey.spec.ts`
- **Coverage**: Complete SIGNUP→PROFILE→MATCH→CHAT flow
- **Dependencies**: All previous subtests pass
- **Execution**: Sequential or independent execution modes
- **Cleanup**: Proper teardown after complete journey

### 3. Test Infrastructure Components

#### Synthetic User Strategy
```typescript
interface SyntheticUser {
  email: string
  userId: string
  profile: UserProfile
  location: GeolocationCoordinates
  accessToken: string
}
```

#### Database Setup/Cleanup
```typescript
// Worker-scoped fixtures for test isolation
// Cleanup patterns from existing tests
// Auto-dependency creation for test data
```

#### Geolocation Mocking
```typescript
// Mock SF Bay Area coordinates
// Match radius testing scenarios
// Location privacy mode testing
```

### 4. Quality Standards

#### Test Stability Requirements
- **Retry Logic**: 2 retries with trace capture
- **Timeouts**: Appropriate timeouts for each operation
- **Error Handling**: Graceful failure handling
- **Isolation**: Each test can run independently

#### Performance Requirements
- **Test Execution**: Complete suite < 5 minutes
- **Individual Tests**: Each test < 30 seconds
- **API Response**: Validate reasonable response times
- **UI Interactions**: No blocking or hanging states

#### Documentation Requirements
- **Test Descriptions**: Clear test purpose and coverage
- **Failure Debugging**: Screenshot capture on failure
- **Setup Instructions**: Clear execution documentation
- **CI Integration**: Ready for continuous integration

## Technical Implementation Strategy

### Phase 1: Foundation Setup
1. Create test directory structure
2. Set up synthetic user creation helpers
3. Configure geolocation mocking
4. Implement database cleanup fixtures

### Phase 2: Individual Subtask Implementation
1. Implement each subtask test file
2. Validate individual test execution
3. Ensure proper test isolation
4. Add screenshot capture on failure

### Phase 3: Integration and Validation
1. Implement full journey test runner
2. Validate complete user flow
3. Test sequential and independent execution
4. Performance and reliability testing

### Phase 4: Documentation and CI
1. Document test execution procedures
2. Configure CI integration settings
3. Create troubleshooting guide
4. Validate deployment pipeline compatibility

## Success Criteria
- ✅ All 6 subtasks implemented as individual test files
- ✅ Complete user journey working from signup to chat
- ✅ Test stability with proper retry and error handling
- ✅ Screenshot capture for failure documentation
- ✅ Database isolation with proper test fixtures
- ✅ Geolocation mocking for match discovery
- ✅ CI integration ready configuration

## Risk Mitigation
- **Authentication Issues**: Use existing test auth infrastructure
- **Match Creation**: Create test match scenarios programmatically
- **Chat Testing**: Focus on basic message flow, avoid complex features
- **Geolocation**: Mock coordinates to avoid browser permission issues
- **Database Conflicts**: Use worker-scoped fixtures for isolation

## Dependencies
- Existing Playwright framework in `tests/e2e/`
- Test authentication endpoint `/auth/test-login`
- Backend APIs for profile, matches, and chat
- Frontend pages for complete user journey
- Database cleanup utilities from existing tests

This plan provides a comprehensive approach to implementing the basic user journey test suite while leveraging existing test infrastructure and ensuring stability and reliability.