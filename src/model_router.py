#!/usr/bin/env python3
"""
AI Model Router for WingmanMatch Performance Optimization

Implements intelligent model selection for cost-optimized Claude API usage.
Routes conversations to appropriate models based on content complexity and type.

Features:
- Content-based model routing (small talk vs coaching)
- Cost optimization with cheaper models for simple interactions
- Context analysis for conversation type detection
- Usage tracking and cost monitoring
- Fallback to premium models when needed
"""

import logging
import re
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger(__name__)

class ConversationType(Enum):
    """Types of conversations for model routing decisions"""
    GREETING = "greeting"
    SMALL_TALK = "small_talk"
    CONFIRMATION = "confirmation"
    DATING_COACHING = "dating_coaching"
    CONFIDENCE_ASSESSMENT = "confidence_assessment"
    CHALLENGE_GUIDANCE = "challenge_guidance"
    GOAL_SETTING = "goal_setting"
    EMOTIONAL_SUPPORT = "emotional_support"
    UNKNOWN = "unknown"

class ModelTier(Enum):
    """Model performance tiers for cost optimization"""
    ECONOMY = "economy"      # Cheapest - Haiku for simple responses
    STANDARD = "standard"    # Mid-tier - Sonnet for most interactions
    PREMIUM = "premium"      # Most expensive - Opus for complex analysis

@dataclass
class ModelRoutingDecision:
    """Result of model routing analysis"""
    model_name: str
    tier: ModelTier
    conversation_type: ConversationType
    confidence: float
    reasoning: str
    estimated_cost_factor: float

