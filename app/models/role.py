"""
Role Model for RBAC
"""

from sqlalchemy import Column, String, Text
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class Role(BaseModel):
    """Role model for role-based access control"""
    
    __tablename__ = "roles"
    
    name = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Relationships
    users = relationship("User", back_populates="role")
    
    def __repr__(self):
        return f"<Role(id={self.id}, name={self.name})>"
