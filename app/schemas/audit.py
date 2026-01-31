"""
Audit Log Pydantic Schemas
"""

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum


class AuditAction(str, Enum):
    """Audit action types"""
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILED = "login_failed"
    LOGOUT = "logout"
    TOKEN_REFRESH = "token_refresh"
    PASSWORD_CHANGE = "password_change"
    USER_CREATE = "user_create"
    USER_UPDATE = "user_update"
    USER_DELETE = "user_delete"
    ROLE_ASSIGN = "role_assign"
    FILE_UPLOAD = "file_upload"
    FILE_DOWNLOAD = "file_download"
    FILE_DELETE = "file_delete"
    FILE_UPDATE = "file_update"
    SHARE_CREATE = "share_create"
    SHARE_ACCESS = "share_access"
    SHARE_REVOKE = "share_revoke"
    PERMISSION_GRANT = "permission_grant"
    PERMISSION_REVOKE = "permission_revoke"


class AuditLogResponse(BaseModel):
    """Audit log response"""
    id: int
    user_id: Optional[int] = None
    user_email: Optional[str] = None
    action: AuditAction
    resource_type: Optional[str] = None
    resource_id: Optional[int] = None
    details: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    status: str
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class AuditLogFilter(BaseModel):
    """Audit log filter parameters"""
    user_id: Optional[int] = None
    action: Optional[AuditAction] = None
    resource_type: Optional[str] = None
    resource_id: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: Optional[str] = None


class AuditLogListResponse(BaseModel):
    """Paginated audit log list response"""
    items: List[AuditLogResponse]
    total: int
    page: int
    size: int
