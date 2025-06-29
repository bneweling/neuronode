# ===================================================================
# JWT HANDLER - ENTERPRISE EDITION
# Production-Ready JWT Authentication & Authorization System
# 
# Features:
# - JWT Access & Refresh Tokens
# - Role-Based Access Control (RBAC)
# - Token Rotation & Security
# - Audit Logging Integration
# - Enterprise Security Standards
# ===================================================================

import jwt
import secrets
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, Union
from pydantic import BaseModel, Field
from enum import Enum
import logging
import hashlib
import hmac
from dataclasses import dataclass

from src.config.settings import settings

logger = logging.getLogger(__name__)

# ===================================================================
# DATA MODELS & TYPES
# ===================================================================

class UserRole(str, Enum):
    """Enterprise User Roles based on LiteLLM Enterprise Documentation"""
    PROXY_ADMIN = "proxy_admin"                    # Full system access
    INTERNAL_USER = "internal_user"               # API access + limited admin  
    INTERNAL_USER_VIEWER = "internal_user_viewer" # Read-only access
    TEAM = "team"                                 # Team-scoped access
    CUSTOMER = "customer"                         # External user access

class TokenType(str, Enum):
    """JWT Token Types"""
    ACCESS = "access"
    REFRESH = "refresh"

@dataclass
class UserPayload:
    """User information for JWT payload"""
    user_id: str
    email: str
    role: UserRole
    team_id: Optional[str] = None
    permissions: Optional[list] = None
    
class JWTTokens(BaseModel):
    """JWT Token Pair Response"""
    access_token: str = Field(..., description="Short-lived access token")
    refresh_token: str = Field(..., description="Long-lived refresh token")
    token_type: str = Field(default="Bearer", description="Token type")
    expires_in: int = Field(..., description="Access token expiry in seconds")
    refresh_expires_in: int = Field(..., description="Refresh token expiry in seconds")

class TokenClaims(BaseModel):
    """JWT Token Claims"""
    sub: str  # User ID
    email: str
    role: str
    team_id: Optional[str] = None
    permissions: Optional[list] = None
    token_type: str
    iat: int  # Issued at
    exp: int  # Expires at
    jti: str  # JWT ID (for revocation)

# ===================================================================
# JWT HANDLER CLASS
# ===================================================================

