# ===================================================================
# SECURITY MIDDLEWARE - ENTERPRISE EDITION
# FastAPI Security Middleware Suite
# 
# Features:
# - Request/Response Logging & Audit
# - Security Headers Injection
# - Rate Limit Headers
# - Request ID Generation
# - Performance Monitoring
# ===================================================================

import time
from typing import Callable, Dict, Any
from uuid import uuid4
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR

from .audit_logger import get_audit_logger, AuditEventType, AuditSeverity
from .dependencies import get_client_ip, get_user_agent

logger = logging.getLogger(__name__)

# ===================================================================
# SECURITY MIDDLEWARE
# ===================================================================

class SecurityMiddleware(BaseHTTPMiddleware):
    """
    Enterprise Security Middleware
    
    Features:
    - Automatic security headers injection
    - Request/response audit logging
    - Performance monitoring
    - Request ID generation
    - Rate limit headers management
    """
    
    def __init__(self, app, enable_audit_logging: bool = True):
        super().__init__(app)
        self.enable_audit_logging = enable_audit_logging
        self.audit_logger = get_audit_logger()
        
        # Security headers to add to all responses
        self.default_security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block", 
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "X-Powered-By": "KI-Wissenssystem Enterprise",
            "Server": "KI-Wissenssystem/2.0"
        }
        
        logger.info("Security Middleware initialized")

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and response with security enhancements"""
        
        # Start timing
        start_time = time.time()
        
        # Generate request ID if not present
        request_id = request.headers.get("X-Request-ID") or str(uuid4())
        
        # Add request metadata to state
        request.state.request_id = request_id
        request.state.start_time = start_time
        request.state.client_ip = get_client_ip(request)
        request.state.user_agent = get_user_agent(request)
        
        # Initialize response headers containers
        request.state.security_headers = {}
        request.state.rate_limit_headers = {}
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate response time
            response_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            
            # Add security headers
            await self._add_security_headers(request, response)
            
            # Add rate limit headers if present
            await self._add_rate_limit_headers(request, response)
            
            # Add request tracking headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Response-Time"] = f"{response_time:.2f}ms"
            
            # Log request for audit (if enabled)
            if self.enable_audit_logging:
                await self._log_request(request, response, response_time)
            
            return response
            
        except Exception as e:
            # Handle errors
            response_time = (time.time() - start_time) * 1000
            
            # Log error for audit
            if self.enable_audit_logging:
                await self._log_error(request, e, response_time)
            
            # Create error response
            error_response = Response(
                content=f'{{"error": "Internal server error", "request_id": "{request_id}"}}',
                status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                media_type="application/json"
            )
            
            # Add security headers to error response
            await self._add_security_headers(request, error_response)
            error_response.headers["X-Request-ID"] = request_id
            error_response.headers["X-Response-Time"] = f"{response_time:.2f}ms"
            
            logger.error(f"Request {request_id} failed: {e}")
            return error_response

    async def _add_security_headers(self, request: Request, response: Response):
        """Add security headers to response"""
        
        # Start with default security headers
        headers_to_add = self.default_security_headers.copy()
        
        # Add custom security headers from request state (set by dependencies)
        if hasattr(request.state, 'security_headers'):
            headers_to_add.update(request.state.security_headers)
        
        # Add CORS headers for API endpoints
        if request.url.path.startswith('/api/'):
            headers_to_add.update({
                "Access-Control-Allow-Origin": "*",  # Configure appropriately for production
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                "Access-Control-Allow-Headers": "Authorization, Content-Type, X-Request-ID",
                "Access-Control-Expose-Headers": "X-Request-ID, X-Response-Time, X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset"
            })
        
        # Apply headers to response
        for header_name, header_value in headers_to_add.items():
            response.headers[header_name] = header_value

    async def _add_rate_limit_headers(self, request: Request, response: Response):
        """Add rate limit headers to response"""
        
        if hasattr(request.state, 'rate_limit_headers'):
            for header_name, header_value in request.state.rate_limit_headers.items():
                response.headers[header_name] = header_value

    async def _log_request(self, request: Request, response: Response, response_time: float):
        """Log request for audit trail"""
        
        try:
            # Extract user information if available (set by auth dependencies)
            user_id = getattr(request.state, 'user_id', None)
            user_role = getattr(request.state, 'user_role', None)
            
            # Log API request
            await self.audit_logger.log_api_request(
                user_id=user_id,
                user_role=user_role,
                endpoint=str(request.url.path),
                method=request.method,
                ip_address=request.state.client_ip,
                status_code=response.status_code,
                response_time_ms=response_time,
                request_id=request.state.request_id
            )
            
        except Exception as e:
            logger.error(f"Failed to log request audit: {e}")

    async def _log_error(self, request: Request, error: Exception, response_time: float):
        """Log error for audit trail"""
        
        try:
            # Create audit event for error
            event = self.audit_logger.create_event(
                event_type=AuditEventType.API_REQUEST_FAILURE,
                severity=AuditSeverity.HIGH,
                user_id=getattr(request.state, 'user_id', None),
                user_role=getattr(request.state, 'user_role', None),
                ip_address=request.state.client_ip,
                endpoint=str(request.url.path),
                http_method=request.method,
                request_id=request.state.request_id,
                action="api_request",
                outcome="error",
                error_message=str(error),
                details={
                    "response_time_ms": response_time,
                    "error_type": type(error).__name__
                }
            )
            
            await self.audit_logger.log_event(event)
            
        except Exception as e:
            logger.error(f"Failed to log error audit: {e}")

# ===================================================================
# CORS MIDDLEWARE
# ===================================================================

class CORSMiddleware(BaseHTTPMiddleware):
    """
    Enterprise CORS Middleware with security controls
    """
    
    def __init__(
        self,
        app,
        allow_origins: list = ["*"],
        allow_methods: list = ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers: list = ["Authorization", "Content-Type", "X-Request-ID"],
        expose_headers: list = ["X-Request-ID", "X-Response-Time"],
        allow_credentials: bool = False,
        max_age: int = 86400  # 24 hours
    ):
        super().__init__(app)
        self.allow_origins = allow_origins
        self.allow_methods = allow_methods
        self.allow_headers = allow_headers
        self.expose_headers = expose_headers
        self.allow_credentials = allow_credentials
        self.max_age = max_age
        
        logger.info("CORS Middleware initialized")

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Handle CORS requests"""
        
        # Handle preflight OPTIONS requests
        if request.method == "OPTIONS":
            return await self._handle_preflight(request)
        
        # Process normal request
        response = await call_next(request)
        
        # Add CORS headers to response
        await self._add_cors_headers(request, response)
        
        return response

    async def _handle_preflight(self, request: Request) -> Response:
        """Handle CORS preflight OPTIONS requests"""
        
        origin = request.headers.get("Origin")
        
        # Check if origin is allowed
        if not self._is_origin_allowed(origin):
            return Response(status_code=403, content="Origin not allowed")
        
        # Create preflight response
        response = Response(status_code=200)
        
        # Add CORS headers
        response.headers["Access-Control-Allow-Origin"] = origin or "*"
        response.headers["Access-Control-Allow-Methods"] = ", ".join(self.allow_methods)
        response.headers["Access-Control-Allow-Headers"] = ", ".join(self.allow_headers)
        response.headers["Access-Control-Max-Age"] = str(self.max_age)
        
        if self.allow_credentials:
            response.headers["Access-Control-Allow-Credentials"] = "true"
        
        return response

    async def _add_cors_headers(self, request: Request, response: Response):
        """Add CORS headers to response"""
        
        origin = request.headers.get("Origin")
        
        if self._is_origin_allowed(origin):
            response.headers["Access-Control-Allow-Origin"] = origin or "*"
            
            if self.expose_headers:
                response.headers["Access-Control-Expose-Headers"] = ", ".join(self.expose_headers)
            
            if self.allow_credentials:
                response.headers["Access-Control-Allow-Credentials"] = "true"

    def _is_origin_allowed(self, origin: str) -> bool:
        """Check if origin is in allowed list"""
        
        if not origin:
            return True  # Allow requests without origin header
        
        if "*" in self.allow_origins:
            return True
        
        return origin in self.allow_origins

# ===================================================================
# MIDDLEWARE FACTORY FUNCTIONS
# ===================================================================

def create_security_middleware(enable_audit_logging: bool = True):
    """Create security middleware with configuration"""
    return SecurityMiddleware(enable_audit_logging=enable_audit_logging)

def create_cors_middleware(
    allow_origins: list = None,
    allow_credentials: bool = False,
    development_mode: bool = False
):
    """Create CORS middleware with configuration"""
    
    if development_mode:
        # Permissive settings for development
        allow_origins = allow_origins or ["http://localhost:3000", "http://localhost:3001", "http://127.0.0.1:3000"]
        expose_headers = [
            "X-Request-ID", 
            "X-Response-Time", 
            "X-RateLimit-Limit", 
            "X-RateLimit-Remaining", 
            "X-RateLimit-Reset"
        ]
    else:
        # Restrictive settings for production
        allow_origins = allow_origins or []
        expose_headers = ["X-Request-ID"]
    
    return CORSMiddleware(
        allow_origins=allow_origins,
        allow_credentials=allow_credentials,
        expose_headers=expose_headers
    ) 