#!/usr/bin/env python3
"""
WingmanMatcher Service for Automatic Buddy Matching

Implements the auto-matching algorithm for finding wingman buddies based on:
- Geographic proximity using existing distance calculations
- Experience level compatibility (same or ±1 level)
- Recency filtering to avoid recent pairs
- Throttling to ensure one active pending match per user

Follows established patterns from WingmanMemory and ConfidenceTestAgent for 
auto-dependency creation and error handling.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone, timedelta
from supabase import Client

from src.database import SupabaseFactory
from src.db.distance import find_candidates_within_radius, BuddyCandidate

logger = logging.getLogger(__name__)

class WingmanMatcher:
    """Service for automatic wingman buddy matching with persistence"""
    
    # Experience level mapping for compatibility
    EXPERIENCE_LEVELS = {
        'beginner': 1,
        'intermediate': 2, 
        'advanced': 3
    }
    
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client
        
    async def create_automatic_match(self, user_id: str, max_radius_miles: int = 25) -> Dict[str, Any]:
        """
        Create automatic wingman match for user within specified radius
        
        Args:
            user_id: User looking for a wingman buddy
            max_radius_miles: Maximum distance for candidates (default 25)
            
        Returns:
            Dict with success status, message, and match details
        """
        try:
            # Ensure user profile exists for foreign key integrity
            await self.ensure_user_profile(user_id)
            
            # Check for existing pending match (throttling)
            existing_match = await self.check_existing_pending_match(user_id)
            if existing_match:
                return {
                    "success": True,
                    "message": "You already have a pending wingman match",
                    "match_id": existing_match['id'],
                    "buddy_user_id": existing_match['buddy_user_id'],
                    "buddy_profile": existing_match.get('buddy_profile')
                }
            
            # Find best candidate within radius
            best_candidate_id = await self.find_best_candidate(user_id, max_radius_miles)
            
            if not best_candidate_id:
                logger.info(f"No compatible candidates found for user {user_id} within {max_radius_miles} miles")
                return {
                    "success": False,
                    "message": f"No compatible wingman buddies found within {max_radius_miles} miles. Try expanding your search radius.",
                    "match_id": None,
                    "buddy_user_id": None,
                    "buddy_profile": None
                }
            
            # Create match record
            match_result = await self.create_match_record(user_id, best_candidate_id)
            
            # Get buddy profile information for response
            buddy_profile = await self._get_user_profile(best_candidate_id)
            
            logger.info(f"Successfully created wingman match {match_result['id']} between {user_id} and {best_candidate_id}")
            
            return {
                "success": True,
                "message": "Wingman buddy match created successfully!",
                "match_id": match_result['id'],
                "buddy_user_id": best_candidate_id,
                "buddy_profile": buddy_profile
            }
            
        except Exception as e:
            logger.error(f"Error creating automatic match for user {user_id}: {e}")
            return {
                "success": False,
                "message": "Unable to create wingman match at this time. Please try again later.",
                "match_id": None,
                "buddy_user_id": None,
                "buddy_profile": None
            }
    
    async def find_best_candidate(self, user_id: str, radius_miles: int) -> Optional[str]:
        """
        Find the best wingman candidate using compatibility rules
        
        Args:
            user_id: User looking for a buddy
            radius_miles: Search radius in miles
            
        Returns:
            User ID of best candidate or None if none found
        """
        try:
            # Get candidates within radius using existing distance calculation
            candidates = await find_candidates_within_radius(user_id, radius_miles)
            
            if not candidates:
                logger.info(f"No candidates found within {radius_miles} miles for user {user_id}")
                return None
            
            # Get user's experience level for compatibility check
            user_profile = await self._get_user_profile(user_id)
            if not user_profile or not user_profile.get('experience_level'):
                logger.warning(f"User {user_id} has incomplete profile, cannot match")
                return None
            
            user_experience_level = user_profile['experience_level']
            user_level_num = self.EXPERIENCE_LEVELS.get(user_experience_level, 2)  # Default intermediate
            
            # Filter candidates by experience level compatibility (same or ±1)
            compatible_candidates = []
            for candidate in candidates:
                candidate_level_num = self.EXPERIENCE_LEVELS.get(candidate.experience_level, 2)
                level_diff = abs(user_level_num - candidate_level_num)
                
                if level_diff <= 1:  # Same level or ±1
                    compatible_candidates.append(candidate)
            
            if not compatible_candidates:
                logger.info(f"No experience-compatible candidates for user {user_id} (level: {user_experience_level})")
                return None
            
            # Filter out users who were recently paired (last 7 days)
            recent_cutoff = datetime.now(timezone.utc) - timedelta(days=7)
            filtered_candidates = []
            
            for candidate in compatible_candidates:
                # Check if they were recently matched
                recent_match = await self._check_recent_pairing(user_id, candidate.user_id, recent_cutoff)
                if not recent_match:
                    filtered_candidates.append(candidate)
                else:
                    logger.info(f"Excluding candidate {candidate.user_id} - recently paired with {user_id}")
            
            if not filtered_candidates:
                logger.info(f"No candidates after recency filtering for user {user_id}")
                return None
            
            # Select best candidate: closest distance first, then by user activity
            # Sort by distance ascending to ensure closest candidate is selected
            filtered_candidates.sort(key=lambda c: c.distance_miles)
            best_candidate = filtered_candidates[0]
            
            logger.info(f"Selected best candidate {best_candidate.user_id} for user {user_id}: "
                       f"distance={best_candidate.distance_miles}mi, level={best_candidate.experience_level}")
            
            return best_candidate.user_id
            
        except Exception as e:
            logger.error(f"Error finding best candidate for user {user_id}: {e}")
            return None
    
    async def create_match_record(self, user1_id: str, user2_id: str) -> Dict[str, Any]:
        """
        Create wingman match record with deterministic user ordering
        
        Args:
            user1_id: First user ID
            user2_id: Second user ID
            
        Returns:
            Created match record
        """
        try:
            # Deterministic ordering: user1_id < user2_id alphabetically
            if user1_id > user2_id:
                user1_id, user2_id = user2_id, user1_id
            
            # Check if match already exists (duplicate prevention)
            existing = self.supabase.table('wingman_matches')\
                .select('*')\
                .eq('user1_id', user1_id)\
                .eq('user2_id', user2_id)\
                .eq('status', 'pending')\
                .execute()
            
            if existing.data:
                logger.info(f"Match already exists between {user1_id} and {user2_id}")
                return existing.data[0]
            
            # Create new match record
            match_data = {
                'user1_id': user1_id,
                'user2_id': user2_id,
                'status': 'pending',
                'user1_reputation': 0,
                'user2_reputation': 0,
                'created_at': datetime.now(timezone.utc).isoformat()
            }
            
            result = self.supabase.table('wingman_matches')\
                .insert(match_data)\
                .execute()
            
            if not result.data:
                raise Exception("Failed to create match record")
            
            match_record = result.data[0]
            logger.info(f"Created wingman match {match_record['id']} between {user1_id} and {user2_id}")
            
            return match_record
            
        except Exception as e:
            logger.error(f"Error creating match record between {user1_id} and {user2_id}: {e}")
            raise
    
    async def check_existing_pending_match(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Check if user already has an active pending match (throttling)
        
        Args:
            user_id: User to check
            
        Returns:
            Existing match record or None
        """
        try:
            # Check both user1_id and user2_id positions
            result = self.supabase.table('wingman_matches')\
                .select('*')\
                .eq('status', 'pending')\
                .or_(f'user1_id.eq.{user_id},user2_id.eq.{user_id}')\
                .execute()
            
            if result.data:
                match = result.data[0]
                # Determine which user is the buddy
                buddy_user_id = match['user2_id'] if match['user1_id'] == user_id else match['user1_id']
                
                # Get buddy profile info separately to avoid complex joins
                buddy_profile = await self._get_user_profile(buddy_user_id)
                
                return {
                    'id': match['id'],
                    'buddy_user_id': buddy_user_id,
                    'buddy_profile': buddy_profile,
                    'created_at': match['created_at']
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error checking existing pending match for user {user_id}: {e}")
            return None
    
    async def ensure_user_profile(self, user_id: str):
        """
        Ensure user profile exists to prevent foreign key constraint violations
        Following the pattern from WingmanMemory.ensure_user_profile
        """
        try:
            # Check if user profile exists
            result = self.supabase.table('user_profiles')\
                .select('id')\
                .eq('id', user_id)\
                .execute()
            
            if not result.data:
                # Create minimal user profile with auto-dependency creation pattern
                profile_data = {
                    "id": user_id,
                    "email": f"user_{user_id[:8]}@wingmanmatch.temp",
                    "first_name": "User",
                    "last_name": "Temp",
                    "bio": "New WingmanMatch user",
                    "experience_level": "beginner",
                    "confidence_archetype": "Naturalist",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
                
                self.supabase.table('user_profiles').insert(profile_data).execute()
                logger.info(f"Auto-created user profile for {user_id}")
        
        except Exception as e:
            logger.error(f"Error ensuring user profile for {user_id}: {e}")
            
    async def _get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user profile information"""
        try:
            result = self.supabase.table('user_profiles')\
                .select('id, first_name, experience_level, confidence_archetype')\
                .eq('id', user_id)\
                .execute()
            
            if result.data:
                return result.data[0]
            else:
                logger.warning(f"No profile found for user {user_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting user profile for {user_id}: {e}")
            return None
    
    async def _check_recent_pairing(self, user1_id: str, user2_id: str, cutoff_date: datetime) -> bool:
        """
        Check if two users were recently paired
        
        Args:
            user1_id: First user ID
            user2_id: Second user ID  
            cutoff_date: Date threshold for "recent"
            
        Returns:
            True if recently paired, False otherwise
        """
        try:
            # Use deterministic ordering for consistent checks
            if user1_id > user2_id:
                user1_id, user2_id = user2_id, user1_id
            
            result = self.supabase.table('wingman_matches')\
                .select('id, created_at')\
                .eq('user1_id', user1_id)\
                .eq('user2_id', user2_id)\
                .gte('created_at', cutoff_date.isoformat())\
                .execute()
            
            return len(result.data) > 0
            
        except Exception as e:
            logger.error(f"Error checking recent pairing for {user1_id} and {user2_id}: {e}")
            return False  # If we can't check, allow the pairing