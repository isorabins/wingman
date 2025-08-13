#!/usr/bin/env python3
"""
Project Planning Module

Handles automatic project planning and onboarding for new users.
Detects users without project overviews and guides them through
comprehensive project planning conversations.
"""

import logging
import json
import re
from typing import Dict, List, Optional, Any
from supabase import Client
from datetime import datetime
from supabase import create_client

# Import our simple Claude client instead of LangChain
from src.claude_client_simple import SimpleClaudeClient, ClaudeCredentials
from src.config import Config
from src.simple_memory import SimpleMemory

logger = logging.getLogger(__name__)

async def check_user_has_project_overview(supabase_client: Client, user_id: str) -> bool:
    """
    Check if a user has an existing project overview.
    
    Args:
        supabase_client: Supabase client instance
        user_id: User ID to check
        
    Returns:
        bool: True if user has project overview, False otherwise
    """
    try:
        result = supabase_client.table('project_overview')\
            .select('id')\
            .eq('user_id', user_id)\
            .execute()
        
        return len(result.data) > 0
        
    except Exception as e:
        logger.error(f"Error checking user project overview: {str(e)}")
        return False

def get_project_planning_prompt() -> str:
    """
    Get the project planning prompt with progress tracking and clear completion flow
    """
    return """You should respond to the user with this onboarding flow:

START YOUR RESPONSE WITH:
"Hi! I see you haven't added a project yet. To work best with me, the first step is to set up your project so I can save it in my memory and it'll always be there for our conversations.

This quick setup takes about 10 minutes and helps me:
- Remember your goals and priorities
- Track your progress over time  
- Give you more personalized support
- Keep our conversations focused on what matters to you

I have 8 key topics to cover with you - I'll let you know our progress as we go so you can see how much we have left.

Let's start with Topic 1 of 8: Project Description. Could you tell me about your project - what are you looking to create or accomplish?"

THEN GUIDE THEM THROUGH THESE 8 TOPICS:

Topic 1 of 8: Project Description
- Ask them to describe their project
- Ask 1-2 specific follow-up questions for clarification

Topic 2 of 8: Goals and Success  
- Ask about main goals and what success looks like
- Follow up about specific metrics or milestones

Topic 3 of 8: Timeline
- Discuss target completion date, weekly time commitment, key milestones

Topic 4 of 8: Current Progress
- Ask about current progress and what's working well

Topic 5 of 8: Required Resources
- Ask what they'll need: software, equipment, skills, support, tools

Topic 6 of 8: Potential Roadblocks
- Explore challenges: personal, resource limitations, dependencies, time constraints

Topic 7 of 8: Motivation and Momentum
- Ask about motivation and what keeps them excited
- Follow up about maintaining momentum strategies

Topic 8 of 8: Weekly Check-ins
- Ask about preference for weekly check-ins and accountability
- IMPORTANT: Say "You'll help me remember to schedule these manually - you'll need to set up any video calls yourself"

COMPLETION:
When all 8 topics are covered, say:
"Perfect! We've covered all 8 topics. Let me create your comprehensive project overview now."

Then say:
"Excellent! Your project overview has been saved and I'll remember all these details for our future conversations. What would you like to focus on next?"

IMPORTANT: Always indicate progress like "Great! That's topic 1 of 8 complete. Now let's move to topic 2 of 8..." so they know where they are."""

