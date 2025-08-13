# 🚀 Product Requirements Document: Intro Flows Implementation

## 📋 Executive Summary

**Project**: Complete the implementation of Fridays at Four's three-stage onboarding system using Claude prompt caching for optimal performance and cost efficiency.

**Goal**: Enable new users to progress through: Intro Flow → Creativity Test → Project Planning → Main Chat with intelligent conversation, state persistence, and 65-75% cost savings via prompt caching.

**Timeline**: 2-3 weeks for experienced developer
**Priority**: High - Critical for user onboarding experience

---

## 🎯 Product Context

### Current State
- **Backend**: Production-ready FastAPI with Claude integration
- **Database**: Supabase PostgreSQL with all required tables
- **AI System**: Direct Claude API integration (no LangChain/LangGraph)
- **Memory System**: Custom conversation storage with auto-dependency creation
- **Onboarding**: Currently skips intro flow, goes directly to main chat

### Target State
- **Three-Stage Onboarding**: Intro Flow → Creativity Test → Project Planning → Main Chat
- **Intelligent Conversations**: AI-driven natural conversation flow
- **Cost Optimization**: 65-75% API cost reduction via prompt caching
- **State Persistence**: Full conversation context maintained across sessions

---

## 📁 Files Provided

You will receive **5 complete implementation files** from the `feat/creativity-test-welcome-flow-v2` branch:

### **1. Core Implementation Files**

#### **`src/intro_flow_handler.py`** (Complete Implementation)
- **Purpose**: Natural conversation intro flow before structured assessments
- **Features**: 
  - AI-driven conversation about platform value
  - Name extraction and personalization
  - Explains 3 key concepts: persistent memory, adaptive partnership, creative support
  - Smart transition detection to creativity test
- **Status**: Production-ready, needs integration only

#### **`src/flow_manager.py`** (State Management)
- **Purpose**: Coordinates all three onboarding flows
- **Features**:
  - Flow state tracking and transitions
  - Session management with cooldowns
  - Error handling and recovery
  - Database integration for flow progress
- **Status**: Complete, needs endpoint integration

#### **`src/project_planning.py`** (Already Integrated)
- **Purpose**: 8-topic comprehensive project planning conversation
- **Features**: Structured conversation flow, project overview creation
- **Status**: ✅ Already working in production

### **2. Documentation Files**

#### **`docs/intro-flow-implementation.md`** (Complete Guide)
- **Purpose**: Comprehensive implementation architecture and strategy
- **Contents**:
  - Detailed conversation flow design
  - Database schema requirements
  - AI prompt engineering strategies
  - Integration patterns and best practices
- **Value**: Complete technical specification

#### **`docs/intro-flow-README.md`** (Integration Guide)
- **Purpose**: Step-by-step integration instructions
- **Contents**:
  - Database schema updates needed
  - Endpoint integration steps
  - Frontend routing requirements
  - Future enhancement roadmap
- **Value**: Implementation checklist

### **3. Test Suite**

#### **`tests/test_intro_flow.py`** (235 Lines of Tests)
- **Purpose**: Comprehensive test coverage for intro flow
- **Coverage**:
  - Name extraction from various input patterns
  - Conversation stage transitions
  - Off-topic question handling
  - Error recovery and fallback responses
  - Context building through conversation stages
- **Value**: Saves days of test development

---

## 🎯 Technical Implementation Strategy

### **Prompt Caching Architecture** (Critical for Cost Efficiency)

#### **Strategy: Full Context Caching**
- **Approach**: Include ENTIRE creativity test and project planning content in cached prompts
- **Benefit**: Claude sees full context and current progress every time
- **Cost Savings**: 65-75% reduction in API costs after initial cache
- **Performance**: Faster responses after cache warmup

#### **Implementation Pattern**:
```python
# Cache the full creativity test with current progress
cached_prompt = f"""
{FULL_CREATIVITY_TEST_CONTENT}

Current Progress: Question {current_question} of 11
User Responses So Far: {user_responses}
Current Context: {conversation_context}
"""

# Use cached prompt for each interaction
response = claude_client.messages.create(
    model="claude-3-5-sonnet-20241022",
    system=cached_prompt,  # This gets cached
    messages=[user_message]
)
```

### **Database Integration**

#### **Required Tables** (Most Already Exist):
- ✅ `creator_profiles` - User basic info
- ✅ `creator_creativity_profiles` - Creativity test results  
- ✅ `project_overview` - Project planning results
- ✅ `conversation_memory` - Chat history storage
- 🆕 `user_flow_progress` - Track onboarding flow state (NEW)

