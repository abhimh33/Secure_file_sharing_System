"""
Audit Log API Tests
"""

import pytest


class TestAuditEndpoints:
    """Test audit log endpoints"""
    
    def test_get_audit_logs_as_admin(self, client, admin_token):
        """Test getting audit logs as admin"""
        response = client.get(
            "/api/v1/audit/",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
    
    def test_get_audit_logs_as_user_forbidden(self, client, user_token):
        """Test that regular user cannot access audit logs"""
        response = client.get(
            "/api/v1/audit/",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 403
    
    def test_get_my_activity(self, client, user_token):
        """Test getting own activity log"""
        response = client.get(
            "/api/v1/audit/my-activity",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_get_file_audit_history_as_admin(self, client, admin_token):
        """Test getting file audit history as admin"""
        response = client.get(
            "/api/v1/audit/file/1",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_get_file_audit_history_as_user_forbidden(self, client, user_token):
        """Test that regular user cannot access file audit history"""
        response = client.get(
            "/api/v1/audit/file/1",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 403
    
    def test_get_user_audit_history_as_admin(self, client, admin_token, test_user):
        """Test getting user audit history as admin"""
        response = client.get(
            f"/api/v1/audit/user/{test_user.id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_audit_logs_with_filters(self, client, admin_token):
        """Test filtering audit logs"""
        response = client.get(
            "/api/v1/audit/?action=login_success&status=success",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
