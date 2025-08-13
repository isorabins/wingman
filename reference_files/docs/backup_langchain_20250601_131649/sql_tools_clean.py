#!/usr/bin/env python3
"""
Database Utilities - Clean Version
Pure database functions without LangChain tools
"""
import logging
from typing import Dict, Optional, List, Any
from datetime import datetime, date
from supabase import create_client
from src.config import Config

logger = logging.getLogger(__name__)

# Error messages
ERROR_MESSAGES = {
    "system_error": "System temporarily unavailable. Please try again.",
    "no_data": "No data found for your query.",
    "invalid_input": "Please provide valid input."
}


def get_supabase_client():
    """Get a Supabase client instance"""
    return create_client(Config.SUPABASE_URL, Config.SUPABASE_SERVICE_KEY)


async def search_database_content(query: str, user_id: str, content_type: Optional[str] = None) -> Dict[str, Any]:
    """
    Search across all content types with relevance ranking.
    
    Args:
        query: Search query
        user_id: User's ID
        content_type: Optional content type filter
        
    Returns:
        Dict with search results
    """
    try:
        logger.info(f"Searching database for query: {query} (user: {user_id})")
        
        client = get_supabase_client()
        results = []
        
        # Search in longterm_memory table
        try:
            longterm_data = client.table('longterm_memory')\
                .select('*')\
                .eq('user_id', user_id)\
                .execute()
                
            for item in longterm_data.data:
                content = item.get('memory_content', '')
                if query.lower() in content.lower():
                    results.append({
                        'source': 'longterm_memory',
                        'content': content,
                        'created_at': item.get('created_at'),
                        'type': 'memory'
                    })
        except Exception as e:
            logger.warning(f"Error searching longterm_memory: {e}")
            
        # Search in project_overview table
        try:
            project_data = client.table('project_overview')\
                .select('*')\
                .eq('user_id', user_id)\
                .execute()
                
            for item in project_data.data:
                searchable_content = f"{item.get('project_name', '')} {item.get('description', '')}"
                if query.lower() in searchable_content.lower():
                    results.append({
                        'source': 'project_overview',
                        'content': f"Project: {item.get('project_name')} - {item.get('description')}",
                        'created_at': item.get('creation_date'),
                        'type': 'project'
                    })
        except Exception as e:
            logger.warning(f"Error searching project_overview: {e}")
            
        # Search in project_updates table
        try:
            updates_data = client.table('project_updates')\
                .select('*')\
                .eq('user_id', user_id)\
                .execute()
                
            for item in updates_data.data:
                content = item.get('progress_summary', '')
                if query.lower() in content.lower():
                    results.append({
                        'source': 'project_updates',
                        'content': content,
                        'created_at': item.get('update_date'),
                        'type': 'update'
                    })
        except Exception as e:
            logger.warning(f"Error searching project_updates: {e}")
            
        # Sort by creation date (most recent first)
        results.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        return {
            "status": "success",
            "results": results[:10],  # Limit to top 10 results
            "count": len(results)
        }
        
    except Exception as e:
        logger.error(f"Database search error: {e}")
        return {"status": "error", "message": ERROR_MESSAGES["system_error"]}


async def update_project_status(project_id: str, user_id: str, progress_summary: str,
                              milestones_hit: List[str] = None, blockers: List[str] = None,
                              next_steps: List[str] = None, mood_rating: Optional[int] = None) -> Dict[str, Any]:
    """
    Update project status with daily summary and metadata.
    
    Args:
        project_id: Project ID
        user_id: User's ID
        progress_summary: Progress summary
        milestones_hit: List of milestones achieved
        blockers: List of current blockers
        next_steps: List of next steps
        mood_rating: Mood rating (1-10)
        
    Returns:
        Dict with update status
    """
    if milestones_hit is None:
        milestones_hit = []
    if blockers is None:
        blockers = []
    if next_steps is None:
        next_steps = []
        
    try:
        logger.info(f"Updating project status for user {user_id}")
        
        client = get_supabase_client()
        
        # Check if update exists for today
        today = datetime.now().date()
        existing = client.table('project_updates').select('id')\
            .eq('project_id', project_id)\
            .eq('update_date', str(today))\
            .execute()

        if existing.data:
            # Update existing record
            response = client.table('project_updates')\
                .update({
                    'progress_summary': progress_summary,
                    'milestones_hit': milestones_hit,
                    'blockers': blockers,
                    'next_steps': next_steps,
                    'mood_rating': mood_rating
                })\
                .eq('id', existing.data[0]['id'])\
                .execute()
        else:
            # Create new record
            response = client.table('project_updates')\
                .insert({
                    'project_id': project_id,
                    'user_id': user_id,
                    'progress_summary': progress_summary,
                    'milestones_hit': milestones_hit,
                    'blockers': blockers,
                    'next_steps': next_steps,
                    'mood_rating': mood_rating
                })\
                .execute()

        return {
            "status": "success",
            "message": "Status updated successfully",
            "data": response.data
        }

    except Exception as e:
        logger.error(f"Status update error: {e}")
        return {"status": "error", "message": ERROR_MESSAGES["system_error"]}


async def get_user_profile(user_id: str) -> Dict[str, Any]:
    """
    Get user profile information.
    
    Args:
        user_id: User's ID
        
    Returns:
        Dict with user profile data
    """
    try:
        logger.info(f"Querying user profile for {user_id}")
        
        client = get_supabase_client()
        
        response = client.table('creator_profiles')\
            .select('*')\
            .eq('id', user_id)\
            .single()\
            .execute()

        if not response.data:
            return {"status": "not_found", "message": ERROR_MESSAGES["no_data"]}
        
        return {
            "status": "success",
            "data": response.data
        }

    except Exception as e:
        logger.error(f"Profile query error: {e}")
        return {"status": "error", "message": ERROR_MESSAGES["system_error"]} 