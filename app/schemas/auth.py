"""
Authentication Pydantic Schemas
"""

from pydantic import BaseModel, EmailStr
from typing import Optional


class Token(BaseModel):
    """JWT token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Token payload data"""
    user_id: Optional[int] = None
    email: Optional[str] = None
    role: Optional[str] = None


class RefreshTokenRequest(BaseModel):
    """Refresh token request"""
    refresh_token: str


class LoginRequest(BaseModel):
    """Login request schema"""
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    """Registration request schema"""
    email: EmailStr
    password: str
    full_name: Optional[str] = None


class LogoutRequest(BaseModel):
    """Logout request (optional - for blacklisting tokens)"""
    refresh_token: Optional[str] = None
