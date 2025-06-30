# ===================================================================
# RATE LIMITER - ENTERPRISE EDITION
# Production-Ready Rate Limiting System
# 
# Features:
# - Redis-based Distributed Rate Limiting
# - Role-based Rate Limits
# - Request Throttling & Burst Protection
# - IP-based & User-based Limiting
# - Enterprise Monitoring & Metrics
# ===================================================================

import time
import asyncio
import logging
from typing import Dict, Optional, Tuple, Any
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
from collections import defaultdict
import redis.asyncio as redis
import json

from src.config.settings import settings
from .rbac import UserRole, RolePermissions

logger = logging.getLogger(__name__)

# ===================================================================
# RATE LIMIT TYPES & CONFIGURATIONS
# ===================================================================

class RateLimitType(str, Enum):
    """Rate limit types for different scenarios"""
    USER_API = "user_api"                 # Per-user API rate limits
    ADMIN_API = "admin_api"               # Admin API rate limits
    IP_GLOBAL = "ip_global"               # Global IP-based limits
    MODEL_ASSIGNMENT = "model_assignment" # Model assignment changes
    AUTH_LOGIN = "auth_login"             # Authentication attempts

@dataclass
class RateLimit:
    """Rate limit configuration"""
    requests: int                         # Number of requests allowed
    window_seconds: int                   # Time window in seconds
    burst_multiplier: float = 1.5         # Burst allowance multiplier
    block_duration_seconds: int = 300     # Block duration after limit exceeded

# Enterprise Rate Limit Configurations
RATE_LIMIT_CONFIGS = {
    RateLimitType.USER_API: {
        UserRole.PROXY_ADMIN: RateLimit(requests=10000, window_seconds=3600, burst_multiplier=2.0),
        UserRole.INTERNAL_USER: RateLimit(requests=5000, window_seconds=3600, burst_multiplier=1.5),
        UserRole.INTERNAL_USER_VIEWER: RateLimit(requests=2000, window_seconds=3600, burst_multiplier=1.2),
        UserRole.TEAM: RateLimit(requests=1000, window_seconds=3600, burst_multiplier=1.0),
        UserRole.CUSTOMER: RateLimit(requests=500, window_seconds=3600, burst_multiplier=1.0)
    },
    RateLimitType.ADMIN_API: {
        UserRole.PROXY_ADMIN: RateLimit(requests=100, window_seconds=300, burst_multiplier=1.5),
        UserRole.INTERNAL_USER: RateLimit(requests=50, window_seconds=300, burst_multiplier=1.2),
        "default": RateLimit(requests=10, window_seconds=300, burst_multiplier=1.0)
    },
    RateLimitType.MODEL_ASSIGNMENT: {
        UserRole.PROXY_ADMIN: RateLimit(requests=50, window_seconds=300, burst_multiplier=1.0),
        UserRole.INTERNAL_USER: RateLimit(requests=20, window_seconds=300, burst_multiplier=1.0),
        "default": RateLimit(requests=5, window_seconds=300, burst_multiplier=1.0)
    },
    RateLimitType.AUTH_LOGIN: {
        "default": RateLimit(requests=10, window_seconds=300, burst_multiplier=1.0, block_duration_seconds=900)
    },
    RateLimitType.IP_GLOBAL: {
        "default": RateLimit(requests=1000, window_seconds=300, burst_multiplier=2.0)
    }
}

# ===================================================================
# RATE LIMITER CLASS
# ===================================================================

