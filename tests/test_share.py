"""
Share Link API Tests
"""

import pytest
from unittest.mock import patch, MagicMock


class TestShareEndpoints:
    """Test share link endpoints"""
    
    def test_list_my_share_links(self, client, user_token):
        """Test listing user's share links"""
        response = client.get(
            "/api/v1/share/",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_create_share_link_nonexistent_file(self, client, user_token):
        """Test creating share link for non-existent file"""
        response = client.post(
            "/api/v1/share/",
            json={
                "file_id": 99999,
                "expiry_minutes": 60
            },
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 404
    
    def test_get_share_link_info_invalid_token(self, client):
        """Test getting info for invalid share link"""
        response = client.get("/api/v1/share/invalidtoken123/info")
        assert response.status_code == 404
    
    def test_download_invalid_share_link(self, client):
        """Test downloading via invalid share link"""
        response = client.get("/api/v1/share/invalidtoken123/download")
        assert response.status_code == 404
    
    def test_revoke_nonexistent_share_link(self, client, user_token):
        """Test revoking non-existent share link"""
        response = client.delete(
            "/api/v1/share/invalidtoken123",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 404
    
    def test_create_share_link_invalid_expiry(self, client, user_token):
        """Test creating share link with invalid expiry"""
        response = client.post(
            "/api/v1/share/",
            json={
                "file_id": 1,
                "expiry_minutes": 0  # Invalid
            },
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 422
    
    def test_create_share_link_expiry_too_long(self, client, user_token):
        """Test creating share link with expiry > 30 days"""
        response = client.post(
            "/api/v1/share/",
            json={
                "file_id": 1,
                "expiry_minutes": 50000  # > 30 days
            },
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 422
