"""
db_cleaner.py
------------
Utility for cleaning up test data from the database.
"""

import os
import sys

# Add project root to Python path for src imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
from typing import List, Optional
from supabase import Client

class DatabaseCleaner:
    """Handles cleanup of test data from the database"""
    
    def __init__(self, supabase_client: Client):
        """Initialize with Supabase client"""
        self.supabase = supabase_client
        self._cleanup_tables: List[str] = []
        self._cleanup_ids: List[str] = []
    
    async def track_table(self, table_name: str) -> None:
        """Add a table to be cleaned up after tests"""
        if table_name not in self._cleanup_tables:
            self._cleanup_tables.append(table_name)
    
    async def track_id(self, id: str) -> None:
        """Track an ID that should be cleaned up"""
        if id not in self._cleanup_ids:
            self._cleanup_ids.append(id)
    
    async def cleanup_test_data(self, user_id: str, tables: Optional[List[str]] = None) -> None:
        """Clean up test data for a specific user"""
        tables_to_clean = tables if tables else self._cleanup_tables
        
        for table in tables_to_clean:
            try:
                # Delete records for the specific user
                await self.supabase.table(table)\
                    .delete()\
                    .eq('user_id', user_id)\
                    .execute()
                
                # Also delete any tracked IDs
                if self._cleanup_ids:
                    await self.supabase.table(table)\
                        .delete()\
                        .in_('id', self._cleanup_ids)\
                        .execute()
                        
            except Exception as e:
                print(f"Warning: Failed to clean up table {table}: {str(e)}")
        
        # Clear tracked items
        self._cleanup_tables = []
        self._cleanup_ids = []
