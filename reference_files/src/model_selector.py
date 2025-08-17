#!/usr/bin/env python3
"""
Model Selector - Smart Claude model routing for cost optimization

This module provides intelligent model selection based on:
- Operation type (chat, summarization, analysis, testing)
- Environment (development, testing, production)
- Cost optimization settings

Cost Optimization Strategy:
- Chat Operations: Claude 4 (premium user experience)
- Summarization: Sonnet (quality matters for user-facing summaries)
- Background Operations: Haiku (90% cost reduction)
- Testing: Always Haiku (maximum cost savings during development)
"""

import os
import logging
from typing import Literal, Optional
from enum import Enum

logger = logging.getLogger(__name__)

# Operation types for model selection
OperationType = Literal['chat', 'summarization', 'analysis', 'testing', 'background']

class ModelTier(Enum):
    """Model tiers for different use cases"""
    PREMIUM = "claude-sonnet-4-20250514"  # Most expensive, highest quality
    STANDARD = "claude-sonnet-4-20250514"  # Good balance
    EFFICIENT = "claude-3-haiku-20240307"  # Cheapest, good for simple tasks
    CHAT_PREMIUM = "claude-3-opus-20240229"  # Updated to Claude 4 as requested

class Environment(Enum):
    """Environment types"""
    PRODUCTION = "production"
    DEVELOPMENT = "development" 
    TESTING = "testing"

class CostOptimizationLogger:
    """Track model usage and cost savings"""
    
    @staticmethod
    def log_model_selection(operation: str, model: str, reason: str):
        logger.info(f"🎯 Model Selection: {operation} -> {model} ({reason})")
    
    @staticmethod
    def log_cost_savings(operation: str, original_model: str, selected_model: str):
        if original_model != selected_model:
            logger.info(f"💰 Cost Optimization: {operation} using {selected_model} instead of {original_model}")

def detect_environment() -> Environment:
    """
    Auto-detect current runtime environment
    
    Returns:
        Environment enum value
    """
    # Check explicit environment override
    if os.getenv("FORCE_TESTING_MODE", "").lower() in ("true", "1", "yes"):
        return Environment.TESTING
    
    # Check if we're in pytest
    if 'pytest' in os.environ.get('_', '') or os.environ.get('PYTEST_CURRENT_TEST'):
        return Environment.TESTING
    
    # Check explicit environment setting first (highest priority)
    explicit_env = os.getenv('ENVIRONMENT', '').lower()
    if explicit_env == 'production':
        return Environment.PRODUCTION
    elif explicit_env == 'development':
        return Environment.DEVELOPMENT
    
    # Check for development indicators
    if os.getenv('DEVELOPMENT_MODE', '').lower() in ("true", "1", "yes"):
        return Environment.DEVELOPMENT
    
    # Check if running locally (common dev indicators)
    # NOTE: Only consider dev if explicitly set, not just because .env exists
    if any([
        os.getenv('LOCAL_DEVELOPMENT'),
        'localhost' in os.getenv('SUPABASE_URL', ''),
        'uvicorn' in ' '.join(os.environ.get('_', '').split())  # Running with uvicorn
    ]):
        return Environment.DEVELOPMENT
    
    # Default to production for safety
    return Environment.PRODUCTION

def is_testing_environment() -> bool:
    """Check if we're in testing environment"""
    return detect_environment() == Environment.TESTING

def is_development_environment() -> bool:
    """Check if we're in development environment"""
    return detect_environment() == Environment.DEVELOPMENT

