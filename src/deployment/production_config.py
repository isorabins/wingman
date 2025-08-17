"""
Production Deployment Configuration for WingmanMatch
Manages production service configuration and environment setup
"""

import os
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class ServiceProvider(Enum):
    REDIS_CLOUD = "redis_cloud"
    UPSTASH = "upstash"
    RESEND = "resend"
    SUPABASE = "supabase"
    VERCEL = "vercel"
    HEROKU = "heroku"

@dataclass
class ServiceConfig:
    """Configuration for external service"""
    provider: ServiceProvider
    url: str
    api_key: Optional[str] = None
    fallback_enabled: bool = True
    health_check_url: Optional[str] = None
    timeout_seconds: int = 30

@dataclass
class MonitoringConfig:
    """Configuration for monitoring services"""
    sentry_dsn: Optional[str] = None
    datadog_api_key: Optional[str] = None
    datadog_app_key: Optional[str] = None
    uptime_robot_api_key: Optional[str] = None
    slack_webhook_url: Optional[str] = None
    enabled: bool = True

class ProductionConfig:
    """Production deployment configuration manager"""
    
    def __init__(self):
        self.environment = os.getenv("ENVIRONMENT", "development")
        self.is_production = self.environment == "production"
        
        # Initialize service configurations
        self.redis_config = self._get_redis_config()
        self.email_config = self._get_email_config()
        self.monitoring_config = self._get_monitoring_config()
        self.feature_flags = self._get_feature_flags()
        
    def _get_redis_config(self) -> ServiceConfig:
        """Get Redis service configuration"""
        redis_url = os.getenv("REDIS_URL")
        
        if not redis_url:
            logger.warning("No Redis URL configured - using fallback mode")
            return ServiceConfig(
                provider=ServiceProvider.UPSTASH,
                url="",
                fallback_enabled=True
            )
        
        # Determine provider from URL
        if "upstash" in redis_url:
            provider = ServiceProvider.UPSTASH
        else:
            provider = ServiceProvider.REDIS_CLOUD
            
        return ServiceConfig(
            provider=provider,
            url=redis_url,
            api_key=os.getenv("REDIS_PASSWORD"),
            fallback_enabled=True,
            health_check_url=f"{redis_url}/ping" if redis_url else None
        )
    
    def _get_email_config(self) -> ServiceConfig:
        """Get email service configuration"""
        api_key = os.getenv("RESEND_API_KEY")
        
        return ServiceConfig(
            provider=ServiceProvider.RESEND,
            url="https://api.resend.com",
            api_key=api_key,
            fallback_enabled=True,
            health_check_url="https://api.resend.com/health" if api_key else None
        )
    
    def _get_monitoring_config(self) -> MonitoringConfig:
        """Get monitoring service configuration"""
        return MonitoringConfig(
            sentry_dsn=os.getenv("SENTRY_DSN"),
            datadog_api_key=os.getenv("DATADOG_API_KEY"),
            datadog_app_key=os.getenv("DATADOG_APP_KEY"),
            uptime_robot_api_key=os.getenv("UPTIME_ROBOT_API_KEY"),
            slack_webhook_url=os.getenv("SLACK_WEBHOOK_URL"),
            enabled=os.getenv("ENABLE_MONITORING", "true").lower() in ("true", "1", "yes")
        )
    
    def _get_feature_flags(self) -> Dict[str, bool]:
        """Get feature flag configuration"""
        return {
            "enhanced_monitoring": os.getenv("ENABLE_ENHANCED_MONITORING", "true").lower() in ("true", "1", "yes"),
            "external_alerts": os.getenv("ENABLE_EXTERNAL_ALERTS", "true").lower() in ("true", "1", "yes"),
            "backup_verification": os.getenv("ENABLE_BACKUP_VERIFICATION", "true").lower() in ("true", "1", "yes"),
            "performance_optimization": os.getenv("ENABLE_PERFORMANCE_OPTIMIZATION", "true").lower() in ("true", "1", "yes"),
            "canary_deployments": os.getenv("ENABLE_CANARY_DEPLOYMENTS", "false").lower() in ("true", "1", "yes"),
            "blue_green_deployment": os.getenv("ENABLE_BLUE_GREEN_DEPLOYMENT", "false").lower() in ("true", "1", "yes")
        }
    
    def get_deployment_info(self) -> Dict[str, Any]:
        """Get deployment information"""
        return {
            "environment": self.environment,
            "is_production": self.is_production,
            "deployment_timestamp": os.getenv("DEPLOYMENT_TIMESTAMP"),
            "git_commit": os.getenv("GIT_COMMIT"),
            "version": os.getenv("APP_VERSION", "1.0.0"),
            "services": {
                "redis": {
                    "provider": self.redis_config.provider.value,
                    "configured": bool(self.redis_config.url),
                    "fallback_enabled": self.redis_config.fallback_enabled
                },
                "email": {
                    "provider": self.email_config.provider.value,
                    "configured": bool(self.email_config.api_key),
                    "fallback_enabled": self.email_config.fallback_enabled
                },
                "monitoring": {
                    "sentry": bool(self.monitoring_config.sentry_dsn),
                    "datadog": bool(self.monitoring_config.datadog_api_key),
                    "uptime_robot": bool(self.monitoring_config.uptime_robot_api_key),
                    "slack": bool(self.monitoring_config.slack_webhook_url)
                }
            },
            "feature_flags": self.feature_flags
        }
    
    def validate_production_readiness(self) -> Dict[str, Any]:
        """Validate production readiness"""
        issues = []
        warnings = []
        
        # Critical checks
        if self.is_production:
            if not self.monitoring_config.sentry_dsn:
                issues.append("Sentry DSN not configured for error tracking")
            
            if not self.monitoring_config.slack_webhook_url:
                warnings.append("Slack webhook not configured for alerts")
            
            if not self.redis_config.url:
                warnings.append("Redis not configured - using fallback mode")
            
            if not self.email_config.api_key:
                issues.append("Email service not configured")
        
        return {
            "production_ready": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "recommendations": self._get_recommendations(issues, warnings)
        }
    
    def _get_recommendations(self, issues: list, warnings: list) -> list:
        """Get deployment recommendations"""
        recommendations = []
        
        if issues:
            recommendations.append("Resolve critical issues before production deployment")
        
        if warnings:
            recommendations.append("Address warnings for optimal production experience")
        
        if not self.monitoring_config.datadog_api_key:
            recommendations.append("Consider adding Datadog for comprehensive logging")
        
        if not self.monitoring_config.uptime_robot_api_key:
            recommendations.append("Consider adding UptimeRobot for uptime monitoring")
        
        return recommendations

# Global production configuration instance
production_config = ProductionConfig()
