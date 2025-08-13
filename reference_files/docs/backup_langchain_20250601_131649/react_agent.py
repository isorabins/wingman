# agent.py

import os
import logging
from typing import Dict, Any
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, BaseMessage, SystemMessage, AIMessage
from langchain_core.prompts import ChatMessagePromptTemplate
from langsmith.run_helpers import traceable
from src.sql_tools import get_all_tools
from langgraph.prebuilt import create_react_agent 
from datetime import datetime
#from prompts import MAIN_PROMPT, ONBOARDING_PROMPT
#from langchain_anthropic import ChatAnthropic
from src.config import Config
from datetime import timezone
from datetime import datetime
from src.simple_memory import SimpleMemory
import json
from src.prompts import main_prompt

# Import project planning functionality
from src.project_planning import (
    check_user_has_project_overview,
    should_trigger_project_planning,
    get_project_planning_prompt,
    monitor_conversation_for_project_completion,
    analyze_project_conversation
)
from src.onboarding_manager import OnboardingManager

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Singleton pattern for agent instance
_agent_instance = None

async def check_and_handle_project_onboarding(supabase_client, user_id: str, user_input: str) -> Dict[str, Any]:
    """
    Check if user needs project onboarding and return appropriate response.
    
    Args:
        supabase_client: Supabase client instance
        user_id: User ID to check
        user_input: Current user input to analyze
        
    Returns:
        dict: Contains should_onboard flag and prompt if needed
    """
    try:
        # Check if onboarding is enabled (can be disabled via feature flag)
        if not Config.ENABLE_ONBOARDING:
            logger.info(f"[{Config.get_app_identifier()}] Onboarding disabled via feature flag")
            return {"should_onboard": False, "prompt": None}
        
        # Check if user has project overview using the new signature
        should_onboard = await should_trigger_project_planning(supabase_client, user_id)
        
        if should_onboard:
            # Enhanced logging for development
            if Config.ENABLE_DETAILED_LOGGING:
                logger.info(f"[{Config.get_app_identifier()}] Triggering onboarding for user {user_id}")
            
            # User doesn't have project - automatically trigger onboarding
            return {
                "should_onboard": True, 
                "prompt": get_project_planning_prompt()
            }
        else:
            # User already has project, no onboarding needed
            return {"should_onboard": False, "prompt": None}
        
    except Exception as e:
        logger.error(f"Error checking project onboarding for user {user_id}: {str(e)}")
        return {"should_onboard": False, "prompt": None}

async def handle_completed_project_conversation(supabase_client, user_id: str, conversation: list) -> Dict[str, Any]:
    """
    Handle a completed project planning conversation by creating project overview.
    
    Args:
        supabase_client: Supabase client instance
        user_id: User ID
        conversation: Full conversation history
        
    Returns:
        dict: Contains project_created flag and project_id if successful
    """
    try:
        # Analyze the conversation to extract project data
        analysis = await analyze_project_conversation(conversation)
        
        # Create project overview using OnboardingManager
        onboarding_manager = OnboardingManager(supabase_client)
        
        project_id = await onboarding_manager.create_project_overview(
            user_id=user_id,
            project_name=analysis["project_name"],
            project_type=analysis["project_type"],
            description=analysis["description"],
            goals=analysis["goals"],
            challenges=analysis["challenges"],
            success_metrics=analysis["success_metrics"]
        )
        
        if project_id:
            logger.info(f"Created project overview {project_id} for user {user_id}")
            return {"project_created": True, "project_id": project_id}
        else:
            logger.error(f"Failed to create project overview for user {user_id}")
            return {"project_created": False, "project_id": None}
            
    except Exception as e:
        logger.error(f"Error handling completed project conversation for user {user_id}: {str(e)}")
        return {"project_created": False, "project_id": None}

@traceable(run_type="chain", name="create_agent")
def create_agent():
    """
    Create a single agent with tools (no memory - using SimpleMemory instead)
    """
    try:
        logger.info("Initializing agent with tools")
        
        model = ChatAnthropic(
            model=Config.ANTHROPIC_MODEL,
            temperature=0.5,
            anthropic_api_key=Config.ANTHROPIC_API_KEY
        )
        #Get chat-specific tools
        tools = get_all_tools()
        
        # Create the agent without memory
        agent = create_react_agent(
            model=model,
            tools=tools
        )
        
        logger.info("Agent initialized successfully")
        return agent
        
    except Exception as e:
        logger.error(f"Error creating agent: {e}")
        raise

def get_agent_instance():
    """
    Get or create the agent instance (singleton pattern)
    """
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = create_agent()
    return _agent_instance

