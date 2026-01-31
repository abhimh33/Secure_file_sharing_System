"""
User Pydantic Schemas
"""

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import datetime


class RoleBase(BaseModel):
    """Base role schema"""
    name: str = Field(..., min_length=2, max_length=50)
    description: Optional[str] = None


class RoleCreate(RoleBase):
    """Role creation schema"""
    pass


class RoleResponse(RoleBase):
    """Role response schema"""
    id: int
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class UserBase(BaseModel):
    """Base user schema"""
    email: EmailStr
    full_name: Optional[str] = Field(None, max_length=255)


class UserCreate(UserBase):
    """User registration schema"""
    password: str = Field(..., min_length=8, max_length=100)
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v


class UserLogin(BaseModel):
    """User login schema"""
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    """User update schema"""
    full_name: Optional[str] = Field(None, max_length=255)
    is_active: Optional[bool] = None


class UserRoleUpdate(BaseModel):
    """Schema for updating user role (admin only)"""
    role_id: int


class PasswordChange(BaseModel):
    """Password change schema"""
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=100)
    
    @validator('new_password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v


class UserResponse(UserBase):
    """User response schema"""
    id: int
    is_active: bool
    is_verified: bool
    role: Optional[RoleResponse] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    """User list response"""
    id: int
    email: str
    full_name: Optional[str] = None
    is_active: bool
    role_name: Optional[str] = None
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