class ConversationClassifier:
    """
    Classifies conversation content to determine appropriate model routing.
    
    Uses pattern matching, keyword analysis, and context to identify
    conversation types for optimal model selection.
    """
    
    def __init__(self):
        # Conversation patterns for classification
        self.patterns = {
            ConversationType.GREETING: [
                r'\b(hi|hello|hey|good morning|good afternoon|good evening)\b',
                r'\b(what\'s up|howdy|greetings)\b',
                r'^(hi|hello|hey)[\s\.,!]*$'
            ],
            
            ConversationType.SMALL_TALK: [
                r'\b(how are you|how\'s it going|nice weather|busy day)\b',
                r'\b(what\'s new|anything interesting|how was your)\b',
                r'\b(weekend|monday|tuesday|wednesday|thursday|friday)\b'
            ],
            
            ConversationType.CONFIRMATION: [
                r'^(yes|no|ok|okay|sure|thanks|got it|understood)[\s\.,!]*$',
                r'\b(sounds good|makes sense|i see|alright)\b',
                r'^(y|n|yep|nope|yeah|nah)[\s\.,!]*$'
            ],
            
            ConversationType.DATING_COACHING: [
                r'\b(dating advice|how to ask|approach|conversation starter)\b',
                r'\b(first date|what to say|nervous about|dating tips)\b',
                r'\b(relationship|attraction|confidence|rejection)\b',
                r'\b(texting|messaging|online dating|dating app)\b'
            ],
            
            ConversationType.CONFIDENCE_ASSESSMENT: [
                r'\b(assessment|test|quiz|evaluate|analyze|score)\b',
                r'\b(confidence level|personality|archetype|profile)\b',
                r'\b(strengths|weaknesses|improvement|growth)\b'
            ],
            
            ConversationType.CHALLENGE_GUIDANCE: [
                r'\b(challenge|practice|exercise|homework|assignment)\b',
                r'\b(try this|attempt|goal|step|progress)\b',
                r'\b(difficulty|struggle|hard|easier|tips)\b'
            ],
            
            ConversationType.GOAL_SETTING: [
                r'\b(goal|objective|target|plan|strategy)\b',
                r'\b(want to|hoping to|trying to|working on)\b',
                r'\b(improve|better|change|develop|achieve)\b'
            ],
            
            ConversationType.EMOTIONAL_SUPPORT: [
                r'\b(anxious|nervous|scared|worried|stressed)\b',
                r'\b(depressed|sad|lonely|frustrated|angry)\b',
                r'\b(need help|struggling|difficult|hard time)\b',
                r'\b(support|encourage|comfort|understand)\b'
            ]
        }
        
        # Keywords that indicate complexity requiring premium models
        self.complex_keywords = [
            'psychology', 'personality', 'behavior', 'analysis', 'assessment',
            'trauma', 'therapy', 'counseling', 'deep', 'complex', 'nuanced'
        ]
        
        # Keywords that indicate simple interactions suitable for economy models
        self.simple_keywords = [
            'yes', 'no', 'thanks', 'ok', 'hello', 'hi', 'bye', 'good',
            'fine', 'sure', 'maybe', 'later', 'nice'
        ]
    
    def classify_conversation(self, message: str, context: Optional[List[str]] = None) -> Tuple[ConversationType, float]:
        """
        Classify conversation type based on message content and context.
        
        Args:
            message: Current user message
            context: Previous messages for context analysis
            
        Returns:
            Tuple of (conversation_type, confidence_score)
        """
        message_lower = message.lower().strip()
        
        # Check for exact pattern matches
        for conv_type, patterns in self.patterns.items():
            for pattern in patterns:
                if re.search(pattern, message_lower, re.IGNORECASE):
                    confidence = self._calculate_pattern_confidence(pattern, message_lower)
                    logger.debug(f"Pattern match: {conv_type} with confidence {confidence}")
                    return conv_type, confidence
        
        # Analyze message complexity and content
        complexity_score = self._analyze_complexity(message)
        content_type = self._analyze_content_type(message_lower, context)
        
        # Use content analysis if no pattern match
        if content_type != ConversationType.UNKNOWN:
            return content_type, 0.7
        
        # Default classification based on complexity
        if complexity_score > 0.7:
            return ConversationType.DATING_COACHING, 0.6
        elif complexity_score < 0.3:
            return ConversationType.SMALL_TALK, 0.5
        else:
            return ConversationType.UNKNOWN, 0.3
    
    def _calculate_pattern_confidence(self, pattern: str, message: str) -> float:
        """Calculate confidence score based on pattern match quality"""
        match_length = len(re.findall(pattern, message, re.IGNORECASE))
        message_length = len(message.split())
        
        if message_length <= 3:  # Short messages get higher confidence
            return min(0.95, 0.7 + (match_length * 0.1))
        else:
            return min(0.9, 0.6 + (match_length * 0.1))
    
    def _analyze_complexity(self, message: str) -> float:
        """Analyze message complexity to determine model requirements"""
        message_lower = message.lower()
        
        # Complexity indicators
        complex_count = sum(1 for keyword in self.complex_keywords if keyword in message_lower)
        simple_count = sum(1 for keyword in self.simple_keywords if keyword in message_lower)
        
        word_count = len(message.split())
        sentence_count = len([s for s in message.split('.') if s.strip()])
        question_count = message.count('?')
        
        # Calculate complexity score
        complexity = 0.0
        
        # Word count factor
        if word_count > 50:
            complexity += 0.3
        elif word_count > 20:
            complexity += 0.2
        elif word_count < 5:
            complexity -= 0.2
        
        # Sentence structure factor
        if sentence_count > 3:
            complexity += 0.2
        
        # Question complexity
        if question_count > 1:
            complexity += 0.2
        
        # Keyword analysis
        complexity += complex_count * 0.3
        complexity -= simple_count * 0.2
        
        return max(0.0, min(1.0, complexity))
    
    def _analyze_content_type(self, message: str, context: Optional[List[str]] = None) -> ConversationType:
        """Analyze content to determine conversation type"""
        # Dating-related keywords
        dating_keywords = ['date', 'dating', 'relationship', 'attraction', 'flirt', 'romance']
        if any(keyword in message for keyword in dating_keywords):
            return ConversationType.DATING_COACHING
        
        # Assessment-related keywords
        assessment_keywords = ['test', 'assessment', 'quiz', 'evaluate', 'analyze']
        if any(keyword in message for keyword in assessment_keywords):
            return ConversationType.CONFIDENCE_ASSESSMENT
        
        # Support-related keywords
        support_keywords = ['anxious', 'nervous', 'scared', 'help', 'support']
        if any(keyword in message for keyword in support_keywords):
            return ConversationType.EMOTIONAL_SUPPORT
        
        return ConversationType.UNKNOWN

