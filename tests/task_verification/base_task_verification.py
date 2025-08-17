"""
Base class for task verification modules

Provides standardized structure and utilities for verifying task completion
"""

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class BaseTaskVerification(ABC):
    """
    Abstract base class for task verification modules
    """
    
    def __init__(self, task_id: str, task_name: str):
        self.task_id = task_id
        self.task_name = task_name
        self.start_time = datetime.now()
        self.checks = {}
        self.action_items = []
        
    async def verify_task_completion(self) -> Dict[str, Any]:
        """
        Main verification method that runs all checks for this task
        """
        logger.info(f"🔍 Starting verification for {self.task_id}: {self.task_name}")
        
        try:
            # Run task-specific verification checks
            await self._run_verification_checks()
            
            # Calculate overall status
            overall_status = self._calculate_overall_status()
            
            # Generate summary
            verification_time = (datetime.now() - self.start_time).total_seconds()
            
            return {
                'task_id': self.task_id,
                'task_name': self.task_name,
                'overall_status': overall_status,
                'checks': self.checks,
                'action_items': self.action_items,
                'verification_time': verification_time,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Verification failed for {self.task_id}: {str(e)}")
            return {
                'task_id': self.task_id,
                'task_name': self.task_name,
                'overall_status': 'error',
                'error': str(e),
                'checks': self.checks,
                'action_items': self.action_items,
                'timestamp': datetime.now().isoformat()
            }
    
    @abstractmethod
    async def _run_verification_checks(self):
        """
        Implement task-specific verification checks in subclasses
        """
        pass
    
    async def _check_requirement(self, check_name: str, check_function, description: str = ""):
        """
        Helper method to run a verification check and record results
        """
        logger.info(f"  🔍 Checking: {check_name}")
        start_time = time.time()
        
        try:
            result = await check_function()
            execution_time = time.time() - start_time
            
            if result.get('success', False):
                self.checks[check_name] = {
                    'status': 'pass',
                    'description': description,
                    'execution_time': execution_time,
                    'details': result.get('details', ''),
                    'timestamp': datetime.now().isoformat()
                }
                logger.info(f"    ✅ {check_name}: PASS ({execution_time:.2f}s)")
            else:
                self.checks[check_name] = {
                    'status': 'fail',
                    'description': description,
                    'execution_time': execution_time,
                    'error': result.get('error', 'Check failed'),
                    'details': result.get('details', ''),
                    'timestamp': datetime.now().isoformat()
                }
                logger.info(f"    ❌ {check_name}: FAIL - {result.get('error', 'Unknown error')}")
                
                # Add to action items
                if result.get('action_item'):
                    self.action_items.append(result['action_item'])
                
        except Exception as e:
            execution_time = time.time() - start_time
            self.checks[check_name] = {
                'status': 'error',
                'description': description,
                'execution_time': execution_time,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
            logger.error(f"    🔥 {check_name}: ERROR - {str(e)}")
            self.action_items.append(f"Fix error in {check_name}: {str(e)}")
    
    def _calculate_overall_status(self) -> str:
        """
        Calculate overall task status based on individual checks
        """
        if not self.checks:
            return 'no_checks'
        
        statuses = [check['status'] for check in self.checks.values()]
        
        if 'error' in statuses:
            return 'error'
        elif 'fail' in statuses:
            return 'fail'
        elif all(status == 'pass' for status in statuses):
            return 'pass'
        else:
            return 'partial'
    
    async def _check_file_exists(self, file_path: str, description: str = "") -> Dict[str, Any]:
        """
        Helper to check if a file exists
        """
        try:
            from pathlib import Path
            path = Path(file_path)
            
            if path.exists():
                return {
                    'success': True,
                    'details': f"File exists: {file_path}"
                }
            else:
                return {
                    'success': False,
                    'error': f"File not found: {file_path}",
                    'action_item': f"Create missing file: {file_path}"
                }
        except Exception as e:
            return {
                'success': False,
                'error': f"Error checking file {file_path}: {str(e)}",
                'action_item': f"Fix file check error for {file_path}"
            }
    
    async def _check_api_endpoint(self, endpoint: str, method: str = 'GET', data: Dict = None, 
                                headers: Dict = None, expected_status: int = 200) -> Dict[str, Any]:
        """
        Helper to check if an API endpoint is working
        """
        try:
            import httpx
            import os
            
            base_url = os.getenv('API_BASE_URL', 'http://localhost:8000')
            url = f"{base_url}{endpoint}"
            
            # Set default headers
            if headers is None:
                headers = {}
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                if method.upper() == 'GET':
                    response = await client.get(url, headers=headers)
                elif method.upper() == 'POST':
                    response = await client.post(url, json=data, headers=headers)
                elif method.upper() == 'PUT':
                    response = await client.put(url, json=data, headers=headers)
                elif method.upper() == 'DELETE':
                    response = await client.delete(url, headers=headers)
                else:
                    return {
                        'success': False,
                        'error': f"Unsupported HTTP method: {method}",
                        'action_item': f"Use supported HTTP method for {endpoint}"
                    }
                
                if response.status_code == expected_status:
                    return {
                        'success': True,
                        'details': f"{method} {endpoint} returned {response.status_code}"
                    }
                else:
                    return {
                        'success': False,
                        'error': f"{method} {endpoint} returned {response.status_code}, expected {expected_status}",
                        'action_item': f"Fix {endpoint} to return proper status code"
                    }
                    
        except Exception as e:
            return {
                'success': False,
                'error': f"Error testing {endpoint}: {str(e)}",
                'action_item': f"Fix API endpoint {endpoint} - {str(e)}"
            }
    
    async def _check_database_table(self, table_name: str) -> Dict[str, Any]:
        """
        Helper to check if a database table exists
        """
        try:
            # Import database connection from the project
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            
            from src.config import Config
            import asyncpg
            
            # Connect to database
            conn = await asyncpg.connect(Config.SUPABASE_URL)
            
            # Check if table exists
            result = await conn.fetchval(
                "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = $1)",
                table_name
            )
            
            await conn.close()
            
            if result:
                return {
                    'success': True,
                    'details': f"Table {table_name} exists"
                }
            else:
                return {
                    'success': False,
                    'error': f"Table {table_name} does not exist",
                    'action_item': f"Create database table: {table_name}"
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f"Error checking table {table_name}: {str(e)}",
                'action_item': f"Fix database connection or create table {table_name}"
            }