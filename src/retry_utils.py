"""
Retry utilities for WingmanMatch with exponential backoff
Provides IO operation wrappers and circuit breaker patterns
"""

import logging
import asyncio
import time
from typing import Any, Callable, Dict, Optional, TypeVar, Union
from functools import wraps
import random

logger = logging.getLogger(__name__)

T = TypeVar('T')

class CircuitBreaker:
    """Circuit breaker pattern implementation"""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half-open
    
    def can_execute(self) -> bool:
        """Check if operation can be executed"""
        if self.state == "closed":
            return True
        
        if self.state == "open":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "half-open"
                return True
            return False
        
        # half-open state
        return True
    
    def record_success(self):
        """Record successful operation"""
        self.failure_count = 0
        self.state = "closed"
    
    def record_failure(self):
        """Record failed operation"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "open"
            logger.warning(f"Circuit breaker opened after {self.failure_count} failures")

# Global circuit breakers for different services
circuit_breakers = {
    "supabase": CircuitBreaker(failure_threshold=5, recovery_timeout=60),
    "redis": CircuitBreaker(failure_threshold=3, recovery_timeout=30),
    "email": CircuitBreaker(failure_threshold=3, recovery_timeout=120),
    "external_api": CircuitBreaker(failure_threshold=5, recovery_timeout=60),
}

async def retry_with_exponential_backoff(
    operation: Callable[[], T],
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff_factor: float = 2.0,
    jitter: bool = True,
    circuit_breaker_key: Optional[str] = None
) -> T:
    """
    Retry operation with exponential backoff
    
    Args:
        operation: Async function to retry
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        backoff_factor: Multiplier for delay between retries
        jitter: Add random jitter to prevent thundering herd
        circuit_breaker_key: Circuit breaker to check before retry
    """
    circuit_breaker = circuit_breakers.get(circuit_breaker_key) if circuit_breaker_key else None
    
    for attempt in range(max_retries + 1):
        # Check circuit breaker
        if circuit_breaker and not circuit_breaker.can_execute():
            raise Exception(f"Circuit breaker open for {circuit_breaker_key}")
        
        try:
            result = await operation()
            
            # Record success in circuit breaker
            if circuit_breaker:
                circuit_breaker.record_success()
            
            if attempt > 0:
                logger.info(f"Operation succeeded on attempt {attempt + 1}")
            
            return result
            
        except Exception as e:
            # Record failure in circuit breaker
            if circuit_breaker:
                circuit_breaker.record_failure()
            
            if attempt == max_retries:
                logger.error(f"Operation failed after {max_retries + 1} attempts: {e}")
                raise
            
            # Calculate delay with exponential backoff
            delay = min(base_delay * (backoff_factor ** attempt), max_delay)
            
            # Add jitter to prevent thundering herd
            if jitter:
                delay = delay * (0.5 + random.random() * 0.5)
            
            logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay:.2f}s")
            await asyncio.sleep(delay)

def with_retry(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff_factor: float = 2.0,
    jitter: bool = True,
    circuit_breaker_key: Optional[str] = None
):
    """Decorator for adding retry logic to async functions"""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            async def operation():
                return await func(*args, **kwargs)
            
            return await retry_with_exponential_backoff(
                operation=operation,
                max_retries=max_retries,
                base_delay=base_delay,
                max_delay=max_delay,
                backoff_factor=backoff_factor,
                jitter=jitter,
                circuit_breaker_key=circuit_breaker_key
            )
        
        return wrapper
    return decorator

class RetryableOperation:
    """Context manager for retryable operations with timeout"""
    
    def __init__(self, name: str, timeout: float = 30.0, circuit_breaker_key: Optional[str] = None):
        self.name = name
        self.timeout = timeout
        self.circuit_breaker_key = circuit_breaker_key
        self.start_time = None
    
    async def __aenter__(self):
        self.start_time = time.time()
        
        circuit_breaker = circuit_breakers.get(self.circuit_breaker_key) if self.circuit_breaker_key else None
        if circuit_breaker and not circuit_breaker.can_execute():
            raise Exception(f"Circuit breaker open for {self.circuit_breaker_key}")
        
        logger.debug(f"Starting retryable operation: {self.name}")
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        circuit_breaker = circuit_breakers.get(self.circuit_breaker_key) if self.circuit_breaker_key else None
        
        if exc_type is None:
            # Success
            if circuit_breaker:
                circuit_breaker.record_success()
            logger.debug(f"Operation {self.name} completed successfully in {duration:.2f}s")
        else:
            # Failure
            if circuit_breaker:
                circuit_breaker.record_failure()
            logger.error(f"Operation {self.name} failed after {duration:.2f}s: {exc_val}")
        
        return False  # Don't suppress exceptions

# Convenience functions for common operations

@with_retry(max_retries=3, circuit_breaker_key="supabase")
async def retry_supabase_operation(operation: Callable[[], T]) -> T:
    """Retry Supabase database operations"""
    return await operation()

@with_retry(max_retries=2, base_delay=0.5, circuit_breaker_key="redis")
async def retry_redis_operation(operation: Callable[[], T]) -> T:
    """Retry Redis operations with shorter delays"""
    return await operation()

@with_retry(max_retries=3, base_delay=2.0, circuit_breaker_key="email")
async def retry_email_operation(operation: Callable[[], T]) -> T:
    """Retry email operations with longer delays"""
    return await operation()

@with_retry(max_retries=2, circuit_breaker_key="external_api")
async def retry_external_api_call(operation: Callable[[], T]) -> T:
    """Retry external API calls"""
    return await operation()

def get_circuit_breaker_status() -> Dict[str, Dict[str, Any]]:
    """Get status of all circuit breakers"""
    status = {}
    for name, breaker in circuit_breakers.items():
        status[name] = {
            "state": breaker.state,
            "failure_count": breaker.failure_count,
            "failure_threshold": breaker.failure_threshold,
            "last_failure_time": breaker.last_failure_time,
            "recovery_timeout": breaker.recovery_timeout
        }
    return status