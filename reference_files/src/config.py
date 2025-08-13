import os
from typing import List, Optional
from dotenv import load_dotenv

# Only load .env in development
if os.getenv('ENVIRONMENT') != 'production':
    load_dotenv()

class ConfigurationError(Exception):
    """Custom exception for configuration errors"""
    pass

class Config:
    # API Configurations
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY")
    
    # DEPRECATED: Use model_selector.py for intelligent model selection
    # This is kept for backward compatibility only
    ANTHROPIC_MODEL: str = "claude-3-5-sonnet-20241022"
    
    # Cost Optimization: Model selection by operation type
    # These can be overridden via environment variables
    CHAT_MODEL: str = os.getenv("CHAT_MODEL", "claude-3-opus-20240229")  # Claude 4 for chat
    BACKGROUND_MODEL: str = os.getenv("BACKGROUND_MODEL", "claude-3-haiku-20240307")  # Haiku for background
    TEST_MODEL: str = os.getenv("TEST_MODEL", "claude-3-haiku-20240307")  # Always cheap for testing
    
    # Development overrides
    DEV_MODEL: str = os.getenv("DEV_MODEL", "claude-3-haiku-20240307")  # Cheap for local dev
    DEV_CHAT_MODEL: str = os.getenv("DEV_CHAT_MODEL", "claude-3-haiku-20240307")  # Cheap for dev chat testing
    
    # Cost optimization flags
    ENABLE_COST_OPTIMIZATION: bool = os.getenv("ENABLE_COST_OPTIMIZATION", "true").lower() in ("true", "1", "yes")
    DEVELOPMENT_MODE: bool = os.getenv("DEVELOPMENT_MODE", "false").lower() in ("true", "1", "yes")
    FORCE_TESTING_MODE: bool = os.getenv("FORCE_TESTING_MODE", "false").lower() in ("true", "1", "yes")
    
    # Zoom Configuration
    ZOOM_ACCOUNT_ID: str = os.getenv("ACCOUNT_ID")
    ZOOM_CLIENT_ID: str = os.getenv("CLIENT_ID")
    ZOOM_CLIENT_SECRET: str = os.getenv("CLIENT_SECRET")
    ZOOM_SECRET_TOKEN: str = os.getenv("SECRET_TOKEN")
    ZOOM_RETURNED_TOKEN: str = os.getenv("RETURNED_TOKEN")
    ZOOM_API_URL: str = os.getenv("ZOOM_API_URL", "https://api.zoom.us/v2")

    # Supabase Configuration
    SUPABASE_REFERENCE_ID: str = os.getenv("SUPABASE_REFERENCE_ID")
    SUPABASE_URL: str = os.getenv("SUPABASE_URL")
    SUPABASE_ANON_KEY: str = os.getenv("SUPABASE_ANON_KEY")
    SUPABASE_SERVICE_KEY: str = os.getenv("SUPABASE_SERVICE_KEY")

    # Slack Configuration
    SLACK_BOT_TOKEN: str = os.getenv("SLACK_BOT_TOKEN")
    SLACK_SIGNING_SECRET: str = os.getenv("SLACK_SIGNING_SECRET")
    SLACK_CLIENT_ID = os.getenv('SLACK_CLIENT_ID')
    SLACK_CLIENT_SECRET = os.getenv('SLACK_CLIENT_SECRET')
    SLACK_CALLBACK_URL = os.getenv('SLACK_CALLBACK_URL')  # Will be set by the workflow
    
    # OpenAI Configuration
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY")

    #google cloud - anthropic - vertex
    VERTEX_PROJECT_ID: str = os.getenv("VERTEX_PROJECT_ID")
    VERTEX_LOCATION: str = os.getenv("VERTEX_LOCATION", "us-east5")  # Default to us-east5

    #langsmith
    LANGCHAIN_API_KEY = os.getenv("LANGCHAIN_API_KEY")
    LANGCHAIN_PROJECT = os.getenv("LANGCHAIN_PROJECT")
    LANGCHAIN_ENDPOINT = os.getenv("LANGCHAIN_ENDPOINT")
    LANGCHAIN_TRACING_V2 = os.getenv("LANGCHAIN_TRACING_V2")
    
    # Feature Flags
    ENABLE_ONBOARDING: bool = os.getenv("ENABLE_ONBOARDING", "True").lower() in ("true", "1", "yes")
    ENABLE_DETAILED_LOGGING: bool = os.getenv("ENABLE_DETAILED_LOGGING", "False").lower() in ("true", "1", "yes")
    ENABLE_EXPERIMENTAL_FEATURES: bool = os.getenv("ENABLE_EXPERIMENTAL_FEATURES", "False").lower() in ("true", "1", "yes")
    
    # Resend Email API
    RESEND_API_KEY: str = os.getenv("RESEND_API_KEY")
    
    @classmethod
    def get_required_vars(cls) -> List[str]:
        """Returns list of required environment variables"""
        return [
            "SUPABASE_URL",
            "SUPABASE_SERVICE_KEY",
            "OPENAI_API_KEY",
            "ZOOM_ACCOUNT_ID",
            "ZOOM_CLIENT_ID",
            "ZOOM_CLIENT_SECRET"
        ]

    @classmethod
    def validate_config(cls) -> None:
        """
        Validates all required configuration variables are set.
        Raises ConfigurationError if any required variables are missing.
        """
        missing_vars = [var for var in cls.get_required_vars() 
                       if not getattr(cls, var)]
        
        if missing_vars:
            raise ConfigurationError(
                "Missing required environment variables: "
                f"{', '.join(missing_vars)}"
            )

    @classmethod
    def get_environment(cls) -> str:
        """Returns the current environment (development/production)"""
        return os.getenv('ENVIRONMENT', 'development')
    
    @classmethod
    def get_app_identifier(cls) -> str:
        """Returns app identifier for logging"""
        env = cls.get_environment()
        return f"fridays-at-four-{env}"
    
    @classmethod
    def get_model_info(cls) -> dict:
        """Get current model configuration for debugging"""
        return {
            "legacy_model": cls.ANTHROPIC_MODEL,
            "chat_model": cls.CHAT_MODEL,
            "background_model": cls.BACKGROUND_MODEL,
            "test_model": cls.TEST_MODEL,
            "dev_model": cls.DEV_MODEL,
            "dev_chat_model": cls.DEV_CHAT_MODEL,
            "cost_optimization_enabled": cls.ENABLE_COST_OPTIMIZATION,
            "development_mode": cls.DEVELOPMENT_MODE,
            "force_testing_mode": cls.FORCE_TESTING_MODE
        }

# Validate configuration on import
Config.validate_config()