# Claude Agents Implementation Guide: Creativity Test & Project Overview

## Why This Implementation

**Business Context:**
Your users need guidance through two critical onboarding flows:
1. **Creativity Assessment** - Understanding their creative archetype for personalized coaching
2. **Project Planning** - Structured 8-topic planning to set them up for success

**Current Challenge:**
Your existing system has basic project planning logic, but it's incomplete - users start flows but don't complete them because there's no state persistence or clear endpoints. You need robust agents that can handle mid-flow interruptions and provide definitive completion experiences.

**Solution:**
Specialized Claude agents using the augmented LLM pattern that integrate seamlessly with your existing LLM router and provide structured, completable experiences.

## Key Features & Benefits

✅ **Mid-Flow State Persistence** - Users can pause and resume anywhere in the 7-question creativity test or 8-topic project planning  
✅ **Automatic Integration** - Triggers when users haven't completed these flows yet (integrates with your existing trigger logic)  
✅ **Structured Data Collection** - Saves properly formatted data to your existing tables for future dashboard use  
✅ **LLM Router Compatible** - Uses your existing fallback system while providing reliable tool calling  
✅ **Clear Completion Experience** - Users get definitive results (creativity archetype reveal, project summary review)  
✅ **Production Ready** - Comprehensive error handling, logging, and testing framework  

## Architecture Decision: Augmented LLM + Integration

This implementation follows 2024-2025 best practices for building production-ready Claude agents with:
- **Two specialized agents** using augmented LLM pattern (not full autonomous agents)
- **Structured tools with explicit parameters** (no raw SQL, type hints for validation)
- **Mid-flow state persistence** with clean resumption logic
- **Integration with your existing LLM router** for automatic fallback
- **XML-structured prompts** for optimal Claude performance
- **Simple, maintainable architecture** avoiding over-engineering

## Integration with Your Existing System

Based on your project knowledge, you already have trigger logic in `src/project_planning.py` and `src/claude_agent.py`. Here's how the agents integrate:

### Current System Analysis
Your existing code has:
- `should_trigger_project_planning()` - checks if user has project overview
- `check_and_handle_project_onboarding()` - triggers creativity test then project planning  
- Basic flow logic but incomplete state management

### Agent Integration Points

```python
# src/claude_agent.py - Update your existing integration
async def check_and_handle_project_onboarding(supabase_client, user_id: str, user_input: str) -> Dict[str, Any]:
    """
    Enhanced version of your existing function with agent integration.
    
    Two-step flow: creativity test first, then project planning.
    Now with proper state management and completion detection.
    """
    try:
        # Import agent factory
        from src.agents import AgentFactory
        agent_factory = AgentFactory()
        
        # Check creativity test status first
        creativity_agent = agent_factory.create_creativity_test_agent()
        creativity_progress = await creativity_agent.db_tools.get_creativity_progress(user_id)
        
        # Check for existing creativity profile  
        existing_profile = supabase_client.table('creator_creativity_profiles').select('*').eq('user_id', user_id).execute()
        has_creativity_profile = len(existing_profile.data) > 0
        
        if not has_creativity_profile and not creativity_progress['exists']:
            # Start creativity test
            response = await creativity_agent.process_message(user_id, user_input)
            return {
                "should_replace_input": True,
                "replacement_response": response,
                "onboarding_active": True,
                "flow_type": "creativity_test"
            }
            
        elif creativity_progress['exists'] and not creativity_progress['is_complete']:
            # Continue creativity test
            response = await creativity_agent.process_message(user_id, user_input)
            return {
                "should_replace_input": True, 
                "replacement_response": response,
                "onboarding_active": True,
                "flow_type": "creativity_test"
            }
            
        # Check project overview status
        has_project = await check_user_has_project_overview(supabase_client, user_id)
        
        if not has_project:
            # Check for project planning progress
            project_agent = agent_factory.create_project_overview_agent()
            project_progress = await project_agent.db_tools.get_project_progress(user_id)
            
            if not project_progress['exists']:
                # Start project planning
                response = await project_agent.process_message(user_id, user_input)
                return {
                    "should_replace_input": True,
                    "replacement_response": response, 
                    "onboarding_active": True,
                    "flow_type": "project_planning"
                }
            elif not project_progress['is_complete']:
                # Continue project planning
                response = await project_agent.process_message(user_id, user_input)
                return {
                    "should_replace_input": True,
                    "replacement_response": response,
                    "onboarding_active": True, 
                    "flow_type": "project_planning"
                }
        
        # No onboarding needed
        return {
            "should_replace_input": False,
            "replacement_response": None,
            "onboarding_active": False,
            "flow_type": None
        }
        
    except Exception as e:
        logger.error(f"Error in project onboarding check: {e}")
        return {
            "should_replace_input": False,
            "replacement_response": None,
            "onboarding_active": False,
            "flow_type": None,
            "error": str(e)
        }

# In your main conversation logic, update the call:
async def send_query_to_claude(supabase_client, user_id: str, user_input: str) -> str:
    """Your existing function with agent integration."""
    
    # Check for onboarding needs (enhanced with agents)
    onboarding_result = await check_and_handle_project_onboarding(supabase_client, user_id, user_input)
    
    if onboarding_result["should_replace_input"]:
        # Agent is handling the conversation
        logger.info(f"Agent handling conversation - flow: {onboarding_result['flow_type']}")
        return onboarding_result["replacement_response"]
    
    # Continue with normal conversation flow
    # ... your existing conversation logic
```

### System Prompts Integration

Your agents include system prompts that handle the conversation flow automatically. Here are the key prompts:

**Creativity Test Agent System Prompt:**
- Guides through 7 questions sequentially
- Saves progress after each answer
- Calculates and reveals archetype at completion
- Handles resumption gracefully

**Project Overview Agent System Prompt:**  
- Guides through 8 topics comprehensively
- Builds on your existing planning framework
- Presents beautiful summary for review
- Allows iteration and refinement

Both prompts are included in the agent implementations (sections 4-5) and follow XML structuring for optimal Claude performance.

### Fallback Integration

The agents integrate with your LLM router for error recovery:

```python
# In BaseAgent.process_message() - automatic fallback
except Exception as e:
    logger.error(f"Error processing message in {self.__class__.__name__}: {e}")
    
    # Fallback to LLM router for error recovery
    try:
        from src.llm_router import get_router
        router = await get_router()
        
        fallback_response = await router.send_message(
            messages=[{"role": "user", "content": message}],
            system="The user was interacting with a specialized agent, but there was a technical issue. Please provide a helpful response and suggest they try again.",
            model=self.model,
            max_tokens=self.max_tokens,
            stream=False
        )
        
        return f"I apologize, but I encountered a technical issue. Here's a helpful response: {fallback_response}"
        
    except Exception as fallback_error:
        logger.error(f"Fallback also failed: {fallback_error}")
        return "I apologize, but I'm experiencing technical difficulties. Please try again in a moment."
```

