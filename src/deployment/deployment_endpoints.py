"""
Deployment and Monitoring API Endpoints for WingmanMatch
Enhanced endpoints for production deployment management and monitoring
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional
import logging
from datetime import datetime, timezone

from src.config import Config
from src.deployment.enhanced_monitoring import (
    enhanced_monitoring, 
    get_enhanced_health_check,
    get_performance_dashboard
)
from src.deployment.backup_recovery import (
    run_backup_verification,
    test_recovery_readiness,
    get_recovery_plans,
    execute_rollback
)
from src.deployment.feature_flags import (
    is_feature_enabled,
    toggle_feature,
    get_user_features,
    get_feature_dashboard,
    initialize_features
)
from src.deployment.deployment_automation import (
    execute_deployment,
    get_deployment_status,
    run_health_checks
)
from src.deployment.production_config import production_config

logger = logging.getLogger(__name__)

# Create deployment router
deployment_router = APIRouter(prefix="/api/deployment", tags=["deployment"])

@deployment_router.get("/health/enhanced")
async def enhanced_health_endpoint():
    """Enhanced health check with monitoring service status"""
    try:
        health_data = await get_enhanced_health_check()
        return JSONResponse(content=health_data, status_code=200)
    except Exception as e:
        logger.error(f"Enhanced health check failed: {e}")
        return JSONResponse(
            content={
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            status_code=500
        )

@deployment_router.get("/health/comprehensive")
async def comprehensive_health_endpoint():
    """Comprehensive health check for deployment validation"""
    try:
        health_data = await run_health_checks()
        status_code = 200 if health_data.get("overall_healthy") else 503
        return JSONResponse(content=health_data, status_code=status_code)
    except Exception as e:
        logger.error(f"Comprehensive health check failed: {e}")
        return JSONResponse(
            content={
                "overall_healthy": False,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            status_code=500
        )

@deployment_router.get("/performance/dashboard")
async def performance_dashboard_endpoint():
    """Get performance dashboard data"""
    try:
        dashboard_data = await get_performance_dashboard()
        return JSONResponse(content=dashboard_data, status_code=200)
    except Exception as e:
        logger.error(f"Performance dashboard failed: {e}")
        return JSONResponse(
            content={
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            status_code=500
        )

@deployment_router.get("/status")
async def deployment_status_endpoint():
    """Get deployment readiness status"""
    try:
        status_data = await get_deployment_status()
        return JSONResponse(content=status_data, status_code=200)
    except Exception as e:
        logger.error(f"Deployment status check failed: {e}")
        return JSONResponse(
            content={
                "deployment_ready": False,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            status_code=500
        )

@deployment_router.post("/deploy")
async def deploy_endpoint(
    background_tasks: BackgroundTasks,
    deployment_type: str = "standard"
):
    """Execute automated deployment"""
    try:
        # Validate deployment type
        valid_types = ["standard", "hotfix", "rollback"]
        if deployment_type not in valid_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid deployment type. Must be one of: {valid_types}"
            )
        
        # Check production readiness
        readiness = production_config.validate_production_readiness()
        if not readiness["production_ready"]:
            return JSONResponse(
                content={
                    "deployment_started": False,
                    "reason": "Production readiness check failed",
                    "issues": readiness["issues"],
                    "warnings": readiness["warnings"]
                },
                status_code=400
            )
        
        # Execute deployment in background
        background_tasks.add_task(execute_deployment, deployment_type)
        
        return JSONResponse(
            content={
                "deployment_started": True,
                "deployment_type": deployment_type,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "message": "Deployment started in background. Check /api/deployment/status for progress."
            },
            status_code=202
        )
        
    except Exception as e:
        logger.error(f"Deployment initiation failed: {e}")
        return JSONResponse(
            content={
                "deployment_started": False,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            status_code=500
        )

@deployment_router.get("/backup/status")
async def backup_status_endpoint():
    """Get backup verification status"""
    try:
        backup_data = await run_backup_verification()
        return JSONResponse(content=backup_data, status_code=200)
    except Exception as e:
        logger.error(f"Backup status check failed: {e}")
        return JSONResponse(
            content={
                "backup_system_healthy": False,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            status_code=500
        )

@deployment_router.get("/backup/recovery-readiness")
async def recovery_readiness_endpoint():
    """Test recovery procedure readiness"""
    try:
        recovery_data = await test_recovery_readiness()
        status_code = 200 if recovery_data.get("recovery_readiness") else 503
        return JSONResponse(content=recovery_data, status_code=status_code)
    except Exception as e:
        logger.error(f"Recovery readiness test failed: {e}")
        return JSONResponse(
            content={
                "recovery_readiness": False,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            status_code=500
        )

@deployment_router.get("/recovery/plans")
async def recovery_plans_endpoint():
    """Get available recovery plans"""
    try:
        plans = await get_recovery_plans()
        return JSONResponse(content={"recovery_plans": plans}, status_code=200)
    except Exception as e:
        logger.error(f"Failed to get recovery plans: {e}")
        return JSONResponse(
            content={
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            status_code=500
        )

@deployment_router.post("/recovery/rollback/{rollback_type}")
async def execute_rollback_endpoint(rollback_type: str):
    """Execute emergency rollback procedure"""
    try:
        # Validate rollback type
        valid_types = ["database_corruption", "application_failure", "performance_degradation"]
        if rollback_type not in valid_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid rollback type. Must be one of: {valid_types}"
            )
        
        rollback_result = await execute_rollback(rollback_type)
        status_code = 200 if rollback_result.get("success") else 500
        
        return JSONResponse(content=rollback_result, status_code=status_code)
        
    except Exception as e:
        logger.error(f"Rollback execution failed: {e}")
        return JSONResponse(
            content={
                "success": False,
                "error": str(e),
                "rollback_type": rollback_type,
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            status_code=500
        )

@deployment_router.get("/features")
async def feature_flags_endpoint():
    """Get feature flag dashboard"""
    try:
        feature_data = await get_feature_dashboard()
        return JSONResponse(content=feature_data, status_code=200)
    except Exception as e:
        logger.error(f"Feature flag dashboard failed: {e}")
        return JSONResponse(
            content={
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            status_code=500
        )

@deployment_router.get("/features/{user_id}")
async def user_features_endpoint(user_id: str):
    """Get feature flags for specific user"""
    try:
        user_features = await get_user_features(user_id)
        return JSONResponse(
            content={
                "user_id": user_id,
                "features": user_features,
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            status_code=200
        )
    except Exception as e:
        logger.error(f"User features check failed: {e}")
        return JSONResponse(
            content={
                "user_id": user_id,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            status_code=500
        )

@deployment_router.post("/features/{flag_name}/toggle")
async def toggle_feature_endpoint(
    flag_name: str,
    enabled: bool,
    user_id: Optional[str] = None
):
    """Toggle feature flag"""
    try:
        success = await toggle_feature(flag_name, enabled, user_id)
        
        if success:
            return JSONResponse(
                content={
                    "success": True,
                    "flag_name": flag_name,
                    "enabled": enabled,
                    "updated_by": user_id,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                },
                status_code=200
            )
        else:
            return JSONResponse(
                content={
                    "success": False,
                    "flag_name": flag_name,
                    "error": "Failed to update feature flag"
                },
                status_code=400
            )
            
    except Exception as e:
        logger.error(f"Feature flag toggle failed: {e}")
        return JSONResponse(
            content={
                "success": False,
                "flag_name": flag_name,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            status_code=500
        )

@deployment_router.get("/config/production")
async def production_config_endpoint():
    """Get production configuration status"""
    try:
        config_data = production_config.get_deployment_info()
        readiness_check = production_config.validate_production_readiness()
        
        return JSONResponse(
            content={
                "deployment_info": config_data,
                "production_readiness": readiness_check,
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            status_code=200
        )
    except Exception as e:
        logger.error(f"Production config check failed: {e}")
        return JSONResponse(
            content={
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            status_code=500
        )

@deployment_router.post("/initialize")
async def initialize_deployment_systems():
    """Initialize deployment systems"""
    try:
        # Initialize feature flags
        await initialize_features()
        
        # Get initial status
        status_data = await get_deployment_status()
        
        return JSONResponse(
            content={
                "initialized": True,
                "status": status_data,
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            status_code=200
        )
    except Exception as e:
        logger.error(f"Deployment system initialization failed: {e}")
        return JSONResponse(
            content={
                "initialized": False,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            status_code=500
        )

# Add startup event to initialize systems
async def initialize_deployment_infrastructure():
    """Initialize deployment infrastructure on startup"""
    try:
        logger.info("Initializing deployment infrastructure...")
        
        # Initialize feature flag system
        await initialize_features()
        
        # Validate production readiness
        readiness = production_config.validate_production_readiness()
        if not readiness["production_ready"]:
            logger.warning(f"Production readiness issues: {readiness['issues']}")
        
        logger.info("Deployment infrastructure initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize deployment infrastructure: {e}")
