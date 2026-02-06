"""
Authentication Service
Business logic for authentication
"""

from sqlalchemy.orm import Session
from typing import Optional, Dict
from fastapi import HTTPException, status, Request

from app.models.user import User
from app.models.role import Role
from app.schemas.auth import RegisterRequest, LoginRequest
from app.security.password import hash_password, verify_password
from app.security.jwt import create_tokens, verify_refresh_token
from app.services.audit_service import AuditService
from app.models.audit_log import AuditAction


class AuthService:
    """Service for authentication operations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.audit_service = AuditService(db)
    
    def register(
        self,
        register_data: RegisterRequest,
        request: Optional[Request] = None
    ) -> Dict:
        """Register a new user"""
        # Check if user exists
        existing_user = self.db.query(User).filter(
            User.email == register_data.email
        ).first()
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Get default 'user' role
        default_role = self.db.query(Role).filter(Role.name == "user").first()
        
        # Create user
        user = User(
            email=register_data.email,
            hashed_password=hash_password(register_data.password),
            full_name=register_data.full_name,
            role_id=default_role.id if default_role else None,
            is_active=True,
            is_verified=False
        )
        
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        
        # Log audit event
        self.audit_service.log(
            action=AuditAction.USER_CREATE,
            user_id=user.id,
            user_email=user.email,
            resource_type="user",
            resource_id=user.id,
            details=f"User registered: {user.email}",
            request=request
        )
        
        # Generate tokens
        role_name = user.role.name if user.role else "user"
        tokens = create_tokens(user.id, user.email, role_name)
        
        return {
            "user": user,
            "tokens": tokens
        }
    
    def login(
        self,
        login_data: LoginRequest,
        request: Optional[Request] = None
    ) -> Dict:
        """Authenticate user and return tokens"""
        # Find user
        user = self.db.query(User).filter(
            User.email == login_data.email
        ).first()
        
        # Verify credentials
        if not user or not verify_password(login_data.password, user.hashed_password):
            # Log failed attempt
            self.audit_service.log(
                action=AuditAction.LOGIN_FAILED,
                user_email=login_data.email,
                details=f"Failed login attempt for: {login_data.email}",
                status="failed",
                request=request
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )
        
        # Check if user is active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is deactivated"
            )
        
        # Log successful login
        self.audit_service.log(
            action=AuditAction.LOGIN_SUCCESS,
            user_id=user.id,
            user_email=user.email,
            resource_type="user",
            resource_id=user.id,
            details=f"User logged in: {user.email}",
            request=request
        )
        
        # Generate tokens
        role_name = user.role.name if user.role else "user"
        tokens = create_tokens(user.id, user.email, role_name)
        
        return {
            "user": user,
            "tokens": tokens
        }
    
    def refresh_token(
        self,
        refresh_token: str,
        request: Optional[Request] = None
    ) -> Dict:
        """Refresh access token using refresh token"""
        # Verify refresh token
        payload = verify_refresh_token(refresh_token)
        
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token"
            )
        
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )
        
        # Get user
        user = self.db.query(User).filter(User.id == int(user_id)).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is deactivated"
            )
        
        # Log token refresh
        self.audit_service.log(
            action=AuditAction.TOKEN_REFRESH,
            user_id=user.id,
            user_email=user.email,
            resource_type="auth",
            details="Token refreshed",
            request=request
        )
        
        # Generate new tokens
        role_name = user.role.name if user.role else "user"
        tokens = create_tokens(user.id, user.email, role_name)
        
        return tokens
    
    def logout(
        self,
        user: User,
        request: Optional[Request] = None
    ) -> bool:
        """
        Logout user
        In a production system, you would blacklist the tokens in Redis
        """
        # Log logout
        self.audit_service.log(
            action=AuditAction.LOGOUT,
            user_id=user.id,
            user_email=user.email,
            resource_type="auth",
            details=f"User logged out: {user.email}",
            request=request
        )
        
        return True
    
    def forgot_password(
        self,
        email: str,
        request: Optional[Request] = None
    ) -> bool:
        """
        Handle forgot password request.
        In production, this would:
        1. Generate a password reset token
        2. Store token in Redis with TTL
        3. Send email with reset link
        
        For now, we just log the request (no email sending)
        """
        # Check if user exists (but don't reveal this to the caller)
        user = self.db.query(User).filter(User.email == email).first()
        
        if user:
            # Log password reset request
            self.audit_service.log(
                action=AuditAction.PASSWORD_RESET_REQUEST,
                user_id=user.id,
                user_email=user.email,
                resource_type="auth",
                details=f"Password reset requested for: {email}",
                request=request
            )
            
            # In production: generate token and send email
            # reset_token = secrets.token_urlsafe(32)
            # redis_client.set(f"password_reset:{reset_token}", user.id, ex=3600)
            # send_reset_email(email, reset_token)
        
        # Always return True for security (don't reveal if email exists)
        return True
    
    def reset_password(
        self,
        token: str,
        new_password: str,
        request: Optional[Request] = None
    ) -> bool:
        """
        Reset password using token.
        In production, this would:
        1. Validate token from Redis
        2. Update user password
        3. Invalidate token
        
        For now, returns an error since email/token system is not implemented
        """
        from fastapi import HTTPException, status
        
        # In production: validate token and get user_id from Redis
        # user_id = redis_client.get(f"password_reset:{token}")
        # if not user_id:
        #     raise HTTPException(status_code=400, detail="Invalid or expired reset token")
        
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Password reset via email is not yet configured. Please contact the administrator."
        )


def get_auth_service(db: Session) -> AuthService:
    """Factory function for AuthService"""
    return AuthService(db)
