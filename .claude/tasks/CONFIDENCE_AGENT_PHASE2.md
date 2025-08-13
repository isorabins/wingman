# Phase 2: ConfidenceTestAgent Implementation Plan

## Overview
Create the ConfidenceTestAgent for WingmanMatch by porting the creativity agent structure and adapting it for dating confidence assessment with 6 archetypes.

## Architecture Analysis
Based on examination of existing patterns:
- **Reference Pattern**: `/Applications/wingman/reference_files/src/agents/creativity_agent.py`
- **Base Class**: `/Applications/wingman/reference_files/src/agents/base_agent.py`
- **Database Schema**: `confidence_test_results` table with specific fields
- **Integration Pattern**: Wire to pure scoring functions (confidence_scoring.py)

## Key Requirements
1. **Create ConfidenceTestAgent** following exact patterns from creativity agent
2. **12-question progression** with state management
3. **Dating confidence context** and 6 archetypes integration
4. **Results storage** in confidence_test_results table
5. **Error handling** and graceful degradation
6. **FastAPI endpoint integration** ready

## 6 Dating Confidence Archetypes
Based on Connell Barrett's framework:
- **Analyzer**: Methodical, research-driven approach to dating
- **Sprinter**: Action-oriented, fast-moving confidence style  
- **Ghost**: Introverted, thoughtful, selective approach
- **Scholar**: Knowledge-focused, learning-based confidence
- **Naturalist**: Authentic, instinctive dating approach
- **Protector**: Caring, relationship-focused confidence style

## Database Schema (confidence_test_results)
```sql
- user_id (uuid) - Foreign key to user_profiles
- test_responses (jsonb) - Raw answers array [0,1,2,3,1,0,...]
- archetype_scores (jsonb) - Computed scores {"Analyzer": 0.8, "Sprinter": 0.3, ...}
- assigned_archetype (text) - Primary archetype name
- experience_level (text) - beginner/intermediate/advanced
```

## Implementation Tasks

### 1. Create Pure Scoring Functions (FIRST - REQUIRED)
**File**: `/Applications/wingman/src/assessment/confidence_scoring.py`
```python
def score_responses(responses: List[int]) -> Dict[str, float]:
    """Convert numeric responses to archetype scores"""
    
def determine_primary_archetype(scores: Dict[str, float]) -> str:
    """Select primary archetype from scores"""
    
def calculate_experience_level(scores: Dict[str, float], total_questions: int) -> str:
    """Determine beginner/intermediate/advanced level"""
```

### 2. Port ConfidenceTestAgent 
**File**: `/Applications/wingman/src/agents/confidence_agent.py`
**Adaptations needed**:
- Import confidence scoring functions
- 12 dating confidence questions (multiple choice)
- Dating context in Claude prompts
- Map to 6 confidence archetypes (not creativity archetypes)
- Store in confidence_test_results table (not creator_creativity_profiles)
- Use same session management and progress tracking patterns

### 3. Key Changes from Creativity Agent

#### Questions Structure
```python
QUESTIONS = [
    {
        "question": "When you see someone attractive, what's your first instinct?",
        "options": {
            "A": "Research their interests before approaching",
            "B": "Go talk to them immediately", 
            "C": "Wait for the right moment",
            "D": "Think about what to say first",
            "E": "Be myself and see what happens",
            "F": "Consider how to make them comfortable"
        },
        "scoring": {
            "A": "Analyzer", "B": "Sprinter", "C": "Ghost",
            "D": "Scholar", "E": "Naturalist", "F": "Protector"
        }
    }
    # ... 11 more questions
]
```

#### Archetype Definitions
```python
ARCHETYPES = {
    "Analyzer": {
        "description": "Methodical, research-driven approach to dating",
        "traits": ["strategic", "prepared", "thoughtful", "systematic"]
    },
    "Sprinter": {
        "description": "Action-oriented, fast-moving confidence style",
        "traits": ["decisive", "bold", "energetic", "spontaneous"]
    },
    # ... other 4 archetypes
}
```

#### Database Integration
```python
async def _save_final_results(self, result: Dict[str, Any]):
    """Save to confidence_test_results table instead of creator_creativity_profiles"""
    profile_data = {
        'user_id': self.user_id,
        'test_responses': result['test_responses'],  # Raw answers
        'archetype_scores': result['archetype_scores'],  # Computed scores
        'assigned_archetype': result['archetype'],  # Primary archetype
        'experience_level': result['experience_level'],  # Calculated level
        'created_at': datetime.now(timezone.utc).isoformat()
    }
```

## Success Criteria
- [ ] Agent follows exact same patterns as creativity_agent.py
- [ ] All 12 questions properly mapped to 6 archetypes
- [ ] Results stored correctly in confidence_test_results table
- [ ] Progress tracking works (can resume mid-assessment)
- [ ] Error handling matches base agent patterns
- [ ] Ready for FastAPI endpoint integration
- [ ] Claude prompts use dating confidence context

## Implementation Steps
1. **FIRST**: Create confidence_scoring.py with pure functions (required for agent)
2. **SECOND**: Port confidence_agent.py from creativity_agent.py structure
3. **THIRD**: Test agent with database operations
4. **FOURTH**: Verify integration points for API endpoints

## Dependencies
- `src/assessment/confidence_scoring.py` (must create first)
- Existing base_agent.py patterns
- confidence_test_results table schema
- Supabase client and memory integration

---

*This plan ensures systematic porting of the proven creativity agent structure while adapting specifically for dating confidence assessment with proper archetype mapping and database integration.*