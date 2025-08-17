#!/usr/bin/env python3
"""
Comprehensive Unit Tests for WingmanMatcher Service

Test Coverage:
- WingmanMatcher initialization and configuration
- Experience level compatibility logic (same level or ±1)
- Candidate selection with synthetic user pools
- Throttling enforcement (one pending match per user)
- Recency filtering (7-day exclusion rule)
- Deterministic selection with fixed candidate pools
- Auto-dependency creation for user profiles
- Error handling for edge cases (empty pools, invalid users)
"""

import pytest
import asyncio
import uuid
import json
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from services.wingman_matcher import WingmanMatcher
from database import SupabaseFactory
from db.distance import BuddyCandidate

class TestWingmanMatcherInitialization:
    """Test WingmanMatcher service initialization and configuration"""
    
    def test_matcher_initialization(self):
        """Test WingmanMatcher initializes with proper client configuration"""
        mock_client = MagicMock()
        matcher = WingmanMatcher(mock_client)
        
        assert matcher.supabase == mock_client
        assert hasattr(matcher, 'EXPERIENCE_LEVELS')
        assert len(matcher.EXPERIENCE_LEVELS) == 3
        assert 'beginner' in matcher.EXPERIENCE_LEVELS
        assert 'intermediate' in matcher.EXPERIENCE_LEVELS
        assert 'advanced' in matcher.EXPERIENCE_LEVELS
    
    def test_experience_level_mapping(self):
        """Test experience level to numeric mapping is correct"""
        mock_client = MagicMock()
        matcher = WingmanMatcher(mock_client)
        
        expected_mapping = {
            'beginner': 1,
            'intermediate': 2,
            'advanced': 3
        }
        
        assert matcher.EXPERIENCE_LEVELS == expected_mapping

class TestExperienceLevelCompatibility:
    """Test experience level compatibility logic (same or ±1 level)"""
    
    @pytest.fixture
    def matcher(self):
        mock_client = MagicMock()
        return WingmanMatcher(mock_client)
    
    @pytest.fixture
    def mock_candidates(self):
        """Create mock candidates with different experience levels"""
        return [
            BuddyCandidate(
                user_id="beginner-user-1",
                city="San Francisco",
                distance_miles=5.0,
                experience_level="beginner",
                confidence_archetype="Naturalist"
            ),
            BuddyCandidate(
                user_id="intermediate-user-1",
                city="Oakland",
                distance_miles=10.0,
                experience_level="intermediate",
                confidence_archetype="Analyzer"
            ),
            BuddyCandidate(
                user_id="advanced-user-1",
                city="Berkeley",
                distance_miles=12.0,
                experience_level="advanced",
                confidence_archetype="Sprinter"
            ),
            BuddyCandidate(
                user_id="intermediate-user-2",
                city="Palo Alto",
                distance_miles=25.0,
                experience_level="intermediate",
                confidence_archetype="Scholar"
            )
        ]
    
    @pytest.mark.asyncio
    async def test_beginner_compatibility(self, matcher, mock_candidates):
        """Test beginner matches with beginner and intermediate only"""
        user_id = "test-beginner"
        
        # Mock user profile as beginner
        user_profile = {
            'id': user_id,
            'experience_level': 'beginner',
            'first_name': 'Test',
            'confidence_archetype': 'Naturalist'
        }
        
        with patch.object(matcher, '_get_user_profile', return_value=user_profile), \
             patch.object(matcher, '_check_recent_pairing', return_value=False), \
             patch('services.wingman_matcher.find_candidates_within_radius', return_value=mock_candidates):
            
            result = await matcher.find_best_candidate(user_id, 25)
            
            # Should select beginner-user-1 (same level, closest distance)
            assert result == "beginner-user-1"
    
    @pytest.mark.asyncio
    async def test_intermediate_compatibility(self, matcher, mock_candidates):
        """Test intermediate matches with all levels (±1)"""
        user_id = "test-intermediate"
        
        # Mock user profile as intermediate
        user_profile = {
            'id': user_id,
            'experience_level': 'intermediate',
            'first_name': 'Test',
            'confidence_archetype': 'Analyzer'
        }
        
        with patch.object(matcher, '_get_user_profile', return_value=user_profile), \
             patch.object(matcher, '_check_recent_pairing', return_value=False), \
             patch('services.wingman_matcher.find_candidates_within_radius', return_value=mock_candidates):
            
            result = await matcher.find_best_candidate(user_id, 25)
            
            # Should select beginner-user-1 (closest compatible candidate)
            assert result == "beginner-user-1"
    
    @pytest.mark.asyncio
    async def test_advanced_compatibility(self, matcher, mock_candidates):
        """Test advanced matches with intermediate and advanced only"""
        user_id = "test-advanced"
        
        # Mock user profile as advanced
        user_profile = {
            'id': user_id,
            'experience_level': 'advanced',
            'first_name': 'Test',
            'confidence_archetype': 'Sprinter'
        }
        
        with patch.object(matcher, '_get_user_profile', return_value=user_profile), \
             patch.object(matcher, '_check_recent_pairing', return_value=False), \
             patch('services.wingman_matcher.find_candidates_within_radius', return_value=mock_candidates):
            
            result = await matcher.find_best_candidate(user_id, 25)
            
            # Should select intermediate-user-1 (compatible and closer than other intermediate)
            assert result == "intermediate-user-1"
    
    @pytest.mark.asyncio
    async def test_no_compatible_experience_levels(self, matcher):
        """Test when no candidates have compatible experience levels"""
        user_id = "test-user"
        
        # User is beginner, but all candidates are advanced (incompatible)
        user_profile = {
            'id': user_id,
            'experience_level': 'beginner',
            'first_name': 'Test',
            'confidence_archetype': 'Naturalist'
        }
        
        advanced_only_candidates = [
            BuddyCandidate(
                user_id="advanced-user-1",
                city="Berkeley",
                distance_miles=12.0,
                experience_level="advanced",
                confidence_archetype="Sprinter"
            )
        ]
        
        with patch.object(matcher, '_get_user_profile', return_value=user_profile), \
             patch('services.wingman_matcher.find_candidates_within_radius', return_value=advanced_only_candidates):
            
            result = await matcher.find_best_candidate(user_id, 25)
            
            assert result is None

