# ===================================================================
# RBAC - ROLE-BASED ACCESS CONTROL
# Enterprise Permission Management System
# 
# Features:
# - LiteLLM Enterprise Role Mapping
# - Granular Permission System
# - Resource-Based Access Control
# - Audit Trail Integration
# ===================================================================

from enum import Enum
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

# ===================================================================
# PERMISSION DEFINITIONS
# ===================================================================

class Permission(str, Enum):
    """Granular permission system for enterprise features"""
    
    # Model Management Permissions
    MODEL_READ = "model:read"                     # View model assignments
    MODEL_WRITE = "model:write"                   # Modify model assignments
    MODEL_DELETE = "model:delete"                 # Delete model configurations
    MODEL_ADMIN = "model:admin"                   # Full model management
    MODEL_ASSIGNMENT_READ = "model_assignment:read"     # Read specific assignments
    MODEL_ASSIGNMENT_WRITE = "model_assignment:write"   # Modify specific assignments
    MODEL_PERFORMANCE_READ = "model_performance:read"   # View performance metrics
    MODEL_HEALTH_READ = "model_health:read"             # View health status
    
    # System Administration
    SYSTEM_READ = "system:read"                   # View system status
    SYSTEM_WRITE = "system:write"                 # Modify system settings
    SYSTEM_ADMIN = "system:admin"                 # Full system administration
    SYSTEM_HEALTH_READ = "system_health:read"    # View system health
    SYSTEM_CONFIG_READ = "system_config:read"    # View system configuration
    SYSTEM_CONFIG_WRITE = "system_config:write"  # Modify system configuration
    
    # User Management
    USER_READ = "user:read"                       # View user information
    USER_WRITE = "user:write"                     # Modify user settings
    USER_DELETE = "user:delete"                   # Delete users
    USER_ADMIN = "user:admin"                     # Full user management
    
    # API Access
    API_READ = "api:read"                         # Read-only API access
    API_WRITE = "api:write"                       # Read-write API access
    API_ADMIN = "api:admin"                       # Administrative API access
    
    # Monitoring & Analytics
    MONITOR_READ = "monitor:read"                 # View monitoring data
    MONITOR_WRITE = "monitor:write"               # Configure monitoring
    MONITOR_ADMIN = "monitor:admin"               # Full monitoring access
    
    # Audit & Compliance
    AUDIT_READ = "audit:read"                     # View audit logs
    AUDIT_WRITE = "audit:write"                   # Create audit entries
    AUDIT_ADMIN = "audit:admin"                   # Full audit management
    
    # Team Management
    TEAM_READ = "team:read"                       # View team information
    TEAM_WRITE = "team:write"                     # Modify team settings
    TEAM_DELETE = "team:delete"                   # Delete teams
    TEAM_ADMIN = "team:admin"                     # Full team management

# ===================================================================
# ROLE DEFINITIONS
# ===================================================================

class UserRole(str, Enum):
    """Enterprise User Roles based on LiteLLM Enterprise Documentation"""
    PROXY_ADMIN = "proxy_admin"                    # Full system access
    INTERNAL_USER = "internal_user"               # API access + limited admin  
    INTERNAL_USER_VIEWER = "internal_user_viewer" # Read-only access
    TEAM = "team"                                 # Team-scoped access
    CUSTOMER = "customer"                         # External user access

@dataclass
class RoleDefinition:
    """Complete role definition with permissions and metadata"""
    role: UserRole
    name: str
    description: str
    permissions: Set[Permission]
    is_admin: bool
    max_rate_limit: int
    can_impersonate: bool = False
    resource_restrictions: Optional[Dict[str, List[str]]] = None

# ===================================================================
# ROLE PERMISSION MAPPING
# ===================================================================

