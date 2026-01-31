"""
User Management API Tests
"""

import pytest


class TestUserEndpoints:
    """Test user management endpoints"""
    
    def test_list_users_as_admin(self, client, admin_token, test_user):
        """Test listing users as admin"""
        response = client.get(
            "/api/v1/users/",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
    
    def test_list_users_as_regular_user(self, client, user_token):
        """Test that regular user cannot list users"""
        response = client.get(
            "/api/v1/users/",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 403
    
    def test_get_user_as_admin(self, client, admin_token, test_user):
        """Test getting specific user as admin"""
        response = client.get(
            f"/api/v1/users/{test_user.id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user.email
    
    def test_update_me(self, client, user_token):
        """Test updating current user's profile"""
        response = client.put(
            "/api/v1/users/me",
            json={"full_name": "Updated Name"},
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == "Updated Name"
    
    def test_change_password(self, client, user_token):
        """Test changing password"""
        response = client.post(
            "/api/v1/users/change-password",
            json={
                "current_password": "TestPassword123",
                "new_password": "NewPassword456"
            },
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 200
        assert response.json()["message"] == "Password changed successfully"
    
    def test_change_password_wrong_current(self, client, user_token):
        """Test changing password with wrong current password"""
        response = client.post(
            "/api/v1/users/change-password",
            json={
                "current_password": "WrongPassword",
                "new_password": "NewPassword456"
            },
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 400
    
    def test_assign_role(self, client, admin_token, test_user, db_session):
        """Test assigning role to user"""
        from app.models.role import Role
        admin_role = db_session.query(Role).filter(Role.name == "admin").first()
        
        response = client.put(
            f"/api/v1/users/{test_user.id}/role",
            json={"role_id": admin_role.id},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
    
    def test_deactivate_user(self, client, admin_token, test_user):
        """Test deactivating a user"""
        response = client.delete(
            f"/api/v1/users/{test_user.id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        assert response.json()["message"] == "User deactivated successfully"
    
    def test_list_roles(self, client, admin_token):
        """Test listing roles"""
        response = client.get(
            "/api/v1/users/roles/list",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 3  # admin, user, viewer
        role_names = [r["name"] for r in data]
        assert "admin" in role_names
        assert "user" in role_names
        assert "viewer" in role_names