async def analyze_conversation_for_project_info(conversation_messages: List[Dict[str, str]]) -> Optional[Dict[str, Any]]:
    """
    Analyze a conversation to extract project planning information using AI.
    
    Args:
        conversation_messages: List of conversation messages with 'role' and 'content' keys
        
    Returns:
        Optional[Dict]: Extracted project information or None if analysis fails
    """
    try:
        # Create the conversation text
        conversation_text = "\n".join([
            f"{msg['role'].upper()}: {msg['content']}" 
            for msg in conversation_messages
        ])
        
        # Create the analysis prompt
        analysis_prompt = f"""
Analyze this project planning conversation and extract structured project information. 
The conversation should contain information about a creative project that someone wants to work on.

Extract the following information in JSON format:
{{
    "project_name": "Clear, descriptive project title",
    "project_type": "Type of project (writing, music, art, business, etc.)",
    "description": "Detailed project description",
    "current_phase": "Current project phase (planning, in-progress, etc.)",
    "goals": [
        {{"goal": "Specific goal description", "timeline": "When they want to achieve it"}},
        {{"goal": "Another goal", "timeline": "Timeline for this goal"}}
    ],
    "challenges": [
        {{"challenge": "Specific challenge or roadblock", "mitigation": "How they plan to address it"}},
        {{"challenge": "Another challenge", "mitigation": "Mitigation strategy"}}
    ],
    "success_metrics": {{
        "primary_metric": "Main way to measure success",
        "target_completion": "Target completion date or milestone",
        "weekly_commitment": "Hours per week they plan to work",
        "zoom_availability": "Their availability for weekly calls"
    }}
}}

Guidelines:
- Extract only information that is explicitly mentioned or clearly implied
- Use the person's own words when possible
- If information is missing, use reasonable defaults or null
- Focus on actionable, specific information
- Ensure the project_name is engaging and descriptive

Conversation to analyze:
{conversation_text}

Return only the JSON object, no additional text.
"""

        # Use our simple Claude client instead of LangChain
        claude_client = SimpleClaudeClient(
            credentials=ClaudeCredentials()
        )
        
        # Build messages for Claude API
        messages = [
            {"role": "user", "content": f"[SYSTEM CONTEXT]\nYou are an expert at analyzing conversations and extracting structured project information.\n\n[END SYSTEM CONTEXT]\n\n{analysis_prompt}"}
        ]
        
        # Get the analysis
        response = await claude_client.send_message(
            messages=messages,
            model="claude-3-5-sonnet-20241022",
            max_tokens=4000,
            temperature=0.1,
            stream=False
        )
        
        # Parse the JSON response
        try:
            project_info = json.loads(response.strip())
            return project_info
        except json.JSONDecodeError:
            # Try to extract JSON from the response if it's wrapped in other text
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                project_info = json.loads(json_match.group())
                return project_info
            else:
                logger.error(f"Failed to parse JSON from AI response: {response}")
                return None
                
    except Exception as e:
        logger.error(f"Error analyzing conversation for project info: {e}")
        return None

