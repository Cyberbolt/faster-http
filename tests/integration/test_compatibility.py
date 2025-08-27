"""Integration tests for httpx compatibility."""

import pytest

from tests.utils.httpx_comparison import httpx_compatibility_test


class TestCompatibility:
    """Test compatibility with httpx API."""

    @pytest.fixture(autouse=True)
    def setup(self, test_server):
        """Setup for each test."""
        self.base_url = test_server.base_url

    @httpx_compatibility_test
    def test_api_parity_sync_client(self, client_factory):
        """Test sync client API matches httpx."""
        # TDD: Red phase - this will fail initially
        client = client_factory()

        # Test all major API methods exist and work
        response = client.get(f"{self.base_url}/get")
        assert response.status_code == 200

        response = client.post(f"{self.base_url}/post", json={"test": "data"})
        assert response.status_code == 200

        response = client.put(f"{self.base_url}/put", data="test data")
        assert response.status_code == 200

        response = client.patch(f"{self.base_url}/patch", json={"update": True})
        assert response.status_code == 200

        response = client.delete(f"{self.base_url}/delete")
        assert response.status_code == 200

    @pytest.mark.asyncio
    @httpx_compatibility_test
    async def test_api_parity_async_client(self, async_client_factory):
        """Test async client API matches httpx."""
        # TDD: Red phase - this will fail initially
        async with async_client_factory() as client:
            # Test all major API methods exist and work
            response = await client.get(f"{self.base_url}/get")
            assert response.status_code == 200

            response = await client.post(f"{self.base_url}/post", json={"test": "data"})
            assert response.status_code == 200

            response = await client.put(f"{self.base_url}/put", data="test data")
            assert response.status_code == 200

            response = await client.patch(f"{self.base_url}/patch", json={"update": True})
            assert response.status_code == 200

            response = await client.delete(f"{self.base_url}/delete")
            assert response.status_code == 200

    @httpx_compatibility_test
    def test_response_interface_compatibility(self, client_factory):
        """Test response interface matches httpx."""
        # TDD: Red phase - this will fail initially
        response = client_factory.get(f"{self.base_url}/get")

        # Test all response attributes exist
        assert hasattr(response, "status_code")
        assert hasattr(response, "headers")
        assert hasattr(response, "text")
        assert hasattr(response, "content")
        assert hasattr(response, "json")
        assert hasattr(response, "url")
        assert hasattr(response, "cookies")
        assert hasattr(response, "history")
        assert hasattr(response, "is_error")
        assert hasattr(response, "raise_for_status")

    @httpx_compatibility_test
    def test_request_interface_compatibility(self, client_factory):
        """Test request interface matches httpx."""
        # TDD: Red phase - this will fail initially
        with client_factory() as client:
            request = client.build_request("GET", f"{self.base_url}/get")

            # Test all request attributes exist
            assert hasattr(request, "method")
            assert hasattr(request, "url")
            assert hasattr(request, "headers")
            assert hasattr(request, "content")

    @httpx_compatibility_test
    def test_exception_compatibility(self, client_factory):
        """Test exception interface matches httpx."""
        # TDD: Red phase - this will fail initially
        import httpx

        import faster_http

        # Test exception hierarchy matches
        httpx_exceptions = {
            "HTTPError",
            "RequestError",
            "TransportError",
            "ProtocolError",
            "HTTPStatusError",
            "ConnectError",
            "TimeoutException",
            "InvalidURL",
        }

        # Check all httpx exceptions exist in faster_http
        for exc_name in httpx_exceptions:
            assert hasattr(faster_http, exc_name), f"Missing exception: {exc_name}"
            assert hasattr(httpx, exc_name), f"httpx missing: {exc_name}"

    @httpx_compatibility_test
    def test_status_codes_compatibility(self, client_factory):
        """Test status code handling matches httpx."""
        # TDD: Red phase - this will fail initially
        test_codes = [200, 201, 204, 301, 302, 400, 401, 404, 500, 502, 503]

        for code in test_codes:
            response = client_factory.get(f"{self.base_url}/status/{code}")
            assert response.status_code == code

    @httpx_compatibility_test
    def test_headers_compatibility(self, client_factory):
        """Test headers handling matches httpx."""
        # TDD: Red phase - this will fail initially
        headers = {"User-Agent": "faster-http-test", "Custom-Header": "test-value", "Content-Type": "application/json"}

        response = client_factory.get(f"{self.base_url}/headers", headers=headers)
        assert response.status_code == 200

        # Verify headers are case-insensitive
        response_headers = response.json().get("headers", {})
        assert "User-Agent" in response_headers or "user-agent" in response_headers

    @httpx_compatibility_test
    def test_params_compatibility(self, client_factory):
        """Test query parameters handling matches httpx."""
        # TDD: Red phase - this will fail initially
        params = {"key1": "value1", "key2": ["value2a", "value2b"], "key3": 123, "key4": True}

        response = client_factory.get(f"{self.base_url}/get", params=params)
        assert response.status_code == 200

        # Verify parameters in response
        response_data = response.json()
        args = response_data.get("args", {})
        assert "key1" in args
        assert args["key1"] == "value1"

    @httpx_compatibility_test
    def test_json_compatibility(self, client_factory):
        """Test JSON handling matches httpx."""
        # TDD: Red phase - this will fail initially
        json_data = {
            "string": "test",
            "number": 123,
            "boolean": True,
            "null": None,
            "array": [1, 2, 3],
            "object": {"nested": "value"},
        }

        response = client_factory.post(f"{self.base_url}/post", json=json_data)
        assert response.status_code == 200

        # Verify JSON was sent correctly
        response_data = response.json()
        received_json = response_data.get("json", {})
        assert received_json == json_data
