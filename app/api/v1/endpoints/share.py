"""
Share Link API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.core.s3 import s3_service
from app.schemas.share import (
    ShareLinkCreate,
    ShareLinkResponse,
    ShareLinkInfo,
    ShareLinkListResponse
)
from app.schemas.common import MessageResponse
from app.services.share_service import ShareLinkService
from app.services.audit_service import AuditService
from app.security.dependencies import get_current_user, require_user
from app.models.user import User
from app.models.audit_log import AuditAction

router = APIRouter(prefix="/share", tags=["Share Links"])


@router.post(
    "/",
    response_model=ShareLinkResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create share link"
)
async def create_share_link(
    link_data: ShareLinkCreate,
    request: Request,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db)
):
    """
    Create an expiring share link for a file.
    
    - **file_id**: ID of file to share
    - **expiry_minutes**: Link expiration time (1 min to 30 days)
    - **max_downloads**: Optional download limit
    - **requires_auth**: Require authentication to access
    - **allowed_email**: Restrict access to specific email
    
    Share link data is stored in Redis with TTL.
    """
    share_service = ShareLinkService(db)
    result = share_service.create_share_link(
        link_data=link_data,
        user=current_user,
        request=request
    )
    
    return ShareLinkResponse(**result)


@router.get(
    "/{token}/info",
    response_model=ShareLinkInfo,
    summary="Get share link info"
)
async def get_share_link_info(
    token: str,
    db: Session = Depends(get_db)
):
    """
    Get information about a share link.
    
    Returns file details and link validity status.
    Does not require authentication.
    """
    share_service = ShareLinkService(db)
    return share_service.get_share_link_info(token)


@router.get(
    "/{token}/download",
    summary="Download file via share link"
)
async def download_via_share_link(
    token: str,
    request: Request,
    password: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Download a file using a share link.
    
    - Validates link expiration (Redis TTL)
    - Checks download limits
    - Verifies password if required
    - Streams file through backend
    
    Authentication is optional unless link requires it.
    """
    share_service = ShareLinkService(db)
    
    # Try to get current user (optional)
    current_user = None
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        from app.security.jwt import verify_access_token
        token_str = auth_header.split(" ")[1]
        payload = verify_access_token(token_str)
        if payload:
            user_id = payload.get("sub")
            if user_id:
                current_user = db.query(User).filter(User.id == int(user_id)).first()
    
    # Get file info via share link
    file_info = share_service.download_via_share_link(
        token=token,
        password=password,
        user=current_user,
        request=request
    )
    
    # Get file stream from S3
    file_stream = s3_service.get_file_stream(file_info["s3_key"])
    if not file_stream:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve file"
        )
    
    return StreamingResponse(
        file_stream,
        media_type=file_info["content_type"],
        headers={
            "Content-Disposition": f'attachment; filename="{file_info["filename"]}"'
        }
    )


@router.delete(
    "/{token}",
    response_model=MessageResponse,
    summary="Revoke share link"
)
async def revoke_share_link(
    token: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Revoke/delete a share link.
    
    Only the creator or admin can revoke a link.
    """
    share_service = ShareLinkService(db)
    share_service.revoke_share_link(
        token=token,
        user=current_user,
        request=request
    )
    
    return MessageResponse(message="Share link revoked successfully")


@router.get(
    "/",
    response_model=List[ShareLinkListResponse],
    summary="List my share links"
)
async def list_my_share_links(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all share links created by current user.
    """
    share_service = ShareLinkService(db)
    links = share_service.get_user_share_links(current_user.id)
    
    return [
        ShareLinkListResponse(
            id=link.id,
            token=link.token,
            file_id=link.file_id,
            filename=link.file.filename if link.file else "Unknown",
            expires_at=link.expires_at,
            is_active=link.is_active,
            download_count=link.download_count,
            max_downloads=link.max_downloads,
            created_at=link.created_at
        )
        for link in links
    ]