async def create_project_overview_from_conversation(
    supabase_client, 
    user_id: str, 
    conversation_data: Dict[str, Any]
) -> bool:
    """
    Create a project overview entry in the database from conversation data.
    
    Args:
        supabase_client: Supabase client instance
        user_id: The user's ID (must be a valid creator profile ID)
        conversation_data: Dictionary containing project planning conversation results
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        from datetime import datetime, timezone
        
        # Ensure creator profile exists before creating project overview
        memory = SimpleMemory(supabase_client, user_id)
        await memory.ensure_creator_profile(user_id)
        
        # Map conversation data to database schema
        project_data = {
            "user_id": user_id,
            "project_name": conversation_data.get("project_name", "Untitled Project"),
            "project_type": conversation_data.get("project_type", "creative"),
            "description": conversation_data.get("description", ""),
            "current_phase": conversation_data.get("current_phase", "planning"),
            "goals": conversation_data.get("goals", []),
            "challenges": conversation_data.get("challenges", []),
            "success_metrics": conversation_data.get("success_metrics", {}),
            "creation_date": datetime.now(timezone.utc).isoformat(),
            "last_updated": datetime.now(timezone.utc).isoformat()
        }
        
        response = supabase_client.table("project_overview").insert(project_data).execute()
        
        if len(response.data) > 0:
            logger.info(f"✅ Successfully created project overview for user {user_id}: {project_data['project_name']}")
            return True
        else:
            logger.error(f"❌ Failed to create project overview - no data returned")
            return False
        
    except Exception as e:
        logger.error(f"Error creating project overview for user {user_id}: {e}")
        # If it's a foreign key constraint error, it means the user doesn't have a creator profile
        if "23503" in str(e) or "foreign key constraint" in str(e).lower():
            logger.error(f"⚠️ User {user_id} doesn't have a creator profile. They need to sign in first.")
        return False

async def monitor_conversation_for_project_completion(
    supabase_client,
    user_id: str,
    conversation_messages: List[Dict[str, str]]
) -> bool:
    """
    Monitor a conversation to detect when project planning is complete and automatically
    create the project overview.
    
    Args:
        supabase_client: Supabase client instance
        user_id: The user's ID
        conversation_messages: Recent conversation messages
        
    Returns:
        bool: True if project overview was created, False otherwise
    """
    try:
        # Check if user already has a project overview
        if await check_user_has_project_overview(supabase_client, user_id):
            return False  # User already has a project
        
        # Look for specific completion indicators from the updated prompt
        conversation_text = " ".join([msg.get('content', '') for msg in conversation_messages])
        
        # Check for explicit completion signals from the new prompt structure
        completion_signals = [
            "Perfect! We've covered all 8 topics",
            "comprehensive project overview",
            "project overview has been saved",
            "Topic 8 of 8",
            "all these details for our future conversations"
        ]
        
        # Check for completion signals
        has_completion_signal = any(signal.lower() in conversation_text.lower() 
                                  for signal in completion_signals)
        
        # Enhanced topic tracking for the 8-topic structure
        planning_topics = [
            # Topic 1: Project Description
            ("project description", ["describe", "project", "working on"]),
            # Topic 2: Goals and Success  
            ("goals and success", ["goals", "success", "accomplish", "achieve"]),
            # Topic 3: Timeline
            ("timeline", ["timeline", "completion", "deadline", "when"]),
            # Topic 4: Current Progress
            ("current progress", ["progress", "current", "so far", "already"]),
            # Topic 5: Required Resources
            ("required resources", ["need", "resources", "tools", "equipment"]),
            # Topic 6: Potential Roadblocks
            ("roadblocks", ["challenges", "roadblocks", "obstacles", "difficult"]),
            # Topic 7: Motivation and Momentum
            ("motivation", ["motivation", "excited", "momentum", "inspired"]),
            # Topic 8: Weekly Check-ins
            ("check-ins", ["check-in", "weekly", "accountability", "schedule"])
        ]
        
        # Count covered topics based on keyword presence
        covered_topics = 0
        for topic_name, keywords in planning_topics:
            if any(keyword.lower() in conversation_text.lower() for keyword in keywords):
                covered_topics += 1
        
        logger.info(f"🔍 Project planning analysis: {covered_topics}/8 topics covered, completion signal: {has_completion_signal}")
        
        # Trigger project creation if we have completion signal OR comprehensive coverage
        should_create_project = (
            has_completion_signal or  # Explicit completion
            (covered_topics >= 7 and len(conversation_messages) >= 12)  # Comprehensive coverage
        )
        
        if should_create_project:
            logger.info(f"🎯 Triggering project creation - completion signal: {has_completion_signal}, topics: {covered_topics}/8")
            
            # Analyze the conversation for project information
            project_info = await analyze_conversation_for_project_info(conversation_messages)
            
            if project_info:
                # Create the project overview
                success = await create_project_overview_from_conversation(
                    supabase_client, user_id, project_info
                )
                
                if success:
                    logger.info(f"🎉 Successfully created project overview for user {user_id}")
                    return True
                else:
                    logger.error(f"❌ Failed to create project overview despite having project info")
            else:
                logger.warning(f"⚠️ Could not extract project information from conversation, but will retry on next interaction")
        
        return False
        
    except Exception as e:
        logger.error(f"Error monitoring conversation for project completion: {e}")
        return False

async def analyze_project_conversation(conversation: List[Dict]) -> Dict:
    """
    Analyze a project planning conversation and extract structured project data.
    
    Args:
        conversation: List of conversation messages with role and content
        
    Returns:
        dict: Structured project data including name, type, goals, challenges, etc.
    """
    try:
        # Use real AI to analyze the conversation and extract project data
        analysis = await analyze_conversation_for_project_info(conversation)
        
        if analysis is None:
            # Fallback structure if AI analysis fails
            analysis = {
                "project_name": "Unknown Project",
                "project_type": "general",
                "description": "Error extracting project description",
                "goals": [],
                "challenges": [],
                "success_metrics": {}
            }
        
        # Validate the analysis has required fields
        required_fields = ["project_name", "project_type", "description", "goals", "challenges", "success_metrics"]
        for field in required_fields:
            if field not in analysis:
                logger.warning(f"Missing required field in analysis: {field}")
                if field in ["goals", "challenges"]:
                    analysis[field] = []
                elif field == "success_metrics":
                    analysis[field] = {}
                else:
                    analysis[field] = "Not provided"
                
        return analysis
        
    except Exception as e:
        logger.error(f"Error analyzing project conversation: {str(e)}")
        return {
            "project_name": "Unknown Project",
            "project_type": "general",
            "description": "Error extracting project description",
            "goals": [],
            "challenges": [],
            "success_metrics": {}
        }

async def should_trigger_project_planning(supabase_client, user_id: str) -> bool:
    """
    Determine if we should trigger project planning for a user.
    Only triggers if user has completed creativity test but not project overview.
    
    Args:
        supabase_client: Supabase client instance
        user_id: User ID to check
        
    Returns:
        bool: True if should trigger project planning, False otherwise
    """
    try:
        # Check if user has creativity profile
        has_creativity = await check_user_has_creativity_profile(supabase_client, user_id)
        
        # Check if user has project overview  
        has_project = await check_user_has_project_overview(supabase_client, user_id)
        
        # Only trigger project planning if they have creativity profile but not project overview
        return has_creativity and not has_project
        
    except Exception as e:
        logger.error(f"Error checking if should trigger project planning: {e}")
        return False

async def should_trigger_creativity_test(supabase_client, user_id: str) -> bool:
    """
    Determine if we should trigger creativity test for a user.
    Triggers if user has neither creativity profile nor project overview.
    
    Args:
        supabase_client: Supabase client instance
        user_id: User ID to check
        
    Returns:
        bool: True if should trigger creativity test, False otherwise
    """
    try:
        # Check if user has creativity profile
        has_creativity = await check_user_has_creativity_profile(supabase_client, user_id)
        
        # Check if user has project overview
        has_project = await check_user_has_project_overview(supabase_client, user_id)
        
        # Only trigger creativity test if they have neither
        return not has_creativity and not has_project
        
    except Exception as e:
        logger.error(f"Error checking if should trigger creativity test: {e}")
        return False

def get_creativity_test_prompt() -> str:
    """
    Get the creativity test prompt that runs before project planning
    """
    return """🎨 Hi! I'm Hai, your creative partner. Before we dive into your project, I'd love to understand your creative style better.

