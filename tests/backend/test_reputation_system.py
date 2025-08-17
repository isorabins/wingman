"""
Test suite for reputation system backend implementation
Validates calculation logic, caching, and API endpoints
"""

import pytest
import asyncio
from datetime import datetime, timezone
from uuid import uuid4
from unittest.mock import Mock, patch, AsyncMock

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.services.reputation_service import ReputationCalculator, ReputationService, ReputationData

class TestReputationCalculator:
    """Test core reputation calculation logic"""
    
    def setup_method(self):
        """Setup test calculator with mocked database"""
        self.calculator = ReputationCalculator()
        self.calculator.supabase = Mock()
    
    @pytest.mark.asyncio
    async def test_calculate_user_reputation_new_user(self):
        """Test reputation calculation for new user with no sessions"""
        user_id = str(uuid4())
        
        # Mock empty session history
        self.calculator.supabase.table.return_value.select.return_value.or_.return_value.execute.return_value.data = []
        
        result = await self.calculator.calculate_user_reputation(user_id)
        
        assert isinstance(result, ReputationData)
        assert result.user_id == user_id
        assert result.score == 0
        assert result.completed_sessions == 0
        assert result.no_shows == 0
        assert result.badge_color == "green"
        assert result.cache_timestamp is not None
    
    @pytest.mark.asyncio
    async def test_calculate_user_reputation_with_sessions(self):
        """Test reputation calculation with mixed session results"""
        user_id = str(uuid4())
        
        # Mock session history with completed and no-show sessions
        mock_sessions = [
            # Completed session - user1 confirmed by user2
            {
                'id': str(uuid4()),
                'status': 'completed',
                'user1_completed_confirmed_by_user2': True,
                'user2_completed_confirmed_by_user1': False,
                'wingman_matches': {'user1_id': user_id, 'user2_id': str(uuid4())}
            },
            # Completed session - user2 confirmed by user1
            {
                'id': str(uuid4()),
                'status': 'completed',
                'user1_completed_confirmed_by_user2': False,
                'user2_completed_confirmed_by_user1': True,
                'wingman_matches': {'user1_id': str(uuid4()), 'user2_id': user_id}
            },
            # No-show session
            {
                'id': str(uuid4()),
                'status': 'no_show',
                'user1_completed_confirmed_by_user2': False,
                'user2_completed_confirmed_by_user1': False,
                'wingman_matches': {'user1_id': user_id, 'user2_id': str(uuid4())}
            },
            # Cancelled session
            {
                'id': str(uuid4()),
                'status': 'cancelled',
                'user1_completed_confirmed_by_user2': False,
                'user2_completed_confirmed_by_user1': False,
                'wingman_matches': {'user1_id': str(uuid4()), 'user2_id': user_id}
            }
        ]
        
        self.calculator.supabase.table.return_value.select.return_value.or_.return_value.execute.return_value.data = mock_sessions
        
        result = await self.calculator.calculate_user_reputation(user_id)
        
        assert result.completed_sessions == 2  # 2 confirmed completions
        assert result.no_shows == 2  # 1 no_show + 1 cancelled
        assert result.score == 0  # 2 - 2 = 0
        assert result.badge_color == "green"  # score >= 0
    
    @pytest.mark.asyncio
    async def test_calculate_user_reputation_bounds(self):
        """Test reputation score bounds enforcement"""
        user_id = str(uuid4())
        
        # Test upper bound - many completed sessions
        mock_sessions_high = []
        for i in range(25):  # 25 completed sessions, 0 no-shows
            mock_sessions_high.append({
                'id': str(uuid4()),
                'status': 'completed',
                'user1_completed_confirmed_by_user2': True,
                'user2_completed_confirmed_by_user1': False,
                'wingman_matches': {'user1_id': user_id, 'user2_id': str(uuid4())}
            })
        
        self.calculator.supabase.table.return_value.select.return_value.or_.return_value.execute.return_value.data = mock_sessions_high
        
        result = await self.calculator.calculate_user_reputation(user_id)
        
        assert result.completed_sessions == 25
        assert result.no_shows == 0
        assert result.score == 20  # Capped at MAX_SCORE
        assert result.badge_color == "gold"
    
    @pytest.mark.asyncio
    async def test_calculate_user_reputation_lower_bound(self):
        """Test reputation score lower bound enforcement"""
        user_id = str(uuid4())
        
        # Test lower bound - many no-shows
        mock_sessions_low = []
        for i in range(10):  # 0 completed, 10 no-shows
            mock_sessions_low.append({
                'id': str(uuid4()),
                'status': 'no_show',
                'user1_completed_confirmed_by_user2': False,
                'user2_completed_confirmed_by_user1': False,
                'wingman_matches': {'user1_id': user_id, 'user2_id': str(uuid4())}
            })
        
        self.calculator.supabase.table.return_value.select.return_value.or_.return_value.execute.return_value.data = mock_sessions_low
        
        result = await self.calculator.calculate_user_reputation(user_id)
        
        assert result.completed_sessions == 0
        assert result.no_shows == 10
        assert result.score == -5  # Capped at MIN_SCORE
        assert result.badge_color == "red"
    
    def test_badge_color_logic(self):
        """Test badge color assignment logic"""
        # Test gold badge
        assert self.calculator._get_badge_color(15) == "gold"
        assert self.calculator._get_badge_color(10) == "gold"
        
        # Test green badge
        assert self.calculator._get_badge_color(9) == "green"
        assert self.calculator._get_badge_color(5) == "green"
        assert self.calculator._get_badge_color(0) == "green"
        
        # Test red badge
        assert self.calculator._get_badge_color(-1) == "red"
        assert self.calculator._get_badge_color(-5) == "red"
    
    @pytest.mark.asyncio
    async def test_invalid_user_id(self):
        """Test error handling for invalid user ID"""
        with pytest.raises(ValueError, match="Invalid user_id format"):
            await self.calculator.calculate_user_reputation("invalid-uuid")
    
    @pytest.mark.asyncio
    async def test_database_error_handling(self):
        """Test error handling for database failures"""
        user_id = str(uuid4())
        
        # Mock database error
        self.calculator.supabase.table.return_value.select.return_value.or_.return_value.execute.side_effect = Exception("DB Error")
        
        with pytest.raises(Exception, match="Failed to fetch session history"):
            await self.calculator.calculate_user_reputation(user_id)

