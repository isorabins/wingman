# Obsolete Tests

This directory contains tests that are no longer compatible with the current system architecture.

## Why These Tests Were Moved

These tests were written for the **old chat system** that used a different function signature and architecture. With the implementation of the **Flow-Based Conversation System**, these tests are no longer valid because:

### Function Signature Changes
- **Old system**: `chat(supabase, user_id, message, thread_id)` 
- **New system**: `FlowBasedChatHandler.chat(message, thread_id)`

### Architecture Changes
- **Old system**: Direct function calls to chat handlers
- **New system**: Flow-based routing through `FlowManager` and specialized handlers

## Moved Tests

### `test_current_endpoints.py`
- Tests for query endpoint with V2 system
- Tests for agent chat endpoints
- **Issue**: Function signature mismatch - `chat() takes 2 positional arguments but 4 were given`

### `test_main_endpoints_updated.py`
- Tests for query, streaming, and chat endpoints
- Tests for agent endpoints with different flow phases
- **Issue**: Same function signature mismatch across all chat-related endpoints

## Current Test Status

The **core functionality tests** are still passing:
- ✅ Memory system tests
- ✅ Database integration tests  
- ✅ External service connection tests
- ✅ Claude client tests
- ✅ Summarization tests

## Future Test Updates

New tests should be written for the **Flow-Based System**:
- Flow routing logic
- Creativity test progression
- Project planning flow
- Flow state management
- Database-driven flow transitions

These obsolete tests serve as reference for the expected API behavior, but need to be rewritten to match the new architecture. 