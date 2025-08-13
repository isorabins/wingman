# Confidence Assessment Test Suite

Comprehensive test suite for the confidence assessment page (`app/confidence-test/page.tsx`) ensuring reliability, accessibility, and performance.

## Test Structure

### Core Test Files

- **`confidence-test.spec.ts`** - Main component testing with complete user flows
- **`confidence-accessibility.spec.ts`** - Accessibility compliance and screen reader support
- **`confidence-edge-cases.spec.ts`** - Error handling and edge case scenarios
- **`confidence-performance.spec.ts`** - Performance benchmarks and optimization validation
- **`confidence-integration.spec.ts`** - End-to-end integration and real-world scenarios

### Supporting Files

- **`setup.ts`** - Test environment configuration and global mocks
- **`test-utils.ts`** - Shared utilities, mock data, and helper functions

## Test Coverage

### ✅ User Journey Testing
- Complete assessment flow (welcome → questions → results)
- All 6 archetype calculations (Analyzer, Sprinter, Ghost, Naturalist, Scholar, Protector)
- Form validation and error states
- Navigation between questions
- Progress tracking and indicators

### ✅ Accessibility Testing (WCAG 2.1 Compliance)
- Keyboard navigation support
- Screen reader compatibility
- ARIA attributes and roles
- Focus management
- Color contrast requirements
- Reduced motion support

### ✅ Error Handling
- Network failures and API errors
- Malformed data scenarios
- Missing archetype information
- Browser compatibility issues
- Graceful degradation

### ✅ Performance Testing
- Initial render speed (<50ms)
- Large dataset handling
- Memory leak prevention
- Rapid interaction handling
- Bundle size optimization

### ✅ Integration Testing
- Analytics event tracking
- API endpoint integration
- Theme and styling consistency
- Mobile and responsive design
- Cross-browser compatibility

## Running Tests

### Basic Commands
```bash
# Run all confidence tests
npm run test:confidence

# Run tests in watch mode
npm run test

# Run with UI
npm run test:ui

# Generate coverage report
npm run test:coverage
```

### Specific Test Categories
```bash
# Core functionality tests
npx vitest app/confidence-test/__tests__/confidence-test.spec.ts

# Accessibility tests only
npx vitest app/confidence-test/__tests__/confidence-accessibility.spec.ts

# Performance tests only
npx vitest app/confidence-test/__tests__/confidence-performance.spec.ts

# Edge cases and error handling
npx vitest app/confidence-test/__tests__/confidence-edge-cases.spec.ts

# Integration scenarios
npx vitest app/confidence-test/__tests__/confidence-integration.spec.ts
```

## Test Data and Mocks

### Mock Questions Data
- **`fullMockQuestionsData`** - Complete 12-question dataset for testing
- **`mockQuestionsData`** - Simplified 2-question dataset for quick tests
- All 6 archetypes with proper scoring mapping
- Realistic question text and answer options

### Mock Functions
- **`createMockFetch()`** - Configurable fetch mock for API testing
- **`createAnalyticsMock()`** - GTM/GA analytics event tracking mock
- **`answerAllQuestionsForArchetype()`** - Generate archetype-specific answer sets

### Environment Mocks
- Next.js router mocking
- Chakra UI provider mocking
- Window.gtag analytics mocking
- Browser API mocking (localStorage, fetch, etc.)

## Key Test Scenarios

### Critical User Paths
1. **Complete Happy Path**: Start → Answer all 12 questions → Get results
2. **Validation Flow**: Try to submit incomplete → See error → Complete → Success
3. **Navigation Flow**: Answer → Go back → Change answer → Continue
4. **Error Recovery**: API fails → See error → Local calculation fallback

### Archetype Validation
Each archetype (Analyzer, Sprinter, Ghost, Naturalist, Scholar, Protector) is tested for:
- Correct answer mapping
- Scoring algorithm accuracy
- Results display formatting
- Experience level calculation

### Accessibility Scenarios
- **Keyboard Only**: Complete assessment using only keyboard navigation
- **Screen Reader**: Proper announcements and ARIA support
- **High Contrast**: Visual accessibility requirements
- **Reduced Motion**: Respects user preferences

### Performance Benchmarks
- Initial render: <50ms
- Question loading: <100ms
- Answer selection: <50ms response time
- Memory usage: No significant leaks
- Large datasets: Handle 500+ questions efficiently

## Debugging and Troubleshooting

### Common Issues
1. **Mock fetch not working**: Ensure `setup.ts` is properly imported
2. **Chakra UI rendering errors**: Check theme provider wrapping
3. **Analytics events not firing**: Verify gtag mock setup
4. **Accessibility failures**: Use screen reader testing tools

### Debug Mode
```bash
# Run tests with debug output
npx vitest --reporter=verbose

# Run single test with full output
npx vitest app/confidence-test/__tests__/confidence-test.spec.ts --reporter=verbose
```

### Performance Profiling
```bash
# Run performance tests with detailed timing
npx vitest app/confidence-test/__tests__/confidence-performance.spec.ts --reporter=verbose
```

## Continuous Integration

### Required Checks
- [ ] All tests pass (100%)
- [ ] Accessibility score ≥95%
- [ ] Performance benchmarks met
- [ ] No memory leaks detected
- [ ] Cross-browser compatibility verified

### Pre-commit Hooks
```bash
# Run before committing
npm run test:confidence
npm run lint
```

## Extending Tests

### Adding New Test Cases
1. Follow existing patterns in `confidence-test.spec.ts`
2. Use helper functions from `test-utils.ts`
3. Include accessibility considerations
4. Add performance impact assessment

### Custom Mock Data
```typescript
// Create scenario-specific mock data
const customMockData = {
  questions: [...],
  archetypes: {...}
}
const mockFetch = createMockFetch(customMockData)
```

### New Archetype Testing
When adding new archetypes:
1. Update `test-utils.ts` with new archetype mapping
2. Add archetype-specific test cases
3. Update scoring algorithm tests
4. Verify results display formatting

## Quality Standards

### Coverage Requirements
- Unit tests: 95%+ line coverage
- Integration tests: All critical user paths
- Accessibility: WCAG 2.1 AA compliance
- Performance: All benchmarks met

### Best Practices
- Test user behavior, not implementation details
- Use semantic queries (getByRole, getByLabelText)
- Mock external dependencies
- Test error states and edge cases
- Ensure tests are fast and reliable

## Related Documentation
- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [Testing Library Best Practices](https://testing-library.com/docs/guiding-principles)
- [Vitest Documentation](https://vitest.dev/guide/)
- [Chakra UI Testing](https://chakra-ui.com/docs/styled-system/style-props)

---

*This test suite ensures the confidence assessment provides a reliable, accessible, and performant user experience across all browsers and devices.*