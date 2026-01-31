"""
Audit Log API Endpoints
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.core.database import get_db
from app.schemas.audit import AuditLogResponse, AuditLogListResponse, AuditAction
from app.services.audit_service import AuditService
from app.security.dependencies import require_admin, get_current_user
from app.models.user import User
from app.models.audit_log import AuditAction as AuditActionModel

router = APIRouter(prefix="/audit", tags=["Audit Logs"])


@router.get(
    "/",
    response_model=AuditLogListResponse,
    summary="Get audit logs (Admin only)"
)
async def get_audit_logs(
    user_id: Optional[int] = None,
    action: Optional[AuditAction] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    status: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Get audit logs with filters.
    
    **Admin only endpoint.**
    
    - **user_id**: Filter by user
    - **action**: Filter by action type
    - **resource_type**: Filter by resource type (file, user, share_link)
    - **resource_id**: Filter by specific resource ID
    - **start_date**: Filter from date
    - **end_date**: Filter to date
    - **status**: Filter by status (success, failed, error)
    """
    audit_service = AuditService(db)
    
    # Convert schema action to model action if provided
    model_action = None
    if action:
        model_action = AuditActionModel(action.value)
    
    logs = audit_service.get_logs(
        user_id=user_id,
        action=model_action,
        resource_type=resource_type,
        resource_id=resource_id,
        start_date=start_date,
        end_date=end_date,
        status=status,
        skip=skip,
        limit=limit
    )
    
    total = audit_service.get_logs_count(
        user_id=user_id,
        action=model_action,
        resource_type=resource_type,
        start_date=start_date,
        end_date=end_date
    )
    
    return AuditLogListResponse(
        items=[AuditLogResponse.model_validate(log) for log in logs],
        total=total,
        page=skip // limit + 1 if limit > 0 else 1,
        size=limit
    )


@router.get(
    "/my-activity",
    response_model=List[AuditLogResponse],
    summary="Get my activity log"
)
async def get_my_activity(
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current user's recent activity log.
    """
    audit_service = AuditService(db)
    logs = audit_service.get_user_activity(
        user_id=current_user.id,
        limit=limit
    )
    
    return [AuditLogResponse.model_validate(log) for log in logs]


@router.get(
    "/file/{file_id}",
    response_model=List[AuditLogResponse],
    summary="Get file audit history"
)
async def get_file_audit_history(
    file_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Get complete audit history for a specific file.
    
    **Admin only endpoint.**
    """
    audit_service = AuditService(db)
    logs = audit_service.get_file_history(file_id)
    
    return [AuditLogResponse.model_validate(log) for log in logs]


@router.get(
    "/user/{user_id}",
    response_model=List[AuditLogResponse],
    summary="Get user audit history (Admin only)"
)
async def get_user_audit_history(
    user_id: int,
    limit: int = Query(100, ge=1, le=500),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Get audit history for a specific user.
    
    **Admin only endpoint.**
    """
    audit_service = AuditService(db)
    logs = audit_service.get_user_activity(
        user_id=user_id,
        limit=limit
    )
    
    return [AuditLogResponse.model_validate(log) for log in logs]
