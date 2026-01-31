"""
File Management API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.schemas.file import (
    FileUploadResponse,
    FileResponse,
    FileListResponse,
    FileUpdate,
    FilePermissionCreate,
    FilePermissionResponse,
    FileStats
)
from app.schemas.common import MessageResponse
from app.services.file_service import FileService
from app.security.dependencies import (
    get_current_user,
    require_admin,
    require_user
)
from app.models.user import User
from app.core.config import settings

router = APIRouter(prefix="/files", tags=["Files"])


@router.post(
    "/upload",
    response_model=FileUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a file"
)
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    description: Optional[str] = None,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db)
):
    """
    Upload a file to secure storage.
    
    - **file**: File to upload (max 200MB)
    - **description**: Optional file description
    
    Files are stored in private S3 bucket with metadata in PostgreSQL.
    """
    # Validate file size via header if available
    content_length = request.headers.get("content-length")
    if content_length:
        if int(content_length) > settings.MAX_FILE_SIZE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File size exceeds maximum allowed ({settings.MAX_FILE_SIZE_MB}MB)"
            )
    
    file_service = FileService(db)
    file_record = await file_service.upload_file(
        file=file,
        owner=current_user,
        description=description,
        request=request
    )
    
    return FileUploadResponse.model_validate(file_record)


@router.get(
    "/",
    response_model=List[FileListResponse],
    summary="List my files"
)
async def list_my_files(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get list of files owned by current user.
    """
    file_service = FileService(db)
    files = file_service.get_user_files(
        user_id=current_user.id,
        skip=skip,
        limit=limit
    )
    
    return [FileListResponse.model_validate(f) for f in files]


@router.get(
    "/shared",
    response_model=List[FileListResponse],
    summary="List files shared with me"
)
async def list_shared_files(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get list of files shared with current user.
    """
    file_service = FileService(db)
    files = file_service.get_shared_files(
        user_id=current_user.id,
        skip=skip,
        limit=limit
    )
    
    return [FileListResponse.model_validate(f) for f in files]


@router.get(
    "/all",
    response_model=List[FileListResponse],
    summary="List all files (Admin only)"
)
async def list_all_files(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Get list of all files in the system.
    
    **Admin only endpoint.**
    """
    file_service = FileService(db)
    files = file_service.get_all_files(skip=skip, limit=limit)
    
    return [FileListResponse.model_validate(f) for f in files]


@router.get(
    "/stats",
    response_model=FileStats,
    summary="Get file statistics"
)
async def get_file_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get file statistics for current user.
    """
    file_service = FileService(db)
    
    files = file_service.get_user_files(user_id=current_user.id, limit=1000)
    total_size = sum(f.size for f in files)
    
    shared_files = file_service.get_shared_files(user_id=current_user.id, limit=1000)
    
    return FileStats(
        total_files=len(files),
        total_size=total_size,
        total_shared=len(shared_files)
    )


@router.get(
    "/{file_id}",
    response_model=FileResponse,
    summary="Get file details"
)
async def get_file(
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get file details by ID.
    """
    file_service = FileService(db)
    file_record = file_service.get_file_by_id(file_id)
    
    if not file_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    # Check access
    if file_record.owner_id != current_user.id:
        if not current_user.role or current_user.role.name != "admin":
            # Check permissions
            permissions = file_service.get_file_permissions(file_id)
            has_access = any(p.user_id == current_user.id for p in permissions)
            if not has_access:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have access to this file"
                )
    
    response = FileResponse.model_validate(file_record)
    response.owner_email = file_record.owner.email if file_record.owner else None
    return response


@router.get(
    "/{file_id}/download",
    summary="Download a file"
)
async def download_file(
    file_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Download a file by ID.
    
    Streams file directly from S3 through the backend.
    """
    file_service = FileService(db)
    file_stream, filename, content_type = file_service.download_file(
        file_id=file_id,
        user=current_user,
        request=request
    )
    
    return StreamingResponse(
        file_stream,
        media_type=content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )


@router.put(
    "/{file_id}",
    response_model=FileResponse,
    summary="Update file metadata"
)
async def update_file(
    file_id: int,
    file_data: FileUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update file metadata (filename, description).
    """
    file_service = FileService(db)
    file_record = file_service.update_file(
        file_id=file_id,
        file_data=file_data,
        user=current_user,
        request=request
    )
    
    return FileResponse.model_validate(file_record)


@router.delete(
    "/{file_id}",
    response_model=MessageResponse,
    summary="Delete a file"
)
async def delete_file(
    file_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a file (soft delete).
    """
    file_service = FileService(db)
    file_service.delete_file(
        file_id=file_id,
        user=current_user,
        request=request
    )
    
    return MessageResponse(message="File deleted successfully")


# ============ File Permissions ============

@router.post(
    "/{file_id}/permissions",
    response_model=FilePermissionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Grant file permission"
)
async def grant_permission(
    file_id: int,
    permission_data: FilePermissionCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Grant permission on a file to another user.
    
    - **user_id**: User to grant access to
    - **permission_level**: read, write, or admin
    - **can_download**: Allow downloads
    - **can_share**: Allow re-sharing
    """
    file_service = FileService(db)
    permission = file_service.grant_permission(
        file_id=file_id,
        permission_data=permission_data,
        granting_user=current_user,
        request=request
    )
    
    response = FilePermissionResponse.model_validate(permission)
    response.user_email = permission.user.email if permission.user else None
    return response


@router.get(
    "/{file_id}/permissions",
    response_model=List[FilePermissionResponse],
    summary="List file permissions"
)
async def list_permissions(
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all permissions for a file.
    """
    file_service = FileService(db)
    file_record = file_service.get_file_by_id(file_id)
    
    if not file_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    # Check ownership
    if file_record.owner_id != current_user.id:
        if not current_user.role or current_user.role.name != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view file permissions"
            )
    
    permissions = file_service.get_file_permissions(file_id)
    
    return [
        FilePermissionResponse(
            id=p.id,
            file_id=p.file_id,
            user_id=p.user_id,
            user_email=p.user.email if p.user else None,
            permission_level=p.permission_level,
            can_download=p.can_download,
            can_share=p.can_share,
            granted_by_id=p.granted_by_id,
            created_at=p.created_at
        )
        for p in permissions
    ]


@router.delete(
    "/{file_id}/permissions/{user_id}",
    response_model=MessageResponse,
    summary="Revoke file permission"
)
async def revoke_permission(
    file_id: int,
    user_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Revoke permission from a user for a file.
    """
    file_service = FileService(db)
    file_service.revoke_permission(
        file_id=file_id,
        user_id=user_id,
        revoking_user=current_user,
        request=request
    )
    
    return MessageResponse(message="Permission revoked successfully")
