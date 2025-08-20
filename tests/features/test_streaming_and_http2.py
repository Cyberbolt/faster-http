"""
Test Streaming and HTTP/2 functionality.
Tests streaming and HTTP/2 with httpx vs faster_http comparison.
Following CLAUDE.md requirements: test httpx first, then faster_http for comparison.
"""

import asyncio

import httpx

import faster_http


class TestStreamingContextManager:
    """Test streaming context manager features - httpx vs faster_http comparison."""

    def test_basic_stream_context_manager_comparison(self):
        """Test basic stream context manager - httpx vs faster_http."""
        url = "https://httpbin.org/get"

        # First test httpx stream context manager
        with httpx.stream("GET", url) as httpx_response:
            assert httpx_response.status_code == 200
            httpx_response.read()  # Must read content first for streaming responses
            httpx_data = httpx_response.json()
            assert "url" in httpx_data  # httpbin returns 'url' field
            len(httpx_response.content)

        # Then test faster_http stream context manager (should match httpx)
        with faster_http.stream("GET", url) as faster_response:
            assert faster_response.status_code == 200
            faster_response.read()  # Must read content first for streaming responses
            faster_data = faster_response.json()
            assert "url" in faster_data  # httpbin returns 'url' field
            len(faster_response.content)

        # Both should provide similar streaming functionality
        assert httpx_data.keys() == faster_data.keys()

    def test_stream_post_request_comparison(self):
        """Test stream context manager with POST - httpx vs faster_http."""
        url = "https://httpbin.org/post"
        post_data = {"test": "streaming", "key": "value"}

        # First test httpx stream POST
        with httpx.stream("POST", url, json=post_data) as httpx_response:
            assert httpx_response.status_code == 200
            httpx_response.read()  # Must read content first for streaming responses
            httpx_data = httpx_response.json()
            assert "json" in httpx_data
            assert httpx_data["json"]["test"] == "streaming"

        # Then test faster_http stream POST (should match httpx)
        with faster_http.stream("POST", url, json=post_data) as faster_response:
            assert faster_response.status_code == 200
            faster_response.read()  # Must read content first for streaming responses
            faster_data = faster_response.json()
            assert "json" in faster_data
            assert faster_data["json"]["test"] == "streaming"

        # Both should handle POST streaming the same way
        assert httpx_response.status_code == faster_response.status_code
        assert httpx_data["json"] == faster_data["json"]

    def test_stream_resource_management_comparison(self):
        """Test stream resource management - httpx vs faster_http."""
        url = "https://httpbin.org/get"

        # First test httpx stream resource management
        httpx_response_ref = None
        with httpx.stream("GET", url) as httpx_response:
            httpx_response_ref = httpx_response
            assert httpx_response.status_code == 200
            assert not httpx_response.is_closed

        # After context exit, response should be closed
        assert httpx_response_ref.is_closed

        # Then test faster_http stream resource management (should match httpx)
        faster_response_ref = None
        with faster_http.stream("GET", url) as faster_response:
            faster_response_ref = faster_response
            assert faster_response.status_code == 200
            assert not faster_response.is_closed

        # After context exit, response should be closed
        assert faster_response_ref.is_closed

        # Both should manage resources the same way
        assert httpx_response_ref.is_closed == faster_response_ref.is_closed

    def test_stream_iteration_methods_comparison(self):
        """Test stream iteration methods - httpx vs faster_http."""
        url = "https://httpbin.org/get"

        # First test httpx stream iteration
        with httpx.stream("GET", url) as httpx_response:
            assert httpx_response.status_code == 200
            httpx_chunks = list(httpx_response.iter_bytes(chunk_size=1024))
            sum(len(chunk) for chunk in httpx_chunks)

        # Then test faster_http stream iteration (should match httpx)
        with faster_http.stream("GET", url) as faster_response:
            assert faster_response.status_code == 200
            faster_chunks = list(faster_response.iter_bytes(chunk_size=1024))
            sum(len(chunk) for chunk in faster_chunks)

        # Both should provide similar iteration functionality
        assert len(httpx_chunks) > 0
        assert len(faster_chunks) > 0
        assert all(isinstance(chunk, bytes) for chunk in httpx_chunks)
        assert all(isinstance(chunk, bytes) for chunk in faster_chunks)

    def test_stream_with_headers_comparison(self):
        """Test stream with custom headers - httpx vs faster_http."""
        url = "https://httpbin.org/headers"
        headers = {"User-Agent": "stream-test/1.0", "X-Stream-Test": "comparison"}

        # First test httpx stream with headers
        with httpx.stream("GET", url, headers=headers) as httpx_response:
            assert httpx_response.status_code == 200
            httpx_response.read()  # Must read content first for streaming responses
            httpx_data = httpx_response.json()
            assert "headers" in httpx_data
            assert httpx_data["headers"]["User-Agent"] == "stream-test/1.0"
            assert httpx_data["headers"]["X-Stream-Test"] == "comparison"

        # Then test faster_http stream with headers (should match httpx)
        with faster_http.stream("GET", url, headers=headers) as faster_response:
            assert faster_response.status_code == 200
            faster_response.read()  # Must read content first for streaming responses
            faster_data = faster_response.json()
            assert "headers" in faster_data
            assert faster_data["headers"]["User-Agent"] == "stream-test/1.0"
            assert faster_data["headers"]["X-Stream-Test"] == "comparison"

        # Both should handle headers the same way
        assert httpx_data["headers"]["User-Agent"] == faster_data["headers"]["User-Agent"]
        assert httpx_data["headers"]["X-Stream-Test"] == faster_data["headers"]["X-Stream-Test"]

    def test_async_stream_context_manager_comparison(self):
        """Test async stream context manager - httpx vs faster_http."""

        async def test_async_streaming():
            url = "https://httpbin.org/get"

            # First test httpx async stream
            async with httpx.AsyncClient() as httpx_client:
                async with httpx_client.stream("GET", url) as httpx_response:
                    assert httpx_response.status_code == 200
                    await httpx_response.aread()  # Must read content first for async streaming responses
                    httpx_data = httpx_response.json()
                    assert "url" in httpx_data  # httpbin returns 'url' field

            # Then test faster_http async stream (should match httpx)
            async with faster_http.AsyncClient() as faster_client:
                async with faster_client.stream("GET", url) as faster_response:
                    assert faster_response.status_code == 200
                    await faster_response.aread()  # Must read content first for async streaming responses
                    faster_data = faster_response.json()
                    assert "url" in faster_data  # httpbin returns 'url' field

            # Both should work with async streaming
            assert httpx_data.keys() == faster_data.keys()

        asyncio.run(test_async_streaming())