I have a quick 5-question creativity assessment that helps me personalize our conversations. This takes about 3-5 minutes and helps me understand:
- How you approach creative challenges
- What motivates and inspires you
- How you prefer to work and make decisions
- What kind of support resonates with you

Once I understand your creative archetype, we'll move on to mapping out your specific project (that's another 8 topics, about 10 minutes).

Ready to discover your creative style?

**Question 1 of 5: Creative Approach**
When starting a new creative project, which best describes your natural approach?

A) I like to envision the big picture and overall impact first
B) I dive into research and gather lots of information before starting  
C) I start experimenting and see what emerges organically
D) I focus on the practical steps and create a clear plan
E) I think about my audience and what will resonate with them
F) I explore different possibilities and keep my options open

What feels most natural to you - A, B, C, D, E, or F?

[DEBUG: Creativity Flow v2.0 - Feature Branch]"""

def get_creativity_test_question(question_number: int) -> str:
    """
    Get specific creativity test questions
    """
    questions = {
        2: """**Question 2 of 5: Creative Inspiration**
When you're feeling stuck or need creative inspiration, what usually works best for you?

A) I step back and think about the bigger vision and purpose
B) I do more research or study examples from others
C) I take a break and let my subconscious work on it
D) I break the problem into smaller, manageable pieces
E) I talk it through with others or get feedback
F) I try a completely different approach or perspective

What resonates most - A, B, C, D, E, or F?""",
        
        3: """**Question 3 of 5: Decision Making**
When you need to make creative decisions, you tend to:

A) Trust your intuition about what feels right for the bigger picture
B) Analyze the options thoroughly before deciding
C) Go with what feels authentic and true to yourself
D) Choose the most practical and achievable option
E) Consider what others would want or find valuable
F) Keep exploring until you find something unexpected

Which feels most like you - A, B, C, D, E, or F?""",
        
        4: """**Question 4 of 5: Working Style**
Your ideal creative working environment and process involves:

A) Having a clear vision and the freedom to pursue it boldly
B) Having access to resources, tools, and knowledge
C) Having flexibility and space for spontaneous creativity
D) Having structure, deadlines, and clear milestones
E) Having collaboration and connection with others
F) Having variety and the ability to change direction

What sounds most appealing - A, B, C, D, E, or F?""",
        
        5: """**Question 5 of 5: Creative Fulfillment**