## Architecture Decision: Augmented LLM + Integration

Based on Anthropic's guidance, we use **augmented LLMs** with **direct Anthropic clients for tool calling**, while leveraging your LLM router for regular conversations. This provides the best of both worlds:
- ✅ **Reliable tool calling** with Anthropic's native API
- ✅ **Fallback protection** via LLM router for regular chat
- ✅ **Simple implementation** following Anthropic's recommendations

## 1. Database Schema (Add to Your Existing Supabase)

```sql
-- Add these tables to your existing Supabase schema
-- Progress tracking for mid-flow saves and resumption

CREATE TABLE creativity_test_progress (
    user_id UUID PRIMARY KEY REFERENCES creator_profiles(id) ON DELETE CASCADE,
    current_question INTEGER NOT NULL CHECK (current_question >= 1 AND current_question <= 7),
    answers JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE project_overview_progress (
    user_id UUID PRIMARY KEY REFERENCES creator_profiles(id) ON DELETE CASCADE,
    current_topic INTEGER NOT NULL CHECK (current_topic >= 1 AND current_topic <= 8),
    collected_data JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add indexes for performance
CREATE INDEX idx_creativity_progress_updated ON creativity_test_progress(updated_at);
CREATE INDEX idx_project_progress_updated ON project_overview_progress(updated_at);
```

## 2. Database Tools (Supabase Integration)

```python
# src/tools/database_tools.py
from supabase import Client
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class DatabaseTools:
    """Database operations for agent state management and final result storage."""
    
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client

    # === CREATIVITY TEST TOOLS ===

    async def save_creativity_answer(
        self,
        user_id: str,
        question_number: int,
        question_text: str,
        answer_text: str
    ) -> Dict[str, Any]:
        """
        Save a single creativity test answer and update progress.
        
        This tool saves individual question responses and tracks overall progress
        through the 7-question creativity assessment. It handles upsert logic
        to allow users to modify previous answers and provides progress tracking.
        
        Args:
            user_id: Unique identifier for the user taking the test
            question_number: Question sequence number (1-7)
            question_text: The exact question that was asked to the user
            answer_text: User's complete response to the question
            
        Returns:
            Dict with success status, current progress, and question count
        """
        try:
            # Get existing progress
            result = self.supabase.table('creativity_test_progress').select('*').eq('user_id', user_id).execute()
            
            if result.data:
                answers = result.data[0]['answers']
            else:
                answers = {}
            
            # Add new answer with metadata
            answers[f"q{question_number}"] = {
                "question": question_text,
                "answer": answer_text,
                "timestamp": datetime.now().isoformat(),
                "question_number": question_number
            }
            
            # Upsert progress
            upsert_result = self.supabase.table('creativity_test_progress').upsert({
                'user_id': user_id,
                'current_question': question_number,
                'answers': answers,
                'updated_at': datetime.now().isoformat()
            }).execute()
            
            logger.info(f"Saved creativity answer {question_number}/7 for user {user_id}")
            
            return {
                "success": True,
                "current_question": question_number,
                "total_questions": 7,
                "answers_count": len(answers),
                "progress_percentage": round((len(answers) / 7) * 100, 1)
            }
            
        except Exception as e:
            logger.error(f"Error saving creativity answer: {e}")
            return {
                "success": False,
                "error": f"Failed to save answer: {str(e)}",
                "current_question": question_number,
                "total_questions": 7
            }

    async def get_creativity_progress(self, user_id: str) -> Dict[str, Any]:
        """
        Load current creativity test progress for user.
        
        Retrieves the user's current position in the creativity test, including
        all previously answered questions and determines if the test is complete.
        Used for resuming interrupted test sessions and avoiding duplicate questions.
        
        Args:
            user_id: Unique identifier for the user
            
        Returns:
            Dict with progress status, current question, answers, and completion status
        """
        try:
            result = self.supabase.table('creativity_test_progress').select('*').eq('user_id', user_id).execute()
            
            if not result.data:
                return {
                    "exists": False,
                    "current_question": 1,
                    "answers": {},
                    "is_complete": False,
                    "progress_percentage": 0.0
                }
            
            progress = result.data[0]
            answers = progress['answers']
            is_complete = len(answers) >= 7
            
            logger.info(f"Loaded creativity progress for user {user_id}: {len(answers)}/7 questions")
            
            return {
                "exists": True,
                "current_question": progress['current_question'],
                "answers": answers,
                "is_complete": is_complete,
                "progress_percentage": round((len(answers) / 7) * 100, 1),
                "last_updated": progress['updated_at']
            }
            
        except Exception as e:
            logger.error(f"Error loading creativity progress: {e}")
            return {
                "exists": False,
                "error": f"Failed to load progress: {str(e)}",
                "current_question": 1,
                "answers": {},
                "is_complete": False
            }

    async def complete_creativity_test(
        self,
        user_id: str,
        archetype: str,
        archetype_description: str,
        archetype_score: float,
        test_responses: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Complete creativity test and store final results in your existing table.
        
        Saves the final creativity assessment results to creator_creativity_profiles
        and cleans up the progress tracking table. This tool should only be called
        after all 7 questions have been answered and the archetype has been calculated.
        
        Args:
            user_id: User identifier
            archetype: Calculated creativity archetype (Explorer, Innovator, Artist, Builder, Collaborator, Synthesizer)
            archetype_description: Detailed 2-3 sentence description of the archetype
            archetype_score: Confidence score for the archetype assignment (0.0-1.0)
            test_responses: Complete dictionary of all user responses for future reference
            
        Returns:
            Dict with completion status and archetype information
        """
        try:
            # Insert into your existing table structure
            result = self.supabase.table('creator_creativity_profiles').upsert({
                'user_id': user_id,
                'archetype': archetype,
                'archetype_score': archetype_score,
                'test_responses': test_responses,
                'created_at': datetime.now().isoformat()
            }).execute()
            
            # Clean up progress table
            self.supabase.table('creativity_test_progress').delete().eq('user_id', user_id).execute()
            
            logger.info(f"Completed creativity test for user {user_id}: {archetype} ({archetype_score:.2f})")
            
            return {
                "success": True,
                "archetype": archetype,
                "archetype_score": archetype_score,
                "message": f"Creativity test completed! You are a {archetype}."
            }
            
        except Exception as e:
            logger.error(f"Error completing creativity test: {e}")
            return {
                "success": False,
                "error": f"Failed to complete test: {str(e)}"
            }

    # === PROJECT OVERVIEW TOOLS ===

    async def save_project_topic(
        self,
        user_id: str,
        topic_number: int,
        topic_name: str,
        response_text: str
    ) -> Dict[str, Any]:
        """
        Save project planning topic response and update progress.
        
        Stores individual topic responses during the 8-topic project planning session.
        Handles upsert logic for topic modifications and tracks overall planning progress.
        Each topic represents a key aspect of project planning (description, goals, timeline, etc.).
        
        Args:
            user_id: Unique identifier for the user
            topic_number: Topic sequence number (1-8)
            topic_name: Name of the topic (e.g., 'Project Description', 'Goals', 'Timeline')
            response_text: User's detailed response about this topic
            
        Returns:
            Dict with success status, current progress, and topic completion count
        """
        try:
            # Get existing data
            result = self.supabase.table('project_overview_progress').select('*').eq('user_id', user_id).execute()
            
            if result.data:
                data = result.data[0]['collected_data']
            else:
                data = {}
            
            # Add new topic data with metadata
            data[f"topic_{topic_number}"] = {
                "name": topic_name,
                "response": response_text,
                "timestamp": datetime.now().isoformat(),
                "topic_number": topic_number
            }
            
            # Upsert progress
            upsert_result = self.supabase.table('project_overview_progress').upsert({
                'user_id': user_id,
                'current_topic': topic_number,
                'collected_data': data,
                'updated_at': datetime.now().isoformat()
            }).execute()
            
            logger.info(f"Saved project topic {topic_number}/8 for user {user_id}: {topic_name}")
            
            return {
                "success": True,
                "current_topic": topic_number,
                "total_topics": 8,
                "topics_completed": len(data),
                "progress_percentage": round((len(data) / 8) * 100, 1)
            }
            
        except Exception as e:
            logger.error(f"Error saving project topic: {e}")
            return {
                "success": False,
                "error": f"Failed to save topic: {str(e)}",
                "current_topic": topic_number,
                "total_topics": 8
            }

    async def get_project_progress(self, user_id: str) -> Dict[str, Any]:
        """
        Load current project overview progress for user.
        
        Retrieves the user's current position in the project planning process,
        including all previously completed topics and determines completion status.
        Used for resuming interrupted planning sessions and building on previous work.
        
        Args:
            user_id: Unique identifier for the user
            
        Returns:
            Dict with progress status, current topic, collected data, and completion status
        """
        try:
            result = self.supabase.table('project_overview_progress').select('*').eq('user_id', user_id).execute()
            
            if not result.data:
                return {
                    "exists": False,
                    "current_topic": 1,
                    "collected_data": {},
                    "is_complete": False,
                    "progress_percentage": 0.0
                }
            
            progress = result.data[0]
            collected_data = progress['collected_data']
            is_complete = len(collected_data) >= 8
            
            logger.info(f"Loaded project progress for user {user_id}: {len(collected_data)}/8 topics")
            
            return {
                "exists": True,
                "current_topic": progress['current_topic'],
                "collected_data": collected_data,
                "is_complete": is_complete,
                "progress_percentage": round((len(collected_data) / 8) * 100, 1),
                "last_updated": progress['updated_at']
            }
            
        except Exception as e:
            logger.error(f"Error loading project progress: {e}")
            return {
                "exists": False,
                "error": f"Failed to load progress: {str(e)}",
                "current_topic": 1,
                "collected_data": {},
                "is_complete": False
            }

    async def complete_project_overview(
        self,
        user_id: str,
        project_name: str,
        project_type: str,
        description: str,
        goals: Dict[str, Any],
        challenges: Dict[str, Any],
        success_metrics: str
    ) -> Dict[str, Any]:
        """
        Complete project overview and store final results in your existing table.
        
        Extracts structured data from the 8-topic planning session and stores it
        in the project_overview table using your existing schema. Cleans up the
        progress tracking table after successful completion.
        
        Args:
            user_id: User identifier
            project_name: Clear, concise name for the project
            project_type: Category (writing, design, business, technology, etc.)
            description: Comprehensive description of what they're creating
            goals: Dictionary containing structured goals and milestones
            challenges: Dictionary containing anticipated challenges and solutions
            success_metrics: How they'll measure project success
            
        Returns:
            Dict with completion status and project information
        """
        try:
            # Insert into your existing table structure
            result = self.supabase.table('project_overview').upsert({
                'user_id': user_id,
                'project_name': project_name,
                'project_type': project_type,
                'description': description,
                'goals': goals,
                'challenges': challenges,
                'success_metrics': success_metrics,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }).execute()
            
            # Clean up progress table
            self.supabase.table('project_overview_progress').delete().eq('user_id', user_id).execute()
            
            project_id = result.data[0]['id'] if result.data else None
            
            logger.info(f"Completed project overview for user {user_id}: {project_name}")
            
            return {
                "success": True,
                "project_id": project_id,
                "project_name": project_name,
                "message": f"Project overview completed for '{project_name}'!"
            }
            
        except Exception as e:
            logger.error(f"Error completing project overview: {e}")
            return {
                "success": False,
                "error": f"Failed to complete project: {str(e)}"
            }
```

