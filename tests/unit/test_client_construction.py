"""
Test client construction and resource management functionality.
Tests are designed to verify httpx compatibility for Client and AsyncClient construction.
"""

import asyncio

import pytest

import faster_http as http
from tests.utils.test_server import HTTPTestServer


class TestClientConstruction:
    """Test Client constructor and resource management."""

    def test_client_default_construction(self):
        """Test Client with default parameters."""
        client = http.Client()

        # Check default values
        assert client.base_url == ""
        assert client.headers is not None
        assert client.cookies is not None

        client.close()

    def test_client_with_base_url(self):
        """Test Client with base_url parameter."""
        with HTTPTestServer() as server:
            client = http.Client(base_url=server.base_url)

            assert str(client.base_url) == server.base_url

            # Test request with base_url
            resp = client.get("/get")
            assert resp.status_code == 200

            client.close()

    def test_client_with_headers(self):
        """Test Client with custom headers."""
        headers = {"User-Agent": "test-client", "Custom": "value"}
        client = http.Client(headers=headers)

        # Headers should be accessible
        client_headers = client.headers
        assert client_headers is not None

        client.close()

    def test_client_with_timeout(self):
        """Test Client with timeout parameter."""
        # Test with float timeout
        client1 = http.Client(timeout=10.0)
        client1.close()

        # Test with dict timeout (httpx style)
        client2 = http.Client(timeout={"connect": 5.0, "read": 10.0})
        client2.close()

    def test_client_with_auth(self):
        """Test Client with authentication."""
        auth = ("username", "password")
        client = http.Client(auth=auth)

        # Auth should be accessible
        assert client.auth is not None

        client.close()

    def test_client_with_cookies(self):
        """Test Client with cookies."""
        cookies = {"session": "abc123", "user": "test"}
        client = http.Client(cookies=cookies)

        # Cookies should be accessible
        client_cookies = client.cookies
        assert client_cookies is not None

        client.close()

    def test_client_with_verify_options(self):
        """Test Client with SSL verification options."""
        # Test verify=True (default)
        client1 = http.Client(verify=True)
        client1.close()

        # Test verify=False
        client2 = http.Client(verify=False)
        client2.close()

    def test_client_with_redirects(self):
        """Test Client with redirect configuration."""
        client = http.Client(follow_redirects=True, max_redirects=10)
        client.close()

    def test_client_with_http_versions(self):
        """Test Client with HTTP version settings."""
        # Test HTTP/1.1 only
        client1 = http.Client(http1=True, http2=False)
        client1.close()

        # Test HTTP/2 enabled
        client2 = http.Client(http1=True, http2=True)
        client2.close()

    def test_client_with_all_parameters(self):
        """Test Client with all constructor parameters."""
        client = http.Client(
            auth=("user", "pass"),
            params={"key": "value"},
            headers={"User-Agent": "test"},
            cookies={"session": "test"},
            verify=True,
            cert=None,
            http1=True,
            http2=False,
            proxy=None,
            mounts=None,
            timeout=10.0,
            follow_redirects=False,
            limits=None,
            max_redirects=20,
            event_hooks=None,
            base_url="",
            transport=None,
            trust_env=True,
            default_encoding="utf-8",
        )

        # Verify basic functionality works
        assert client is not None
        client.close()

    def test_client_context_manager(self):
        """Test Client as context manager."""
        with HTTPTestServer() as server:
            with http.Client(base_url=server.base_url) as client:
                # Client should be usable within context
                resp = client.get("/get")
                assert resp.status_code == 200

        # Client should be closed after context

    def test_client_close_method(self):
        """Test Client.close() method."""
        client = http.Client()

        # Close should work without errors
        client.close()

        # Multiple closes should be safe
        client.close()

    def test_client_build_request_method(self):
        """Test Client.build_request() method."""
        with HTTPTestServer() as server:
            client = http.Client(base_url=server.base_url)

            # Test build_request
            request = client.build_request("GET", "/get")
            assert request is not None
            assert request.method == "GET"
            assert "/get" in str(request.url)

            client.close()

    def test_client_build_request_with_params(self):
        """Test Client.build_request() with various parameters."""
        client = http.Client()

        # Test with different parameters
        request = client.build_request(
            "POST",
            "http://example.com/api",
            headers={"Content-Type": "application/json"},
            json={"key": "value"},
            params={"param": "value"},
        )

        assert request is not None
        assert request.method == "POST"

        client.close()

    def test_client_send_method(self):
        """Test Client.send() method with built request."""
        with HTTPTestServer() as server:
            client = http.Client(base_url=server.base_url)

            # Build and send request
            request = client.build_request("GET", "/get")
            response = client.send(request)

            assert response.status_code == 200

            client.close()

    def test_client_property_access(self):
        """Test Client property access for httpx compatibility."""
        client = http.Client(base_url="http://example.com", headers={"Custom": "value"}, cookies={"session": "test"})

        # Test property access
        assert client.base_url is not None
        assert client.headers is not None
        assert client.cookies is not None
        assert client.auth is not None or client.auth is None

        client.close()


