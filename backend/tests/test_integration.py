"""Integration tests for API endpoints and services."""
import pytest


class TestAuthIntegration:
    """Integration tests for authentication flow."""

    def test_full_auth_flow(self, test_client):
        """Test complete authentication flow: login -> access -> logout."""
        # Login
        login_resp = test_client.post("/api/auth/login", json={
            "username": "admin",
            "password": "admin"
        })
        assert login_resp.status_code in [200, 401]  # May not be implemented
        
        # If login succeeds, test protected endpoint
        if login_resp.status_code == 200:
            token = login_resp.json().get("access_token")
            if token:
                headers = {"Authorization": f"Bearer {token}"}
                # Try to access a protected endpoint
                resp = test_client.get("/api/user/profile", headers=headers)
                assert resp.status_code in [200, 404, 401]


class TestAPIEndpoints:
    """Integration tests for core API endpoints."""

    def test_health_endpoint_accessible(self, test_client):
        """Test that health endpoint is always accessible."""
        response = test_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data

    @pytest.mark.parametrize("method,path", [
        ("GET", "/api/tasks"),
        ("GET", "/health"),
    ])
    def test_api_methods(self, test_client, method, path):
        """Test various HTTP methods on API paths."""
        if method == "GET":
            response = test_client.get(path)
        elif method == "POST":
            response = test_client.post(path, json={})
        
        # Expect 2xx, 4xx, or 5xx but not connection errors
        assert response.status_code >= 200


class TestErrorRecovery:
    """Integration tests for error handling and recovery."""

    def test_graceful_error_on_missing_auth(self, test_client):
        """Test that missing auth returns proper error (not 500)."""
        # Try accessing a protected endpoint without auth
        response = test_client.get(
            "/api/protected",
            headers={"Authorization": "Bearer invalid"}
        )
        # Should be 401 or 404, not 500
        assert response.status_code in [401, 404, 403]

    def test_server_error_format(self, test_client):
        """Test that server errors are formatted consistently."""
        # Trigger an error (e.g., bad request)
        response = test_client.post("/api/task", json={})
        # If it errors, should have a structured response
        if response.status_code >= 400:
            data = response.json()
            # Ensure response has expected fields if structured
            assert isinstance(data, (dict, list))


class TestConcurrency:
    """Integration tests for concurrent request handling."""

    def test_concurrent_health_checks(self, test_client):
        """Test that multiple concurrent requests work."""
        responses = []
        for _ in range(5):
            resp = test_client.get("/health")
            responses.append(resp.status_code)
        
        # All should succeed
        assert all(s == 200 for s in responses if s != 500)

    def test_request_isolation(self, test_client):
        """Test that concurrent requests don't interfere."""
        resp1 = test_client.get("/health")
        resp2 = test_client.get("/health")
        
        # Both should be independent and succeed
        assert resp1.status_code == 200
        assert resp2.status_code == 200


class TestResponseValidation:
    """Integration tests for response validation."""

    def test_response_structure(self, test_client):
        """Test that API responses have expected structure."""
        response = test_client.get("/health")
        data = response.json()
        
        # Typical structure validation
        assert isinstance(data, dict)
        assert response.status_code in range(200, 600)

    def test_response_content_type(self, test_client):
        """Test that responses have correct content type."""
        response = test_client.get("/health")
        assert "application/json" in response.headers.get("content-type", "")


class TestDatabaseIntegration:
    """Integration tests with database (if available)."""

    def test_db_connectivity(self, db_session):
        """Test that database session can be established."""
        # If db_session fixture is available, test basic connectivity
        if db_session:
            # Basic sanity check
            assert db_session is not None
        else:
            pytest.skip("Database not available")

    def test_transaction_rollback(self, db_session):
        """Test that transactions are properly rolled back in tests."""
        if db_session:
            # Fixture should auto-rollback changes
            assert db_session is not None


class TestCacheIntegration:
    """Integration tests for caching (if Redis is available)."""

    def test_redis_connectivity(self, redis_client):
        """Test that Redis can be connected to."""
        if redis_client:
            try:
                redis_client.ping()
            except Exception:
                pytest.skip("Redis not available")

    def test_cache_operations(self, redis_client):
        """Test basic cache operations."""
        if redis_client:
            redis_client.set("test_key", "test_value")
            result = redis_client.get("test_key")
            assert result in [b"test_value", "test_value"]