@traceable(run_type="chain")
async def interact_with_agent(
    user_input: str, 
    user_id: str, 
    user_timezone: str,
    thread_id: str,
    supabase_client,
    context: Dict[str, Any]
):
    """Process user input using LangChain agent with project onboarding integration"""
    try:
        logger.info(f"Processing input for user {user_id}")
        logger.info(f"\n{'='*50}\nNEW INTERACTION\n{'='*50}")
        logger.info(f"User Input: {user_input}")
        logger.info(f"User ID: {user_id}")
        logger.info(f"Thread ID: {thread_id}")
        
        # Get memory context
        memory = SimpleMemory(supabase_client, user_id)
        memory_context = await memory.get_context(thread_id)
        logger.info(f"[MEMORY DEBUG] Full memory context retrieved: {json.dumps(memory_context, indent=2)}")
        
        # === PROJECT ONBOARDING INTEGRATION ===
        
        # Check if user needs project onboarding  
        onboarding_check = await check_and_handle_project_onboarding(supabase_client, user_id, user_input)
        
        # Check if user is in the middle of project planning and conversation is complete
        if not onboarding_check["should_onboard"]:
            # User has project overview - check if they might be completing an ongoing conversation
            # (This handles edge case where user had conversation before we added project overview)
            has_project = await check_user_has_project_overview(supabase_client, user_id)
            
            if not has_project and memory_context["messages"]:
                # User doesn't have project but has conversation history
                # Check if the conversation is complete enough to create project overview
                full_conversation = memory_context["messages"] + [{"role": "user", "content": user_input}]
                
                if await monitor_conversation_for_project_completion(supabase_client, user_id, full_conversation):
                    logger.info(f"Project conversation appears complete for user {user_id}, creating project overview")
                    
                    creation_result = await handle_completed_project_conversation(
                        supabase_client, user_id, full_conversation
                    )
                    
                    if creation_result["project_created"]:
                        # Add a system message about project creation
                        project_creation_message = (
                            f"Perfect! I've successfully created your project overview based on our conversation. "
                            f"Your project details have been saved and I can now help you work on your project more effectively. "
                            f"What would you like to focus on next?"
                        )
                        
                        # Return the project creation message directly
                        return project_creation_message

        # Start with system context including timezone info
        chat_messages = [
            SystemMessage(content=f"""User ID: {user_id}
            User timezone: {user_timezone}
            Current Time: {datetime.now(timezone.utc)}
            Thread: {thread_id}"""),
            SystemMessage(content=main_prompt)
        ]
        
        # Add project onboarding prompt if needed
        if onboarding_check["should_onboard"]:
            logger.info(f"Adding project onboarding prompt for user {user_id}")
            chat_messages.append(SystemMessage(
                content=f"IMPORTANT: This user doesn't have a project overview yet and seems interested in project work. "
                f"Guide them through this comprehensive project planning process:\n\n{onboarding_check['prompt']}"
            ))
        
        logger.info(f"[MEMORY DEBUG] Chat messages being sent to agent: {json.dumps(chat_messages, default=str, indent=2)}")
        
        # Add memory summaries as additional system context
        if memory_context["summaries"]:
            chat_messages.append(SystemMessage(
                content="Previous Context:\n" + "\n".join(memory_context["summaries"])
            ))
            
        # Add conversation history, but exclude any message that matches the current input
        # to avoid duplication
        messages_to_include = []
        duplicate_found = False
        
        for msg in memory_context["messages"]:
            # If this message matches the current input, mark it as a duplicate but don't include it
            if msg["content"] == user_input:
                logger.info(f"[DEBUG] Found duplicate message in context matching current input: {user_input[:50]}...")
                duplicate_found = True
                continue
            messages_to_include.append(msg)
        
        if duplicate_found:
            logger.info(f"[DEBUG] Excluded duplicate message from context")
            
        for msg in messages_to_include:
            if msg["role"] == "assistant":
                chat_messages.append(AIMessage(content=msg["content"]))
            elif msg["role"] == "user":
                chat_messages.append(HumanMessage(content=msg["content"]))
        
        # Log the final message list being sent to the AI
        logger.info(f"[DEBUG] Final message list being sent to AI:")
        for i, msg in enumerate(chat_messages):
            logger.info(f"[DEBUG] AI Message {i+1}: Type={type(msg).__name__}, Content={msg.content[:50]}...")
        
        # Add current user input
        chat_messages.append(HumanMessage(content=user_input))
        logger.info(f"[DEBUG] Added current user input: {user_input[:50]}...")

        # Create agent and invoke
        agent = create_agent()
        response = await agent.ainvoke({
            "messages": chat_messages,
            "input": user_input,
            "context": {
                "thread_id": thread_id,
                "user_id": user_id,
                "timezone": user_timezone,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        })
        
        response_content = response["messages"][-1].content if response.get("messages") else "Error getting response"
        
        # === POST-RESPONSE PROJECT MONITORING ===
        # Monitor conversation for project completion (after generating response)
        try:
            # Prepare conversation messages for analysis
            conversation_messages = []
            
            # Add recent conversation history
            for msg in messages_to_include[-10:]:  # Last 10 messages for context
                conversation_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
            
            # Add current exchange
            conversation_messages.append({
                "role": "user",
                "content": user_input
            })
            conversation_messages.append({
                "role": "assistant", 
                "content": response_content
            })
            
            # Check if project planning is complete and create overview if needed
            project_created = await monitor_conversation_for_project_completion(
                supabase_client, user_id, conversation_messages
            )
            
            if project_created:
                logger.info(f"🎉 Successfully created project overview for user {user_id} from conversation analysis")
            
        except Exception as e:
            logger.error(f"Error monitoring conversation for project completion: {e}")
            # Don't fail the main response if monitoring fails
        
        logger.info(f"Generated response for user {user_id}")
        return response_content
        
    except Exception as e:
        logger.error(f"Agent interaction failed: {str(e)}", exc_info=True)
        return f"Error processing your request: {str(e)}"


@traceable(run_type="chain")
async def interact_with_agent_stream(
    user_input: str, 
    user_id: str, 
    user_timezone: str,
    thread_id: str,
    supabase_client,
    context: Dict[str, Any]
):
    """Process user input using LangChain agent with streaming support"""
    try:
        logger.info(f"Processing streaming input for user {user_id}")
        logger.info(f"\n{'='*50}\nNEW STREAMING INTERACTION\n{'='*50}")
        logger.info(f"User Input: {user_input}")
        logger.info(f"User ID: {user_id}")
        logger.info(f"Thread ID: {thread_id}")
        
        # Get memory context
        memory = SimpleMemory(supabase_client, user_id)
        memory_context = await memory.get_context(thread_id)
        logger.info(f"[MEMORY DEBUG] Full memory context retrieved: {json.dumps(memory_context, indent=2)}")
        
        # Start with system context including timezone info
        chat_messages = [
            SystemMessage(content=f"""User ID: {user_id}
            User timezone: {user_timezone}
            Current Time: {datetime.now(timezone.utc)}
            Thread: {thread_id}"""),
            SystemMessage(content=main_prompt)
        ]
        logger.info(f"[MEMORY DEBUG] Chat messages being sent to agent: {json.dumps(chat_messages, default=str, indent=2)}")
        
        # Add memory summaries as additional system context
        if memory_context["summaries"]:
            chat_messages.append(SystemMessage(
                content="Previous Context:\n" + "\n".join(memory_context["summaries"])
            ))
            
        # Add conversation history, but exclude any message that matches the current input
        # to avoid duplication
        messages_to_include = []
        duplicate_found = False
        
        for msg in memory_context["messages"]:
            # If this message matches the current input, mark it as a duplicate but don't include it
            if msg["content"] == user_input:
                logger.info(f"[DEBUG] Found duplicate message in context matching current input: {user_input[:50]}...")
                duplicate_found = True
                continue
            messages_to_include.append(msg)
        
        if duplicate_found:
            logger.info(f"[DEBUG] Excluded duplicate message from context")
            
        for msg in messages_to_include:
            if msg["role"] == "assistant":
                chat_messages.append(AIMessage(content=msg["content"]))
            elif msg["role"] == "user":
                chat_messages.append(HumanMessage(content=msg["content"]))
        
        # Log the final message list being sent to the AI
        logger.info(f"[DEBUG] Final message list being sent to AI:")
        for i, msg in enumerate(chat_messages):
            logger.info(f"[DEBUG] AI Message {i+1}: Type={type(msg).__name__}, Content={msg.content[:50]}...")
        
        # Add current user input
        chat_messages.append(HumanMessage(content=user_input))
        logger.info(f"[DEBUG] Added current user input: {user_input[:50]}...")

        # Create agent
        agent = create_agent()
        
        # Return the streaming generator instead of awaiting the response
        return agent.astream({
            "messages": chat_messages,
            "input": user_input,
            "context": {
                "thread_id": thread_id,
                "user_id": user_id,
                "timezone": user_timezone,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Agent streaming interaction failed: {str(e)}", exc_info=True)
        raise