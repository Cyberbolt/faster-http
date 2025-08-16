"""
Unit tests for Client functionality.
Tests the synchronous and asynchronous client implementations.
Following CLAUDE.md requirements: test httpx first, then faster_http for comparison.
"""

import httpx

import faster_http


class TestSyncClient:
    """Test synchronous Client functionality - httpx vs faster_http comparison."""

    def test_client_creation_comparison(self):
        """Test basic client creation - httpx vs faster_http."""
        # First test httpx Client creation
        httpx_client = httpx.Client()
        assert httpx_client is not None

        # Test that httpx client has expected methods
        httpx_methods = ["get", "post", "put", "patch", "delete", "head", "options", "request"]
        for method in httpx_methods:
            assert hasattr(httpx_client, method)
            assert callable(getattr(httpx_client, method))

        httpx_client.close()

        # Then test faster_http Client creation with same interface
        faster_client = faster_http.Client()
        assert faster_client is not None

        # Test that faster_http client has all httpx methods
        for method in httpx_methods:
            assert hasattr(faster_client, method), f"faster_http missing {method} method"
            assert callable(getattr(faster_client, method)), f"faster_http {method} not callable"

        faster_client.close()

    def test_client_with_base_url_comparison(self):
        """Test client creation with base URL - httpx vs faster_http."""
        base_url = "https://api.test.local"

        # First test httpx Client with base_url
        httpx_client = httpx.Client(base_url=base_url)
        assert str(httpx_client.base_url) == base_url
        httpx_client.close()

        # Then test faster_http Client with base_url
        faster_client = faster_http.Client(base_url=base_url)
        assert faster_client.base_url == base_url
        faster_client.close()

        # Both should support the same base_url interface
        assert str(httpx_client.base_url) == faster_client.base_url

    def test_client_with_headers_comparison(self):
        """Test client creation with default headers - httpx vs faster_http."""
        headers = {"Authorization": "Bearer token", "User-Agent": "test-client"}

        # First test httpx Client with headers
        httpx_client = httpx.Client(headers=headers)
        assert "Authorization" in httpx_client.headers
        assert "User-Agent" in httpx_client.headers
        httpx_client.close()

        # Then test faster_http Client with headers
        faster_client = faster_http.Client(headers=headers)
        assert hasattr(faster_client, "headers")
        assert "Authorization" in faster_client.headers
        assert "User-Agent" in faster_client.headers
        faster_client.close()

    def test_client_with_timeout_comparison(self):
        """Test client creation with timeout - httpx vs faster_http."""
        timeout = 30.0

        # First test httpx Client with timeout
        httpx_client = httpx.Client(timeout=timeout)
        assert httpx_client is not None
        httpx_client.close()

        # Then test faster_http Client with timeout
        faster_client = faster_http.Client(timeout=timeout)
        assert faster_client is not None
        faster_client.close()

    def test_client_context_manager_comparison(self):
        """Test client as context manager - httpx vs faster_http."""
        # First test httpx Client as context manager
        with httpx.Client() as httpx_client:
            assert httpx_client is not None
            assert hasattr(httpx_client, "get")

        # Then test faster_http Client as context manager
        with faster_http.Client() as faster_client:
            assert faster_client is not None
            assert hasattr(faster_client, "get")

    def test_client_with_cookies_comparison(self):
        """Test client creation with cookies - httpx vs faster_http."""
        cookies = {"session": "abc123", "theme": "dark"}

        # First test httpx Client with cookies
        httpx_client = httpx.Client(cookies=cookies)
        assert "session" in httpx_client.cookies
        assert "theme" in httpx_client.cookies
        httpx_client.close()

        # Then test faster_http Client with cookies
        faster_client = faster_http.Client(cookies=cookies)
        assert hasattr(faster_client, "cookies")
        assert "session" in faster_client.cookies
        assert "theme" in faster_client.cookies
        faster_client.close()

    def test_client_with_auth_comparison(self):
        """Test client creation with authentication - httpx vs faster_http."""
        # First test httpx Client with auth
        httpx_auth = httpx.BasicAuth("user", "pass")
        httpx_client = httpx.Client(auth=httpx_auth)
        assert httpx_client.auth is not None
        httpx_client.close()

        # Then test faster_http Client with auth
        faster_auth = faster_http.BasicAuth("user", "pass")
        faster_client = faster_http.Client(auth=faster_auth)
        assert hasattr(faster_client, "auth")
        faster_client.close()


