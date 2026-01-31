"""
Common Pydantic Schemas
"""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Generic, TypeVar, List

T = TypeVar('T')


class BaseSchema(BaseModel):
    """Base schema with common configuration"""
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class TimestampMixin(BaseModel):
    """Mixin for timestamp fields"""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class MessageResponse(BaseModel):
    """Generic message response"""
    message: str
    success: bool = True


class ErrorResponse(BaseModel):
    """Error response schema"""
    detail: str
    error_code: Optional[str] = None


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response wrapper"""
    items: List[T]
    total: int
    page: int
    size: int
    pages: int
    
    @classmethod
    def create(cls, items: List[T], total: int, page: int, size: int):
        pages = (total + size - 1) // size if size > 0 else 0
        return cls(items=items, total=total, page=page, size=size, pages=pages)


class HealthCheck(BaseModel):
    """Health check response"""
    status: str = "healthy"
    version: str
    timestamp: datetime
