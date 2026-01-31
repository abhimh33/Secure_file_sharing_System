"""
Health Check API Endpoint
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.database import get_db
from app.core.redis import redis_client
from app.core.config import settings
from app.schemas.common import HealthCheck

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthCheck,
    summary="Health check"
)
async def health_check():
    """
    Check application health status.
    """
    return HealthCheck(
        status="healthy",
        version=settings.APP_VERSION,
        timestamp=datetime.utcnow()
    )


@router.get(
    "/health/detailed",
    summary="Detailed health check"
)
async def detailed_health_check(
    db: Session = Depends(get_db)
):
    """
    Detailed health check including database and Redis connectivity.
    """
    health = {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "timestamp": datetime.utcnow().isoformat(),
        "services": {}
    }
    
    # Check database
    try:
        db.execute("SELECT 1")
        health["services"]["database"] = {"status": "healthy"}
    except Exception as e:
        health["services"]["database"] = {"status": "unhealthy", "error": str(e)}
        health["status"] = "degraded"
    
    # Check Redis
    try:
        redis_client.client.ping()
        health["services"]["redis"] = {"status": "healthy"}
    except Exception as e:
        health["services"]["redis"] = {"status": "unhealthy", "error": str(e)}
        health["status"] = "degraded"
    
    return health
