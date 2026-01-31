"""
Test Configuration and Fixtures
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from app.core.database import Base, get_db
from app.models.role import Role
from app.models.user import User
from app.security.password import hash_password

# Test database URL (in-memory SQLite)
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    
    # Create default roles
    roles = [
        Role(name="admin", description="Administrator"),
        Role(name="user", description="Regular user"),
        Role(name="viewer", description="Viewer")
    ]
    for role in roles:
        db.add(role)
    db.commit()
    
    yield db
    
    db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with overridden database dependency"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db_session):
    """Create a test user"""
    user_role = db_session.query(Role).filter(Role.name == "user").first()
    user = User(
        email="testuser@example.com",
        hashed_password=hash_password("TestPassword123"),
        full_name="Test User",
        role_id=user_role.id,
        is_active=True,
        is_verified=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_admin(db_session):
    """Create a test admin user"""
    admin_role = db_session.query(Role).filter(Role.name == "admin").first()
    admin = User(
        email="admin@example.com",
        hashed_password=hash_password("AdminPassword123"),
        full_name="Test Admin",
        role_id=admin_role.id,
        is_active=True,
        is_verified=True
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)
    return admin


@pytest.fixture
def user_token(client, test_user):
    """Get auth token for test user"""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "testuser@example.com",
            "password": "TestPassword123"
        }
    )
    return response.json()["tokens"]["access_token"]


@pytest.fixture
def admin_token(client, test_admin):
    """Get auth token for test admin"""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "admin@example.com",
            "password": "AdminPassword123"
        }
    )
    return response.json()["tokens"]["access_token"]
