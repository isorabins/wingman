"""
Retry Policies for WingmanMatch

Provides comprehensive retry mechanisms with exponential backoff, circuit breaker
patterns, and configurable policies for different external services. Designed
for resilient external API integrations.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Union
from functools import wraps
import random
import time

from src.config import Config

logger = logging.getLogger(__name__)

class RetryError(Exception):
    """Exception raised when all retry attempts are exhausted"""
    pass

class CircuitBreakerError(Exception):
    """Exception raised when circuit breaker is open"""
    pass

class CircuitBreaker:
    """
    Circuit breaker implementation to prevent cascading failures.
    
    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Failure threshold exceeded, requests fail immediately
    - HALF_OPEN: Testing if service has recovered
    """
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    def can_execute(self) -> bool:
        """Check if request can be executed based on circuit breaker state"""
        if self.state == "CLOSED":
            return True
        elif self.state == "OPEN":
            if (datetime.now() - self.last_failure_time).seconds >= self.recovery_timeout:
                self.state = "HALF_OPEN"
                logger.info("Circuit breaker transitioning to HALF_OPEN")
                return True
            return False
        elif self.state == "HALF_OPEN":
            return True
        return False
    
    def record_success(self):
        """Record successful operation"""
        self.failure_count = 0
        if self.state == "HALF_OPEN":
            self.state = "CLOSED"
            logger.info("Circuit breaker reset to CLOSED")
    
    def record_failure(self):
        """Record failed operation"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            logger.warning(f"Circuit breaker opened after {self.failure_count} failures")

class RetryPolicy:
    """
    Configurable retry policy with exponential backoff and jitter.
    """
    
    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        retryable_exceptions: Optional[List[type]] = None,
        circuit_breaker: Optional[CircuitBreaker] = None
    ):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.retryable_exceptions = retryable_exceptions or [Exception]
        self.circuit_breaker = circuit_breaker
    
    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt number"""
        delay = self.base_delay * (self.exponential_base ** (attempt - 1))
        delay = min(delay, self.max_delay)
        
        if self.jitter:
            # Add random jitter to prevent thundering herd
            delay *= (0.5 + random.random() * 0.5)
        
        return delay
    
    def is_retryable_exception(self, exception: Exception) -> bool:
        """Check if exception is retryable"""
        return any(isinstance(exception, exc_type) for exc_type in self.retryable_exceptions)

class RetryManager:
    """
    Central manager for retry policies and circuit breakers.
    
    Provides predefined policies for different WingmanMatch services.
    """
    
    def __init__(self):
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.policies: Dict[str, RetryPolicy] = {}
        self._initialize_policies()
    
    def _initialize_policies(self):
        """Initialize predefined retry policies for WingmanMatch services"""
        
        # Anthropic API policy - more aggressive retries for critical AI operations
        self.policies["anthropic"] = RetryPolicy(
            max_attempts=3,
            base_delay=1.0,
            max_delay=30.0,
            exponential_base=2.0,
            jitter=True,
            retryable_exceptions=[
                ConnectionError,
                TimeoutError,
                # Add Anthropic-specific exceptions here
            ],
            circuit_breaker=self._get_or_create_circuit_breaker("anthropic", 5, 120)
        )
        
        # Supabase API policy - database operations
        self.policies["supabase"] = RetryPolicy(
            max_attempts=3,
            base_delay=0.5,
            max_delay=15.0,
            exponential_base=2.0,
            jitter=True,
            retryable_exceptions=[
                ConnectionError,
                TimeoutError,
            ],
            circuit_breaker=self._get_or_create_circuit_breaker("supabase", 3, 60)
        )
        
        # Email service policy - can tolerate failures
        self.policies["email"] = RetryPolicy(
            max_attempts=2,
            base_delay=2.0,
            max_delay=30.0,
            exponential_base=2.0,
            jitter=True,
            retryable_exceptions=[
                ConnectionError,
                TimeoutError,
            ],
            circuit_breaker=self._get_or_create_circuit_breaker("email", 5, 300)  # 5 min recovery
        )
        
        # Redis policy - caching operations, should fail fast
        self.policies["redis"] = RetryPolicy(
            max_attempts=2,
            base_delay=0.1,
            max_delay=1.0,
            exponential_base=2.0,
            jitter=False,
            retryable_exceptions=[
                ConnectionError,
                TimeoutError,
            ],
            circuit_breaker=self._get_or_create_circuit_breaker("redis", 3, 30)
        )
        
        # General HTTP API policy
        self.policies["http"] = RetryPolicy(
            max_attempts=3,
            base_delay=1.0,
            max_delay=20.0,
            exponential_base=2.0,
            jitter=True,
            retryable_exceptions=[
                ConnectionError,
                TimeoutError,
            ],
            circuit_breaker=self._get_or_create_circuit_breaker("http", 5, 60)
        )
    
    def _get_or_create_circuit_breaker(
        self, 
        service: str, 
        failure_threshold: int, 
        recovery_timeout: int
    ) -> CircuitBreaker:
        """Get or create circuit breaker for service"""
        if service not in self.circuit_breakers:
            self.circuit_breakers[service] = CircuitBreaker(
                failure_threshold=failure_threshold,
                recovery_timeout=recovery_timeout
            )
        return self.circuit_breakers[service]
    
    def get_policy(self, service: str) -> RetryPolicy:
        """Get retry policy for service"""
        return self.policies.get(service, self.policies["http"])
    
    def get_circuit_breaker_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all circuit breakers"""
        status = {}
        for service, cb in self.circuit_breakers.items():
            status[service] = {
                "state": cb.state,
                "failure_count": cb.failure_count,
                "last_failure": cb.last_failure_time.isoformat() if cb.last_failure_time else None,
                "can_execute": cb.can_execute()
            }
        return status

