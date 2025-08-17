#!/usr/bin/env python3
"""
Test Suite Runner for Fridays at Four
Run with: python -m test-suite
"""

import os
import sys
import subprocess
import pytest
from pathlib import Path

def main():
    """Run the test suite"""
    print("🧪 Fridays at Four Test Suite")
    print("=" * 50)
    
    # Get the test-suite directory path
    test_suite_dir = Path(__file__).parent
    
    # Add project root to path
    project_root = test_suite_dir.parent
    sys.path.insert(0, str(project_root))
    
    print(f"📁 Test directory: {test_suite_dir}")
    print(f"🏠 Project root: {project_root}")
    
    # Check if server is running
    try:
        import requests
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ Local server is running")
        else:
            print("⚠️  Local server responded but not healthy")
    except Exception:
        print("❌ Local server is not running. Start it with:")
        print("   uvicorn src.main:app --reload --host localhost --port 8000")
        return 1
    
    print("\n🚀 Running tests...")
    print("-" * 30)
    
    # Run pytest on the test-suite directory
    # Use -v for verbose output, -x to stop on first failure
    pytest_args = [
        "-v",  # verbose
        "-x",  # stop on first failure
        "--tb=short",  # shorter traceback format
        str(test_suite_dir)
    ]
    
    # Run pytest
    exit_code = pytest.main(pytest_args)
    
    print("\n" + "=" * 50)
    if exit_code == 0:
        print("🎉 All tests passed!")
    else:
        print("💥 Some tests failed.")
    
    return exit_code

if __name__ == "__main__":
    sys.exit(main()) 