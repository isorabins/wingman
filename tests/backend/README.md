# Backend Test Suite for WingmanMatcher Service

## Overview

This directory contains comprehensive unit and integration tests for the WingmanMatcher service and auto-match API endpoint.

## Test Files

### `test_matcher_service.py` - Unit Tests
Comprehensive unit tests for the WingmanMatcher service class including:

- **Service Initialization & Configuration**
  - WingmanMatcher setup with proper database client
  - Experience level mapping validation

- **Experience Level Compatibility Logic**
  - Same level or ±1 level matching rules
  - Beginner, intermediate, and advanced compatibility scenarios
  - Edge cases with incompatible experience levels

- **Throttling Enforcement**
  - One pending match per user rule
  - Existing match detection and return behavior
  - New match creation when no existing match

- **Recency Filtering**
  - 7-day exclusion rule for recent pairs
  - Cutoff date calculation verification
  - All recent pairs exclusion scenarios

- **Deterministic Selection**
  - Closest distance candidate selection
  - Consistent behavior with identical candidates
  - Fixed candidate pool testing

- **Auto-dependency Creation**
  - User profile creation for foreign key integrity
  - Existing profile skip logic
  - Integration with match creation flow

- **Error Handling**
  - Empty candidate pool scenarios
  - Invalid user profile handling
  - Database error graceful handling
  - Match creation failure scenarios

- **Match Record Operations**
  - Deterministic user ordering (alphabetical)
  - Duplicate match prevention
  - Database persistence validation

### `test_match_find_endpoint.py` - Integration Tests
End-to-end integration tests for the POST `/api/matches/auto/{user_id}` endpoint:

- **Successful Match Creation**
  - Complete request/response cycle testing
  - Database match record creation validation
  - Geographic and experience compatibility integration
  - Response format validation

- **Throttling Behavior**
  - Multiple requests return same match
  - Different users can create independent matches
  - Concurrent request handling

- **Recency Rules Integration**
  - Recent pairs exclusion from new matches
  - Old pairs re-matching allowance
  - Database historical match queries

- **Error Scenarios**
  - Invalid user ID format handling
  - Nonexistent user ID processing
  - Invalid radius parameter validation
  - No candidates within radius scenarios

- **Performance Testing**
  - Response time validation
  - Concurrent request handling
  - Load testing scenarios

## Running the Tests

### Prerequisites

```bash
# Install required dependencies
pip install pytest pytest-asyncio
```

### Unit Tests Only

```bash
# Run all unit tests
python -m pytest tests/backend/test_matcher_service.py -v

# Run specific test class
python -m pytest tests/backend/test_matcher_service.py::TestExperienceLevelCompatibility -v

# Run specific test
python -m pytest tests/backend/test_matcher_service.py::TestThrottlingEnforcement::test_existing_pending_match_returned -v
```

### Integration Tests Only

```bash
# Run all integration tests
python -m pytest tests/backend/test_match_find_endpoint.py -v

# Run specific test class
python -m pytest tests/backend/test_match_find_endpoint.py::TestAutoMatchErrorScenarios -v
```

### All Backend Tests

```bash
# Run complete backend test suite
python -m pytest tests/backend/ -v --tb=short

# Run with coverage (if coverage is installed)
python -m pytest tests/backend/ --cov=src/services/wingman_matcher --cov-report=html
```

### Development Testing

```bash
# Run tests with output capture for debugging
python -m pytest tests/backend/ -v -s

# Run tests with specific markers (if defined)
python -m pytest tests/backend/ -m "unit" -v

# Run tests with exit on first failure
python -m pytest tests/backend/ -x
```

## Test Configuration

### Environment Requirements

- **Backend Server**: Tests expect the FastAPI server to be running on `http://localhost:8000`
- **Database**: Supabase connection configured with proper environment variables
- **Test Data**: Some integration tests create and clean up test data automatically

### Mock Strategy

- **Unit Tests**: Extensively mock database operations and external dependencies
- **Integration Tests**: Use real database with automatic test data setup/cleanup
- **Performance Tests**: Create controlled test scenarios with known data sets

## Test Data Management

### Synthetic Test Users

Integration tests create test users with:
- Geographic distribution across SF Bay Area
- Varied experience levels (beginner, intermediate, advanced)
- Different confidence archetypes
- Proper location data with coordinates

### Cleanup Strategy

- **Automatic Cleanup**: Integration tests clean up created data after completion
- **Configurable**: Cleanup can be disabled via `TEST_CONFIG["cleanup_after_tests"] = False`
- **Safety**: Tests use unique UUIDs to avoid conflicts with real data

## Expected Results

### Test Coverage Summary

- **34+ passing tests** covering all critical functionality
- **Unit Tests**: 100% mock-based, fast execution
- **Integration Tests**: Real API endpoint validation
- **Error Scenarios**: Comprehensive edge case coverage
- **Performance**: Concurrent access and response time validation

### Known Limitations

- Some integration tests depend on database state
- Redis-related warnings for rate limiting (non-blocking)
- Async fixture warnings in pytest (future compatibility)

## Contributing

When adding new tests:

1. Follow existing naming conventions (`test_<functionality>_<scenario>`)
2. Use appropriate mocking for unit tests
3. Include proper setup/cleanup for integration tests
4. Add docstrings explaining test purpose and expected behavior
5. Ensure tests are deterministic and repeatable

## Debugging

### Common Issues

1. **Import Errors**: Ensure `src` directory is in Python path
2. **Database Errors**: Verify Supabase configuration and connectivity
3. **Patch Failures**: Check import paths match actual module structure
4. **Async Warnings**: Use `@pytest.mark.asyncio` for async test functions

### Logging

Tests capture application logs. To see debug output:

```bash
python -m pytest tests/backend/ -v -s --log-cli-level=DEBUG
```