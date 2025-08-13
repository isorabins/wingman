# Connell Barrett Coaching System Completion Plan

## Executive Summary
Complete the final components for the WingmanMatch dating confidence coaching platform by implementing safety filters, testing framework, context optimization, and A/B testing infrastructure. This will finalize the Connell Barrett coaching system integration.

## Implementation Plan

### 1. Safety Filters System (`src/safety_filters.py`)
**Objective**: Implement comprehensive safety guardrails for respectful dating guidance

**Components**:
- PII detection and blocking (phone numbers, emails, addresses)
- Content filtering against pickup artist/misogynistic language
- Respectful guidance enforcement
- Toxic masculinity detection and redirection
- Consent and respect validation

**Technical Approach**:
- Create filter classes for each safety concern
- Use regex patterns for PII detection
- Build keyword/phrase blacklists for problematic content
- Implement scoring system for content toxicity
- Return filtered content with safety guidance

**Integration Points**:
- Hook into `claude_agent.py` before processing user input
- Hook into `claude_agent.py` before returning coach responses
- Log safety violations for monitoring

### 2. Prompt Testing Framework (`tests/test_prompts.py`)
**Objective**: Comprehensive testing for prompt behavior and safety

**Test Categories**:
- Memory context references work correctly
- Archetype personalization consistency
- Safety guardrail triggers and responses
- Conversation continuity across sessions
- Manual evaluation set with sample coaching inputs

**Technical Approach**:
- Use pytest with async support
- Mock Anthropic API responses for deterministic testing
- Create test fixtures for different archetypes
- Build assertion helpers for prompt behavior validation
- Implement scoring system for response quality

**Test Data**:
- 10 sample coaching scenarios covering different archetypes
- Edge cases for safety violations
- Context injection scenarios
- Conversation continuity tests

### 3. Context Optimization (`src/context_formatter.py`)
**Objective**: Optimize coaching context for Claude API prompt caching

**Features**:
- Format coaching context for prompt caching
- Integrate assessment results, attempts, triggers, session history
- Optimize context size and structure for caching
- Handle missing context gracefully

**Technical Approach**:
- Create structured context formatting
- Implement prompt caching strategies
- Add context compression for large histories
- Provide fallback for missing data

**Integration**:
- Replace existing context formatting in `claude_agent.py`
- Maintain backward compatibility
- Add performance monitoring

### 4. A/B Testing Infrastructure (`config.py` updates)
**Objective**: Enable testing different coaching approaches

**Features**:
- ENABLE_NEW_COACH_PROMPTS flag for staging
- Old/new prompt comparison capability
- Feature flag for testing Connell vs other coaching styles
- A/B test result tracking

**Technical Approach**:
- Add configuration flags to `Config` class
- Implement prompt version switching
- Add A/B test tracking to memory system
- Create performance comparison tools

## Implementation Timeline

**Phase 1**: Safety Filters (Day 1)
- Create safety filter classes
- Implement PII detection
- Build content filtering
- Add integration hooks

**Phase 2**: Testing Framework (Day 1-2)  
- Set up test structure
- Create test fixtures
- Implement prompt tests
- Add manual evaluation set

**Phase 3**: Context Optimization (Day 2)
- Create context formatter
- Implement prompt caching
- Add performance monitoring
- Update integration points

**Phase 4**: A/B Testing Setup (Day 2-3)
- Add configuration flags
- Implement version switching
- Add tracking infrastructure
- Test deployment readiness

## Quality Standards

- **Safety**: All content must pass safety filters
- **Testing**: 100% test coverage for new components
- **Performance**: Context optimization must improve response times
- **Integration**: Seamless integration with existing WingmanMatch infrastructure
- **Documentation**: Clear integration guides for each component

## Risk Mitigation

- **Safety Filter False Positives**: Implement severity levels and override mechanisms
- **Performance Impact**: Use async processing and caching
- **Integration Complexity**: Maintain backward compatibility
- **Testing Coverage**: Comprehensive test scenarios for edge cases

## Success Criteria

- All safety filters operational and tested
- Comprehensive test suite with >95% coverage
- Context optimization improves prompt caching efficiency
- A/B testing infrastructure enables experimentation
- All components integrate seamlessly with existing system
- Performance metrics show no degradation
- Documentation enables future maintenance and extension

## Dependencies

- Existing WingmanMatch infrastructure
- Anthropic Claude API integration
- Supabase database schema
- Pytest testing framework
- FastAPI application structure

## Next Steps After Completion

1. Deploy to staging environment
2. Run comprehensive safety testing
3. Enable A/B testing with small user cohort
4. Monitor performance and safety metrics
5. Gradually rollout to full user base