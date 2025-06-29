# ===================================================================
# AUDIT LOGGER - ENTERPRISE EDITION
# Production-Ready Audit Logging System
# 
# Features:
# - PostgreSQL-based Audit Trail
# - Comprehensive Event Tracking
# - Real-time Audit Stream
# - Compliance & Security Monitoring
# - Enterprise Retention Policies
# ===================================================================

import json
import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List, Union
from enum import Enum
from dataclasses import dataclass, asdict
from uuid import uuid4
import uuid
import asyncpg
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy import Column, String, DateTime, JSON, Integer, Boolean, MetaData, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID

from src.config.settings import settings
from .rbac import UserRole

logger = logging.getLogger(__name__)

# ===================================================================
# AUDIT EVENT TYPES & DEFINITIONS
# ===================================================================

class AuditEventType(str, Enum):
    """Comprehensive audit event types for enterprise compliance"""
    
    # Authentication & Authorization Events
    AUTH_LOGIN_SUCCESS = "auth.login.success"
    AUTH_LOGIN_FAILURE = "auth.login.failure"
    AUTH_LOGOUT = "auth.logout"
    AUTH_TOKEN_CREATED = "auth.token.created"
    AUTH_TOKEN_REFRESHED = "auth.token.refreshed"
    AUTH_TOKEN_REVOKED = "auth.token.revoked"
    AUTH_PERMISSION_DENIED = "auth.permission.denied"
    AUTH_ROLE_CHANGED = "auth.role.changed"
    
    # Model Management Events
    MODEL_ASSIGNMENT_CHANGED = "model.assignment.changed"
    MODEL_ASSIGNMENT_VIEWED = "model.assignment.viewed"
    MODEL_PERFORMANCE_VIEWED = "model.performance.viewed"
    MODEL_CONFIGURATION_UPDATED = "model.config.updated"
    
    # System Administration Events
    SYSTEM_CONFIG_CHANGED = "system.config.changed"
    SYSTEM_HEALTH_CHECKED = "system.health.checked"
    SYSTEM_MAINTENANCE_START = "system.maintenance.start"
    SYSTEM_MAINTENANCE_END = "system.maintenance.end"
    
    # API Access Events
    API_REQUEST_SUCCESS = "api.request.success"
    API_REQUEST_FAILURE = "api.request.failure"
    API_RATE_LIMIT_EXCEEDED = "api.rate_limit.exceeded"
    API_UNAUTHORIZED_ACCESS = "api.unauthorized.access"
    
    # User Management Events
    USER_CREATED = "user.created"
    USER_UPDATED = "user.updated"
    USER_DELETED = "user.deleted"
    USER_ROLE_ASSIGNED = "user.role.assigned"
    USER_PERMISSIONS_CHANGED = "user.permissions.changed"
    
    # Data & Document Events
    DOCUMENT_UPLOADED = "document.uploaded"
    DOCUMENT_PROCESSED = "document.processed"
    DOCUMENT_DELETED = "document.deleted"
    QUERY_EXECUTED = "query.executed"
    
    # Security Events
    SECURITY_VIOLATION = "security.violation"
    SECURITY_THREAT_DETECTED = "security.threat.detected"
    SECURITY_POLICY_VIOLATION = "security.policy.violation"
    
    # Compliance Events
    COMPLIANCE_REPORT_GENERATED = "compliance.report.generated"
    COMPLIANCE_AUDIT_STARTED = "compliance.audit.started"
    COMPLIANCE_AUDIT_COMPLETED = "compliance.audit.completed"

class AuditSeverity(str, Enum):
    """Audit event severity levels"""
    CRITICAL = "critical"      # Security breaches, system failures
    HIGH = "high"             # Important security events, admin actions
    MEDIUM = "medium"         # Regular admin operations, configuration changes
    LOW = "low"               # Normal user operations, read operations
    INFO = "info"             # Informational events, system status

@dataclass
class AuditEvent:
    """Comprehensive audit event data structure"""
    # Core event information
    event_id: str
    event_type: AuditEventType
    severity: AuditSeverity
    timestamp: datetime
    
    # User & Session Information
    user_id: Optional[str] = None
    user_email: Optional[str] = None
    user_role: Optional[UserRole] = None
    session_id: Optional[str] = None
    
    # Request Information
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    request_id: Optional[str] = None
    endpoint: Optional[str] = None
    http_method: Optional[str] = None
    
    # Event Details
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    action: Optional[str] = None
    outcome: Optional[str] = None
    
    # Additional Context
    details: Dict[str, Any] = None
    error_message: Optional[str] = None
    stack_trace: Optional[str] = None
    
    # Metadata
    source_system: str = "ki-wissenssystem"
    compliance_tags: List[str] = None