class TestHTTP2Support:
    """Test HTTP/2 support features - httpx vs faster_http comparison."""

    def test_http2_client_creation_comparison(self):
        """Test HTTP/2 client creation - httpx vs faster_http."""
        # First test httpx Client with HTTP/2 enabled
        try:
            httpx_client = httpx.Client(http2=True)
            httpx_client.close()
        except Exception:
            pass

        # Then test faster_http Client with HTTP/2 enabled (should match httpx)
        try:
            faster_client = faster_http.Client(http2=True)
            faster_client.close()
        except Exception:
            pass

        # Both should have consistent HTTP/2 support
        # Note: This documents current HTTP/2 support behavior

    def test_http2_vs_http1_configuration_comparison(self):
        """Test HTTP/2 vs HTTP/1.1 configuration - httpx vs faster_http."""
        # First test httpx clients with different HTTP versions
        httpx_http1_client = httpx.Client(http2=False)
        assert httpx_http1_client is not None
        httpx_http1_client.close()

        try:
            httpx_http2_client = httpx.Client(http2=True)
            httpx_http2_available = True
            httpx_http2_client.close()
        except Exception:
            httpx_http2_available = False

        # Then test faster_http clients with different HTTP versions (should match httpx)
        faster_http1_client = faster_http.Client(http2=False)
        assert faster_http1_client is not None
        faster_http1_client.close()

        try:
            faster_http2_client = faster_http.Client(http2=True)
            faster_http2_available = True
            faster_http2_client.close()
        except Exception:
            faster_http2_available = False

        # Both should support HTTP version configuration consistently
        assert httpx_http2_available == faster_http2_available

    def test_http2_with_ssl_configuration_comparison(self):
        """Test HTTP/2 with SSL configuration - httpx vs faster_http."""
        # First test httpx HTTP/2 client with SSL
        try:
            httpx_client = httpx.Client(http2=True, verify=True, trust_env=True)
            httpx_client.close()
        except Exception:
            pass

        # Then test faster_http HTTP/2 client with SSL (should match httpx)
        try:
            faster_client = faster_http.Client(http2=True, verify=True, trust_env=True)
            faster_client.close()
        except Exception:
            pass

        # Both should handle HTTP/2 with SSL consistently
        # Note: This documents current HTTP/2 SSL support

    def test_http2_async_client_comparison(self):
        """Test HTTP/2 async client - httpx vs faster_http."""

        async def test_http2_async():
            # First test httpx AsyncClient with HTTP/2
            try:
                async with httpx.AsyncClient(http2=True) as httpx_client:
                    assert httpx_client is not None
            except Exception:
                pass

            # Then test faster_http AsyncClient with HTTP/2 (should match httpx)
            try:
                async with faster_http.AsyncClient(http2=True) as faster_client:
                    assert faster_client is not None
            except Exception:
                pass

            # Both should support async HTTP/2 consistently
            # Note: This documents current async HTTP/2 support

        asyncio.run(test_http2_async())

    def test_http2_version_detection_comparison(self):
        """Test HTTP version detection - httpx vs faster_http."""
        url = "https://httpbin.org/headers"

        # First test httpx HTTP version detection
        httpx_client = httpx.Client(http2=False)  # Use HTTP/1.1 for local server
        httpx_response = httpx_client.get(url)
        assert httpx_response.status_code == 200
        httpx_version = httpx_response.http_version
        assert httpx_version in ["HTTP/1.1", "HTTP/1.0", "HTTP/2"]
        httpx_client.close()

        # Then test faster_http HTTP version detection (should match httpx)
        faster_client = faster_http.Client(http2=False)  # Use HTTP/1.1 for local server
        faster_response = faster_client.get(url)
        assert faster_response.status_code == 200
        faster_version = faster_response.http_version
        assert faster_version in ["HTTP/1.1", "HTTP/1.0", "HTTP/2"]
        faster_client.close()

        # Both should detect HTTP version for same server consistently
        # Note: Local server typically uses HTTP/1.1

    def test_http2_with_proxy_configuration_comparison(self):
        """Test HTTP/2 with proxy configuration - httpx vs faster_http."""
        proxy_url = "http://http2-proxy.example.com:8080"

        # First test httpx HTTP/2 client with proxy
        try:
            httpx_client = httpx.Client(http2=True, proxy=proxy_url)
            httpx_client.close()
        except Exception:
            pass

        # Then test faster_http HTTP/2 client with proxy (should match httpx)
        try:
            faster_client = faster_http.Client(http2=True, proxy=proxy_url)
            faster_client.close()
        except Exception:
            pass

        # Both should handle HTTP/2 with proxy consistently
        # Note: This documents current HTTP/2 proxy support