You feel most fulfilled creatively when:

A) Your work has meaningful impact and changes perspectives
B) You've mastered something challenging and complex
C) You've expressed something authentic and personal
D) You've completed something useful and well-executed
E) Your work connects with and helps others
F) You've discovered something new and innovative

Which brings you the most satisfaction - A, B, C, D, E, or F?"""
    }
    
    return questions.get(question_number, "")

def analyze_creativity_responses(responses: Dict[str, str]) -> Dict[str, Any]:
    """
    Analyze creativity test responses and determine archetype
    
    Args:
        responses: Dict with question numbers as keys and A-F responses as values
        
    Returns:
        Dict with archetype info
    """
    # Count responses for each archetype
    archetype_counts = {
        'A': 0,  # Big Picture Visionary
        'B': 0,  # Knowledge Seeker  
        'C': 0,  # Authentic Creator
        'D': 0,  # Practical Builder
        'E': 0,  # People Connector
        'F': 0   # Innovative Explorer
    }
    
    # Count responses
    for response in responses.values():
        if response.upper() in archetype_counts:
            archetype_counts[response.upper()] += 1
    
    # Determine primary archetype
    primary = max(archetype_counts, key=archetype_counts.get)
    primary_score = archetype_counts[primary]
    
    # Determine secondary archetype
    secondary_counts = {k: v for k, v in archetype_counts.items() if k != primary}
    secondary = max(secondary_counts, key=secondary_counts.get) if secondary_counts else None
    secondary_score = secondary_counts.get(secondary, 0) if secondary else 0
    
    # Map to archetype names
    archetype_map = {
        'A': 'big_picture_visionary',
        'B': 'knowledge_seeker',
        'C': 'authentic_creator', 
        'D': 'practical_builder',
        'E': 'people_connector',
        'F': 'innovative_explorer'
    }
    
    return {
        'primary_archetype': archetype_map[primary],
        'primary_score': primary_score,
        'secondary_archetype': archetype_map.get(secondary) if secondary else None,
        'secondary_score': secondary_score,
        'all_scores': archetype_counts,
        'test_responses': responses
    }

async def save_creativity_profile(supabase_client: Client, user_id: str, archetype_data: Dict[str, Any]) -> bool:
    """
    Save creativity test results to creator_creativity_profiles table
    
    Args:
        supabase_client: Supabase client instance
        user_id: User ID
        archetype_data: Results from analyze_creativity_responses
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Ensure creator profile exists first
        from src.simple_memory import SimpleMemory
        memory = SimpleMemory(supabase_client)
        await memory.ensure_creator_profile(user_id)
        
        # Insert creativity profile
        result = supabase_client.table('creator_creativity_profiles').insert({
            'user_id': user_id,
            'archetype': archetype_data['primary_archetype'],
            'archetype_score': archetype_data['primary_score'],
            'secondary_archetype': archetype_data['secondary_archetype'],
            'secondary_score': archetype_data['secondary_score'],
            'test_responses': archetype_data['test_responses']
        }).execute()
        
        logger.info(f"Saved creativity profile for user {user_id}: {archetype_data['primary_archetype']}")
        return True
        
    except Exception as e:
        logger.error(f"Error saving creativity profile: {e}")
        return False

async def check_user_has_creativity_profile(supabase_client: Client, user_id: str) -> bool:
    """
    Check if a user has completed the creativity test
    
    Args:
        supabase_client: Supabase client instance
        user_id: User ID to check
        
    Returns:
        bool: True if user has creativity profile, False otherwise
    """
    try:
        result = supabase_client.table('creator_creativity_profiles')\
            .select('id')\
            .eq('user_id', user_id)\
            .execute()
        
        return len(result.data) > 0
        
    except Exception as e:
        logger.error(f"Error checking user creativity profile: {str(e)}")
        return False

async def get_user_creativity_profile(supabase_client: Client, user_id: str) -> Optional[Dict[str, Any]]:
    """
    Get user's creativity profile for AI context
    
    Args:
        supabase_client: Supabase client instance
        user_id: User ID
        
    Returns:
        Dict with creativity profile data or None
    """
    try:
        result = supabase_client.table('creator_creativity_profiles')\
            .select('*')\
            .eq('user_id', user_id)\
            .execute()
        
        if result.data:
            return result.data[0]
        return None
        
    except Exception as e:
        logger.error(f"Error getting user creativity profile: {str(e)}")
        return None

