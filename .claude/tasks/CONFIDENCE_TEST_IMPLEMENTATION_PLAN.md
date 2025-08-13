# Confidence Assessment Frontend Testing Implementation Plan

## Overview
Create comprehensive tests for the confidence assessment page (`app/confidence-test/page.tsx`) that was just implemented. This includes setting up the testing infrastructure and creating thorough test coverage for all user interactions and edge cases.

## Current State Analysis
- **Component**: `app/confidence-test/page.tsx` is implemented with 12-question assessment flow
- **Tech Stack**: Next.js 14, React 18, Chakra UI, TypeScript
- **Testing Needs**: No testing infrastructure currently set up in this project
- **Reference**: Similar Vitest setup exists in `/reference_files/frontend_reference/FAF_website/`

## Implementation Plan

### Phase 1: Testing Infrastructure Setup (30 mins)
**1.1 Install Testing Dependencies**
```bash
npm install --save-dev \
  vitest \
  @vitejs/plugin-react \
  @testing-library/react \
  @testing-library/jest-dom \
  @testing-library/user-event \
  jsdom \
  msw
```

**1.2 Create Configuration Files**
- `vitest.config.ts` - Vitest configuration with jsdom environment
- `app/confidence-test/__tests__/setup.ts` - Test setup with mocks
- Update `package.json` with test scripts

**1.3 Mock Setup**
- Mock Next.js router
- Mock Chakra UI toast
- Mock fetch for API calls
- Mock window.gtag for analytics

### Phase 2: Core Component Testing (45 mins)
**2.1 Basic Rendering Tests**
- Test welcome screen renders correctly
- Test question progression (1-12)
- Test results screen display
- Test navigation between screens

**2.2 Question Flow Tests** 
- Test answering all 12 questions progresses correctly
- Test progress indicator updates (1/12 → 12/12)
- Test back/forward navigation between questions
- Test submit button states (disabled/enabled)

### Phase 3: User Interaction Testing (60 mins)
**3.1 Complete Assessment Flow**
- Test full user journey from welcome to results
- Test each archetype can be calculated (6 different paths)
- Test analytics events fire correctly (assessment_started, assessment_completed)
- Test submission with all questions answered

**3.2 Form Validation Tests**
- Test incomplete forms cannot be submitted
- Test toast appears for incomplete submission
- Test radio button selection updates state
- Test answer persistence during navigation

### Phase 4: Error Handling & Edge Cases (45 mins)
**4.1 API Error Handling**
- Mock API failure scenarios
- Test toast error messages display
- Test graceful degradation when API unavailable
- Test local archetype calculation fallback

**4.2 Edge Cases**
- Test with malformed questions data
- Test with missing archetype data
- Test rapid clicking/double submission
- Test browser back/forward navigation

### Phase 5: Accessibility Testing (30 mins)
**5.1 Keyboard Navigation**
- Test tab navigation through questions
- Test arrow key navigation in radio groups
- Test enter/space for selection
- Test escape key behavior

**5.2 ARIA & Screen Reader Support**
- Test radio groups have proper ARIA attributes
- Test progress announcements
- Test focus management during navigation
- Test screen reader friendly text

### Phase 6: Visual & UI Testing (30 mins)
**6.1 Responsive Design**
- Test layout on different screen sizes
- Test mobile-friendly interactions
- Test touch targets are accessible

**6.2 Theme Integration**
- Test proper color usage from theme
- Test typography from theme tokens
- Test spacing consistency

### Phase 7: Performance & Analytics (30 mins)
**7.1 Performance Tests**
- Test component renders within reasonable time
- Test question loading performance
- Test large datasets don't cause issues

**7.2 Analytics Integration**
- Test GTM/GA events fire correctly
- Test event data includes proper context
- Test analytics work without breaking functionality

## Test File Structure
```
app/confidence-test/__tests__/
├── confidence-test.spec.ts (main test file)
├── test-utils.ts (helper functions)
├── mocks/
│   ├── questions.mock.ts
│   ├── api.mock.ts
│   └── analytics.mock.ts
└── setup.ts (test environment setup)
```

## Key Test Scenarios

### Critical User Journeys
1. **Happy Path**: Answer all 12 questions → Get archetype result
2. **Incomplete Submission**: Try to submit early → See validation error
3. **Navigation**: Go back/forward through questions → Answers persist
4. **API Failure**: Submit when API down → See local calculation
5. **Accessibility**: Navigate with keyboard only → All functions work

### Archetype Testing
Test each of the 6 archetypes can be calculated:
- **Analyzer**: Methodical, research-driven responses
- **Sprinter**: Action-oriented responses  
- **Ghost**: Introverted, cautious responses
- **Naturalist**: Authentic, instinctive responses
- **Scholar**: Knowledge-focused responses
- **Protector**: Caring, relationship-focused responses

### Validation Scenarios
- Submit with 0 answers → Error toast
- Submit with 11/12 answers → Error toast
- Submit with all 12 answers → Success flow
- Navigate without answering → Progress saves correctly

## Success Criteria
- [ ] All tests pass consistently
- [ ] 95%+ code coverage for confidence-test component
- [ ] All user interactions tested
- [ ] Error handling comprehensive
- [ ] Accessibility requirements met (keyboard nav, ARIA)
- [ ] Visual regression tests for key screens
- [ ] Performance tests pass
- [ ] Analytics integration verified

## Risk Mitigation
- **Chakra UI Mocking**: Use reference FAF setup patterns
- **API Integration**: Mock all external calls with MSW
- **Analytics Testing**: Mock gtag to avoid external dependencies
- **Flaky Tests**: Use stable selectors and proper async handling

## Timeline: 4-5 hours total
- Phase 1 (Setup): 30 mins
- Phase 2 (Core): 45 mins  
- Phase 3 (Interactions): 60 mins
- Phase 4 (Errors): 45 mins
- Phase 5 (A11y): 30 mins
- Phase 6 (Visual): 30 mins
- Phase 7 (Performance): 30 mins

## Dependencies
- Questions data structure in `questions.v1.json`
- Archetype calculation logic in component
- Theme tokens from `app/theme.ts`
- API endpoint contracts (if implemented)

---

*This plan ensures comprehensive testing coverage while following React Testing Library best practices and accessibility standards.*