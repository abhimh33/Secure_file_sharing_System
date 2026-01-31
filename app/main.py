"""
Secure File Sharing System - Main Application Entry Point
"""

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
import time

from app.core.config import settings
from app.core.database import engine, Base, SessionLocal
from app.core.redis import redis_client
from app.api.v1.router import api_router
from app.models.role import Role
from app.models.user import User
from app.security.password import hash_password


def init_roles(db):
    """Initialize default roles"""
    default_roles = [
        {"name": "admin", "description": "Administrator with full access"},
        {"name": "user", "description": "Regular user with file management access"},
        {"name": "viewer", "description": "Viewer with read-only access to shared files"}
    ]
    
    for role_data in default_roles:
        existing = db.query(Role).filter(Role.name == role_data["name"]).first()
        if not existing:
            role = Role(**role_data)
            db.add(role)
    
    db.commit()


def init_admin_user(db):
    """Initialize default admin user"""
    admin_email = settings.ADMIN_EMAIL
    admin = db.query(User).filter(User.email == admin_email).first()
    
    if not admin:
        admin_role = db.query(Role).filter(Role.name == "admin").first()
        admin = User(
            email=admin_email,
            hashed_password=hash_password(settings.ADMIN_PASSWORD),
            full_name="System Administrator",
            role_id=admin_role.id if admin_role else None,
            is_active=True,
            is_verified=True
        )
        db.add(admin)
        db.commit()
        print(f"✅ Default admin user created: {admin_email}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan events
    Runs on startup and shutdown
    """
    # Startup
    print("🚀 Starting Secure File Sharing System...")
    
    # Create database tables
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created")
    
    # Initialize roles and admin user
    db = SessionLocal()
    try:
        init_roles(db)
        print("✅ Default roles initialized")
        
        init_admin_user(db)
    finally:
        db.close()
    
    # Connect to Redis
    try:
        redis_client.connect()
        print("✅ Redis connected")
    except Exception as e:
        print(f"⚠️ Redis connection failed: {e}")
    
    print("✅ Application started successfully!")
    print(f"📚 API Docs: http://localhost:8000{settings.API_V1_PREFIX}/docs")
    
    yield
    
    # Shutdown
    print("🛑 Shutting down...")
    redis_client.close()
    print("✅ Cleanup completed")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
    🔒 **Secure File Sharing System**
    
    A production-ready secure file sharing platform with:
    
    - **JWT Authentication** (access + refresh tokens)
    - **Role-Based Access Control** (admin, user, viewer)
    - **Secure File Storage** (AWS S3 private buckets)
    - **Expiring Share Links** (Redis TTL)
    - **Complete Audit Logging**
    
    ## Security Features
    - All files stored in private S3 buckets
    - No direct S3 access - all downloads through backend
    - Rate limiting on all endpoints
    - Full audit trail of all actions
    
    ## Roles
    - **Admin**: Full system access
    - **User**: Upload, manage, share own files
    - **Viewer**: Download shared files only
    """,
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url=f"{settings.API_V1_PREFIX}/docs",
    redoc_url=f"{settings.API_V1_PREFIX}/redoc",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add processing time to response headers"""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors"""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation error",
            "errors": exc.errors()
        }
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors"""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An unexpected error occurred",
            "error": str(exc) if settings.DEBUG else "Internal server error"
        }
    )


# Include API router
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint - API information"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": f"{settings.API_V1_PREFIX}/docs",
        "health": f"{settings.API_V1_PREFIX}/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
