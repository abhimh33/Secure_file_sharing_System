"""
Authentication API Tests
"""

import pytest
from fastapi.testclient import TestClient


class TestAuthEndpoints:
    """Test authentication endpoints"""
    
    def test_register_success(self, client):
        """Test successful user registration"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "NewPassword123",
                "full_name": "New User"
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["message"] == "User registered successfully"
        assert "tokens" in data
        assert "access_token" in data["tokens"]
        assert "refresh_token" in data["tokens"]
    
    def test_register_duplicate_email(self, client, test_user):
        """Test registration with existing email"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "testuser@example.com",
                "password": "SomePassword123",
                "full_name": "Another User"
            }
        )
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]
    
    def test_register_weak_password(self, client):
        """Test registration with weak password"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "weak@example.com",
                "password": "weak",
                "full_name": "Weak Password User"
            }
        )
        assert response.status_code == 422
    
    def test_login_success(self, client, test_user):
        """Test successful login"""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "testuser@example.com",
                "password": "TestPassword123"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Login successful"
        assert "tokens" in data
    
    def test_login_wrong_password(self, client, test_user):
        """Test login with wrong password"""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "testuser@example.com",
                "password": "WrongPassword123"
            }
        )
        assert response.status_code == 401
    
    def test_login_nonexistent_user(self, client):
        """Test login with non-existent email"""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "noone@example.com",
                "password": "SomePassword123"
            }
        )
        assert response.status_code == 401
    
    def test_get_me(self, client, user_token):
        """Test get current user info"""
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "testuser@example.com"
    
    def test_get_me_unauthorized(self, client):
        """Test get me without token"""
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 403
    
    def test_refresh_token(self, client, test_user):
        """Test token refresh"""
        # First login to get refresh token
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "testuser@example.com",
                "password": "TestPassword123"
            }
        )
        refresh_token = login_response.json()["tokens"]["refresh_token"]
        
        # Use refresh token to get new tokens
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
    
    def test_logout(self, client, user_token):
        """Test logout"""
        response = client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 200
        assert response.json()["message"] == "Logged out successfully"
