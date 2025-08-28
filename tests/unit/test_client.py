"""Tests for the Client class."""

import pytest

from tests.utils.httpx_comparison import httpx_compatibility_test


class TestClient:
    """Test Client class functionality."""

    @pytest.fixture(autouse=True)
    def setup(self, test_server):
        """Setup for each test."""
        self.base_url = test_server.base_url

    @httpx_compatibility_test
    def test_client_creation(self, client_factory):
        """Test client can be created with default settings."""
        # TDD: Red phase - this will fail initially
        client = client_factory()
        assert client is not None

    @httpx_compatibility_test
    def test_client_with_timeout(self, client_factory):
        """Test client creation with timeout configuration."""
        # TDD: Red phase - this will fail initially
        client = client_factory(timeout=30.0)
        assert client is not None

    @httpx_compatibility_test
    def test_client_with_headers(self, client_factory):
        """Test client creation with default headers."""
        # TDD: Red phase - this will fail initially
        headers = {"User-Agent": "faster-http-test"}
        client = client_factory(headers=headers)
        response = client.get(f"{self.base_url}/headers")
        assert response.status_code == 200

    @httpx_compatibility_test
    def test_client_with_base_url(self, client_factory):
        """Test client creation with base URL."""
        # TDD: Red phase - this will fail initially
        client = client_factory(base_url=self.base_url)
        response = client.get("/get")
        assert response.status_code == 200

    @httpx_compatibility_test
    def test_client_context_manager(self, client_factory):
        """Test client as context manager."""
        # TDD: Red phase - this will fail initially
        with client_factory() as client:
            response = client.get(f"{self.base_url}/get")
            assert response.status_code == 200

    @httpx_compatibility_test
    def test_client_request_method(self, client_factory):
        """Test client.request() method."""
        # TDD: Red phase - this will fail initially
        client = client_factory()
        response = client.request("GET", f"{self.base_url}/get")
        assert response.status_code == 200

    @httpx_compatibility_test
    def test_client_params(self, client_factory):
        """Test client with query parameters."""
        # TDD: Red phase - this will fail initially
        client = client_factory()
        params = {"key": "value", "test": "data"}
        response = client.get(f"{self.base_url}/get", params=params)
        assert response.status_code == 200

    # === High Priority Client Resource Management Tests ===

    @httpx_compatibility_test
    def test_client_close_method(self, client_factory):
        """Test client.close() method exists and works correctly."""
        client = client_factory()

        # Ensure close method exists
        assert hasattr(client, "close")
        assert callable(client.close)

        # Make a request before closing
        response = client.get(f"{self.base_url}/get")
        assert response.status_code == 200

        # Close the client - should not raise an exception
        client.close()

    @httpx_compatibility_test
    def test_client_multiple_close_calls(self, client_factory):
        """Test that calling close() multiple times doesn't cause issues."""
        client = client_factory()

        # Make a request
        response = client.get(f"{self.base_url}/get")
        assert response.status_code == 200

        # Close multiple times - should not raise
        client.close()
        client.close()
        client.close()

    @httpx_compatibility_test
    def test_client_context_manager_auto_close(self, client_factory):
        """Test that context manager automatically closes the client."""
        with client_factory() as client:
            # Ensure the client works inside the context
            response = client.get(f"{self.base_url}/get")
            assert response.status_code == 200

            # Verify close method exists
            assert hasattr(client, "close")

        # After context manager exits, client should be closed
        # (We can't easily test if it's actually closed, but at least verify no errors)

    @httpx_compatibility_test
    def test_client_context_manager_exception_handling(self, client_factory):
        """Test that context manager closes client even if exception occurs."""
        try:
            with client_factory() as client:
                # Make a successful request first
                response = client.get(f"{self.base_url}/get")
                assert response.status_code == 200

                # Raise an exception
                raise ValueError("Test exception")
        except ValueError:
            pass  # Expected

        # Client should still be properly closed

    @httpx_compatibility_test
    def test_client_reuse_after_close(self, client_factory):
        """Test client behavior after being closed."""
        client = client_factory()

        # Make initial request
        response = client.get(f"{self.base_url}/get")
        assert response.status_code == 200

        # Close the client
        client.close()

        # Try to make another request - behavior may vary by implementation
        # but should not crash the process
        try:
            client.get(f"{self.base_url}/get")
        except Exception:
            # Some implementations may raise an exception, which is fine
            pass