class RateLimiter:
    """
    Enterprise Rate Limiter with Redis Backend
    
    Features:
    - Distributed rate limiting across multiple instances
    - Role-based rate limits with burst allowances
    - IP-based and user-based limiting
    - Automatic cleanup of expired entries
    - Enterprise monitoring and metrics
    """
    
    def __init__(self):
        # Redis configuration
        self.redis_host = getattr(settings, 'REDIS_HOST', 'localhost')
        self.redis_port = getattr(settings, 'REDIS_PORT', 6379)
        self.redis_db = getattr(settings, 'RATE_LIMIT_REDIS_DB', 2)
        self.redis_password = getattr(settings, 'REDIS_PASSWORD', None)
        
        # Rate limiter settings
        self.key_prefix = "rate_limit:"
        self.cleanup_interval = 300  # Cleanup expired keys every 5 minutes
        
        # In-memory fallback for when Redis is unavailable
        self._memory_store: Dict[str, Dict[str, Any]] = defaultdict(dict)
        self._use_redis = True
        
        # Redis connection pool
        self._redis_pool: Optional[redis.Redis] = None
        
        logger.info("Rate Limiter initialized with Redis backend")

    async def _get_redis(self) -> Optional[redis.Redis]:
        """Get Redis connection with connection pooling"""
        if not self._use_redis:
            return None
            
        if self._redis_pool is None:
            try:
                self._redis_pool = redis.Redis(
                    host=self.redis_host,
                    port=self.redis_port,
                    db=self.redis_db,
                    password=self.redis_password,
                    decode_responses=True,
                    max_connections=20
                )
                # Test connection
                await self._redis_pool.ping()
                logger.info("Redis connection established for rate limiting")
            except Exception as e:
                logger.warning(f"Redis connection failed, falling back to memory store: {e}")
                self._use_redis = False
                return None
                
        return self._redis_pool

    def _get_rate_limit_config(self, rate_type: RateLimitType, user_role: Optional[UserRole] = None) -> RateLimit:
        """Get rate limit configuration for type and role"""
        config_map = RATE_LIMIT_CONFIGS.get(rate_type, {})
        
        if user_role and user_role in config_map:
            return config_map[user_role]
        elif "default" in config_map:
            return config_map["default"]
        else:
            # Fallback default
            return RateLimit(requests=100, window_seconds=3600)

    def _generate_key(self, rate_type: RateLimitType, identifier: str) -> str:
        """Generate Redis key for rate limit tracking"""
        return f"{self.key_prefix}{rate_type.value}:{identifier}"

    async def _check_rate_limit_redis(
        self, 
        key: str, 
        rate_limit: RateLimit
    ) -> Tuple[bool, Dict[str, Any]]:
        """Check rate limit using Redis backend"""
        redis_client = await self._get_redis()
        if not redis_client:
            return await self._check_rate_limit_memory(key, rate_limit)
            
        try:
            current_time = int(time.time())
            window_start = current_time - rate_limit.window_seconds
            
            # Use Redis pipeline for atomic operations
            pipe = redis_client.pipeline()
            
            # Remove expired entries
            pipe.zremrangebyscore(key, 0, window_start)
            
            # Count current requests in window
            pipe.zcard(key)
            
            # Execute pipeline
            results = await pipe.execute()
            current_count = results[1]
            
            # Check if limit exceeded (including burst allowance)
            max_requests = int(rate_limit.requests * rate_limit.burst_multiplier)
            allowed = current_count < max_requests
            
            if allowed:
                # Add current request
                await redis_client.zadd(key, {str(current_time): current_time})
                await redis_client.expire(key, rate_limit.window_seconds + 60)  # Extra TTL buffer
            
            # Calculate reset time and remaining requests
            remaining = max(0, max_requests - current_count - (1 if allowed else 0))
            reset_time = current_time + rate_limit.window_seconds
            
            return allowed, {
                "allowed": allowed,
                "limit": max_requests,
                "remaining": remaining,
                "reset_time": reset_time,
                "current_count": current_count,
                "window_seconds": rate_limit.window_seconds
            }
            
        except Exception as e:
            logger.error(f"Redis rate limit check failed: {e}")
            return await self._check_rate_limit_memory(key, rate_limit)

    async def _check_rate_limit_memory(
        self, 
        key: str, 
        rate_limit: RateLimit
    ) -> Tuple[bool, Dict[str, Any]]:
        """Fallback in-memory rate limit checking"""
        current_time = time.time()
        window_start = current_time - rate_limit.window_seconds
        
        # Get or create entry
        if key not in self._memory_store:
            self._memory_store[key] = {"requests": [], "blocked_until": 0}
        
        entry = self._memory_store[key]
        
        # Check if currently blocked
        if entry["blocked_until"] > current_time:
            return False, {
                "allowed": False,
                "limit": rate_limit.requests,
                "remaining": 0,
                "reset_time": int(entry["blocked_until"]),
                "current_count": len(entry["requests"]),
                "window_seconds": rate_limit.window_seconds
            }
        
        # Remove expired requests
        entry["requests"] = [req_time for req_time in entry["requests"] if req_time > window_start]
        
        # Check limit
        max_requests = int(rate_limit.requests * rate_limit.burst_multiplier)
        current_count = len(entry["requests"])
        allowed = current_count < max_requests
        
        if allowed:
            entry["requests"].append(current_time)
        else:
            # Block for the configured duration
            entry["blocked_until"] = current_time + rate_limit.block_duration_seconds
        
        remaining = max(0, max_requests - current_count - (1 if allowed else 0))
        reset_time = int(current_time + rate_limit.window_seconds)
        
        return allowed, {
            "allowed": allowed,
            "limit": max_requests,
            "remaining": remaining,
            "reset_time": reset_time,
            "current_count": current_count,
            "window_seconds": rate_limit.window_seconds
        }

    async def check_rate_limit(
        self,
        rate_type: RateLimitType,
        identifier: str,
        user_role: Optional[UserRole] = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if request is within rate limits
        
        Args:
            rate_type: Type of rate limit to check
            identifier: Unique identifier (user_id, ip_address, etc.)
            user_role: User role for role-based limits
            
        Returns:
            Tuple of (allowed: bool, metadata: dict)
        """
        rate_limit = self._get_rate_limit_config(rate_type, user_role)
        key = self._generate_key(rate_type, identifier)
        
        allowed, metadata = await self._check_rate_limit_redis(key, rate_limit)
        
        # Log rate limit check
        logger.debug(
            f"Rate limit check: type={rate_type.value}, id={identifier}, "
            f"role={user_role.value if user_role else 'none'}, allowed={allowed}, "
            f"remaining={metadata.get('remaining', 0)}"
        )
        
        return allowed, metadata

    async def is_blocked(self, rate_type: RateLimitType, identifier: str) -> bool:
        """Check if identifier is currently blocked"""
        allowed, _ = await self.check_rate_limit(rate_type, identifier)
        return not allowed

    async def reset_rate_limit(self, rate_type: RateLimitType, identifier: str) -> bool:
        """Reset rate limit for identifier (admin function)"""
        key = self._generate_key(rate_type, identifier)
        
        redis_client = await self._get_redis()
        if redis_client:
            try:
                await redis_client.delete(key)
                logger.info(f"Reset rate limit for {rate_type.value}:{identifier}")
                return True
            except Exception as e:
                logger.error(f"Failed to reset rate limit in Redis: {e}")
        
        # Fallback to memory store
        if key in self._memory_store:
            del self._memory_store[key]
            logger.info(f"Reset rate limit in memory for {rate_type.value}:{identifier}")
            return True
            
        return False

    async def get_rate_limit_status(
        self, 
        rate_type: RateLimitType, 
        identifier: str,
        user_role: Optional[UserRole] = None
    ) -> Dict[str, Any]:
        """Get current rate limit status without incrementing counter"""
        rate_limit = self._get_rate_limit_config(rate_type, user_role)
        key = self._generate_key(rate_type, identifier)
        
        redis_client = await self._get_redis()
        if redis_client:
            try:
                current_time = int(time.time())
                window_start = current_time - rate_limit.window_seconds
                
                # Count current requests without modifying
                current_count = await redis_client.zcount(key, window_start, current_time)
                max_requests = int(rate_limit.requests * rate_limit.burst_multiplier)
                
                return {
                    "limit": max_requests,
                    "remaining": max(0, max_requests - current_count),
                    "reset_time": current_time + rate_limit.window_seconds,
                    "current_count": current_count,
                    "window_seconds": rate_limit.window_seconds
                }
            except Exception as e:
                logger.error(f"Failed to get rate limit status from Redis: {e}")
        
        # Fallback to memory store
        if key in self._memory_store:
            entry = self._memory_store[key]
            current_time = time.time()
            window_start = current_time - rate_limit.window_seconds
            
            # Count valid requests
            valid_requests = [req for req in entry["requests"] if req > window_start]
            max_requests = int(rate_limit.requests * rate_limit.burst_multiplier)
            
            return {
                "limit": max_requests,
                "remaining": max(0, max_requests - len(valid_requests)),
                "reset_time": int(current_time + rate_limit.window_seconds),
                "current_count": len(valid_requests),
                "window_seconds": rate_limit.window_seconds
            }
        
        # No data found
        max_requests = int(rate_limit.requests * rate_limit.burst_multiplier)
        return {
            "limit": max_requests,
            "remaining": max_requests,
            "reset_time": int(time.time() + rate_limit.window_seconds),
            "current_count": 0,
            "window_seconds": rate_limit.window_seconds
        }

    async def cleanup_expired_entries(self):
        """Cleanup expired rate limit entries (maintenance task)"""
        if not self._use_redis:
            # Cleanup memory store
            current_time = time.time()
            expired_keys = []
            
            for key, entry in self._memory_store.items():
                if entry.get("blocked_until", 0) < current_time and not entry.get("requests"):
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self._memory_store[key]
                
            logger.debug(f"Cleaned up {len(expired_keys)} expired rate limit entries from memory")
        
        logger.debug("Rate limit cleanup completed")

# ===================================================================
# SINGLETON INSTANCE
# ===================================================================

# Global rate limiter instance
rate_limiter = RateLimiter()

def get_rate_limiter() -> RateLimiter:
    """Get singleton rate limiter instance"""
    return rate_limiter 