# Global retry manager instance
retry_manager = RetryManager()

def with_retry(
    service: str = "http",
    policy: Optional[RetryPolicy] = None,
    on_retry: Optional[Callable[[int, Exception], None]] = None,
    on_failure: Optional[Callable[[Exception], None]] = None
):
    """
    Decorator for adding retry logic to async functions.
    
    Args:
        service: Service name to get predefined policy
        policy: Custom retry policy (overrides service policy)
        on_retry: Callback function called on each retry
        on_failure: Callback function called on final failure
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            used_policy = policy or retry_manager.get_policy(service)
            last_exception = None
            
            for attempt in range(1, used_policy.max_attempts + 1):
                # Check circuit breaker
                if used_policy.circuit_breaker and not used_policy.circuit_breaker.can_execute():
                    raise CircuitBreakerError(f"Circuit breaker open for service: {service}")
                
                try:
                    result = await func(*args, **kwargs)
                    
                    # Record success in circuit breaker
                    if used_policy.circuit_breaker:
                        used_policy.circuit_breaker.record_success()
                    
                    # Log success after retries
                    if attempt > 1:
                        logger.info(f"Function {func.__name__} succeeded on attempt {attempt}")
                    
                    return result
                    
                except Exception as e:
                    last_exception = e
                    
                    # Record failure in circuit breaker
                    if used_policy.circuit_breaker:
                        used_policy.circuit_breaker.record_failure()
                    
                    # Check if exception is retryable
                    if not used_policy.is_retryable_exception(e):
                        logger.error(f"Non-retryable exception in {func.__name__}: {str(e)}")
                        raise e
                    
                    # Check if this is the last attempt
                    if attempt == used_policy.max_attempts:
                        logger.error(f"All retry attempts exhausted for {func.__name__}: {str(e)}")
                        if on_failure:
                            on_failure(e)
                        raise RetryError(f"Max retries ({used_policy.max_attempts}) exceeded") from e
                    
                    # Calculate delay and wait
                    delay = used_policy.calculate_delay(attempt)
                    logger.warning(
                        f"Retry attempt {attempt}/{used_policy.max_attempts} for {func.__name__} "
                        f"failed: {str(e)}. Retrying in {delay:.2f}s"
                    )
                    
                    if on_retry:
                        on_retry(attempt, e)
                    
                    await asyncio.sleep(delay)
            
            # This should never be reached, but just in case
            raise last_exception
        
        return wrapper
    return decorator

async def execute_with_retry(
    func: Callable,
    service: str = "http",
    policy: Optional[RetryPolicy] = None,
    *args,
    **kwargs
) -> Any:
    """
    Execute function with retry logic (functional approach).
    
    Args:
        func: Async function to execute
        service: Service name for predefined policy
        policy: Custom retry policy
        *args, **kwargs: Arguments to pass to function
        
    Returns:
        Function result
        
    Raises:
        RetryError: When all retry attempts are exhausted
        CircuitBreakerError: When circuit breaker is open
    """
    used_policy = policy or retry_manager.get_policy(service)
    last_exception = None
    
    for attempt in range(1, used_policy.max_attempts + 1):
        # Check circuit breaker
        if used_policy.circuit_breaker and not used_policy.circuit_breaker.can_execute():
            raise CircuitBreakerError(f"Circuit breaker open for service: {service}")
        
        try:
            result = await func(*args, **kwargs)
            
            # Record success in circuit breaker
            if used_policy.circuit_breaker:
                used_policy.circuit_breaker.record_success()
            
            return result
            
        except Exception as e:
            last_exception = e
            
            # Record failure in circuit breaker
            if used_policy.circuit_breaker:
                used_policy.circuit_breaker.record_failure()
            
            # Check if exception is retryable
            if not used_policy.is_retryable_exception(e):
                raise e
            
            # Check if this is the last attempt
            if attempt == used_policy.max_attempts:
                raise RetryError(f"Max retries ({used_policy.max_attempts}) exceeded") from e
            
            # Calculate delay and wait
            delay = used_policy.calculate_delay(attempt)
            logger.warning(
                f"Retry attempt {attempt}/{used_policy.max_attempts} failed: {str(e)}. "
                f"Retrying in {delay:.2f}s"
            )
            
            await asyncio.sleep(delay)
    
    raise last_exception

# Convenience decorators for specific services

def with_anthropic_retry(on_retry=None, on_failure=None):
    """Decorator for Anthropic API calls"""
    return with_retry("anthropic", on_retry=on_retry, on_failure=on_failure)

def with_supabase_retry(on_retry=None, on_failure=None):
    """Decorator for Supabase API calls"""
    return with_retry("supabase", on_retry=on_retry, on_failure=on_failure)

def with_email_retry(on_retry=None, on_failure=None):
    """Decorator for email service calls"""
    return with_retry("email", on_retry=on_retry, on_failure=on_failure)

def with_redis_retry(on_retry=None, on_failure=None):
    """Decorator for Redis operations"""
    return with_retry("redis", on_retry=on_retry, on_failure=on_failure)

# Health check utilities

async def check_service_health(service: str) -> Dict[str, Any]:
    """
    Check health status of a service including circuit breaker state.
    
    Args:
        service: Service name
        
    Returns:
        Dict with health status information
    """
    circuit_breaker = retry_manager.circuit_breakers.get(service)
    policy = retry_manager.get_policy(service)
    
    health_info = {
        "service": service,
        "policy_configured": True,
        "max_attempts": policy.max_attempts,
        "base_delay": policy.base_delay,
        "max_delay": policy.max_delay
    }
    
    if circuit_breaker:
        health_info.update({
            "circuit_breaker_state": circuit_breaker.state,
            "failure_count": circuit_breaker.failure_count,
            "can_execute": circuit_breaker.can_execute(),
            "last_failure": circuit_breaker.last_failure_time.isoformat() if circuit_breaker.last_failure_time else None
        })
    else:
        health_info["circuit_breaker_state"] = "not_configured"
    
    return health_info

async def get_all_service_health() -> Dict[str, Dict[str, Any]]:
    """Get health status for all configured services"""
    services = list(retry_manager.policies.keys())
    health_status = {}
    
    for service in services:
        health_status[service] = await check_service_health(service)
    
    return health_status

def reset_circuit_breaker(service: str) -> bool:
    """
    Manually reset circuit breaker for a service.
    
    Args:
        service: Service name
        
    Returns:
        bool: True if reset successful, False if service not found
    """
    if service in retry_manager.circuit_breakers:
        cb = retry_manager.circuit_breakers[service]
        cb.failure_count = 0
        cb.state = "CLOSED"
        cb.last_failure_time = None
        logger.info(f"Circuit breaker reset for service: {service}")
        return True
    return False