class JWTHandler:
    """
    Enterprise JWT Handler with Advanced Security Features
    
    Features:
    - Access & Refresh Token Management
    - Token Rotation & Revocation
    - Role-Based Claims
    - Security Validation
    - Audit Trail Integration
    """
    
    def __init__(self):
        # JWT Configuration
        self.secret_key = getattr(settings, 'JWT_SECRET_KEY', self._generate_secure_key())
        self.refresh_secret_key = getattr(settings, 'JWT_REFRESH_SECRET_KEY', self._generate_secure_key())
        self.algorithm = "HS256"
        
        # Token Expiry Settings (Production Values)
        self.access_token_expire_minutes = getattr(settings, 'JWT_ACCESS_TOKEN_EXPIRE_MINUTES', 15)
        self.refresh_token_expire_days = getattr(settings, 'JWT_REFRESH_TOKEN_EXPIRE_DAYS', 30)
        
        # Security Settings
        self.issuer = getattr(settings, 'JWT_ISSUER', 'ki-wissenssystem.enterprise')
        self.audience = getattr(settings, 'JWT_AUDIENCE', 'ki-wissenssystem-api')
        
        # Token Revocation Store (In production: Redis/Database)
        self._revoked_tokens = set()
        
        logger.info(f"JWT Handler initialized with {self.access_token_expire_minutes}min access token expiry")

    def _generate_secure_key(self) -> str:
        """Generate cryptographically secure key"""
        return secrets.token_urlsafe(64)

    def _generate_jti(self) -> str:
        """Generate unique JWT ID for revocation tracking"""
        return secrets.token_urlsafe(32)

    def create_token_pair(self, user: UserPayload) -> JWTTokens:
        """
        Create JWT access & refresh token pair
        
        Args:
            user: User payload with role and permissions
            
        Returns:
            JWTTokens with access and refresh tokens
        """
        now = datetime.now(timezone.utc)
        
        # Access Token Claims
        access_jti = self._generate_jti()
        access_claims = {
            "sub": user.user_id,
            "email": user.email,
            "role": user.role.value,
            "team_id": user.team_id,
            "permissions": user.permissions or [],
            "token_type": TokenType.ACCESS.value,
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(minutes=self.access_token_expire_minutes)).timestamp()),
            "jti": access_jti,
            "iss": self.issuer,
            "aud": self.audience
        }
        
        # Refresh Token Claims
        refresh_jti = self._generate_jti()
        refresh_claims = {
            "sub": user.user_id,
            "email": user.email,
            "role": user.role.value,
            "token_type": TokenType.REFRESH.value,
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(days=self.refresh_token_expire_days)).timestamp()),
            "jti": refresh_jti,
            "iss": self.issuer,
            "aud": self.audience
        }
        
        # Encode Tokens
        access_token = jwt.encode(access_claims, self.secret_key, algorithm=self.algorithm)
        refresh_token = jwt.encode(refresh_claims, self.refresh_secret_key, algorithm=self.algorithm)
        
        logger.info(f"Created token pair for user {user.user_id} with role {user.role.value}")
        
        return JWTTokens(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=self.access_token_expire_minutes * 60,
            refresh_expires_in=self.refresh_token_expire_days * 24 * 60 * 60
        )

    def verify_token(self, token: str, token_type: TokenType = TokenType.ACCESS) -> TokenClaims:
        """
        Verify and decode JWT token with comprehensive validation
        
        Args:
            token: JWT token string
            token_type: Expected token type (access/refresh)
            
        Returns:
            TokenClaims with validated user information
            
        Raises:
            jwt.ExpiredSignatureError: Token expired
            jwt.InvalidTokenError: Invalid token
            ValueError: Token revoked or wrong type
        """
        try:
            # Select appropriate secret key
            secret_key = self.secret_key if token_type == TokenType.ACCESS else self.refresh_secret_key
            
            # Decode token with full validation
            payload = jwt.decode(
                token,
                secret_key,
                algorithms=[self.algorithm],
                issuer=self.issuer,
                audience=self.audience,
                options={
                    "verify_signature": True,
                    "verify_exp": True,
                    "verify_iat": True,
                    "verify_iss": True,
                    "verify_aud": True
                }
            )
            
            # Validate token type
            if payload.get("token_type") != token_type.value:
                raise ValueError(f"Expected {token_type.value} token, got {payload.get('token_type')}")
            
            # Check if token is revoked
            jti = payload.get("jti")
            if jti in self._revoked_tokens:
                raise ValueError("Token has been revoked")
            
            # Create validated claims
            claims = TokenClaims(**payload)
            
            logger.debug(f"Successfully verified {token_type.value} token for user {claims.sub}")
            return claims
            
        except jwt.ExpiredSignatureError:
            logger.warning(f"Expired {token_type.value} token attempt")
            raise
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid {token_type.value} token: {e}")
            raise
        except Exception as e:
            logger.error(f"Token verification error: {e}")
            raise ValueError(f"Token verification failed: {e}")

    def refresh_access_token(self, refresh_token: str) -> JWTTokens:
        """
        Create new access token using valid refresh token
        
        Args:
            refresh_token: Valid refresh token
            
        Returns:
            New JWTTokens pair with rotated refresh token
        """
        # Verify refresh token
        refresh_claims = self.verify_token(refresh_token, TokenType.REFRESH)
        
        # Create user payload from refresh token
        user = UserPayload(
            user_id=refresh_claims.sub,
            email=refresh_claims.email,
            role=UserRole(refresh_claims.role),
            team_id=refresh_claims.team_id,
            permissions=refresh_claims.permissions
        )
        
        # Revoke old refresh token
        self.revoke_token(refresh_token)
        
        # Create new token pair
        new_tokens = self.create_token_pair(user)
        
        logger.info(f"Refreshed tokens for user {user.user_id}")
        return new_tokens

    def revoke_token(self, token: str) -> bool:
        """
        Revoke token by adding JTI to revocation list
        
        Args:
            token: Token to revoke
            
        Returns:
            True if successfully revoked
        """
        try:
            # Decode without verification to get JTI
            payload = jwt.decode(
                token, 
                options={"verify_signature": False, "verify_exp": False}
            )
            
            jti = payload.get("jti")
            if jti:
                self._revoked_tokens.add(jti)
                logger.info(f"Revoked token with JTI: {jti}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to revoke token: {e}")
            
        return False

    def create_api_key_token(self, user: UserPayload, expires_days: int = 365) -> str:
        """
        Create long-lived API key token for service-to-service authentication
        
        Args:
            user: User payload
            expires_days: Token validity in days
            
        Returns:
            Long-lived API key token
        """
        now = datetime.now(timezone.utc)
        
        claims = {
            "sub": user.user_id,
            "email": user.email,
            "role": user.role.value,
            "team_id": user.team_id,
            "permissions": user.permissions or [],
            "token_type": "api_key",
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(days=expires_days)).timestamp()),
            "jti": self._generate_jti(),
            "iss": self.issuer,
            "aud": self.audience
        }
        
        token = jwt.encode(claims, self.secret_key, algorithm=self.algorithm)
        logger.info(f"Created API key token for user {user.user_id}, expires in {expires_days} days")
        
        return token

    def get_user_from_token(self, token: str) -> UserPayload:
        """
        Extract user information from validated token
        
        Args:
            token: Valid JWT token
            
        Returns:
            UserPayload with user information
        """
        claims = self.verify_token(token, TokenType.ACCESS)
        
        return UserPayload(
            user_id=claims.sub,
            email=claims.email,
            role=UserRole(claims.role),
            team_id=claims.team_id,
            permissions=claims.permissions
        )

# ===================================================================
# SINGLETON INSTANCE
# ===================================================================

# Global JWT handler instance
jwt_handler = JWTHandler()

def get_jwt_handler() -> JWTHandler:
    """Get singleton JWT handler instance"""
    return jwt_handler 