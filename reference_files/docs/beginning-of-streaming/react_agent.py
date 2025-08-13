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
    """Process user input using LangChain agent"""
    try:
        logger.info(f"Processing input for user {user_id}")
        logger.info(f"\n{'='*50}\nNEW INTERACTION\n{'='*50}")
        logger.info(f"User Input: {user_input}")
        logger.info(f"User ID: {user_id}")
        logger.info(f"Thread ID: {thread_id}")
        
        # Get memory context
        memory = SimpleMemory(supabase_client, user_id)
        memory_context = await memory.get_context(thread_id)
        # In react_agent.py, in the interact_with_agent function, right after getting memory context:
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
        
        logger.info(f"Generated response for user {user_id}")
        return response["messages"][-1].content if response.get("messages") else "Error getting response"
        
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