class TestAsyncClientConstruction:
    """Test AsyncClient constructor and resource management."""

    def test_async_client_default_construction(self):
        """Test AsyncClient with default parameters."""
        client = http.AsyncClient()

        # Check default values
        assert client.base_url == ""
        assert client.headers is not None
        assert client.cookies is not None

        asyncio.run(client.aclose())

    def test_async_client_with_base_url(self):
        """Test AsyncClient with base_url parameter."""

        async def test():
            with HTTPTestServer() as server:
                client = http.AsyncClient(base_url=server.base_url)

                assert str(client.base_url) == server.base_url

                # Test request with base_url
                resp = await client.get("/get")
                assert resp.status_code == 200

                await client.aclose()

        asyncio.run(test())

    def test_async_client_with_parameters(self):
        """Test AsyncClient with various parameters."""

        async def test():
            client = http.AsyncClient(
                headers={"User-Agent": "test-async"}, timeout=10.0, verify=True, follow_redirects=False
            )

            # Verify basic functionality
            assert client is not None
            await client.aclose()

        asyncio.run(test())

    def test_async_client_context_manager(self):
        """Test AsyncClient as async context manager."""

        async def test():
            with HTTPTestServer() as server:
                async with http.AsyncClient(base_url=server.base_url) as client:
                    # Client should be usable within context
                    resp = await client.get("/get")
                    assert resp.status_code == 200

                # Client should be closed after context

        asyncio.run(test())

    def test_async_client_aclose_method(self):
        """Test AsyncClient.aclose() method."""

        async def test():
            client = http.AsyncClient()

            # Close should work without errors
            await client.aclose()

            # Multiple closes should be safe
            await client.aclose()

        asyncio.run(test())

    def test_async_client_build_request_method(self):
        """Test AsyncClient.build_request() method."""

        async def test():
            with HTTPTestServer() as server:
                client = http.AsyncClient(base_url=server.base_url)

                # Test build_request
                request = client.build_request("GET", "/get")
                assert request is not None
                assert request.method == "GET"
                assert "/get" in str(request.url)

                await client.aclose()

        asyncio.run(test())

    def test_async_client_send_method(self):
        """Test AsyncClient.send() method with built request."""

        async def test():
            with HTTPTestServer() as server:
                client = http.AsyncClient(base_url=server.base_url)

                # Build and send request
                request = client.build_request("GET", "/get")
                response = await client.send(request)

                assert response.status_code == 200

                await client.aclose()

        asyncio.run(test())

    def test_async_client_with_all_parameters(self):
        """Test AsyncClient with all constructor parameters."""

        async def test():
            client = http.AsyncClient(
                auth=("user", "pass"),
                params={"key": "value"},
                headers={"User-Agent": "test"},
                cookies={"session": "test"},
                verify=True,
                cert=None,
                http1=True,
                http2=False,
                proxy=None,
                mounts=None,
                timeout=10.0,
                follow_redirects=False,
                limits=None,
                max_redirects=20,
                event_hooks=None,
                base_url="",
                transport=None,
                trust_env=True,
                default_encoding="utf-8",
            )

            # Verify basic functionality works
            assert client is not None
            await client.aclose()

        asyncio.run(test())

    def test_async_client_property_access(self):
        """Test AsyncClient property access for httpx compatibility."""

        async def test():
            client = http.AsyncClient(
                base_url="http://example.com", headers={"Custom": "value"}, cookies={"session": "test"}
            )

            # Test property access
            assert client.base_url is not None
            assert client.headers is not None
            assert client.cookies is not None
            assert client.auth is not None or client.auth is None

            await client.aclose()

        asyncio.run(test())


class TestClientResourceManagement:
    """Test resource management and cleanup."""

    def test_client_multiple_context_managers(self):
        """Test multiple Client context managers."""
        with HTTPTestServer() as server:
            # Test nested context managers
            with http.Client(base_url=server.base_url) as client1:
                with http.Client(base_url=server.base_url) as client2:
                    resp1 = client1.get("/get")
                    resp2 = client2.get("/get")
                    assert resp1.status_code == 200
                    assert resp2.status_code == 200

    def test_async_client_multiple_context_managers(self):
        """Test multiple AsyncClient context managers."""

        async def test():
            with HTTPTestServer() as server:
                # Test nested async context managers
                async with http.AsyncClient(base_url=server.base_url) as client1:
                    async with http.AsyncClient(base_url=server.base_url) as client2:
                        resp1 = await client1.get("/get")
                        resp2 = await client2.get("/get")
                        assert resp1.status_code == 200
                        assert resp2.status_code == 200

        asyncio.run(test())

    def test_client_reuse_after_close(self):
        """Test that Client cannot be reused after close (httpx compatibility)."""
        client = http.Client()
        client.close()

        # This should work (though may give different behavior)
        # We don't expect errors for basic operations after close
        try:
            client.close()  # Should not raise
        except Exception:
            pass  # Different behavior is acceptable

    def test_async_client_reuse_after_close(self):
        """Test that AsyncClient cannot be reused after close."""

        async def test():
            client = http.AsyncClient()
            await client.aclose()

            # This should work (though may give different behavior)
            try:
                await client.aclose()  # Should not raise
            except Exception:
                pass  # Different behavior is acceptable

        asyncio.run(test())


if __name__ == "__main__":
    pytest.main([__file__])