## 3. Agent Base Class (Production Architecture)

```python
# src/agents/base_agent.py
from abc import ABC, abstractmethod
from anthropic import AsyncAnthropic
from typing import Dict, List, Any, Optional
import json
import logging
import os

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    """
    Base class for Claude agents using augmented LLM pattern.
    
    Uses direct Anthropic client for reliable tool calling while integrating
    with LLM router for fallback protection in regular conversations.
    """
    
    def __init__(self, db_tools):
        self.db_tools = db_tools
        self.anthropic_client = AsyncAnthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
        self.model = "claude-3-5-sonnet-20241022"
        self.max_tokens = 2000

    @abstractmethod
    def get_system_prompt(self) -> str:
        """Return the XML-structured system prompt for this agent."""
        pass

    @abstractmethod
    def get_tools(self) -> List[Dict[str, Any]]:
        """Return the tool definitions for this agent."""
        pass

    async def handle_tool_call(self, tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Route tool calls to appropriate database methods with error handling."""
        method_name = f"tool_{tool_name}"
        if hasattr(self, method_name):
            method = getattr(self, method_name)
            try:
                result = await method(**tool_input)
                logger.info(f"Tool {tool_name} executed successfully")
                return result
            except Exception as e:
                logger.error(f"Tool {tool_name} failed: {e}")
                return {
                    "success": False,
                    "error": f"Tool execution failed: {str(e)}"
                }
        else:
            logger.error(f"Unknown tool: {tool_name}")
            return {
                "success": False,
                "error": f"Unknown tool: {tool_name}"
            }

    async def process_message(self, user_id: str, message: str) -> str:
        """
        Process user message through the agent with tool calling support.
        
        Uses direct Anthropic client for reliable tool calling while maintaining
        integration with your existing LLM router for regular conversations.
        """
        try:
            # Create conversation with proper user context
            messages = [
                {
                    "role": "user", 
                    "content": f"User ID: {user_id}\n\nUser Message: {message}"
                }
            ]

            # Initial call to Claude with tools
            response = await self.anthropic_client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                system=self.get_system_prompt(),
                tools=self.get_tools(),
                tool_choice={"type": "auto"},  # Let Claude decide when to use tools
                messages=messages
            )

            # Handle tool calls if present
            if response.stop_reason == "tool_use":
                # Process all tool calls in the response
                tool_results = []
                
                for content_block in response.content:
                    if content_block.type == "tool_use":
                        # Execute the tool
                        tool_result = await self.handle_tool_call(
                            content_block.name,
                            content_block.input
                        )
                        
                        tool_results.append({
                            "tool_use_id": content_block.id,
                            "content": json.dumps(tool_result)
                        })

                # Continue conversation with tool results
                messages.extend([
                    {"role": "assistant", "content": response.content},
                    {"role": "user", "content": tool_results}
                ])

                # Get final response after tool execution
                final_response = await self.anthropic_client.messages.create(
                    model=self.model,
                    max_tokens=self.max_tokens,
                    system=self.get_system_prompt(),
                    tools=self.get_tools(),
                    messages=messages
                )
                
                return final_response.content[0].text if final_response.content else "I apologize, but I didn't receive a proper response."

            else:
                # No tools used, return direct response
                return response.content[0].text if response.content else "I apologize, but I didn't receive a proper response."

        except Exception as e:
            logger.error(f"Error processing message in {self.__class__.__name__}: {e}")
            
            # Fallback to LLM router for error recovery
            try:
                from src.llm_router import get_router
                router = await get_router()
                
                fallback_response = await router.send_message(
                    messages=[{"role": "user", "content": message}],
                    system="You are a helpful AI assistant. The user was interacting with a specialized agent, but there was a technical issue. Please provide a helpful response and suggest they try again.",
                    model=self.model,
                    max_tokens=self.max_tokens,
                    stream=False
                )
                
                return f"I apologize, but I encountered a technical issue. Here's a helpful response: {fallback_response}"
                
            except Exception as fallback_error:
                logger.error(f"Fallback also failed: {fallback_error}")
                return "I apologize, but I'm experiencing technical difficulties. Please try again in a moment."
```

