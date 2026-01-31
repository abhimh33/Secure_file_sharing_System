"""
User Model
"""

from sqlalchemy import Column, String, Boolean, Integer, ForeignKey, Text
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class User(BaseModel):
    """User model for authentication and authorization"""
    
    __tablename__ = "users"
    
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    
    # Foreign Keys
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=True)
    
    # Relationships
    role = relationship("Role", back_populates="users")
    files = relationship("File", back_populates="owner", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email})>"
    
    @property
    def role_name(self) -> str:
        """Get role name or default to 'viewer'"""
        return self.role.name if self.role else "viewer"