class ModelRouter:
    """
    Routes conversations to appropriate Claude models based on content analysis.
    
    Optimizes costs by using cheaper models for simple interactions while
    maintaining quality for complex coaching scenarios.
    """
    
    def __init__(self):
        self.classifier = ConversationClassifier()
        
        # Model configuration for cost optimization
        self.model_config = {
            ModelTier.ECONOMY: {
                "model": "claude-3-haiku-20240307",
                "cost_factor": 1.0,  # Base cost
                "max_tokens": 2000,
                "temperature": 0.3
            },
            ModelTier.STANDARD: {
                "model": "claude-3-5-sonnet-20241022", 
                "cost_factor": 3.0,  # 3x more expensive than Haiku
                "max_tokens": 4000,
                "temperature": 0.7
            },
            ModelTier.PREMIUM: {
                "model": "claude-3-opus-20240229",
                "cost_factor": 15.0,  # 15x more expensive than Haiku
                "max_tokens": 8000,
                "temperature": 0.5
            }
        }
        
        # Routing rules for conversation types
        self.routing_rules = {
            ConversationType.GREETING: ModelTier.ECONOMY,
            ConversationType.SMALL_TALK: ModelTier.ECONOMY,
            ConversationType.CONFIRMATION: ModelTier.ECONOMY,
            ConversationType.DATING_COACHING: ModelTier.STANDARD,
            ConversationType.CONFIDENCE_ASSESSMENT: ModelTier.PREMIUM,
            ConversationType.CHALLENGE_GUIDANCE: ModelTier.STANDARD,
            ConversationType.GOAL_SETTING: ModelTier.STANDARD,
            ConversationType.EMOTIONAL_SUPPORT: ModelTier.STANDARD,
            ConversationType.UNKNOWN: ModelTier.STANDARD  # Safe default
        }
        
        # Track usage for monitoring
        self.usage_stats = {
            "total_requests": 0,
            "economy_usage": 0,
            "standard_usage": 0,
            "premium_usage": 0,
            "cost_savings": 0.0
        }
    
    def route_conversation(self, message: str, context: Optional[List[str]] = None,
                          user_preferences: Optional[Dict[str, Any]] = None) -> ModelRoutingDecision:
        """
        Determine the best model for a conversation based on content analysis.
        
        Args:
            message: Current user message
            context: Previous conversation context
            user_preferences: User-specific routing preferences
            
        Returns:
            ModelRoutingDecision with selected model and reasoning
        """
        # Classify conversation type
        conv_type, confidence = self.classifier.classify_conversation(message, context)
        
        # Get base tier from routing rules
        base_tier = self.routing_rules.get(conv_type, ModelTier.STANDARD)
        
        # Apply user preferences and overrides
        selected_tier = self._apply_preferences(base_tier, conv_type, user_preferences)
        
        # Get model configuration
        model_config = self.model_config[selected_tier]
        
        # Calculate estimated cost factor
        estimated_cost = self._calculate_cost_factor(selected_tier, message)
        
        # Update usage statistics
        self._update_usage_stats(selected_tier)
        
        # Build reasoning
        reasoning = self._build_reasoning(conv_type, confidence, selected_tier, base_tier)
        
        return ModelRoutingDecision(
            model_name=model_config["model"],
            tier=selected_tier,
            conversation_type=conv_type,
            confidence=confidence,
            reasoning=reasoning,
            estimated_cost_factor=estimated_cost
        )
    
    def _apply_preferences(self, base_tier: ModelTier, conv_type: ConversationType,
                          preferences: Optional[Dict[str, Any]]) -> ModelTier:
        """Apply user preferences and system overrides to tier selection"""
        if not preferences:
            return base_tier
        
        # Check for premium user (always use best models)
        if preferences.get("premium_user", False):
            if base_tier == ModelTier.ECONOMY:
                return ModelTier.STANDARD
            return base_tier
        
        # Check for cost-conscious user (prefer economy models)
        if preferences.get("cost_conscious", False):
            if base_tier == ModelTier.PREMIUM:
                return ModelTier.STANDARD
            elif base_tier == ModelTier.STANDARD and conv_type in [ConversationType.SMALL_TALK, ConversationType.GREETING]:
                return ModelTier.ECONOMY
        
        # Check for force premium for assessments
        if conv_type == ConversationType.CONFIDENCE_ASSESSMENT:
            return ModelTier.PREMIUM
        
        return base_tier
    
    def _calculate_cost_factor(self, tier: ModelTier, message: str) -> float:
        """Calculate estimated cost factor for the request"""
        base_cost = self.model_config[tier]["cost_factor"]
        
        # Adjust for message length (longer messages cost more)
        token_estimate = len(message.split()) * 1.3  # Rough token estimation
        length_multiplier = min(2.0, token_estimate / 1000)
        
        return base_cost * length_multiplier
    
    def _update_usage_stats(self, tier: ModelTier) -> None:
        """Update usage statistics for monitoring"""
        self.usage_stats["total_requests"] += 1
        
        if tier == ModelTier.ECONOMY:
            self.usage_stats["economy_usage"] += 1
        elif tier == ModelTier.STANDARD:
            self.usage_stats["standard_usage"] += 1
        else:
            self.usage_stats["premium_usage"] += 1
        
        # Calculate cost savings (compared to always using premium)
        premium_cost = self.model_config[ModelTier.PREMIUM]["cost_factor"]
        actual_cost = self.model_config[tier]["cost_factor"]
        savings = premium_cost - actual_cost
        self.usage_stats["cost_savings"] += max(0, savings)
    
    def _build_reasoning(self, conv_type: ConversationType, confidence: float,
                        selected_tier: ModelTier, base_tier: ModelTier) -> str:
        """Build human-readable reasoning for model selection"""
        reasoning_parts = [
            f"Detected conversation type: {conv_type.value} (confidence: {confidence:.2f})"
        ]
        
        if selected_tier == base_tier:
            reasoning_parts.append(f"Selected {selected_tier.value} tier model as recommended")
        else:
            reasoning_parts.append(f"Upgraded from {base_tier.value} to {selected_tier.value} tier")
        
        model_name = self.model_config[selected_tier]["model"]
        reasoning_parts.append(f"Using model: {model_name}")
        
        return "; ".join(reasoning_parts)
    
    def get_model_config(self, tier: ModelTier) -> Dict[str, Any]:
        """Get configuration for a specific model tier"""
        return self.model_config[tier].copy()
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get current usage statistics"""
        stats = self.usage_stats.copy()
        
        # Calculate percentages
        total = stats["total_requests"]
        if total > 0:
            stats["economy_percentage"] = (stats["economy_usage"] / total) * 100
            stats["standard_percentage"] = (stats["standard_usage"] / total) * 100
            stats["premium_percentage"] = (stats["premium_usage"] / total) * 100
            stats["average_cost_savings"] = stats["cost_savings"] / total
        else:
            stats["economy_percentage"] = 0
            stats["standard_percentage"] = 0
            stats["premium_percentage"] = 0
            stats["average_cost_savings"] = 0
        
        return stats
    
    def reset_usage_stats(self) -> None:
        """Reset usage statistics"""
        self.usage_stats = {
            "total_requests": 0,
            "economy_usage": 0,
            "standard_usage": 0,
            "premium_usage": 0,
            "cost_savings": 0.0
        }

# Global model router instance
model_router = ModelRouter()

def get_optimal_model(message: str, context: Optional[List[str]] = None,
                     user_preferences: Optional[Dict[str, Any]] = None) -> ModelRoutingDecision:
    """
    Convenience function to get optimal model for a message.
    
    Args:
        message: User message
        context: Conversation context
        user_preferences: User-specific preferences
        
    Returns:
        ModelRoutingDecision with selected model and configuration
    """
    return model_router.route_conversation(message, context, user_preferences)