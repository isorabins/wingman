# Fridays at Four: DB-Driven Agent Refactor Plan

## Background & Motivation

### Previous Approach: Hardcoded, Manager-Agent-Driven Flow
- Every user message triggered a manager agent API call to check which flow (intro, creativity, project overview, etc.) the user should be routed to.
- The manager agent used a hardcoded state machine to determine the next step, then routed the message to the appropriate agent or handler.
- Each flow (intro, creativity, project) was implemented as a series of hardcoded steps, with explicit stage numbers and triggers.

#### Problems
- **Performance:** Every chat message resulted in multiple API calls (user → manager agent → flow agent), even after onboarding was complete.
- **Brittleness:** The hardcoded step logic was fragile—if a user answered out of order, or the AI's response format changed, the flow could break or repeat.
- **Maintainability:** Updating the flow (adding/removing steps, changing logic) required changes in multiple places and was error-prone.
- **User Experience:** Users could get stuck in loops or be re-prompted for information they'd already provided.

---

### New Approach: Agent-Driven, DB-Aware, Stateless Flow
- On every user message, the backend queries the database (see `full_schema_6_13.json`) for the user's current state in each flow (intro, creativity, project overview).
- The backend then routes the message to the appropriate agent (intro agent, creativity agent, project agent, or main chat agent) **based on what's missing**, not a hardcoded step number.
- Each agent is responsible for:
    - Extracting relevant information from the user's message (e.g., name, project type, etc.).
    - Updating the database with new information as it's collected.
    - Prompting for the next missing piece of information, or handing off to the next agent when its flow is complete.
- **No manager agent API call is needed**—all routing and state management is handled in the backend, with a single DB query per message.

#### Why this is better
- **Performance:** Only one API call per user message (no redundant manager agent calls).
- **Robustness:** The system is resilient to users answering out of order, skipping steps, or returning after a break.
- **Maintainability:** Flows can be updated by changing the DB schema or agent logic, without touching a brittle state machine.
- **User Experience:** Users are never re-prompted for information they've already provided, and can always pick up where they left off.

---

## Database Schema Alignment
- The schema in `full_schema_6_13.json` already supports this approach:
    - `creativity_test_progress` and `project_overview_progress` tables track per-user flow state, responses, and completion.
    - Fields like `intro_stage`, `intro_data`, `has_seen_intro`, `skipped_until`, and `is_completed` allow agents to determine exactly what's missing for each user.
    - All agents can read/write to these tables to update progress and context.

---

## Implementation Plan

### 1. Remove Manager Agent API Call
- Refactor the main chat handler to **not** call a manager agent on every message.
- Instead, on each message, query the relevant progress tables for the user's current state.

### 2. Implement Agent-Based, DB-Aware Routing
- In the main chat handler:
  1. Query the DB for the user's intro, creativity, and project overview progress.
  2. If intro is incomplete, route to the intro agent.
  3. If intro is complete but creativity test is not, route to the creativity agent.
  4. If both are complete but project overview is not, route to the project agent.
  5. If all are complete, route to the main chat agent.

### 3. Refactor Agents to Use DB State
- Each agent (intro, creativity, project) should:
  - Accept the user's message and the current state from the DB.
  - Use extraction logic (from your docs) to pull out relevant info.
  - Update the DB as new info is collected.
  - Prompt for the next missing piece, or hand off when done.
- **No hardcoded step numbers**—always check "what info do I have, what's missing?"

### 4. Update Extraction and Prompt Logic
- Use robust extraction functions (as in `intro_flow_implementation.md`) to identify names, project types, readiness, etc.
- Prompts should be dynamic, based on what's missing, not a fixed script.

### 5. Test with Real User Journeys
- Use the new real-world test suite (now in `/new_tests`) to validate:
  - Full onboarding flows
  - Abandon/resume scenarios
  - Out-of-order answers
  - Edge cases (skipping, ambiguous responses)

---

## Code Sketches

### Main Chat Handler (Pseudocode)

```python
def handle_user_message(user_id, message, thread_id):
    # 1. Query DB for intro/creativity/project state
    intro_state = get_intro_state_from_db(user_id)
    creativity_state = get_creativity_state_from_db(user_id)
    project_state = get_project_state_from_db(user_id)

    # 2. Route to the right agent/handler
    if not intro_state['complete']:
        return intro_agent.handle(message, intro_state)
    elif not creativity_state['complete']:
        return creativity_agent.handle(message, creativity_state)
    elif not project_state['complete']:
        return project_agent.handle(message, project_state)
    else:
        return main_chat_agent.handle(message)
```

