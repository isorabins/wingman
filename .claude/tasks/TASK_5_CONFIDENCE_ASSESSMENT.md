# Task 5: Confidence Assessment Agent and Flow Implementation Plan

## Overview
Implement a comprehensive dating confidence assessment system for WingmanMatch, including 12-question confidence assessment, scoring functions, agent integration, FastAPI endpoints, and persistence layer.

## Architecture Analysis
Based on examination of existing codebase:
- **Reference Pattern**: `reference_files/src/agents/creativity_agent.py` - Complete assessment agent structure  
- **Scoring Pattern**: Pure function approach for deterministic results
- **API Pattern**: `reference_files/src/main.py` - FastAPI + Pydantic v2 endpoints
- **Persistence**: Supabase tables with JSON storage for answers and structured results

## Technical Stack Requirements
- **Backend**: FastAPI with async patterns (following `src/main.py`)
- **Database**: Supabase PostgreSQL with `confidence_test_results` table
- **AI Integration**: Following existing Claude agent patterns (`src/claude_agent.py`)
- **Validation**: Pydantic v2 models for request/response validation
- **Testing**: Unit tests following TDD approach

## Implementation Plan

### Phase 1: Foundation & Pure Functions (2-3 hours)
**1.1 Design Confidence Assessment Questions (45 mins)**
- Research Connell Barrett's 6 confidence archetypes:
  - **Analyzer**: Methodical, research-driven approach to dating
  - **Sprinter**: Action-oriented, fast-moving confidence style  
  - **Ghost**: Introverted, thoughtful, selective approach
  - **Scholar**: Knowledge-focused, learning-based confidence
  - **Naturalist**: Authentic, instinctive dating approach
  - **Protector**: Caring, relationship-focused confidence style

- Create 12 multiple-choice questions covering dating confidence scenarios:
  - Approaching someone new
  - Handling rejection
  - First date anxiety
  - Conversation confidence
  - Self-presentation
  - Dating app interactions
  - Relationship building
  - Conflict resolution
  - Expressing interest
  - Setting boundaries
  - Social situations
  - Long-term confidence

**1.2 Implement Pure Scoring Functions (60 mins)**
- **File**: `src/assessment/confidence_scoring.py`
- **Functions**:
  - `score_answers(answers: List[str]) -> Dict[str, int]` - Convert answers to archetype scores
  - `choose_archetype(scores: Dict[str, int]) -> str` - Select primary archetype 
  - `compute_level(scores: Dict[str, int], total_questions: int) -> str` - Determine experience level
- **Design**: Deterministic mapping with clear weighting system
- **Testing**: Each function individually testable with known inputs/outputs

**1.3 Unit Tests for Scoring (45 mins)**
- **File**: `tests/backend/test_confidence_scoring.py`
- **Coverage**: 
  - Test each scoring function independently
  - Edge cases (ties, low scores, perfect scores)
  - Validate deterministic behavior
  - Test level computation logic

### Phase 2: Agent Implementation (1.5-2 hours)
**2.1 Create ConfidenceTestAgent (75 mins)**
- **File**: `src/agents/confidence_agent.py`
- **Base**: Port from `reference_files/src/agents/creativity_agent.py`
- **Adaptations**:
  - 12 confidence-focused questions
  - Dating confidence context in prompts
  - Wire to pure scoring functions
  - Progress tracking for 12-step flow
  - Claude integration for natural conversation

**2.2 Agent Integration Testing (45 mins)**
- **File**: `tests/backend/test_confidence_agent.py`
- **Tests**:
  - Question flow progression
  - Answer parsing and validation
  - Score calculation integration
  - Results generation
  - Error handling and recovery

### Phase 3: API Layer (1-1.5 hours)
**3.1 Pydantic Models (30 mins)**
- **File**: `src/models/confidence_models.py`
- **Models**:
  - `ConfidenceAssessmentRequest` - Submit assessment data
  - `ConfidenceAssessmentResponse` - Return results
  - `ConfidenceResultsResponse` - Retrieve stored results
- **Validation**: Following Pydantic v2 patterns from existing codebase

**3.2 FastAPI Endpoints (45 mins)**
- **File**: Update `src/main.py`
- **Endpoints**:
  - `POST /api/assessment/confidence` - Submit confidence assessment
  - `GET /api/assessment/results/{user_id}` - Retrieve results