async def monitor_creativity_test_completion(
    supabase_client,
    user_id: str,
    conversation_messages: List[Dict[str, str]]
) -> bool:
    """
    Monitor if a creativity test conversation is complete.
    Looks for 5 A-F responses to determine completion.
    
    Args:
        supabase_client: Supabase client instance
        user_id: User ID
        conversation_messages: List of conversation messages
        
    Returns:
        bool: True if creativity test appears complete, False otherwise
    """
    try:
        # Convert messages to text for analysis
        conversation_text = "\n".join([
            f"{msg['role'].upper()}: {msg['content']}" 
            for msg in conversation_messages
        ])
        
        # Look for 5 A-F responses in the conversation
        responses = re.findall(r'\b[A-F]\b', conversation_text, re.IGNORECASE)
        
        # Check if we have at least 5 distinct responses
        unique_responses = list(set([r.upper() for r in responses]))
        
        # More sophisticated check: look for pattern of questions and answers
        question_patterns = [
            r'Question 1 of 5',
            r'Question 2 of 5', 
            r'Question 3 of 5',
            r'Question 4 of 5',
            r'Question 5 of 5'
        ]
        
        questions_found = sum(1 for pattern in question_patterns if re.search(pattern, conversation_text))
        
        # Consider complete if we've seen all 5 questions and have some A-F responses
        is_complete = questions_found >= 5 and len(responses) >= 3
        
        logger.info(f"Creativity test completion check for user {user_id}: "
                   f"Questions found: {questions_found}/5, "
                   f"A-F responses: {len(responses)}, "
                   f"Complete: {is_complete}")
        
        return is_complete
        
    except Exception as e:
        logger.error(f"Error monitoring creativity test completion: {e}")
        return False

async def handle_completed_creativity_test(
    supabase_client, 
    user_id: str, 
    conversation_messages: List[Dict[str, str]]
) -> Dict[str, Any]:
    """
    Handle a completed creativity test by extracting responses and saving profile.
    
    Args:
        supabase_client: Supabase client instance
        user_id: User ID
        conversation_messages: List of conversation messages
        
    Returns:
        Dict with completion info
    """
    try:
        # Extract A-F responses from conversation
        conversation_text = "\n".join([
            f"{msg['role'].upper()}: {msg['content']}" 
            for msg in conversation_messages
        ])
        
        # Extract responses more carefully by looking for user messages with A-F
        user_responses = {}
        current_question = 1
        
        for msg in conversation_messages:
            if msg['role'] == 'user':
                content = msg['content'].strip().upper()
                # Look for single letter A-F responses
                if re.match(r'^[A-F]$', content) or re.search(r'\b[A-F]\b', content):
                    # Extract the letter
                    letter_match = re.search(r'\b([A-F])\b', content)
                    if letter_match and current_question <= 5:
                        user_responses[str(current_question)] = letter_match.group(1)
                        current_question += 1
        
        # If we didn't get responses that way, try a fallback approach
        if len(user_responses) < 3:
            # Look for any A-F responses in order
            responses = re.findall(r'\b([A-F])\b', conversation_text)
            for i, response in enumerate(responses[:5]):
                user_responses[str(i + 1)] = response.upper()
        
        logger.info(f"Extracted creativity responses for user {user_id}: {user_responses}")
        
        # Analyze responses to determine archetype
        if len(user_responses) >= 3:  # Need at least 3 responses for meaningful analysis
            archetype_data = analyze_creativity_responses(user_responses)
            
            # Save to database
            success = await save_creativity_profile(supabase_client, user_id, archetype_data)
            
            if success:
                return {
                    "test_completed": True,
                    "archetype": archetype_data['primary_archetype'],
                    "responses": user_responses,
                    "archetype_data": archetype_data
                }
            else:
                logger.error(f"Failed to save creativity profile for user {user_id}")
                return {"test_completed": False, "error": "Failed to save profile"}
        else:
            logger.warning(f"Insufficient responses for user {user_id}: {user_responses}")
            return {"test_completed": False, "error": "Insufficient responses"}
            
    except Exception as e:
        logger.error(f"Error handling completed creativity test for user {user_id}: {str(e)}")
        return {"test_completed": False, "error": str(e)}

# Additional planning functions will be added here 