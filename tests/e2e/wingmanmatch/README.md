# WingmanMatch E2E Test Suite

## Overview

This comprehensive end-to-end test suite covers the complete WingmanMatch user journey: **SIGNUP→PROFILE→MATCH→CHAT**. The test suite validates the core platform functionality through automated browser testing using Playwright.

## Test Structure

### Individual Journey Tests

| Test File | Purpose | Coverage |
|-----------|---------|----------|
| `01-signup-flow.spec.ts` | Authentication & user creation | Magic link auth, test users, error handling |
| `02-profile-creation.spec.ts` | Profile setup & validation | Bio validation, location services, form submission |
| `03-match-discovery.spec.ts` | Match finding & filtering | Location-based matching, candidate display |
| `04-match-selection.spec.ts` | Match interaction & selection | Accept/decline workflow, API integration |
| `05-chat-initiation.spec.ts` | Chat functionality | Message sending, rate limiting, UI validation |
| `06-full-journey.spec.ts` | Complete user journey | End-to-end flow, performance benchmarks |

### Helper Modules

| File | Purpose |
|------|---------|
| `helpers/test-data.ts` | Test data, validation patterns, mock responses |
| `helpers/synthetic-users.ts` | User creation, authentication, profile management |
| `helpers/geolocation-mock.ts` | Location mocking, coordinate simulation |
| `fixtures/user-fixtures.ts` | Playwright fixtures, test setup utilities |
| `fixtures/database-cleanup.ts` | Database cleanup, test isolation |

## Quick Start

### Prerequisites

1. **Playwright Installation**:
   ```bash
   npm install @playwright/test
   npx playwright install
   ```

2. **Environment Setup**:
   ```bash
   # Required environment variables
   export TEST_BASE_URL="http://localhost:3000"
   export TEST_API_URL="http://localhost:8000"
   export NEXT_PUBLIC_SUPABASE_URL="your-supabase-url"
   ```

3. **Backend Services**:
   - WingmanMatch backend running on port 8000
   - Test authentication endpoint (`/auth/test-login`) available
   - Database with test data capabilities

### Running Tests

```bash
# Run all WingmanMatch tests
npx playwright test tests/e2e/wingmanmatch/

# Run specific test suite
npx playwright test tests/e2e/wingmanmatch/01-signup-flow.spec.ts

# Run with UI mode
npx playwright test tests/e2e/wingmanmatch/ --ui

# Run full journey test only
npx playwright test tests/e2e/wingmanmatch/06-full-journey.spec.ts
```

### Debug Mode

```bash
# Run with debug mode
npx playwright test tests/e2e/wingmanmatch/ --debug

# Generate test report
npx playwright show-report
```

## Test Configuration

### Playwright Config

The tests use the following configuration:

```typescript
{
  timeout: 30000,        // 30 second test timeout
  retries: 2,           // Retry failed tests twice
  workers: 2,           // Parallel execution
  trace: 'on-first-retry', // Capture traces on retry
  screenshot: 'only-on-failure' // Screenshots on failure
}
```

### Test Data

Tests use synthetic data defined in `helpers/test-data.ts`:

- **Users**: 4 test user profiles (Alex, Jordan, Taylor, Casey)
- **Locations**: SF Bay Area coordinates for geographic testing
- **Messages**: Predefined chat messages for conversation testing
- **Validation**: Input validation patterns and error scenarios

## Key Features

### 🔐 Authentication Testing

- **Magic Link Flow**: Tests email-based authentication
- **Test Mode**: Uses `/auth/test-login` endpoint for reliable testing
- **Session Management**: Browser authentication state handling
- **Route Protection**: Validates protected page access

### 👤 Profile Management

- **Form Validation**: Bio requirements, character limits, PII detection
- **Location Services**: Geolocation mocking, privacy modes
- **Photo Upload**: File validation, size limits (mocked for testing)
- **API Integration**: Profile completion endpoint validation

### 🎯 Match Discovery

- **Geographic Filtering**: Location-based candidate discovery
- **Radius Testing**: Different distance parameters
- **Empty States**: Graceful handling of no candidates
- **Performance**: API response time validation

### 🤝 Match Selection

- **Accept/Decline Flow**: Complete match response workflow
- **State Management**: Match status transitions
- **Error Handling**: Network failures, invalid matches
- **UI Feedback**: Loading states, success/error messages

### 💬 Chat Functionality

- **Message Sending**: Text input validation, character limits
- **Rate Limiting**: 1 message per 0.5 seconds enforcement
- **Real-time Simulation**: Message delivery simulation
- **Venue Suggestions**: Static panel with categorized venues

### 🔄 Full Journey Integration

- **End-to-End Flow**: Complete SIGNUP→PROFILE→MATCH→CHAT
- **Performance Benchmarks**: Step-by-step timing validation
- **Interruption Recovery**: Session restoration testing
- **Independent Execution**: Each step can run standalone

## Advanced Features

### Synthetic User Management