def get_model_for_operation(
    operation_type: OperationType,
    override_model: Optional[str] = None,
    force_environment: Optional[Environment] = None
) -> str:
    """
    Smart model selection based on operation type and environment
    
    Args:
        operation_type: Type of operation needing a model
        override_model: Optional explicit model override
        force_environment: Optional environment override for testing
    
    Returns:
        Appropriate Claude model name for the operation
    """
    # Use override if provided
    if override_model:
        CostOptimizationLogger.log_model_selection(
            operation_type, override_model, "explicit override"
        )
        return override_model
    
    # Detect environment
    env = force_environment or detect_environment()
    
    # TESTING: Always use cheapest model for any testing
    if env == Environment.TESTING:
        model = ModelTier.EFFICIENT.value
        CostOptimizationLogger.log_model_selection(
            operation_type, model, "testing environment - cost optimization"
        )
        return model
    
    # DEVELOPMENT: Use cheap models unless overridden
    if env == Environment.DEVELOPMENT:
        # Allow dev override for chat testing, but default to cheap
        if operation_type == 'chat':
            model = os.getenv("DEV_CHAT_MODEL", ModelTier.EFFICIENT.value)
        else:
            model = os.getenv("DEV_MODEL", ModelTier.EFFICIENT.value)
        
        CostOptimizationLogger.log_model_selection(
            operation_type, model, "development environment - cost optimization"
        )
        return model
    
    # PRODUCTION: Smart model selection by operation type
    operation_models = {
        'chat': os.getenv("CHAT_MODEL", ModelTier.CHAT_PREMIUM.value),  # Claude 4 for chat
        'summarization': os.getenv("SUMMARIZATION_MODEL", ModelTier.STANDARD.value),  # Sonnet for quality summaries
        'analysis': os.getenv("BACKGROUND_MODEL", ModelTier.EFFICIENT.value),  # Haiku for analysis
        'testing': ModelTier.EFFICIENT.value,  # Always cheap for testing
        'background': os.getenv("BACKGROUND_MODEL", ModelTier.EFFICIENT.value)  # Haiku for background
    }
    
    selected_model = operation_models.get(operation_type, ModelTier.EFFICIENT.value)
    default_expensive = ModelTier.STANDARD.value
    
    # Log cost optimization
    CostOptimizationLogger.log_cost_savings(operation_type, default_expensive, selected_model)
    CostOptimizationLogger.log_model_selection(
        operation_type, selected_model, f"production - {operation_type} optimization"
    )
    
    return selected_model

def get_chat_model() -> str:
    """Get model for chat operations (premium experience)"""
    return get_model_for_operation('chat')

def get_summarization_model() -> str:
    """Get model for summarization operations (cost optimized)"""
    return get_model_for_operation('summarization')

def get_analysis_model() -> str:
    """Get model for analysis operations (cost optimized)"""  
    return get_model_for_operation('analysis')

def get_testing_model() -> str:
    """Get model for testing operations (always cheapest)"""
    return get_model_for_operation('testing')

def get_background_model() -> str:
    """Get model for background operations (cost optimized)"""
    return get_model_for_operation('background')

# Testing helper functions
def force_testing_mode():
    """Force testing mode for unit tests"""
    os.environ["FORCE_TESTING_MODE"] = "true"

def clear_testing_mode():
    """Clear forced testing mode"""
    os.environ.pop("FORCE_TESTING_MODE", None)

# Environment info for debugging
def get_environment_info() -> dict:
    """Get detailed environment information for debugging"""
    env = detect_environment()
    return {
        "detected_environment": env.value,
        "chat_model": get_chat_model(),
        "summarization_model": get_summarization_model(),
        "analysis_model": get_analysis_model(),
        "testing_model": get_testing_model(),
        "background_model": get_background_model(),
        "environment_variables": {
            "CHAT_MODEL": os.getenv("CHAT_MODEL"),
            "SUMMARIZATION_MODEL": os.getenv("SUMMARIZATION_MODEL"),
            "BACKGROUND_MODEL": os.getenv("BACKGROUND_MODEL"),
            "DEV_MODEL": os.getenv("DEV_MODEL"),
            "DEVELOPMENT_MODE": os.getenv("DEVELOPMENT_MODE"),
            "FORCE_TESTING_MODE": os.getenv("FORCE_TESTING_MODE"),
            "ENVIRONMENT": os.getenv("ENVIRONMENT")
        }
    }

if __name__ == "__main__":
    # Quick test/demo
    print("🎯 Model Selector Environment Info:")
    import json
    print(json.dumps(get_environment_info(), indent=2)) 