class RolePermissions:
    """Enterprise Role Permission Management"""
    
    # Role definitions with granular permissions
    ROLE_DEFINITIONS: Dict[UserRole, RoleDefinition] = {
        
        UserRole.PROXY_ADMIN: RoleDefinition(
            role=UserRole.PROXY_ADMIN,
            name="Proxy Administrator",
            description="Full system access with all administrative privileges",
            permissions={
                # Full access to all resources
                Permission.MODEL_ADMIN,
                Permission.SYSTEM_ADMIN,
                Permission.USER_ADMIN,
                Permission.API_ADMIN,
                Permission.MONITOR_WRITE,
                Permission.AUDIT_WRITE,
                Permission.TEAM_ADMIN,
                # Individual permissions for granular control
                Permission.MODEL_READ, Permission.MODEL_WRITE, Permission.MODEL_DELETE,
                Permission.MODEL_ASSIGNMENT_READ, Permission.MODEL_ASSIGNMENT_WRITE,
                Permission.MODEL_PERFORMANCE_READ, Permission.MODEL_HEALTH_READ,
                Permission.SYSTEM_READ, Permission.SYSTEM_WRITE,
                Permission.SYSTEM_HEALTH_READ, Permission.SYSTEM_CONFIG_READ, Permission.SYSTEM_CONFIG_WRITE,
                Permission.USER_READ, Permission.USER_WRITE, Permission.USER_DELETE,
                Permission.API_READ, Permission.API_WRITE,
                Permission.MONITOR_READ,
                Permission.AUDIT_READ,
                Permission.TEAM_READ, Permission.TEAM_WRITE
            },
            is_admin=True,
            max_rate_limit=10000,
            can_impersonate=True
        ),
        
        UserRole.INTERNAL_USER: RoleDefinition(
            role=UserRole.INTERNAL_USER,
            name="Internal User",
            description="API access with limited administrative capabilities",
            permissions={
                Permission.MODEL_READ, Permission.MODEL_WRITE,
                Permission.MODEL_ASSIGNMENT_READ, Permission.MODEL_ASSIGNMENT_WRITE,
                Permission.MODEL_PERFORMANCE_READ, Permission.MODEL_HEALTH_READ,
                Permission.SYSTEM_READ, Permission.SYSTEM_HEALTH_READ,
                Permission.API_READ, Permission.API_WRITE,
                Permission.MONITOR_READ,
                Permission.AUDIT_READ,
                Permission.TEAM_READ
            },
            is_admin=False,
            max_rate_limit=5000,
            can_impersonate=False
        ),
        
        UserRole.INTERNAL_USER_VIEWER: RoleDefinition(
            role=UserRole.INTERNAL_USER_VIEWER,
            name="Internal User Viewer", 
            description="Read-only access to internal systems",
            permissions={
                Permission.MODEL_READ,
                Permission.MODEL_ASSIGNMENT_READ,
                Permission.MODEL_PERFORMANCE_READ, Permission.MODEL_HEALTH_READ,
                Permission.SYSTEM_READ, Permission.SYSTEM_HEALTH_READ,
                Permission.API_READ,
                Permission.MONITOR_READ,
                Permission.AUDIT_READ,
                Permission.TEAM_READ
            },
            is_admin=False,
            max_rate_limit=2000,
            can_impersonate=False
        ),
        
        UserRole.TEAM: RoleDefinition(
            role=UserRole.TEAM,
            name="Team Member",
            description="Team-scoped access with limited permissions",
            permissions={
                Permission.MODEL_READ,
                Permission.MODEL_ASSIGNMENT_READ,
                Permission.MODEL_PERFORMANCE_READ,
                Permission.API_READ, Permission.API_WRITE,
                Permission.MONITOR_READ,
                Permission.TEAM_READ
            },
            is_admin=False,
            max_rate_limit=1000,
            can_impersonate=False
        ),
        
        UserRole.CUSTOMER: RoleDefinition(
            role=UserRole.CUSTOMER,
            name="Customer",
            description="External user with basic API access",
            permissions={
                Permission.API_READ,
                Permission.MONITOR_READ
            },
            is_admin=False,
            max_rate_limit=500,
            can_impersonate=False
        )
    }
    
    @classmethod
    def get_permissions(cls, role: UserRole) -> Set[Permission]:
        """Get all permissions for a role"""
        role_def = cls.ROLE_DEFINITIONS.get(role)
        return role_def.permissions if role_def else set()
    
    @classmethod
    def has_permission(cls, role: UserRole, permission: Permission) -> bool:
        """Check if role has specific permission"""
        permissions = cls.get_permissions(role)
        return permission in permissions
    
    @classmethod
    def has_any_permission(cls, role: UserRole, permissions: List[Permission]) -> bool:
        """Check if role has any of the specified permissions"""
        user_permissions = cls.get_permissions(role)
        return any(perm in user_permissions for perm in permissions)
    
    @classmethod
    def has_all_permissions(cls, role: UserRole, permissions: List[Permission]) -> bool:
        """Check if role has all specified permissions"""
        user_permissions = cls.get_permissions(role)
        return all(perm in user_permissions for perm in permissions)
    
    @classmethod
    def is_admin(cls, role: UserRole) -> bool:
        """Check if role has admin privileges"""
        role_def = cls.ROLE_DEFINITIONS.get(role)
        return role_def.is_admin if role_def else False
    
    @classmethod
    def get_max_rate_limit(cls, role: UserRole) -> int:
        """Get maximum rate limit for role"""
        role_def = cls.ROLE_DEFINITIONS.get(role)
        return role_def.max_rate_limit if role_def else 100
    
    @classmethod
    def can_impersonate(cls, role: UserRole, target_role: UserRole) -> bool:
        """Check if role can impersonate another role"""
        role_def = cls.ROLE_DEFINITIONS.get(role)
        if not role_def or not role_def.can_impersonate:
            return False
        
        # Only admins can impersonate other roles
        if not role_def.is_admin:
            return False
        
        # Cannot impersonate same or higher privilege level
        role_hierarchy = [UserRole.PROXY_ADMIN, UserRole.INTERNAL_USER, 
                         UserRole.INTERNAL_USER_VIEWER, UserRole.TEAM, UserRole.CUSTOMER]
        
        current_level = role_hierarchy.index(role) if role in role_hierarchy else len(role_hierarchy)
        target_level = role_hierarchy.index(target_role) if target_role in role_hierarchy else len(role_hierarchy)
        
        return current_level < target_level