```typescript
// Create authenticated user with profile
const user = await createAuthenticatedUser(page, {
  useFixedProfile: 'alex'
})

// Create matched user pair
const [user1, user2, matchId] = await createMatchedUserPair(page)

// Switch between users in same test
await syntheticUsers.switchToUser(page, user2)
```

### Geolocation Mocking

```typescript
// Set specific test location
await setupLocationMocking(page, 'sanFrancisco')

// Mock location errors
await mockLocationPermissionDenied(page)
await mockLocationTimeout(page)

// Simulate location movement
await GeolocationMocker.simulateLocationMovement(context, locations)
```

### Database Cleanup

```typescript
// Register for cleanup
DatabaseCleaner.registerUserForCleanup(userId)
DatabaseCleaner.registerMatchForCleanup(matchId)

// Manual cleanup
await DatabaseCleaner.cleanupUser(page, userId)
await DatabaseCleaner.cleanupAll(page)
```

## Performance Benchmarks

The test suite validates performance against these thresholds:

| Operation | Threshold | Purpose |
|-----------|-----------|---------|
| Page Load | < 3 seconds | Initial page rendering |
| API Response | < 1 second | Backend response time |
| Form Interaction | < 100ms | UI responsiveness |
| Chat Message | < 2 seconds | Message delivery |
| Full Journey | < 10 seconds | Complete user flow |

## Error Handling

### Network Failures
- API timeout simulation
- Connection error recovery
- Graceful degradation testing

### Invalid Inputs
- Form validation testing
- SQL injection prevention
- XSS attack prevention

### Authentication Issues
- Session expiration handling
- Invalid token scenarios
- Permission denied cases

## Test Isolation

### Worker-Scoped Fixtures
- Each test worker has isolated database state
- Automatic cleanup between tests
- Parallel execution safety

### Synthetic Users
- Unique test users per test
- Automatic user cleanup
- No test data conflicts

### Mocked Services
- External API mocking
- Predictable test conditions
- Network independence

## Debugging

### Screenshot Capture
- Automatic screenshots on test failure
- Manual screenshot capture capability
- Step-by-step visual debugging

### Trace Files
- Full browser interaction traces
- Network request/response logs
- Console error capture

### Logging
- Comprehensive test step logging
- Performance timing logs
- Error context information

## CI/CD Integration

### GitHub Actions

```yaml
- name: Run E2E Tests
  run: npx playwright test tests/e2e/wingmanmatch/
  env:
    TEST_BASE_URL: ${{ secrets.TEST_BASE_URL }}
    TEST_API_URL: ${{ secrets.TEST_API_URL }}
```

### Test Reports
- HTML reports with screenshots
- JUnit XML for CI integration
- Performance metrics tracking

## Maintenance

### Adding New Tests

1. **Follow naming convention**: `##-test-name.spec.ts`
2. **Use existing fixtures**: Import from `./fixtures/user-fixtures`
3. **Include performance tests**: Add timing validations
4. **Add cleanup**: Register any created resources

### Updating Test Data

1. **Modify `helpers/test-data.ts`**: Update user profiles, messages
2. **Update validation patterns**: Adjust for new requirements
3. **Update API endpoints**: Keep endpoint list current

### Debugging Test Failures

1. **Check screenshots**: Review failure screenshots in test-results/
2. **Review traces**: Use `npx playwright show-trace trace.zip`
3. **Check logs**: Review console output for error context
4. **Verify environment**: Ensure backend services are running

## Best Practices

### Test Writing
- ✅ Use descriptive test names
- ✅ Include performance assertions
- ✅ Add screenshot capture on failure
- ✅ Test error scenarios
- ✅ Clean up test data

### Test Maintenance
- ✅ Keep tests independent
- ✅ Use stable selectors
- ✅ Mock external dependencies
- ✅ Regular test data cleanup
- ✅ Update with UI changes

### Performance
- ✅ Minimize test execution time
- ✅ Use parallel execution
- ✅ Cache test fixtures
- ✅ Optimize API calls
- ✅ Profile test performance

## Troubleshooting

### Common Issues

**Authentication Failures**:
- Verify test auth endpoint is available
- Check environment variables
- Review browser session storage

**Test Timeouts**:
- Increase timeout for slow operations
- Check network conditions
- Verify backend service availability

**Flaky Tests**:
- Add proper wait conditions
- Increase retry attempts
- Review timing-dependent operations

**Database Issues**:
- Verify cleanup is working
- Check test data isolation
- Review RLS policies

### Support

For issues with the test suite:

1. **Check logs**: Review test execution logs
2. **Verify environment**: Ensure all services are running
3. **Update dependencies**: Keep Playwright up to date
4. **Review documentation**: Check for recent changes

---

## Test Statistics

- **Total Test Files**: 6
- **Test Cases**: ~35 individual tests
- **Coverage**: Complete user journey
- **Execution Time**: ~2-5 minutes for full suite
- **Supported Browsers**: Chromium, Firefox, WebKit

**Last Updated**: August 17, 2025  
**Version**: 1.0.0  
**Playwright Version**: Latest