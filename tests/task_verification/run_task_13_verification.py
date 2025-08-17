#!/usr/bin/env python3
"""
Task 13 Verification Runner

Executes comprehensive verification of Task 13: Session Creation Flow and API Implementation.

Usage:
    python tests/task_verification/run_task_13_verification.py

This script:
1. Sets up the proper Python path
2. Runs the Task 13 verification module
3. Generates a detailed verification report
4. Provides actionable feedback for any issues found
"""

import sys
import os
import asyncio
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

async def main():
    """Run Task 13 verification with proper setup"""
    print("🚀 Task 13 Verification Runner")
    print("=" * 50)
    print("📋 Verifying: Session Creation Flow and API Implementation")
    print("📁 Project Root:", project_root)
    print("🐍 Python Path:", sys.path[:3])
    print()
    
    try:
        # Import and run the verification
        from tests.task_verification.task_13_sessions import main as run_verification
        await run_verification()
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("💡 Suggestion: Ensure all dependencies are installed and paths are correct")
        print("🔧 Try: pip install -r requirements.txt")
        return 1
        
    except Exception as e:
        print(f"❌ Verification Error: {e}")
        print("💡 Check the error details above and ensure the system is properly configured")
        return 1
    
    print("\n✅ Verification completed successfully!")
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)