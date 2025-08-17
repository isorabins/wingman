# this is a new test
# happy
# this is a tesT

"""
test_config.py
-------------
Test configuration and environment setup
"""

import sys
import os

# Add project root to Python path for src imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from pathlib import Path
from dotenv import load_dotenv
from typing import Dict

# Add root directory to Python path
# ROOT_DIR = Path('/Applications/fridays-at-four')
ROOT_DIR = Path("./")


# Load test environment variables
load_dotenv(".env.test")

class TestConfig:
    """Test configuration settings"""
    

    # Anthropic 
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY")
    # COST OPTIMIZATION: Always use Haiku for testing (90% cost reduction)
    ANTHROPIC_MODEL: str = "claude-3-haiku-20240307"  # Changed from expensive Sonnet to cheap Haiku

    # Test Environment
    TEST_ENV = os.getenv("TEST_ENV", "development")
    
    # Database configuration
    TEST_DB_URL = os.getenv("SUPABASE_URL")
    TEST_DB_KEY = os.getenv("SUPABASE_SERVICE_KEY")
    
    # Test user configuration (we'll keep these as is for now)
    TEST_USER_ID = "e4c932b7-1190-4463-818b-a804a644f01f"
    TEST_SLACK_ID = "U0873G42G7Q"
    TEST_EMAIL = "test@fridaysatfour.co"
    TEST_TEAM_ID = "1"
    
    # API Keys
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    
    # Zoom credentials
    ZOOM_CLIENT_ID = os.getenv("CLIENT_ID")
    ZOOM_CLIENT_SECRET = os.getenv("CLIENT_SECRET")
    ZOOM_ACCOUNT_ID = os.getenv("ACCOUNT_ID")
    
    # Slack credentials
    SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
    SLACK_CLIENT_ID = os.getenv("SLACK_CLIENT_ID")
    SLACK_SIGNING_SECRET = os.getenv("SLACK_SIGNING_SECRET")
    SLACK_CLIENT_SECRET = os.getenv('SLACK_CLIENT_SECRET')
    
    # LangSmith configuration
    LANGCHAIN_API_KEY = os.getenv("LANGCHAIN_API_KEY")
    LANGCHAIN_PROJECT = os.getenv("LANGCHAIN_PROJECT")
    LANGCHAIN_ENDPOINT = os.getenv("LANGCHAIN_ENDPOINT")
    LANGCHAIN_TRACING_V2 = os.getenv("LANGCHAIN_TRACING_V2", "true").lower() == "true"
    
    # Directory paths
    BASE_DIR = ROOT_DIR
    TEST_DATA_DIR = ROOT_DIR / 'test-suite' / 'test_data'
    TRANSCRIPT_DIR = TEST_DATA_DIR / 'transcripts_and_video'
    WEBHOOK_DIR = TEST_DATA_DIR / 'webhooks'
    
    # Sample files
    SAMPLE_TRANSCRIPT_FILE = TRANSCRIPT_DIR / 'sample_transcript.vtt'
    SAMPLE_VIDEO_FILE = TRANSCRIPT_DIR / 'sample_recording.mp4'
    
    @classmethod
    def validate_config(cls) -> None:
        """Validate that all required configuration is present"""
        required_vars = [
            "TEST_DB_URL",
            "TEST_DB_KEY",
            "OPENAI_API_KEY",
            "ZOOM_CLIENT_ID",
            "ZOOM_CLIENT_SECRET",
            "SLACK_BOT_TOKEN",
            "SLACK_SIGNING_SECRET",
            "LANGCHAIN_API_KEY"
        ]
        
        missing = [var for var in required_vars if not getattr(cls, var)]
        if missing:
            raise ValueError(
                f"Missing required test configuration: {', '.join(missing)}\n"
                "Please ensure all variables are set in .env.test"
            )
        
        # Validate test data directory
        if not cls.TEST_DATA_DIR.exists():
            raise ValueError(f"Test data directory not found: {cls.TEST_DATA_DIR}")
    
    @classmethod
    def get_test_user(cls) -> Dict[str, str]:
        """Get test user configuration"""
        return {
            "id": cls.TEST_USER_ID,
            "slack_id": cls.TEST_SLACK_ID,
            "email": cls.TEST_EMAIL,
            "team_id": cls.TEST_TEAM_ID
        }