### Agent Interface Example (Intro Agent)

```python
class IntroAgent:
    def handle(self, message, intro_state):
        # 1. Check which fields are missing (name, project, accountability, etc.)
        missing = self.get_missing_fields(intro_state)
        # 2. Extract info from message
        extracted = self.extract_info(message)
        # 3. Update DB with new info
        self.update_intro_state_in_db(user_id, extracted)
        # 4. If all info collected, mark intro complete and hand off
        if self.is_intro_complete(intro_state):
            return "Intro complete! Moving to creativity test..."
        # 5. Otherwise, prompt for next missing info
        return self.prompt_for_next(missing)
```

---

## Summary Table

| Approach                | API Calls per Chat | Robustness | Maintainability | User Experience |
|-------------------------|-------------------|------------|----------------|-----------------|
| Manager agent (old)     | 2+                | Brittle    | Hard to update | Can get stuck   |
| DB-driven agents (new)  | 1                 | Robust     | Easy to update | Always resumes  |

---

## Next Steps
1. Refactor main chat handler to use DB-driven routing.
2. Refactor intro, creativity, and project agents to use DB state and dynamic prompts.
3. Remove all manager agent API calls.
4. Test thoroughly with the new real-world test suite.
5. Incrementally improve agent logic and prompts based on user feedback and test results.

---

## Rationale for Sharing with the AI Who Designed the Previous Version
- This plan documents the architectural shift from a hardcoded, manager-agent-driven flow to a robust, DB-driven, agent-based system.
- It explains the rationale, benefits, and concrete implementation steps, so the AI (or any collaborator) can understand the evolution and contribute to the new approach.
- The plan is fully aligned with the current database schema and leverages the best patterns from both the old and new systems.

---

# Detailed Analysis & Expanded Roadmap (June 2025)

## What's Excellent About the Current Approach

- **No More Manager Agent API Call:**  The new system eliminates the expensive, redundant manager agent call on every message. Instead, it uses a single, fast DB query to get all relevant user flow state.
- **Centralized Flow State:**  The `UserFlowState` dataclass and `FlowStateManager` provide a single source of truth for intro, creativity, and project progress, making routing and state checks simple and robust.
- **Agent Pattern with Standardized Interface:**  Each flow (Intro, Creativity, Project, Main Chat) is encapsulated in its own agent class, all inheriting from a common `BaseFlowAgent`. This makes the system modular, testable, and easy to extend.
- **DB-Driven Routing:**  The main handler (`DatabaseDrivenChatHandler`) routes messages to the correct agent based on DB state, not hardcoded steps or brittle state machines.
- **Resilience to User Behavior:**  The system is robust to users answering out of order, skipping, or returning after a break. Agents always check "what's missing" and prompt accordingly.
- **Extensible and Maintainable:**  Adding new flows or updating logic is as simple as adding/updating an agent class and updating the DB schema if needed.
- **Performance:**  Only one DB query per message, and all state is managed in the backend—no unnecessary API hops.

## What Could Be Improved or Further Detailed

- **Agent Prompting and Extraction:**  The extraction and prompt logic in each agent could be further modularized, and more advanced NLP (or LLM) extraction could be used for ambiguous or multi-intent messages.
- **Error Handling and Fallbacks:**  The system has basic error handling, but could benefit from more granular logging, user-facing error messages, and retry logic for DB/API failures.
- **Testing and Observability:**  The plan should include how to test each agent in isolation, as well as end-to-end, and how to monitor flow completion and user drop-off in production.
- **Schema Evolution:**  As flows evolve, the plan should include how to migrate or version DB schemas and agent logic.
- **Agent Collaboration:**  In the future, agents could collaborate (e.g., project agent referencing creativity results), and the plan should outline how to share context between agents.

---

## Updated & Expanded Agent Refactor Plan (with AI Feedback)

### 1. Rationale and Direction
- **Why:**  The old manager agent/state machine approach was brittle, slow, and hard to maintain. The new DB-driven, agent-based system is robust, fast, and easy to extend.
- **What's new:**
  - One DB query per message for all flow state.
  - Modular agent classes for each flow.
  - Stateless, DB-aware routing and prompting.
  - No redundant API calls.

