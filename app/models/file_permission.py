"""
File Permission Model for file sharing
"""

from sqlalchemy import Column, String, Integer, ForeignKey, Boolean, Enum
from sqlalchemy.orm import relationship
import enum

from app.models.base import BaseModel


class PermissionLevel(str, enum.Enum):
    """Permission levels for file access"""
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"


class FilePermission(BaseModel):
    """File permission model for sharing files with users"""
    
    __tablename__ = "file_permissions"
    
    # Foreign Keys
    file_id = Column(Integer, ForeignKey("files.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Permission settings
    permission_level = Column(
        Enum(PermissionLevel),
        default=PermissionLevel.READ,
        nullable=False
    )
    can_download = Column(Boolean, default=True, nullable=False)
    can_share = Column(Boolean, default=False, nullable=False)
    
    # Who granted this permission
    granted_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relationships
    file = relationship("File", back_populates="permissions")
    user = relationship("User", foreign_keys=[user_id])
    granted_by = relationship("User", foreign_keys=[granted_by_id])
    
    def __repr__(self):
        return f"<FilePermission(file_id={self.file_id}, user_id={self.user_id}, level={self.permission_level})>"
