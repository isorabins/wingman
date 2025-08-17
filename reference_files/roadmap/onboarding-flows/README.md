# Onboarding Flows - Roadmap

This folder contains the complete onboarding flow system that was temporarily removed from the main application. The code is fully functional and can be re-integrated when needed for future product development.

## 🎯 Overview

The onboarding system consists of two sequential flows:
1. **Creativity Assessment** (5 questions) - Determines user's creative archetype
2. **Project Planning** (8 topics) - Comprehensive project setup and goal setting

## 📁 Structure

```
onboarding-flows/
├── creativity-assessment/
│   ├── test_creativity_flow.py     # Complete 5-question assessment test
│   └── simple_creativity_test.py   # Simple creativity test implementation
├── project-planning/
│   ├── project_planning.py         # Core project planning logic
│   └── test_onboarding_conversation.py  # 8-topic onboarding test
├── tests/                          # All onboarding-related tests moved from main test suite
│   ├── test_agent.py              # Agent system tests
│   ├── test_agent_streaming.py    # Streaming agent tests
│   ├── test_caching_headers.py    # Claude caching header tests
│   ├── test_caching_implementation.py  # Full caching implementation tests
│   ├── test_claude_agent_simple.py    # Simple Claude agent tests
│   ├── test_complete_user_journey.py  # End-to-end user journey tests
│   ├── test_cost_savings_demo.py      # Claude caching cost savings demo
│   ├── test_db_driven_system.py       # Database-driven agent system tests
│   ├── test_end_to_end_journey.py     # Complete journey integration tests
│   ├── test_flow_state_manager.py     # Flow state management tests
│   ├── test_production_validation.py  # Production environment validation
│   ├── test_project_planning_ci.py    # CI/CD project planning tests
│   ├── test_project_planning_core.py  # Core project planning logic tests
│   ├── test_project_planning_integration.py  # Project planning integration tests
│   ├── test_prompt_caching.py         # Claude prompt caching optimization tests
│   └── test_slack_integration.py      # Slack bot integration tests
├── context_formatter.py           # Claude prompt caching & context formatting
├── onboarding_manager.py           # Database operations for onboarding
└── README.md                       # This file
```

## 🔧 Key Components

### **context_formatter.py** - AI Context Management
- **Purpose**: Formats user data for Claude prompt caching optimization
- **Features**:
  - Structured context formatting (User Profile, Creativity Profile, Project Data)
  - Claude prompt caching headers and optimization
  - Consistent output format for cache efficiency
  - Creative archetype guidance for AI personalization
- **Usage**: Called by claude_agent.py to format user context before AI calls
- **Cache Strategy**: Ensures identical input produces identical output for Claude caching

### **project_planning.py** - 8-Topic Onboarding Flow
- **Purpose**: Comprehensive project planning conversation flow
- **Features**:
  - 8 structured topics for complete project setup
  - Progress tracking ("Topic X of 8")
  - Completion detection and project overview creation
  - AI-powered conversation management
- **Database Integration**: Creates project_overview records upon completion

### **onboarding_manager.py** - Database Operations
- **Purpose**: Handles all database operations for onboarding flows
- **Features**:
  - Creator profile management
  - Creativity assessment storage
  - Project overview creation
  - Auto-dependency creation for foreign keys

## 🎨 Creativity Assessment System

The creativity assessment determines user archetypes through 5 carefully designed questions:

**Creative Archetypes:**
- **Big Picture Visionary** - Focus on vision, impact, and meaning
- **Knowledge Seeker** - Values research, learning, and thorough understanding  
- **Authentic Creator** - Values personal expression and authenticity
- **Practical Builder** - Values structure, clear steps, and practical outcomes
- **People Connector** - Values collaboration, feedback, and community
- **Innovative Explorer** - Values novelty, experimentation, and discovery

## 🧪 Comprehensive Test Suite

All tests related to onboarding flows have been moved to the `tests/` directory to prevent import conflicts with the simplified main application. These tests cover:

### **Core Functionality Tests:**
- `test_project_planning_core.py` - Project planning logic validation
- `test_db_driven_system.py` - Database-driven agent system
- `test_flow_state_manager.py` - Flow state management

### **Integration Tests:**
- `test_complete_user_journey.py` - Full user onboarding experience
- `test_end_to_end_journey.py` - Complete system integration
- `test_project_planning_integration.py` - Project planning with database

### **Performance & Optimization Tests:**
- `test_caching_implementation.py` - Claude prompt caching system
- `test_prompt_caching.py` - Prompt optimization strategies
- `test_cost_savings_demo.py` - API cost reduction validation
- `test_caching_headers.py` - Cache header implementation

### **Agent System Tests:**
- `test_agent.py` - Core agent functionality
- `test_agent_streaming.py` - Streaming response handling
- `test_claude_agent_simple.py` - Simplified Claude integration

### **Production & CI Tests:**
- `test_production_validation.py` - Production environment checks
- `test_project_planning_ci.py` - CI/CD pipeline validation

### **External Integration Tests:**
- `test_slack_integration.py` - Slack bot functionality

**All tests were passing when moved to roadmap and are ready for re-integration.**

## 🚀 Re-Integration Guide

When ready to re-add onboarding flows:

1. **Move files back to src/**:
   ```bash
   mv roadmap/onboarding-flows/context_formatter.py src/
   mv roadmap/onboarding-flows/project_planning.py src/
   mv roadmap/onboarding-flows/onboarding_manager.py src/
   ```

2. **Move tests back to main test suite**:
   ```bash
   mv roadmap/onboarding-flows/tests/* new_tests/test-suite/integrations/
   ```

3. **Update claude_agent.py** to import and use onboarding logic:
   ```python
   from src.project_planning import should_trigger_creativity_test, get_project_planning_prompt
   from src.context_formatter import format_static_context_for_caching, get_cache_control_header
   ```

4. **Re-enable onboarding triggers** in main.py project-overview endpoint

5. **Update context formatting** to use cache control headers for Claude optimization

## 💡 Design Philosophy

The onboarding system was designed with these principles:
- **User-Centric**: Focus on understanding user needs before project planning
- **Progressive**: Build complexity gradually through structured conversations
- **Intelligent**: AI adapts responses based on user's creative archetype
- **Persistent**: All progress saved to enable conversation continuity
- **Optimized**: Claude prompt caching reduces API costs and improves performance

## 🔄 Current Status

- **Code Status**: ✅ Fully functional and tested
- **Database Schema**: ✅ All tables exist and working
- **AI Integration**: ✅ Complete with Claude 3.5 Sonnet
- **Test Coverage**: ✅ Comprehensive real-world testing (18 test files)
- **Documentation**: ✅ Complete implementation guide
- **Separation**: ✅ Cleanly separated from simplified main application

**Ready for re-integration when product strategy calls for enhanced onboarding experience.**

---

*This roadmap preserves all the sophisticated onboarding functionality while keeping the main application simple and focused.* 