class TestAsyncClient:
    """Test asynchronous Client functionality - httpx vs faster_http comparison."""

    def test_async_client_creation_comparison(self):
        """Test basic async client creation - httpx vs faster_http."""
        # First test httpx AsyncClient creation
        httpx_client = httpx.AsyncClient()
        assert httpx_client is not None

        # Test that httpx async client has expected methods
        httpx_methods = ["get", "post", "put", "patch", "delete", "head", "options", "request"]
        for method in httpx_methods:
            assert hasattr(httpx_client, method)
            assert callable(getattr(httpx_client, method))

        # httpx AsyncClient should have async context methods
        assert hasattr(httpx_client, "__aenter__")
        assert hasattr(httpx_client, "__aexit__")

        # Then test faster_http AsyncClient creation with same interface
        faster_client = faster_http.AsyncClient()
        assert faster_client is not None

        # Test that faster_http async client has all httpx methods
        for method in httpx_methods:
            assert hasattr(faster_client, method), f"faster_http missing {method} method"
            assert callable(getattr(faster_client, method)), f"faster_http {method} not callable"

        # faster_http AsyncClient should have async context methods
        assert hasattr(faster_client, "__aenter__")
        assert hasattr(faster_client, "__aexit__")

    def test_async_client_with_base_url_comparison(self):
        """Test async client creation with base URL - httpx vs faster_http."""
        base_url = "https://async-api.test.local"

        # First test httpx AsyncClient with base_url
        httpx_client = httpx.AsyncClient(base_url=base_url)
        assert str(httpx_client.base_url) == base_url

        # Then test faster_http AsyncClient with base_url
        faster_client = faster_http.AsyncClient(base_url=base_url)
        assert faster_client.base_url == base_url

        # Both should support the same base_url interface
        assert str(httpx_client.base_url) == faster_client.base_url

    def test_async_client_with_headers_comparison(self):
        """Test async client creation with default headers - httpx vs faster_http."""
        headers = {"Authorization": "Bearer token", "User-Agent": "async-test-client"}

        # First test httpx AsyncClient with headers
        httpx_client = httpx.AsyncClient(headers=headers)
        assert "Authorization" in httpx_client.headers
        assert "User-Agent" in httpx_client.headers

        # Then test faster_http AsyncClient with headers
        faster_client = faster_http.AsyncClient(headers=headers)
        assert hasattr(faster_client, "headers")
        assert "Authorization" in faster_client.headers
        assert "User-Agent" in faster_client.headers

    def test_async_client_with_timeout_comparison(self):
        """Test async client creation with timeout - httpx vs faster_http."""
        timeout = 30.0

        # First test httpx AsyncClient with timeout
        httpx_client = httpx.AsyncClient(timeout=timeout)
        assert httpx_client is not None

        # Then test faster_http AsyncClient with timeout
        faster_client = faster_http.AsyncClient(timeout=timeout)
        assert faster_client is not None


