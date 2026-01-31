"""
API Endpoint Testing Script
Tests all endpoints of the Secure File Sharing System
"""

import httpx
import json
import os
import tempfile

BASE_URL = "http://localhost:8001/api/v1"

# Test results tracking
results = []

def log_result(endpoint: str, method: str, status: int, success: bool, message: str = ""):
    emoji = "✅" if success else "❌"
    results.append({
        "endpoint": endpoint,
        "method": method,
        "status": status,
        "success": success,
        "message": message
    })
    print(f"{emoji} [{method}] {endpoint} - Status: {status} {message}")

def test_health_endpoints(client: httpx.Client):
    """Test health check endpoints"""
    print("\n" + "="*50)
    print("🏥 TESTING HEALTH ENDPOINTS")
    print("="*50)
    
    # Test basic health (follow redirects)
    response = client.get(f"{BASE_URL}/health/", follow_redirects=True)
    log_result("/health/", "GET", response.status_code, response.status_code == 200)
    
    # Test detailed health
    response = client.get(f"{BASE_URL}/health/detailed")
    log_result("/health/detailed", "GET", response.status_code, response.status_code == 200)

def test_auth_endpoints(client: httpx.Client) -> str | None:
    """Test authentication endpoints and return access token"""
    print("\n" + "="*50)
    print("🔐 TESTING AUTH ENDPOINTS")
    print("="*50)
    
    # Test register (new user)
    register_data = {
        "email": "testuser@example.com",
        "password": "TestPass123!@#",
        "full_name": "Test User"
    }
    response = client.post(f"{BASE_URL}/auth/register", json=register_data)
    # 201 = created, 400 = already exists (both are valid)
    success = response.status_code in [201, 400]
    log_result("/auth/register", "POST", response.status_code, success, 
               "(new user or already exists)")
    
    # Test login with admin - use JSON body with email field
    login_data = {
        "email": "admin@securefile.com",
        "password": "AbhiMH33"
    }
    response = client.post(
        f"{BASE_URL}/auth/login",
        json=login_data
    )
    success = response.status_code == 200
    log_result("/auth/login", "POST", response.status_code, success)
    
    if not success:
        print(f"   Login error: {response.text}")
    
    access_token = None
    if success:
        token_data = response.json()
        # Tokens are nested under "tokens" key
        tokens = token_data.get("tokens", {})
        access_token = tokens.get("access_token")
        refresh_token = tokens.get("refresh_token")
        
        print(f"   Token received: {access_token[:20]}..." if access_token else "   No token received!")
        
        # Test refresh token
        if refresh_token:
            refresh_response = client.post(
                f"{BASE_URL}/auth/refresh",
                json={"refresh_token": refresh_token}
            )
            log_result("/auth/refresh", "POST", refresh_response.status_code, 
                      refresh_response.status_code == 200)
    
    # Test /auth/me
    if access_token:
        response = client.get(
            f"{BASE_URL}/auth/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        log_result("/auth/me", "GET", response.status_code, response.status_code == 200)
    
    return access_token

def test_user_endpoints(client: httpx.Client, token: str):
    """Test user management endpoints"""
    print("\n" + "="*50)
    print("👤 TESTING USER ENDPOINTS")
    print("="*50)
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get all users (admin only)
    response = client.get(f"{BASE_URL}/users/", headers=headers)
    log_result("/users/", "GET", response.status_code, response.status_code == 200)
    
    # Get user by ID
    response = client.get(f"{BASE_URL}/users/1", headers=headers)
    log_result("/users/1", "GET", response.status_code, response.status_code == 200)
    
    # Update current user (PUT /users/me)
    update_data = {"full_name": "Updated Admin Name"}
    response = client.put(f"{BASE_URL}/users/me", json=update_data, headers=headers)
    log_result("/users/me", "PUT", response.status_code, response.status_code == 200)
    
    # Get roles list
    response = client.get(f"{BASE_URL}/users/roles/list", headers=headers)
    log_result("/users/roles/list", "GET", response.status_code, response.status_code == 200)

def test_file_endpoints(client: httpx.Client, token: str) -> int | None:
    """Test file management endpoints"""
    print("\n" + "="*50)
    print("📁 TESTING FILE ENDPOINTS")
    print("="*50)
    
    headers = {"Authorization": f"Bearer {token}"}
    file_id = None
    
    # Create a temp file for upload testing
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("This is a test file for the Secure File Sharing System.")
        temp_file_path = f.name
    
    try:
        # Upload file
        with open(temp_file_path, 'rb') as f:
            files = {'file': ('test_document.txt', f, 'text/plain')}
            response = client.post(
                f"{BASE_URL}/files/upload",
                files=files,
                headers=headers
            )
            success = response.status_code in [201, 200]
            log_result("/files/upload", "POST", response.status_code, success)
            
            if success:
                file_data = response.json()
                file_id = file_data.get("id")
        
        # List files
        response = client.get(f"{BASE_URL}/files/", headers=headers)
        log_result("/files/", "GET", response.status_code, response.status_code == 200)
        
        # Get file by ID
        if file_id:
            response = client.get(f"{BASE_URL}/files/{file_id}", headers=headers)
            log_result(f"/files/{file_id}", "GET", response.status_code, 
                      response.status_code == 200)
            
            # Download file
            response = client.get(f"{BASE_URL}/files/{file_id}/download", headers=headers)
            log_result(f"/files/{file_id}/download", "GET", response.status_code, 
                      response.status_code == 200)
    
    finally:
        # Cleanup temp file
        os.unlink(temp_file_path)
    
    return file_id

def test_share_endpoints(client: httpx.Client, token: str, file_id: int | None):
    """Test share link endpoints"""
    print("\n" + "="*50)
    print("🔗 TESTING SHARE ENDPOINTS")
    print("="*50)
    
    headers = {"Authorization": f"Bearer {token}"}
    share_token = None
    
    if file_id:
        # Create share link - use expiry_minutes not expires_in_hours
        share_data = {
            "file_id": file_id,
            "expiry_minutes": 1440,  # 24 hours = 1440 minutes
            "max_downloads": 10
        }
        response = client.post(f"{BASE_URL}/share/", json=share_data, headers=headers)
        success = response.status_code in [201, 200]
        log_result("/share/", "POST", response.status_code, success)
        
        if not success:
            print(f"   Share error: {response.text}")
        
        if success:
            share_response = response.json()
            share_token = share_response.get("token")
        
        # List my share links
        if share_token:
            response = client.get(f"{BASE_URL}/share/", headers=headers)
            log_result(f"/share/", "GET", response.status_code, 
                      response.status_code == 200)
            
            # Download via share token
            response = client.get(f"{BASE_URL}/share/{share_token}/download")
            log_result(f"/share/{{token}}/download", "GET", response.status_code, 
                      response.status_code == 200)
            
            # Get share link info
            response = client.get(f"{BASE_URL}/share/{share_token}/info")
            log_result(f"/share/{{token}}/info", "GET", response.status_code, 
                      response.status_code == 200)
    else:
        print("⚠️ Skipping share tests - no file_id available")

def test_audit_endpoints(client: httpx.Client, token: str):
    """Test audit log endpoints"""
    print("\n" + "="*50)
    print("📋 TESTING AUDIT ENDPOINTS")
    print("="*50)
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get audit logs (admin only)
    response = client.get(f"{BASE_URL}/audit/", headers=headers)
    log_result("/audit/", "GET", response.status_code, response.status_code == 200)
    
    # Get audit logs with filters
    response = client.get(f"{BASE_URL}/audit/?limit=10", headers=headers)
    log_result("/audit/?limit=10", "GET", response.status_code, response.status_code == 200)

def print_summary():
    """Print test summary"""
    print("\n" + "="*50)
    print("📊 TEST SUMMARY")
    print("="*50)
    
    total = len(results)
    passed = sum(1 for r in results if r["success"])
    failed = total - passed
    
    print(f"\nTotal Tests: {total}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    if failed > 0:
        print("\n❌ Failed Tests:")
        for r in results:
            if not r["success"]:
                print(f"   - [{r['method']}] {r['endpoint']} (Status: {r['status']})")

def main():
    print("🚀 Starting API Endpoint Tests")
    print("="*50)
    
    with httpx.Client(timeout=30.0) as client:
        # Test health endpoints
        test_health_endpoints(client)
        
        # Test auth and get token
        token = test_auth_endpoints(client)
        
        if token:
            # Test user endpoints
            test_user_endpoints(client, token)
            
            # Test file endpoints
            file_id = test_file_endpoints(client, token)
            
            # Test share endpoints
            test_share_endpoints(client, token, file_id)
            
            # Test audit endpoints
            test_audit_endpoints(client, token)
        else:
            print("\n❌ Cannot proceed with tests - authentication failed")
    
    # Print summary
    print_summary()

if __name__ == "__main__":
    main()
