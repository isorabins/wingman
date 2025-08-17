"""
Reputation Service for WingmanMatch
Calculates user reputation scores based on session completion and no-shows
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from uuid import UUID

from src.config import Config
from src.database import SupabaseFactory

logger = logging.getLogger(__name__)

@dataclass
class ReputationData:
    """Data class for user reputation metrics"""
    user_id: str
    score: int
    completed_sessions: int
    no_shows: int
    badge_color: str
    cache_timestamp: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response"""
        return {
            "score": self.score,
            "completed_sessions": self.completed_sessions,
            "no_shows": self.no_shows,
            "badge_color": self.badge_color,
            "cache_timestamp": self.cache_timestamp
        }

class ReputationCalculator:
    """Core business logic for reputation score calculation"""
    
    # Score bounds
    MIN_SCORE = -5
    MAX_SCORE = 20
    
    # Badge color thresholds
    GOLD_THRESHOLD = 10
    GREEN_THRESHOLD = 0
    
    def __init__(self):
        self.supabase = SupabaseFactory.get_service_client()
    
    async def calculate_user_reputation(self, user_id: str) -> ReputationData:
        """
        Calculate complete reputation data for a user
        
        Args:
            user_id: UUID string of the user
            
        Returns:
            ReputationData with score, counts, and badge color
        """
        try:
            # Validate user_id format
            UUID(user_id)
        except ValueError:
            raise ValueError(f"Invalid user_id format: {user_id}")
        
        # Query user session history
        session_data = await self._get_user_session_history(user_id)
        
        # Calculate metrics
        completed_sessions = self._count_completed_sessions(session_data, user_id)
        no_shows = self._count_no_shows(session_data, user_id)
        
        # Calculate score with bounds
        raw_score = completed_sessions - no_shows
        score = max(self.MIN_SCORE, min(self.MAX_SCORE, raw_score))
        
        # Determine badge color
        badge_color = self._get_badge_color(score)
        
        # Create timestamp
        cache_timestamp = datetime.now(timezone.utc).isoformat()
        
        return ReputationData(
            user_id=user_id,
            score=score,
            completed_sessions=completed_sessions,
            no_shows=no_shows,
            badge_color=badge_color,
            cache_timestamp=cache_timestamp
        )
    
    async def _get_user_session_history(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Query wingman_sessions for user's session history
        
        Args:
            user_id: UUID string of the user
            
        Returns:
            List of session records where user was a participant
        """
        try:
            # First get all match IDs where user is a participant
            matches_result = self.supabase.table('wingman_matches')\
                .select('id')\
                .or_(f'user1_id.eq.{user_id},user2_id.eq.{user_id}')\
                .execute()
            
            if not matches_result.data:
                logger.debug(f"No matches found for user {user_id}")
                return []
            
            # Extract match IDs
            match_ids = [match['id'] for match in matches_result.data]
            logger.debug(f"Found {len(match_ids)} matches for user {user_id}")
            
            # Query sessions for these matches
            result = self.supabase.table('wingman_sessions')\
                .select("""
                    id,
                    match_id,
                    status,
                    completed_at,
                    user1_completed_confirmed_by_user2,
                    user2_completed_confirmed_by_user1,
                    created_at,
                    wingman_matches!inner(
                        user1_id,
                        user2_id
                    )
                """)\
                .in_('match_id', match_ids)\
                .execute()
            
            if result.data:
                logger.debug(f"Found {len(result.data)} sessions for user {user_id}")
                return result.data
            else:
                logger.debug(f"No sessions found for user {user_id}")
                return []
                
        except Exception as e:
            logger.error(f"Database error getting session history for user {user_id}: {e}")
            raise Exception(f"Failed to fetch session history: {str(e)}")
    
    def _count_completed_sessions(self, sessions: List[Dict[str, Any]], user_id: str) -> int:
        """
        Count successfully completed sessions for the user
        
        A session is completed if:
        - Status is 'completed'
        - User's completion was confirmed by their buddy
        """
        completed_count = 0
        
        for session in sessions:
            if session.get('status') != 'completed':
                continue
                
            # Determine if this user's completion was confirmed
            match = session.get('wingman_matches', {})
            user1_id = match.get('user1_id')
            user2_id = match.get('user2_id')
            
            # Check which user this is and if their completion was confirmed
            if user_id == user1_id:
                # User is user1, check if user2 confirmed their completion
                if session.get('user1_completed_confirmed_by_user2'):
                    completed_count += 1
            elif user_id == user2_id:
                # User is user2, check if user1 confirmed their completion
                if session.get('user2_completed_confirmed_by_user1'):
                    completed_count += 1
        
        logger.debug(f"User {user_id} has {completed_count} completed sessions")
        return completed_count
    
    def _count_no_shows(self, sessions: List[Dict[str, Any]], user_id: str) -> int:
        """
        Count no-show sessions for the user
        
        A session is a no-show if:
        - Status is 'no_show' or 'cancelled'
        - The user was responsible for the no-show (simplified: count all for now)
        """
        no_show_count = 0
        
        for session in sessions:
            if session.get('status') in ['no_show', 'cancelled']:
                no_show_count += 1
        
        logger.debug(f"User {user_id} has {no_show_count} no-show sessions")
        return no_show_count
    
    def _get_badge_color(self, score: int) -> str:
        """
        Determine badge color based on reputation score
        
        Args:
            score: Reputation score (-5 to 20)
            
        Returns:
            Badge color: "gold", "green", or "red"
        """
        if score >= self.GOLD_THRESHOLD:
            return "gold"
        elif score >= self.GREEN_THRESHOLD:
            return "green"
        else:
            return "red"

class ReputationService:
    """
    High-level reputation service with caching
    Main interface for reputation system
    """
    
    CACHE_TTL = 300  # 5 minutes
    CACHE_KEY_PREFIX = "reputation:user"
    
    def __init__(self):
        self.calculator = ReputationCalculator()
    
    async def get_user_reputation(self, user_id: str, use_cache: bool = True) -> ReputationData:
        """
        Get user reputation with optional caching
        
        Args:
            user_id: UUID string of the user
            use_cache: Whether to use Redis cache (default True)
            
        Returns:
            ReputationData with complete reputation metrics
        """
        # Try cache first if enabled
        if use_cache:
            cached_data = await self._get_cached_reputation(user_id)
            if cached_data:
                logger.debug(f"Cache hit for user reputation {user_id}")
                return cached_data
        
        # Calculate fresh reputation data
        logger.debug(f"Calculating fresh reputation for user {user_id}")
        reputation_data = await self.calculator.calculate_user_reputation(user_id)
        
        # Cache the result if caching is enabled
        if use_cache:
            await self._cache_reputation(user_id, reputation_data)
        
        return reputation_data
    
    async def _get_cached_reputation(self, user_id: str) -> Optional[ReputationData]:
        """Get reputation data from Redis cache"""
        try:
            from src.redis_session import RedisSession
            
            cache_key = f"{self.CACHE_KEY_PREFIX}:{user_id}"
            cached_data = await RedisSession.get_session(cache_key)
            
            if cached_data:
                return ReputationData(
                    user_id=cached_data['user_id'],
                    score=cached_data['score'],
                    completed_sessions=cached_data['completed_sessions'],
                    no_shows=cached_data['no_shows'],
                    badge_color=cached_data['badge_color'],
                    cache_timestamp=cached_data['cache_timestamp']
                )
            
            return None
            
        except Exception as e:
            logger.warning(f"Cache retrieval failed for user {user_id}: {e}")
            return None
    
    async def _cache_reputation(self, user_id: str, reputation_data: ReputationData) -> bool:
        """Cache reputation data in Redis"""
        try:
            from src.redis_session import RedisSession
            
            cache_key = f"{self.CACHE_KEY_PREFIX}:{user_id}"
            cache_data = {
                'user_id': reputation_data.user_id,
                'score': reputation_data.score,
                'completed_sessions': reputation_data.completed_sessions,
                'no_shows': reputation_data.no_shows,
                'badge_color': reputation_data.badge_color,
                'cache_timestamp': reputation_data.cache_timestamp
            }
            
            success = await RedisSession.set_session(cache_key, cache_data, self.CACHE_TTL)
            if success:
                logger.debug(f"Cached reputation for user {user_id} with TTL {self.CACHE_TTL}s")
            
            return success
            
        except Exception as e:
            logger.warning(f"Cache storage failed for user {user_id}: {e}")
            return False
    
    async def invalidate_user_cache(self, user_id: str) -> bool:
        """Invalidate cached reputation for a specific user"""
        try:
            from src.redis_session import RedisSession
            
            if not RedisSession._healthy or not RedisSession._client:
                logger.warning("Redis unavailable - cache not invalidated")
                return False
            
            cache_key = f"{self.CACHE_KEY_PREFIX}:{user_id}"
            result = await RedisSession._client.delete(cache_key)
            
            logger.info(f"Invalidated reputation cache for user {user_id}")
            return result > 0
            
        except Exception as e:
            logger.error(f"Cache invalidation failed for user {user_id}: {e}")
            return False
    
    async def invalidate_all_cache(self) -> bool:
        """Invalidate all reputation cache entries"""
        try:
            from src.redis_session import RedisSession
            
            if not RedisSession._healthy or not RedisSession._client:
                logger.warning("Redis unavailable - cache not invalidated")
                return False
            
            # Find all reputation cache keys
            pattern = f"{self.CACHE_KEY_PREFIX}:*"
            keys = await RedisSession._client.keys(pattern)
            
            if keys:
                await RedisSession._client.delete(*keys)
                logger.info(f"Invalidated {len(keys)} reputation cache entries")
                return True
            else:
                logger.info("No reputation cache entries to invalidate")
                return True
                
        except Exception as e:
            logger.error(f"Bulk cache invalidation failed: {e}")
            return False

# Global service instance
reputation_service = ReputationService()