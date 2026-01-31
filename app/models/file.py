"""
File Model for stored files metadata
"""

from sqlalchemy import Column, String, BigInteger, Integer, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class File(BaseModel):
    """File metadata model"""
    
    __tablename__ = "files"
    
    # File information
    filename = Column(String(500), nullable=False)
    original_filename = Column(String(500), nullable=False)
    content_type = Column(String(255), nullable=False)
    size = Column(BigInteger, nullable=False)  # Size in bytes
    
    # S3 storage information
    s3_key = Column(String(1000), unique=True, nullable=False, index=True)
    s3_bucket = Column(String(255), nullable=False)
    
    # File status
    is_deleted = Column(Boolean, default=False, nullable=False)
    
    # Optional description
    description = Column(Text, nullable=True)
    
    # Foreign Keys
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Relationships
    owner = relationship("User", back_populates="files")
    permissions = relationship("FilePermission", back_populates="file", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<File(id={self.id}, filename={self.filename}, owner_id={self.owner_id})>"
