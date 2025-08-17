#!/usr/bin/env python3
"""
Test Runner for Task 7 Profile Setup Integration Tests

This script runs comprehensive tests for the profile setup feature including:
- Frontend integration tests (Playwright)
- Backend API tests (pytest)
- Security validation tests  
- Performance benchmarks
- Database integration tests

Usage:
    python tests/run_profile_setup_tests.py [options]
    
Options:
    --frontend-only: Run only frontend tests
    --backend-only: Run only backend tests
    --security-only: Run only security tests
    --performance-only: Run only performance tests
    --quick: Run quick test suite (subset of tests)
    --verbose: Enable verbose output
    --report: Generate HTML test report
"""

import os
import sys
import argparse
import subprocess
import json
import time
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tests.test_config import TestConfig

class TestRunner:
    """Test runner for profile setup integration tests"""
    
    def __init__(self, args):
        self.args = args
        self.results = {
            'start_time': datetime.now().isoformat(),
            'test_suites': {},
            'summary': {
                'total_tests': 0,
                'passed': 0,
                'failed': 0,
                'skipped': 0,
                'errors': []
            }
        }
        
        # Setup test environment
        TestConfig.setup_test_directories()
    
    def run_all_tests(self) -> Dict:
        """Run all test suites"""
        print("🚀 Starting Task 7 Profile Setup Integration Tests")
        print(f"Test environment: {TestConfig.TEST_ENV}")
        print(f"Frontend URL: {TestConfig.BASE_URL}")
        print(f"API URL: {TestConfig.API_URL}")
        print("-" * 60)
        
        # Determine which test suites to run
        suites_to_run = self._get_test_suites()
        
        for suite_name, suite_config in suites_to_run.items():
            print(f"\n📋 Running {suite_name} tests...")
            result = self._run_test_suite(suite_name, suite_config)
            self.results['test_suites'][suite_name] = result
            
            # Update summary
            self.results['summary']['total_tests'] += result.get('total', 0)
            self.results['summary']['passed'] += result.get('passed', 0)
            self.results['summary']['failed'] += result.get('failed', 0)
            self.results['summary']['skipped'] += result.get('skipped', 0)
            
            if result.get('errors'):
                self.results['summary']['errors'].extend(result['errors'])
        
        # Generate report
        self._print_summary()
        
        if self.args.report:
            self._generate_html_report()
        
        # Cleanup
        TestConfig.cleanup_test_directories()
        
        return self.results
    
    def _get_test_suites(self) -> Dict:
        """Determine which test suites to run based on arguments"""
        all_suites = {
            'frontend': {
                'command': ['npx', 'playwright', 'test', 'tests/e2e/profile_setup.spec.ts'],
                'description': 'Frontend E2E Tests (Playwright)',
                'timeout': 300,
                'enabled': True
            },
            'backend_api': {
                'command': ['python3', '-m', 'pytest', 'tests/test_profile_setup_api.py', '-v'],
                'description': 'Backend API Tests (pytest)',
                'timeout': 120,
                'enabled': True
            },
            'security': {
                'command': ['python3', '-m', 'pytest', 'tests/test_photo_upload_security.py', '-v'],
                'description': 'Security Tests',
                'timeout': 180,
                'enabled': TestConfig.ENABLE_SECURITY_TESTS
            },
            'performance': {
                'command': ['python3', '-m', 'pytest', 'tests/test_profile_setup_api.py::TestProfileSetupPerformance', '-v'],
                'description': 'Performance Tests',
                'timeout': 300,
                'enabled': TestConfig.ENABLE_LOAD_TESTS
            }
        }
        
        # Filter based on command line arguments
        if self.args.frontend_only:
            return {'frontend': all_suites['frontend']}
        elif self.args.backend_only:
            return {'backend_api': all_suites['backend_api']}
        elif self.args.security_only:
            return {'security': all_suites['security']}
        elif self.args.performance_only:
            return {'performance': all_suites['performance']}
        elif self.args.quick:
            # Quick test suite - subset of tests
            quick_suites = {}
            for name, config in all_suites.items():
                if name in ['backend_api']:  # Only run backend API tests for quick mode
                    quick_config = config.copy()
                    quick_config['command'].extend(['-k', 'not (performance or load)'])
                    quick_suites[name] = quick_config
            return quick_suites
        else:
            # Return enabled suites
            return {name: config for name, config in all_suites.items() if config['enabled']}
    
    def _run_test_suite(self, suite_name: str, suite_config: Dict) -> Dict:
        """Run a single test suite"""
        print(f"  {suite_config['description']}")
        print(f"  Command: {' '.join(suite_config['command'])}")
        
        start_time = time.time()
        
        try:
            # Set environment variables
            env = os.environ.copy()
            env.update({
                'TEST_ENV': TestConfig.TEST_ENV,
                'TEST_BASE_URL': TestConfig.BASE_URL,
                'TEST_API_URL': TestConfig.API_URL,
                'PYTHONPATH': str(PROJECT_ROOT),
            })
            
            # Run the test command
            result = subprocess.run(
                suite_config['command'],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                timeout=suite_config.get('timeout', 120),
                env=env
            )
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            # Parse results based on test type
            if suite_name == 'frontend':
                parsed_results = self._parse_playwright_results(result)
            else:
                parsed_results = self._parse_pytest_results(result)
            
            parsed_results.update({
                'execution_time': execution_time,
                'return_code': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr
            })
            
            # Print status
            status = "✅ PASSED" if result.returncode == 0 else "❌ FAILED"
            print(f"  Status: {status} ({execution_time:.1f}s)")
            
            if result.returncode != 0 and self.args.verbose:
                print(f"  Error output: {result.stderr}")
            
            return parsed_results
            
        except subprocess.TimeoutExpired:
            print(f"  ⏰ TIMEOUT after {suite_config.get('timeout', 120)}s")
            return {
                'total': 0,
                'passed': 0,
                'failed': 1,
                'skipped': 0,
                'errors': [f"Test suite {suite_name} timed out"],
                'execution_time': suite_config.get('timeout', 120)
            }
        except Exception as e:
            print(f"  💥 ERROR: {str(e)}")
            return {
                'total': 0,
                'passed': 0,
                'failed': 1,
                'skipped': 0,
                'errors': [f"Test suite {suite_name} failed with error: {str(e)}"],
                'execution_time': 0
            }
    
    def _parse_playwright_results(self, result: subprocess.CompletedProcess) -> Dict:
        """Parse Playwright test results"""
        output = result.stdout + result.stderr
        
        # Basic parsing - in production, we'd use Playwright's JSON reporter
        total = 0
        passed = 0
        failed = 0
        skipped = 0
        errors = []
        
        lines = output.split('\n')
        for line in lines:
            if 'tests passed' in line.lower():
                # Extract numbers from summary line
                parts = line.split()
                for i, part in enumerate(parts):
                    if part.isdigit():
                        if 'passed' in ' '.join(parts[i:i+2]):
                            passed = int(part)
                        elif 'failed' in ' '.join(parts[i:i+2]):
                            failed = int(part)
            elif 'error' in line.lower() and '✗' in line:
                errors.append(line.strip())
        
        total = passed + failed + skipped
        
        return {
            'total': total,
            'passed': passed,
            'failed': failed,
            'skipped': skipped,
            'errors': errors
        }
    
    def _parse_pytest_results(self, result: subprocess.CompletedProcess) -> Dict:
        """Parse pytest results"""
        output = result.stdout + result.stderr
        
        total = 0
        passed = 0
        failed = 0
        skipped = 0
        errors = []
        
        lines = output.split('\n')
        for line in lines:
            # Look for pytest summary line
            if '=====' in line and ('passed' in line or 'failed' in line):
                # Parse summary like "===== 5 passed, 2 failed in 1.23s ====="
                parts = line.split()
                for i, part in enumerate(parts):
                    if part.isdigit():
                        count = int(part)
                        if i + 1 < len(parts):
                            if 'passed' in parts[i + 1]:
                                passed = count
                            elif 'failed' in parts[i + 1]:
                                failed = count
                            elif 'skipped' in parts[i + 1]:
                                skipped = count
            elif 'FAILED' in line:
                errors.append(line.strip())
        
        total = passed + failed + skipped
        
        return {
            'total': total,
            'passed': passed,
            'failed': failed,
            'skipped': skipped,
            'errors': errors
        }
    
    def _print_summary(self):
        """Print test execution summary"""
        print("\n" + "=" * 60)
        print("📊 TEST EXECUTION SUMMARY")
        print("=" * 60)
        
        summary = self.results['summary']
        print(f"Total Tests: {summary['total_tests']}")
        print(f"✅ Passed: {summary['passed']}")
        print(f"❌ Failed: {summary['failed']}")
        print(f"⏭️ Skipped: {summary['skipped']}")
        
        if summary['failed'] > 0:
            print(f"\n🔍 FAILED TESTS:")
            for error in summary['errors'][:10]:  # Show first 10 errors
                print(f"  • {error}")
            if len(summary['errors']) > 10:
                print(f"  ... and {len(summary['errors']) - 10} more")
        
        # Test suite breakdown
        print(f"\n📋 TEST SUITE BREAKDOWN:")
        for suite_name, suite_result in self.results['test_suites'].items():
            status = "✅" if suite_result.get('failed', 0) == 0 else "❌"
            time_taken = suite_result.get('execution_time', 0)
            print(f"  {status} {suite_name}: {suite_result.get('passed', 0)}/{suite_result.get('total', 0)} passed ({time_taken:.1f}s)")
        
        # Overall result
        overall_status = "✅ ALL TESTS PASSED" if summary['failed'] == 0 else "❌ SOME TESTS FAILED"
        print(f"\n🎯 OVERALL RESULT: {overall_status}")
        
        # Performance insights
        total_time = sum(suite.get('execution_time', 0) for suite in self.results['test_suites'].values())
        print(f"⏱️ Total execution time: {total_time:.1f} seconds")
    
    def _generate_html_report(self):
        """Generate HTML test report"""
        report_path = PROJECT_ROOT / "test_report.html"
        
        html_content = self._create_html_report()
        
        with open(report_path, 'w') as f:
            f.write(html_content)
        
        print(f"\n📄 HTML report generated: {report_path}")
    
    def _create_html_report(self) -> str:
        """Create HTML report content"""
        summary = self.results['summary']
        
        # Calculate pass rate
        pass_rate = (summary['passed'] / max(summary['total_tests'], 1)) * 100
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>WingmanMatch Profile Setup Test Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        .header {{ background-color: #f5f5f5; padding: 20px; border-radius: 8px; }}
        .summary {{ display: flex; gap: 20px; margin: 20px 0; }}
        .metric {{ background: white; padding: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .passed {{ color: #28a745; }}
        .failed {{ color: #dc3545; }}
        .skipped {{ color: #ffc107; }}
        .suite {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 8px; }}
        .error {{ background-color: #f8d7da; padding: 10px; border-radius: 4px; margin: 5px 0; }}
        .pass-rate {{ font-size: 24px; font-weight: bold; }}
        .timestamp {{ color: #666; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🧪 WingmanMatch Profile Setup Test Report</h1>
        <div class="timestamp">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
        <div class="pass-rate {'passed' if pass_rate >= 90 else 'failed'}">
            Pass Rate: {pass_rate:.1f}%
        </div>
    </div>
    
    <div class="summary">
        <div class="metric">
            <h3>Total Tests</h3>
            <div style="font-size: 24px; font-weight: bold;">{summary['total_tests']}</div>
        </div>
        <div class="metric passed">
            <h3>Passed</h3>
            <div style="font-size: 24px; font-weight: bold;">{summary['passed']}</div>
        </div>
        <div class="metric failed">
            <h3>Failed</h3>
            <div style="font-size: 24px; font-weight: bold;">{summary['failed']}</div>
        </div>
        <div class="metric skipped">
            <h3>Skipped</h3>
            <div style="font-size: 24px; font-weight: bold;">{summary['skipped']}</div>
        </div>
    </div>
    
    <h2>📋 Test Suite Results</h2>
        """
        
        # Add test suite details
        for suite_name, suite_result in self.results['test_suites'].items():
            status_icon = "✅" if suite_result.get('failed', 0) == 0 else "❌"
            execution_time = suite_result.get('execution_time', 0)
            
            html += f"""
    <div class="suite">
        <h3>{status_icon} {suite_name.title()}</h3>
        <p>Execution time: {execution_time:.1f} seconds</p>
        <p>Results: {suite_result.get('passed', 0)} passed, {suite_result.get('failed', 0)} failed, {suite_result.get('skipped', 0)} skipped</p>
        """
            
            if suite_result.get('errors'):
                html += "<h4>Errors:</h4>"
                for error in suite_result['errors']:
                    html += f'<div class="error">{error}</div>'
            
            html += "</div>"
        
        html += """
</body>
</html>
        """
        
        return html

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Run Task 7 Profile Setup Integration Tests')
    
    parser.add_argument('--frontend-only', action='store_true', help='Run only frontend tests')
    parser.add_argument('--backend-only', action='store_true', help='Run only backend tests')
    parser.add_argument('--security-only', action='store_true', help='Run only security tests')
    parser.add_argument('--performance-only', action='store_true', help='Run only performance tests')
    parser.add_argument('--quick', action='store_true', help='Run quick test suite')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose output')
    parser.add_argument('--report', action='store_true', help='Generate HTML test report')
    
    args = parser.parse_args()
    
    # Run tests
    runner = TestRunner(args)
    results = runner.run_all_tests()
    
    # Exit with appropriate code
    exit_code = 1 if results['summary']['failed'] > 0 else 0
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