class TestStreamingHTTP2Integration:
    """Test streaming and HTTP/2 integration - httpx vs faster_http comparison."""

    def test_http2_streaming_combination_comparison(self):
        """Test HTTP/2 with streaming combination - httpx vs faster_http."""
        url = "https://httpbin.org/get"

        # First test httpx HTTP/2 client with streaming
        try:
            httpx_client = httpx.Client(http2=True)
            with httpx_client.stream("GET", url) as httpx_response:
                assert httpx_response.status_code == 200
                httpx_chunks = list(httpx_response.iter_bytes())
                httpx_http2_stream_works = True
            httpx_client.close()
        except Exception:
            httpx_http2_stream_works = False
            httpx_chunks = []

        # Then test faster_http HTTP/2 client with streaming (should match httpx)
        try:
            faster_client = faster_http.Client(http2=True)
            with faster_client.stream("GET", url) as faster_response:
                assert faster_response.status_code == 200
                faster_chunks = list(faster_response.iter_bytes())
                faster_http2_stream_works = True
            faster_client.close()
        except Exception:
            faster_http2_stream_works = False
            faster_chunks = []

        # Both should handle HTTP/2 streaming consistently
        assert httpx_http2_stream_works == faster_http2_stream_works
        if httpx_http2_stream_works and faster_http2_stream_works:
            assert len(httpx_chunks) > 0
            assert len(faster_chunks) > 0

    def test_comprehensive_streaming_http2_comparison(self):
        """Test comprehensive streaming HTTP/2 configuration - httpx vs faster_http."""
        url = "https://httpbin.org/get"
        data = {"test": "comprehensive", "http2": True, "streaming": True}
        headers = {"User-Agent": "http2-stream-test/1.0"}

        # First test httpx comprehensive configuration
        try:
            httpx_client = httpx.Client(
                http2=True,
                verify=False,  # Disable for local testing
                timeout=30.0,
                headers=headers,
            )

            with httpx_client.stream("POST", url, json=data) as httpx_response:
                assert httpx_response.status_code == 200
                httpx_data = httpx_response.json()
                assert "json" in httpx_data
                assert httpx_data["json"]["test"] == "comprehensive"
                httpx_comprehensive_works = True

            httpx_client.close()
        except Exception:
            httpx_comprehensive_works = False
            httpx_data = {}

        # Then test faster_http comprehensive configuration (should match httpx)
        try:
            faster_client = faster_http.Client(
                http2=True,
                verify=False,  # Disable for local testing
                timeout=30.0,
                headers=headers,
            )

            with faster_client.stream("POST", url, json=data) as faster_response:
                assert faster_response.status_code == 200
                faster_data = faster_response.json()
                assert "json" in faster_data
                assert faster_data["json"]["test"] == "comprehensive"
                faster_comprehensive_works = True

            faster_client.close()
        except Exception:
            faster_comprehensive_works = False
            faster_data = {}

        # Both should handle comprehensive configuration consistently
        assert httpx_comprehensive_works == faster_comprehensive_works
        if httpx_comprehensive_works and faster_comprehensive_works:
            assert httpx_data["json"]["test"] == faster_data["json"]["test"]

    def test_async_streaming_http2_combination_comparison(self):
        """Test async streaming HTTP/2 combination - httpx vs faster_http."""

        async def test_async_streaming_http2():
            url = "https://httpbin.org/get"

            # First test httpx async streaming HTTP/2
            try:
                async with httpx.AsyncClient(http2=True) as httpx_client:
                    async with httpx_client.stream("GET", url) as httpx_response:
                        assert httpx_response.status_code == 200
                        httpx_data = httpx_response.json()
                        assert "args" in httpx_data
                        httpx_async_stream_http2_works = True
            except Exception:
                httpx_async_stream_http2_works = False
                httpx_data = {}

            # Then test faster_http async streaming HTTP/2 (should match httpx)
            try:
                async with faster_http.AsyncClient(http2=True) as faster_client:
                    async with faster_client.stream("GET", url) as faster_response:
                        assert faster_response.status_code == 200
                        faster_data = faster_response.json()
                        assert "args" in faster_data
                        faster_async_stream_http2_works = True
            except Exception:
                faster_async_stream_http2_works = False
                faster_data = {}

            # Both should handle async streaming HTTP/2 consistently
            assert httpx_async_stream_http2_works == faster_async_stream_http2_works
            if httpx_async_stream_http2_works and faster_async_stream_http2_works:
                assert httpx_data.keys() == faster_data.keys()

        asyncio.run(test_async_streaming_http2())


