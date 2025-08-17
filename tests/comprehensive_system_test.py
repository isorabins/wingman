#!/usr/bin/env python3
"""
WingmanMatch Task-by-Task Verification Suite

This comprehensive test suite verifies that each completed task (Tasks 1-17)
has been implemented correctly and all deliverables are working as specified.

Usage:
    python tests/comprehensive_system_test.py

Features:
- Verifies each task's specific deliverables and requirements
- Tests functionality exactly as described in task files
- Resilient execution (doesn't stop on first failure)
- Task-by-task pass/fail reporting with specific action items
- Complete project readiness assessment
"""

import asyncio
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# Import task verification modules
from task_verification.task_01_environment import Task01Verification
from task_verification.task_02_database import Task02Verification
from task_verification.task_03_backend import Task03Verification
from task_verification.task_04_ai_coach import Task04Verification
from task_verification.task_05_confidence import Task05Verification
from task_verification.task_06_frontend import Task06Verification
from task_verification.task_07_profile import Task07Verification
from task_verification.task_08_distance import Task08Verification
from task_verification.task_09_matching import Task09Verification
from task_verification.task_10_response import Task10Verification
from task_verification.task_11_chat import Task11Verification
from task_verification.task_12_challenges import Task12Verification
from task_verification.task_13_sessions import Task13Verification
from task_verification.task_17_branding import Task17Verification
from utils.health_reporter import HealthReporter
from utils.test_data_factory import TestDataFactory

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('tests/logs/system_test.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class TaskByTaskVerification:
    """
    Master test orchestrator that verifies each completed task's deliverables
    """
    
    def __init__(self):
        self.start_time = datetime.now()
        self.reporter = HealthReporter()
        self.test_data_factory = TestDataFactory()
        self.results = {
            'task_results': {},
            'summary': {},
            'action_items': []
        }
        
        # Define completed tasks to verify
        self.completed_tasks = [
            ('Task 1', 'Environment Setup & Dependencies', Task01Verification),
            ('Task 2', 'Database Schema & Core Tables', Task02Verification),
            ('Task 3', 'Backend Services & Architecture', Task03Verification),
            ('Task 4', 'AI Coach Agent Implementation', Task04Verification),
            ('Task 5', 'Confidence Assessment System', Task05Verification),
            ('Task 6', 'Frontend Development & User Interface', Task06Verification),
            ('Task 7', 'Profile Setup API and Page', Task07Verification),
            ('Task 8', 'Distance Calculation & Buddy Candidate Discovery', Task08Verification),
            ('Task 9', 'Auto-Matching Service & Wingman Matcher', Task09Verification),
            ('Task 10', 'Match Response Endpoint and State Machine', Task10Verification),
            ('Task 11', 'Basic Buddy Chat Implementation', Task11Verification),
            ('Task 12', 'Challenges Catalog and API System', Task12Verification),
            ('Task 13', 'Session Creation Flow and API', Task13Verification),
            ('Task 17', 'Homepage and AI Agent Branding Updates', Task17Verification)
        ]
        
    async def run_all_verifications(self) -> Dict[str, Any]:
        """
        Verify all completed tasks and return comprehensive results
        """
        logger.info("🎯 Starting WingmanMatch Task-by-Task Verification Suite")
        logger.info(f"📅 Verification run started at: {self.start_time}")
        logger.info(f"📋 Verifying {len(self.completed_tasks)} completed tasks")
        
        # Initialize test data
        await self._setup_test_environment()
        
        # Run task verifications (resilient - don't stop on failures)
        for task_id, task_name, verification_class in self.completed_tasks:
            try:
                logger.info(f"\n{'='*80}")
                logger.info(f"📝 Verifying {task_id}: {task_name}")
                logger.info(f"{'='*80}")
                
                # Initialize task verification
                task_verifier = verification_class()
                task_results = await task_verifier.verify_task_completion()
                
                self.results['task_results'][task_id] = {
                    'name': task_name,
                    'results': task_results,
                    'timestamp': datetime.now().isoformat()
                }
                
                # Log immediate results
                total_checks = len(task_results.get('checks', {}))
                passed_checks = sum(1 for check in task_results.get('checks', {}).values() 
                                  if check.get('status') == 'pass')
                
                status_icon = "✅" if passed_checks == total_checks else "❌"
                logger.info(f"{status_icon} {task_id}: {passed_checks}/{total_checks} deliverables verified")
                
                # Collect action items
                if task_results.get('action_items'):
                    self.results['action_items'].extend([
                        f"{task_id}: {item}" for item in task_results['action_items']
                    ])
                
            except Exception as e:
                logger.error(f"❌ Error verifying {task_id}: {str(e)}")
                self.results['task_results'][task_id] = {
                    'name': task_name,
                    'error': str(e),
                    'status': 'verification_failed',
                    'timestamp': datetime.now().isoformat()
                }
                self.results['action_items'].append(f"{task_id}: Fix verification error - {str(e)}")
        
        # Generate final report
        await self._generate_final_report()
        
        # Cleanup
        await self._cleanup_test_environment()
        
        return self.results
    
    async def _setup_test_environment(self):
        """Setup test data and environment"""
        logger.info("🔧 Setting up test environment...")
        try:
            await self.test_data_factory.setup()
            logger.info("✅ Test environment setup complete")
        except Exception as e:
            logger.error(f"❌ Test environment setup failed: {str(e)}")
            # Continue anyway - some tests might still work
    
    async def _run_infrastructure_tests(self) -> Dict[str, Any]:
        """Run infrastructure and connectivity tests"""
        infrastructure_tests = InfrastructureTests()
        
        tests = {
            'supabase_connection': infrastructure_tests.test_supabase_connection,
            'supabase_tables': infrastructure_tests.test_database_tables,
            'redis_connection': infrastructure_tests.test_redis_connection,
            'redis_rate_limiting': infrastructure_tests.test_redis_rate_limiting,
            'email_service': infrastructure_tests.test_email_service,
            'environment_config': infrastructure_tests.test_environment_config,
            'rls_policies': infrastructure_tests.test_rls_policies
        }
        
        return await self._run_test_category(tests, "Infrastructure")
    
    async def _run_api_tests(self) -> Dict[str, Any]:
        """Run API endpoint tests for all completed tasks"""
        api_tests = APIEndpointTests()
        
        tests = {
            # Task 7: Profile System
            'profile_completion_api': api_tests.test_profile_completion,
            'profile_retrieval_api': api_tests.test_profile_retrieval,
            
            # Task 8: Distance/Matching
            'buddy_candidates_api': api_tests.test_buddy_candidates,
            'distance_calculation_api': api_tests.test_distance_calculation,
            
            # Task 9: Auto-matching
            'auto_matching_api': api_tests.test_auto_matching,
            
            # Task 10: Match responses
            'match_response_api': api_tests.test_match_response,
            
            # Task 11: Chat system
            'chat_messages_api': api_tests.test_chat_messages,
            'chat_send_api': api_tests.test_chat_send,
            
            # Task 12: Challenges
            'challenges_api': api_tests.test_challenges_endpoint,
            'challenges_caching': api_tests.test_challenges_caching,
            
            # Task 13: Session creation
            'session_creation_api': api_tests.test_session_creation,
            'session_validation': api_tests.test_session_validation
        }
        
        return await self._run_test_category(tests, "API Endpoints")
    
    async def _run_frontend_tests(self) -> Dict[str, Any]:
        """Run frontend component and page tests"""
        frontend_tests = FrontendComponentTests()
        
        tests = {
            'homepage_load': frontend_tests.test_homepage_load,
            'authentication_flow': frontend_tests.test_authentication_flow,
            'confidence_assessment': frontend_tests.test_confidence_assessment_flow,
            'profile_setup_form': frontend_tests.test_profile_setup_form,
            'photo_upload': frontend_tests.test_photo_upload,
            'chat_interface': frontend_tests.test_chat_interface,
            'venue_suggestions': frontend_tests.test_venue_suggestions,
            'navigation_flow': frontend_tests.test_navigation_flow,
            'responsive_design': frontend_tests.test_responsive_design
        }
        
        return await self._run_test_category(tests, "Frontend Components")
    
    async def _run_integration_tests(self) -> Dict[str, Any]:
        """Run complete user journey integration tests"""
        integration_tests = IntegrationFlowTests()
        
        tests = {
            'complete_onboarding': integration_tests.test_complete_user_onboarding,
            'matching_to_chat_flow': integration_tests.test_matching_to_chat_flow,
            'session_scheduling_flow': integration_tests.test_session_scheduling_flow,
            'error_handling_flows': integration_tests.test_error_handling_flows,
            'database_consistency': integration_tests.test_database_consistency,
            'authentication_security': integration_tests.test_authentication_security
        }
        
        return await self._run_test_category(tests, "Integration Flows")
    
    async def _run_performance_tests(self) -> Dict[str, Any]:
        """Run basic performance and load tests"""
        performance_tests = BasicPerformanceTests()
        
        tests = {
            'api_response_times': performance_tests.test_api_response_times,
            'database_query_performance': performance_tests.test_database_performance,
            'frontend_page_load_times': performance_tests.test_frontend_performance,
            'concurrent_user_simulation': performance_tests.test_concurrent_users,
            'rate_limiting_behavior': performance_tests.test_rate_limiting_behavior
        }
        
        return await self._run_test_category(tests, "Performance")
    
    async def _run_test_category(self, tests: Dict[str, callable], category_name: str) -> Dict[str, Any]:
        """
        Run a category of tests with resilient execution
        """
        results = {}
        
        for test_name, test_function in tests.items():
            try:
                logger.info(f"  🧪 Running {test_name}...")
                start_time = time.time()
                
                result = await test_function()
                execution_time = time.time() - start_time
                
                results[test_name] = {
                    'status': 'pass' if result.get('success', False) else 'fail',
                    'execution_time': execution_time,
                    'details': result,
                    'timestamp': datetime.now().isoformat()
                }
                
                status_icon = "✅" if result.get('success', False) else "❌"
                logger.info(f"    {status_icon} {test_name}: {execution_time:.2f}s")
                
            except Exception as e:
                results[test_name] = {
                    'status': 'error',
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }
                logger.error(f"    ❌ {test_name}: ERROR - {str(e)}")
        
        return results
    
    async def _generate_final_report(self):
        """Generate comprehensive final report"""
        end_time = datetime.now()
        total_duration = (end_time - self.start_time).total_seconds()
        
        # Calculate summary statistics
        total_tests = 0
        passed_tests = 0
        failed_tests = 0
        error_tests = 0
        
        for category, tests in self.results.items():
            if isinstance(tests, dict) and 'error' not in tests:
                for test_name, test_result in tests.items():
                    total_tests += 1
                    status = test_result.get('status', 'unknown')
                    if status == 'pass':
                        passed_tests += 1
                    elif status == 'fail':
                        failed_tests += 1
                    elif status == 'error':
                        error_tests += 1
        
        self.results['summary'] = {
            'start_time': self.start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'total_duration_seconds': total_duration,
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'error_tests': error_tests,
            'success_rate': (passed_tests / total_tests * 100) if total_tests > 0 else 0
        }
        
        # Generate reports
        await self.reporter.generate_console_report(self.results)
        await self.reporter.generate_html_report(self.results)
        await self.reporter.generate_json_report(self.results)
        
        logger.info(f"\n{'='*80}")
        logger.info(f"🎯 FINAL SUMMARY")
        logger.info(f"{'='*80}")
        logger.info(f"📊 Total Tests: {total_tests}")
        logger.info(f"✅ Passed: {passed_tests}")
        logger.info(f"❌ Failed: {failed_tests}")
        logger.info(f"🔥 Errors: {error_tests}")
        logger.info(f"📈 Success Rate: {self.results['summary']['success_rate']:.1f}%")
        logger.info(f"⏱️  Total Duration: {total_duration:.1f} seconds")
        logger.info(f"{'='*80}")
    
    async def _cleanup_test_environment(self):
        """Cleanup test data and connections"""
        try:
            await self.test_data_factory.cleanup()
            logger.info("🧹 Test environment cleanup complete")
        except Exception as e:
            logger.error(f"❌ Cleanup error: {str(e)}")

async def main():
    """Main entry point for task-by-task verification"""
    verification_suite = TaskByTaskVerification()
    
    try:
        results = await verification_suite.run_all_verifications()
        
        # Exit with appropriate code based on verification results
        failed_tasks = sum(1 for task_result in results.get('task_results', {}).values() 
                          if task_result.get('results', {}).get('overall_status') != 'pass')
        
        if failed_tasks > 0:
            logger.info(f"🚨 {failed_tasks} tasks have incomplete or failing deliverables")
            sys.exit(1)  # Indicate failures
        else:
            logger.info("🎉 All tasks verified successfully - project ready!")
            sys.exit(0)  # Success
            
    except KeyboardInterrupt:
        logger.info("🛑 Verification interrupted by user")
        sys.exit(2)
    except Exception as e:
        logger.error(f"💥 Fatal error: {str(e)}")
        sys.exit(3)

if __name__ == "__main__":
    # Create logs directory if it doesn't exist
    Path("tests/logs").mkdir(exist_ok=True)
    
    # Run the comprehensive test suite
    asyncio.run(main())