# ===================================================================
# AUTHENTICATION DEPENDENCIES - ENTERPRISE EDITION
# FastAPI Authentication & Authorization Dependencies
# 
# Features:
# - JWT Token Validation
# - Role-Based Access Control
# - Resource-Based Access Control
# - Rate Limiting Integration
# - Audit Logging Integration
# - Enterprise Security Headers
# ===================================================================

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, List, Dict, Any, Callable
import logging
from datetime import datetime, timezone

from .jwt_handler import get_jwt_handler, JWTHandler, UserPayload, TokenType
from .rbac import (
    UserRole, Permission, RolePermissions, ResourceType, ResourceAccess,
    check_permissions, check_resource_access
)
from .rate_limiter import get_rate_limiter, RateLimiter, RateLimitType
from .audit_logger import get_audit_logger, AuditLogger, AuditEventType, AuditSeverity

logger = logging.getLogger(__name__)

# ===================================================================
# SECURITY SCHEMES
# ===================================================================

# HTTP Bearer token security scheme
security_scheme = HTTPBearer(
    scheme_name="Bearer Token",
    description="JWT Bearer Token Authentication",
    bearerFormat="JWT",
    auto_error=False  # Don't auto-raise errors, we handle them manually
)

# ===================================================================
# CORE AUTHENTICATION DEPENDENCIES
# ===================================================================

async def get_current_user_optional(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    jwt_handler: JWTHandler = Depends(get_jwt_handler),
    audit_logger: AuditLogger = Depends(get_audit_logger)
) -> Optional[UserPayload]:
    """
    Get current user from JWT token (optional - returns None if no valid token)
    
    Args:
        request: FastAPI request object
        credentials: HTTP Bearer credentials
        jwt_handler: JWT handler instance
        audit_logger: Audit logger instance
        
    Returns:
        UserPayload if valid token, None otherwise
    """
    if not credentials or not credentials.credentials:
        return None
    
    try:
        # Verify JWT token
        token_claims = jwt_handler.verify_token(credentials.credentials, TokenType.ACCESS)
        
        # Create user payload
        user = UserPayload(
            user_id=token_claims.sub,
            email=token_claims.email,
            role=UserRole(token_claims.role),
            team_id=token_claims.team_id,
            permissions=token_claims.permissions
        )
        
        # Log successful authentication
        await audit_logger.log_api_request(
            user_id=user.user_id,
            user_role=user.role,
            endpoint=str(request.url.path),
            method=request.method,
            ip_address=request.client.host if request.client else "unknown",
            status_code=200,
            response_time_ms=0.0  # Will be updated by middleware
        )
        
        return user
        
    except Exception as e:
        # Log failed authentication attempt
        await audit_logger.log_api_request(
            user_id=None,
            user_role=None,
            endpoint=str(request.url.path),
            method=request.method,  
            ip_address=request.client.host if request.client else "unknown",
            status_code=401,
            response_time_ms=0.0
        )
        
        logger.debug(f"Invalid token in optional authentication: {e}")
        return None