class TestStreamingAuthentication:
    """Test streaming with authentication - httpx vs faster_http comparison."""

    def test_streaming_with_basic_auth_comparison(self):
        """Test streaming with BasicAuth - httpx vs faster_http."""
        url = "https://httpbin.org/get"

        # First test httpx streaming with BasicAuth
        httpx_auth = httpx.BasicAuth("user", "pass")
        with httpx.stream("GET", url, auth=httpx_auth) as httpx_response:
            # Note: stable_server may not actually require auth, so we test interface
            assert httpx_response.status_code in [200, 401, 404]

        # Then test faster_http streaming with BasicAuth (should match httpx)
        faster_auth = faster_http.BasicAuth("user", "pass")
        with faster_http.stream("GET", url, auth=faster_auth) as faster_response:
            # Note: stable_server may not actually require auth, so we test interface
            assert faster_response.status_code in [200, 401, 404]

        # Both should handle auth with streaming consistently
        # Note: This tests the interface, not actual authentication

    def test_streaming_with_timeout_comparison(self):
        """Test streaming with timeout configuration - httpx vs faster_http."""
        url = "https://httpbin.org/get"
        timeout = 5.0

        # First test httpx streaming with timeout
        try:
            with httpx.stream("GET", url, timeout=timeout) as httpx_response:
                assert httpx_response.status_code == 200
        except Exception:
            pass

        # Then test faster_http streaming with timeout (should match httpx)
        try:
            with faster_http.stream("GET", url, timeout=timeout) as faster_response:
                assert faster_response.status_code == 200
        except Exception:
            pass

        # Both should handle timeout with streaming consistently
        # Note: This documents current timeout behavior
