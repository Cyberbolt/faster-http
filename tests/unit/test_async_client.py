"""Tests for the AsyncClient class."""

import pytest

from tests.utils.httpx_comparison import httpx_compatibility_test


class TestAsyncClient:
    """Test AsyncClient class functionality."""

    @pytest.fixture(autouse=True)
    def setup(self, test_server):
        """Setup for each test."""
        self.base_url = test_server.base_url

    @pytest.mark.asyncio
    @httpx_compatibility_test
    async def test_async_client_creation(self, async_client_factory):
        """Test async client can be created with default settings."""
        # TDD: Red phase - this will fail initially
        client = async_client_factory()
        assert client is not None

    @pytest.mark.asyncio
    @httpx_compatibility_test
    async def test_async_client_get(self, async_client_factory):
        """Test async client GET request."""
        # TDD: Red phase - this will fail initially
        async with async_client_factory() as client:
            response = await client.get(f"{self.base_url}/get")
            assert response.status_code == 200

    @pytest.mark.asyncio
    @httpx_compatibility_test
    async def test_async_client_post(self, async_client_factory):
        """Test async client POST request."""
        # TDD: Red phase - this will fail initially
        async with async_client_factory() as client:
            response = await client.post(f"{self.base_url}/post", json={"test": "data"})
            assert response.status_code == 200

    @pytest.mark.asyncio
    @httpx_compatibility_test
    async def test_async_client_with_timeout(self, async_client_factory):
        """Test async client with timeout configuration."""
        # TDD: Red phase - this will fail initially
        async with async_client_factory(timeout=30.0) as client:
            response = await client.get(f"{self.base_url}/get")
            assert response.status_code == 200

    @pytest.mark.asyncio
    @httpx_compatibility_test
    async def test_async_client_with_headers(self, async_client_factory):
        """Test async client with default headers."""
        # TDD: Red phase - this will fail initially
        headers = {"User-Agent": "faster-http-test"}
        async with async_client_factory(headers=headers) as client:
            response = await client.get(f"{self.base_url}/headers")
            assert response.status_code == 200

    @pytest.mark.asyncio
    @httpx_compatibility_test
    async def test_async_client_with_base_url(self, async_client_factory):
        """Test async client with base URL."""
        # TDD: Red phase - this will fail initially
        async with async_client_factory(base_url=self.base_url) as client:
            response = await client.get("/get")
            assert response.status_code == 200

    @pytest.mark.asyncio
    @httpx_compatibility_test
    async def test_async_client_request_method(self, async_client_factory):
        """Test async client.request() method."""
        # TDD: Red phase - this will fail initially
        async with async_client_factory() as client:
            response = await client.request("GET", f"{self.base_url}/get")
            assert response.status_code == 200

    @pytest.mark.asyncio
    @httpx_compatibility_test
    async def test_async_client_params(self, async_client_factory):
        """Test async client with query parameters."""
        # TDD: Red phase - this will fail initially
        async with async_client_factory() as client:
            params = {"key": "value", "test": "data"}
            response = await client.get(f"{self.base_url}/get", params=params)
            assert response.status_code == 200

    # === High Priority AsyncClient Resource Management Tests ===

    @pytest.mark.asyncio
    @httpx_compatibility_test
    async def test_async_client_aclose_method(self, async_client_factory):
        """Test async client.aclose() method exists and works correctly."""
        client = async_client_factory()

        # Ensure aclose method exists
        assert hasattr(client, "aclose")
        assert callable(client.aclose)

        # Make a request before closing
        response = await client.get(f"{self.base_url}/get")
        assert response.status_code == 200

        # Close the client - should not raise an exception
        await client.aclose()

    @pytest.mark.asyncio
    @httpx_compatibility_test
    async def test_async_client_multiple_aclose_calls(self, async_client_factory):
        """Test that calling aclose() multiple times doesn't cause issues."""
        client = async_client_factory()

        # Make a request
        response = await client.get(f"{self.base_url}/get")
        assert response.status_code == 200

        # Close multiple times - should not raise
        await client.aclose()
        await client.aclose()
        await client.aclose()

    @pytest.mark.asyncio
    @httpx_compatibility_test
    async def test_async_client_context_manager_auto_close(self, async_client_factory):
        """Test that async context manager automatically closes the client."""
        async with async_client_factory() as client:
            # Ensure the client works inside the context
            response = await client.get(f"{self.base_url}/get")
            assert response.status_code == 200

            # Verify aclose method exists
            assert hasattr(client, "aclose")

        # After context manager exits, client should be closed
        # (We can't easily test if it's actually closed, but at least verify no errors)

    @pytest.mark.asyncio
    @httpx_compatibility_test
    async def test_async_client_context_manager_exception_handling(self, async_client_factory):
        """Test that async context manager closes client even if exception occurs."""
        try:
            async with async_client_factory() as client:
                # Make a successful request first
                response = await client.get(f"{self.base_url}/get")
                assert response.status_code == 200

                # Raise an exception
                raise ValueError("Test exception")
        except ValueError:
            pass  # Expected

        # Client should still be properly closed

    @pytest.mark.asyncio
    @httpx_compatibility_test
    async def test_async_client_reuse_after_aclose(self, async_client_factory):
        """Test async client behavior after being closed."""
        client = async_client_factory()

        # Make initial request
        response = await client.get(f"{self.base_url}/get")
        assert response.status_code == 200

        # Close the client
        await client.aclose()

        # Try to make another request - behavior may vary by implementation
        # but should not crash the process
        try:
            await client.get(f"{self.base_url}/get")
        except Exception:
            # Some implementations may raise an exception, which is fine
            pass
