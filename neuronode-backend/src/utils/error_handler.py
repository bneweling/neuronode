"""
Enterprise error handling utilities for Neuronode

Provides:
- Structured error logging with context
- Error monitoring and metrics collection
- HTTP error response formatting
- Retry mechanisms with backoff
- Error recovery strategies
"""

import logging
import traceback
import time
from typing import Dict, Any, Optional, Callable, Type
from functools import wraps
from datetime import datetime

from src.config.exceptions import (
    KIWissenssystemException, ErrorCode,
    DocumentProcessingError, LLMServiceError, DatabaseError,
    ProcessingPipelineError, QueryProcessingError, SystemError
)


class ErrorHandler:
    """Centralized error handling with logging and monitoring"""
    
    def __init__(self, logger_name: str = __name__):
        self.logger = logging.getLogger(logger_name)
        self.error_counts: Dict[str, int] = {}
        self.last_errors: Dict[str, datetime] = {}
    
    def log_error(
        self, 
        error: Exception, 
        context: Optional[Dict[str, Any]] = None,
        notify_monitoring: bool = True
    ) -> None:
        """
        Log error with structured context and optional monitoring notification
        
        Args:
            error: The exception that occurred
            context: Additional context for debugging
            notify_monitoring: Whether to notify monitoring systems
        """
        error_info = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "timestamp": datetime.utcnow().isoformat(),
            "context": context or {}
        }
        
        # Add structured error info for custom exceptions
        if isinstance(error, KIWissenssystemException):
            error_info.update({
                "error_code": error.error_code.value,
                "structured_context": error.context,
                "cause": str(error.cause) if error.cause else None
            })
        
        # Add stack trace for debugging
        error_info["stack_trace"] = traceback.format_exc()
        
        # Log based on error severity
        if isinstance(error, (SystemError, DatabaseError)):
            self.logger.critical("CRITICAL_ERROR", extra=error_info)
        elif isinstance(error, LLMServiceError):
            self.logger.error("LLM_SERVICE_ERROR", extra=error_info)
        elif isinstance(error, (DocumentProcessingError, ProcessingPipelineError)):
            self.logger.warning("PROCESSING_ERROR", extra=error_info)
        else:
            self.logger.error("UNEXPECTED_ERROR", extra=error_info)
        
        # Update error metrics
        error_key = f"{type(error).__name__}"
        self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1
        self.last_errors[error_key] = datetime.utcnow()
        
        # TODO: Integrate with monitoring system (Prometheus, DataDog, etc.)
        if notify_monitoring:
            self._notify_monitoring(error, error_info)
    
    def _notify_monitoring(self, error: Exception, error_info: Dict[str, Any]) -> None:
        """Send error metrics to monitoring system"""
        # This would integrate with your monitoring solution
        # For now, we'll log it as a placeholder
        self.logger.info("MONITORING_NOTIFICATION", extra={
            "error_code": getattr(error, 'error_code', 'UNKNOWN'),
            "error_count": self.error_counts.get(type(error).__name__, 0)
        })
    
    def get_error_stats(self) -> Dict[str, Any]:
        """Get current error statistics"""
        return {
            "error_counts": self.error_counts.copy(),
            "last_errors": {k: v.isoformat() for k, v in self.last_errors.items()},
            "total_errors": sum(self.error_counts.values())
        }


# Global error handler instance
error_handler = ErrorHandler()


def handle_exceptions(
    default_error_type: Type[KIWissenssystemException] = SystemError,
    default_error_code: ErrorCode = ErrorCode.DEPENDENCY_ERROR,
    log_level: str = "error",
    reraise: bool = True
):
    """
    Decorator for comprehensive exception handling
    
    Args:
        default_error_type: Exception type to wrap unexpected errors in
        default_error_code: Error code for unexpected errors
        log_level: Logging level for caught exceptions
        reraise: Whether to re-raise the exception after logging
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except KIWissenssystemException as e:
                # Already a structured exception, just log and re-raise
                error_handler.log_error(e, {
                    "function": func.__name__,
                    "args": str(args)[:100],  # Truncate for logging
                    "kwargs": str(kwargs)[:100]
                })
                if reraise:
                    raise
                return None
            except Exception as e:
                # Wrap unexpected exceptions in structured format
                context = {
                    "function": func.__name__,
                    "original_error": str(e),
                    "original_type": type(e).__name__,
                    "args": str(args)[:100],
                    "kwargs": str(kwargs)[:100]
                }
                
                structured_error = default_error_type(
                    f"Unexpected error in {func.__name__}: {str(e)}",
                    default_error_code,
                    context,
                    cause=e
                )
                
                error_handler.log_error(structured_error, context)
                
                if reraise:
                    raise structured_error
                return None
        
        return wrapper
    return decorator


def safe_execute(
    func: Callable, 
    *args, 
    error_type: Type[KIWissenssystemException] = SystemError,
    error_code: ErrorCode = ErrorCode.DEPENDENCY_ERROR,
    default_return: Any = None,
    **kwargs
) -> Any:
    """
    Safely execute a function with comprehensive error handling
    
    Args:
        func: Function to execute
        *args: Function arguments
        error_type: Exception type for wrapping errors
        error_code: Error code for wrapped errors
        default_return: Value to return on error
        **kwargs: Function keyword arguments
    
    Returns:
        Function result or default_return on error
    """
    try:
        return func(*args, **kwargs)
    except KIWissenssystemException as e:
        error_handler.log_error(e, {"function": func.__name__})
        return default_return
    except Exception as e:
        structured_error = error_type(
            f"Error executing {func.__name__}: {str(e)}",
            error_code,
            {"function": func.__name__, "original_error": str(e)},
            cause=e
        )
        error_handler.log_error(structured_error)
        return default_return


def retry_with_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff_factor: float = 2.0,
    retryable_errors: tuple = (LLMServiceError, DatabaseError)
):
    """
    Retry decorator with exponential backoff for transient errors
    
    Args:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay between retries in seconds
        max_delay: Maximum delay between retries in seconds
        backoff_factor: Multiplier for delay between retries
        retryable_errors: Exception types that should trigger retries
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            delay = initial_delay
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except retryable_errors as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        # Log final failure
                        error_handler.log_error(e, {
                            "function": func.__name__,
                            "attempts": attempt + 1,
                            "final_failure": True
                        })
                        raise
                    
                    # Log retry attempt
                    error_handler.logger.warning(
                        f"Retrying {func.__name__} after error (attempt {attempt + 1}/{max_retries}): {str(e)}"
                    )
                    
                    time.sleep(delay)
                    delay = min(delay * backoff_factor, max_delay)
                
                except Exception as e:
                    # Non-retryable error, fail immediately
                    error_handler.log_error(e, {
                        "function": func.__name__,
                        "non_retryable": True
                    })
                    raise
            
            # This should never be reached, but just in case
            if last_exception:
                raise last_exception
        
        return wrapper
    return decorator


def format_http_error_response(error: Exception) -> Dict[str, Any]:
    """
    Format an exception as an HTTP error response
    
    Args:
        error: Exception to format
    
    Returns:
        Dictionary with error details for HTTP response
    """
    if isinstance(error, KIWissenssystemException):
        return {
            "error": {
                "code": error.error_code.value,
                "message": error.message,
                "context": error.context,
                "timestamp": datetime.utcnow().isoformat()
            },
            "status_code": error.get_http_status_code()
        }
    else:
        return {
            "error": {
                "code": "UNKNOWN_ERROR",
                "message": str(error),
                "timestamp": datetime.utcnow().isoformat()
            },
            "status_code": 500
        } 