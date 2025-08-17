#!/usr/bin/env python3
"""
Test Helpers - Utilities for cost-optimized testing

This module provides utilities to ensure all tests use cheaper Claude models
automatically, reducing development costs by 90%.
"""

import os
import logging
from typing import Optional, Dict, Any
from contextlib import contextmanager
from unittest.mock import patch

logger = logging.getLogger(__name__)

# Test-specific model configuration
TEST_MODEL = "claude-3-haiku-20240307"  # Always use cheapest model for tests

class TestModelEnforcer:
    """Ensures all tests use cost-optimized models"""
    
    @staticmethod
    def setup_test_environment():
        """Set up environment variables for cost-optimized testing"""
        test_env_vars = {
            "FORCE_TESTING_MODE": "true",
            "TEST_MODEL": TEST_MODEL,
            "DEV_MODEL": TEST_MODEL,
            "DEV_CHAT_MODEL": TEST_MODEL,
            "BACKGROUND_MODEL": TEST_MODEL,
            "ENABLE_COST_OPTIMIZATION": "true"
        }
        
        for key, value in test_env_vars.items():
            os.environ[key] = value
            
        logger.info(f"🧪 Test environment configured with model: {TEST_MODEL}")
    
    @staticmethod
    def cleanup_test_environment():
        """Clean up test environment variables"""
        test_env_vars = [
            "FORCE_TESTING_MODE",
            "TEST_MODEL", 
            "DEV_MODEL",
            "DEV_CHAT_MODEL",
            "BACKGROUND_MODEL"
        ]
        
        for key in test_env_vars:
            os.environ.pop(key, None)
    
    @staticmethod
    def get_test_model() -> str:
        """Get the model that should be used for testing"""
        return TEST_MODEL

@contextmanager
def cost_optimized_test():
    """
    Context manager for cost-optimized testing
    
    Usage:
        with cost_optimized_test():
            # Your test code here - will automatically use Haiku
            response = await claude_client.send_message(...)
    """
    TestModelEnforcer.setup_test_environment()
    try:
        yield
    finally:
        TestModelEnforcer.cleanup_test_environment()

@contextmanager
def patch_claude_models():
    """
    Patch all Claude model references to use test model
    
    Returns:
        A context manager that patches model usage
    """
    test_model = TestModelEnforcer.get_test_model()
    
    # Patch all model selection functions to return test model
    patches = [
        # Patch model selection functions
        patch('src.model_selector.get_chat_model', return_value=test_model),
        patch('src.model_selector.get_summarization_model', return_value=test_model),
        patch('src.model_selector.get_analysis_model', return_value=test_model),
        patch('src.model_selector.get_testing_model', return_value=test_model),
        patch('src.model_selector.get_background_model', return_value=test_model),
        patch('src.model_selector.get_model_for_operation', return_value=test_model),
        
        # Patch direct model calls with proper return values
        patch('src.claude_agent.interact_with_agent', 
              return_value="Test response from mocked Claude agent"),
        patch('src.claude_client_simple.SimpleClaudeClient.send_message',
              return_value="Test response from mocked Claude client"),
    ]
    
    # Start all patches
    started_patches = []
    try:
        for p in patches:
            started_patches.append(p.__enter__())
        yield started_patches
    finally:
        # Stop all patches in reverse order
        for p in reversed(patches):
            p.__exit__(None, None, None)

def ensure_test_model_usage():
    """
    Decorator to ensure test functions use cost-optimized models
    
    Usage:
        @ensure_test_model_usage()
        def test_my_function():
            # This test will automatically use Haiku model
            pass
    """
    def decorator(test_func):
        def wrapper(*args, **kwargs):
            with cost_optimized_test():
                return test_func(*args, **kwargs)
        return wrapper
    return decorator

async def create_test_claude_client():
    """
    Create a Claude client configured for testing with cost optimization
    
    Returns:
        SimpleClaudeClient configured to use test model
    """
    from src.claude_client_simple import SimpleClaudeClient, ClaudeCredentials
    from src.model_selector import force_testing_mode
    
    # Force testing mode
    force_testing_mode()
    
    # Create client
    credentials = ClaudeCredentials()
    client = SimpleClaudeClient(credentials)
    
    logger.info(f"🧪 Created test Claude client using model: {TEST_MODEL}")
    return client

def get_test_model_info() -> Dict[str, Any]:
    """Get information about test model configuration"""
    from src.model_selector import get_environment_info
    
    TestModelEnforcer.setup_test_environment()
    
    info = get_environment_info()
    info.update({
        "test_model_enforced": TEST_MODEL,
        "cost_savings": "~90% compared to production models"
    })
    
    return info

def log_test_cost_savings():
    """Log cost savings information for test runs"""
    logger.info("💰 TEST COST OPTIMIZATION ACTIVE")
    logger.info(f"   Using model: {TEST_MODEL} (90% cost reduction)")
    logger.info("   All API calls in this test will use the cheapest model")

# Auto-setup for pytest
def pytest_configure():
    """Automatically configure pytest for cost optimization"""
    TestModelEnforcer.setup_test_environment()
    log_test_cost_savings()

def pytest_unconfigure():
    """Clean up after pytest runs"""
    TestModelEnforcer.cleanup_test_environment()

# Example usage in test files:
"""
# Option 1: Use the decorator
@ensure_test_model_usage()
def test_claude_summarization():
    # This automatically uses Haiku model
    summarizer = ContentSummarizer()
    assert summarizer.model_name == "claude-3-haiku-20240307"

# Option 2: Use context manager
def test_claude_chat():
    with cost_optimized_test():
        # This code uses Haiku model
        client = create_test_claude_client()
        response = await client.send_message([...])

# Option 3: Manual setup (for complex tests)
def test_complex_scenario():
    TestModelEnforcer.setup_test_environment()
    try:
        # Your test code here
        pass
    finally:
        TestModelEnforcer.cleanup_test_environment()
"""

if __name__ == "__main__":
    # Demo the test configuration
    print("🧪 Test Model Configuration:")
    import json
    print(json.dumps(get_test_model_info(), indent=2)) 