"""
API v1 Router
Combines all endpoint routers
"""

from fastapi import APIRouter

from app.api.v1.endpoints import auth, users, files, share, audit, health

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(files.router)
api_router.include_router(share.router)
api_router.include_router(audit.router)