## 4. Creativity Test Agent (Perfect Implementation)

```python
# src/agents/creativity_test_agent.py
from .base_agent import BaseAgent
from typing import Dict, List, Any

class CreativityTestAgent(BaseAgent):
    """
    Specialized agent for conducting 7-question creativity assessments.
    
    Follows augmented LLM pattern with structured tools for state management
    and archetype calculation. Provides warm, engaging experience while
    collecting reliable data for creativity profiling.
    """
    
    def __init__(self, db_tools):
        super().__init__(db_tools)
        self.max_tokens = 1500  # Appropriate for creativity conversations
    
    def get_system_prompt(self) -> str:
        return """<role>
You are an expert creativity assessment specialist conducting a comprehensive 7-question evaluation to determine someone's creativity archetype. Your mission is to create a warm, engaging experience while collecting precise data for accurate profiling.
</role>

<workflow>
1. ALWAYS start by checking user progress with get_creativity_progress
2. If resuming, warmly acknowledge their previous work and continue from where they left off
3. Guide through questions sequentially (1-7), asking ONE question at a time
4. After each answer, use save_creativity_answer to preserve their response
5. When all 7 questions are complete, analyze patterns and use complete_creativity_test
6. Present results with celebration and encouragement for their creative journey
</workflow>

<assessment_framework>
CREATIVITY ARCHETYPES (choose the best fit):
• Explorer: Thrives on discovery, experimentation, and new experiences
• Innovator: Focuses on problem-solving and creating practical solutions  
• Artist: Expresses creativity through aesthetic, emotional, and sensory means
• Builder: Creates systems, structures, and tangible outcomes
• Collaborator: Generates ideas through teamwork and social interaction
• Synthesizer: Combines diverse concepts and perspectives into unified wholes

QUESTION SEQUENCE (ask in order):
1. When do you feel most creative and energized?
2. How do you typically respond to creative challenges?
3. What's your biggest challenge when working on projects?
4. How do you prefer to track your progress?
5. When are you comfortable sharing your creative work?
6. How do you best process new ideas and inspiration?
7. What aspects of creative projects give you the most satisfaction?
</assessment_framework>

<interaction_style>
• Be genuinely warm, encouraging, and personally engaged
• Ask follow-up questions to deepen understanding
• Acknowledge and build on their responses with enthusiasm
• Use their name when they provide it
• Maintain natural conversation flow while staying focused
• Save progress after EVERY question to enable resumption
• Celebrate their insights and creative perspectives
</interaction_style>

<completion_protocol>
After collecting all 7 responses:
1. Analyze response patterns across all questions
2. Identify strongest archetype based on consistent themes
3. Calculate confidence score (0.0-1.0) based on pattern clarity
4. Write compelling 2-3 sentence description of their archetype
5. Use complete_creativity_test with all parameters
6. Present results with enthusiasm and actionable insights
</completion_protocol>

<error_handling>
If any tool fails, acknowledge the issue gracefully and either retry or guide the user to continue manually. Always maintain the warm, supportive tone even during technical difficulties.
</error_handling>"""

    def get_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "get_creativity_progress",
                "description": "Retrieve the user's current progress in the creativity assessment to determine where to resume. This tool checks if they have already answered some questions and loads their previous responses. Always call this first when starting any interaction to avoid asking duplicate questions and to provide continuity in their assessment experience.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "string",
                            "description": "Unique identifier for the user taking the creativity assessment"
                        }
                    },
                    "required": ["user_id"]
                }
            },
            {
                "name": "save_creativity_answer",
                "description": "Save the user's response to a specific creativity test question and update their progress. This tool preserves their answer, tracks which question they completed, and enables resumption if they need to pause the assessment. Call this immediately after receiving each answer to ensure no progress is lost.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "string", 
                            "description": "Unique identifier for the user taking the assessment"
                        },
                        "question_number": {
                            "type": "integer",
                            "description": "Question sequence number from 1 to 7",
                            "minimum": 1,
                            "maximum": 7
                        },
                        "question_text": {
                            "type": "string",
                            "description": "The exact question that was asked to the user, for reference and consistency"
                        },
                        "answer_text": {
                            "type": "string",
                            "description": "The user's complete response to the question, preserving their exact words"
                        }
                    },
                    "required": ["user_id", "question_number", "question_text", "answer_text"]
                }
            },
            {
                "name": "complete_creativity_test",
                "description": "Complete the creativity assessment by calculating and storing the user's final archetype and results. This tool should only be called after all 7 questions have been answered. It performs the final analysis, determines their creativity archetype, and saves the complete profile for future reference and coaching.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "string",
                            "description": "Unique identifier for the user completing the assessment"
                        },
                        "archetype": {
                            "type": "string",
                            "description": "Primary creativity archetype based on response analysis: Explorer, Innovator, Artist, Builder, Collaborator, or Synthesizer"
                        },
                        "archetype_description": {
                            "type": "string",
                            "description": "Compelling 2-3 sentence description explaining what this archetype means, their creative strengths, and how they approach creative work"
                        },
                        "archetype_score": {
                            "type": "number",
                            "description": "Confidence score for the archetype assignment, ranging from 0.0 to 1.0, where 1.0 indicates very strong pattern match",
                            "minimum": 0.0,
                            "maximum": 1.0
                        },
                        "test_responses": {
                            "type": "object",
                            "description": "Complete dictionary containing all user responses, question metadata, analysis notes, and any additional insights for future reference"
                        }
                    },
                    "required": ["user_id", "archetype", "archetype_description", "archetype_score", "test_responses"]
                }
            }
        ]

    # Tool method implementations
    async def tool_get_creativity_progress(self, user_id: str) -> Dict[str, Any]:
        return await self.db_tools.get_creativity_progress(user_id)

    async def tool_save_creativity_answer(self, user_id: str, question_number: int, 
                                        question_text: str, answer_text: str) -> Dict[str, Any]:
        return await self.db_tools.save_creativity_answer(
            user_id, question_number, question_text, answer_text
        )

    async def tool_complete_creativity_test(self, user_id: str, archetype: str, 
                                          archetype_description: str, archetype_score: float,
                                          test_responses: Dict[str, Any]) -> Dict[str, Any]:
        return await self.db_tools.complete_creativity_test(
            user_id, archetype, archetype_description, archetype_score, test_responses
        )
```

