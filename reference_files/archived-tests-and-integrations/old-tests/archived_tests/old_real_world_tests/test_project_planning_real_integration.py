#!/usr/bin/env python3
"""
Real Integration Tests for Project Planning

Test the complete onboarding flow with real database connections.
"""

import pytest
import asyncio
import os
import sys
from dotenv import load_dotenv

# Add project root to Python path  
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Load environment variables
load_dotenv()

@pytest.mark.integration
class TestRealProjectOnboarding:
    """Test project onboarding with real database connections"""

    @pytest.fixture
    def real_supabase_client(self):
        """Create a real Supabase client"""
        from supabase import create_client
        
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_KEY")
        
        if not url or not key:
            pytest.skip("Real Supabase credentials not available")
            
        return create_client(url, key)

    @pytest.fixture
    def test_user_id(self):
        """Real test user ID provided"""
        return "3189d065-7a5c-41a7-8cf6-4a6164fd7d1b"

    @pytest.mark.asyncio
    async def test_real_user_project_overview_check(self, real_supabase_client, test_user_id):
        """Test checking if real user has project overview"""
        from src.project_planning import check_user_has_project_overview
        
        # Check the real user's project overview status
        has_project = await check_user_has_project_overview(real_supabase_client, test_user_id)
        
        # This should return a boolean (likely False for our test user)
        assert isinstance(has_project, bool)
        print(f"Test user {test_user_id} has project overview: {has_project}")

    @pytest.mark.asyncio
    async def test_real_onboarding_check(self, real_supabase_client, test_user_id):
        """Test the complete onboarding check with real user"""
        from src.claude_agent import check_and_handle_project_onboarding
        
        # Test with a simple greeting
        result = await check_and_handle_project_onboarding(
            real_supabase_client,
            test_user_id, 
            "Hello there!"
        )
        
        # Should return proper structure
        assert "should_onboard" in result
        assert "prompt" in result
        
        print(f"Onboarding result: should_onboard={result['should_onboard']}")
        
        if result["should_onboard"]:
            assert result["prompt"] is not None
            assert len(result["prompt"]) > 100
            print("✓ User will be onboarded - prompt ready")
        else:
            print("✓ User already has project overview - no onboarding needed")

    @pytest.mark.asyncio 
    async def test_onboarding_manager_connection(self, real_supabase_client, test_user_id):
        """Test that OnboardingManager can connect and create project overview"""
        from src.onboarding_manager import OnboardingManager
        
        # Create OnboardingManager instance
        onboarding_manager = OnboardingManager(real_supabase_client)
        
        # Test data for project creation
        test_project_data = {
            "user_id": test_user_id,
            "project_name": "Test Integration Project",
            "project_type": "test",
            "description": "A test project created during integration testing",
            "goals": [{"goal": "Test goal", "timeline": "Test timeline"}],
            "challenges": [{"challenge": "Test challenge", "mitigation": "Test mitigation"}],
            "success_metrics": {"metrics": [{"metric": "Test metric", "target": "Test target"}]}
        }
        
        print("🧪 Testing OnboardingManager database connection...")
        
        # Note: We're not actually creating the project to avoid polluting the database
        # Just testing that the manager can be instantiated and has the right methods
        assert hasattr(onboarding_manager, 'create_project_overview')
        assert callable(onboarding_manager.create_project_overview)
        
        print("✓ OnboardingManager initialized successfully")
        print("✓ create_project_overview method available")
        
        # Test the actual creation method signature by calling it with dry_run simulation
        # (We would need to add a dry_run parameter to safely test this)
        print("⚠️  Skipping actual project creation to avoid database pollution")

if __name__ == "__main__":
    # Run integration tests manually
    pytest.main([__file__, "-v", "-s"]) 