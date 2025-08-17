# Task 11: Basic Buddy Chat Implementation Plan

## Task Overview
Create a simple buddy chat page at `/buddy-chat/[matchId]` by reusing existing chat components and implementing basic message endpoints.

## Implementation Plan (Simple & Focused)

### Phase 1: Database Structure (30 mins)
**Reference**: Check existing message structure first
- Look for existing messages table in database
- If none exists, create simple `chat_messages` table:
  ```sql
  CREATE TABLE chat_messages (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    match_id uuid REFERENCES wingman_matches(match_id),
    sender_id uuid REFERENCES auth.users(id),
    message_text text CHECK (length(message_text) BETWEEN 2 AND 2000),
    created_at timestamptz DEFAULT now(),
    INDEX ON (match_id, created_at)
  );
  ```
- Add `last_read_timestamp` to existing user tables or create simple tracking

### Phase 2: Backend Endpoints (1 hour)
**Reference**: Follow patterns from `reference_files/src/main.py`
- **GET `/api/chat/messages/{match_id}`**: Basic message retrieval with pagination
- **POST `/api/chat/send`**: Simple message creation with validation
- Use existing Redis rate limiting (1 msg/0.5s)
- Validate user is participant in match before any operations

### Phase 3: Frontend Chat Page (1.5 hours)
**Reference**: Follow patterns from `reference_files/frontend_reference/FAF_website/app/chat/`
- Create `app/buddy-chat/[matchId]/page.tsx`
- Simple message list + input field
- Copy UI patterns from reference files (DON'T modify them)
- Basic styling with existing Chakra UI components

### Phase 4: Polling & Updates (30 mins)
- Simple 5-second polling with `setInterval`
- Append new messages to state
- Basic scroll position maintenance

### Phase 5: Static Venue Panel (30 mins)
- Simple toggleable section with hardcoded categories:
  - Coffee shops, Bookstores, Malls, Parks
- Basic tips/examples (no external API)

### Phase 6: Testing (1 hour)
- Create `tests/e2e/chat.spec.ts`
- Test basic send/receive flow
- Verify 5-second polling works
- Test access control (non-participants blocked)

## Success Criteria
- [ ] Users can send/receive text messages
- [ ] 5-second polling shows new messages  
- [ ] Only match participants can access chat
- [ ] Rate limiting prevents spam
- [ ] Static venue suggestions work

## Total Time: ~4.5 hours (simple implementation)

## Key Principles
- ✅ Follow existing patterns from reference files
- ✅ Don't modify reference_files/*
- ✅ Keep it simple - text-only messages
- ✅ Use existing Redis/auth infrastructure
- ✅ Minimal viable chat functionality