class TestClientConfiguration:
    """Test client configuration and options - httpx vs faster_http comparison."""

    def test_timeout_object_comparison(self):
        """Test Timeout object creation and usage - httpx vs faster_http."""
        # First test httpx Timeout object - need to provide all parameters
        httpx_timeout = httpx.Timeout(connect=5.0, read=30.0, write=10.0, pool=5.0)
        assert httpx_timeout.connect == 5.0
        assert httpx_timeout.read == 30.0

        # Test httpx Client with Timeout object
        httpx_client = httpx.Client(timeout=httpx_timeout)
        assert httpx_client is not None
        httpx_client.close()

        # Then test faster_http Timeout object
        faster_timeout = faster_http.Timeout(connect=5.0, read=30.0, write=10.0, pool=5.0)
        assert faster_timeout.connect == 5.0
        assert faster_timeout.read == 30.0

        # Test faster_http Client with Timeout object
        faster_client = faster_http.Client(timeout=faster_timeout)
        assert faster_client is not None
        faster_client.close()

    def test_headers_object_comparison(self):
        """Test Headers object creation and usage - httpx vs faster_http."""
        headers_data = {"User-Agent": "test-client", "Accept": "application/json"}

        # First test httpx Headers object
        httpx_headers = httpx.Headers(headers_data)

        # Test case-insensitive access in httpx
        assert httpx_headers["user-agent"] == "test-client"
        assert httpx_headers["USER-AGENT"] == "test-client"
        assert httpx_headers["User-Agent"] == "test-client"

        # Test httpx Client with Headers object
        httpx_client = httpx.Client(headers=httpx_headers)
        assert "User-Agent" in httpx_client.headers
        httpx_client.close()

        # Then test faster_http Headers object
        faster_headers = faster_http.Headers(headers_data)

        # Test case-insensitive access in faster_http
        assert faster_headers["user-agent"] == "test-client"
        assert faster_headers["USER-AGENT"] == "test-client"
        assert faster_headers["User-Agent"] == "test-client"

        # Test faster_http Client with Headers object
        faster_client = faster_http.Client(headers=faster_headers)
        assert "User-Agent" in faster_client.headers
        faster_client.close()

    def test_cookies_object_comparison(self):
        """Test Cookies object creation and usage - httpx vs faster_http."""
        # First test httpx Cookies object
        httpx_cookies = httpx.Cookies()
        httpx_cookies["session"] = "abc123"
        httpx_cookies["theme"] = "dark"

        assert httpx_cookies["session"] == "abc123"
        assert httpx_cookies["theme"] == "dark"

        # Test httpx Client with Cookies object
        httpx_client = httpx.Client(cookies=httpx_cookies)
        assert "session" in httpx_client.cookies
        httpx_client.close()

        # Then test faster_http Cookies object
        faster_cookies = faster_http.Cookies()
        faster_cookies["session"] = "abc123"
        faster_cookies["theme"] = "dark"

        assert faster_cookies["session"] == "abc123"
        assert faster_cookies["theme"] == "dark"

        # Test faster_http Client with Cookies object
        faster_client = faster_http.Client(cookies=faster_cookies)
        assert "session" in faster_client.cookies
        faster_client.close()

    def test_query_params_object_comparison(self):
        """Test QueryParams object creation and usage - httpx vs faster_http."""
        params_data = {"search": "python", "limit": "10"}

        # First test httpx QueryParams object
        httpx_params = httpx.QueryParams(params_data)

        # Test that it can be converted to dict
        httpx_params_dict = dict(httpx_params)
        assert httpx_params_dict["search"] == "python"
        assert httpx_params_dict["limit"] == "10"

        # Test httpx QueryParams from string
        httpx_params_from_string = httpx.QueryParams("search=python&limit=10")
        httpx_dict_from_string = dict(httpx_params_from_string)
        assert "search" in httpx_dict_from_string
        assert "limit" in httpx_dict_from_string

        # Then test faster_http QueryParams object
        faster_params = faster_http.QueryParams(params_data)

        # Test that it can be converted to dict
        faster_params_dict = dict(faster_params)
        assert faster_params_dict["search"] == "python"
        assert faster_params_dict["limit"] == "10"

        # Test faster_http QueryParams from string
        faster_params_from_string = faster_http.QueryParams("search=python&limit=10")
        faster_dict_from_string = dict(faster_params_from_string)
        assert "search" in faster_dict_from_string
        assert "limit" in faster_dict_from_string
