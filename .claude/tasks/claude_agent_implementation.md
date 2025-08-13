# Claude Agent Implementation Plan for WingmanMatch

## Overview
Implement Claude agent integration for WingmanMatch with Connell Barrett persona using reference patterns from Fridays at Four, adapted for dating confidence coaching context.

## Implementation Requirements

### 1. Core Files to Create/Update

#### A. `/Applications/wingman/src/claude_agent.py` - Main Agent
- Direct Anthropic SDK usage (no LangChain abstractions)
- Streaming and non-streaming response functions  
- Model routing: Claude 3.5 Sonnet primary, GPT-4o-mini fallback
- Temperature 0.7, top_p 0.9 for optimal coaching responses
- Integration with existing simple_memory.py and database.py
- Memory hooks for assessment_results, attempts, triggers, session_history

#### B. `/Applications/wingman/src/simple_memory.py` - Memory System
- User-keyed conversation persistence using existing Supabase pattern
- Memory hooks for dating confidence coaching context:
  - assessment_results: confidence test scores and archetype
  - attempts: approach attempts and outcomes  
  - triggers: fear patterns and anxiety points
  - session_history: coaching session results and breakthroughs
- Context retrieval and formatting for Claude API
- Thread-based conversation management across sessions

#### C. `/Applications/wingman/src/tools.py` - Function Calling Tools
- get_approach_challenges: Fetch challenges by difficulty level
- record_attempt_outcome: Log approach attempts and results
- get_session_history: Retrieve past wingman coaching sessions
- update_confidence_notes: Save coaching insights and breakthroughs

### 2. Model Configuration

#### Model Selection Strategy
- **Primary Model**: Claude 3.5 Sonnet for high-quality coaching responses
- **Fallback Model**: GPT-4o-mini for cost-effective operation during high volume
- **Development Model**: Claude 3 Haiku for local testing and development

#### Model Parameters
- **Temperature**: 0.7 (more creative than reference 0.6 for coaching warmth)
- **Top_p**: 0.9 (balanced nucleus sampling for natural conversation)
- **Max Tokens**: 1024-2048 optimized for streaming responses
- **Stream**: True for real-time coaching experience

### 3. Integration Requirements

#### Database Integration
- Use existing `src/database.py` SupabaseFactory patterns
- Leverage existing `src/retry_utils.py` for resilience
- Support WingmanMatch schema (user_profiles, approach_challenges, etc.)

#### Memory Persistence
- Extend existing memory patterns for dating coaching context
- Maintain conversation context across multiple coaching sessions
- Support memory hooks for dating confidence tracking

#### API Integration
- Integrate with existing `src/main.py` FastAPI structure
- Support both streaming and non-streaming endpoints
- Maintain existing CORS and middleware patterns

### 4. Connell Barrett Persona Adaptation

#### Core Personality Traits
- Authentic confidence coaching (not pickup tactics)
- Warm, encouraging, and genuinely supportive
- Focus on inner confidence development vs external validation
- Emphasis on authentic masculinity and genuine connection

#### Coaching Boundaries
- NEVER provide pickup lines or scripts
- REFUSE manipulation or deceptive tactics  
- ALWAYS emphasize respect, consent, and authenticity
- REDIRECT toxic masculinity toward healthy confidence building

#### Memory Context Hooks
- **assessment_results**: Dating confidence archetype and test scores
- **attempts**: Approach attempts with outcomes and lessons learned
- **triggers**: Personal fears, anxiety patterns, social obstacles
- **session_history**: Coaching breakthroughs and progress tracking

### 5. Implementation Steps

1. **Create core claude_agent.py** with direct Anthropic SDK integration
2. **Update simple_memory.py** with WingmanMatch-specific memory hooks
3. **Create tools.py** with dating confidence function calling tools
4. **Update prompts.py** (already contains Connell Barrett persona)
5. **Test integration** with existing database and API infrastructure
6. **Validate streaming responses** work with coaching conversation flow

### 6. Technical Specifications

#### Error Handling
- Graceful fallback when Claude API unavailable
- Retry logic using existing retry_utils.py patterns
- Comprehensive logging for debugging and monitoring

#### Performance Optimization
- Streaming responses for real-time coaching experience
- Model routing for cost optimization during high volume
- Memory caching for frequently accessed coaching context

#### Safety Measures
- Content filtering for inappropriate requests
- Privacy protection for personal dating information
- Rate limiting integration with existing middleware

## Expected Outcomes

### Functional Requirements Met
- ✅ Claude 3.5 Sonnet integration with streaming support
- ✅ Connell Barrett coaching persona implementation
- ✅ Memory hooks for dating confidence tracking
- ✅ Function calling tools for coaching activities
- ✅ Integration with existing WingmanMatch infrastructure

### Quality Standards
- Response quality optimized for authentic dating confidence coaching
- Memory continuity maintains coaching relationship context
- Error handling ensures reliable coaching availability
- Performance suitable for real-time coaching conversations

### Safety & Ethics
- No pickup tactics or manipulative content
- Emphasis on authentic confidence and genuine connection
- Respect for consent and healthy dating boundaries
- Support for positive masculinity development

---

*Implementation will leverage proven patterns from Fridays at Four reference while adapting specifically for WingmanMatch's dating confidence coaching context and Connell Barrett's authentic coaching approach.*