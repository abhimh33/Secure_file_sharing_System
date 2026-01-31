"""
Role-Based Access Control (RBAC) Implementation
"""

from enum import Enum
from typing import List


class UserRole(str, Enum):
    """User role enumeration"""
    ADMIN = "admin"
    USER = "user"
    VIEWER = "viewer"


# Role hierarchy - higher roles include permissions of lower roles
ROLE_HIERARCHY = {
    UserRole.ADMIN: [UserRole.ADMIN, UserRole.USER, UserRole.VIEWER],
    UserRole.USER: [UserRole.USER, UserRole.VIEWER],
    UserRole.VIEWER: [UserRole.VIEWER]
}

# Role permissions mapping
ROLE_PERMISSIONS = {
    UserRole.ADMIN: [
        "user:create",
        "user:read",
        "user:update",
        "user:delete",
        "user:assign_role",
        "file:upload",
        "file:download",
        "file:delete",
        "file:share",
        "file:read_all",
        "audit:read"
    ],
    UserRole.USER: [
        "file:upload",
        "file:download",
        "file:delete",
        "file:share",
        "file:read_own"
    ],
    UserRole.VIEWER: [
        "file:download_shared"
    ]
}


def has_role(user_role: str, required_role: UserRole) -> bool:
    """
    Check if user has the required role or higher
    
    Args:
        user_role: User's current role string
        required_role: Required role to check
        
    Returns:
        True if user has required role or higher
    """
    try:
        user_role_enum = UserRole(user_role)
        allowed_roles = ROLE_HIERARCHY.get(user_role_enum, [])
        return required_role in allowed_roles
    except ValueError:
        return False


def has_permission(user_role: str, permission: str) -> bool:
    """
    Check if user's role has the required permission
    
    Args:
        user_role: User's role string
        permission: Permission string to check
        
    Returns:
        True if user has permission
    """
    try:
        user_role_enum = UserRole(user_role)
        permissions = ROLE_PERMISSIONS.get(user_role_enum, [])
        return permission in permissions
    except ValueError:
        return False


def get_role_permissions(role: str) -> List[str]:
    """
    Get all permissions for a role
    
    Args:
        role: Role string
        
    Returns:
        List of permission strings
    """
    try:
        role_enum = UserRole(role)
        return ROLE_PERMISSIONS.get(role_enum, [])
    except ValueError:
        return []


def is_admin(role: str) -> bool:
    """Check if role is admin"""
    return role == UserRole.ADMIN.value


def is_user(role: str) -> bool:
    """Check if role is user"""
    return role == UserRole.USER.value


def is_viewer(role: str) -> bool:
    """Check if role is viewer"""
    return role == UserRole.VIEWER.value
