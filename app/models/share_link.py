"""
Share Link Model (optional - primarily uses Redis)
For persistent record of share links
"""

from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime

from app.models.base import BaseModel


class ShareLink(BaseModel):
    """Share link model for persistent record of expiring links"""
    
    __tablename__ = "share_links"
    
    # Unique token for the share link
    token = Column(String(64), unique=True, nullable=False, index=True)
    
    # Foreign Keys
    file_id = Column(Integer, ForeignKey("files.id", ondelete="CASCADE"), nullable=False)
    created_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # Link settings
    expires_at = Column(DateTime(timezone=True), nullable=False)
    max_downloads = Column(Integer, nullable=True)  # None = unlimited
    download_count = Column(Integer, default=0, nullable=False)
    
    # Password protection (hashed)
    password_hash = Column(String(255), nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Access control
    requires_auth = Column(Boolean, default=False, nullable=False)
    allowed_email = Column(String(255), nullable=True)  # Restrict to specific email
    
    # Relationships
    file = relationship("File")
    created_by = relationship("User")
    
    def __repr__(self):
        return f"<ShareLink(token={self.token[:8]}..., file_id={self.file_id})>"
    
    @property
    def is_expired(self) -> bool:
        """Check if link has expired"""
        return datetime.utcnow() > self.expires_at.replace(tzinfo=None) if self.expires_at else True
    
    @property
    def is_valid(self) -> bool:
        """Check if link is still valid (not expired and active)"""
        if not self.is_active:
            return False
        if self.is_expired:
            return False
        if self.max_downloads and self.download_count >= self.max_downloads:
            return False
        return True
    
    @property
    def has_password(self) -> bool:
        """Check if link has password protection"""
        return self.password_hash is not None
