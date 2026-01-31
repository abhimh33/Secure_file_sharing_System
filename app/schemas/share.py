"""
Share Link Pydantic Schemas
"""

from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime


class ShareLinkCreate(BaseModel):
    """Create share link request"""
    file_id: int
    expiry_minutes: int = Field(..., ge=1, le=43200)  # 1 min to 30 days
    max_downloads: Optional[int] = Field(None, ge=1)
    password: Optional[str] = Field(None, min_length=1)  # Password protection
    requires_auth: bool = False
    allowed_email: Optional[str] = None
    
    @validator('expiry_minutes')
    def validate_expiry(cls, v):
        if v < 1:
            raise ValueError('Expiry must be at least 1 minute')
        if v > 43200:  # 30 days
            raise ValueError('Expiry cannot exceed 30 days')
        return v


class ShareLinkResponse(BaseModel):
    """Share link response"""
    token: str
    share_url: str
    file_id: int
    filename: str
    expires_at: datetime
    expires_in_minutes: int
    max_downloads: Optional[int] = None
    has_password: bool = False
    requires_auth: bool = False
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ShareLinkInfo(BaseModel):
    """Share link information for validation"""
    token: str
    file_id: int
    filename: str
    content_type: str
    size: int
    expires_at: datetime
    is_valid: bool
    download_count: int
    max_downloads: Optional[int] = None
    has_password: bool = False


class ShareLinkValidation(BaseModel):
    """Share link validation result"""
    is_valid: bool
    file_id: Optional[int] = None
    message: str
    expires_at: Optional[datetime] = None


class ShareLinkListResponse(BaseModel):
    """Share link list item"""
    id: int
    token: str
    file_id: int
    filename: str
    expires_at: datetime
    is_active: bool
    download_count: int
    max_downloads: Optional[int] = None
    has_password: bool = False
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