## 5. Project Overview Agent (Perfect Implementation)

```python
# src/agents/project_overview_agent.py
from .base_agent import BaseAgent
from typing import Dict, List, Any

class ProjectOverviewAgent(BaseAgent):
    """
    Specialized agent for comprehensive 8-topic project planning.
    
    Guides users through structured project planning while maintaining
    enthusiasm and building excitement for their creative journey.
    Integrates with existing project_overview table structure.
    """
    
    def __init__(self, db_tools):
        super().__init__(db_tools)
        self.max_tokens = 2000  # Higher limit for project planning discussions
    
    def get_system_prompt(self) -> str:
        return """<role>
You are an expert project planning coach who helps creators build comprehensive project overviews. Your mission is to guide them through 8 essential topics while building excitement and confidence for their creative journey.
</role>

<workflow>
1. ALWAYS start by checking existing progress with get_project_progress
2. If resuming, enthusiastically acknowledge their previous work and continue from current topic
3. Guide through topics sequentially (1-8), focusing on ONE topic at a time
4. After each topic discussion, use save_project_topic to preserve their insights
5. When all 8 topics are complete, extract structured data and use complete_project_overview
6. Present beautiful summary for review and offer iteration opportunities
7. Celebrate their completed planning process and readiness to begin
</workflow>

<project_planning_framework>
8 ESSENTIAL TOPICS (cover in sequence):

1. PROJECT DESCRIPTION
   • What they're creating or building
   • Core concept and unique value
   • Target audience or beneficiaries

2. GOALS & MILESTONES  
   • Specific, measurable objectives
   • Key milestones and deadlines
   • Success criteria and outcomes

3. TIMELINE & SCHEDULE
   • Target completion timeframe
   • Major phases and deadlines
   • Critical path dependencies

4. TIME COMMITMENT
   • Weekly hours available
   • Best times for focused work
   • Realistic schedule constraints

5. PROGRESS TRACKING
   • How they'll measure advancement
   • Tools and methods for monitoring
   • Accountability systems

6. RESOURCES & SUPPORT
   • Skills, tools, and materials needed
   • Learning requirements
   • Support network and collaboration

7. CHALLENGES & SOLUTIONS
   • Anticipated obstacles and risks
   • Mitigation strategies
   • Backup plans and alternatives

8. MOTIVATION & PURPOSE
   • Why this project matters to them
   • Personal meaning and impact
   • Long-term vision and legacy
</project_planning_framework>

<interaction_style>
• Be enthusiastic, supportive, and personally invested in their success
• Ask thoughtful follow-up questions to deepen their thinking
• Help them think bigger while staying realistic
• Acknowledge their vision and validate their goals
• Build excitement for their creative potential
• Save progress after each topic to enable seamless resumption
• Use their project name and details to personalize the conversation
</interaction_style>

<completion_protocol>
After collecting all 8 topics:
1. Extract and organize structured information from their responses
2. Create clear, actionable project overview using complete_project_overview
3. Present summary in beautiful, inspiring format
4. Ask if they want to modify or expand any aspects
5. If changes requested, update stored data accordingly
6. Celebrate their comprehensive planning achievement
</completion_protocol>

<project_types>
Common categories: writing, design, business, education, technology, art, music, film, research, personal development, health, community, environment, innovation
</project_types>

<error_handling>
If any tool fails, maintain enthusiasm while addressing the issue. Guide users to continue the planning process manually if needed, ensuring their valuable insights aren't lost.
</error_handling>"""

    def get_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "get_project_progress", 
                "description": "Retrieve the user's current progress in the project planning process to determine where to resume. This tool loads their previously completed topics and identifies the next topic to discuss. Always call this first when starting any interaction to provide continuity and avoid repeating completed work.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "string",
                            "description": "Unique identifier for the user working on project planning"
                        }
                    },
                    "required": ["user_id"]
                }
            },
            {
                "name": "save_project_topic",
                "description": "Save the user's insights and responses for a specific project planning topic and update their progress. This tool preserves their detailed thinking about each topic, tracks completion, and enables resumption if they need to pause the planning session. Call this after thoroughly discussing each topic.",
                "input_schema": {
                    "type": "object", 
                    "properties": {
                        "user_id": {
                            "type": "string",
                            "description": "Unique identifier for the user working on project planning"
                        },
                        "topic_number": {
                            "type": "integer",
                            "description": "Topic sequence number from 1 to 8",
                            "minimum": 1,
                            "maximum": 8
                        },
                        "topic_name": {
                            "type": "string",
                            "description": "Name of the topic being discussed (e.g., 'Project Description', 'Goals & Milestones', 'Timeline & Schedule')"
                        },
                        "response_text": {
                            "type": "string",
                            "description": "The user's complete insights, ideas, and responses about this topic, preserving their detailed thinking"
                        }
                    },
                    "required": ["user_id", "topic_number", "topic_name", "response_text"]
                }
            },
            {
                "name": "complete_project_overview",
                "description": "Complete the project planning process by extracting structured data from all 8 topics and storing the final project overview. This tool should only be called after all topics have been thoroughly discussed. It creates the structured project overview that will guide their ongoing work and coaching relationship.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "string",
                            "description": "Unique identifier for the user completing project planning"
                        },
                        "project_name": {
                            "type": "string", 
                            "description": "Clear, compelling name for the project that captures its essence"
                        },
                        "project_type": {
                            "type": "string",
                            "description": "Category of project (writing, design, business, technology, art, music, etc.) for classification and coaching optimization"
                        },
                        "description": {
                            "type": "string",
                            "description": "Comprehensive description of what they're creating, including core concept, unique value, and target audience"
                        },
                        "goals": {
                            "type": "object",
                            "description": "Structured dictionary containing their specific goals, milestones, deadlines, and success criteria organized for easy reference"
                        },
                        "challenges": {
                            "type": "object",
                            "description": "Structured dictionary containing anticipated challenges, risks, mitigation strategies, and backup plans"
                        },
                        "success_metrics": {
                            "type": "string",
                            "description": "Clear description of how they'll know the project is successful, including measurable outcomes and personal satisfaction indicators"
                        }
                    },
                    "required": ["user_id", "project_name", "project_type", "description", 
                               "goals", "challenges", "success_metrics"]
                }
            }
        ]

    # Tool method implementations
    async def tool_get_project_progress(self, user_id: str) -> Dict[str, Any]:
        return await self.db_tools.get_project_progress(user_id)

    async def tool_save_project_topic(self, user_id: str, topic_number: int,
                                    topic_name: str, response_text: str) -> Dict[str, Any]:
        return await self.db_tools.save_project_topic(
            user_id, topic_number, topic_name, response_text
        )

    async def tool_complete_project_overview(self, user_id: str, project_name: str,
                                           project_type: str, description: str, goals: Dict[str, Any],
                                           challenges: Dict[str, Any], success_metrics: str) -> Dict[str, Any]:
        return await self.db_tools.complete_project_overview(
            user_id, project_name, project_type, description, goals, challenges, success_metrics
        )
```

