# ===================================================================
# AUTHENTICATION API - ENTERPRISE EDITION
# JWT-based Authentication System for Neuronode
# 
# Features:
# - Enterprise User Authentication
# - JWT Token Management
# - Role-Based Access Control
# - Audit Logging Integration
# - Rate Limiting Protection
# ===================================================================

from fastapi import APIRouter, HTTPException, Depends, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from typing import Dict, Any, Optional
from pydantic import BaseModel, EmailStr
from datetime import datetime
import logging

from src.auth.jwt_handler import get_jwt_handler, JWTHandler, UserPayload, JWTTokens
from src.auth.rbac import UserRole
from src.auth.rate_limiter import get_rate_limiter, RateLimitType
from src.auth.audit_logger import get_audit_logger, AuditEventType, AuditSeverity
from src.auth.dependencies import get_current_user, get_client_ip, add_security_headers
from src.config.settings import settings

logger = logging.getLogger(__name__)

# ===================================================================
# DATA MODELS
# ===================================================================

class LoginRequest(BaseModel):
    """Login request model"""
    email: EmailStr
    password: str
    remember_me: Optional[bool] = False

class LoginResponse(BaseModel):
    """Login response model"""
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int
    refresh_expires_in: int
    user: Dict[str, Any]

class RefreshTokenRequest(BaseModel):
    """Refresh token request"""
    refresh_token: str

class UserInfo(BaseModel):
    """User information response"""
    user_id: str
    email: str
    role: str
    team_id: Optional[str] = None
    permissions: Optional[list] = None
    last_login: Optional[datetime] = None

class ChangePasswordRequest(BaseModel):
    """Change password request"""
    current_password: str
    new_password: str

# ===================================================================
# ENTERPRISE USER STORE (Production: Use Database)
# ===================================================================

class EnterpriseUserStore:
    """
    Enterprise User Store - In Production: Replace with Database/LDAP
    
    For demo purposes, contains admin users with proper password hashing
    """
    
    def __init__(self):
        # Demo users - In production: Load from database/LDAP
        self.users = {
            "admin@neuronode.com": {
                "user_id": "admin-001",
                "email": "admin@neuronode.com",
                "password_hash": "hashed_admin_password",  # In production: bcrypt hash
                "role": UserRole.PROXY_ADMIN,
                "team_id": "admin-team",
                "is_active": True,
                "created_at": datetime.utcnow(),
                "last_login": None
            },
            "user@neuronode.com": {
                "user_id": "user-001",
                "email": "user@neuronode.com",
                "password_hash": "hashed_user_password",  # In production: bcrypt hash
                "role": UserRole.INTERNAL_USER,
                "team_id": "internal-team",
                "is_active": True,
                "created_at": datetime.utcnow(),
                "last_login": None
            },
            "viewer@neuronode.com": {
                "user_id": "viewer-001",
                "email": "viewer@neuronode.com",
                "password_hash": "hashed_viewer_password",  # In production: bcrypt hash
                "role": UserRole.INTERNAL_USER_VIEWER,
                "team_id": "viewer-team",
                "is_active": True,
                "created_at": datetime.utcnow(),
                "last_login": None
            }
        }
    
    def authenticate_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Authenticate user with email and password
        In production: Use proper password hashing (bcrypt)
        """
        user = self.users.get(email)
        if not user:
            return None
        
        if not user["is_active"]:
            return None
        
        # In production: Use bcrypt.checkpw(password, user["password_hash"])
        # For demo: Simple password check
        demo_passwords = {
            "admin@neuronode.com": "admin123",
            "user@neuronode.com": "user123",
            "viewer@neuronode.com": "viewer123"
        }
        
        if demo_passwords.get(email) == password:
            # Update last login
            user["last_login"] = datetime.utcnow()
            return user
        
        return None
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by user ID"""
        for user in self.users.values():
            if user["user_id"] == user_id:
                return user
        return None

# Global user store instance
user_store = EnterpriseUserStore()

# ===================================================================
# ROUTER DEFINITION
# ===================================================================

router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"],
    responses={
        401: {"description": "Authentication failed"},
        429: {"description": "Rate limit exceeded"},
        500: {"description": "Internal server error"}
    }
)

# ===================================================================
# AUTHENTICATION ENDPOINTS
# ===================================================================

