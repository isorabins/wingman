# Dating Goals Frontend Integration - Implementation Plan

## Overview
Implement frontend integration for the dating goals conversation system, adding a seamless flow from confidence assessment results to dating goals exploration.

## Current State Analysis
- ✅ Backend API already implemented (/api/dating-goals POST & GET endpoints)
- ✅ 4-topic conversation flow with AI coach (Connell Barrett style) 
- ✅ Progress tracking and completion states available
- ✅ Dating goals data storage with venue preferences and comfort levels
- ❌ No frontend integration exists yet
- ❌ No link from assessment results page

## Implementation Strategy

### 1. Dating Goals Conversation Page
**File**: `/app/dating-goals/page.tsx`
- Similar structure to confidence test flow
- Streaming conversation interface with AI coach
- Progress tracking (4 topics, completion percentage)
- Professional Chakra UI design matching existing patterns

### 2. Assessment Results Integration  
**File**: `/app/confidence-test/page.tsx` (modify results screen)
- Add link to dating goals in results section
- Position as "next step" after assessment completion
- Optional flow - users can skip to matching instead

### 3. API Integration Services
**File**: `/lib/dating-goals-api.ts` 
- TypeScript interface for API calls
- Error handling and retry logic
- Streaming response handling

### 4. Component Architecture
- **DatingGoalsChat**: Main conversation component
- **TopicProgress**: Progress indicator for 4 topics
- **GoalsCompletion**: Summary when flow complete
- **ConversationHistory**: Display previous messages

## Technical Requirements

### API Contract (Already Implemented)
```typescript
// Start/continue conversation
POST /api/dating-goals
{
  user_id: string,
  message: string, 
  thread_id?: string
}
→ {
  success: boolean,
  message: string,          // AI coach response
  thread_id: string,
  is_complete: boolean,
  topic_number: number,     // Current topic (1-4)
  completion_percentage: number
}

// Get completed goals
GET /api/dating-goals/{user_id}
→ {
  success: boolean,
  goals: string,
  preferred_venues: string[],
  comfort_level: 'low'|'moderate'|'high',
  goals_data: object,
  created_at: string,
  updated_at: string
}
```

### Design Patterns
- Follow confidence test UI patterns from `/app/confidence-test/page.tsx`
- Use Chakra UI components: Box, VStack, Button, Progress, etc.
- Maintain brand colors: brand.900, brand.50, brand.400
- Mobile-first responsive design
- Loading states and error handling

### Conversation Flow (4 Topics)
1. **Topic 1**: Core dating goals and objectives
2. **Topic 2**: Preferred venues and meeting settings  
3. **Topic 3**: Comfort level and boundaries
4. **Topic 4**: Integration with wingman matching

### Integration Points
- **From**: Confidence test results page
- **To**: Goals completion → buddy matching flow
- **Memory**: Goals available to AI coach in future conversations

## Implementation Tasks

### Task 1: Create Dating Goals API Service
- [ ] Create `/lib/dating-goals-api.ts`
- [ ] TypeScript interfaces for API responses
- [ ] Error handling and validation
- [ ] Streaming response utilities

### Task 2: Build Dating Goals Conversation Page
- [ ] Create `/app/dating-goals/page.tsx`
- [ ] Chat interface with message history
- [ ] Progress tracking (4 topics)
- [ ] Loading states and error handling
- [ ] Mobile-responsive design

### Task 3: Add Results Page Integration
- [ ] Modify `/app/confidence-test/page.tsx` results screen
- [ ] Add "Continue to Dating Goals" button
- [ ] Optional flow design (can skip to matching)
- [ ] Preserve existing "Continue to Matching" option

### Task 4: Create Supporting Components
- [ ] `components/DatingGoalsChat.tsx` - Main conversation
- [ ] `components/TopicProgress.tsx` - Progress indicator  
- [ ] `components/GoalsCompletion.tsx` - Summary screen
- [ ] Navigation and routing logic

### Task 5: Testing & Integration
- [ ] Unit tests for components
- [ ] Integration testing with API
- [ ] User flow testing (assessment → goals → matching)
- [ ] Error handling validation

## Success Criteria
- [ ] Users can access dating goals from assessment results
- [ ] 4-topic conversation flows smoothly with AI coach
- [ ] Progress tracking works correctly
- [ ] Completed goals integrate with buddy matching
- [ ] Mobile-responsive and accessible
- [ ] Follows existing UI/UX patterns
- [ ] Proper error handling and loading states

## Architecture Notes
- **State Management**: Local state for conversation history
- **API Integration**: RESTful calls with proper error handling  
- **UI Framework**: Chakra UI matching confidence test patterns
- **Routing**: Next.js app router with dynamic routes
- **Authentication**: Use existing auth context for user ID
- **Memory**: Conversation stored in backend for coach integration

## Files to Create/Modify
- ✅ **Create**: `/app/dating-goals/page.tsx` - Main dating goals page
- ✅ **Create**: `/lib/dating-goals-api.ts` - API service functions
- ✅ **Create**: `components/DatingGoalsChat.tsx` - Conversation component
- ✅ **Modify**: `/app/confidence-test/page.tsx` - Add link in results
- ✅ **Optional**: Additional components as needed

This plan delivers a complete frontend integration for the dating goals system, seamlessly connecting confidence assessment to goal setting and buddy matching.