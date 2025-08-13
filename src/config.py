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
    
    # Model selection for WingmanMatch operations
    # Chat model for wingman conversations (premium for quality)
    CHAT_MODEL: str = os.getenv("CHAT_MODEL", "claude-3-5-sonnet-20241022")
    # Background model for data processing and summaries
    BACKGROUND_MODEL: str = os.getenv("BACKGROUND_MODEL", "claude-3-haiku-20240307")
    # Test model for development and testing
    TEST_MODEL: str = os.getenv("TEST_MODEL", "claude-3-haiku-20240307")
    
    # Development overrides
    DEV_MODEL: str = os.getenv("DEV_MODEL", "claude-3-haiku-20240307")
    DEV_CHAT_MODEL: str = os.getenv("DEV_CHAT_MODEL", "claude-3-haiku-20240307")
    
    # Cost optimization flags
    ENABLE_COST_OPTIMIZATION: bool = os.getenv("ENABLE_COST_OPTIMIZATION", "true").lower() in ("true", "1", "yes")
    DEVELOPMENT_MODE: bool = os.getenv("DEVELOPMENT_MODE", "false").lower() in ("true", "1", "yes")
    FORCE_TESTING_MODE: bool = os.getenv("FORCE_TESTING_MODE", "false").lower() in ("true", "1", "yes")

    # Supabase Configuration
    SUPABASE_URL: str = os.getenv("SUPABASE_URL")
    SUPABASE_ANON_KEY: str = os.getenv("SUPABASE_ANON_KEY")
    SUPABASE_SERVICE_KEY: str = os.getenv("SUPABASE_SERVICE_KEY")

    # Redis Configuration for session management
    REDIS_URL: str = os.getenv("REDIS_URL")
    REDIS_PASSWORD: str = os.getenv("REDIS_PASSWORD")
    
    # Email Configuration for match notifications
    RESEND_API_KEY: str = os.getenv("RESEND_API_KEY")
    
    # WingmanMatch Feature Flags
    ENABLE_MATCHING: bool = os.getenv("ENABLE_MATCHING", "true").lower() in ("true", "1", "yes")
    ENABLE_AI_COACHING: bool = os.getenv("ENABLE_AI_COACHING", "true").lower() in ("true", "1", "yes")
    ENABLE_CHALLENGE_SHARING: bool = os.getenv("ENABLE_CHALLENGE_SHARING", "true").lower() in ("true", "1", "yes")
    ENABLE_DETAILED_LOGGING: bool = os.getenv("ENABLE_DETAILED_LOGGING", "false").lower() in ("true", "1", "yes")
    
    # A/B Testing Flags for Coaching Persona
    ENABLE_NEW_COACH_PROMPTS: bool = os.getenv("ENABLE_NEW_COACH_PROMPTS", "true").lower() in ("true", "1", "yes")
    COACH_PERSONA_VERSION: str = os.getenv("COACH_PERSONA_VERSION", "connell_v1")  # connell_v1, hai_legacy, etc.
    ENABLE_EXPERIMENTAL_FEATURES: bool = os.getenv("ENABLE_EXPERIMENTAL_FEATURES", "false").lower() in ("true", "1", "yes")
    ENABLE_SAFETY_FILTERS: bool = os.getenv("ENABLE_SAFETY_FILTERS", "true").lower() in ("true", "1", "yes")
    ENABLE_CONTEXT_OPTIMIZATION: bool = os.getenv("ENABLE_CONTEXT_OPTIMIZATION", "true").lower() in ("true", "1", "yes")
    ENABLE_PROMPT_CACHING: bool = os.getenv("ENABLE_PROMPT_CACHING", "true").lower() in ("true", "1", "yes")
    ENABLE_AB_TESTING: bool = os.getenv("ENABLE_AB_TESTING", "false").lower() in ("true", "1", "yes")
    
    # Coaching Style A/B Testing
    COACHING_STYLE_VARIANT: str = os.getenv("COACHING_STYLE_VARIANT", "connell_barrett")  # connell_barrett, alternative, control
    AB_TEST_COHORT_PERCENTAGE: int = int(os.getenv("AB_TEST_COHORT_PERCENTAGE", "10"))  # Percentage of users in A/B test
    AB_TEST_SEED: str = os.getenv("AB_TEST_SEED", "wingman_2024")  # For consistent user assignment
    
    # WingmanMatch-specific configurations
    MAX_WINGMAN_MATCHES: int = int(os.getenv("MAX_WINGMAN_MATCHES", "5"))
    CHALLENGE_DURATION_DAYS: int = int(os.getenv("CHALLENGE_DURATION_DAYS", "30"))
    SESSION_TIMEOUT_HOURS: int = int(os.getenv("SESSION_TIMEOUT_HOURS", "24"))
    
    @classmethod
    def get_required_vars(cls) -> List[str]:
        """Returns list of required environment variables"""
        return [
            "ANTHROPIC_API_KEY",
            "SUPABASE_URL",
            "SUPABASE_SERVICE_KEY",
            "SUPABASE_ANON_KEY"
        ]

    @classmethod
    def get_optional_vars(cls) -> List[str]:
        """Returns list of optional environment variables"""
        return [
            "REDIS_URL",
            "RESEND_API_KEY"
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
    def validate_optional_config(cls) -> dict:
        """Returns status of optional configuration variables"""
        optional_status = {}
        for var in cls.get_optional_vars():
            optional_status[var] = bool(getattr(cls, var))
        return optional_status

    @classmethod
    def get_environment(cls) -> str:
        """Returns the current environment (development/production)"""
        return os.getenv('ENVIRONMENT', 'development')
    
    @classmethod
    def get_app_identifier(cls) -> str:
        """Returns app identifier for logging"""
        env = cls.get_environment()
        return f"wingman-match-{env}"
    
    @classmethod
    def get_model_info(cls) -> dict:
        """Get current model configuration for debugging"""
        return {
            "chat_model": cls.CHAT_MODEL,
            "background_model": cls.BACKGROUND_MODEL,
            "test_model": cls.TEST_MODEL,
            "dev_model": cls.DEV_MODEL,
            "dev_chat_model": cls.DEV_CHAT_MODEL,
            "cost_optimization_enabled": cls.ENABLE_COST_OPTIMIZATION,
            "development_mode": cls.DEVELOPMENT_MODE,
            "force_testing_mode": cls.FORCE_TESTING_MODE
        }

    @classmethod
    def get_feature_flags(cls) -> dict:
        """Get current feature flag configuration"""
        return {
            "matching_enabled": cls.ENABLE_MATCHING,
            "ai_coaching_enabled": cls.ENABLE_AI_COACHING,
            "challenge_sharing_enabled": cls.ENABLE_CHALLENGE_SHARING,
            "detailed_logging_enabled": cls.ENABLE_DETAILED_LOGGING,
            "experimental_features_enabled": cls.ENABLE_EXPERIMENTAL_FEATURES,
            "new_coach_prompts_enabled": cls.ENABLE_NEW_COACH_PROMPTS,
            "safety_filters_enabled": cls.ENABLE_SAFETY_FILTERS,
            "context_optimization_enabled": cls.ENABLE_CONTEXT_OPTIMIZATION,
            "prompt_caching_enabled": cls.ENABLE_PROMPT_CACHING,
            "ab_testing_enabled": cls.ENABLE_AB_TESTING
        }

    @classmethod
    def get_wingman_settings(cls) -> dict:
        """Get WingmanMatch-specific settings"""
        return {
            "max_wingman_matches": cls.MAX_WINGMAN_MATCHES,
            "challenge_duration_days": cls.CHALLENGE_DURATION_DAYS,
            "session_timeout_hours": cls.SESSION_TIMEOUT_HOURS
        }

    @classmethod
    def get_ab_testing_config(cls) -> dict:
        """Get A/B testing configuration"""
        return {
            "ab_testing_enabled": cls.ENABLE_AB_TESTING,
            "coaching_style_variant": cls.COACHING_STYLE_VARIANT,
            "cohort_percentage": cls.AB_TEST_COHORT_PERCENTAGE,
            "test_seed": cls.AB_TEST_SEED,
            "new_prompts_enabled": cls.ENABLE_NEW_COACH_PROMPTS
        }

    @classmethod
    def get_coaching_enhancements_config(cls) -> dict:
        """Get coaching system enhancement configuration"""
        return {
            "safety_filters_enabled": cls.ENABLE_SAFETY_FILTERS,
            "context_optimization_enabled": cls.ENABLE_CONTEXT_OPTIMIZATION,
            "prompt_caching_enabled": cls.ENABLE_PROMPT_CACHING,
            "new_coach_prompts_enabled": cls.ENABLE_NEW_COACH_PROMPTS
        }

# Validate required configuration on import
Config.validate_config()