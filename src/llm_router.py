#!/usr/bin/env python3
"""
LLM Router for WingmanMatch

Handles model selection and routing for different use cases.
Optimizes cost and performance for dating confidence coaching.
"""

import logging
from typing import Optional, Dict, Any
from enum import Enum

from src.config import Config

logger = logging.getLogger(__name__)

class ModelTier(Enum):
    """Model performance tiers"""
    PREMIUM = "premium"      # Best quality for coaching conversations
    STANDARD = "standard"    # Good quality for general use
    ECONOMY = "economy"      # Cost-effective for background tasks

class UsageContext(Enum):
    """Different usage contexts for model selection"""
    COACHING_CHAT = "coaching_chat"           # Main coaching conversations
    ASSESSMENT = "assessment"                 # Confidence assessments
    SUMMARIZATION = "summarization"           # Session summaries
    BACKGROUND_TASK = "background_task"       # Background processing
    DEVELOPMENT = "development"               # Development and testing
    HEALTH_CHECK = "health_check"             # System health checks

class LLMRouter:
    """Routes requests to appropriate language models based on context and configuration"""
    
    # Model configurations
    MODEL_CONFIG = {
        ModelTier.PREMIUM: {
            "anthropic": "claude-3-5-sonnet-20241022",
            "openai": "gpt-4o",
            "temperature": 0.7,
            "max_tokens": 2048,
            "top_p": 0.9
        },
        ModelTier.STANDARD: {
            "anthropic": "claude-3-haiku-20240307", 
            "openai": "gpt-4o-mini",
            "temperature": 0.6,
            "max_tokens": 1024,
            "top_p": 0.8
        },
        ModelTier.ECONOMY: {
            "anthropic": "claude-3-haiku-20240307",
            "openai": "gpt-4o-mini", 
            "temperature": 0.5,
            "max_tokens": 512,
            "top_p": 0.7
        }
    }
    
    # Context to tier mapping
    CONTEXT_TIER_MAP = {
        UsageContext.COACHING_CHAT: ModelTier.PREMIUM,
        UsageContext.ASSESSMENT: ModelTier.PREMIUM,
        UsageContext.SUMMARIZATION: ModelTier.STANDARD,
        UsageContext.BACKGROUND_TASK: ModelTier.ECONOMY,
        UsageContext.DEVELOPMENT: ModelTier.ECONOMY,
        UsageContext.HEALTH_CHECK: ModelTier.ECONOMY
    }
    
    def __init__(self):
        self.primary_provider = "anthropic"  # WingmanMatch uses Claude primarily
        self.fallback_provider = "openai"    # GPT as fallback
        
    def get_model_for_context(self, context: UsageContext, override_tier: Optional[ModelTier] = None) -> Dict[str, Any]:
        """
        Get the appropriate model configuration for a given context
        
        Args:
            context: The usage context
            override_tier: Optional tier override
            
        Returns:
            Dictionary with model configuration
        """
        try:
            # Apply configuration overrides
            if Config.DEVELOPMENT_MODE:
                tier = ModelTier.ECONOMY
                provider = self.primary_provider
            elif Config.FORCE_TESTING_MODE:
                tier = ModelTier.ECONOMY
                provider = self.primary_provider
            elif override_tier:
                tier = override_tier
                provider = self.primary_provider
            else:
                tier = self.CONTEXT_TIER_MAP.get(context, ModelTier.STANDARD)
                provider = self.primary_provider
                
                # Apply cost optimization if enabled
                if Config.ENABLE_COST_OPTIMIZATION and context != UsageContext.COACHING_CHAT:
                    tier = ModelTier.ECONOMY
            
            model_config = self.MODEL_CONFIG[tier].copy()
            model_name = model_config[provider]
            
            result = {
                "model": model_name,
                "provider": provider,
                "tier": tier.value,
                "context": context.value,
                "temperature": model_config["temperature"],
                "max_tokens": model_config["max_tokens"],
                "top_p": model_config["top_p"]
            }
            
            logger.info(f"Selected model {model_name} ({tier.value}) for context {context.value}")
            return result
            
        except Exception as e:
            logger.error(f"Error selecting model for context {context}: {e}")
            # Return safe default
            return {
                "model": "claude-3-haiku-20240307",
                "provider": "anthropic",
                "tier": "economy",
                "context": context.value,
                "temperature": 0.6,
                "max_tokens": 1024,
                "top_p": 0.8
            }
    
    def get_coaching_model(self) -> Dict[str, Any]:
        """Get model configuration for coaching conversations"""
        return self.get_model_for_context(UsageContext.COACHING_CHAT)
    
    def get_assessment_model(self) -> Dict[str, Any]:
        """Get model configuration for confidence assessments"""
        return self.get_model_for_context(UsageContext.ASSESSMENT)
    
    def get_summarization_model(self) -> Dict[str, Any]:
        """Get model configuration for session summarization"""
        return self.get_model_for_context(UsageContext.SUMMARIZATION)
    
    def get_background_model(self) -> Dict[str, Any]:
        """Get model configuration for background tasks"""
        return self.get_model_for_context(UsageContext.BACKGROUND_TASK)
    
    def get_development_model(self) -> Dict[str, Any]:
        """Get model configuration for development/testing"""
        return self.get_model_for_context(UsageContext.DEVELOPMENT)
    
    def get_fallback_model(self) -> Dict[str, Any]:
        """Get fallback model configuration when primary fails"""
        model_config = self.MODEL_CONFIG[ModelTier.STANDARD].copy()
        fallback_model = model_config[self.fallback_provider]
        
        return {
            "model": fallback_model,
            "provider": self.fallback_provider,
            "tier": "standard",
            "context": "fallback",
            "temperature": model_config["temperature"],
            "max_tokens": model_config["max_tokens"],
            "top_p": model_config["top_p"]
        }
    
    def estimate_cost(self, context: UsageContext, tokens: int) -> Dict[str, Any]:
        """
        Estimate cost for a request based on context and token count
        
        Args:
            context: Usage context
            tokens: Estimated token count
            
        Returns:
            Cost estimation dictionary
        """
        try:
            model_config = self.get_model_for_context(context)
            model = model_config["model"]
            tier = model_config["tier"]
            
            # Simplified cost estimation (rough Claude pricing)
            cost_per_1k = {
                ModelTier.PREMIUM: 0.015,  # Claude 3.5 Sonnet
                ModelTier.STANDARD: 0.0025,  # Claude 3 Haiku
                ModelTier.ECONOMY: 0.0025   # Claude 3 Haiku
            }
            
            tier_enum = ModelTier(tier)
            estimated_cost = (tokens / 1000) * cost_per_1k.get(tier_enum, 0.005)
            
            return {
                "model": model,
                "tier": tier,
                "estimated_tokens": tokens,
                "estimated_cost_usd": round(estimated_cost, 6),
                "cost_per_1k_tokens": cost_per_1k.get(tier_enum, 0.005)
            }
            
        except Exception as e:
            logger.error(f"Error estimating cost: {e}")
            return {
                "model": "unknown",
                "tier": "unknown", 
                "estimated_tokens": tokens,
                "estimated_cost_usd": 0.0,
                "cost_per_1k_tokens": 0.0
            }
    
    def get_model_status(self) -> Dict[str, Any]:
        """Get current model routing status and configuration"""
        return {
            "primary_provider": self.primary_provider,
            "fallback_provider": self.fallback_provider,
            "development_mode": Config.DEVELOPMENT_MODE,
            "cost_optimization_enabled": Config.ENABLE_COST_OPTIMIZATION,
            "force_testing_mode": Config.FORCE_TESTING_MODE,
            "available_contexts": [context.value for context in UsageContext],
            "available_tiers": [tier.value for tier in ModelTier],
            "current_models": {
                "coaching": self.get_coaching_model()["model"],
                "assessment": self.get_assessment_model()["model"],
                "summarization": self.get_summarization_model()["model"],
                "background": self.get_background_model()["model"]
            }
        }

# Global router instance
llm_router = LLMRouter()

# Convenience functions for common use cases
def get_coaching_model() -> str:
    """Get model name for coaching conversations"""
    return llm_router.get_coaching_model()["model"]

def get_coaching_config() -> Dict[str, Any]:
    """Get full model configuration for coaching"""
    return llm_router.get_coaching_model()

def get_model_for_context(context: str) -> str:
    """Get model name for a specific context string"""
    try:
        context_enum = UsageContext(context)
        return llm_router.get_model_for_context(context_enum)["model"]
    except ValueError:
        logger.warning(f"Unknown context '{context}', using standard model")
        return llm_router.get_model_for_context(UsageContext.COACHING_CHAT)["model"]

# Export for API integration
__all__ = [
    'LLMRouter',
    'ModelTier', 
    'UsageContext',
    'llm_router',
    'get_coaching_model',
    'get_coaching_config',
    'get_model_for_context'
]