async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    jwt_handler: JWTHandler = Depends(get_jwt_handler),
    audit_logger: AuditLogger = Depends(get_audit_logger)
) -> UserPayload:
    """
    Get current user from JWT token (required)
    
    Args:
        request: FastAPI request object
        credentials: HTTP Bearer credentials (required)
        jwt_handler: JWT handler instance
        audit_logger: Audit logger instance
        
    Returns:
        UserPayload with user information
        
    Raises:
        HTTPException: If authentication fails
    """
    if not credentials or not credentials.credentials:
        await audit_logger.log_api_request(
            user_id=None,
            user_role=None,
            endpoint=str(request.url.path),
            method=request.method,
            ip_address=request.client.host if request.client else "unknown",
            status_code=401,
            response_time_ms=0.0
        )
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    try:
        # Verify JWT token
        token_claims = jwt_handler.verify_token(credentials.credentials, TokenType.ACCESS)
        
        # Create user payload
        user = UserPayload(
            user_id=token_claims.sub,
            email=token_claims.email,
            role=UserRole(token_claims.role),
            team_id=token_claims.team_id,
            permissions=token_claims.permissions
        )
        
        # Log successful authentication
        await audit_logger.log_api_request(
            user_id=user.user_id,
            user_role=user.role,
            endpoint=str(request.url.path),
            method=request.method,
            ip_address=request.client.host if request.client else "unknown",
            status_code=200,
            response_time_ms=0.0
        )
        
        return user
        
    except Exception as e:
        # Log failed authentication
        await audit_logger.log_api_request(
            user_id=None,
            user_role=None,
            endpoint=str(request.url.path),
            method=request.method,
            ip_address=request.client.host if request.client else "unknown",
            status_code=401,
            response_time_ms=0.0
        )
        
        logger.warning(f"Authentication failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )

# ===================================================================
# ROLE-BASED ACCESS CONTROL DEPENDENCIES
# ===================================================================

def require_role(required_role: UserRole):
    """
    Dependency factory for role-based access control
    
    Args:
        required_role: Minimum required role
        
    Returns:
        FastAPI dependency function
    """
    async def check_role(
        request: Request,
        current_user: UserPayload = Depends(get_current_user),
        audit_logger: AuditLogger = Depends(get_audit_logger)
    ) -> UserPayload:
        """Check if user has required role"""
        
        # Check if user has required role or higher
        user_role_level = list(UserRole).index(current_user.role)
        required_role_level = list(UserRole).index(required_role)
        
        # For proxy_admin: has access to everything
        if current_user.role == UserRole.PROXY_ADMIN:
            return current_user
            
        # Check role hierarchy (lower index = higher privilege)
        if user_role_level > required_role_level:
            # Log permission denied
            await audit_logger.create_event(
                event_type=AuditEventType.AUTH_PERMISSION_DENIED,
                severity=AuditSeverity.HIGH,
                user_id=current_user.user_id,
                user_email=current_user.email,
                user_role=current_user.role,
                ip_address=request.client.host if request.client else "unknown",
                endpoint=str(request.url.path),
                action="role_check",
                outcome="failure",
                details={
                    "required_role": required_role.value,
                    "user_role": current_user.role.value
                }
            )
            
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient privileges. Role '{required_role.value}' or higher required."
            )
        
        return current_user
    
    return check_role

def require_permissions(required_permissions: List[Permission], require_all: bool = False):
    """
    Dependency factory for permission-based access control
    
    Args:
        required_permissions: List of required permissions
        require_all: If True, user must have ALL permissions. If False, ANY permission.
        
    Returns:
        FastAPI dependency function
    """
    async def check_permissions_dep(
        request: Request,
        current_user: UserPayload = Depends(get_current_user),
        audit_logger: AuditLogger = Depends(get_audit_logger)
    ) -> UserPayload:
        """Check if user has required permissions"""
        
        # Check permissions
        has_permission = check_permissions(current_user.role, required_permissions, require_all)
        
        if not has_permission:
            # Log permission denied
            await audit_logger.create_event(
                event_type=AuditEventType.AUTH_PERMISSION_DENIED,
                severity=AuditSeverity.MEDIUM,
                user_id=current_user.user_id,
                user_email=current_user.email,
                user_role=current_user.role,
                ip_address=request.client.host if request.client else "unknown",
                endpoint=str(request.url.path),
                action="permission_check",
                outcome="failure",
                details={
                    "required_permissions": [p.value for p in required_permissions],
                    "require_all": require_all,
                    "user_role": current_user.role.value
                }
            )
            
            permissions_str = " AND ".join([p.value for p in required_permissions]) if require_all else " OR ".join([p.value for p in required_permissions])
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {permissions_str}"
            )
        
        return current_user
    
    return check_permissions_dep