## 6. Agent Factory & Router (Production Ready)

```python
# src/agents/__init__.py
from .creativity_test_agent import CreativityTestAgent  
from .project_overview_agent import ProjectOverviewAgent
from .base_agent import BaseAgent
from supabase import create_client, Client
import os
import logging

logger = logging.getLogger(__name__)

class AgentFactory:
    """
    Factory for creating properly configured agent instances.
    
    Handles Supabase client creation and dependency injection
    following production best practices.
    """
    
    def __init__(self):
        # Initialize Supabase client
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_KEY')
        
        if not supabase_url or not supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY environment variables required")
            
        self.supabase_client = create_client(supabase_url, supabase_key)

    def create_creativity_test_agent(self) -> CreativityTestAgent:
        """Create a properly configured creativity test agent."""
        from .database_tools import DatabaseTools
        db_tools = DatabaseTools(self.supabase_client)
        return CreativityTestAgent(db_tools)
    
    def create_project_overview_agent(self) -> ProjectOverviewAgent:
        """Create a properly configured project overview agent."""
        from .database_tools import DatabaseTools
        db_tools = DatabaseTools(self.supabase_client)
        return ProjectOverviewAgent(db_tools)

async def route_message(user_id: str, message: str, factory: AgentFactory) -> tuple[str, str]:
    """
    Route user message to appropriate agent based on context and state.
    
    Returns:
        tuple: (response_message, agent_used)
    """
    try:
        # Check for incomplete creativity test (highest priority)
        creativity_agent = factory.create_creativity_test_agent()
        creativity_progress = await creativity_agent.db_tools.get_creativity_progress(user_id)
        
        if creativity_progress['exists'] and not creativity_progress['is_complete']:
            logger.info(f"Routing to creativity agent - progress: {creativity_progress['progress_percentage']}%")
            response = await creativity_agent.process_message(user_id, message)
            return response, "creativity_test"
        
        # Check for incomplete project overview (second priority)
        project_agent = factory.create_project_overview_agent() 
        project_progress = await project_agent.db_tools.get_project_progress(user_id)
        
        if project_progress['exists'] and not project_progress['is_complete']:
            logger.info(f"Routing to project agent - progress: {project_progress['progress_percentage']}%")
            response = await project_agent.process_message(user_id, message)
            return response, "project_overview"
        
        # Route based on message intent
        message_lower = message.lower()
        creativity_keywords = ['creativity', 'creative', 'test', 'assessment', 'archetype', 'type']
        project_keywords = ['project', 'planning', 'plan', 'overview', 'goal', 'goals']
        
        if any(word in message_lower for word in creativity_keywords):
            logger.info("Routing to creativity agent - keyword match")
            response = await creativity_agent.process_message(user_id, message)
            return response, "creativity_test"
            
        elif any(word in message_lower for word in project_keywords):
            logger.info("Routing to project agent - keyword match")
            response = await project_agent.process_message(user_id, message)
            return response, "project_overview"
        
        # Default to project planning for new users (aligns with your business model)
        logger.info("Routing to project agent - default for new user")
        response = await project_agent.process_message(user_id, message)
        return response, "project_overview"
        
    except Exception as e:
        logger.error(f"Error in message routing: {e}")
        
        # Fallback to LLM router for error recovery
        try:
            from src.llm_router import get_router
            router = await get_router()
            
            fallback_response = await router.send_message(
                messages=[{"role": "user", "content": message}],
                system="You are a helpful AI assistant. The user was trying to use a specialized agent, but there was a technical issue. Please provide a helpful response.",
                stream=False
            )
            
            return fallback_response, "fallback"
            
        except Exception as fallback_error:
            logger.error(f"Fallback routing also failed: {fallback_error}")
            return "I apologize, but I'm experiencing technical difficulties. Please try again in a moment.", "error"
```

## 7. FastAPI Integration (Production Endpoints)

