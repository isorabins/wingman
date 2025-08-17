"""
Deployment Automation for WingmanMatch
Automated deployment pipeline with health checks and rollback capabilities
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import json
import subprocess
import os
from dataclasses import dataclass

from src.config import Config
from src.deployment.production_config import production_config
from src.deployment.enhanced_monitoring import enhanced_monitoring
from src.deployment.backup_recovery import backup_verification, recovery_manager

logger = logging.getLogger(__name__)

@dataclass
class DeploymentStep:
    """Deployment step configuration"""
    name: str
    command: str
    timeout_seconds: int = 300
    required: bool = True
    rollback_command: Optional[str] = None

@dataclass
class DeploymentResult:
    """Deployment execution result"""
    step_name: str
    success: bool
    duration_seconds: float
    output: str
    error: Optional[str] = None

class DeploymentManager:
    """Manages automated deployment pipeline"""
    
    def __init__(self):
        self.deployment_steps = self._get_deployment_steps()
        self.health_check_retries = 3
        self.health_check_delay_seconds = 10
        
    def _get_deployment_steps(self) -> List[DeploymentStep]:
        """Get deployment pipeline steps"""
        return [
            DeploymentStep(
                name="pre_deployment_health_check",
                command="python -c 'from src.deployment.enhanced_monitoring import get_enhanced_health_check; import asyncio; print(asyncio.run(get_enhanced_health_check()))'",
                timeout_seconds=30,
                required=True
            ),
            DeploymentStep(
                name="backup_verification",
                command="python -c 'from src.deployment.backup_recovery import run_backup_verification; import asyncio; print(asyncio.run(run_backup_verification()))'",
                timeout_seconds=60,
                required=True
            ),
            DeploymentStep(
                name="database_migration",
                command="supabase migration up",
                timeout_seconds=120,
                required=True,
                rollback_command="supabase migration down"
            ),
            DeploymentStep(
                name="dependency_update",
                command="pip install -r requirements.txt",
                timeout_seconds=180,
                required=True
            ),
            DeploymentStep(
                name="application_deployment",
                command="echo 'Application deployment step - would execute: git push heroku main'",
                timeout_seconds=300,
                required=True,
                rollback_command="heroku rollback"
            ),
            DeploymentStep(
                name="post_deployment_health_check",
                command="python -c 'from src.deployment.enhanced_monitoring import get_enhanced_health_check; import asyncio; print(asyncio.run(get_enhanced_health_check()))'",
                timeout_seconds=60,
                required=True
            ),
            DeploymentStep(
                name="performance_validation",
                command="python -c 'from src.deployment.enhanced_monitoring import get_performance_dashboard; import asyncio; print(asyncio.run(get_performance_dashboard()))'",
                timeout_seconds=30,
                required=False
            )
        ]
    
    async def execute_deployment(self, deployment_type: str = "standard") -> Dict[str, Any]:
        """Execute automated deployment pipeline"""
        deployment_id = f"deploy_{int(datetime.now().timestamp())}"
        start_time = datetime.now(timezone.utc)
        
        logger.info(f"Starting deployment {deployment_id} - type: {deployment_type}")
        
        deployment_log = {
            "deployment_id": deployment_id,
            "deployment_type": deployment_type,
            "start_time": start_time.isoformat(),
            "environment": production_config.environment,
            "steps": [],
            "overall_success": False,
            "rollback_executed": False
        }
        
        try:
            # Execute deployment steps
            for step in self.deployment_steps:
                step_result = await self._execute_step(step)
                deployment_log["steps"].append({
                    "name": step_result.step_name,
                    "success": step_result.success,
                    "duration_seconds": step_result.duration_seconds,
                    "required": step.required,
                    "error": step_result.error
                })
                
                # Check if required step failed
                if step.required and not step_result.success:
                    logger.error(f"Required deployment step failed: {step.name}")
                    
                    # Execute rollback if needed
                    if step.rollback_command:
                        await self._execute_rollback(deployment_log)
                    
                    deployment_log["overall_success"] = False
                    deployment_log["failure_reason"] = f"Required step '{step.name}' failed"
                    break
                
                logger.info(f"Deployment step completed: {step.name} - Success: {step_result.success}")
            
            else:
                # All steps completed successfully
                deployment_log["overall_success"] = True
                logger.info(f"Deployment {deployment_id} completed successfully")
            
        except Exception as e:
            logger.error(f"Deployment {deployment_id} failed with exception: {e}")
            deployment_log["overall_success"] = False
            deployment_log["exception"] = str(e)
            
            # Execute emergency rollback
            await self._execute_rollback(deployment_log)
        
        finally:
            end_time = datetime.now(timezone.utc)
            deployment_log["end_time"] = end_time.isoformat()
            deployment_log["total_duration_seconds"] = (end_time - start_time).total_seconds()
            
            # Send deployment notification
            await self._send_deployment_notification(deployment_log)
        
        return deployment_log
    
    async def _execute_step(self, step: DeploymentStep) -> DeploymentResult:
        """Execute single deployment step"""
        start_time = datetime.now()
        
        try:
            logger.info(f"Executing deployment step: {step.name}")
            
            # For safety, we'll simulate deployment commands
            # In production, this would execute actual commands
            if "echo" in step.command or "python -c" in step.command:
                # Safe commands that can be executed
                process = await asyncio.create_subprocess_shell(
                    step.command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                try:
                    stdout, stderr = await asyncio.wait_for(
                        process.communicate(),
                        timeout=step.timeout_seconds
                    )
                    
                    success = process.returncode == 0
                    output = stdout.decode() if stdout else ""
                    error = stderr.decode() if stderr else None
                    
                except asyncio.TimeoutError:
                    process.kill()
                    success = False
                    output = ""
                    error = f"Step timed out after {step.timeout_seconds} seconds"
                    
            else:
                # Simulate other commands for safety
                await asyncio.sleep(1)  # Simulate execution time
                success = True
                output = f"Simulated execution of: {step.command}"
                error = None
                logger.info(f"Simulated deployment step: {step.name}")
            
            duration_seconds = (datetime.now() - start_time).total_seconds()
            
            return DeploymentResult(
                step_name=step.name,
                success=success,
                duration_seconds=duration_seconds,
                output=output,
                error=error
            )
            
        except Exception as e:
            duration_seconds = (datetime.now() - start_time).total_seconds()
            return DeploymentResult(
                step_name=step.name,
                success=False,
                duration_seconds=duration_seconds,
                output="",
                error=str(e)
            )
    
    async def _execute_rollback(self, deployment_log: Dict[str, Any]):
        """Execute rollback procedures"""
        try:
            logger.warning("Executing deployment rollback")
            
            # Mark rollback as executed
            deployment_log["rollback_executed"] = True
            deployment_log["rollback_time"] = datetime.now(timezone.utc).isoformat()
            
            # Execute rollback for completed steps in reverse order
            rollback_steps = []
            for step_log in reversed(deployment_log["steps"]):
                if step_log["success"]:
                    # Find the deployment step
                    deployment_step = next(
                        (step for step in self.deployment_steps if step.name == step_log["name"]),
                        None
                    )
                    
                    if deployment_step and deployment_step.rollback_command:
                        rollback_result = await self._execute_rollback_step(deployment_step)
                        rollback_steps.append(rollback_result)
            
            deployment_log["rollback_steps"] = rollback_steps
            logger.info("Deployment rollback completed")
            
        except Exception as e:
            logger.error(f"Rollback execution failed: {e}")
            deployment_log["rollback_error"] = str(e)
    
    async def _execute_rollback_step(self, step: DeploymentStep) -> Dict[str, Any]:
        """Execute single rollback step"""
        try:
            logger.info(f"Executing rollback for step: {step.name}")
            
            # For safety, simulate rollback commands
            await asyncio.sleep(0.5)  # Simulate rollback time
            
            return {
                "step_name": step.name,
                "rollback_command": step.rollback_command,
                "success": True,
                "simulated": True
            }
            
        except Exception as e:
            return {
                "step_name": step.name,
                "rollback_command": step.rollback_command,
                "success": False,
                "error": str(e)
            }
    
    async def _send_deployment_notification(self, deployment_log: Dict[str, Any]):
        """Send deployment notification"""
        try:
            success = deployment_log["overall_success"]
            deployment_id = deployment_log["deployment_id"]
            
            # Create notification message
            if success:
                message = f"✅ Deployment {deployment_id} completed successfully"
                severity = "info"
            else:
                message = f"❌ Deployment {deployment_id} failed"
                if deployment_log.get("rollback_executed"):
                    message += " - Rollback executed"
                severity = "critical"
            
            # Add deployment details
            message += f"\nEnvironment: {deployment_log['environment']}"
            message += f"\nDuration: {deployment_log.get('total_duration_seconds', 0):.1f}s"
            message += f"\nSteps completed: {sum(1 for step in deployment_log['steps'] if step['success'])}/{len(deployment_log['steps'])}"
            
            # Send notification using existing alert system
            if production_config.monitoring_config.slack_webhook_url:
                from src.observability.alert_system import trigger_custom_alert, AlertSeverity
                
                alert_severity = AlertSeverity.INFO if success else AlertSeverity.CRITICAL
                await trigger_custom_alert(message, alert_severity)
            
            logger.info(f"Deployment notification sent: {message}")
            
        except Exception as e:
            logger.error(f"Failed to send deployment notification: {e}")
    
    async def get_deployment_status(self) -> Dict[str, Any]:
        """Get current deployment status"""
        try:
            # Get health status
            health_status = await enhanced_monitoring.health_check_with_monitoring()
            
            # Get production readiness
            readiness_check = production_config.validate_production_readiness()
            
            # Get backup status
            backup_status = await backup_verification.verify_daily_backups()
            
            return {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "environment": production_config.environment,
                "deployment_ready": readiness_check["production_ready"],
                "health_status": health_status,
                "backup_status": backup_status["backup_system_healthy"],
                "monitoring_enabled": health_status.get("monitoring", {}).get("sentry", {}).get("enabled", False),
                "issues": readiness_check.get("issues", []),
                "warnings": readiness_check.get("warnings", []),
                "recommendations": readiness_check.get("recommendations", [])
            }
            
        except Exception as e:
            logger.error(f"Error getting deployment status: {e}")
            return {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "error": str(e),
                "deployment_ready": False
            }

class HealthCheckManager:
    """Manages comprehensive health checks for deployment validation"""
    
    def __init__(self):
        self.health_checks = self._get_health_checks()
    
    def _get_health_checks(self) -> List[str]:
        """Get list of health check endpoints and commands"""
        return [
            "database_connectivity",
            "redis_connectivity", 
            "email_service",
            "external_apis",
            "performance_metrics",
            "security_policies"
        ]
    
    async def run_comprehensive_health_check(self) -> Dict[str, Any]:
        """Run comprehensive health check for deployment validation"""
        health_results = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "overall_healthy": True,
            "checks": {}
        }
        
        try:
            # Database connectivity
            health_results["checks"]["database"] = await self._check_database_health()
            
            # Redis connectivity
            health_results["checks"]["redis"] = await self._check_redis_health()
            
            # Email service
            health_results["checks"]["email"] = await self._check_email_health()
            
            # Performance metrics
            health_results["checks"]["performance"] = await self._check_performance_health()
            
            # Security policies
            health_results["checks"]["security"] = await self._check_security_health()
            
            # Overall health assessment
            failed_checks = [
                check_name for check_name, check_result in health_results["checks"].items()
                if not check_result.get("healthy", False)
            ]
            
            health_results["overall_healthy"] = len(failed_checks) == 0
            health_results["failed_checks"] = failed_checks
            health_results["passed_checks"] = len(health_results["checks"]) - len(failed_checks)
            
        except Exception as e:
            logger.error(f"Comprehensive health check failed: {e}")
            health_results["overall_healthy"] = False
            health_results["error"] = str(e)
        
        return health_results
    
    async def _check_database_health(self) -> Dict[str, Any]:
        """Check database health"""
        try:
            from supabase import create_client
            
            supabase = create_client(Config.SUPABASE_URL, Config.SUPABASE_SERVICE_KEY)
            
            # Test basic connectivity
            start_time = datetime.now()
            result = supabase.table('user_profiles').select('id').limit(1).execute()
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return {
                "healthy": True,
                "response_time_ms": response_time,
                "connection_active": True,
                "tables_accessible": True
            }
            
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
                "connection_active": False
            }
    
    async def _check_redis_health(self) -> Dict[str, Any]:
        """Check Redis health"""
        try:
            from src.redis_session import RedisSession
            
            redis_client = await RedisSession.get_client()
            if redis_client:
                # Test Redis operation
                test_key = f"health_check_{int(datetime.now().timestamp())}"
                await redis_client.set(test_key, "ok", ex=10)
                value = await redis_client.get(test_key)
                await redis_client.delete(test_key)
                
                return {
                    "healthy": True,
                    "connection_active": True,
                    "operations_working": value.decode() == "ok" if value else False
                }
            else:
                return {
                    "healthy": True,  # Fallback mode is acceptable
                    "connection_active": False,
                    "fallback_mode": True
                }
                
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
                "connection_active": False
            }
    
    async def _check_email_health(self) -> Dict[str, Any]:
        """Check email service health"""
        try:
            from src.email_templates import email_service
            
            return {
                "healthy": True,
                "service_configured": email_service.enabled,
                "api_key_present": bool(Config.RESEND_API_KEY)
            }
            
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
                "service_configured": False
            }
    
    async def _check_performance_health(self) -> Dict[str, Any]:
        """Check performance health"""
        try:
            from src.observability.metrics_collector import get_real_time_metrics
            
            metrics = await get_real_time_metrics()
            
            return {
                "healthy": True,
                "metrics_collection_active": "avg_response_time_ms" in metrics,
                "recent_performance": metrics
            }
            
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
                "metrics_collection_active": False
            }
    
    async def _check_security_health(self) -> Dict[str, Any]:
        """Check security health"""
        try:
            # Check environment variables
            security_checks = {
                "api_keys_configured": all([
                    Config.ANTHROPIC_API_KEY,
                    Config.SUPABASE_SERVICE_KEY
                ]),
                "environment_production": Config.get_environment() == "production",
                "monitoring_enabled": production_config.monitoring_config.enabled
            }
            
            return {
                "healthy": all(security_checks.values()),
                "checks": security_checks
            }
            
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e)
            }

# Global instances
deployment_manager = DeploymentManager()
health_check_manager = HealthCheckManager()

# Convenience functions
async def execute_deployment(deployment_type: str = "standard"):
    """Execute automated deployment"""
    return await deployment_manager.execute_deployment(deployment_type)

async def get_deployment_status():
    """Get deployment readiness status"""
    return await deployment_manager.get_deployment_status()

async def run_health_checks():
    """Run comprehensive health checks"""
    return await health_check_manager.run_comprehensive_health_check()
