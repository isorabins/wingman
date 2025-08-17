"""
Feature Flag System for WingmanMatch
Simple JSON-based feature toggles with database storage for runtime configuration
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
import json
from dataclasses import dataclass, asdict

from src.config import Config
from supabase import create_client

logger = logging.getLogger(__name__)

@dataclass
class FeatureFlag:
    """Feature flag configuration"""
    name: str
    enabled: bool
    description: str
    environment: str = "all"  # "all", "production", "development"
    rollout_percentage: int = 100  # 0-100 for gradual rollouts
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None

@dataclass 
class FeatureFlagRule:
    """Feature flag rule for conditional enabling"""
    condition_type: str  # "user_id", "percentage", "environment"
    condition_value: str
    enabled: bool

class FeatureFlagManager:
    """Manages feature flags with database persistence"""
    
    def __init__(self):
        self.supabase = create_client(Config.SUPABASE_URL, Config.SUPABASE_SERVICE_KEY)
        self.cache: Dict[str, FeatureFlag] = {}
        self.cache_ttl_seconds = 300  # 5 minutes
        self.last_cache_update: Optional[datetime] = None
        
        # Default feature flags for WingmanMatch
        self.default_flags = self._get_default_flags()
        
    def _get_default_flags(self) -> List[FeatureFlag]:
        """Get default feature flags for WingmanMatch"""
        return [
            FeatureFlag(
                name="enhanced_monitoring",
                enabled=True,
                description="Enable enhanced monitoring and observability features"
            ),
            FeatureFlag(
                name="external_alerts",
                enabled=True,
                description="Enable external alert notifications (Slack, email)"
            ),
            FeatureFlag(
                name="backup_verification",
                enabled=True,
                description="Enable automated backup verification system"
            ),
            FeatureFlag(
                name="performance_optimization", 
                enabled=True,
                description="Enable performance optimization features"
            ),
            FeatureFlag(
                name="canary_deployments",
                enabled=False,
                description="Enable canary deployment features for gradual rollouts"
            ),
            FeatureFlag(
                name="blue_green_deployment",
                enabled=False,
                description="Enable blue-green deployment capabilities"
            ),
            FeatureFlag(
                name="advanced_analytics",
                enabled=False,
                description="Enable advanced analytics and user behavior tracking"
            ),
            FeatureFlag(
                name="a_b_testing",
                enabled=False,
                description="Enable A/B testing framework for feature experimentation"
            ),
            FeatureFlag(
                name="rate_limiting_enhanced",
                enabled=True,
                description="Enable enhanced rate limiting with user-specific quotas"
            ),
            FeatureFlag(
                name="real_time_notifications",
                enabled=False,
                description="Enable real-time push notifications for matches and messages"
            ),
            FeatureFlag(
                name="ai_coaching_v2",
                enabled=False,
                description="Enable next-generation AI coaching features"
            ),
            FeatureFlag(
                name="voice_messages",
                enabled=False,
                description="Enable voice message functionality in chat"
            ),
            FeatureFlag(
                name="video_sessions",
                enabled=False,
                description="Enable video session functionality for wingman meetings"
            ),
            FeatureFlag(
                name="premium_features",
                enabled=False,
                description="Enable premium subscription features"
            )
        ]
    
    async def initialize_feature_flags(self):
        """Initialize feature flag table and default flags"""
        try:
            # Create feature_flags table if it doesn't exist
            await self._ensure_feature_flags_table()
            
            # Initialize default flags if table is empty
            existing_flags = await self.get_all_flags()
            if not existing_flags:
                await self._create_default_flags()
                logger.info("Initialized default feature flags")
            
        except Exception as e:
            logger.error(f"Failed to initialize feature flags: {e}")
    
    async def _ensure_feature_flags_table(self):
        """Ensure feature flags table exists"""
        # Note: In production, this would be handled by migrations
        # This is a fallback for development environments
        try:
            # Test if table exists by querying it
            self.supabase.table('feature_flags').select('*').limit(1).execute()
        except Exception:
            logger.warning("Feature flags table may not exist - check migrations")
    
    async def _create_default_flags(self):
        """Create default feature flags in database"""
        try:
            for flag in self.default_flags:
                flag_data = {
                    "name": flag.name,
                    "enabled": flag.enabled,
                    "description": flag.description,
                    "environment": flag.environment,
                    "rollout_percentage": flag.rollout_percentage,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "created_by": "system"
                }
                
                self.supabase.table('feature_flags').upsert(flag_data).execute()
            
        except Exception as e:
            logger.error(f"Failed to create default feature flags: {e}")
    
    async def get_flag(self, flag_name: str, user_id: Optional[str] = None) -> bool:
        """Get feature flag value for user"""
        try:
            # Check cache first
            if self._is_cache_valid():
                if flag_name in self.cache:
                    flag = self.cache[flag_name]
                    return self._evaluate_flag(flag, user_id)
            
            # Refresh cache if stale
            await self._refresh_cache()
            
            # Check cache again
            if flag_name in self.cache:
                flag = self.cache[flag_name]
                return self._evaluate_flag(flag, user_id)
            
            # Flag not found, return False
            logger.warning(f"Feature flag '{flag_name}' not found")
            return False
            
        except Exception as e:
            logger.error(f"Error getting feature flag '{flag_name}': {e}")
            return False
    
    def _evaluate_flag(self, flag: FeatureFlag, user_id: Optional[str] = None) -> bool:
        """Evaluate feature flag based on conditions"""
        if not flag.enabled:
            return False
        
        # Environment check
        current_env = Config.get_environment()
        if flag.environment != "all" and flag.environment != current_env:
            return False
        
        # Rollout percentage check
        if flag.rollout_percentage < 100:
            if user_id:
                # Deterministic rollout based on user ID
                import hashlib
                hash_value = int(hashlib.md5(f"{flag.name}:{user_id}".encode()).hexdigest(), 16)
                percentage = hash_value % 100
                return percentage < flag.rollout_percentage
            else:
                # Random rollout for anonymous users
                import random
                return random.randint(1, 100) <= flag.rollout_percentage
        
        return True
    
    async def set_flag(self, flag_name: str, enabled: bool, user_id: Optional[str] = None) -> bool:
        """Set feature flag value"""
        try:
            update_data = {
                "enabled": enabled,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            
            if user_id:
                update_data["updated_by"] = user_id
            
            result = self.supabase.table('feature_flags')\
                .update(update_data)\
                .eq('name', flag_name)\
                .execute()
            
            if result.data:
                # Invalidate cache
                self._invalidate_cache()
                logger.info(f"Feature flag '{flag_name}' set to {enabled}")
                return True
            else:
                logger.warning(f"Failed to update feature flag '{flag_name}'")
                return False
                
        except Exception as e:
            logger.error(f"Error setting feature flag '{flag_name}': {e}")
            return False
    
    async def create_flag(self, 
                         flag_name: str,
                         enabled: bool,
                         description: str,
                         environment: str = "all",
                         rollout_percentage: int = 100,
                         user_id: Optional[str] = None) -> bool:
        """Create new feature flag"""
        try:
            flag_data = {
                "name": flag_name,
                "enabled": enabled,
                "description": description,
                "environment": environment,
                "rollout_percentage": rollout_percentage,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "created_by": user_id or "system"
            }
            
            result = self.supabase.table('feature_flags').insert(flag_data).execute()
            
            if result.data:
                # Invalidate cache
                self._invalidate_cache()
                logger.info(f"Created feature flag '{flag_name}'")
                return True
            else:
                return False
                
        except Exception as e:
            logger.error(f"Error creating feature flag '{flag_name}': {e}")
            return False
    
    async def get_all_flags(self) -> Dict[str, FeatureFlag]:
        """Get all feature flags"""
        try:
            result = self.supabase.table('feature_flags').select('*').execute()
            
            flags = {}
            for row in result.data:
                flag = FeatureFlag(
                    name=row['name'],
                    enabled=row['enabled'],
                    description=row['description'],
                    environment=row.get('environment', 'all'),
                    rollout_percentage=row.get('rollout_percentage', 100),
                    created_at=datetime.fromisoformat(row['created_at']) if row.get('created_at') else None,
                    updated_at=datetime.fromisoformat(row['updated_at']) if row.get('updated_at') else None,
                    created_by=row.get('created_by')
                )
                flags[flag.name] = flag
            
            return flags
            
        except Exception as e:
            logger.error(f"Error getting all feature flags: {e}")
            return {}
    
    async def _refresh_cache(self):
        """Refresh feature flag cache"""
        try:
            self.cache = await self.get_all_flags()
            self.last_cache_update = datetime.now(timezone.utc)
            
        except Exception as e:
            logger.error(f"Error refreshing feature flag cache: {e}")
    
    def _is_cache_valid(self) -> bool:
        """Check if cache is still valid"""
        if not self.last_cache_update:
            return False
        
        cache_age = datetime.now(timezone.utc) - self.last_cache_update
        return cache_age.total_seconds() < self.cache_ttl_seconds
    
    def _invalidate_cache(self):
        """Invalidate feature flag cache"""
        self.last_cache_update = None
        self.cache.clear()
    
    async def get_flags_for_user(self, user_id: str) -> Dict[str, bool]:
        """Get all feature flags evaluated for specific user"""
        all_flags = await self.get_all_flags()
        user_flags = {}
        
        for flag_name, flag in all_flags.items():
            user_flags[flag_name] = self._evaluate_flag(flag, user_id)
        
        return user_flags
    
    async def get_flag_status_dashboard(self) -> Dict[str, Any]:
        """Get feature flag status for dashboard"""
        try:
            all_flags = await self.get_all_flags()
            
            dashboard_data = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "total_flags": len(all_flags),
                "enabled_flags": sum(1 for flag in all_flags.values() if flag.enabled),
                "environment": Config.get_environment(),
                "flags": {}
            }
            
            for flag_name, flag in all_flags.items():
                dashboard_data["flags"][flag_name] = {
                    "enabled": flag.enabled,
                    "description": flag.description,
                    "environment": flag.environment,
                    "rollout_percentage": flag.rollout_percentage,
                    "created_at": flag.created_at.isoformat() if flag.created_at else None,
                    "updated_at": flag.updated_at.isoformat() if flag.updated_at else None
                }
            
            return dashboard_data
            
        except Exception as e:
            logger.error(f"Error getting flag status dashboard: {e}")
            return {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "error": str(e)
            }

# Global feature flag manager
feature_flag_manager = FeatureFlagManager()

# Convenience functions
async def is_feature_enabled(flag_name: str, user_id: Optional[str] = None) -> bool:
    """Check if feature is enabled for user"""
    return await feature_flag_manager.get_flag(flag_name, user_id)

async def toggle_feature(flag_name: str, enabled: bool, user_id: Optional[str] = None) -> bool:
    """Toggle feature flag"""
    return await feature_flag_manager.set_flag(flag_name, enabled, user_id)

async def get_user_features(user_id: str) -> Dict[str, bool]:
    """Get all features enabled for user"""
    return await feature_flag_manager.get_flags_for_user(user_id)

async def get_feature_dashboard() -> Dict[str, Any]:
    """Get feature flag dashboard data"""
    return await feature_flag_manager.get_flag_status_dashboard()

async def initialize_features():
    """Initialize feature flag system"""
    await feature_flag_manager.initialize_feature_flags()