### 2. Architecture Overview
- **FlowStateManager:**  Handles all DB queries for user flow state. Returns a `UserFlowState` object with all relevant info.
- **BaseFlowAgent:**  Abstract class defining the interface for all agents (`handle`, `extract_info`, `update_state`, `is_complete`, `prompt_for_next`, etc.).
- **IntroAgent, CreativityAgent, ProjectAgent, MainChatAgent:**  Each implements the flow logic for its stage, using DB state and robust extraction/prompting.
- **DatabaseDrivenChatHandler:**  Main entry point. On each message:
    1. Gets user flow state from DB.
    2. Routes to the correct agent.
    3. Stores conversation in memory.
    4. Returns the agent's response.

### 3. Detailed Implementation Steps

#### A. Remove Manager Agent API Call
- Delete any code that calls a manager agent for routing.
- All routing is now handled in `DatabaseDrivenChatHandler` using DB state.

#### B. Implement/Refine FlowStateManager
- Ensure all relevant fields (`intro_stage`, `intro_data`, `has_seen_intro`, `skipped_until`, `is_completed`, etc.) are queried in one go.
- Add methods for schema evolution and migration as flows change.

#### C. Refactor/Expand Agents
- **IntroAgent:**
  - Extracts name, project info, accountability experience.
  - Prompts for missing info, updates DB, marks intro complete when done.
  - Handles off-topic questions and readiness to proceed.
- **CreativityAgent:**
  - Handles all 12 creativity questions, skip logic, and result calculation.
  - Updates DB after each answer, marks complete when all are answered.
- **ProjectAgent:**
  - Handles all 8 project overview topics, using LLM extraction for complex answers.
  - Updates DB and marks complete when all topics are covered.
- **MainChatAgent:**
  - Handles general conversation, using memory/context as needed.

#### D. Robust Extraction and Prompting
- Use regex, keyword matching, and LLM calls for info extraction.
- Prompts should be dynamic, based on what's missing, and context-aware.

#### E. Error Handling and Observability
- Add detailed logging for all agent actions and DB updates.
- Implement user-facing error messages and fallback prompts.
- Track flow completion and drop-off rates for analytics.

#### F. Testing
- Unit tests for each agent's extraction, update, and prompt logic.
- End-to-end tests for full user journeys, abandon/resume, and edge cases.
- Use the `/new_tests` suite as a foundation.

#### G. Schema Evolution
- Document how to add new fields or flows, and how to migrate user state.
- Version agent logic if flows change significantly.

### 4. Example: Main Handler Routing (Expanded)

```python
async def process_message(user_id, message, thread_id, supabase_client):
    handler = DatabaseDrivenChatHandler(supabase_client)
    return await handler.process_message(user_id, message, thread_id)
```

- Inside `DatabaseDrivenChatHandler.process_message`:
    1. `flow_state = await self.state_manager.get_user_flow_state(user_id)`
    2. If not `flow_state.intro_complete`: `await self.intro_agent.handle(...)`
    3. Else if not `flow_state.creativity_complete` and not skipped: `await self.creativity_agent.handle(...)`
    4. Else if not `flow_state.project_complete`: `await self.project_agent.handle(...)`
    5. Else: `await self.main_chat_agent.handle(...)`

### 5. Incorporating the Other AI's Feedback

- **The other AI's implementation is robust and modular.**
  - The use of dataclasses, async methods, and clear agent interfaces is excellent.
  - The system is ready for further extension (e.g., more flows, richer context sharing).
- **Areas to expand:**
  - More advanced extraction (LLM-based for ambiguous input).
  - More granular error handling and user feedback.
  - Analytics and observability for flow completion/drop-off.
  - Schema migration/versioning for future-proofing.

### 6. Next Steps for Implementation

1. **Finalize and document the agent interfaces and flow state schema.**
2. **Implement/refine each agent's extraction, update, and prompt logic.**
3. **Remove all manager agent API calls and legacy state machine code.**
4. **Test with the real-world test suite and iterate on edge cases.**
5. **Add analytics and observability for flow tracking.**
6. **Document schema evolution and agent versioning for future changes.**

---

## Why This Matters

- This approach is robust, maintainable, and scalable.
- It's easy for any future AI or developer to understand, extend, and debug.
- It's aligned with your current schema and leverages the best of both the old and new systems.

---

**You can now share this plan and the code with any AI or developer, and they'll have everything they need to implement, test, and extend the system.** 