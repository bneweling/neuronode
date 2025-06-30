"""
Enterprise-grade exception hierarchy for Neuronode

This module provides structured exception handling with:
- Specific exception types for different error categories
- Error codes for monitoring and debugging
- Structured error context for logging
- HTTP status code mapping for API responses
"""

from typing import Dict, Any, Optional
from enum import Enum


class ErrorCode(Enum):
    """Structured error codes for monitoring and debugging"""
    
    # Document Processing Errors (1000-1999)
    DOCUMENT_UPLOAD_FAILED = "DOC_1001"
    DOCUMENT_TYPE_UNSUPPORTED = "DOC_1002"
    DOCUMENT_PARSING_FAILED = "DOC_1003"
    DOCUMENT_TOO_LARGE = "DOC_1004"
    DOCUMENT_CORRUPTED = "DOC_1005"
    DOCUMENT_CLASSIFICATION_FAILED = "DOC_1006"
    
    # LLM Service Errors (2000-2999)
    LLM_API_UNAVAILABLE = "LLM_2001"
    LLM_API_QUOTA_EXCEEDED = "LLM_2002"
    LLM_RESPONSE_INVALID = "LLM_2003"
    LLM_TIMEOUT = "LLM_2004"
    LLM_AUTHENTICATION_FAILED = "LLM_2005"
    LLM_MODEL_NOT_FOUND = "LLM_2006"
    
    # Database Errors (3000-3999)
    NEO4J_CONNECTION_FAILED = "DB_3001"
    NEO4J_QUERY_FAILED = "DB_3002"
    CHROMADB_CONNECTION_FAILED = "DB_3003"
    CHROMADB_QUERY_FAILED = "DB_3004"
    REDIS_CONNECTION_FAILED = "DB_3005"
    
    # Processing Pipeline Errors (4000-4999)
    EXTRACTION_FAILED = "PROC_4001"
    VALIDATION_FAILED = "PROC_4002"
    CHUNKING_FAILED = "PROC_4003"
    ENTITY_LINKING_FAILED = "PROC_4004"
    QUALITY_CHECK_FAILED = "PROC_4005"
    
    # Query Processing Errors (5000-5999)
    QUERY_ANALYSIS_FAILED = "QUERY_5001"
    RETRIEVAL_FAILED = "QUERY_5002"
    SYNTHESIS_FAILED = "QUERY_5003"
    INTENT_RECOGNITION_FAILED = "QUERY_5004"
    
    # System Errors (6000-6999)
    CONFIGURATION_ERROR = "SYS_6001"
    DEPENDENCY_ERROR = "SYS_6002"
    RESOURCE_EXHAUSTED = "SYS_6003"
    PERMISSION_DENIED = "SYS_6004"
    CONCURRENT_MODIFICATION = "SYS_6005"


class KIWissenssystemException(Exception):
    """Base exception for all Neuronode specific errors"""
    
    def __init__(
        self, 
        message: str,
        error_code: ErrorCode,
        context: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.context = context or {}
        self.cause = cause
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to structured dictionary for logging/API responses"""
        return {
            "error_code": self.error_code.value,
            "message": self.message,
            "context": self.context,
            "cause": str(self.cause) if self.cause else None
        }
    
    def get_http_status_code(self) -> int:
        """Map exception to appropriate HTTP status code"""
        return 500  # Default to 500 for base exception


class DocumentProcessingError(KIWissenssystemException):
    """Errors during document processing pipeline"""
    
    def get_http_status_code(self) -> int:
        status_mapping = {
            ErrorCode.DOCUMENT_TYPE_UNSUPPORTED: 415,
            ErrorCode.DOCUMENT_TOO_LARGE: 413,
            ErrorCode.DOCUMENT_CORRUPTED: 400,
            ErrorCode.DOCUMENT_UPLOAD_FAILED: 400
        }
        return status_mapping.get(self.error_code, 422)


class LLMServiceError(KIWissenssystemException):
    """Errors from LLM API services"""
    
    def get_http_status_code(self) -> int:
        status_mapping = {
            ErrorCode.LLM_API_QUOTA_EXCEEDED: 429,
            ErrorCode.LLM_AUTHENTICATION_FAILED: 401,
            ErrorCode.LLM_TIMEOUT: 504,
            ErrorCode.LLM_API_UNAVAILABLE: 503
        }
        return status_mapping.get(self.error_code, 502)


class DatabaseError(KIWissenssystemException):
    """Database connection and query errors"""
    
    def get_http_status_code(self) -> int:
        return 503  # Service Unavailable for database issues


class ProcessingPipelineError(KIWissenssystemException):
    """Errors in the document processing pipeline"""
    
    def get_http_status_code(self) -> int:
        return 422  # Unprocessable Entity


class QueryProcessingError(KIWissenssystemException):
    """Errors during query processing and response generation"""
    
    def get_http_status_code(self) -> int:
        return 400  # Bad Request for query processing issues


class SystemError(KIWissenssystemException):
    """System-level configuration and dependency errors"""
    
    def get_http_status_code(self) -> int:
        status_mapping = {
            ErrorCode.PERMISSION_DENIED: 403,
            ErrorCode.RESOURCE_EXHAUSTED: 503,
            ErrorCode.CONFIGURATION_ERROR: 500
        }
        return status_mapping.get(self.error_code, 500)


# Convenience functions for common error patterns
def document_error(message: str, error_code: ErrorCode, **context) -> DocumentProcessingError:
    """Create a document processing error with context"""
    return DocumentProcessingError(message, error_code, context)


def llm_error(message: str, error_code: ErrorCode, **context) -> LLMServiceError:
    """Create an LLM service error with context"""
    return LLMServiceError(message, error_code, context)


def database_error(message: str, error_code: ErrorCode, **context) -> DatabaseError:
    """Create a database error with context"""
    return DatabaseError(message, error_code, context)


def processing_error(message: str, error_code: ErrorCode, **context) -> ProcessingPipelineError:
    """Create a processing pipeline error with context"""
    return ProcessingPipelineError(message, error_code, context)


def query_error(message: str, error_code: ErrorCode, **context) -> QueryProcessingError:
    """Create a query processing error with context"""
    return QueryProcessingError(message, error_code, context)


def system_error(message: str, error_code: ErrorCode, **context) -> SystemError:
    """Create a system error with context"""
    return SystemError(message, error_code, context) 