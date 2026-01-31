"""
Schemas Package
Export all schemas for easy imports
"""

from app.schemas.common import (
    BaseSchema,
    MessageResponse,
    ErrorResponse,
    PaginatedResponse,
    HealthCheck
)
from app.schemas.user import (
    UserCreate,
    UserLogin,
    UserUpdate,
    UserResponse,
    UserListResponse,
    UserRoleUpdate,
    PasswordChange,
    RoleCreate,
    RoleResponse
)
from app.schemas.auth import (
    Token,
    TokenData,
    RefreshTokenRequest,
    LoginRequest,
    RegisterRequest,
    LogoutRequest
)
from app.schemas.file import (
    FileUploadResponse,
    FileResponse,
    FileListResponse,
    FileUpdate,
    FilePermissionCreate,
    FilePermissionResponse,
    FileStats,
    PermissionLevel
)
from app.schemas.share import (
    ShareLinkCreate,
    ShareLinkResponse,
    ShareLinkInfo,
    ShareLinkValidation,
    ShareLinkListResponse
)
from app.schemas.audit import (
    AuditLogResponse,
    AuditLogFilter,
    AuditLogListResponse,
    AuditAction
)

__all__ = [
    # Common
    "BaseSchema",
    "MessageResponse",
    "ErrorResponse",
    "PaginatedResponse",
    "HealthCheck",
    # User
    "UserCreate",
    "UserLogin",
    "UserUpdate",
    "UserResponse",
    "UserListResponse",
    "UserRoleUpdate",
    "PasswordChange",
    "RoleCreate",
    "RoleResponse",
    # Auth
    "Token",
    "TokenData",
    "RefreshTokenRequest",
    "LoginRequest",
    "RegisterRequest",
    "LogoutRequest",
    # File
    "FileUploadResponse",
    "FileResponse",
    "FileListResponse",
    "FileUpdate",
    "FilePermissionCreate",
    "FilePermissionResponse",
    "FileStats",
    "PermissionLevel",
    # Share
    "ShareLinkCreate",
    "ShareLinkResponse",
    "ShareLinkInfo",
    "ShareLinkValidation",
    "ShareLinkListResponse",
    # Audit
    "AuditLogResponse",
    "AuditLogFilter",
    "AuditLogListResponse",
    "AuditAction"
]
