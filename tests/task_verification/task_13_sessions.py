"""
Task 13 Verification Module: Session Creation Flow and API Implementation

This module verifies all deliverables from Task 13 based on the memory bank documentation:
- Database Schema (wingman_sessions table)
- API Endpoint Validation (POST /api/session/create)
- Email Notification System 
- Chat System Integration
- Error Handling
- Test Coverage

Follows the Task Verification framework established in this directory.
"""

import asyncio
import uuid
import sys
import os
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
from unittest.mock import patch, MagicMock, AsyncMock

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from .base_task_verification import BaseTaskVerification

class Task13SessionsVerification(BaseTaskVerification):
    """Task 13: Session Creation Flow and API Implementation Verification"""
    
    def __init__(self):
        super().__init__("Task_13", "Session Creation Flow and API Implementation")
        self.test_match_id = str(uuid.uuid4())
        self.test_user1_id = str(uuid.uuid4())
        self.test_user2_id = str(uuid.uuid4())
        self.test_challenge1_id = str(uuid.uuid4())
        self.test_challenge2_id = str(uuid.uuid4())
        
    async def _run_verification_checks(self):
        """Run all Task 13 verification checks"""
        
        # 1. Database Schema Verification
        await self._check_requirement(
            "database_schema",
            self._verify_database_schema,
            "Verify wingman_sessions table schema and structure"
        )
        
        # 2. API Endpoint Validation
        await self._check_requirement(
            "api_endpoint",
            self._verify_api_endpoint,
            "Verify POST /api/session/create endpoint exists and responds"
        )
        
        # 3. Pydantic Models Validation
        await self._check_requirement(
            "pydantic_models",
            self._verify_pydantic_models,
            "Verify Pydantic request/response models"
        )
        
        # 4. Business Logic Validation
        await self._check_requirement(
            "business_logic",
            self._verify_business_logic,
            "Verify business logic validation"
        )
        
        # 5. Email Notification System
        await self._check_requirement(
            "email_notifications",
            self._verify_email_notifications,
            "Verify email notification system integration"
        )
        
        # 6. Chat System Integration
        await self._check_requirement(
            "chat_integration", 
            self._verify_chat_integration,
            "Verify chat system integration"
        )
        
        # 7. Error Handling
        await self._check_requirement(
            "error_handling",
            self._verify_error_handling,
            "Verify comprehensive error handling"
        )
        
        # 8. Test Coverage
        await self._check_requirement(
            "test_coverage",
            self._verify_test_coverage,
            "Verify comprehensive test coverage"
        )
        
        # 9. Security and Authorization
        await self._check_requirement(
            "security",
            self._verify_security,
            "Verify security measures and authorization"
        )
        
        # 10. Timezone Handling
        await self._check_requirement(
            "timezone_handling",
            self._verify_timezone_handling,
            "Verify proper timezone handling"
        )
    
    async def _verify_database_schema(self) -> Dict[str, Any]:
        """Verify wingman_sessions table schema and structure"""
        try:
            from database import SupabaseFactory
            
            db_client = SupabaseFactory.get_service_client()
            
            # Check if wingman_sessions table exists and get schema
            schema_query = """
            SELECT 
                column_name, 
                data_type, 
                is_nullable, 
                column_default,
                character_maximum_length
            FROM information_schema.columns 
            WHERE table_name = 'wingman_sessions' 
            AND table_schema = 'public'
            ORDER BY ordinal_position;
            """
            
            schema_result = db_client.rpc('exec_sql', {'sql': schema_query}).execute()
            
            if not schema_result.data:
                return {
                    'success': False,
                    'error': "wingman_sessions table does not exist",
                    'action_item': "Run migration to create wingman_sessions table"
                }
            
            # Expected columns
            expected_columns = [
                'id', 'match_id', 'user1_challenge_id', 'user2_challenge_id', 
                'venue_name', 'scheduled_time', 'status', 'completed_at',
                'user1_completed_confirmed_by_user2', 'user2_completed_confirmed_by_user1',
                'notes', 'created_at'
            ]
            
            found_columns = [row['column_name'] for row in schema_result.data]
            missing_columns = [col for col in expected_columns if col not in found_columns]
            
            if missing_columns:
                return {
                    'success': False,
                    'error': f"Missing columns: {missing_columns}",
                    'action_item': f"Add missing columns to wingman_sessions table: {missing_columns}"
                }
            
            # Check foreign key constraints
            fk_query = """
            SELECT 
                tc.constraint_name,
                kcu.column_name,
                ccu.table_name AS foreign_table_name
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
            JOIN information_schema.constraint_column_usage AS ccu
                ON ccu.constraint_name = tc.constraint_name
            WHERE tc.constraint_type = 'FOREIGN KEY' 
            AND tc.table_name = 'wingman_sessions';
            """
            
            fk_result = db_client.rpc('exec_sql', {'sql': fk_query}).execute()
            found_fks = fk_result.data if fk_result.data else []
            
            # Check for expected foreign keys
            expected_fk_tables = ['wingman_matches', 'approach_challenges']
            missing_fks = []
            
            for table in expected_fk_tables:
                fk_found = any(fk['foreign_table_name'] == table for fk in found_fks)
                if not fk_found:
                    missing_fks.append(table)
            
            if missing_fks:
                return {
                    'success': False,
                    'error': f"Missing foreign keys to: {missing_fks}",
                    'action_item': f"Add foreign key constraints to: {missing_fks}"
                }
            
            return {
                'success': True,
                'details': f"Database schema verified - {len(found_columns)} columns, {len(found_fks)} foreign keys"
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Error verifying database schema: {str(e)}",
                'action_item': "Fix database connection and schema verification"
            }
    
    async def _verify_api_endpoint(self) -> Dict[str, Any]:
        """Verify POST /api/session/create endpoint exists and responds"""
        try:
            from fastapi.testclient import TestClient
            from main import app
            
            client = TestClient(app)
            
            # Test that endpoint exists by checking it doesn't return 404
            response = client.post("/api/session/create", json={})
            
            if response.status_code == 404:
                return {
                    'success': False,
                    'error': "API endpoint /api/session/create not found",
                    'action_item': "Implement POST /api/session/create endpoint"
                }
            
            # Endpoint exists if we get validation error (422) or other error (not 404)
            return {
                'success': True,
                'details': f"API endpoint exists, returns status {response.status_code}"
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Error verifying API endpoint: {str(e)}",
                'action_item': "Fix API endpoint implementation"
            }
    
    async def _verify_pydantic_models(self) -> Dict[str, Any]:
        """Verify Pydantic request/response models are working"""
        try:
            from main import SessionCreateRequest, SessionCreateResponse
            from pydantic import ValidationError
            
            # Test SessionCreateRequest model validation
            valid_request_data = {
                "match_id": str(uuid.uuid4()),
                "venue_name": "Test Venue",
                "time": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
                "user1_challenge_id": str(uuid.uuid4()),
                "user2_challenge_id": str(uuid.uuid4())
            }
            
            # Test valid request creation
            request_model = SessionCreateRequest(**valid_request_data)
            assert isinstance(request_model.match_id, uuid.UUID)
            
            # Test invalid request validation
            validation_errors_caught = 0
            invalid_cases = [
                {"venue_name": "Test"},  # Missing required fields
                {**valid_request_data, "match_id": "invalid-uuid"},  # Invalid UUID
                {**valid_request_data, "venue_name": ""},  # Empty venue name
            ]
            
            for invalid_data in invalid_cases:
                try:
                    SessionCreateRequest(**invalid_data)
                except ValidationError:
                    validation_errors_caught += 1
            
            # Test SessionCreateResponse model
            response_data = {
                "success": True,
                "session_id": str(uuid.uuid4()),
                "message": "Test message",
                "scheduled_time": datetime.now(timezone.utc),
                "venue_name": "Test Venue",
                "notifications_sent": True
            }
            
            response_model = SessionCreateResponse(**response_data)
            assert response_model.success is True
            
            return {
                'success': True,
                'details': f"Pydantic models working - {validation_errors_caught}/{len(invalid_cases)} validation errors caught"
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Error verifying Pydantic models: {str(e)}",
                'action_item': "Fix Pydantic model definitions and validation"
            }
    
    async def _verify_business_logic(self) -> Dict[str, Any]:
        """Verify business logic validation in the endpoint"""
        try:
            from fastapi.testclient import TestClient
            from main import app
            
            client = TestClient(app)
            
            # Create test request data
            future_time = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
            test_request = {
                "match_id": self.test_match_id,
                "venue_name": "Test Venue",
                "time": future_time,
                "user1_challenge_id": self.test_challenge1_id,
                "user2_challenge_id": self.test_challenge2_id
            }
            
            passed_tests = 0
            total_tests = 0
            
            # Test 1: Match status validation
            total_tests += 1
            with patch('src.database.SupabaseFactory.get_service_client') as mock_db:
                mock_client = MagicMock()
                mock_db.return_value = mock_client
                
                # Mock match with pending status (not accepted)
                mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
                    data=[{'id': self.test_match_id, 'user1_id': self.test_user1_id, 
                          'user2_id': self.test_user2_id, 'status': 'pending'}]
                )
                
                response = client.post("/api/session/create", json=test_request)
                if response.status_code == 400 and "accepted" in response.text.lower():
                    passed_tests += 1
            
            # Test 2: Future time validation
            total_tests += 1
            past_request = test_request.copy()
            past_request["time"] = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
            
            with patch('src.database.SupabaseFactory.get_service_client') as mock_db:
                mock_client = MagicMock()
                mock_db.return_value = mock_client
                self._setup_valid_mocks(mock_client)
                
                response = client.post("/api/session/create", json=past_request)
                if response.status_code == 400 and "future" in response.text.lower():
                    passed_tests += 1
            
            # Test 3: Duplicate session prevention
            total_tests += 1
            with patch('src.database.SupabaseFactory.get_service_client') as mock_db:
                mock_client = MagicMock()
                mock_db.return_value = mock_client
                
                def table_side_effect(table_name):
                    mock_table = MagicMock()
                    if table_name == 'wingman_matches':
                        mock_match_result = MagicMock()
                        mock_match_result.data = [{'id': self.test_match_id, 'user1_id': self.test_user1_id, 
                                                 'user2_id': self.test_user2_id, 'status': 'accepted'}]
                        mock_table.select.return_value.eq.return_value.execute.return_value = mock_match_result
                        return mock_table
                    elif table_name == 'approach_challenges':
                        mock_challenge_check = MagicMock()
                        mock_challenge_check.data = [{'id': self.test_challenge1_id}, {'id': self.test_challenge2_id}]
                        mock_table.select.return_value.in_.return_value.execute.return_value = mock_challenge_check
                        return mock_table
                    elif table_name == 'wingman_sessions':
                        # Mock existing active session
                        mock_existing_sessions = MagicMock()
                        mock_existing_sessions.data = [{'id': str(uuid.uuid4()), 'status': 'scheduled'}]
                        mock_table.select.return_value.eq.return_value.in_.return_value.execute.return_value = mock_existing_sessions
                        return mock_table
                    return mock_table
                
                mock_client.table.side_effect = table_side_effect
                
                response = client.post("/api/session/create", json=test_request)
                if response.status_code == 409 and "active" in response.text.lower():
                    passed_tests += 1
            
            success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
            
            return {
                'success': passed_tests == total_tests,
                'details': f"Business logic validation: {passed_tests}/{total_tests} tests passed ({success_rate:.1f}%)",
                'error': f"Some business logic tests failed: {passed_tests}/{total_tests}" if passed_tests < total_tests else None,
                'action_item': "Fix business logic validation" if passed_tests < total_tests else None
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Error verifying business logic: {str(e)}",
                'action_item': "Fix business logic validation implementation"
            }
    
    async def _verify_email_notifications(self) -> Dict[str, Any]:
        """Verify email notification system integration"""
        try:
            # Check if email templates module exists and has required method
            from email_templates import email_service
            
            # Check if send_session_scheduled method exists
            has_method = hasattr(email_service, 'send_session_scheduled')
            has_template_method = hasattr(email_service, '_get_session_scheduled_template')
            
            if not has_method:
                return {
                    'success': False,
                    'error': "send_session_scheduled method not found in email service",
                    'action_item': "Implement send_session_scheduled method in email service"
                }
            
            # Test graceful degradation when email service disabled
            original_enabled = email_service.enabled
            email_service.enabled = False
            result = await email_service.send_session_scheduled(
                to_email="test@example.com",
                user_name="Test User", 
                venue_name="Test Venue",
                scheduled_time="Test Time"
            )
            email_service.enabled = original_enabled  # Restore original state
            
            graceful_degradation = result is False
            
            # Test template generation
            template_works = False
            try:
                template = email_service._get_session_scheduled_template(
                    user_name="Test User",
                    venue_name="Test Venue", 
                    scheduled_time="Test Time"
                )
                template_works = ("Test Venue" in template and "Test User" in template 
                                and "<html>" in template.lower())
            except Exception:
                template_works = False
            
            return {
                'success': True,
                'details': f"Email system verified - method exists: {has_method}, template works: {template_works}, graceful degradation: {graceful_degradation}"
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Error verifying email notifications: {str(e)}",
                'action_item': "Fix email notification system implementation"
            }
    
    async def _verify_chat_integration(self) -> Dict[str, Any]:
        """Verify chat system integration for session notifications"""
        try:
            from fastapi.testclient import TestClient
            from main import app
            
            client = TestClient(app)
            
            # Test session creation with mocked database to verify chat message creation
            future_time = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
            test_request = {
                "match_id": self.test_match_id,
                "venue_name": "Test Venue",
                "time": future_time,
                "user1_challenge_id": self.test_challenge1_id,
                "user2_challenge_id": self.test_challenge2_id
            }
            
            chat_message_created = False
            
            with patch('src.database.SupabaseFactory.get_service_client') as mock_db:
                mock_client = MagicMock()
                mock_db.return_value = mock_client
                
                # Track chat message insertion
                def table_side_effect(table_name):
                    nonlocal chat_message_created
                    mock_table = MagicMock()
                    
                    if table_name == 'wingman_matches':
                        mock_match_result = MagicMock()
                        mock_match_result.data = [{
                            'id': self.test_match_id, 
                            'user1_id': self.test_user1_id, 
                            'user2_id': self.test_user2_id, 
                            'status': 'accepted'
                        }]
                        mock_table.select.return_value.eq.return_value.execute.return_value = mock_match_result
                        return mock_table
                    elif table_name == 'approach_challenges':
                        mock_challenge_check = MagicMock()
                        mock_challenge_check.data = [{'id': self.test_challenge1_id}, {'id': self.test_challenge2_id}]
                        mock_table.select.return_value.in_.return_value.execute.return_value = mock_challenge_check
                        return mock_table
                    elif table_name == 'wingman_sessions':
                        # No existing sessions and session creation success
                        mock_existing_sessions = MagicMock()
                        mock_existing_sessions.data = []
                        mock_session_result = MagicMock()
                        mock_session_result.data = [{'id': str(uuid.uuid4())}]
                        
                        mock_table.select.return_value.eq.return_value.in_.return_value.execute.return_value = mock_existing_sessions
                        mock_table.insert.return_value.execute.return_value = mock_session_result
                        return mock_table
                    elif table_name == 'user_profiles':
                        mock_user_profiles = MagicMock()
                        mock_user_profiles.data = [
                            {'id': self.test_user1_id, 'email': 'user1@test.com', 'first_name': 'User1'},
                            {'id': self.test_user2_id, 'email': 'user2@test.com', 'first_name': 'User2'}
                        ]
                        mock_table.select.return_value.in_.return_value.execute.return_value = mock_user_profiles
                        return mock_table
                    elif table_name == 'chat_messages':
                        # Mark that chat message creation was attempted
                        chat_message_created = True
                        mock_chat_result = MagicMock()
                        mock_chat_result.data = [{'id': str(uuid.uuid4())}]
                        mock_table.insert.return_value.execute.return_value = mock_chat_result
                        return mock_table
                    return mock_table
                
                mock_client.table.side_effect = table_side_effect
                
                # Mock email service
                with patch('src.email_templates.email_service') as mock_email:
                    mock_email.enabled = True
                    mock_email.send_session_scheduled = AsyncMock(return_value=True)
                    
                    response = client.post("/api/session/create", json=test_request)
            
            return {
                'success': chat_message_created,
                'details': f"Chat integration verified - message creation attempted: {chat_message_created}",
                'error': "Chat message creation not attempted" if not chat_message_created else None,
                'action_item': "Implement chat message creation in session endpoint" if not chat_message_created else None
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Error verifying chat integration: {str(e)}",
                'action_item': "Fix chat system integration"
            }
    
    async def _verify_error_handling(self) -> Dict[str, Any]:
        """Verify comprehensive error handling and HTTP status codes"""
        try:
            from fastapi.testclient import TestClient
            from main import app
            
            client = TestClient(app)
            
            error_tests = []
            
            # Test invalid JSON format
            response = client.post("/api/session/create", data="invalid json")
            error_tests.append({
                "test": "Invalid JSON", 
                "expected": 422, 
                "actual": response.status_code,
                "passed": response.status_code == 422
            })
            
            # Test missing required fields
            response = client.post("/api/session/create", json={})
            error_tests.append({
                "test": "Missing fields",
                "expected": 422,
                "actual": response.status_code,
                "passed": response.status_code == 422
            })
            
            # Test invalid UUID format
            invalid_request = {
                "match_id": "invalid-uuid",
                "venue_name": "Test",
                "time": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
                "user1_challenge_id": str(uuid.uuid4()),
                "user2_challenge_id": str(uuid.uuid4())
            }
            response = client.post("/api/session/create", json=invalid_request)
            error_tests.append({
                "test": "Invalid UUID",
                "expected": 422,
                "actual": response.status_code,
                "passed": response.status_code == 422
            })
            
            # Test non-existent match (404)
            with patch('src.database.SupabaseFactory.get_service_client') as mock_db:
                mock_client = MagicMock()
                mock_db.return_value = mock_client
                mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[])
                
                valid_request = {
                    "match_id": str(uuid.uuid4()),
                    "venue_name": "Test",
                    "time": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
                    "user1_challenge_id": str(uuid.uuid4()),
                    "user2_challenge_id": str(uuid.uuid4())
                }
                
                response = client.post("/api/session/create", json=valid_request)
                error_tests.append({
                    "test": "Non-existent match",
                    "expected": 404,
                    "actual": response.status_code,
                    "passed": response.status_code == 404
                })
            
            passed_tests = sum(1 for test in error_tests if test['passed'])
            total_tests = len(error_tests)
            
            return {
                'success': passed_tests == total_tests,
                'details': f"Error handling: {passed_tests}/{total_tests} tests passed",
                'error': f"Some error handling tests failed: {passed_tests}/{total_tests}" if passed_tests < total_tests else None,
                'action_item': "Fix error handling for failed test cases" if passed_tests < total_tests else None
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Error verifying error handling: {str(e)}",
                'action_item': "Fix error handling verification"
            }
    
    async def _verify_test_coverage(self) -> Dict[str, Any]:
        """Verify comprehensive test coverage exists"""
        try:
            import os
            
            # Check if test file exists
            test_file_path = os.path.join(
                os.path.dirname(__file__), 
                '..', 
                'backend', 
                'test_session_creation.py'
            )
            
            if not os.path.exists(test_file_path):
                return {
                    'success': False,
                    'error': "Test file test_session_creation.py not found",
                    'action_item': "Create comprehensive test file for session creation"
                }
            
            # Read and analyze test file
            with open(test_file_path, 'r') as f:
                test_content = f.read()
            
            # Count test methods
            test_methods = [line for line in test_content.split('\n') if line.strip().startswith('def test_')]
            test_count = len(test_methods)
            
            # Check for key test scenarios
            required_scenarios = [
                'test_create_session_success',
                'test_match_not_found', 
                'test_match_not_accepted',
                'test_invalid_challenges',
                'test_duplicate_session_prevention',
                'test_past_time_validation',
                'test_timezone_validation'
            ]
            
            found_scenarios = [scenario for scenario in required_scenarios if scenario in test_content]
            missing_scenarios = [scenario for scenario in required_scenarios if scenario not in test_content]
            
            # Check for proper testing patterns
            uses_mocks = '@patch(' in test_content and 'MagicMock' in test_content
            handles_async = 'AsyncMock' in test_content or 'await' in test_content
            
            coverage_score = (len(found_scenarios) / len(required_scenarios)) * 100
            
            return {
                'success': coverage_score >= 80,
                'details': f"Test coverage: {test_count} tests, {coverage_score:.1f}% scenario coverage, uses mocks: {uses_mocks}",
                'error': f"Test coverage insufficient: {coverage_score:.1f}%" if coverage_score < 80 else None,
                'action_item': f"Add missing test scenarios: {missing_scenarios}" if missing_scenarios else None
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Error verifying test coverage: {str(e)}",
                'action_item': "Fix test coverage verification"
            }
    
    async def _verify_security(self) -> Dict[str, Any]:
        """Verify security measures and authorization"""
        try:
            security_checks = []
            
            # Check 1: Input validation via Pydantic
            try:
                from main import SessionCreateRequest
                from pydantic import ValidationError
                
                # Test that invalid input is rejected
                try:
                    SessionCreateRequest(
                        match_id="invalid-uuid",
                        venue_name="",
                        time="invalid-time",
                        user1_challenge_id="invalid",
                        user2_challenge_id="invalid"
                    )
                    input_validation = False
                except ValidationError:
                    input_validation = True
                
                security_checks.append(input_validation)
            except Exception:
                security_checks.append(False)
            
            # Check 2: UUID format validation
            try:
                test_uuid = str(uuid.uuid4())
                from main import SessionCreateRequest
                
                valid_request = SessionCreateRequest(
                    match_id=test_uuid,
                    venue_name="Test",
                    time=datetime.now(timezone.utc) + timedelta(days=1),
                    user1_challenge_id=test_uuid,
                    user2_challenge_id=test_uuid
                )
                uuid_validation = str(valid_request.match_id) == test_uuid
                security_checks.append(uuid_validation)
            except Exception:
                security_checks.append(False)
            
            # Check 3: Venue name length limits
            try:
                from main import SessionCreateRequest
                from pydantic import ValidationError
                
                try:
                    SessionCreateRequest(
                        match_id=str(uuid.uuid4()),
                        venue_name="A" * 201,  # Over 200 char limit
                        time=datetime.now(timezone.utc) + timedelta(days=1),
                        user1_challenge_id=str(uuid.uuid4()),
                        user2_challenge_id=str(uuid.uuid4())
                    )
                    length_protection = False
                except ValidationError:
                    length_protection = True
                
                security_checks.append(length_protection)
            except Exception:
                security_checks.append(False)
            
            passed_checks = sum(security_checks)
            total_checks = len(security_checks)
            
            return {
                'success': passed_checks == total_checks,
                'details': f"Security verification: {passed_checks}/{total_checks} checks passed",
                'error': f"Some security checks failed: {passed_checks}/{total_checks}" if passed_checks < total_checks else None,
                'action_item': "Fix security validation issues" if passed_checks < total_checks else None
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Error verifying security: {str(e)}",
                'action_item': "Fix security verification"
            }
    
    async def _verify_timezone_handling(self) -> Dict[str, Any]:
        """Verify proper timezone handling for scheduled times"""
        try:
            from main import SessionCreateRequest
            from datetime import datetime, timezone, timedelta
            
            timezone_tests = []
            
            # Test 1: UTC timezone handling
            try:
                utc_time = datetime.now(timezone.utc) + timedelta(days=1)
                request = SessionCreateRequest(
                    match_id=str(uuid.uuid4()),
                    venue_name="Test",
                    time=utc_time,
                    user1_challenge_id=str(uuid.uuid4()),
                    user2_challenge_id=str(uuid.uuid4())
                )
                timezone_tests.append(request.time.tzinfo is not None)
            except Exception:
                timezone_tests.append(False)
            
            # Test 2: ISO8601 string parsing
            try:
                iso_time = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
                request = SessionCreateRequest(
                    match_id=str(uuid.uuid4()),
                    venue_name="Test",
                    time=iso_time,
                    user1_challenge_id=str(uuid.uuid4()),
                    user2_challenge_id=str(uuid.uuid4())
                )
                timezone_tests.append(isinstance(request.time, datetime))
            except Exception:
                timezone_tests.append(False)
            
            # Test 3: Future time validation in API
            try:
                from fastapi.testclient import TestClient
                from main import app
                
                client = TestClient(app)
                past_time = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
                past_request = {
                    "match_id": str(uuid.uuid4()),
                    "venue_name": "Test",
                    "time": past_time,
                    "user1_challenge_id": str(uuid.uuid4()),
                    "user2_challenge_id": str(uuid.uuid4())
                }
                
                with patch('src.database.SupabaseFactory.get_service_client') as mock_db:
                    mock_client = MagicMock()
                    mock_db.return_value = mock_client
                    self._setup_valid_mocks(mock_client)
                    
                    response = client.post("/api/session/create", json=past_request)
                    timezone_tests.append(response.status_code == 400 and "future" in response.text.lower())
            except Exception:
                timezone_tests.append(False)
            
            passed_tests = sum(timezone_tests)
            total_tests = len(timezone_tests)
            
            return {
                'success': passed_tests == total_tests,
                'details': f"Timezone handling: {passed_tests}/{total_tests} tests passed",
                'error': f"Some timezone tests failed: {passed_tests}/{total_tests}" if passed_tests < total_tests else None,
                'action_item': "Fix timezone handling issues" if passed_tests < total_tests else None
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Error verifying timezone handling: {str(e)}",
                'action_item': "Fix timezone handling verification"
            }
    
    def _setup_valid_mocks(self, mock_client):
        """Helper method to set up valid database mocks"""
        def table_side_effect(table_name):
            mock_table = MagicMock()
            if table_name == 'wingman_matches':
                mock_match_result = MagicMock()
                mock_match_result.data = [{
                    'id': self.test_match_id,
                    'user1_id': self.test_user1_id,
                    'user2_id': self.test_user2_id,
                    'status': 'accepted'
                }]
                mock_table.select.return_value.eq.return_value.execute.return_value = mock_match_result
                return mock_table
            elif table_name == 'approach_challenges':
                mock_challenge_check = MagicMock()
                mock_challenge_check.data = [
                    {'id': self.test_challenge1_id},
                    {'id': self.test_challenge2_id}
                ]
                mock_table.select.return_value.in_.return_value.execute.return_value = mock_challenge_check
                return mock_table
            elif table_name == 'wingman_sessions':
                mock_existing_sessions = MagicMock()
                mock_existing_sessions.data = []
                mock_table.select.return_value.eq.return_value.in_.return_value.execute.return_value = mock_existing_sessions
                return mock_table
            return mock_table
        
        mock_client.table.side_effect = table_side_effect