def require_resource_access(resource_type: ResourceType, action: str):
    """
    Dependency factory for resource-based access control
    
    Args:
        resource_type: Type of resource being accessed  
        action: Action being performed on resource
        
    Returns:
        FastAPI dependency function
    """
    async def check_resource_access_dep(
        request: Request,
        current_user: UserPayload = Depends(get_current_user),
        audit_logger: AuditLogger = Depends(get_audit_logger)
    ) -> UserPayload:
        """Check if user can access specific resource"""
        
        # Check resource access
        is_allowed, reason = check_resource_access(
            current_user.role, 
            resource_type, 
            action
        )
        
        if not is_allowed:
            # Log access denied
            await audit_logger.create_event(
                event_type=AuditEventType.AUTH_PERMISSION_DENIED,
                severity=AuditSeverity.MEDIUM,
                user_id=current_user.user_id,
                user_email=current_user.email,
                user_role=current_user.role,
                ip_address=request.client.host if request.client else "unknown",
                endpoint=str(request.url.path),
                action=f"resource_access_{resource_type.value}_{action}",
                outcome="denied",
                details={
                    "resource_type": resource_type.value,
                    "action": action,
                    "reason": reason
                }
            )
            
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied to {resource_type.value}:{action}. {reason}"
            )
        
        return current_user
    
    return check_resource_access_dep

# ===================================================================
# RATE LIMITING DEPENDENCIES
# ===================================================================

def require_rate_limit(rate_type: RateLimitType, identifier_field: str = "user_id"):
    """
    Dependency factory for rate limiting
    
    Args:
        rate_type: Type of rate limit to apply
        identifier_field: Field to use as identifier (user_id, ip_address)
        
    Returns:
        FastAPI dependency function
    """
    async def check_rate_limit(
        request: Request,
        current_user: Optional[UserPayload] = Depends(get_current_user_optional),
        rate_limiter: RateLimiter = Depends(get_rate_limiter),
        audit_logger: AuditLogger = Depends(get_audit_logger)
    ) -> Dict[str, Any]:
        """Check rate limits"""
        
        # Determine identifier
        if identifier_field == "user_id" and current_user:
            identifier = current_user.user_id
            user_role = current_user.role
        elif identifier_field == "ip_address":
            identifier = request.client.host if request.client else "unknown"
            user_role = current_user.role if current_user else None
        else:
            identifier = "anonymous"
            user_role = None
        
        # Check rate limit
        allowed, metadata = await rate_limiter.check_rate_limit(rate_type, identifier, user_role)
        
        if not allowed:
            # Log rate limit exceeded
            await audit_logger.create_event(
                event_type=AuditEventType.API_RATE_LIMIT_EXCEEDED,
                severity=AuditSeverity.MEDIUM,
                user_id=current_user.user_id if current_user else None,
                user_role=current_user.role if current_user else None,
                ip_address=request.client.host if request.client else "unknown",
                endpoint=str(request.url.path),
                action="rate_limit_check",
                outcome="blocked",
                details={
                    "rate_type": rate_type.value,
                    "identifier": identifier,
                    "limit": metadata.get("limit"),
                    "current_count": metadata.get("current_count")
                }
            )
            
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded",
                headers={
                    "X-RateLimit-Limit": str(metadata.get("limit", 0)),
                    "X-RateLimit-Remaining": str(metadata.get("remaining", 0)),
                    "X-RateLimit-Reset": str(metadata.get("reset_time", 0)),
                    "Retry-After": str(metadata.get("window_seconds", 60))
                }
            )
        
        # Add rate limit headers to response
        request.state.rate_limit_headers = {
            "X-RateLimit-Limit": str(metadata.get("limit", 0)),
            "X-RateLimit-Remaining": str(metadata.get("remaining", 0)),
            "X-RateLimit-Reset": str(metadata.get("reset_time", 0))
        }
        
        return metadata
    
    return check_rate_limit

# ===================================================================
# MODEL MANAGEMENT SPECIFIC DEPENDENCIES  
# ===================================================================

# Model Assignment Dependencies
async def get_model_assignment_reader(
    request: Request,
    current_user: UserPayload = Depends(require_resource_access(ResourceType.MODEL_ASSIGNMENT, "read")),
    rate_limit: Dict[str, Any] = Depends(require_rate_limit(RateLimitType.MODEL_ASSIGNMENT))
) -> UserPayload:
    """Dependency for reading model assignments"""
    return current_user

async def get_model_assignment_writer(
    request: Request,
    current_user: UserPayload = Depends(require_resource_access(ResourceType.MODEL_ASSIGNMENT, "write")),
    rate_limit: Dict[str, Any] = Depends(require_rate_limit(RateLimitType.MODEL_ASSIGNMENT))
) -> UserPayload:
    """Dependency for modifying model assignments"""
    return current_user

