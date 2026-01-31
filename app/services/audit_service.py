"""
Audit Log Service
Business logic for audit logging
"""

import json
from datetime import datetime
from sqlalchemy.orm import Session
from typing import Optional, List
from fastapi import Request

from app.models.audit_log import AuditLog, AuditAction


class AuditService:
    """Service for audit logging operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def log(
        self,
        action: AuditAction,
        user_id: Optional[int] = None,
        user_email: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[int] = None,
        details: Optional[str] = None,
        status: str = "success",
        request: Optional[Request] = None
    ) -> AuditLog:
        """
        Create an audit log entry
        
        Args:
            action: The action being logged
            user_id: ID of user performing action
            user_email: Email of user (for persistence if user deleted)
            resource_type: Type of resource affected
            resource_id: ID of resource affected
            details: Additional details (JSON string)
            status: success/failed/error
            request: FastAPI request object for IP/user-agent
        """
        # Extract request info
        ip_address = None
        user_agent = None
        
        if request:
            # Get client IP
            if request.client:
                ip_address = request.client.host
            # Check for forwarded IP (behind proxy)
            forwarded = request.headers.get("X-Forwarded-For")
            if forwarded:
                ip_address = forwarded.split(",")[0].strip()
            
            user_agent = request.headers.get("User-Agent", "")[:500]
        
        # Create audit log entry
        audit_log = AuditLog(
            user_id=user_id,
            user_email=user_email,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
            status=status
        )
        
        self.db.add(audit_log)
        self.db.commit()
        self.db.refresh(audit_log)
        
        return audit_log
    
    def get_logs(
        self,
        user_id: Optional[int] = None,
        action: Optional[AuditAction] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[AuditLog]:
        """Get audit logs with filters"""
        query = self.db.query(AuditLog)
        
        if user_id:
            query = query.filter(AuditLog.user_id == user_id)
        if action:
            query = query.filter(AuditLog.action == action)
        if resource_type:
            query = query.filter(AuditLog.resource_type == resource_type)
        if resource_id:
            query = query.filter(AuditLog.resource_id == resource_id)
        if start_date:
            query = query.filter(AuditLog.created_at >= start_date)
        if end_date:
            query = query.filter(AuditLog.created_at <= end_date)
        if status:
            query = query.filter(AuditLog.status == status)
        
        return query.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit).all()
    
    def get_logs_count(
        self,
        user_id: Optional[int] = None,
        action: Optional[AuditAction] = None,
        resource_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> int:
        """Get total count of audit logs with filters"""
        query = self.db.query(AuditLog)
        
        if user_id:
            query = query.filter(AuditLog.user_id == user_id)
        if action:
            query = query.filter(AuditLog.action == action)
        if resource_type:
            query = query.filter(AuditLog.resource_type == resource_type)
        if start_date:
            query = query.filter(AuditLog.created_at >= start_date)
        if end_date:
            query = query.filter(AuditLog.created_at <= end_date)
        
        return query.count()
    
    def get_user_activity(
        self,
        user_id: int,
        limit: int = 50
    ) -> List[AuditLog]:
        """Get recent activity for a specific user"""
        return self.db.query(AuditLog).filter(
            AuditLog.user_id == user_id
        ).order_by(AuditLog.created_at.desc()).limit(limit).all()
    
    def get_file_history(
        self,
        file_id: int
    ) -> List[AuditLog]:
        """Get audit history for a specific file"""
        return self.db.query(AuditLog).filter(
            AuditLog.resource_type == "file",
            AuditLog.resource_id == file_id
        ).order_by(AuditLog.created_at.desc()).all()


def get_audit_service(db: Session) -> AuditService:
    """Factory function for AuditService"""
    return AuditService(db)
