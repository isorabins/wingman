"""
Supabase client factory for WingmanMatch
Provides centralized database client management with service and anonymous roles
"""

import logging
from typing import Optional
from supabase import create_client, Client
from src.config import Config

logger = logging.getLogger(__name__)

class SupabaseFactory:
    """Centralized Supabase client factory with role-based access"""
    
    _service_client: Optional[Client] = None
    _anon_client: Optional[Client] = None
    
    @classmethod
    def get_service_client(cls) -> Client:
        """Get Supabase client with service role for server routes"""
        if cls._service_client is None:
            try:
                cls._service_client = create_client(
                    Config.SUPABASE_URL, 
                    Config.SUPABASE_SERVICE_KEY
                )
                logger.info("Supabase service client initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Supabase service client: {e}")
                raise
        
        return cls._service_client
    
    @classmethod
    def get_anon_client(cls) -> Client:
        """Get Supabase client with anonymous role for edge functions"""
        if cls._anon_client is None:
            try:
                cls._anon_client = create_client(
                    Config.SUPABASE_URL,
                    Config.SUPABASE_ANON_KEY
                )
                logger.info("Supabase anonymous client initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Supabase anonymous client: {e}")
                raise
        
        return cls._anon_client
    
    @classmethod
    def health_check(cls) -> dict:
        """Check health of Supabase connections"""
        health = {
            "service_client": False,
            "anon_client": False,
            "errors": []
        }
        
        # Test service client
        try:
            service_client = cls.get_service_client()
            # Simple query to test connection
            result = service_client.table('user_profiles').select('id').limit(1).execute()
            health["service_client"] = True
        except Exception as e:
            health["errors"].append(f"Service client error: {str(e)}")
            logger.error(f"Supabase service client health check failed: {e}")
        
        # Test anonymous client
        try:
            anon_client = cls.get_anon_client()
            # Test with a public table
            result = anon_client.table('approach_challenges').select('id').limit(1).execute()
            health["anon_client"] = True
        except Exception as e:
            health["errors"].append(f"Anonymous client error: {str(e)}")
            logger.error(f"Supabase anonymous client health check failed: {e}")
        
        return health

# Convenience functions for common database operations
def get_db_service() -> Client:
    """Get service role client for server-side operations"""
    return SupabaseFactory.get_service_client()

def get_db_anon() -> Client:
    """Get anonymous client for edge/public operations"""
    return SupabaseFactory.get_anon_client()