async def get_model_performance_reader(
    request: Request,
    current_user: UserPayload = Depends(require_resource_access(ResourceType.MODEL_PERFORMANCE, "read")),
    rate_limit: Dict[str, Any] = Depends(require_rate_limit(RateLimitType.USER_API))
) -> UserPayload:
    """Dependency for reading model performance metrics"""
    return current_user

async def get_system_health_reader(
    request: Request,
    current_user: UserPayload = Depends(require_resource_access(ResourceType.SYSTEM_HEALTH, "read")),
    rate_limit: Dict[str, Any] = Depends(require_rate_limit(RateLimitType.USER_API))
) -> UserPayload:
    """Dependency for reading system health status"""
    return current_user

# ===================================================================
# COMBINED DEPENDENCIES
# ===================================================================

# Admin user dependency (most restrictive)
async def get_admin_user(
    request: Request,
    current_user: UserPayload = Depends(require_role(UserRole.PROXY_ADMIN)),
    rate_limit: Dict[str, Any] = Depends(require_rate_limit(RateLimitType.ADMIN_API))
) -> UserPayload:
    """
    Get admin user with rate limiting
    Combined dependency for admin endpoints
    """
    return current_user

# Model management dependency with granular permissions
async def get_model_manager_user(
    request: Request,
    current_user: UserPayload = Depends(require_permissions([
        Permission.MODEL_READ,
        Permission.MODEL_ASSIGNMENT_READ,
        Permission.MODEL_PERFORMANCE_READ
    ], require_all=False)),
    rate_limit: Dict[str, Any] = Depends(require_rate_limit(RateLimitType.MODEL_ASSIGNMENT))
) -> UserPayload:
    """
    Get user with model management read permissions
    Combined dependency for model management read endpoints
    """
    return current_user

# Model write operations dependency
async def get_model_writer_user(
    request: Request,
    current_user: UserPayload = Depends(require_permissions([
        Permission.MODEL_WRITE,
        Permission.MODEL_ASSIGNMENT_WRITE
    ], require_all=True)),
    rate_limit: Dict[str, Any] = Depends(require_rate_limit(RateLimitType.MODEL_ASSIGNMENT))
) -> UserPayload:
    """
    Get user with model management write permissions
    Combined dependency for model assignment modification endpoints
    """
    return current_user

# API user dependency
async def get_api_user(
    request: Request,
    current_user: UserPayload = Depends(get_current_user),
    rate_limit: Dict[str, Any] = Depends(require_rate_limit(RateLimitType.USER_API))
) -> UserPayload:
    """
    Get API user with standard rate limiting
    Combined dependency for regular API endpoints  
    """
    return current_user

# ===================================================================
# SECURITY MIDDLEWARE DEPENDENCIES
# ===================================================================

async def add_security_headers(request: Request):
    """Add enterprise security headers to response"""
    security_headers = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Content-Security-Policy": "default-src 'self'",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": "geolocation=(), microphone=(), camera=()"
    }
    request.state.security_headers = security_headers
    return security_headers

# ===================================================================
# UTILITY FUNCTIONS
# ===================================================================

def get_client_ip(request: Request) -> str:
    """Extract client IP address from request"""
    # Check for forwarded headers (for proxied requests)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Take the first IP in the chain
        return forwarded_for.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # Fall back to direct client IP
    if request.client:
        return request.client.host
    
    return "unknown"

def get_user_agent(request: Request) -> str:
    """Extract user agent from request"""
    return request.headers.get("User-Agent", "unknown")

def get_request_id(request: Request) -> Optional[str]:
    """Extract request ID from headers"""
    return request.headers.get("X-Request-ID")

def create_audit_context(request: Request, current_user: Optional[UserPayload] = None) -> Dict[str, Any]:
    """Create audit context from request and user"""
    return {
        "endpoint": str(request.url.path),
        "method": request.method,
        "ip_address": get_client_ip(request),
        "user_agent": get_user_agent(request),
        "request_id": get_request_id(request),
        "user_id": current_user.user_id if current_user else None,
        "user_role": current_user.role.value if current_user else None,
        "timestamp": datetime.now(timezone.utc).isoformat()
    } 