```python
# Example integration with your existing FastAPI app
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class AgentMessageRequest(BaseModel):
    user_id: str = Field(..., description="User identifier")
    message: str = Field(..., description="User's message")
    agent_type: Optional[str] = Field(None, description="Specific agent to use (creativity/project/auto)")

class AgentMessageResponse(BaseModel):
    response: str = Field(..., description="Agent's response")
    agent_used: str = Field(..., description="Which agent processed the message")
    llm_provider: Optional[str] = Field(None, description="LLM provider used (anthropic/openai)")
    progress_info: Optional[Dict[str, Any]] = Field(None, description="Current progress if applicable")

class ProgressResponse(BaseModel):
    creativity_test: Dict[str, Any] = Field(..., description="Creativity test progress")
    project_overview: Dict[str, Any] = Field(..., description="Project overview progress")

# Initialize agent factory (singleton pattern)
_agent_factory = None

def get_agent_factory() -> AgentFactory:
    global _agent_factory
    if _agent_factory is None:
        _agent_factory = AgentFactory()
    return _agent_factory

@app.post("/agents/chat", response_model=AgentMessageResponse)
async def chat_with_agent(
    request: AgentMessageRequest,
    factory: AgentFactory = Depends(get_agent_factory)
):
    """
    Send message to appropriate agent with automatic routing.
    
    Provides intelligent routing based on user context and message content,
    with fallback protection and comprehensive error handling.
    """
    try:
        if request.agent_type == "creativity":
            agent = factory.create_creativity_test_agent()
            response = await agent.process_message(request.user_id, request.message)
            agent_used = "creativity_test"
            
        elif request.agent_type == "project":
            agent = factory.create_project_overview_agent()
            response = await agent.process_message(request.user_id, request.message)
            agent_used = "project_overview"
            
        else:
            # Auto-route based on context
            response, agent_used = await route_message(request.user_id, request.message, factory)
        
        # Get LLM provider info if available
        llm_provider = None
        try:
            from src.llm_router import get_router
            router = await get_router()
            llm_provider = router.get_last_provider()
        except:
            pass  # Router info is optional
        
        # Get current progress for frontend
        progress_info = None
        try:
            if agent_used == "creativity_test":
                agent = factory.create_creativity_test_agent()
                progress_info = await agent.db_tools.get_creativity_progress(request.user_id)
            elif agent_used == "project_overview":
                agent = factory.create_project_overview_agent()
                progress_info = await agent.db_tools.get_project_progress(request.user_id)
        except:
            pass  # Progress info is optional
            
        return AgentMessageResponse(
            response=response,
            agent_used=agent_used,
            llm_provider=llm_provider,
            progress_info=progress_info
        )
        
    except Exception as e:
        logger.error(f"Error in agent chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Agent processing failed: {str(e)}")

@app.get("/agents/progress/{user_id}", response_model=ProgressResponse)
async def get_user_progress(
    user_id: str,
    factory: AgentFactory = Depends(get_agent_factory)
):
    """Get user's progress across all agent flows."""
    try:
        creativity_agent = factory.create_creativity_test_agent()
        project_agent = factory.create_project_overview_agent()
        
        creativity_progress = await creativity_agent.db_tools.get_creativity_progress(user_id)
        project_progress = await project_agent.db_tools.get_project_progress(user_id)
        
        return ProgressResponse(
            creativity_test=creativity_progress,
            project_overview=project_progress
        )
        
    except Exception as e:
        logger.error(f"Error getting user progress: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get progress: {str(e)}")

@app.post("/agents/reset-progress/{user_id}")
async def reset_user_progress(
    user_id: str,
    agent_type: str,  # "creativity" or "project"
    factory: AgentFactory = Depends(get_agent_factory)
):
    """Reset user's progress in specific agent flow (for testing/debugging)."""
    try:
        if agent_type == "creativity":
            # Delete from progress table (keeps final results)
            factory.supabase_client.table('creativity_test_progress').delete().eq('user_id', user_id).execute()
            return {"message": "Creativity test progress reset"}
            
        elif agent_type == "project":
            factory.supabase_client.table('project_overview_progress').delete().eq('user_id', user_id).execute()
            return {"message": "Project overview progress reset"}
            
        else:
            raise HTTPException(status_code=400, detail="agent_type must be 'creativity' or 'project'")
            
    except Exception as e:
        logger.error(f"Error resetting progress: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to reset progress: {str(e)}")

@app.get("/agents/usage-stats")
async def get_agent_usage_stats():
    """Get LLM usage statistics for monitoring."""
    try:
        from src.llm_router import get_llm_usage_stats
        stats = await get_llm_usage_stats()
        return stats
    except Exception as e:
        logger.error(f"Error getting usage stats: {e}")
        return {"error": "Usage stats unavailable"}
```

## 8. Testing Framework (Production Quality)

