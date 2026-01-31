"""
Authentication API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.auth import (
    Token,
    LoginRequest,
    RegisterRequest,
    RefreshTokenRequest
)
from app.schemas.user import UserResponse
from app.schemas.common import MessageResponse
from app.services.auth_service import AuthService
from app.security.dependencies import get_current_user, rate_limiter
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user"
)
async def register(
    register_data: RegisterRequest,
    request: Request,
    db: Session = Depends(get_db),
    _: bool = Depends(rate_limiter)
):
    """
    Register a new user account.
    
    - **email**: Valid email address (unique)
    - **password**: Password (min 8 chars, must contain uppercase, lowercase, digit)
    - **full_name**: Optional full name
    
    Returns user info and JWT tokens.
    """
    auth_service = AuthService(db)
    result = auth_service.register(register_data, request)
    
    return {
        "message": "User registered successfully",
        "user": UserResponse.model_validate(result["user"]),
        "tokens": result["tokens"]
    }


@router.post(
    "/login",
    response_model=dict,
    summary="Login and get tokens"
)
async def login(
    login_data: LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
    _: bool = Depends(rate_limiter)
):
    """
    Authenticate user and get JWT tokens.
    
    - **email**: User's email address
    - **password**: User's password
    
    Returns access token (20 min) and refresh token (7 days).
    """
    auth_service = AuthService(db)
    result = auth_service.login(login_data, request)
    
    return {
        "message": "Login successful",
        "user": UserResponse.model_validate(result["user"]),
        "tokens": result["tokens"]
    }


@router.post(
    "/refresh",
    response_model=Token,
    summary="Refresh access token"
)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Get a new access token using refresh token.
    
    - **refresh_token**: Valid refresh token
    
    Returns new access and refresh tokens.
    """
    auth_service = AuthService(db)
    tokens = auth_service.refresh_token(refresh_data.refresh_token, request)
    
    return Token(**tokens)


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Logout user"
)
async def logout(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Logout current user.
    
    Logs the logout action in audit trail.
    """
    auth_service = AuthService(db)
    auth_service.logout(current_user, request)
    
    return MessageResponse(message="Logged out successfully")


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user"
)
async def get_me(
    current_user: User = Depends(get_current_user)
):
    """
    Get current authenticated user's information.
    """
    return UserResponse.model_validate(current_user)
