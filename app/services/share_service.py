"""
Share Link Service
Business logic for creating and validating expiring share links
Uses Redis for TTL-based expiration
"""

import uuid
import json
import bcrypt
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from typing import Optional, Dict
from fastapi import HTTPException, status, Request

from app.models.file import File
from app.models.share_link import ShareLink
from app.models.user import User
from app.schemas.share import ShareLinkCreate, ShareLinkInfo
from app.core.redis import redis_client
from app.core.config import settings
from app.services.audit_service import AuditService
from app.models.audit_log import AuditAction


class ShareLinkService:
    """Service for share link operations with Redis TTL"""
    
    REDIS_PREFIX = "share_link:"
    
    def __init__(self, db: Session):
        self.db = db
        self.redis = redis_client
        self.audit_service = AuditService(db)
    
    def _generate_token(self) -> str:
        """Generate unique share token"""
        return uuid.uuid4().hex
    
    def _hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    
    def create_share_link(
        self,
        link_data: ShareLinkCreate,
        user: User,
        request: Optional[Request] = None
    ) -> Dict:
        """Create a new expiring share link"""
        # Get file
        file = self.db.query(File).filter(
            File.id == link_data.file_id,
            File.is_deleted == False
        ).first()
        
        if not file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        # Check if user owns the file or is admin
        if file.owner_id != user.id:
            if not user.role or user.role.name != "admin":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have permission to share this file"
                )
        
        # Generate token and expiry
        token = self._generate_token()
        expiry_seconds = link_data.expiry_minutes * 60
        expires_at = datetime.utcnow() + timedelta(minutes=link_data.expiry_minutes)
        
        # Hash password if provided
        password_hash = None
        if link_data.password:
            password_hash = self._hash_password(link_data.password)
        
        # Store in Redis with TTL
        redis_data = {
            "file_id": file.id,
            "filename": file.filename,
            "content_type": file.content_type,
            "size": file.size,
            "s3_key": file.s3_key,
            "created_by": user.id,
            "created_at": datetime.utcnow().isoformat(),
            "expires_at": expires_at.isoformat(),
            "max_downloads": link_data.max_downloads,
            "download_count": 0,
            "password_hash": password_hash,
            "requires_auth": link_data.requires_auth,
            "allowed_email": link_data.allowed_email
        }
        
        redis_key = f"{self.REDIS_PREFIX}{token}"
        success = self.redis.set_with_expiry(redis_key, redis_data, expiry_seconds)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create share link"
            )
        
        # Also store in database for record keeping
        share_link = ShareLink(
            token=token,
            file_id=file.id,
            created_by_id=user.id,
            expires_at=expires_at,
            max_downloads=link_data.max_downloads,
            password_hash=password_hash,
            requires_auth=link_data.requires_auth,
            allowed_email=link_data.allowed_email
        )
        
        self.db.add(share_link)
        self.db.commit()
        self.db.refresh(share_link)
        
        # Log audit event
        self.audit_service.log(
            action=AuditAction.SHARE_CREATE,
            user_id=user.id,
            user_email=user.email,
            resource_type="share_link",
            resource_id=share_link.id,
            details=f"Share link created for file {file.id}, expires in {link_data.expiry_minutes} minutes",
            request=request
        )
        
        return {
            "token": token,
            "share_url": f"/api/v1/share/{token}/download",
            "file_id": file.id,
            "filename": file.filename,
            "expires_at": expires_at,
            "expires_in_minutes": link_data.expiry_minutes,
            "max_downloads": link_data.max_downloads,
            "has_password": password_hash is not None,
            "requires_auth": link_data.requires_auth,
            "created_at": share_link.created_at
        }
    
    def validate_share_link(self, token: str) -> Optional[Dict]:
        """Validate a share link and return file info if valid"""
        redis_key = f"{self.REDIS_PREFIX}{token}"
        data = self.redis.get(redis_key)
        
        if not data:
            # Check database as fallback (link might have expired)
            db_link = self.db.query(ShareLink).filter(
                ShareLink.token == token
            ).first()
            
            if db_link:
                if not db_link.is_valid:
                    return None
            return None
        
        # Check max downloads
        if data.get("max_downloads"):
            if data.get("download_count", 0) >= data["max_downloads"]:
                return None
        
        return data
    
    def get_share_link_info(self, token: str) -> ShareLinkInfo:
        """Get detailed information about a share link"""
        data = self.validate_share_link(token)
        
        if not data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Share link not found or expired"
            )
        
        return ShareLinkInfo(
            token=token,
            file_id=data["file_id"],
            filename=data["filename"],
            content_type=data["content_type"],
            size=data["size"],
            expires_at=datetime.fromisoformat(data["expires_at"]),
            is_valid=True,
            download_count=data.get("download_count", 0),
            max_downloads=data.get("max_downloads"),
            has_password=data.get("password_hash") is not None
        )
    
    def increment_download_count(self, token: str) -> bool:
        """Increment download count for a share link"""
        redis_key = f"{self.REDIS_PREFIX}{token}"
        data = self.redis.get(redis_key)
        
        if not data:
            return False
        
        # Get remaining TTL
        ttl = self.redis.get_ttl(redis_key)
        if ttl <= 0:
            return False
        
        # Update download count
        data["download_count"] = data.get("download_count", 0) + 1
        self.redis.set_with_expiry(redis_key, data, ttl)
        
        # Also update in database
        db_link = self.db.query(ShareLink).filter(
            ShareLink.token == token
        ).first()
        
        if db_link:
            db_link.download_count += 1
            self.db.commit()
        
        return True
    
    def download_via_share_link(
        self,
        token: str,
        password: Optional[str] = None,
        user: Optional[User] = None,
        request: Optional[Request] = None
    ) -> Dict:
        """
        Download file via share link
        Returns file info for streaming
        """
        # Validate link
        data = self.validate_share_link(token)
        
        if not data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Share link not found, expired, or download limit reached"
            )
        
        # Check password if required
        if data.get("password_hash"):
            if not password:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Password required to access this file"
                )
            if not self._verify_password(password, data["password_hash"]):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid password"
                )
        
        # Check authentication requirement
        if data.get("requires_auth") and not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required to access this file"
            )
        
        # Check allowed email
        if data.get("allowed_email"):
            if not user or user.email != data["allowed_email"]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="This link is restricted to a specific user"
                )
        
        # Increment download count
        self.increment_download_count(token)
        
        # Log audit event
        self.audit_service.log(
            action=AuditAction.SHARE_ACCESS,
            user_id=user.id if user else None,
            user_email=user.email if user else None,
            resource_type="share_link",
            resource_id=data["file_id"],
            details=f"File downloaded via share link: {data['filename']}",
            request=request
        )
        
        return {
            "file_id": data["file_id"],
            "filename": data["filename"],
            "content_type": data["content_type"],
            "s3_key": data["s3_key"]
        }
    
    def revoke_share_link(
        self,
        token: str,
        user: User,
        request: Optional[Request] = None
    ) -> bool:
        """Revoke/delete a share link"""
        # Check ownership
        db_link = self.db.query(ShareLink).filter(
            ShareLink.token == token
        ).first()
        
        if not db_link:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Share link not found"
            )
        
        if db_link.created_by_id != user.id:
            if not user.role or user.role.name != "admin":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have permission to revoke this link"
                )
        
        # Delete from Redis
        redis_key = f"{self.REDIS_PREFIX}{token}"
        self.redis.delete(redis_key)
        
        # Update database
        db_link.is_active = False
        self.db.commit()
        
        # Log audit event
        self.audit_service.log(
            action=AuditAction.SHARE_REVOKE,
            user_id=user.id,
            user_email=user.email,
            resource_type="share_link",
            resource_id=db_link.id,
            details=f"Share link revoked for file {db_link.file_id}",
            request=request
        )
        
        return True
    
    def get_user_share_links(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 100
    ):
        """Get share links created by user"""
        return self.db.query(ShareLink).filter(
            ShareLink.created_by_id == user_id,
            ShareLink.is_active == True
        ).offset(skip).limit(limit).all()


def get_share_link_service(db: Session) -> ShareLinkService:
    """Factory function for ShareLinkService"""
    return ShareLinkService(db)
