#!/usr/bin/env python3
"""
Run All Real World Tests for SimpleChatHandler System

Executes all real-world integration tests against live API endpoints.
Tests the new SimpleChatHandler architecture end-to-end.

Usage:
    python run_all_tests.py --env=dev      # Test against dev server  
    python run_all_tests.py --env=prod     # Test against production
    python run_all_tests.py --quick        # Run quick smoke tests only
"""

import argparse
import subprocess
import sys
import os
from pathlib import Path
from typing import List, Dict

# Updated test execution order for SimpleChatHandler system
TEST_SUITES = {
    "quick": [
        "test_live_endpoints.py --quick",
    ],
    "comprehensive": [
        "test_full_user_journey.py",
        "test_live_endpoints.py",
        "test_creativity_flow.py", 
        "test_onboarding_conversation.py",
    ]
}

class SimpleChatTestRunner:
    """Test runner for SimpleChatHandler system"""
    
    def __init__(self, env: str = "dev"):
        self.env = env
        self.test_dir = Path(__file__).parent
        self.passed_tests = []
        self.failed_tests = []
        
    def check_environment(self) -> bool:
        """Check that we can reach the target environment"""
        print(f"🔍 Environment Check - {self.env.upper()}")
        print("=" * 60)
        
        # Basic environment validation
        if self.env not in ["dev", "prod", "local"]:
            print(f"❌ Invalid environment: {self.env}")
            return False
            
        print(f"✅ Environment '{self.env}' is valid")
        return True
    
    def run_test_command(self, test_command: str) -> bool:
        """Run a single test command"""
        command_parts = test_command.split()
        test_file = command_parts[0]
        test_args = command_parts[1:] if len(command_parts) > 1 else []
        
        # Add environment argument
        test_args.extend(["--env", self.env])
        
        test_path = self.test_dir / test_file
        
        if not test_path.exists():
            print(f"⚠️  Test file not found: {test_file}")
            self.failed_tests.append(test_command)
            return False
        
        print(f"\n🧪 Running {test_command} (env: {self.env})")
        print("=" * 60)
        
        try:
            # Build full command
            full_command = [sys.executable, str(test_path)] + test_args
            
            # Run the test
            result = subprocess.run(
                full_command,
                cwd=str(test_path.parent),
                capture_output=False,  # Show output in real-time
                text=True
            )
            
            if result.returncode == 0:
                print(f"✅ {test_command} PASSED")
                self.passed_tests.append(test_command)
                return True
            else:
                print(f"❌ {test_command} FAILED (exit code: {result.returncode})")
                self.failed_tests.append(test_command)
                return False
                
        except Exception as e:
            print(f"❌ {test_command} ERROR: {e}")
            self.failed_tests.append(test_command)
            return False
    
    def run_cleanup(self):
        """Run cleanup after tests"""
        cleanup_script = self.test_dir / "cleanup_test_user.py"
        if cleanup_script.exists():
            print(f"\n🧹 Running cleanup...")
            try:
                subprocess.run([sys.executable, str(cleanup_script)], check=True)
                print("✅ Cleanup completed")
            except Exception as e:
                print(f"⚠️  Cleanup failed: {e}")
    
    def print_summary(self):
        """Print test execution summary"""
        total_tests = len(self.passed_tests) + len(self.failed_tests)
        pass_rate = (len(self.passed_tests) / total_tests * 100) if total_tests > 0 else 0
        
        print(f"\n{'='*60}")
        print(f"🎯 SIMPLECHATHANDLER TEST SUMMARY")
        print(f"{'='*60}")
        print(f"🌍 Environment: {self.env.upper()}")
        print(f"✅ Passed: {len(self.passed_tests)}")
        print(f"❌ Failed: {len(self.failed_tests)}")
        print(f"📊 Pass Rate: {pass_rate:.1f}%")
        
        if self.passed_tests:
            print(f"\n✅ Passed Tests:")
            for test in self.passed_tests:
                print(f"   - {test}")
        
        if self.failed_tests:
            print(f"\n❌ Failed Tests:")
            for test in self.failed_tests:
                print(f"   - {test}")
            print(f"\n⚠️  Some tests failed. Check output above for details.")
        else:
            print(f"\n🎉 ALL TESTS PASSED!")
            print(f"✅ SimpleChatHandler system is working correctly")
        
        return pass_rate
    
    def run_test_suite(self, suite_name: str = "comprehensive", stop_on_failure: bool = False):
        """Run a specific test suite"""
        if suite_name not in TEST_SUITES:
            print(f"❌ Unknown test suite: {suite_name}")
            return False
            
        test_commands = TEST_SUITES[suite_name]
        
        print(f"🚀 Starting SimpleChatHandler {suite_name.title()} Tests")
        print(f"🌍 Environment: {self.env.upper()}")
        print(f"📋 Test Commands: {len(test_commands)}")
        print("⚠️  WARNING: These tests hit real API endpoints!")
        print("=" * 60)
        
        # Check environment first
        if not self.check_environment():
            print("❌ Environment check failed. Aborting.")
            return False
        
        # Run tests in order
        for test_command in test_commands:
            success = self.run_test_command(test_command)
            
            if not success and stop_on_failure:
                print(f"\n🛑 Stopping execution due to failure in {test_command}")
                break
        
        # Always run cleanup
        self.run_cleanup()
        
        # Print summary
        pass_rate = self.print_summary()
        
        return len(self.failed_tests) == 0

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Run SimpleChatHandler real-world tests")
    parser.add_argument(
        "--env", 
        choices=["dev", "prod", "local"],
        default="dev",
        help="Environment to test against (default: dev)"
    )
    parser.add_argument(
        "--quick",
        action="store_true", 
        help="Run quick smoke tests only"
    )
    parser.add_argument(
        "--stop-on-failure", 
        action="store_true",
        help="Stop execution if any test fails"
    )
    parser.add_argument(
        "--test",
        help="Run only a specific test command (e.g., 'test_creativity_flow.py')"
    )
    
    args = parser.parse_args()
    
    runner = SimpleChatTestRunner(args.env)
    
    if args.test:
        # Run single test
        if not runner.check_environment():
            sys.exit(1)
        
        success = runner.run_test_command(args.test)
        runner.run_cleanup()
        
        if success:
            print("🎉 Single test completed successfully!")
        else:
            print("❌ Single test failed!")
            
        sys.exit(0 if success else 1)
    else:
        # Run test suite
        suite_name = "quick" if args.quick else "comprehensive"
        success = runner.run_test_suite(suite_name, stop_on_failure=args.stop_on_failure)
        
        if success:
            print(f"\n🎉 All {suite_name} tests completed successfully!")
            print("✅ SimpleChatHandler system is production ready!")
        else:
            print(f"\n⚠️  Some {suite_name} tests failed!")
            print("🔧 Check the output above for details on what needs attention.")
            
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 