class TestThrottlingEnforcement:
    """Test throttling enforcement (one pending match per user)"""
    
    @pytest.fixture
    def matcher(self):
        mock_client = MagicMock()
        return WingmanMatcher(mock_client)
    
    @pytest.mark.asyncio
    async def test_existing_pending_match_returned(self, matcher):
        """Test that existing pending match is returned instead of creating new one"""
        user_id = "test-user"
        
        # Mock existing pending match
        existing_match = {
            'id': 'match-123',
            'buddy_user_id': 'buddy-456',
            'buddy_profile': {'first_name': 'Buddy', 'experience_level': 'intermediate'},
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        
        with patch.object(matcher, 'ensure_user_profile'), \
             patch.object(matcher, 'check_existing_pending_match', return_value=existing_match):
            
            result = await matcher.create_automatic_match(user_id, 25)
            
            assert result['success'] is True
            assert result['message'] == "You already have a pending wingman match"
            assert result['match_id'] == 'match-123'
            assert result['buddy_user_id'] == 'buddy-456'
    
    @pytest.mark.asyncio
    async def test_no_existing_match_creates_new(self, matcher):
        """Test that new match is created when no existing pending match"""
        user_id = "test-user"
        
        # Mock no existing match
        mock_candidate = BuddyCandidate(
            user_id="candidate-789",
            city="San Francisco",
            distance_miles=10.0,
            experience_level="intermediate",
            confidence_archetype="Analyzer"
        )
        
        mock_match_record = {
            'id': 'new-match-456',
            'user1_id': user_id,
            'user2_id': 'candidate-789',
            'status': 'pending'
        }
        
        mock_buddy_profile = {
            'id': 'candidate-789',
            'first_name': 'Candidate',
            'experience_level': 'intermediate'
        }
        
        with patch.object(matcher, 'ensure_user_profile'), \
             patch.object(matcher, 'check_existing_pending_match', return_value=None), \
             patch.object(matcher, 'find_best_candidate', return_value='candidate-789'), \
             patch.object(matcher, 'create_match_record', return_value=mock_match_record), \
             patch.object(matcher, '_get_user_profile', return_value=mock_buddy_profile):
            
            result = await matcher.create_automatic_match(user_id, 25)
            
            assert result['success'] is True
            assert result['message'] == "Wingman buddy match created successfully!"
            assert result['match_id'] == 'new-match-456'
            assert result['buddy_user_id'] == 'candidate-789'

class TestRecencyFiltering:
    """Test recency filtering (7-day exclusion rule)"""
    
    @pytest.fixture
    def matcher(self):
        mock_client = MagicMock()
        return WingmanMatcher(mock_client)
    
    @pytest.mark.asyncio
    async def test_recent_pairing_excluded(self, matcher):
        """Test that users paired within last 7 days are excluded"""
        user_id = "test-user"
        
        user_profile = {
            'id': user_id,
            'experience_level': 'intermediate',
            'first_name': 'Test',
            'confidence_archetype': 'Analyzer'
        }
        
        candidates = [
            BuddyCandidate(
                user_id="recent-buddy",
                city="San Francisco",
                distance_miles=5.0,
                experience_level="intermediate",
                confidence_archetype="Naturalist"
            ),
            BuddyCandidate(
                user_id="old-buddy",
                city="Oakland",
                distance_miles=10.0,
                experience_level="intermediate",
                confidence_archetype="Scholar"
            )
        ]
        
        # Mock recent pairing check - first candidate was recent, second was not
        async def mock_recent_check(user1, user2, cutoff):
            return user2 == "recent-buddy"  # Only recent-buddy was recently paired
        
        with patch.object(matcher, '_get_user_profile', return_value=user_profile), \
             patch.object(matcher, '_check_recent_pairing', side_effect=mock_recent_check), \
             patch('services.wingman_matcher.find_candidates_within_radius', return_value=candidates):
            
            result = await matcher.find_best_candidate(user_id, 25)
            
            # Should select old-buddy (not recently paired)
            assert result == "old-buddy"
    
    @pytest.mark.asyncio
    async def test_all_recent_pairings_excluded(self, matcher):
        """Test when all candidates were recently paired"""
        user_id = "test-user"
        
        user_profile = {
            'id': user_id,
            'experience_level': 'intermediate',
            'first_name': 'Test',
            'confidence_archetype': 'Analyzer'
        }
        
        candidates = [
            BuddyCandidate(
                user_id="recent-buddy-1",
                city="San Francisco",
                distance_miles=5.0,
                experience_level="intermediate",
                confidence_archetype="Naturalist"
            ),
            BuddyCandidate(
                user_id="recent-buddy-2",
                city="Oakland",
                distance_miles=10.0,
                experience_level="intermediate",
                confidence_archetype="Scholar"
            )
        ]
        
        with patch.object(matcher, '_get_user_profile', return_value=user_profile), \
             patch.object(matcher, '_check_recent_pairing', return_value=True), \
             patch('services.wingman_matcher.find_candidates_within_radius', return_value=candidates):
            
            result = await matcher.find_best_candidate(user_id, 25)
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_recency_cutoff_calculation(self, matcher):
        """Test that 7-day cutoff is calculated correctly"""
        user_id = "test-user"
        
        # Mock the recent pairing check to capture the cutoff date
        captured_cutoff = None
        
        async def mock_recent_check(user1, user2, cutoff):
            nonlocal captured_cutoff
            captured_cutoff = cutoff
            return False
        
        user_profile = {
            'id': user_id,
            'experience_level': 'intermediate',
            'first_name': 'Test',
            'confidence_archetype': 'Analyzer'
        }
        
        candidates = [
            BuddyCandidate(
                user_id="buddy",
                city="San Francisco",
                distance_miles=5.0,
                experience_level="intermediate",
                confidence_archetype="Naturalist"
            )
        ]
        
        with patch.object(matcher, '_get_user_profile', return_value=user_profile), \
             patch.object(matcher, '_check_recent_pairing', side_effect=mock_recent_check), \
             patch('services.wingman_matcher.find_candidates_within_radius', return_value=candidates):
            
            await matcher.find_best_candidate(user_id, 25)
            
            # Verify cutoff is approximately 7 days ago
            now = datetime.now(timezone.utc)
            expected_cutoff = now - timedelta(days=7)
            assert captured_cutoff is not None
            time_diff = abs((captured_cutoff - expected_cutoff).total_seconds())
            assert time_diff < 60  # Within 1 minute tolerance

class TestDeterministicSelection:
    """Test deterministic selection with fixed candidate pools"""
    
    @pytest.fixture
    def matcher(self):
        mock_client = MagicMock()
        return WingmanMatcher(mock_client)
    
    @pytest.fixture
    def fixed_candidates(self):
        """Fixed set of candidates for deterministic testing"""
        return [
            BuddyCandidate(
                user_id="candidate-far",
                city="San Jose",
                distance_miles=30.0,
                experience_level="intermediate",
                confidence_archetype="Naturalist"
            ),
            BuddyCandidate(
                user_id="candidate-close",
                city="Oakland",
                distance_miles=10.0,
                experience_level="intermediate",
                confidence_archetype="Analyzer"
            ),
            BuddyCandidate(
                user_id="candidate-medium",
                city="Berkeley",
                distance_miles=20.0,
                experience_level="intermediate",
                confidence_archetype="Scholar"
            )
        ]
    
    @pytest.mark.asyncio
    async def test_closest_distance_selected_first(self, matcher, fixed_candidates):
        """Test that closest distance candidate is selected first"""
        user_id = "test-user"
        
        user_profile = {
            'id': user_id,
            'experience_level': 'intermediate',
            'first_name': 'Test',
            'confidence_archetype': 'Analyzer'
        }
        
        with patch.object(matcher, '_get_user_profile', return_value=user_profile), \
             patch.object(matcher, '_check_recent_pairing', return_value=False), \
             patch('services.wingman_matcher.find_candidates_within_radius', return_value=fixed_candidates):
            
            result = await matcher.find_best_candidate(user_id, 35)
            
            # Should select candidate-close (10.0 miles - closest)
            assert result == "candidate-close"
    
    @pytest.mark.asyncio
    async def test_deterministic_with_identical_candidates(self, matcher):
        """Test deterministic selection when candidates are identical"""
        user_id = "test-user"
        
        user_profile = {
            'id': user_id,
            'experience_level': 'intermediate',
            'first_name': 'Test',
            'confidence_archetype': 'Analyzer'
        }
        
        # Two identical candidates (same distance, experience, etc.)
        identical_candidates = [
            BuddyCandidate(
                user_id="candidate-a",
                city="San Francisco",
                distance_miles=15.0,
                experience_level="intermediate",
                confidence_archetype="Naturalist"
            ),
            BuddyCandidate(
                user_id="candidate-b",
                city="San Francisco",
                distance_miles=15.0,
                experience_level="intermediate",
                confidence_archetype="Naturalist"
            )
        ]
        
        with patch.object(matcher, '_get_user_profile', return_value=user_profile), \
             patch.object(matcher, '_check_recent_pairing', return_value=False), \
             patch('services.wingman_matcher.find_candidates_within_radius', return_value=identical_candidates):
            
            # Run multiple times to ensure deterministic result
            results = []
            for _ in range(3):
                result = await matcher.find_best_candidate(user_id, 25)
                results.append(result)
            
            # All results should be the same (deterministic)
            assert all(r == results[0] for r in results)
            # Should pick first candidate in list (candidate-a)
            assert results[0] == "candidate-a"

class TestAutoDependencyCreation:
    """Test auto-dependency creation for user profiles"""
    
    @pytest.fixture
    def matcher(self):
        mock_client = MagicMock()
        return WingmanMatcher(mock_client)
    
    @pytest.mark.asyncio
    async def test_ensure_user_profile_creates_missing_profile(self, matcher):
        """Test that missing user profile is created automatically"""
        user_id = "new-user-123"
        
        # Mock Supabase responses
        matcher.supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
        matcher.supabase.table.return_value.insert.return_value.execute.return_value = MagicMock()
        
        await matcher.ensure_user_profile(user_id)
        
        # Verify profile creation was attempted
        matcher.supabase.table.assert_called()
        insert_call = None
        for call in matcher.supabase.table.return_value.insert.call_args_list:
            if call[0]:  # Check if insert was called with data
                insert_call = call[0][0]
                break
        
        assert insert_call is not None
        assert insert_call['id'] == user_id
        assert insert_call['experience_level'] == 'beginner'
        assert insert_call['confidence_archetype'] == 'Naturalist'
    
    @pytest.mark.asyncio
    async def test_ensure_user_profile_skips_existing_profile(self, matcher):
        """Test that existing user profile is not recreated"""
        user_id = "existing-user-456"
        
        # Mock existing profile
        existing_profile = {'id': user_id, 'first_name': 'Existing'}
        matcher.supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [existing_profile]
        
        await matcher.ensure_user_profile(user_id)
        
        # Verify insert was not called
        matcher.supabase.table.return_value.insert.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_auto_dependency_creation_in_match_flow(self, matcher):
        """Test auto-dependency creation is called during match creation"""
        user_id = "test-user"
        
        with patch.object(matcher, 'ensure_user_profile') as mock_ensure, \
             patch.object(matcher, 'check_existing_pending_match', return_value=None), \
             patch.object(matcher, 'find_best_candidate', return_value=None):
            
            await matcher.create_automatic_match(user_id, 25)
            
            # Verify ensure_user_profile was called
            mock_ensure.assert_called_once_with(user_id)

class TestErrorHandling:
    """Test error handling for edge cases"""
    
    @pytest.fixture
    def matcher(self):
        mock_client = MagicMock()
        return WingmanMatcher(mock_client)
    
    @pytest.mark.asyncio
    async def test_empty_candidate_pool(self, matcher):
        """Test handling when no candidates are found"""
        user_id = "isolated-user"
        
        with patch.object(matcher, 'ensure_user_profile'), \
             patch.object(matcher, 'check_existing_pending_match', return_value=None), \
             patch.object(matcher, 'find_best_candidate', return_value=None):
            
            result = await matcher.create_automatic_match(user_id, 25)
            
            assert result['success'] is False
            assert "No compatible wingman buddies found" in result['message']
            assert result['match_id'] is None
            assert result['buddy_user_id'] is None
    
    @pytest.mark.asyncio
    async def test_invalid_user_profile(self, matcher):
        """Test handling when user has invalid/incomplete profile"""
        user_id = "invalid-user"
        
        user_profile = None  # No profile found
        
        with patch.object(matcher, '_get_user_profile', return_value=user_profile), \
             patch('services.wingman_matcher.find_candidates_within_radius', return_value=[]):
            
            result = await matcher.find_best_candidate(user_id, 25)
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_database_error_handling(self, matcher):
        """Test graceful handling of database errors"""
        user_id = "test-user"
        
        with patch.object(matcher, 'ensure_user_profile'), \
             patch.object(matcher, 'check_existing_pending_match', side_effect=Exception("Database error")):
            
            result = await matcher.create_automatic_match(user_id, 25)
            
            assert result['success'] is False
            assert "Unable to create wingman match" in result['message']
    
    @pytest.mark.asyncio
    async def test_match_creation_failure(self, matcher):
        """Test handling when match record creation fails"""
        user_id = "test-user"
        candidate_id = "candidate-user"
        
        with patch.object(matcher, 'ensure_user_profile'), \
             patch.object(matcher, 'check_existing_pending_match', return_value=None), \
             patch.object(matcher, 'find_best_candidate', return_value=candidate_id), \
             patch.object(matcher, 'create_match_record', side_effect=Exception("Match creation failed")):
            
            result = await matcher.create_automatic_match(user_id, 25)
            
            assert result['success'] is False
            assert "Unable to create wingman match" in result['message']

class TestMatchRecordOperations:
    """Test match record creation and management"""
    
    @pytest.fixture
    def matcher(self):
        mock_client = MagicMock()
        return WingmanMatcher(mock_client)
    
    @pytest.mark.asyncio
    async def test_deterministic_user_ordering(self, matcher):
        """Test that users are ordered deterministically in match records"""
        user1_id = "user-zebra"
        user2_id = "user-alpha"
        
        # Mock database responses
        matcher.supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.eq.return_value.execute.return_value.data = []
        
        mock_match = {
            'id': 'match-123',
            'user1_id': 'user-alpha',  # Should be ordered alphabetically
            'user2_id': 'user-zebra',
            'status': 'pending'
        }
        matcher.supabase.table.return_value.insert.return_value.execute.return_value.data = [mock_match]
        
        result = await matcher.create_match_record(user1_id, user2_id)
        
        # Verify users were ordered alphabetically
        insert_call = matcher.supabase.table.return_value.insert.call_args[0][0]
        assert insert_call['user1_id'] == 'user-alpha'
        assert insert_call['user2_id'] == 'user-zebra'
    
    @pytest.mark.asyncio
    async def test_duplicate_match_prevention(self, matcher):
        """Test prevention of duplicate match records"""
        user1_id = "user-a"
        user2_id = "user-b"
        
        # Mock existing match
        existing_match = {
            'id': 'existing-match-456',
            'user1_id': user1_id,
            'user2_id': user2_id,
            'status': 'pending'
        }
        matcher.supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.eq.return_value.execute.return_value.data = [existing_match]
        
        result = await matcher.create_match_record(user1_id, user2_id)
        
        # Should return existing match, not create new one
        assert result == existing_match
        matcher.supabase.table.return_value.insert.assert_not_called()

if __name__ == "__main__":
    # Run tests with pytest
    import pytest
    pytest.main([__file__, "-v", "--tb=short", "-s"])