# ===================================================================
# RESOURCE-BASED ACCESS CONTROL
# ===================================================================

class ResourceType(str, Enum):
    """Resource types for fine-grained access control"""
    MODEL_ASSIGNMENT = "model_assignment"
    MODEL_PERFORMANCE = "model_performance" 
    MODEL_HEALTH = "model_health"
    SYSTEM_HEALTH = "system_health"
    SYSTEM_CONFIG = "system_config"
    USER_PROFILE = "user_profile"
    TEAM_CONFIG = "team_config"
    AUDIT_LOG = "audit_log"

class ResourceAccess:
    """Resource-based access control for fine-grained permissions"""
    
    # Model Management Resources with granular permissions
    MODEL_MANAGEMENT_RESOURCES = {
        "assignments": {
            "read": [Permission.MODEL_READ, Permission.MODEL_ASSIGNMENT_READ],
            "write": [Permission.MODEL_WRITE, Permission.MODEL_ASSIGNMENT_WRITE, Permission.MODEL_ADMIN],
            "delete": [Permission.MODEL_DELETE, Permission.MODEL_ADMIN]
        },
        "available": {
            "read": [Permission.MODEL_READ, Permission.API_READ]
        },
        "performance": {
            "read": [Permission.MODEL_PERFORMANCE_READ, Permission.MONITOR_READ]
        },
        "health": {
            "read": [Permission.MODEL_HEALTH_READ, Permission.SYSTEM_HEALTH_READ]
        }
    }
    
    # System Administration Resources
    SYSTEM_RESOURCES = {
        "health": {
            "read": [Permission.SYSTEM_HEALTH_READ, Permission.SYSTEM_READ]
        },
        "metrics": {
            "read": [Permission.SYSTEM_READ, Permission.MONITOR_READ]
        },
        "config": {
            "read": [Permission.SYSTEM_CONFIG_READ, Permission.SYSTEM_READ],
            "write": [Permission.SYSTEM_CONFIG_WRITE, Permission.SYSTEM_ADMIN]
        }
    }
    
    @classmethod
    def can_access_resource(
        cls,
        user_role: UserRole,
        resource_type: str,
        resource_name: str,
        action: str = "read"
    ) -> bool:
        """
        Check if user can access specific resource
        
        Args:
            user_role: User's role
            resource_type: Type of resource (model, system, etc.)
            resource_name: Specific resource name
            action: Action being performed (read, write, delete)
            
        Returns:
            True if access is allowed
        """
        # Map resource type to permission sets
        resource_map = {
            "model": cls.MODEL_MANAGEMENT_RESOURCES,
            "system": cls.SYSTEM_RESOURCES
        }
        
        resource_perms = resource_map.get(resource_type, {}).get(resource_name, {})
        required_perms = resource_perms.get(action, [])
        
        if not required_perms:
            return False
        
        # Check if user has any required permission
        return RolePermissions.has_any_permission(user_role, required_perms)
    
    @classmethod
    def get_accessible_actions(
        cls,
        user_role: UserRole,
        resource_type: str,
        resource_name: str
    ) -> List[str]:
        """
        Get list of actions user can perform on resource
        
        Args:
            user_role: User's role
            resource_type: Type of resource
            resource_name: Specific resource name
            
        Returns:
            List of allowed actions
        """
        resource_map = {
            "model": cls.MODEL_MANAGEMENT_RESOURCES,
            "system": cls.SYSTEM_RESOURCES
        }
        
        resource_perms = resource_map.get(resource_type, {}).get(resource_name, {})
        accessible_actions = []
        
        for action, required_perms in resource_perms.items():
            if RolePermissions.has_any_permission(user_role, required_perms):
                accessible_actions.append(action)
        
        return accessible_actions

