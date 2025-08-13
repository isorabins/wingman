"""
Test script to verify imports are working correctly.

This script imports from the migrated modules to ensure they can be
properly imported using the new package structure.
"""

import sys
import os
from pathlib import Path

# Add the project root to the Python path
# This is necessary to make the imports work
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

def test_config_import():
    """Test importing from the config module."""
    try:
        from src.config import Config
        print("✅ Successfully imported Config from src.config")
        
        # Test accessing some attributes
        print(f"  DEBUG setting: {Config.DEBUG}")
        print(f"  DEFAULT_MODEL: {Config.DEFAULT_MODEL}")
        
        return True
    except Exception as e:
        print(f"❌ Failed to import Config from src.config: {str(e)}")
        return False

def test_prompts_import():
    """Test importing from the prompts module."""
    try:
        from src.prompts import (
            MAP_PROMPT, 
            REDUCE_PROMPT, 
            QUALITY_ANALYSIS_PROMPT,
            TRANSCRIPT_MAP_PROMPT,
            PROJECT_UPDATE_PROMPT
        )
        print("✅ Successfully imported prompts from src.prompts")
        
        # Test accessing some attributes
        print(f"  MAP_PROMPT type: {type(MAP_PROMPT)}")
        
        return True
    except Exception as e:
        print(f"❌ Failed to import prompts from src.prompts: {str(e)}")
        return False

def test_sql_tools_import():
    """Test importing from the sql_tools module."""
    try:
        from src.sql_tools import DatabaseTools
        print("✅ Successfully imported DatabaseTools from src.sql_tools")
        
        # Test creating an instance (with a mock client)
        mock_client = type('MockClient', (), {})()
        db_tools = DatabaseTools(mock_client)
        print(f"  Created DatabaseTools instance: {db_tools}")
        
        return True
    except Exception as e:
        print(f"❌ Failed to import DatabaseTools from src.sql_tools: {str(e)}")
        return False

def run_tests():
    """Run all import tests."""
    print("Testing imports from migrated modules...")
    print(f"Python path includes: {project_root}")
    
    config_success = test_config_import()
    prompts_success = test_prompts_import()
    sql_tools_success = test_sql_tools_import()
    
    if config_success and prompts_success and sql_tools_success:
        print("\n🎉 All imports working correctly!")
        return True
    else:
        print("\n⚠️ Some imports failed. See errors above.")
        return False

if __name__ == "__main__":
    run_tests() 