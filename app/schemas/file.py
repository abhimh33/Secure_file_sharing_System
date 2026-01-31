"""
File Pydantic Schemas
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class PermissionLevel(str, Enum):
    """Permission level enum"""
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"


class FileBase(BaseModel):
    """Base file schema"""
    filename: str
    description: Optional[str] = None


class FileUploadResponse(BaseModel):
    """File upload response"""
    id: int
    filename: str
    original_filename: str
    content_type: str
    size: int
    s3_key: str
    owner_id: int
    created_at: Optional[datetime] = None
    message: str = "File uploaded successfully"
    
    class Config:
        from_attributes = True


class FileResponse(BaseModel):
    """File detail response"""
    id: int
    filename: str
    original_filename: str
    content_type: str
    size: int
    description: Optional[str] = None
    owner_id: int
    owner_email: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class FileListResponse(BaseModel):
    """File list item response"""
    id: int
    filename: str
    original_filename: str
    content_type: str
    size: int
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class FileUpdate(BaseModel):
    """File update schema"""
    filename: Optional[str] = None
    description: Optional[str] = None


class FilePermissionCreate(BaseModel):
    """Create file permission schema"""
    user_id: int
    permission_level: PermissionLevel = PermissionLevel.READ
    can_download: bool = True
    can_share: bool = False


class FilePermissionResponse(BaseModel):
    """File permission response"""
    id: int
    file_id: int
    user_id: int
    user_email: Optional[str] = None
    permission_level: PermissionLevel
    can_download: bool
    can_share: bool
    granted_by_id: Optional[int] = None
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class FileStats(BaseModel):
    """File statistics"""
    total_files: int
    total_size: int
    total_shared: int