# ===================================================================
# PERMISSION CHECKING FUNCTIONS
# ===================================================================

def check_permissions(
    user_role: UserRole,
    required_permissions: List[Permission],
    require_all: bool = False
) -> bool:
    """
    Check if user has required permissions
    
    Args:
        user_role: User's role
        required_permissions: List of required permissions
        require_all: If True, user must have ALL permissions
        
    Returns:
        True if user has required permissions
    """
    if require_all:
        return RolePermissions.has_all_permissions(user_role, required_permissions)
    else:
        return RolePermissions.has_any_permission(user_role, required_permissions)

def check_resource_access(
    user_role: UserRole,
    resource_type: ResourceType,
    action: str,
    resource_id: Optional[str] = None
) -> Tuple[bool, Optional[str]]:
    """
    Check resource-based access control
    
    Args:
        user_role: User's role 
        resource_type: Type of resource
        action: Action being performed
        resource_id: Optional specific resource identifier
        
    Returns:
        Tuple of (is_allowed, reason)
    """
    # Map resource types to required permissions
    resource_permission_map = {
        ResourceType.MODEL_ASSIGNMENT: {
            "read": [Permission.MODEL_READ, Permission.MODEL_ASSIGNMENT_READ],
            "write": [Permission.MODEL_WRITE, Permission.MODEL_ASSIGNMENT_WRITE],
            "delete": [Permission.MODEL_DELETE, Permission.MODEL_ADMIN]
        },
        ResourceType.MODEL_PERFORMANCE: {
            "read": [Permission.MODEL_PERFORMANCE_READ, Permission.MONITOR_READ]
        },
        ResourceType.SYSTEM_HEALTH: {
            "read": [Permission.SYSTEM_HEALTH_READ, Permission.SYSTEM_READ]
        }
    }
    
    required_perms = resource_permission_map.get(resource_type, {}).get(action, [])
    
    if not required_perms:
        return False, f"No permissions defined for {resource_type.value}:{action}"
    
    has_permission = RolePermissions.has_any_permission(user_role, required_perms)
    
    if not has_permission:
        return False, f"Insufficient permissions for {resource_type.value}:{action}"
    
    return True, None

# ===================================================================
# AUDIT INTEGRATION
# ===================================================================

def log_permission_check(
    user_id: str,
    user_role: UserRole,
    permission: Permission,
    resource: str,
    granted: bool
):
    """Log permission check for audit trail"""
    logger.info(
        f"Permission check: user={user_id}, role={user_role.value}, "
        f"permission={permission.value}, resource={resource}, granted={granted}"
    ) 