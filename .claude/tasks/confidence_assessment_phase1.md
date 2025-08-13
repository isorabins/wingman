# Phase 1: Dating Confidence Assessment System Implementation Plan

## Project Overview
Implement foundation components for a 12-question dating confidence assessment system for WingmanMatch, following the established pattern from the creativity agent while adapting content for dating scenarios.

## Technical Requirements Analysis

### Database Integration ✅ READY
- `confidence_test_results` table already exists with correct schema:
  - `test_responses` (jsonb) - Raw answers array
  - `archetype_scores` (jsonb) - Computed scores per archetype  
  - `assigned_archetype` (text) - Primary archetype
  - `experience_level` (text) - beginner/intermediate/advanced

### Architecture Pattern ✅ CONFIRMED
- Reference: `/reference_files/src/agents/creativity_agent.py`
- Pattern: Pure scoring functions, deterministic results, comprehensive typing
- Database: Supabase PostgreSQL with auto-dependency creation patterns

## Implementation Tasks

### Task 1: Create Assessment Directory Structure
**Files to create:**
- `/Applications/wingman/src/assessment/__init__.py`
- Directory: `/Applications/wingman/src/assessment/`

**Deliverable**: Clean module structure for assessment components

### Task 2: Design 12-Question Dating Confidence Assessment  
**File**: `/Applications/wingman/src/assessment/confidence_questions.py`

**Content Requirements:**
- 12 multiple-choice questions (4 options each)
- Focus areas:
  - Approaching strangers in social settings
  - Handling rejection gracefully
  - Social anxiety in dating contexts
  - Conversation skills and flow
  - Venue comfort (bars, coffee shops, events)
  - Body language confidence
  - Initiating romantic interest
  - Managing dating app interactions
  - Group social dynamics
  - Emotional regulation during dating
  - Recovery from dating setbacks
  - Long-term relationship confidence

**Question Structure** (following creativity agent pattern):
```python
QUESTIONS = [
    {
        "question": "When you see someone attractive at a coffee shop, your first instinct is:",
        "options": {
            "A": "Analyze the situation and plan the perfect approach",
            "B": "Wait for the right moment, then make a quick confident move", 
            "C": "Feel anxious and probably avoid eye contact",
            "D": "Overthink all possible conversation starters",
            "E": "Casually be yourself and see if natural interaction happens",
            "F": "Worry about rejection and protect yourself by not trying"
        },
        "scoring": {
            "A": "Analyzer", "B": "Sprinter", "C": "Ghost",
            "D": "Scholar", "E": "Naturalist", "F": "Protector"
        }
    }
]
```

### Task 3: Define 6 Dating Confidence Archetypes
**Adaptation from creativity archetypes to dating context:**

1. **Analyzer** (Strategic Planner)
   - Description: "Takes a methodical, strategic approach to dating"
   - Traits: ["analytical", "strategic", "systematic", "research-oriented"]
   - Dating approach: Plans dates carefully, studies dating advice, strategic about timing

2. **Sprinter** (Momentum-Based)
   - Description: "Performs best with quick bursts of confidence and social momentum"
   - Traits: ["momentum-driven", "spontaneous", "high-energy", "social-dependent"]
   - Dating approach: Great at parties/events, needs social energy, struggles with solo approaches

3. **Ghost** (Socially Anxious)
   - Description: "Struggles with social anxiety and tends to avoid potential rejection"
   - Traits: ["anxious", "avoidant", "self-protective", "overthinking"]
   - Dating approach: Online dating preferred, avoids cold approaches, fear-based responses

4. **Scholar** (Intellectual)
   - Description: "Approaches dating through learning and intellectual connection"
   - Traits: ["intellectual", "research-focused", "conversation-driven", "analytical"]
   - Dating approach: Values deep conversations, overthinks interactions, knowledge-seeking

5. **Naturalist** (Authentic Self)
   - Description: "Most comfortable being authentic and letting connections develop naturally"
   - Traits: ["authentic", "natural", "patient", "relationship-focused"]
   - Dating approach: Values genuine connections, patient with timing, comfortable being themselves

6. **Protector** (Defensive Guard)
   - Description: "Uses defensive strategies to protect against emotional vulnerability"
   - Traits: ["defensive", "guarded", "risk-averse", "self-protective"]
   - Dating approach: Avoids vulnerability, tests potential partners, fear of emotional exposure

### Task 4: Implement Pure Scoring Functions
**File**: `/Applications/wingman/src/assessment/confidence_scoring.py`

**Required Functions:**
```python
def score_answers(answers: List[int]) -> Dict[str, float]:
    """Convert raw answers (0-3 indices) to archetype scores"""

def choose_archetype(scores: Dict[str, float]) -> str:
    """Select primary archetype with sophisticated tie-breaking"""

def compute_level(scores: Dict[str, float], archetype: str) -> str:
    """Determine beginner/intermediate/advanced based on confidence patterns"""
```

**Scoring Configuration Requirements:**
- Map each answer choice (A-F) to archetype weights
- Handle tie-breaking logic (secondary scores, question-specific weights)
- Experience level calculation based on overall confidence indicators
- Pure functions - no database calls, deterministic results

### Task 5: Configuration and Documentation
**Requirements:**
- Comprehensive docstrings with type hints
- Clear separation of concerns (questions vs scoring vs config)
- Following existing project patterns for imports and structure
- Error handling for edge cases (incomplete answers, invalid responses)

## Quality Standards

### Testing Strategy (Future Phase)
- Pure functions enable easy unit testing
- Deterministic scoring for regression testing
- Edge case coverage (ties, incomplete responses)

### Integration Points
- Results stored in existing `confidence_test_results` table
- Compatible with existing FastAPI patterns
- Memory system integration (WingmanMemory class)

### Performance Considerations
- Pure functions for fast computation
- No external API calls in scoring logic
- Minimal memory footprint for question storage

## Success Criteria

### Functional Requirements ✅
- [ ] 12 comprehensive dating confidence questions
- [ ] 6 well-defined dating archetypes with clear traits
- [ ] Pure scoring functions with proper typing
- [ ] Clean module structure following project patterns

### Technical Requirements ✅
- [ ] Type hints throughout (Python 3.10+ style)
- [ ] Comprehensive docstrings
- [ ] No external dependencies in scoring functions
- [ ] Compatible with existing database schema

### Code Quality ✅  
- [ ] Follows existing project patterns
- [ ] Clear separation of concerns
- [ ] Error handling for edge cases
- [ ] Ready for TDD implementation

## Implementation Notes

### Reference Patterns to Follow
- Question structure from `creativity_agent.py` lines 52-233
- Archetype definitions from lines 24-49
- Scoring logic from `_calculate_results()` method
- Database integration patterns from existing WingmanMatch codebase

### Adaptations for Dating Context
- Questions focus on real dating scenarios vs creative processes
- Archetypes reflect dating confidence patterns vs creative styles
- Experience levels tied to social confidence vs creative experience

### Future Integration Points
- Agent system for guided assessment flow
- Memory system for storing results and progress
- Frontend API endpoints for question delivery
- Personalized coaching based on archetype results

---

**Ready for Implementation**: All foundation research completed, database schema confirmed, patterns identified. Proceeding with Phase 1 implementation.