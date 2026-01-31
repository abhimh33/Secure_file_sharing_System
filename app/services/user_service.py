"""
User Service
Business logic for user management
"""

from sqlalchemy.orm import Session
from typing import Optional, List
from fastapi import HTTPException, status

from app.models.user import User
from app.models.role import Role
from app.schemas.user import UserCreate, UserUpdate, UserRoleUpdate
from app.security.password import hash_password, verify_password


class UserService:
    """Service for user-related operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        return self.db.query(User).filter(User.email == email).first()
    
    def get_users(
        self,
        skip: int = 0,
        limit: int = 100,
        is_active: Optional[bool] = None
    ) -> List[User]:
        """Get list of users with pagination"""
        query = self.db.query(User)
        
        if is_active is not None:
            query = query.filter(User.is_active == is_active)
        
        return query.offset(skip).limit(limit).all()
    
    def get_users_count(self, is_active: Optional[bool] = None) -> int:
        """Get total count of users"""
        query = self.db.query(User)
        if is_active is not None:
            query = query.filter(User.is_active == is_active)
        return query.count()
    
    def create_user(
        self,
        user_data: UserCreate,
        role_name: str = "user"
    ) -> User:
        """Create a new user"""
        # Check if user already exists
        existing_user = self.get_user_by_email(user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Get role
        role = self.db.query(Role).filter(Role.name == role_name).first()
        
        # Create user
        user = User(
            email=user_data.email,
            hashed_password=hash_password(user_data.password),
            full_name=user_data.full_name,
            role_id=role.id if role else None,
            is_active=True,
            is_verified=False
        )
        
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    def update_user(self, user_id: int, user_data: UserUpdate) -> User:
        """Update user information"""
        user = self.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        update_data = user_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)
        
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    def update_user_role(
        self,
        user_id: int,
        role_data: UserRoleUpdate,
        admin_user: User
    ) -> User:
        """Update user's role (admin only)"""
        user = self.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        role = self.db.query(Role).filter(Role.id == role_data.role_id).first()
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Role not found"
            )
        
        user.role_id = role.id
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    def change_password(
        self,
        user_id: int,
        current_password: str,
        new_password: str
    ) -> bool:
        """Change user password"""
        user = self.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Verify current password
        if not verify_password(current_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        # Update password
        user.hashed_password = hash_password(new_password)
        self.db.commit()
        
        return True
    
    def delete_user(self, user_id: int) -> bool:
        """Soft delete user (deactivate)"""
        user = self.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user.is_active = False
        self.db.commit()
        
        return True
    
    def hard_delete_user(self, user_id: int) -> bool:
        """Permanently delete user"""
        user = self.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        self.db.delete(user)
        self.db.commit()
        
        return True


def get_user_service(db: Session) -> UserService:
    """Factory function for UserService"""
    return UserService(db)
