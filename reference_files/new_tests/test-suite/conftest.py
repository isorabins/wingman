#!/usr/bin/env python3
"""
Pytest configuration for DB-driven agent system tests
"""

import pytest
import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from .test_config import TestConfig

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def test_config():
    """Provide test configuration"""
    return TestConfig

@pytest.fixture
def test_user_id():
    """Generate unique test user ID for each test"""
    return TestConfig.get_test_user_id()

@pytest.fixture
def performance_thresholds():
    """Get performance expectations"""
    return TestConfig.get_performance_thresholds()