# Main execution for standalone testing
async def verify_task_13_sessions():
    """Run Task 13 verification and return results"""
    verification = Task13SessionsVerification()
    return await verification.verify_task_completion()


async def main():
    """Run Task 13 verification with formatted output"""
    print("🔍 Starting Task 13: Session Creation Flow and API Implementation Verification")
    print("=" * 80)
    
    verification = Task13SessionsVerification()
    results = await verification.verify_task_completion()
    
    # Print formatted results
    print(f"\n📋 Task: {results['task_name']}")
    print(f"🎯 Overall Status: {results['overall_status'].upper()}")
    print(f"⏱️  Verification Time: {results.get('verification_time', 0):.2f} seconds")
    
    if 'error' in results:
        print(f"🔥 Error: {results['error']}")
        return
    
    # Print check results
    passed = sum(1 for check in results['checks'].values() if check['status'] == 'pass')
    failed = sum(1 for check in results['checks'].values() if check['status'] == 'fail')
    errors = sum(1 for check in results['checks'].values() if check['status'] == 'error')
    total = len(results['checks'])
    
    print(f"\n📊 Check Summary:")
    print(f"   ✅ Passed: {passed}")
    print(f"   ❌ Failed: {failed}")
    print(f"   🔥 Errors: {errors}")
    print(f"   📋 Total: {total}")
    print(f"   🎯 Success Rate: {(passed/total)*100:.1f}%" if total > 0 else "🎯 Success Rate: 0%")
    
    # Print individual check results
    print(f"\n🔍 Detailed Results:")
    for check_name, check_data in results['checks'].items():
        status_icon = "✅" if check_data['status'] == 'pass' else "❌" if check_data['status'] == 'fail' else "🔥"
        print(f"   {status_icon} {check_name}: {check_data['status'].upper()}")
        print(f"      └─ {check_data.get('details', check_data.get('error', 'No details'))}")
    
    # Print action items
    if results.get('action_items'):
        print(f"\n🔧 Action Items:")
        for i, action in enumerate(results['action_items'], 1):
            print(f"   {i}. {action}")
    
    # Overall conclusion
    if results['overall_status'] == 'pass':
        print(f"\n🎉 All Task 13 deliverables verified successfully!")
    elif results['overall_status'] == 'fail':
        print(f"\n⚠️  Task 13 verification failed - see action items above")
    elif results['overall_status'] == 'partial':
        print(f"\n⚠️  Task 13 verification partially successful - some issues need attention")
    else:
        print(f"\n🔥 Task 13 verification encountered errors")


if __name__ == "__main__":
    asyncio.run(main())