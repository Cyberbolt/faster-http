"""Tests for the AsyncClient class."""

import pytest

from tests.utils.httpx_comparison import httpx_compatibility_test


class TestAsyncClient:
    """Test AsyncClient class functionality."""

    @pytest.fixture(autouse=True)
    def setup(self, test_server):
        """Setup for each test."""
        self.base_url = test_server.base_url

    @httpx_compatibility_test
    async def test_async_client_creation(self, async_client_factory):
        """Test async client can be created with default settings."""
        # TDD: Red phase - this will fail initially
        client = async_client_factory()
        assert client is not None

    @httpx_compatibility_test
    async def test_async_client_get(self, async_client_factory):
        """Test async client GET request."""
        # TDD: Red phase - this will fail initially
        async with async_client_factory() as client:
            response = await client.get(f"{self.base_url}/get")
            assert response.status_code == 200

    @httpx_compatibility_test
    async def test_async_client_post(self, async_client_factory):
        """Test async client POST request."""
        # TDD: Red phase - this will fail initially
        async with async_client_factory() as client:
            response = await client.post(f"{self.base_url}/post", json={"test": "data"})
            assert response.status_code == 200

    @httpx_compatibility_test
    async def test_async_client_with_timeout(self, async_client_factory):
        """Test async client with timeout configuration."""
        # TDD: Red phase - this will fail initially
        async with async_client_factory(timeout=30.0) as client:
            response = await client.get(f"{self.base_url}/get")
            assert response.status_code == 200

    @httpx_compatibility_test
    async def test_async_client_with_headers(self, async_client_factory):
        """Test async client with default headers."""
        # TDD: Red phase - this will fail initially
        headers = {"User-Agent": "faster-http-test"}
        async with async_client_factory(headers=headers) as client:
            response = await client.get(f"{self.base_url}/headers")
            assert response.status_code == 200

    @httpx_compatibility_test
    async def test_async_client_with_base_url(self, async_client_factory):
        """Test async client with base URL."""
        # TDD: Red phase - this will fail initially
        async with async_client_factory(base_url=self.base_url) as client:
            response = await client.get("/get")
            assert response.status_code == 200

    @httpx_compatibility_test
    async def test_async_client_request_method(self, async_client_factory):
        """Test async client.request() method."""
        # TDD: Red phase - this will fail initially
        async with async_client_factory() as client:
            response = await client.request("GET", f"{self.base_url}/get")
            assert response.status_code == 200

    @httpx_compatibility_test
    async def test_async_client_params(self, async_client_factory):
        """Test async client with query parameters."""
        # TDD: Red phase - this will fail initially
        async with async_client_factory() as client:
            params = {"key": "value", "test": "data"}
            response = await client.get(f"{self.base_url}/get", params=params)
            assert response.status_code == 200