class TestReputationService:
    """Test reputation service with caching"""
    
    def setup_method(self):
        """Setup test service with mocked dependencies"""
        self.service = ReputationService()
        self.service.calculator = Mock()
    
    @pytest.mark.asyncio
    async def test_get_user_reputation_cache_miss(self):
        """Test reputation fetching with cache miss"""
        user_id = str(uuid4())
        
        # Mock cache miss and fresh calculation
        with patch('src.services.reputation_service.ReputationService._get_cached_reputation', return_value=None):
            with patch('src.services.reputation_service.ReputationService._cache_reputation', return_value=True) as mock_cache:
                
                mock_reputation = ReputationData(
                    user_id=user_id,
                    score=5,
                    completed_sessions=7,
                    no_shows=2,
                    badge_color="green",
                    cache_timestamp=datetime.now(timezone.utc).isoformat()
                )
                
                self.service.calculator.calculate_user_reputation = AsyncMock(return_value=mock_reputation)
                
                result = await self.service.get_user_reputation(user_id)
                
                assert result == mock_reputation
                mock_cache.assert_called_once_with(user_id, mock_reputation)
    
    @pytest.mark.asyncio
    async def test_get_user_reputation_cache_hit(self):
        """Test reputation fetching with cache hit"""
        user_id = str(uuid4())
        
        cached_reputation = ReputationData(
            user_id=user_id,
            score=8,
            completed_sessions=10,
            no_shows=2,
            badge_color="green",
            cache_timestamp=datetime.now(timezone.utc).isoformat()
        )
        
        with patch('src.services.reputation_service.ReputationService._get_cached_reputation', return_value=cached_reputation):
            result = await self.service.get_user_reputation(user_id)
            
            assert result == cached_reputation
            # Calculator should not be called for cache hit
            self.service.calculator.calculate_user_reputation.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_get_user_reputation_no_cache(self):
        """Test reputation fetching with cache disabled"""
        user_id = str(uuid4())
        
        mock_reputation = ReputationData(
            user_id=user_id,
            score=3,
            completed_sessions=5,
            no_shows=2,
            badge_color="green",
            cache_timestamp=datetime.now(timezone.utc).isoformat()
        )
        
        self.service.calculator.calculate_user_reputation = AsyncMock(return_value=mock_reputation)
        
        result = await self.service.get_user_reputation(user_id, use_cache=False)
        
        assert result == mock_reputation
        # Should not check cache when use_cache=False
        self.service.calculator.calculate_user_reputation.assert_called_once_with(user_id)

class TestReputationData:
    """Test reputation data model"""
    
    def test_to_dict(self):
        """Test conversion to dictionary for API response"""
        timestamp = datetime.now(timezone.utc).isoformat()
        
        reputation = ReputationData(
            user_id=str(uuid4()),
            score=10,
            completed_sessions=15,
            no_shows=5,
            badge_color="gold",
            cache_timestamp=timestamp
        )
        
        result = reputation.to_dict()
        
        expected = {
            "score": 10,
            "completed_sessions": 15,
            "no_shows": 5,
            "badge_color": "gold",
            "cache_timestamp": timestamp
        }
        
        assert result == expected
        # user_id should not be in API response dict
        assert "user_id" not in result

# Integration tests with actual Redis (if available)
class TestReputationIntegration:
    """Integration tests for reputation system"""
    
    @pytest.mark.asyncio
    async def test_cache_integration(self):
        """Test actual Redis caching if available"""
        try:
            from src.redis_session import RedisSession
            await RedisSession.initialize()
            
            if not RedisSession._healthy:
                pytest.skip("Redis not available for integration test")
            
            service = ReputationService()
            user_id = str(uuid4())
            
            # Mock the calculator to return test data
            service.calculator = Mock()
            mock_reputation = ReputationData(
                user_id=user_id,
                score=7,
                completed_sessions=9,
                no_shows=2,
                badge_color="green",
                cache_timestamp=datetime.now(timezone.utc).isoformat()
            )
            service.calculator.calculate_user_reputation = AsyncMock(return_value=mock_reputation)
            
            # First call should miss cache and calculate
            result1 = await service.get_user_reputation(user_id)
            assert result1 == mock_reputation
            
            # Second call should hit cache
            service.calculator.calculate_user_reputation.reset_mock()
            result2 = await service.get_user_reputation(user_id)
            assert result2.score == mock_reputation.score
            
            # Calculator should not be called on cache hit
            service.calculator.calculate_user_reputation.assert_not_called()
            
            # Cleanup
            await service.invalidate_user_cache(user_id)
            
        except ImportError:
            pytest.skip("Redis dependencies not available")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])