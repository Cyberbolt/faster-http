"""Integration tests for complete usage scenarios."""

import pytest

from tests.utils.httpx_comparison import httpx_compatibility_test


def get_exception_class(client_factory, exception_name):
    """
    Get the appropriate exception class based on the client library.

    Args:
        client_factory: The client factory instance
        exception_name: Name of the exception (e.g., 'TimeoutException', 'ConnectError')

    Returns:
        The exception class from the appropriate library
    """
    if client_factory.library == "httpx":
        import httpx

        # Map faster_http exception names to httpx exception names
        exception_mapping = {
            "TimeoutException": "ReadTimeout",  # httpx uses more specific timeout exceptions
            "ConnectError": "ConnectError",
            "HTTPStatusError": "HTTPStatusError",
            "InvalidURL": "UnsupportedProtocol",  # httpx uses different name for URL errors
            "TooManyRedirects": "TooManyRedirects",
        }
        httpx_exception_name = exception_mapping.get(exception_name, exception_name)
        return getattr(httpx, httpx_exception_name)
    else:
        # faster_http
        import faster_http

        return getattr(faster_http, exception_name)


class TestScenarios:
    """Test complete usage scenarios."""

    @pytest.fixture(autouse=True)
    def setup(self, test_server):
        """Setup for each test."""
        self.base_url = test_server.base_url

    @httpx_compatibility_test
    def test_api_workflow_scenario(self, client_factory):
        """Test complete API workflow scenario."""
        # TDD: Red phase - this will fail initially
        with client_factory(base_url=self.base_url) as client:
            # 1. Authentication
            auth_response = client.post("/post", json={"username": "test", "password": "secret"})
            assert auth_response.status_code == 200

            # 2. Get user data
            user_response = client.get("/get", headers={"Authorization": "Bearer token"})
            assert user_response.status_code == 200

            # 3. Update user data
            update_response = client.patch("/patch", json={"name": "Updated Name"})
            assert update_response.status_code == 200

            # 4. Upload file
            files = {"file": ("test.txt", "file content", "text/plain")}
            upload_response = client.post("/post", files=files)
            assert upload_response.status_code == 200

            # 5. Delete resource
            delete_response = client.delete("/delete")
            assert delete_response.status_code == 200

    @pytest.mark.asyncio
    @httpx_compatibility_test
    async def test_async_api_workflow_scenario(self, async_client_factory):
        """Test complete async API workflow scenario."""
        # TDD: Red phase - this will fail initially
        async with async_client_factory(base_url=self.base_url) as client:
            # 1. Authentication
            auth_response = await client.post("/post", json={"username": "test", "password": "secret"})
            assert auth_response.status_code == 200

            # 2. Get user data
            user_response = await client.get("/get", headers={"Authorization": "Bearer token"})
            assert user_response.status_code == 200

            # 3. Update user data
            update_response = await client.patch("/patch", json={"name": "Updated Name"})
            assert update_response.status_code == 200

            # 4. Delete resource
            delete_response = await client.delete("/delete")
            assert delete_response.status_code == 200

    @httpx_compatibility_test
    def test_session_with_cookies_scenario(self, client_factory):
        """Test session management with cookies."""
        # TDD: Red phase - this will fail initially
        with client_factory() as client:
            # 1. Set cookies
            response1 = client.get(f"{self.base_url}/cookies/set/session_id/abc123")
            assert "session_id" in response1.cookies

            # 2. Use cookies in subsequent requests
            response2 = client.get(f"{self.base_url}/cookies")
            cookies_data = response2.json().get("cookies", {})
            assert "session_id" in cookies_data

    @httpx_compatibility_test
    def test_redirect_scenario(self, client_factory):
        """Test redirect handling scenario."""
        # TDD: Red phase - this will fail initially
        # Test redirect following
        response = client_factory.get(f"{self.base_url}/redirect/3", follow_redirects=True)
        assert response.status_code == 200
        assert len(response.history) == 3

        # Test redirect without following
        response = client_factory.get(f"{self.base_url}/redirect/1", follow_redirects=False)
        assert response.status_code in [301, 302, 303, 307, 308]

    @httpx_compatibility_test
    def test_error_handling_scenario(self, client_factory):
        """Test comprehensive error handling scenario."""
        # TDD: Red phase - this will fail initially
        import faster_http

        # Test various error conditions

        # 1. Network error - use reliable connection refused scenario
        connect_error_class = get_exception_class(client_factory, "ConnectError")
        with pytest.raises(connect_error_class):
            client_factory.get("http://127.0.0.1:9999", timeout=2.0)

        # 2. Timeout error
        timeout_error_class = get_exception_class(client_factory, "TimeoutException")
        with pytest.raises(timeout_error_class):
            client_factory.get(f"{self.base_url}/delay/10", timeout=1.0)

        # 3. HTTP status errors
        response = client_factory.get(f"{self.base_url}/status/404")
        status_error_class = get_exception_class(client_factory, "HTTPStatusError")
        with pytest.raises(status_error_class):
            response.raise_for_status()

        # 4. Invalid URL error
        with pytest.raises(faster_http.InvalidURL):
            client_factory.get("not-a-url")

    @httpx_compatibility_test
    def test_streaming_scenario(self, client_factory):
        """Test streaming response scenario."""
        # TDD: Red phase - this will fail initially
        with client_factory.stream("GET", f"{self.base_url}/stream/20") as response:
            assert response.status_code == 200

            content = b""
            for chunk in response.iter_bytes():
                content += chunk

            assert len(content) > 0

    @httpx_compatibility_test
    def test_authentication_scenario(self, client_factory):
        """Test authentication scenario."""
        # TDD: Red phase - this will fail initially
        import faster_http

        # Basic auth
        auth = faster_http.BasicAuth("user", "pass")
        response = client_factory.get(f"{self.base_url}/basic-auth/user/pass", auth=auth)
        assert response.status_code == 200

        # Digest auth
        digest_auth = faster_http.DigestAuth("user", "pass")
        response = client_factory.get(f"{self.base_url}/digest-auth/auth/user/pass", auth=digest_auth)
        assert response.status_code == 200

    @httpx_compatibility_test
    def test_file_upload_scenario(self, client_factory):
        """Test file upload scenario."""
        # TDD: Red phase - this will fail initially
        # Single file upload
        files = {"file": ("test.txt", "file content", "text/plain")}
        response = client_factory.post(f"{self.base_url}/post", files=files)
        assert response.status_code == 200

        # Multiple files upload
        files = {"file1": ("test1.txt", "content1", "text/plain"), "file2": ("test2.txt", "content2", "text/plain")}
        response = client_factory.post(f"{self.base_url}/post", files=files)
        assert response.status_code == 200

    @httpx_compatibility_test
    def test_mixed_data_scenario(self, client_factory):
        """Test mixed data types in single request."""
        # TDD: Red phase - this will fail initially
        data = {"text_field": "text_value", "number_field": "123"}
        files = {"file": ("test.txt", "file content", "text/plain")}

        response = client_factory.post(f"{self.base_url}/post", data=data, files=files)
        assert response.status_code == 200

    @httpx_compatibility_test
    def test_custom_headers_scenario(self, client_factory):
        """Test custom headers scenario."""
        # TDD: Red phase - this will fail initially
        headers = {
            "Authorization": "Bearer token123",
            "User-Agent": "faster-http-test/1.0",
            "Custom-Header": "custom-value",
            "Content-Type": "application/json",
        }

        response = client_factory.get(f"{self.base_url}/headers", headers=headers)
        assert response.status_code == 200

        # Verify headers were sent
        response_data = response.json()
        sent_headers = response_data.get("headers", {})
        assert "Authorization" in sent_headers or "authorization" in sent_headers

    @httpx_compatibility_test
    def test_connection_pooling_scenario(self, client_factory):
        """Test connection pooling behavior."""
        # TDD: Red phase - this will fail initially
        with client_factory() as client:
            # Make multiple requests to test connection reuse
            responses = []
            for i in range(10):
                response = client.get(f"{self.base_url}/get?request={i}")
                responses.append(response)

            # All requests should succeed
            assert all(r.status_code == 200 for r in responses)
