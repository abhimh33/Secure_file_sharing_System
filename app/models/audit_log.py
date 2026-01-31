"""
Audit Log Model for tracking all sensitive actions
"""

from sqlalchemy import Column, String, Integer, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
import enum

from app.models.base import BaseModel


class AuditAction(str, enum.Enum):
    """Audit action types"""
    # Authentication
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILED = "login_failed"
    LOGOUT = "logout"
    TOKEN_REFRESH = "token_refresh"
    PASSWORD_CHANGE = "password_change"
    
    # User management
    USER_CREATE = "user_create"
    USER_UPDATE = "user_update"
    USER_DELETE = "user_delete"
    ROLE_ASSIGN = "role_assign"
    
    # File operations
    FILE_UPLOAD = "file_upload"
    FILE_DOWNLOAD = "file_download"
    FILE_DELETE = "file_delete"
    FILE_UPDATE = "file_update"
    
    # Sharing
    SHARE_CREATE = "share_create"
    SHARE_ACCESS = "share_access"
    SHARE_REVOKE = "share_revoke"
    PERMISSION_GRANT = "permission_grant"
    PERMISSION_REVOKE = "permission_revoke"


class AuditLog(BaseModel):
    """Audit log model for tracking all sensitive actions"""
    
    __tablename__ = "audit_logs"
    
    # Who performed the action
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    user_email = Column(String(255), nullable=True)  # Store email in case user is deleted
    
    # What action was performed
    action = Column(Enum(AuditAction), nullable=False, index=True)
    
    # Resource affected
    resource_type = Column(String(50), nullable=True)  # e.g., "file", "user", "share_link"
    resource_id = Column(Integer, nullable=True)
    
    # Additional details
    details = Column(Text, nullable=True)  # JSON string with additional info
    
    # Request information
    ip_address = Column(String(45), nullable=True)  # IPv6 compatible
    user_agent = Column(String(500), nullable=True)
    
    # Status
    status = Column(String(20), default="success", nullable=False)  # success, failed, error
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")
    
    def __repr__(self):
        return f"<AuditLog(id={self.id}, action={self.action}, user_id={self.user_id})>"
