# WingmanMatch Integration Testing Plan

## Objective
Create comprehensive integration tests for the WingmanMatch AI coaching system to validate Connell Barrett persona responses, safety guardrails, memory persistence, function calling, and error handling.

## Test Architecture Overview

### Core Components to Test
1. **Claude Agent** (`src/claude_agent.py`) - AI coach implementation
2. **Prompts System** (`src/prompts.py`) - Connell Barrett persona
3. **Safety Filters** (`src/safety_filters.py`) - PII protection and toxic content filtering
4. **Memory System** (`src/simple_memory.py`) - Conversation persistence and context retrieval
5. **Tools System** (`src/tools.py`) - Function calling for challenges and progress tracking

### Test Files to Create

#### 1. `/tests/test_coaching_integration.py`
**End-to-end coaching conversation tests**
- Test Connell Barrett persona consistency
- Validate coaching responses for different user archetypes
- Test conversation flow and memory continuity
- Validate context injection and personalization
- Test both streaming and non-streaming responses

#### 2. `/tests/test_safety_pipeline.py`
**Safety filter validation with real examples**
- Test PII detection (emails, phones, addresses)
- Test toxic masculinity content blocking
- Test pickup artist tactic detection
- Test safety message generation
- Test response filtering for coach outputs

#### 3. `/tests/test_memory_system.py`
**Memory persistence and context tests**
- Test conversation storage and retrieval
- Test deduplication logic
- Test session summarization
- Test coaching context assembly
- Test archetype and assessment data retrieval

#### 4. `/tests/test_coaching_scenarios.py`
**10 realistic coaching scenarios from prompts**
- Scenario: First approach anxiety
- Scenario: Confidence after rejection
- Scenario: Social skills development
- Scenario: Building authentic personality
- Scenario: Fear of judgment
- Scenario: Success celebration
- Scenario: Progress tracking
- Scenario: Goal setting
- Scenario: Breakthrough moments
- Scenario: Challenge planning

#### 5. `/manual_coaching_test.py`
**Interactive manual testing script**
- Command-line interface for live coaching testing
- Real-time conversation with Connell Barrett
- Safety filter demonstrations
- Function calling examples
- Memory system validation

## Implementation Details

### Test Structure Pattern
```python
class TestWingmanComponent:
    @pytest.fixture
    def setup_test_environment(self):
        # Mock external dependencies
        # Setup test database state
        # Initialize safety filters
        
    @pytest.mark.asyncio
    async def test_core_functionality(self):
        # Test core component behavior
        
    def test_error_handling(self):
        # Test graceful degradation
        
    def test_integration_points(self):
        # Test component interactions
```

### Mock Strategy
- Mock Anthropic API calls with realistic Connell Barrett responses
- Mock Supabase database with in-memory test data
- Mock safety filter responses for consistent testing
- Use actual prompts and logic for authentic testing

### Safety Testing Approach
- Test with realistic problematic inputs
- Validate safety message appropriateness
- Test edge cases and boundary conditions
- Ensure coaching quality maintained with safety active

### Memory Testing Strategy
- Test conversation persistence across sessions
- Test context retrieval for coaching continuity
- Test assessment and archetype integration
- Test session summarization accuracy

### Coaching Quality Validation
- Test persona consistency across conversations
- Test archetype-specific response variations
- Test coaching advice quality and appropriateness
- Test authentic vs manipulative guidance distinction

## Success Criteria

### 1. Coaching Conversation Flow ✅
- Connell Barrett persona maintained consistently
- Archetype personalization working correctly
- Memory continuity across sessions
- Natural conversation flow without technical artifacts

### 2. Safety Guardrails ✅
- PII detection blocks personal information sharing
- Toxic content filtered with appropriate guidance
- Pickup tactics redirected to authentic approaches
- Safety messages maintain coaching rapport

### 3. Memory System ✅
- Conversations persist correctly
- Context retrieval provides relevant information
- Deduplication prevents duplicate messages
- Session summaries capture key insights

### 4. Function Calling ✅
- Challenge tools provide appropriate difficulties
- Progress tracking records attempts accurately
- Session history maintains coaching continuity
- Tool integration enhances coaching experience

### 5. Error Handling ✅
- Graceful degradation when services unavailable
- User-friendly error messages
- System continues functioning with reduced capabilities
- Logs provide debugging information

## Test Data Requirements

### User Profiles
- Test users with different archetypes (1-6)
- Various confidence levels and dating goals
- Different experience levels and backgrounds

### Conversation Examples
- Typical coaching conversations
- Safety-triggering content examples
- Technical error scenarios
- Edge cases and boundary conditions

### Assessment Data
- Complete confidence assessments
- Archetype classifications
- Progress tracking data
- Challenge completion records

## Implementation Priority

1. **Core Coaching Integration** - Basic conversation flow
2. **Safety Pipeline** - PII and toxic content protection
3. **Memory System** - Conversation persistence
4. **Coaching Scenarios** - Realistic use cases
5. **Manual Testing** - Interactive validation tool

This plan ensures comprehensive coverage of the WingmanMatch coaching system while maintaining focus on authentic coaching quality and user safety.