#### **New Table Schema**:
```sql
CREATE TABLE user_flow_progress (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id),
    current_flow VARCHAR(50), -- 'intro', 'creativity', 'project_planning', 'completed'
    flow_data JSONB, -- Store conversation context and progress
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### **API Endpoints to Implement**

#### **New Endpoints Needed**:
```python
# Intro Flow Management
POST /api/intro-flow/start        # Initialize intro conversation
POST /api/intro-flow/continue     # Continue intro conversation
GET  /api/intro-flow/status       # Check intro flow progress

# Flow Coordination
GET  /api/onboarding/status       # Overall onboarding progress
POST /api/onboarding/transition   # Move between flows
```

#### **Integration with Existing**:
- ✅ `/api/creativity-test/*` - Already implemented
- ✅ `/api/project-planning/*` - Already implemented  
- ✅ `/api/chat/*` - Main chat system

---

## 🎭 User Experience Flow

### **Complete User Journey**:

1. **User Signs Up** → Redirected to intro flow
2. **Intro Flow** (5-10 minutes):
   - Natural conversation with Hai
   - Learn about platform value
   - Name collection and personalization
   - Explain persistent memory, adaptive partnership, creative support
3. **Creativity Test** (5-7 minutes):
   - 11 questions to determine creative archetype
   - Results stored in `creator_creativity_profiles`
4. **Project Planning** (10-15 minutes):
   - 8-topic comprehensive project setup
   - Results stored in `project_overview`
5. **Main Chat** → Full platform access

### **Conversation Intelligence**:
- **Natural Language**: No rigid scripts, AI-driven responses
- **Context Awareness**: Remember everything across sessions
- **Personalization**: Use name and adapt to user responses
- **Question Handling**: Answer questions naturally within flow context

---

## 🔧 Implementation Requirements

### **Phase 1: Core Integration (Week 1)**
- [ ] Add `user_flow_progress` table to database
- [ ] Integrate `intro_flow_handler.py` into main FastAPI app
- [ ] Create intro flow API endpoints
- [ ] Implement prompt caching for intro conversations
- [ ] Connect intro flow to existing creativity test

### **Phase 2: Flow Coordination (Week 2)**
- [ ] Integrate `flow_manager.py` for state management
- [ ] Implement onboarding status tracking
- [ ] Add transition logic between flows
- [ ] Implement prompt caching for creativity test and project planning
- [ ] Create comprehensive error handling

### **Phase 3: Testing & Polish (Week 3)**
- [ ] Run provided test suite (`test_intro_flow.py`)
- [ ] Integration testing with existing systems
- [ ] Performance testing with prompt caching
- [ ] User experience testing and refinement

---

## 💡 Key Success Metrics

### **Technical Metrics**:
- **Cost Reduction**: 65-75% decrease in Claude API costs via caching
- **Response Time**: <2 seconds for cached prompts, <5 seconds for new prompts
- **Error Rate**: <1% conversation failures with proper fallbacks
- **Completion Rate**: >80% users complete full onboarding flow

### **User Experience Metrics**:
- **Engagement**: Users spend 20-30 minutes in onboarding
- **Satisfaction**: Natural conversation feel vs rigid forms
- **Retention**: Users who complete onboarding have higher long-term engagement
- **Conversion**: Smooth transition from onboarding to active platform use

---

## 🚨 Critical Implementation Notes

### **Prompt Caching Strategy**:
- **Cache Full Context**: Include entire test/planning content in prompts
- **State Awareness**: Claude sees complete progress every interaction
- **Cost Optimization**: Massive savings after initial cache warmup
- **Performance**: Faster responses with cached context

### **Database Safety**:
- **Auto-Dependencies**: Use existing `ensure_creator_profile()` pattern
- **Foreign Key Safety**: Always check relationships before inserts
- **Graceful Errors**: Never expose internal errors to users

### **AI Integration**:
- **Direct Claude API**: No LangChain/LangGraph dependencies
- **Memory Injection**: Context provided as SystemMessages
- **Natural Conversation**: AI-driven responses, not scripted flows

---

## 📞 Support & Resources

### **Existing Production Systems**:
- **Backend**: `fridays-at-four-c9c6b7a513be.herokuapp.com`
- **Database**: Supabase with full schema documentation
- **AI Integration**: Direct Claude API integration patterns
- **Memory System**: Proven conversation storage and retrieval

### **Code Quality Standards**:
- **Type Hints**: Required throughout Python codebase
- **Async/Await**: All I/O operations must be async
- **Error Logging**: Comprehensive logging with context
- **Testing**: Provided test suite must pass

---

**This PRD provides everything needed to implement the three-stage onboarding system with optimal cost efficiency and user experience. The provided files contain all the hard work - implementation is primarily integration and optimization.** 