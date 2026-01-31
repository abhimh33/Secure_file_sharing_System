"""
User Management API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.schemas.user import (
    UserResponse,
    UserListResponse,
    UserUpdate,
    UserRoleUpdate,
    PasswordChange,
    RoleResponse,
    RoleCreate
)
from app.schemas.common import MessageResponse
from app.services.user_service import UserService
from app.security.dependencies import (
    get_current_user,
    require_admin,
    require_user
)
from app.models.user import User
from app.models.role import Role

router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    "/",
    response_model=List[UserListResponse],
    summary="List all users (Admin only)"
)
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    is_active: Optional[bool] = None,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Get list of all users.
    
    **Admin only endpoint.**
    
    - **skip**: Number of records to skip (pagination)
    - **limit**: Maximum records to return
    - **is_active**: Filter by active status
    """
    user_service = UserService(db)
    users = user_service.get_users(skip=skip, limit=limit, is_active=is_active)
    
    return [
        UserListResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
            role_name=user.role.name if user.role else None,
            created_at=user.created_at
        )
        for user in users
    ]


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Get user by ID"
)
async def get_user(
    user_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Get user details by ID.
    
    **Admin only endpoint.**
    """
    user_service = UserService(db)
    user = user_service.get_user_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse.model_validate(user)


@router.put(
    "/me",
    response_model=UserResponse,
    summary="Update current user"
)
async def update_me(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update current user's information.
    
    - **full_name**: Update display name
    """
    user_service = UserService(db)
    updated_user = user_service.update_user(current_user.id, user_data)
    
    return UserResponse.model_validate(updated_user)


@router.put(
    "/{user_id}",
    response_model=UserResponse,
    summary="Update user (Admin only)"
)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Update any user's information.
    
    **Admin only endpoint.**
    """
    user_service = UserService(db)
    updated_user = user_service.update_user(user_id, user_data)
    
    return UserResponse.model_validate(updated_user)


@router.put(
    "/{user_id}/role",
    response_model=UserResponse,
    summary="Assign role to user (Admin only)"
)
async def assign_role(
    user_id: int,
    role_data: UserRoleUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Assign a role to a user.
    
    **Admin only endpoint.**
    
    - **role_id**: ID of the role to assign
    """
    user_service = UserService(db)
    updated_user = user_service.update_user_role(user_id, role_data, current_user)
    
    return UserResponse.model_validate(updated_user)


@router.post(
    "/change-password",
    response_model=MessageResponse,
    summary="Change password"
)
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Change current user's password.
    
    - **current_password**: Current password for verification
    - **new_password**: New password (min 8 chars)
    """
    user_service = UserService(db)
    user_service.change_password(
        current_user.id,
        password_data.current_password,
        password_data.new_password
    )
    
    return MessageResponse(message="Password changed successfully")


@router.delete(
    "/{user_id}",
    response_model=MessageResponse,
    summary="Deactivate user (Admin only)"
)
async def deactivate_user(
    user_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Deactivate a user account (soft delete).
    
    **Admin only endpoint.**
    """
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own account"
        )
    
    user_service = UserService(db)
    user_service.delete_user(user_id)
    
    return MessageResponse(message="User deactivated successfully")


# ============ Role Management ============

@router.get(
    "/roles/list",
    response_model=List[RoleResponse],
    summary="List all roles"
)
async def list_roles(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Get list of all available roles.
    
    **Admin only endpoint.**
    """
    roles = db.query(Role).all()
    return [RoleResponse.model_validate(role) for role in roles]


@router.post(
    "/roles",
    response_model=RoleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new role (Admin only)"
)
async def create_role(
    role_data: RoleCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Create a new role.
    
    **Admin only endpoint.**
    """
    # Check if role exists
    existing = db.query(Role).filter(Role.name == role_data.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role already exists"
        )
    
    role = Role(name=role_data.name, description=role_data.description)
    db.add(role)
    db.commit()
    db.refresh(role)
    
    return RoleResponse.model_validate(role)
