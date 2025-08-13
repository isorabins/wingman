import sys
import os
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

@pytest.fixture
def client():
    """FastAPI test client fixture for API endpoint testing"""
    from src.main import app
    return TestClient(app)
