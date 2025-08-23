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