# ===================================================================
# DATABASE MODEL
# ===================================================================

Base = declarative_base()

class AuditLogEntry(Base):
    """PostgreSQL audit log table schema"""
    __tablename__ = "audit_logs"
    
    # Primary key and identification
    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4)
    
    # Event classification
    event_type = Column(String(100), nullable=False, index=True)
    severity = Column(String(20), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # User context
    user_id = Column(String(100), index=True)
    user_email = Column(String(255), index=True)
    user_role = Column(String(50), index=True)
    session_id = Column(String(100), index=True)
    
    # Request context
    ip_address = Column(String(45), index=True)  # Support IPv6
    user_agent = Column(String(500))
    request_id = Column(String(100), index=True)
    endpoint = Column(String(200), index=True)
    http_method = Column(String(10))
    
    # Resource context
    resource_type = Column(String(100), index=True)
    resource_id = Column(String(100), index=True)
    action = Column(String(100), index=True)
    outcome = Column(String(50), index=True)
    
    # Event details (JSON)
    details = Column(JSON)
    error_message = Column(String(1000))
    stack_trace = Column(String(5000))
    
    # Metadata
    source_system = Column(String(100), nullable=False, default="ki-wissenssystem")
    compliance_tags = Column(JSON)

# ===================================================================
# AUDIT LOGGER CLASS
# ===================================================================

class AuditLogger:
    """
    Enterprise Audit Logger with PostgreSQL Backend
    
    Features:
    - Comprehensive audit event tracking
    - PostgreSQL-based persistent storage
    - Real-time audit streaming
    - Compliance reporting capabilities
    - Enterprise retention policies
    """
    
    def __init__(self):
        # Database configuration
        self.database_url = getattr(settings, 'DATABASE_URL', 'postgresql://localhost/ki_wissenssystem')
        self.max_retries = 3
        self.retry_delay = 1.0
        
        # Audit configuration
        self.batch_size = 100
        self.batch_timeout = 30  # seconds
        self.retention_days = getattr(settings, 'AUDIT_RETENTION_DAYS', 2555)  # 7 years default
        
        # In-memory event buffer for batching
        self._event_buffer: List[AuditEvent] = []
        self._buffer_lock = asyncio.Lock()
        
        # Database engine (lazy initialization)
        self._engine = None
        self._initialized = False
        
        logger.info("Audit Logger initialized with PostgreSQL backend")

    async def _get_engine(self):
        """Get or create async database engine"""
        if self._engine is None:
            try:
                # Convert sync URL to async if needed
                if self.database_url.startswith('postgresql://'):
                    async_url = self.database_url.replace('postgresql://', 'postgresql+asyncpg://', 1)
                else:
                    async_url = self.database_url
                    
                self._engine = create_async_engine(
                    async_url,
                    echo=False,
                    pool_size=5,
                    max_overflow=10,
                    pool_pre_ping=True
                )
                
                logger.info("Audit Logger database engine created")
            except Exception as e:
                logger.error(f"Failed to create audit database engine: {e}")
                raise
                
        return self._engine

    async def _ensure_table_exists(self):
        """Ensure audit log table exists"""
        if self._initialized:
            return
            
        try:
            engine = await self._get_engine()
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            
            self._initialized = True
            logger.info("Audit log table initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize audit log table: {e}")
            # Don't raise - continue with in-memory logging
            pass

    async def log_event(self, event: AuditEvent) -> bool:
        """
        Log audit event to database
        
        Args:
            event: AuditEvent to log
            
        Returns:
            True if successfully logged
        """
        try:
            await self._ensure_table_exists()
            
            # Add to buffer for batching
            async with self._buffer_lock:
                self._event_buffer.append(event)
                
                # Flush buffer if it's full
                if len(self._event_buffer) >= self.batch_size:
                    await self._flush_buffer()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to log audit event: {e}")
            return False

    async def _flush_buffer(self):
        """Flush event buffer to database"""
        if not self._event_buffer:
            return
            
        events_to_flush = self._event_buffer.copy()
        self._event_buffer.clear()
        
        try:
            engine = await self._get_engine()
            async with engine.begin() as conn:
                # Convert events to database records
                records = []
                for event in events_to_flush:
                    record = {
                        'event_id': uuid.UUID(event.event_id) if isinstance(event.event_id, str) else event.event_id,
                        'event_type': event.event_type.value,
                        'severity': event.severity.value,
                        'timestamp': event.timestamp,
                        'user_id': event.user_id,
                        'user_email': event.user_email,
                        'user_role': event.user_role.value if event.user_role else None,
                        'session_id': event.session_id,
                        'ip_address': event.ip_address,
                        'user_agent': event.user_agent,
                        'request_id': event.request_id,
                        'endpoint': event.endpoint,
                        'http_method': event.http_method,
                        'resource_type': event.resource_type,
                        'resource_id': event.resource_id,
                        'action': event.action,
                        'outcome': event.outcome,
                        'details': event.details,
                        'error_message': event.error_message,
                        'stack_trace': event.stack_trace,
                        'source_system': event.source_system,
                        'compliance_tags': event.compliance_tags
                    }
                    records.append(record)
                
                # Bulk insert
                await conn.execute(AuditLogEntry.__table__.insert(), records)
                
            logger.debug(f"Flushed {len(events_to_flush)} audit events to database")
            
        except Exception as e:
            logger.error(f"Failed to flush audit events to database: {e}")
            # Re-add events to buffer for retry
            async with self._buffer_lock:
                self._event_buffer = events_to_flush + self._event_buffer

    def create_event(
        self,
        event_type: AuditEventType,
        severity: AuditSeverity = AuditSeverity.INFO,
        user_id: Optional[str] = None,
        user_email: Optional[str] = None,
        user_role: Optional[UserRole] = None,
        ip_address: Optional[str] = None,
        endpoint: Optional[str] = None,
        action: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> AuditEvent:
        """
        Create audit event with standard fields
        
        Args:
            event_type: Type of audit event
            severity: Event severity level
            user_id: User identifier
            user_email: User email address
            user_role: User role
            ip_address: Client IP address
            endpoint: API endpoint
            action: Action performed
            resource_type: Type of resource affected
            resource_id: Resource identifier
            details: Additional event details
            **kwargs: Additional fields
            
        Returns:
            AuditEvent instance
        """
        event = AuditEvent(
            event_id=str(uuid4()),
            event_type=event_type,
            severity=severity,
            timestamp=datetime.now(timezone.utc),
            user_id=user_id,
            user_email=user_email,
            user_role=user_role,
            ip_address=ip_address,
            endpoint=endpoint,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details or {},
            **kwargs
        )
        
        return event

    async def log_authentication_event(
        self,
        event_type: AuditEventType,
        user_id: str,
        user_email: str,
        user_role: UserRole,
        ip_address: str,
        success: bool,
        details: Optional[Dict[str, Any]] = None
    ):
        """Log authentication-related events"""
        severity = AuditSeverity.HIGH if not success else AuditSeverity.MEDIUM
        
        event = self.create_event(
            event_type=event_type,
            severity=severity,
            user_id=user_id,
            user_email=user_email,
            user_role=user_role,
            ip_address=ip_address,
            action="authenticate",
            outcome="success" if success else "failure",
            details=details
        )
        
        await self.log_event(event)

    async def log_model_management_event(
        self,
        event_type: AuditEventType,
        user_id: str,
        user_role: UserRole,
        action: str,
        task_type: Optional[str] = None,
        profile: Optional[str] = None,
        old_model: Optional[str] = None,
        new_model: Optional[str] = None,
        ip_address: Optional[str] = None
    ):
        """Log model management events"""
        details = {}
        if task_type:
            details["task_type"] = task_type
        if profile:
            details["profile"] = profile
        if old_model:
            details["old_model"] = old_model
        if new_model:
            details["new_model"] = new_model
            
        event = self.create_event(
            event_type=event_type,
            severity=AuditSeverity.HIGH,
            user_id=user_id,
            user_role=user_role,
            ip_address=ip_address,
            action=action,
            resource_type="model_assignment",
            resource_id=f"{task_type}_{profile}" if task_type and profile else None,
            details=details
        )
        
        await self.log_event(event)

    async def log_api_request(
        self,
        user_id: Optional[str],
        user_role: Optional[UserRole],
        endpoint: str,
        method: str,
        ip_address: str,
        status_code: int,
        response_time_ms: float,
        request_id: Optional[str] = None
    ):
        """Log API request events"""
        success = 200 <= status_code < 400
        severity = AuditSeverity.LOW if success else AuditSeverity.MEDIUM
        
        event = self.create_event(
            event_type=AuditEventType.API_REQUEST_SUCCESS if success else AuditEventType.API_REQUEST_FAILURE,
            severity=severity,
            user_id=user_id,
            user_role=user_role,
            ip_address=ip_address,
            endpoint=endpoint,
            http_method=method,
            request_id=request_id,
            action="api_request",
            outcome="success" if success else "failure",
            details={
                "status_code": status_code,
                "response_time_ms": response_time_ms
            }
        )
        
        await self.log_event(event)

    async def get_audit_events(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        user_id: Optional[str] = None,
        event_type: Optional[AuditEventType] = None,
        severity: Optional[AuditSeverity] = None,
        limit: int = 1000,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Query audit events with filters
        
        Args:
            start_date: Filter events after this date
            end_date: Filter events before this date
            user_id: Filter by user ID
            event_type: Filter by event type
            severity: Filter by severity
            limit: Maximum number of events to return
            offset: Number of events to skip
            
        Returns:
            List of audit event dictionaries
        """
        try:
            await self._ensure_table_exists()
            engine = await self._get_engine()
            
            # Build query
            query = "SELECT * FROM audit_logs WHERE 1=1"
            params = {}
            
            if start_date:
                query += " AND timestamp >= :start_date"
                params["start_date"] = start_date
                
            if end_date:
                query += " AND timestamp <= :end_date"
                params["end_date"] = end_date
                
            if user_id:
                query += " AND user_id = :user_id"
                params["user_id"] = user_id
                
            if event_type:
                query += " AND event_type = :event_type"
                params["event_type"] = event_type.value
                
            if severity:
                query += " AND severity = :severity"
                params["severity"] = severity.value
            
            query += " ORDER BY timestamp DESC LIMIT :limit OFFSET :offset"
            params["limit"] = limit
            params["offset"] = offset
            
            async with engine.begin() as conn:
                result = await conn.execute(query, params)
                rows = result.fetchall()
                
                # Convert to dictionaries
                events = []
                for row in rows:
                    event_dict = dict(row)
                    # Convert UUID to string for JSON serialization
                    if 'event_id' in event_dict and event_dict['event_id']:
                        event_dict['event_id'] = str(event_dict['event_id'])
                    events.append(event_dict)
                
                return events
                
        except Exception as e:
            logger.error(f"Failed to query audit events: {e}")
            return []

    async def cleanup_old_events(self):
        """Clean up audit events older than retention period"""
        try:
            await self._ensure_table_exists()
            engine = await self._get_engine()
            
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=self.retention_days)
            
            async with engine.begin() as conn:
                result = await conn.execute(
                    "DELETE FROM audit_logs WHERE timestamp < :cutoff_date",
                    {"cutoff_date": cutoff_date}
                )
                
                deleted_count = result.rowcount
                logger.info(f"Deleted {deleted_count} old audit events (older than {self.retention_days} days)")
                
        except Exception as e:
            logger.error(f"Failed to cleanup old audit events: {e}")

# ===================================================================
# SINGLETON INSTANCE & CONVENIENCE FUNCTIONS
# ===================================================================

# Global audit logger instance
audit_logger = AuditLogger()

def get_audit_logger() -> AuditLogger:
    """Get singleton audit logger instance"""
    return audit_logger

# Convenience functions for common audit events
async def audit_login_success(user_id: str, user_email: str, user_role: UserRole, ip_address: str):
    """Audit successful login"""
    await audit_logger.log_authentication_event(
        AuditEventType.AUTH_LOGIN_SUCCESS, user_id, user_email, user_role, ip_address, True
    )

async def audit_login_failure(user_email: str, ip_address: str, reason: str):
    """Audit failed login attempt"""
    await audit_logger.log_authentication_event(
        AuditEventType.AUTH_LOGIN_FAILURE, None, user_email, None, ip_address, False,
        {"failure_reason": reason}
    )

async def audit_model_assignment_change(
    user_id: str, 
    user_role: UserRole, 
    task_type: str, 
    profile: str, 
    old_model: str, 
    new_model: str,
    ip_address: str
):
    """Audit model assignment change"""
    await audit_logger.log_model_management_event(
        AuditEventType.MODEL_ASSIGNMENT_CHANGED, user_id, user_role, "change",
        task_type, profile, old_model, new_model, ip_address
    ) 