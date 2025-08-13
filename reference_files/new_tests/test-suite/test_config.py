#!/usr/bin/env python3
"""
Test Configuration for DB-Driven Agent System
Configures environment, database, and API settings for comprehensive testing
"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv
from typing import Dict

# Add project root to Python path for src imports
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Load test environment variables
load_dotenv(".env")

class TestConfig:
    """Test configuration for DB-driven agent system"""
    
    # Environment settings
    TEST_ENV = os.getenv("TEST_ENV", "development")
    
    # Database configuration
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    # Test database aliases (same as main database for testing)
    TEST_DB_URL = os.getenv("SUPABASE_URL")
    TEST_DB_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    # API Keys for LLM Router
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    
    # Model configuration
    # COST OPTIMIZATION: Always use Haiku for testing (90% cost reduction)
    ANTHROPIC_MODEL = "claude-3-haiku-20240307"  # Changed from expensive Sonnet to cheap Haiku
    
    # Test user configuration
    TEST_USER_PREFIX = "test_db_agent_"
    DEFAULT_THREAD_ID = "test_thread_default"
    
    # Performance expectations for DB-driven system
    EXPECTED_FLOW_STATE_QUERY_TIME_MS = 200  # Max 200ms for flow state queries
    EXPECTED_TOTAL_RESPONSE_TIME_MS = 5000   # Max 5s for complete response
    EXPECTED_API_CALLS_PER_MESSAGE = 1       # Should be exactly 1 API call per message
    
    # Directory paths
    ROOT_DIR = Path(project_root)
    TEST_DATA_DIR = Path(__file__).parent / 'test_data'
    
    @classmethod
    def validate_config(cls) -> None:
        """Validate that all required configuration is present"""
        required_vars = [
            "SUPABASE_URL",
            "SUPABASE_SERVICE_ROLE_KEY",
            "ANTHROPIC_API_KEY"
        ]
        
        missing = [var for var in required_vars if not os.getenv(var)]
        if missing:
            raise ValueError(
                f"Missing required test configuration: {', '.join(missing)}\n"
                "Please ensure all variables are set in .env file"
            )
    
    @classmethod
    def get_test_user_id(cls, suffix: str = "") -> str:
        """Generate unique test user ID"""
        import uuid
        test_id = f"{cls.TEST_USER_PREFIX}{uuid.uuid4()}"
        if suffix:
            test_id += f"_{suffix}"
        return test_id
    
    @classmethod
    def get_performance_thresholds(cls) -> Dict[str, float]:
        """Get performance expectations for validation"""
        return {
            "flow_state_query_ms": cls.EXPECTED_FLOW_STATE_QUERY_TIME_MS,
            "total_response_ms": cls.EXPECTED_TOTAL_RESPONSE_TIME_MS,
            "api_calls_per_message": cls.EXPECTED_API_CALLS_PER_MESSAGE
        }

# Environment configurations for real-world tests
ENVIRONMENTS = {
    "dev": {
        "api_url": "https://fridays-at-four-dev-434b1a68908b.herokuapp.com",
        "name": "Development"
    },
    "prod": {
        "api_url": "https://fridays-at-four-c9c6b7a513be.herokuapp.com", 
        "name": "Production"
    },
    "local": {
        "api_url": "http://localhost:8000",
        "name": "Local Development"
    }
}

# Note: Validation is available via TestConfig.validate_config() but not run automatically
# This allows tests to run even in environments without full configuration