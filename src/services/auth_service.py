"""
Authentication service for WingmanMatch
Handles user authentication and authorization
"""

import logging
from typing import Optional
from fastapi import HTTPException, Request
from src.config import Config

logger = logging.getLogger(__name__)

async def get_current_user_id(request: Optional[Request] = None) -> Optional[str]:
    """
    Get current user ID from authentication context
    For now, this is a simplified implementation for development
    In production, this would extract from JWT tokens
    """
    try:
        # For development/testing, check for test headers
        if Config.ENABLE_TEST_AUTH and Config.DEVELOPMENT_MODE:
            # Check for test user ID in headers (for development testing)
            test_user_id = None
            if request:
                test_user_id = request.headers.get("X-Test-User-ID")
            
            if test_user_id:
                logger.info(f"🧪 TEST AUTH: Using test user ID {test_user_id}")
                return test_user_id
        
        # TODO: In production, implement proper JWT token validation
        # For now, return None to indicate no authentication
        # This will cause the endpoints to return 401 Unauthorized
        
        logger.warning("Authentication not implemented - returning None")
        return None
        
    except Exception as e:
        logger.error(f"Error getting current user ID: {str(e)}")
        return None

def require_authentication(user_id: Optional[str]) -> str:
    """
    Require authentication and return user ID
    Raises HTTPException if not authenticated
    """
    if not user_id:
        raise HTTPException(
            status_code=401, 
            detail="Authentication required. Please log in to access this resource."
        )
    
    return user_id