```python
# tests/test_agents.py
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from src.agents import CreativityTestAgent, ProjectOverviewAgent, AgentFactory
from src.tools.database_tools import DatabaseTools

@pytest.fixture
def mock_supabase_client():
    """Mock Supabase client with realistic responses."""
    client = MagicMock()
    
    # Mock table operations
    table_mock = MagicMock()
    client.table.return_value = table_mock
    
    # Chain method calls for select operations
    select_mock = MagicMock()
    table_mock.select.return_value = select_mock
    eq_mock = MagicMock()
    select_mock.eq.return_value = eq_mock
    
    # Mock execute responses
    execute_mock = MagicMock()
    eq_mock.execute.return_value = execute_mock
    
    return client

@pytest.fixture 
def mock_db_tools(mock_supabase_client):
    """Create mock database tools with realistic method responses."""
    tools = DatabaseTools(mock_supabase_client)
    
    # Mock creativity test methods
    tools.get_creativity_progress = AsyncMock(return_value={
        "exists": False,
        "current_question": 1,
        "answers": {},
        "is_complete": False,
        "progress_percentage": 0.0
    })
    
    tools.save_creativity_answer = AsyncMock(return_value={
        "success": True,
        "current_question": 1,
        "total_questions": 7,
        "answers_count": 1,
        "progress_percentage": 14.3
    })
    
    tools.complete_creativity_test = AsyncMock(return_value={
        "success": True,
        "archetype": "Explorer",
        "archetype_score": 0.85,
        "message": "Creativity test completed! You are an Explorer."
    })
    
    # Mock project overview methods
    tools.get_project_progress = AsyncMock(return_value={
        "exists": False, 
        "current_topic": 1,
        "collected_data": {},
        "is_complete": False,
        "progress_percentage": 0.0
    })
    
    tools.save_project_topic = AsyncMock(return_value={
        "success": True,
        "current_topic": 1,
        "total_topics": 8,
        "topics_completed": 1,
        "progress_percentage": 12.5
    })
    
    tools.complete_project_overview = AsyncMock(return_value={
        "success": True,
        "project_id": "test-project-123",
        "project_name": "Test Project",
        "message": "Project overview completed for 'Test Project'!"
    })
    
    return tools

@pytest.fixture
def mock_anthropic_client():
    """Mock Anthropic client for agent testing."""
    with patch('anthropic.AsyncAnthropic') as mock_class:
        mock_client = AsyncMock()
        mock_class.return_value = mock_client
        
        # Mock successful response without tools
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Test response")]
        mock_response.stop_reason = "end_turn"
        mock_client.messages.create = AsyncMock(return_value=mock_response)
        
        yield mock_client

@pytest.mark.asyncio
async def test_creativity_agent_initialization(mock_db_tools):
    """Test creativity agent initializes correctly."""
    agent = CreativityTestAgent(mock_db_tools)
    
    assert agent.db_tools == mock_db_tools
    assert agent.model == "claude-3-5-sonnet-20241022"
    assert agent.max_tokens == 1500
    assert len(agent.get_tools()) == 3
    assert "creativity" in agent.get_system_prompt().lower()

@pytest.mark.asyncio
async def test_creativity_agent_tool_execution(mock_db_tools):
    """Test creativity agent tool methods execute correctly."""
    agent = CreativityTestAgent(mock_db_tools)
    
    # Test get_creativity_progress tool
    result = await agent.tool_get_creativity_progress("test_user")
    assert result["exists"] is False
    assert result["progress_percentage"] == 0.0
    mock_db_tools.get_creativity_progress.assert_called_once_with("test_user")
    
    # Test save_creativity_answer tool
    result = await agent.tool_save_creativity_answer(
        "test_user", 1, "When are you most creative?", "In the morning"
    )
    assert result["success"] is True
    assert result["current_question"] == 1
    mock_db_tools.save_creativity_answer.assert_called_once()

@pytest.mark.asyncio
async def test_project_agent_initialization(mock_db_tools):
    """Test project agent initializes correctly."""
    agent = ProjectOverviewAgent(mock_db_tools)
    
    assert agent.db_tools == mock_db_tools
    assert agent.model == "claude-3-5-sonnet-20241022"
    assert agent.max_tokens == 2000
    assert len(agent.get_tools()) == 3
    assert "project" in agent.get_system_prompt().lower()

@pytest.mark.asyncio
async def test_project_agent_complete_flow(mock_db_tools):
    """Test project agent complete workflow."""
    agent = ProjectOverviewAgent(mock_db_tools)
    
    # Test completion tool
    result = await agent.tool_complete_project_overview(
        user_id="test_user",
        project_name="Test Project",
        project_type="writing",
        description="A test project", 
        goals={"goal1": "Complete first draft"},
        challenges={"challenge1": "Time management"},
        success_metrics="Finished product with positive feedback"
    )
    
    assert result["success"] is True
    assert "project_id" in result
    mock_db_tools.complete_project_overview.assert_called_once()

@pytest.mark.asyncio 
async def test_agent_error_handling(mock_db_tools):
    """Test agent error handling when tools fail."""
    agent = CreativityTestAgent(mock_db_tools)
    
    # Mock tool failure
    mock_db_tools.get_creativity_progress.side_effect = Exception("Database error")
    
    result = await agent.handle_tool_call("get_creativity_progress", {"user_id": "test_user"})
    assert result["success"] is False
    assert "error" in result

@pytest.mark.asyncio
async def test_agent_factory():
    """Test agent factory creates agents correctly."""
    with patch.dict('os.environ', {
        'SUPABASE_URL': 'https://test.supabase.co',
        'SUPABASE_KEY': 'test-key'
    }):
        with patch('supabase.create_client') as mock_create:
            mock_client = MagicMock()
            mock_create.return_value = mock_client
            
            factory = AgentFactory()
            
            creativity_agent = factory.create_creativity_test_agent()
            assert isinstance(creativity_agent, CreativityTestAgent)
            
            project_agent = factory.create_project_overview_agent()
            assert isinstance(project_agent, ProjectOverviewAgent)

@pytest.mark.asyncio
async def test_message_routing():
    """Test message routing logic."""
    from src.agents import route_message
    
    mock_factory = MagicMock()
    mock_creativity_agent = MagicMock()
    mock_project_agent = MagicMock()
    
    mock_factory.create_creativity_test_agent.return_value = mock_creativity_agent
    mock_factory.create_project_overview_agent.return_value = mock_project_agent
    
    # Mock progress responses
    mock_creativity_agent.db_tools.get_creativity_progress = AsyncMock(return_value={
        "exists": False, "is_complete": False
    })
    mock_project_agent.db_tools.get_project_progress = AsyncMock(return_value={
        "exists": False, "is_complete": False  
    })
    
    # Mock process_message responses
    mock_project_agent.process_message = AsyncMock(return_value="Project response")
    
    # Test default routing (should go to project)
    response, agent_used = await route_message("test_user", "Hello", mock_factory)
    assert agent_used == "project_overview"
    assert response == "Project response"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

## 9. Environment & Deployment

```bash
# .env (updated for production)
# Your existing Supabase configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_anon_key

# LLM Router configuration (already in your system)
ANTHROPIC_API_KEY=your_anthropic_key
OPENAI_API_KEY=your_openai_key_for_fallback

# Agent-specific configuration
AGENT_LOG_LEVEL=INFO
AGENT_MAX_RETRIES=3
AGENT_TIMEOUT_SECONDS=30

# Production settings
ENVIRONMENT=production
ENABLE_AGENT_MONITORING=true
```

```python
# requirements.txt (additions to your existing)
# Core dependencies (you already have most)
anthropic>=0.39.0
supabase>=2.0.0
fastapi>=0.104.0
uvicorn>=0.24.0
python-dotenv>=1.0.0

# Testing dependencies  
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-mock>=3.12.0

# Production monitoring
structlog>=23.2.0  # Better logging
```

## 10. Integration Steps

```bash
# 1. Add database tables to your Supabase
# Run this SQL in your Supabase dashboard SQL editor:

CREATE TABLE creativity_test_progress (
    user_id UUID PRIMARY KEY REFERENCES creator_profiles(id) ON DELETE CASCADE,
    current_question INTEGER NOT NULL CHECK (current_question >= 1 AND current_question <= 7),
    answers JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE project_overview_progress (
    user_id UUID PRIMARY KEY REFERENCES creator_profiles(id) ON DELETE CASCADE,
    current_topic INTEGER NOT NULL CHECK (current_topic >= 1 AND current_topic <= 8),
    collected_data JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_creativity_progress_updated ON creativity_test_progress(updated_at);
CREATE INDEX idx_project_progress_updated ON project_overview_progress(updated_at);

# 2. Add agent files to your project
mkdir -p src/agents src/tools
# Copy all the Python files from sections 2-6

# 3. Add agent endpoints to your FastAPI app
# Integrate the code from section 7 into your src/main.py

# 4. Test the integration
curl -X POST "http://localhost:8000/agents/chat" \
     -H "Content-Type: application/json" \
     -d '{"user_id": "test-user-123", "message": "I want to take the creativity test"}'

# 5. Test progress tracking
curl "http://localhost:8000/agents/progress/test-user-123"

# 6. Run tests
pytest tests/test_agents.py -v
```

## Summary

This implementation provides:

✅ **Perfect Adherence to Best Practices**
- Detailed tool descriptions (3-4+ sentences each)
- XML-structured prompts for optimal Claude performance
- Simple, composable architecture without over-engineering
- External state persistence with clean resumption
- Type hints for validation without Pydantic overhead

✅ **Production-Ready Architecture** 
- Direct Anthropic client for reliable tool calling
- Integration with your LLM router for fallback protection
- Comprehensive error handling and logging
- Proper async/await patterns throughout

✅ **Seamless Integration**
- Uses your existing Supabase schema
- Minimal additions (just 2 progress tables)
- Works with your LLM router system
- Preserves your authentication flow

✅ **Robust Agent Design**
- Mid-flow state persistence with resumption
- Structured data collection for future dashboards
- Tool choice control and proper schemas
- Comprehensive testing framework

The agents follow the augmented LLM pattern exactly as recommended by Anthropic, provide reliable tool calling with your existing infrastructure, and deliver the creativity test + project overview functionality you discussed.

