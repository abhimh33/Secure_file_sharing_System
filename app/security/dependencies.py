"""
Authentication and Authorization Dependencies
FastAPI dependencies for protecting endpoints
"""

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional, List

from app.core.database import get_db
from app.core.redis import get_redis, RedisClient
from app.security.jwt import verify_access_token
from app.security.rbac import UserRole, has_role, has_permission
from app.models.user import User


# HTTP Bearer token scheme
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Get current authenticated user from JWT token
    
    Args:
        credentials: Bearer token from request header
        db: Database session
        
    Returns:
        User object if authenticated
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"}
    )
    
    token = credentials.credentials
    payload = verify_access_token(token)
    
    if payload is None:
        raise credentials_exception
    
    user_id = payload.get("sub")
    if user_id is None:
        raise credentials_exception
    
    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise credentials_exception
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated"
        )
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current active user
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User object if active
        
    Raises:
        HTTPException: If user is not active
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return current_user


def require_role(required_roles: List[UserRole]):
    """
    Dependency factory to require specific roles
    
    Args:
        required_roles: List of allowed roles
        
    Returns:
        Dependency function
    """
    async def role_checker(
        current_user: User = Depends(get_current_user)
    ) -> User:
        user_role = current_user.role.name if current_user.role else None
        
        if user_role is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no role assigned"
            )
        
        # Check if user has any of the required roles
        has_required_role = any(
            has_role(user_role, role) for role in required_roles
        )
        
        if not has_required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        return current_user
    
    return role_checker


def require_permission(permission: str):
    """
    Dependency factory to require specific permission
    
    Args:
        permission: Required permission string
        
    Returns:
        Dependency function
    """
    async def permission_checker(
        current_user: User = Depends(get_current_user)
    ) -> User:
        user_role = current_user.role.name if current_user.role else None
        
        if user_role is None or not has_permission(user_role, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {permission}"
            )
        
        return current_user
    
    return permission_checker


# Convenience dependencies
require_admin = require_role([UserRole.ADMIN])
require_user = require_role([UserRole.ADMIN, UserRole.USER])
require_viewer = require_role([UserRole.ADMIN, UserRole.USER, UserRole.VIEWER])


class RateLimiter:
    """Rate limiting using Redis"""
    
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.window_seconds = 60
    
    async def __call__(
        self,
        request: Request,
        redis: RedisClient = Depends(get_redis)
    ):
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        key = f"rate_limit:{client_ip}:{request.url.path}"
        
        # Increment counter
        count = redis.increment(key, self.window_seconds)
        
        if count > self.requests_per_minute:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again later."
            )
        
        return True


# Default rate limiter
rate_limiter = RateLimiter()
