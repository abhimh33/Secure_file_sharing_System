"""
File Service
Business logic for file management
"""

import uuid
from datetime import datetime
from sqlalchemy.orm import Session
from typing import Optional, List, BinaryIO
from fastapi import HTTPException, status, UploadFile, Request
from io import BytesIO

from app.models.file import File
from app.models.file_permission import FilePermission, PermissionLevel
from app.models.user import User
from app.schemas.file import FileUpdate, FilePermissionCreate
from app.core.s3 import s3_service
from app.core.config import settings
from app.services.audit_service import AuditService
from app.models.audit_log import AuditAction


class FileService:
    """Service for file-related operations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.audit_service = AuditService(db)
        self.s3 = s3_service
    
    def _generate_s3_key(self, user_id: int, filename: str) -> str:
        """Generate unique S3 key for file"""
        unique_id = uuid.uuid4().hex
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        return f"files/{user_id}/{timestamp}_{unique_id}_{filename}"
    
    def _validate_file_size(self, file_size: int) -> None:
        """Validate file size against max allowed"""
        if file_size > settings.MAX_FILE_SIZE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File size exceeds maximum allowed ({settings.MAX_FILE_SIZE_MB}MB)"
            )
    
    async def upload_file(
        self,
        file: UploadFile,
        owner: User,
        description: Optional[str] = None,
        request: Optional[Request] = None
    ) -> File:
        """Upload a file to S3 and create metadata record"""
        # Read file content
        content = await file.read()
        file_size = len(content)
        
        # Validate file size
        self._validate_file_size(file_size)
        
        # Generate S3 key
        s3_key = self._generate_s3_key(owner.id, file.filename)
        
        # Upload to S3
        file_obj = BytesIO(content)
        success = self.s3.upload_file(
            file_data=file_obj,
            s3_key=s3_key,
            content_type=file.content_type
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to upload file to storage"
            )
        
        # Create file record
        file_record = File(
            filename=file.filename,
            original_filename=file.filename,
            content_type=file.content_type or "application/octet-stream",
            size=file_size,
            s3_key=s3_key,
            s3_bucket=settings.S3_BUCKET_NAME,
            owner_id=owner.id,
            description=description
        )
        
        self.db.add(file_record)
        self.db.commit()
        self.db.refresh(file_record)
        
        # Log audit event
        self.audit_service.log(
            action=AuditAction.FILE_UPLOAD,
            user_id=owner.id,
            user_email=owner.email,
            resource_type="file",
            resource_id=file_record.id,
            details=f"File uploaded: {file.filename} ({file_size} bytes)",
            request=request
        )
        
        return file_record
    
    def get_file_by_id(self, file_id: int) -> Optional[File]:
        """Get file by ID"""
        return self.db.query(File).filter(
            File.id == file_id,
            File.is_deleted == False
        ).first()
    
    def get_user_files(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[File]:
        """Get files owned by user"""
        return self.db.query(File).filter(
            File.owner_id == user_id,
            File.is_deleted == False
        ).offset(skip).limit(limit).all()
    
    def get_user_files_count(self, user_id: int) -> int:
        """Get count of files owned by user"""
        return self.db.query(File).filter(
            File.owner_id == user_id,
            File.is_deleted == False
        ).count()
    
    def get_shared_files(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[File]:
        """Get files shared with user"""
        return self.db.query(File).join(FilePermission).filter(
            FilePermission.user_id == user_id,
            File.is_deleted == False
        ).offset(skip).limit(limit).all()
    
    def get_all_files(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> List[File]:
        """Get all files (admin only)"""
        return self.db.query(File).filter(
            File.is_deleted == False
        ).offset(skip).limit(limit).all()
    
    def download_file(
        self,
        file_id: int,
        user: User,
        request: Optional[Request] = None
    ) -> tuple:
        """
        Download file from S3
        Returns tuple of (file_stream, filename, content_type)
        """
        # Get file
        file_record = self.get_file_by_id(file_id)
        if not file_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        # Check permissions
        if not self._has_download_permission(file_record, user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to download this file"
            )
        
        # Get file from S3
        file_stream = self.s3.get_file_stream(file_record.s3_key)
        if not file_stream:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve file from storage"
            )
        
        # Log audit event
        self.audit_service.log(
            action=AuditAction.FILE_DOWNLOAD,
            user_id=user.id,
            user_email=user.email,
            resource_type="file",
            resource_id=file_record.id,
            details=f"File downloaded: {file_record.filename}",
            request=request
        )
        
        return file_stream, file_record.original_filename, file_record.content_type
    
    def _has_download_permission(self, file: File, user: User) -> bool:
        """Check if user has permission to download file"""
        # Owner always has access
        if file.owner_id == user.id:
            return True
        
        # Admin has access to all files
        if user.role and user.role.name == "admin":
            return True
        
        # Check file permissions
        permission = self.db.query(FilePermission).filter(
            FilePermission.file_id == file.id,
            FilePermission.user_id == user.id,
            FilePermission.can_download == True
        ).first()
        
        return permission is not None
    
    def update_file(
        self,
        file_id: int,
        file_data: FileUpdate,
        user: User,
        request: Optional[Request] = None
    ) -> File:
        """Update file metadata"""
        file_record = self.get_file_by_id(file_id)
        if not file_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        # Check ownership or admin
        if file_record.owner_id != user.id:
            if not user.role or user.role.name != "admin":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have permission to update this file"
                )
        
        # Update fields
        update_data = file_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(file_record, field, value)
        
        self.db.commit()
        self.db.refresh(file_record)
        
        # Log audit event
        self.audit_service.log(
            action=AuditAction.FILE_UPDATE,
            user_id=user.id,
            user_email=user.email,
            resource_type="file",
            resource_id=file_record.id,
            details=f"File updated: {file_record.filename}",
            request=request
        )
        
        return file_record
    
    def delete_file(
        self,
        file_id: int,
        user: User,
        request: Optional[Request] = None
    ) -> bool:
        """Soft delete file"""
        file_record = self.get_file_by_id(file_id)
        if not file_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        # Check ownership or admin
        if file_record.owner_id != user.id:
            if not user.role or user.role.name != "admin":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have permission to delete this file"
                )
        
        # Soft delete
        file_record.is_deleted = True
        self.db.commit()
        
        # Optionally delete from S3
        # self.s3.delete_file(file_record.s3_key)
        
        # Log audit event
        self.audit_service.log(
            action=AuditAction.FILE_DELETE,
            user_id=user.id,
            user_email=user.email,
            resource_type="file",
            resource_id=file_record.id,
            details=f"File deleted: {file_record.filename}",
            request=request
        )
        
        return True
    
    def grant_permission(
        self,
        file_id: int,
        permission_data: FilePermissionCreate,
        granting_user: User,
        request: Optional[Request] = None
    ) -> FilePermission:
        """Grant file permission to a user"""
        file_record = self.get_file_by_id(file_id)
        if not file_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        # Check if user can grant permissions
        if file_record.owner_id != granting_user.id:
            if not granting_user.role or granting_user.role.name != "admin":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have permission to share this file"
                )
        
        # Check if permission already exists
        existing = self.db.query(FilePermission).filter(
            FilePermission.file_id == file_id,
            FilePermission.user_id == permission_data.user_id
        ).first()
        
        if existing:
            # Update existing permission
            existing.permission_level = permission_data.permission_level
            existing.can_download = permission_data.can_download
            existing.can_share = permission_data.can_share
            self.db.commit()
            self.db.refresh(existing)
            return existing
        
        # Create new permission
        permission = FilePermission(
            file_id=file_id,
            user_id=permission_data.user_id,
            permission_level=PermissionLevel(permission_data.permission_level.value),
            can_download=permission_data.can_download,
            can_share=permission_data.can_share,
            granted_by_id=granting_user.id
        )
        
        self.db.add(permission)
        self.db.commit()
        self.db.refresh(permission)
        
        # Log audit event
        self.audit_service.log(
            action=AuditAction.PERMISSION_GRANT,
            user_id=granting_user.id,
            user_email=granting_user.email,
            resource_type="file_permission",
            resource_id=permission.id,
            details=f"Permission granted on file {file_id} to user {permission_data.user_id}",
            request=request
        )
        
        return permission
    
    def revoke_permission(
        self,
        file_id: int,
        user_id: int,
        revoking_user: User,
        request: Optional[Request] = None
    ) -> bool:
        """Revoke file permission from a user"""
        file_record = self.get_file_by_id(file_id)
        if not file_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        # Check if user can revoke permissions
        if file_record.owner_id != revoking_user.id:
            if not revoking_user.role or revoking_user.role.name != "admin":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have permission to revoke access"
                )
        
        permission = self.db.query(FilePermission).filter(
            FilePermission.file_id == file_id,
            FilePermission.user_id == user_id
        ).first()
        
        if not permission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Permission not found"
            )
        
        self.db.delete(permission)
        self.db.commit()
        
        # Log audit event
        self.audit_service.log(
            action=AuditAction.PERMISSION_REVOKE,
            user_id=revoking_user.id,
            user_email=revoking_user.email,
            resource_type="file_permission",
            resource_id=file_id,
            details=f"Permission revoked on file {file_id} from user {user_id}",
            request=request
        )
        
        return True
    
    def get_file_permissions(self, file_id: int) -> List[FilePermission]:
        """Get all permissions for a file"""
        return self.db.query(FilePermission).filter(
            FilePermission.file_id == file_id
        ).all()


def get_file_service(db: Session) -> FileService:
    """Factory function for FileService"""
    return FileService(db)