- **Integration**: Follow patterns from existing endpoints
- **Error Handling**: Comprehensive validation and error responses

### Phase 4: Persistence Layer (45 mins)
**4.1 Database Schema (15 mins)**
- **Table**: `confidence_test_results`
- **Fields**:
  - `id` (UUID primary key)
  - `user_id` (UUID foreign key)
  - `answers` (JSON array)
  - `archetype` (varchar)
  - `level` (varchar)
  - `scores` (JSON object)
  - `created_at` (timestamp)
  - `updated_at` (timestamp)

**4.2 Database Operations (30 mins)**
- **Functions**: 
  - Store assessment results (handle resubmissions)
  - Retrieve user results
  - Update existing results
- **Safety**: Auto-dependency creation patterns from existing codebase

### Phase 5: Integration Testing (1 hour)
**5.1 Endpoint Integration Tests (45 mins)**
- **File**: `tests/backend/test_confidence_endpoints.py`
- **Tests**:
  - End-to-end assessment submission
  - Results retrieval
  - Error scenarios (invalid data, missing user)
  - Resubmission handling

**5.2 System Integration Validation (15 mins)**
- Test complete flow: questions → answers → scoring → storage → retrieval
- Validate against reference creativity assessment patterns
- Performance testing for realistic response times

## Key Design Decisions

### 1. Archetype Mapping Strategy
**Decision**: Use weighted scoring where each question answer maps to 1-2 archetypes
**Rationale**: Allows for nuanced profiles, not rigid categorization
**Implementation**: Each answer gives +1 to primary archetype, +0.5 to secondary (if applicable)

### 2. Experience Level Computation  
**Decision**: Base level on total score distribution across all archetypes
**Levels**:
- **Beginner**: Low total engagement (< 60% max possible)
- **Intermediate**: Moderate engagement (60-85% max possible) 
- **Advanced**: High engagement (> 85% max possible)

### 3. Error Handling Strategy
**Decision**: Graceful degradation with comprehensive logging
**Approach**: 
- Invalid answers default to first option
- Missing data triggers re-assessment flow
- Database errors return cached results if available

### 4. Security Considerations
**Decision**: User-scoped access with authentication validation
**Implementation**:
- All endpoints require valid user_id
- Results only accessible by original user
- No sensitive personal data in assessment questions

## Success Metrics

### Technical Success
- [ ] All unit tests pass (100% coverage for pure functions)
- [ ] Integration tests pass (end-to-end scenarios)
- [ ] API response times < 500ms 
- [ ] Database operations atomic and consistent

### User Experience Success  
- [ ] Assessment completion rate > 90%
- [ ] Results feel accurate and actionable
- [ ] Resubmission flow works smoothly
- [ ] Error states handled gracefully

### Maintainability Success
- [ ] Code follows existing patterns and conventions
- [ ] Documentation covers all public interfaces
- [ ] Easy to add new questions or archetypes
- [ ] Clear separation of concerns (scoring, storage, presentation)

## Risk Mitigation

### High Risk: Claude Agent Integration Complexity
**Mitigation**: Start with reference creativity agent, make minimal changes
**Fallback**: Simple form-based assessment if conversation flow fails

### Medium Risk: Scoring Algorithm Accuracy
**Mitigation**: Extensive testing with edge cases, validate against expected outcomes
**Fallback**: Manual review and adjustment of weightings

### Low Risk: Database Performance
**Mitigation**: Follow existing patterns, use indexes on user_id
**Fallback**: Caching layer for frequently accessed results

## Timeline Estimate: 6-7 hours total
- Phase 1 (Foundation): 2-3 hours
- Phase 2 (Agent): 1.5-2 hours  
- Phase 3 (API): 1-1.5 hours
- Phase 4 (Persistence): 45 mins
- Phase 5 (Testing): 1 hour

## Dependencies
- Existing Claude agent infrastructure (`src/claude_agent.py`)
- Database connection patterns (`src/database.py`)
- FastAPI setup (`src/main.py`)
- Testing infrastructure (`tests/` structure)

## Next Steps
1. Obtain approval for this implementation plan
2. Begin Phase 1 with question design and pure function implementation
3. Proceed systematically through each phase
4. Update Memory Bank files upon completion

---

*This plan follows TDD principles with pure functions first, builds on existing patterns, and ensures systematic implementation of the complete confidence assessment system.*