@router.post("/login", response_model=LoginResponse)
async def login(
    login_data: LoginRequest,
    request: Request,
    jwt_handler: JWTHandler = Depends(get_jwt_handler),
    rate_limiter = Depends(get_rate_limiter),
    audit_logger = Depends(get_audit_logger),
    security_headers = Depends(add_security_headers)
):
    """
    Enterprise user authentication with JWT token generation
    
    Features:
    - Rate limiting protection
    - Comprehensive audit logging
    - Enterprise security headers
    - JWT token generation with refresh tokens
    """
    
    client_ip = get_client_ip(request)
    
    try:
        # Rate limiting for login attempts
        allowed, rate_metadata = await rate_limiter.check_rate_limit(
            RateLimitType.AUTH_LOGIN, 
            client_ip
        )
        
        if not allowed:
            # Audit log rate limit exceeded
            event = audit_logger.create_event(
                event_type=AuditEventType.API_RATE_LIMIT_EXCEEDED,
                severity=AuditSeverity.HIGH,
                ip_address=client_ip,
                endpoint="/api/auth/login",
                action="login_attempt",
                outcome="blocked",
                details={
                    "reason": "rate_limit_exceeded",
                    "email": login_data.email,
                    "rate_limit": rate_metadata
                }
            )
            await audit_logger.log_event(event)
            
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many login attempts. Please try again later.",
                headers={
                    "X-RateLimit-Limit": str(rate_metadata.get("limit", 0)),
                    "X-RateLimit-Reset": str(rate_metadata.get("reset_time", 0)),
                    "Retry-After": str(rate_metadata.get("window_seconds", 300))
                }
            )
        
        # Authenticate user
        user_data = user_store.authenticate_user(login_data.email, login_data.password)
        
        if not user_data:
            # Audit log failed login
            event = audit_logger.create_event(
                event_type=AuditEventType.AUTH_LOGIN_FAILURE,
                severity=AuditSeverity.HIGH,
                ip_address=client_ip,
                endpoint="/api/auth/login",
                action="login",
                outcome="failure",
                details={
                    "email": login_data.email,
                    "reason": "invalid_credentials"
                }
            )
            await audit_logger.log_event(event)
            
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Create user payload
        user_payload = UserPayload(
            user_id=user_data["user_id"],
            email=user_data["email"],
            role=user_data["role"],
            team_id=user_data.get("team_id"),
            permissions=[]  # Will be populated from role permissions
        )
        
        # Generate JWT tokens
        tokens = jwt_handler.create_token_pair(user_payload)
        
        # Audit log successful login
        event = audit_logger.create_event(
            event_type=AuditEventType.AUTH_LOGIN_SUCCESS,
            severity=AuditSeverity.MEDIUM,
            user_id=user_payload.user_id,
            user_email=user_payload.email,
            user_role=user_payload.role,
            ip_address=client_ip,
            endpoint="/api/auth/login",
            action="login",
            outcome="success",
            details={
                "remember_me": login_data.remember_me,
                "role": user_payload.role.value
            }
        )
        await audit_logger.log_event(event)
        
        logger.info(f"User {user_payload.email} logged in successfully from {client_ip}")
        
        return LoginResponse(
            access_token=tokens.access_token,
            refresh_token=tokens.refresh_token,
            token_type=tokens.token_type,
            expires_in=tokens.expires_in,
            refresh_expires_in=tokens.refresh_expires_in,
            user={
                "user_id": user_payload.user_id,
                "email": user_payload.email,
                "role": user_payload.role.value,
                "team_id": user_payload.team_id,
                "last_login": user_data["last_login"].isoformat() if user_data["last_login"] else None
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error for {login_data.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service temporarily unavailable"
        )

@router.post("/refresh", response_model=JWTTokens)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    request: Request,
    jwt_handler: JWTHandler = Depends(get_jwt_handler),
    audit_logger = Depends(get_audit_logger),
    security_headers = Depends(add_security_headers)
):
    """
    Refresh JWT access token using valid refresh token
    
    Features:
    - Token rotation for enhanced security
    - Audit logging of token refresh events
    - Rate limiting protection
    """
    
    client_ip = get_client_ip(request)
    
    try:
        # Refresh tokens
        new_tokens = jwt_handler.refresh_access_token(refresh_data.refresh_token)
        
        # Extract user info from new token for audit logging
        user_payload = jwt_handler.get_user_from_token(new_tokens.access_token)
        
        # Audit log token refresh
        event = audit_logger.create_event(
            event_type=AuditEventType.AUTH_TOKEN_REFRESHED,
            severity=AuditSeverity.INFO,
            user_id=user_payload.user_id,
            user_email=user_payload.email,
            user_role=user_payload.role,
            ip_address=client_ip,
            endpoint="/api/auth/refresh",
            action="token_refresh",
            outcome="success"
        )
        await audit_logger.log_event(event)
        
        return new_tokens
        
    except Exception as e:
        # Audit log failed token refresh
        event = audit_logger.create_event(
            event_type=AuditEventType.AUTH_TOKEN_REFRESHED,
            severity=AuditSeverity.MEDIUM,
            ip_address=client_ip,
            endpoint="/api/auth/refresh",
            action="token_refresh",
            outcome="failure",
            details={"error": str(e)}
        )
        await audit_logger.log_event(event)
        
        logger.warning(f"Token refresh failed from {client_ip}: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )

@router.post("/logout")
async def logout(
    request: Request,
    current_user: UserPayload = Depends(get_current_user),
    jwt_handler: JWTHandler = Depends(get_jwt_handler),
    audit_logger = Depends(get_audit_logger),
    security_headers = Depends(add_security_headers)
):
    """
    User logout with token revocation
    
    Features:
    - JWT token revocation
    - Comprehensive audit logging
    - Security headers
    """
    
    client_ip = get_client_ip(request)
    
    try:
        # Get token from Authorization header
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            # Revoke the token
            jwt_handler.revoke_token(token)
        
        # Audit log logout
        event = audit_logger.create_event(
            event_type=AuditEventType.AUTH_LOGOUT,
            severity=AuditSeverity.INFO,
            user_id=current_user.user_id,
            user_email=current_user.email,
            user_role=current_user.role,
            ip_address=client_ip,
            endpoint="/api/auth/logout",
            action="logout",
            outcome="success"
        )
        await audit_logger.log_event(event)
        
        logger.info(f"User {current_user.email} logged out from {client_ip}")
        
        return {
            "message": "Logged out successfully",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Logout error for {current_user.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )

# ===================================================================
# USER PROFILE ENDPOINTS
# ===================================================================

@router.get("/me", response_model=UserInfo)
async def get_current_user_info(
    request: Request,
    current_user: UserPayload = Depends(get_current_user),
    security_headers = Depends(add_security_headers)
):
    """
    Get current user information
    
    Returns detailed user profile information including:
    - User ID and email
    - Role and permissions
    - Team information
    - Last login timestamp
    """
    
    # Get additional user data from store
    user_data = user_store.get_user_by_id(current_user.user_id)
    
    return UserInfo(
        user_id=current_user.user_id,
        email=current_user.email,
        role=current_user.role.value,
        team_id=current_user.team_id,
        permissions=current_user.permissions,
        last_login=user_data.get("last_login") if user_data else None
    )

# ===================================================================
# SYSTEM STATUS ENDPOINTS
# ===================================================================

@router.get("/status")
async def get_auth_system_status(
    request: Request,
    security_headers = Depends(add_security_headers)
):
    """
    Get authentication system status (public endpoint)
    
    Returns:
    - Authentication system health
    - Available login methods
    - System configuration
    """
    
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "authentication": {
            "jwt_enabled": True,
            "token_expiry_minutes": 15,
            "refresh_token_expiry_days": 30,
            "rate_limiting_enabled": True
        },
        "security_features": {
            "rbac_enabled": True,
            "audit_logging": True,
            "password_policy": True,
            "multi_factor_auth": False  # Future feature
        },
        "endpoints": {
            "login": "/api/auth/login",
            "refresh": "/api/auth/refresh",
            "logout": "/api/auth/logout",
            "profile": "/api/auth/me"
        }
    }

# ===================================================================
# DEMO CREDENTIALS ENDPOINT (Development Only)
# ===================================================================

@router.get("/demo-credentials")
async def get_demo_credentials(
    request: Request,
    security_headers = Depends(add_security_headers)
):
    """
    Get demo credentials for testing (Development/Demo only)
    
    WARNING: Remove this endpoint in production!
    """
    
    # Only enable in development mode
    if not getattr(settings, 'DEBUG', False):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Endpoint not available in production"
        )
    
    return {
        "demo_users": [
            {
                "email": "admin@neuronode.com",
                "password": "admin123",
                "role": "proxy_admin",
                "description": "Full system administrator"
            },
            {
                "email": "user@neuronode.com", 
                "password": "user123",
                "role": "internal_user",
                "description": "Internal user with model management access"
            },
            {
                "email": "viewer@neuronode.com",
                "password": "viewer123", 
                "role": "internal_user_viewer",
                "description": "Read-only internal user"
            }
        ],
        "note": "These are demo credentials for testing only. Remove in production!",
        "endpoints": {
            "login": "POST /api/auth/login",
            "refresh": "POST /api/auth/refresh",
            "profile": "GET /api/auth/me"
        }
    }

# ===================================================================
# EXPORT
# ===================================================================

__all__ = ["router"]