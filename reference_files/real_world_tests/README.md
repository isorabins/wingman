# Real World Tests - SimpleChatHandler System

This directory contains live API tests for the **SimpleChatHandler architecture**. These tests verify that the production system works correctly by testing real endpoints against dev/production servers.

## 🎯 Test Purpose

After migrating from the complex multi-agent system to SimpleChatHandler, these tests ensure:
- **All SimpleChatHandler flows work correctly** (creativity test, project overview, general chat)
- **API endpoints respond properly** with expected data structures
- **Database integration functions** without errors
- **User journeys complete successfully** from start to finish
- **Performance is acceptable** for production use

## 🧪 Available Tests

### Core Test Suite

| Test File | Purpose | Duration |
|-----------|---------|----------|
| `test_live_endpoints.py` | **Comprehensive API testing** - All endpoints, flows, error handling | ~2-3 min |
| `test_creativity_flow.py` | **Complete creativity assessment** - All 12 questions, archetype assignment | ~3-4 min |
| `test_onboarding_conversation.py` | **Project onboarding flow** - Full 8-topic conversation simulation | ~5-8 min |

### Utility Files

| File | Purpose |
|------|---------|
| `run_all_tests.py` | **Test orchestrator** - Runs complete test suite with proper reporting |
| `cleanup_test_user.py` | **Data cleanup** - Removes test data from production database |

## 🚀 Quick Start

### Test Against Dev Server
```bash
# Quick smoke test (30 seconds)
python run_all_tests.py --env=dev --quick

# Full test suite (5-8 minutes)  
python run_all_tests.py --env=dev
```

### Test Against Production (Use Carefully!)
```bash
# Production smoke test
python run_all_tests.py --env=prod --quick

# Full production validation
python run_all_tests.py --env=prod
```

### Individual Test Execution
```bash
# Test specific functionality
python test_live_endpoints.py --env=dev
python test_creativity_flow.py --env=dev
python test_onboarding_conversation.py --env=dev
```

## 🔧 Environment Configuration

The tests automatically configure API URLs based on environment:

```python
ENVIRONMENTS = {
    "dev": "https://dev-fridays-at-four.herokuapp.com",      # Dev server
    "prod": "https://fridays-at-four-c9c6b7a513be.herokuapp.com",  # Production  
    "local": "http://localhost:8000"                         # Local development
}
```

**Update the dev URL** in test files when you have the actual dev server endpoint.

## 📊 What Gets Tested

### SimpleChatHandler Flows
- ✅ **Creativity Assessment**: 12-question test, archetype assignment, skip functionality
- ✅ **Project Onboarding**: 8-topic conversation, completion detection, database persistence  
- ✅ **General Conversation**: Creative Q&A, helpful responses, memory continuity

### API Endpoints
- ✅ **Health Check** (`/health`) - Service status
- ✅ **Query** (`/query`) - Main chat endpoint  
- ✅ **Streaming** (`/query_stream`) - Real-time responses
- ✅ **Chat History** (`/chat-history/{user_id}`) - Message retrieval
- ✅ **Project Overview** (`/project-overview/{user_id}`) - Project data
- ✅ **Progress Tracking** (`/agents/creativity-progress/{user_id}`) - Flow status

### Quality Metrics
- ✅ **Response Times**: < 10 seconds per request
- ✅ **Response Quality**: Appropriate content length and relevance
- ✅ **Error Handling**: Graceful failures with proper HTTP codes
- ✅ **Data Persistence**: Messages saved correctly in database

## 🎭 Test Data & Cleanup

### Test User Management
- Each test run creates **unique test user IDs** (UUID format)
- Test users go through **real conversation flows** 
- **Automatic cleanup** removes test data after completion

### Manual Cleanup (If Needed)
```bash
# Clean up test data from database
python cleanup_test_user.py
```

**⚠️ Important**: Always run cleanup after testing production to avoid polluting real user data.

## 📈 Test Results & Reporting

### Success Criteria
- **80%+ pass rate** for production readiness
- **All core flows working** (creativity, project, general chat)
- **Response times < 10s** for acceptable performance
- **No database errors** during test execution

### Example Output
```
🎯 SIMPLECHATHANDLER TEST SUMMARY
============================================================
🌍 Environment: DEV
✅ Passed: 7
❌ Failed: 0  
📊 Pass Rate: 100.0%

✅ Passed Tests:
   - Health Check: Service healthy (0.45s)
   - Creativity Flow Trigger: Creativity assessment triggered (2.31s)
   - Project Overview Trigger: Project onboarding triggered (1.87s)
   - General Creative Question: Helpful response provided (1.92s)
   - Streaming Response: Received 8 chunks, 245 total chars (3.12s)

⚡ Performance: Average response time: 1.93s

🎉 ALL TESTS PASSED!
✅ SimpleChatHandler system is production ready!
```

## ⚠️ Important Notes

### Production Testing Guidelines
- **Use sparingly** - Tests create real database entries
- **Run cleanup** - Always clean up test data after completion
- **Monitor performance** - Tests make real API calls that count toward usage
- **Check results** - Validate that all systems are working before deployment

### Development Workflow
1. **Deploy to dev server** - Push your changes to dev environment
2. **Run smoke tests** - Quick validation that nothing is broken
3. **Run full suite** - Comprehensive testing if major changes
4. **Fix any failures** - Address issues before production deployment
5. **Production validation** - Final check against live system

### Troubleshooting
- **Environment errors**: Check that dev/prod URLs are correct
- **Timeout issues**: Increase timeout values in test files  
- **Database errors**: Check Supabase connection and permissions
- **API errors**: Verify SimpleChatHandler is deployed and running

## 🏗️ Architecture Context

These tests validate the **SimpleChatHandler architecture** that replaced the complex multi-agent system:

### What Changed
- ❌ **Old**: Complex agent routing, LangGraph, multiple agent files
- ✅ **New**: Single SimpleChatHandler, direct database queries, functional approach

### What's Tested
- ✅ **SimpleChatHandler flows**: All creativity/project/general conversation logic
- ✅ **Database integration**: Memory storage, progress tracking, auto-dependencies
- ✅ **API consistency**: Same endpoints, same user experience
- ✅ **Performance**: Response times within acceptable ranges

### Migration Validation
These tests confirm that the SimpleChatHandler migration preserved **100% of user-facing functionality** while improving **maintainability and performance**.

---

## 🎉 Quick Test Commands

```bash
# Most common usage - test dev environment  
python run_all_tests.py --env=dev

# Quick validation after deployment
python run_all_tests.py --env=dev --quick

# Test specific functionality
python test_creativity_flow.py --env=dev

# Production validation (use carefully)
python run_all_tests.py --env=prod --quick
```

These tests replace the need for manual UI testing - run them instead of clicking through the interface manually! 🚀 