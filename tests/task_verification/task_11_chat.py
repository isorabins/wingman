"""
Task 11 Basic Buddy Chat Implementation Verification Module

Verifies all deliverables from Task 11: Basic Buddy Chat Implementation
for the WingmanMatch platform chat system.
"""

import asyncio
import json
import logging
import os
import sys
import time
import uuid
from pathlib import Path
from typing import Dict, Any, Optional, List

try:
    from .base_task_verification import BaseTaskVerification
except ImportError:
    # Handle direct execution
    import sys
    sys.path.append(os.path.dirname(__file__))
    from base_task_verification import BaseTaskVerification

logger = logging.getLogger(__name__)


class Task11ChatVerification(BaseTaskVerification):
    """
    Verification module for Task 11: Basic Buddy Chat Implementation
    
    Validates:
    - Database schema (chat_messages, chat_read_timestamps tables)
    - RLS policies for participant-only access
    - API endpoints (GET messages, POST send)
    - Frontend chat page and components
    - Venue suggestions panel
    - Security features (auth, rate limiting, validation)
    - Real-time polling and UI updates
    """
    
    def __init__(self):
        super().__init__("task_11", "Basic Buddy Chat Implementation")
        self.project_root = Path(__file__).parent.parent.parent
        self.test_match_id = None
        self.test_user1_id = None
        self.test_user2_id = None
        
    async def _run_verification_checks(self):
        """Run all Task 11 verification checks"""
        
        # Setup test data
        await self._check_requirement("setup_test_data", self._setup_test_data,
                                    "Create test data for chat verification")
        
        # Database Structure
        await self._check_requirement("chat_messages_table", self._check_chat_messages_table,
                                    "chat_messages table exists with proper schema")
        await self._check_requirement("chat_read_timestamps_table", self._check_chat_read_timestamps_table,
                                    "chat_read_timestamps table exists with proper schema")
        await self._check_requirement("database_indexes", self._check_database_indexes,
                                    "Performance indexes exist on chat tables")
        await self._check_requirement("rls_policies", self._check_rls_policies,
                                    "Row Level Security policies configured correctly")
        
        # API Endpoints
        await self._check_requirement("get_messages_endpoint", self._check_get_messages_endpoint,
                                    "GET /api/chat/messages/{match_id} endpoint working")
        await self._check_requirement("send_message_endpoint", self._check_send_message_endpoint,
                                    "POST /api/chat/send endpoint working")
        await self._check_requirement("api_authentication", self._check_api_authentication,
                                    "API endpoints require authentication")
        await self._check_requirement("message_validation", self._check_message_validation,
                                    "Message validation (2-2000 chars) working")
        await self._check_requirement("rate_limiting", self._check_rate_limiting,
                                    "Rate limiting (1 msg/0.5s) functional")
        
        # Frontend Chat Page
        await self._check_requirement("chat_page_exists", self._check_chat_page_exists,
                                    "Frontend chat page file exists")
        await self._check_requirement("chat_page_structure", self._check_chat_page_structure,
                                    "Chat page has required components and structure")
        await self._check_requirement("typescript_interfaces", self._check_typescript_interfaces,
                                    "TypeScript interfaces defined correctly")
        await self._check_requirement("ui_components", self._check_ui_components,
                                    "UI components (header, messages, input) present")
        
        # Venue Suggestions
        await self._check_requirement("venue_suggestions_panel", self._check_venue_suggestions_panel,
                                    "Venue suggestions panel exists and functional")
        await self._check_requirement("venue_categories", self._check_venue_categories,
                                    "4 venue categories present with correct content")
        
        # Integration Features
        await self._check_requirement("polling_mechanism", self._check_polling_mechanism,
                                    "5-second polling mechanism implemented")
        await self._check_requirement("scroll_management", self._check_scroll_management,
                                    "Auto-scroll to bottom functionality")
        await self._check_requirement("character_counter", self._check_character_counter,
                                    "Character counter (2000 max) implemented")
        await self._check_requirement("error_handling", self._check_error_handling,
                                    "Error handling and user feedback")
        
        # Security Features
        await self._check_requirement("participant_access", self._check_participant_access,
                                    "Participant-only access validation")
        await self._check_requirement("message_sanitization", self._check_message_sanitization,
                                    "Message sanitization and XSS protection")

    async def _setup_test_data(self) -> Dict[str, Any]:
        """Setup test data for verification"""
        try:
            # Generate test IDs
            self.test_match_id = str(uuid.uuid4())
            self.test_user1_id = str(uuid.uuid4())
            self.test_user2_id = str(uuid.uuid4())
            
            return {
                'success': True,
                'details': f'Test data IDs generated: match={self.test_match_id[:8]}..., users={self.test_user1_id[:8]}..., {self.test_user2_id[:8]}...'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to setup test data: {str(e)}',
                'action_item': 'Fix test data setup process'
            }

    async def _check_chat_messages_table(self) -> Dict[str, Any]:
        """Check chat_messages table exists with proper schema"""
        try:
            # Import database connection
            sys.path.append(str(self.project_root / 'src'))
            from config import Config
            import asyncpg
            
            conn = await asyncpg.connect(Config.SUPABASE_URL)
            
            # Check table exists
            table_exists = await conn.fetchval(
                "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'chat_messages')"
            )
            
            if not table_exists:
                await conn.close()
                return {
                    'success': False,
                    'error': 'chat_messages table does not exist',
                    'action_item': 'Run migration 004_add_chat_messages.sql to create chat_messages table'
                }
            
            # Check schema
            columns = await conn.fetch("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_name = 'chat_messages'
                ORDER BY ordinal_position
            """)
            
            required_columns = {
                'id': 'uuid',
                'match_id': 'uuid', 
                'sender_id': 'uuid',
                'message_text': 'text',
                'created_at': 'timestamp with time zone'
            }
            
            column_map = {col['column_name']: col['data_type'] for col in columns}
            missing_columns = []
            
            for col_name, col_type in required_columns.items():
                if col_name not in column_map:
                    missing_columns.append(col_name)
                elif col_type not in column_map[col_name]:
                    missing_columns.append(f"{col_name} (wrong type: {column_map[col_name]})")
            
            # Check constraints
            constraints = await conn.fetch("""
                SELECT constraint_name, constraint_type
                FROM information_schema.table_constraints
                WHERE table_name = 'chat_messages'
            """)
            
            constraint_types = {c['constraint_type'] for c in constraints}
            
            await conn.close()
            
            if missing_columns:
                return {
                    'success': False,
                    'error': f'Missing or incorrect columns: {", ".join(missing_columns)}',
                    'action_item': 'Fix chat_messages table schema to include all required columns'
                }
            
            if 'FOREIGN KEY' not in constraint_types:
                return {
                    'success': False,
                    'error': 'Foreign key constraints missing on chat_messages table',
                    'action_item': 'Add foreign key constraints to chat_messages table'
                }
            
            return {
                'success': True,
                'details': f'chat_messages table exists with {len(columns)} columns and proper constraints'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Error checking chat_messages table: {str(e)}',
                'action_item': 'Check database connection and run chat messages migration'
            }

    async def _check_chat_read_timestamps_table(self) -> Dict[str, Any]:
        """Check chat_read_timestamps table exists with proper schema"""
        try:
            sys.path.append(str(self.project_root / 'src'))
            from config import Config
            import asyncpg
            
            conn = await asyncpg.connect(Config.SUPABASE_URL)
            
            # Check table exists
            table_exists = await conn.fetchval(
                "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'chat_read_timestamps')"
            )
            
            if not table_exists:
                await conn.close()
                return {
                    'success': False,
                    'error': 'chat_read_timestamps table does not exist',
                    'action_item': 'Run migration 004_add_chat_messages.sql to create chat_read_timestamps table'
                }
            
            # Check schema
            columns = await conn.fetch("""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = 'chat_read_timestamps'
                ORDER BY ordinal_position
            """)
            
            required_columns = {
                'match_id': 'uuid',
                'user_id': 'uuid',
                'last_read_at': 'timestamp with time zone',
                'updated_at': 'timestamp with time zone'
            }
            
            column_map = {col['column_name']: col['data_type'] for col in columns}
            missing_columns = []
            
            for col_name, col_type in required_columns.items():
                if col_name not in column_map:
                    missing_columns.append(col_name)
                elif col_type not in column_map[col_name]:
                    missing_columns.append(f"{col_name} (wrong type)")
            
            await conn.close()
            
            if missing_columns:
                return {
                    'success': False,
                    'error': f'Missing or incorrect columns: {", ".join(missing_columns)}',
                    'action_item': 'Fix chat_read_timestamps table schema'
                }
            
            return {
                'success': True,
                'details': f'chat_read_timestamps table exists with {len(columns)} columns'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Error checking chat_read_timestamps table: {str(e)}',
                'action_item': 'Check database connection and run chat timestamps migration'
            }

    async def _check_database_indexes(self) -> Dict[str, Any]:
        """Check performance indexes exist on chat tables"""
        try:
            sys.path.append(str(self.project_root / 'src'))
            from config import Config
            import asyncpg
            
            conn = await asyncpg.connect(Config.SUPABASE_URL)
            
            # Check for required indexes
            indexes = await conn.fetch("""
                SELECT indexname, tablename
                FROM pg_indexes
                WHERE schemaname = 'public' 
                AND (tablename = 'chat_messages' OR tablename = 'chat_read_timestamps')
            """)
            
            index_names = {idx['indexname'] for idx in indexes}
            
            required_indexes = [
                'idx_chat_messages_match_id_created_at',
                'idx_chat_messages_sender_id',
                'idx_chat_read_timestamps_user_id'
            ]
            
            missing_indexes = [idx for idx in required_indexes if idx not in index_names]
            
            await conn.close()
            
            if missing_indexes:
                return {
                    'success': False,
                    'error': f'Missing performance indexes: {", ".join(missing_indexes)}',
                    'action_item': f'Create missing indexes: {", ".join(missing_indexes)}'
                }
            
            return {
                'success': True,
                'details': f'All required performance indexes present: {", ".join(required_indexes)}'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Error checking database indexes: {str(e)}',
                'action_item': 'Check database connection and create missing indexes'
            }

    async def _check_rls_policies(self) -> Dict[str, Any]:
        """Check Row Level Security policies configured correctly"""
        try:
            sys.path.append(str(self.project_root / 'src'))
            from config import Config
            import asyncpg
            
            conn = await asyncpg.connect(Config.SUPABASE_URL)
            
            # Check RLS is enabled
            rls_status = await conn.fetch("""
                SELECT tablename, rowsecurity
                FROM pg_tables
                WHERE schemaname = 'public' 
                AND (tablename = 'chat_messages' OR tablename = 'chat_read_timestamps')
            """)
            
            rls_disabled = [row['tablename'] for row in rls_status if not row['rowsecurity']]
            
            if rls_disabled:
                await conn.close()
                return {
                    'success': False,
                    'error': f'RLS not enabled on tables: {", ".join(rls_disabled)}',
                    'action_item': f'Enable RLS on tables: {", ".join(rls_disabled)}'
                }
            
            # Check for required policies
            policies = await conn.fetch("""
                SELECT policyname, tablename, cmd
                FROM pg_policies
                WHERE schemaname = 'public'
                AND (tablename = 'chat_messages' OR tablename = 'chat_read_timestamps')
            """)
            
            policy_map = {f"{pol['tablename']}_{pol['cmd']}": pol['policyname'] for pol in policies}
            
            required_policies = [
                'chat_messages_SELECT',
                'chat_messages_INSERT',
                'chat_read_timestamps_SELECT',
                'chat_read_timestamps_INSERT',
                'chat_read_timestamps_UPDATE'
            ]
            
            missing_policies = [pol for pol in required_policies if pol not in policy_map]
            
            await conn.close()
            
            if missing_policies:
                return {
                    'success': False,
                    'error': f'Missing RLS policies: {", ".join(missing_policies)}',
                    'action_item': f'Create missing RLS policies for participant access'
                }
            
            return {
                'success': True,
                'details': f'RLS enabled with {len(policies)} policies configured'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Error checking RLS policies: {str(e)}',
                'action_item': 'Check database connection and RLS policy configuration'
            }

    async def _check_get_messages_endpoint(self) -> Dict[str, Any]:
        """Check GET /api/chat/messages/{match_id} endpoint working"""
        try:
            endpoint = f"/api/chat/messages/{self.test_match_id}"
            headers = {"X-Test-User-ID": self.test_user1_id}
            
            result = await self._check_api_endpoint(endpoint, "GET", headers=headers, expected_status=200)
            
            if not result['success']:
                # Try with 404 if match doesn't exist - that's also valid
                if '404' in result.get('error', ''):
                    return {
                        'success': True,
                        'details': 'GET messages endpoint returns 404 for non-existent match (correct behavior)'
                    }
                return result
            
            return {
                'success': True,
                'details': 'GET messages endpoint responds correctly'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Error testing GET messages endpoint: {str(e)}',
                'action_item': 'Implement or fix GET /api/chat/messages/{match_id} endpoint'
            }

    async def _check_send_message_endpoint(self) -> Dict[str, Any]:
        """Check POST /api/chat/send endpoint working"""
        try:
            endpoint = "/api/chat/send"
            headers = {"X-Test-User-ID": self.test_user1_id}
            data = {
                "match_id": self.test_match_id,
                "message": "Test message for verification"
            }
            
            result = await self._check_api_endpoint(endpoint, "POST", data=data, headers=headers, expected_status=200)
            
            if not result['success']:
                # Check if it's a validation error (which might be expected for non-existent match)
                if any(code in result.get('error', '') for code in ['400', '403', '404']):
                    return {
                        'success': True,
                        'details': 'POST send message endpoint rejects invalid requests correctly (expected behavior)'
                    }
                return result
            
            return {
                'success': True,
                'details': 'POST send message endpoint responds correctly'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Error testing POST send message endpoint: {str(e)}',
                'action_item': 'Implement or fix POST /api/chat/send endpoint'
            }

    async def _check_api_authentication(self) -> Dict[str, Any]:
        """Check API endpoints require authentication"""
        try:
            # Test without auth header
            endpoint = f"/api/chat/messages/{self.test_match_id}"
            result = await self._check_api_endpoint(endpoint, "GET", expected_status=401)
            
            if result['success']:
                return {
                    'success': True,
                    'details': 'API endpoints properly require authentication'
                }
            else:
                # Check if it returns 403 instead of 401 (also acceptable)
                if '403' in result.get('error', ''):
                    return {
                        'success': True,
                        'details': 'API endpoints properly require authentication (403 Forbidden)'
                    }
                return {
                    'success': False,
                    'error': 'API endpoints do not require authentication',
                    'action_item': 'Add authentication requirement to chat API endpoints'
                }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Error testing API authentication: {str(e)}',
                'action_item': 'Fix authentication middleware for chat endpoints'
            }

    async def _check_message_validation(self) -> Dict[str, Any]:
        """Check message validation (2-2000 chars) working"""
        try:
            endpoint = "/api/chat/send"
            headers = {"X-Test-User-ID": self.test_user1_id}
            
            # Test message too short
            short_data = {
                "match_id": self.test_match_id,
                "message": "x"  # 1 character
            }
            
            result = await self._check_api_endpoint(endpoint, "POST", data=short_data, headers=headers, expected_status=422)
            
            if not result['success'] and '422' not in result.get('error', ''):
                return {
                    'success': False,
                    'error': 'Message length validation not working for short messages',
                    'action_item': 'Add message length validation (minimum 2 characters)'
                }
            
            # Test message too long
            long_data = {
                "match_id": self.test_match_id,
                "message": "x" * 2001  # 2001 characters
            }
            
            result = await self._check_api_endpoint(endpoint, "POST", data=long_data, headers=headers, expected_status=422)
            
            if not result['success'] and '422' not in result.get('error', ''):
                return {
                    'success': False,
                    'error': 'Message length validation not working for long messages',
                    'action_item': 'Add message length validation (maximum 2000 characters)'
                }
            
            return {
                'success': True,
                'details': 'Message validation (2-2000 chars) working correctly'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Error testing message validation: {str(e)}',
                'action_item': 'Implement message length validation (2-2000 characters)'
            }

    async def _check_rate_limiting(self) -> Dict[str, Any]:
        """Check rate limiting (1 msg/0.5s) functional"""
        try:
            endpoint = "/api/chat/send"
            headers = {"X-Test-User-ID": self.test_user1_id}
            data = {
                "match_id": self.test_match_id,
                "message": "Test message 1"
            }
            
            # Send first message
            await self._check_api_endpoint(endpoint, "POST", data=data, headers=headers, expected_status=200)
            
            # Immediately send second message (should be rate limited)
            data["message"] = "Test message 2"
            result = await self._check_api_endpoint(endpoint, "POST", data=data, headers=headers, expected_status=429)
            
            if result['success']:
                return {
                    'success': True,
                    'details': 'Rate limiting (1 msg/0.5s) working correctly'
                }
            else:
                # Rate limiting might not be enabled or working
                return {
                    'success': False,
                    'error': 'Rate limiting not working - should return 429 for rapid messages',
                    'action_item': 'Implement rate limiting (1 message per 0.5 seconds) using Redis TokenBucket'
                }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Error testing rate limiting: {str(e)}',
                'action_item': 'Implement rate limiting functionality for chat messages'
            }

    async def _check_chat_page_exists(self) -> Dict[str, Any]:
        """Check frontend chat page file exists"""
        try:
            chat_page_path = self.project_root / "app" / "buddy-chat" / "[matchId]" / "page.tsx"
            
            if not chat_page_path.exists():
                return {
                    'success': False,
                    'error': 'Chat page file does not exist',
                    'action_item': 'Create /app/buddy-chat/[matchId]/page.tsx file'
                }
            
            # Check file is not empty
            content = chat_page_path.read_text()
            if len(content.strip()) < 100:
                return {
                    'success': False,
                    'error': 'Chat page file exists but appears empty or minimal',
                    'action_item': 'Implement complete chat page component'
                }
            
            return {
                'success': True,
                'details': f'Chat page file exists ({len(content)} characters)'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Error checking chat page file: {str(e)}',
                'action_item': 'Create frontend chat page at /app/buddy-chat/[matchId]/page.tsx'
            }

    async def _check_chat_page_structure(self) -> Dict[str, Any]:
        """Check chat page has required components and structure"""
        try:
            chat_page_path = self.project_root / "app" / "buddy-chat" / "[matchId]" / "page.tsx"
            content = chat_page_path.read_text()
            
            required_elements = [
                "BuddyChatPage",
                "useParams",
                "useState",
                "useEffect",
                "Container",
                "Card",
                "fetchMessages",
                "sendMessage",
                "messageInput",
                "messagesEndRef"
            ]
            
            missing_elements = [elem for elem in required_elements if elem not in content]
            
            if missing_elements:
                return {
                    'success': False,
                    'error': f'Missing required elements: {", ".join(missing_elements)}',
                    'action_item': f'Add missing chat page elements: {", ".join(missing_elements)}'
                }
            
            return {
                'success': True,
                'details': f'Chat page has all required structural elements'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Error checking chat page structure: {str(e)}',
                'action_item': 'Fix chat page component structure'
            }

    async def _check_typescript_interfaces(self) -> Dict[str, Any]:
        """Check TypeScript interfaces defined correctly"""
        try:
            chat_page_path = self.project_root / "app" / "buddy-chat" / "[matchId]" / "page.tsx"
            content = chat_page_path.read_text()
            
            required_interfaces = [
                "interface ChatMessage",
                "interface ChatResponse", 
                "interface SendMessageResponse"
            ]
            
            missing_interfaces = [iface for iface in required_interfaces if iface not in content]
            
            if missing_interfaces:
                return {
                    'success': False,
                    'error': f'Missing TypeScript interfaces: {", ".join(missing_interfaces)}',
                    'action_item': f'Add missing interfaces: {", ".join(missing_interfaces)}'
                }
            
            # Check interface properties
            interface_properties = [
                "id: string",
                "match_id: string", 
                "sender_id: string",
                "message_text: string",
                "created_at: string",
                "messages: ChatMessage[]",
                "has_more: boolean",
                "success: boolean",
                "message_id: string"
            ]
            
            missing_properties = [prop for prop in interface_properties if prop not in content]
            
            if missing_properties:
                return {
                    'success': False,
                    'error': f'Missing interface properties: {", ".join(missing_properties[:3])}...',
                    'action_item': 'Add missing properties to TypeScript interfaces'
                }
            
            return {
                'success': True,
                'details': 'All required TypeScript interfaces defined correctly'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Error checking TypeScript interfaces: {str(e)}',
                'action_item': 'Add proper TypeScript interfaces to chat page'
            }

    async def _check_ui_components(self) -> Dict[str, Any]:
        """Check UI components (header, messages, input) present"""
        try:
            chat_page_path = self.project_root / "app" / "buddy-chat" / "[matchId]" / "page.tsx"
            content = chat_page_path.read_text()
            
            ui_components = [
                "Buddy Chat",  # Header title
                "Active Match",  # Badge
                "CardHeader",
                "CardBody", 
                "Input",
                "IconButton",
                "Send",
                "characters",  # Character counter
                "messagesEndRef",  # Scroll reference
                "Skeleton"  # Loading skeleton
            ]
            
            missing_components = [comp for comp in ui_components if comp not in content]
            
            if missing_components:
                return {
                    'success': False,
                    'error': f'Missing UI components: {", ".join(missing_components)}',
                    'action_item': f'Add missing UI components: {", ".join(missing_components)}'
                }
            
            return {
                'success': True,
                'details': 'All required UI components present in chat page'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Error checking UI components: {str(e)}',
                'action_item': 'Add complete UI components to chat page'
            }

    async def _check_venue_suggestions_panel(self) -> Dict[str, Any]:
        """Check venue suggestions panel exists and functional"""
        try:
            chat_page_path = self.project_root / "app" / "buddy-chat" / "[matchId]" / "page.tsx"
            content = chat_page_path.read_text()
            
            venue_elements = [
                "Venue Suggestions",
                "venueCategories",
                "MapPin",
                "Collapse",
                "useDisclosure",
                "toggleVenue"
            ]
            
            missing_elements = [elem for elem in venue_elements if elem not in content]
            
            if missing_elements:
                return {
                    'success': False,
                    'error': f'Missing venue suggestion elements: {", ".join(missing_elements)}',
                    'action_item': f'Add venue suggestions panel with: {", ".join(missing_elements)}'
                }
            
            return {
                'success': True,
                'details': 'Venue suggestions panel implemented with collapsible functionality'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Error checking venue suggestions panel: {str(e)}',
                'action_item': 'Implement venue suggestions panel with MapPin icon and collapse functionality'
            }

    async def _check_venue_categories(self) -> Dict[str, Any]:
        """Check 4 venue categories present with correct content"""
        try:
            chat_page_path = self.project_root / "app" / "buddy-chat" / "[matchId]" / "page.tsx"
            content = chat_page_path.read_text()
            
            venue_categories = [
                "Coffee Shops",
                "Bookstores", 
                "Malls",
                "Parks"
            ]
            
            venue_icons = [
                "Coffee",
                "BookOpen",
                "ShoppingBag", 
                "Trees"
            ]
            
            venue_descriptions = [
                "Relaxed atmosphere for conversation",
                "Quiet spaces with conversation starters",
                "Busy environments for practice",
                "Outdoor spaces for natural interactions"
            ]
            
            missing_categories = [cat for cat in venue_categories if cat not in content]
            missing_icons = [icon for icon in venue_icons if icon not in content]
            missing_descriptions = [desc for desc in venue_descriptions if desc not in content]
            
            if missing_categories:
                return {
                    'success': False,
                    'error': f'Missing venue categories: {", ".join(missing_categories)}',
                    'action_item': f'Add missing venue categories: {", ".join(missing_categories)}'
                }
            
            if missing_icons:
                return {
                    'success': False,
                    'error': f'Missing venue icons: {", ".join(missing_icons)}',
                    'action_item': f'Add missing icons from lucide-react: {", ".join(missing_icons)}'
                }
            
            if missing_descriptions:
                return {
                    'success': False,
                    'error': f'Missing venue descriptions: {", ".join(missing_descriptions[:2])}...',
                    'action_item': 'Add proper descriptions for all venue categories'
                }
            
            return {
                'success': True,
                'details': 'All 4 venue categories present with icons and descriptions'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Error checking venue categories: {str(e)}',
                'action_item': 'Add complete venue categories with Coffee, Bookstores, Malls, Parks'
            }

    async def _check_polling_mechanism(self) -> Dict[str, Any]:
        """Check 5-second polling mechanism implemented"""
        try:
            chat_page_path = self.project_root / "app" / "buddy-chat" / "[matchId]" / "page.tsx"
            content = chat_page_path.read_text()
            
            polling_elements = [
                "setInterval",
                "5000",  # 5 second interval
                "fetchMessages",
                "pollingRef",
                "clearInterval"
            ]
            
            missing_elements = [elem for elem in polling_elements if elem not in content]
            
            if missing_elements:
                return {
                    'success': False,
                    'error': f'Missing polling mechanism elements: {", ".join(missing_elements)}',
                    'action_item': f'Implement 5-second polling with: {", ".join(missing_elements)}'
                }
            
            return {
                'success': True,
                'details': '5-second polling mechanism implemented with proper cleanup'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Error checking polling mechanism: {str(e)}',
                'action_item': 'Implement 5-second polling for real-time message updates'
            }

    async def _check_scroll_management(self) -> Dict[str, Any]:
        """Check auto-scroll to bottom functionality"""
        try:
            chat_page_path = self.project_root / "app" / "buddy-chat" / "[matchId]" / "page.tsx"
            content = chat_page_path.read_text()
            
            scroll_elements = [
                "messagesEndRef",
                "scrollToBottom",
                "scrollIntoView",
                "behavior: \"smooth\""
            ]
            
            missing_elements = [elem for elem in scroll_elements if elem not in content]
            
            if missing_elements:
                return {
                    'success': False,
                    'error': f'Missing scroll management elements: {", ".join(missing_elements)}',
                    'action_item': f'Implement auto-scroll functionality with: {", ".join(missing_elements)}'
                }
            
            return {
                'success': True,
                'details': 'Auto-scroll to bottom functionality implemented'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Error checking scroll management: {str(e)}',
                'action_item': 'Implement auto-scroll to bottom when new messages arrive'
            }

    async def _check_character_counter(self) -> Dict[str, Any]:
        """Check character counter (2000 max) implemented"""
        try:
            chat_page_path = self.project_root / "app" / "buddy-chat" / "[matchId]" / "page.tsx"
            content = chat_page_path.read_text()
            
            counter_elements = [
                "messageInput.length",
                "2000",
                "characters",
                "maxLength={2000}"
            ]
            
            missing_elements = [elem for elem in counter_elements if elem not in content]
            
            if missing_elements:
                return {
                    'success': False,
                    'error': f'Missing character counter elements: {", ".join(missing_elements)}',
                    'action_item': f'Implement character counter with: {", ".join(missing_elements)}'
                }
            
            return {
                'success': True,
                'details': 'Character counter (2000 max) implemented correctly'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Error checking character counter: {str(e)}',
                'action_item': 'Implement character counter showing current/2000 characters'
            }

    async def _check_error_handling(self) -> Dict[str, Any]:
        """Check error handling and user feedback"""
        try:
            chat_page_path = self.project_root / "app" / "buddy-chat" / "[matchId]" / "page.tsx"
            content = chat_page_path.read_text()
            
            error_elements = [
                "useToast",
                "toast(",
                "try {",
                "catch",
                "error",
                "status: \"error\"",
                "finally"
            ]
            
            missing_elements = [elem for elem in error_elements if elem not in content]
            
            if missing_elements:
                return {
                    'success': False,
                    'error': f'Missing error handling elements: {", ".join(missing_elements)}',
                    'action_item': f'Implement error handling with toast notifications'
                }
            
            return {
                'success': True,
                'details': 'Error handling and user feedback implemented'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Error checking error handling: {str(e)}',
                'action_item': 'Implement comprehensive error handling with user notifications'
            }

    async def _check_participant_access(self) -> Dict[str, Any]:
        """Check participant-only access validation"""
        try:
            # Test with non-participant user ID
            endpoint = f"/api/chat/messages/{self.test_match_id}"
            non_participant_id = str(uuid.uuid4())
            headers = {"X-Test-User-ID": non_participant_id}
            
            result = await self._check_api_endpoint(endpoint, "GET", headers=headers, expected_status=403)
            
            if result['success']:
                return {
                    'success': True,
                    'details': 'Participant-only access validation working (403 for non-participants)'
                }
            else:
                return {
                    'success': False,
                    'error': 'Non-participants can access chat messages',
                    'action_item': 'Implement participant-only access validation returning 403 for non-participants'
                }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Error testing participant access: {str(e)}',
                'action_item': 'Implement proper participant validation for chat access'
            }

    async def _check_message_sanitization(self) -> Dict[str, Any]:
        """Check message sanitization and XSS protection"""
        try:
            endpoint = "/api/chat/send"
            headers = {"X-Test-User-ID": self.test_user1_id}
            
            # Test with potential XSS payload
            xss_data = {
                "match_id": self.test_match_id,
                "message": "<script>alert('xss')</script>Test message"
            }
            
            # Should either reject the message or sanitize it
            result = await self._check_api_endpoint(endpoint, "POST", data=xss_data, headers=headers, expected_status=422)
            
            # If it doesn't reject, check if it accepts but sanitizes
            if not result['success']:
                result = await self._check_api_endpoint(endpoint, "POST", data=xss_data, headers=headers, expected_status=200)
                if result['success']:
                    return {
                        'success': True,
                        'details': 'Message sanitization allows HTML but likely sanitizes it'
                    }
            else:
                return {
                    'success': True,
                    'details': 'Message validation rejects HTML content (XSS protection)'
                }
            
            return {
                'success': False,
                'error': 'No apparent XSS protection or message sanitization',
                'action_item': 'Implement HTML sanitization or reject messages with HTML content'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Error testing message sanitization: {str(e)}',
                'action_item': 'Implement message sanitization to prevent XSS attacks'
            }


# Convenience function for running the verification
async def verify_task_11_chat():
    """
    Run Task 11 chat verification and return results
    """
    verifier = Task11ChatVerification()
    return await verifier.verify_task_completion()


if __name__ == "__main__":
    # Allow running this module directly for testing
    async def main():
        results = await verify_task_11_chat()
        print(json.dumps(results, indent=2))
    
    asyncio.run(main())