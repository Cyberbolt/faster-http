"""
Test suite for httpx-compatible tool classes: URL, Headers, Cookies
Tests compatibility with httpx API and functionality
"""

import httpx

import faster_http as http


class TestURL:
    """Test URL class compatibility with httpx.URL"""

    def test_url_parsing(self):
        """Test URL parsing and property access"""
        url = http.URL("https://api.example.com:8080/v1/data?limit=10&page=2#section1")

        assert url.scheme == "https"
        assert url.host == "api.example.com"
        assert url.port == 8080
        assert url.path == "/v1/data"
        assert url.fragment == "section1"

    def test_url_query_params(self):
        """Test URL query parameter handling"""
        url = http.URL("https://api.example.com/search?q=test&limit=10&page=2")

        # Test params property returns QueryParams object
        params = url.params
        assert hasattr(params, "items")
        params_dict = dict(params.items())
        assert "q" in params_dict
        assert params_dict["q"] == "test"
        assert params_dict["limit"] == "10"
        assert params_dict["page"] == "2"

    def test_url_query_bytes(self):
        """Test URL query returns bytes like httpx"""
        url = http.URL("https://example.com?q=test&limit=10")
        query = url.query
        assert isinstance(query, bytes)
        assert b"q=test" in query
        assert b"limit=10" in query

    def test_url_fragment_empty(self):
        """Test URL fragment returns empty string when missing (httpx compatibility)"""
        url = http.URL("https://example.com/path")
        assert url.fragment == ""

    def test_url_repr(self):
        """Test URL string representation"""
        url_str = "https://example.com/path?q=test"
        url = http.URL(url_str)
        assert repr(url) == f"URL('{url_str}')"
        assert str(url) == url_str

    def test_url_copy_with(self):
        """Test URL.copy_with method"""
        url = http.URL("https://example.com/path?q=test#section")

        # Test path modification
        url2 = url.copy_with(path="/new-path")
        assert url2.path == "/new-path"
        assert url2.scheme == "https"  # Other properties unchanged
        assert url2.host == "example.com"

        # Test query modification with bytes
        url3 = url.copy_with(query=b"new=value")
        assert b"new=value" in url3.query

        # Test fragment modification
        url4 = url.copy_with(fragment="new-section")
        assert url4.fragment == "new-section"

    def test_url_httpx_compatibility(self):
        """Test URL compatibility with httpx.URL"""
        test_url = "https://api.example.com:8080/v1/data?limit=10&page=2#section1"
        httpx_url = httpx.URL(test_url)
        faster_url = http.URL(test_url)

        # Compare properties
        assert httpx_url.scheme == faster_url.scheme
        assert httpx_url.host == faster_url.host
        assert httpx_url.port == faster_url.port
        assert httpx_url.path == faster_url.path
        assert httpx_url.fragment == faster_url.fragment


class TestHeaders:
    """Test Headers class compatibility with httpx.Headers"""

    def test_headers_creation(self):
        """Test Headers creation and basic operations"""
        headers = http.Headers({"Content-Type": "application/json", "X-Custom": "value"})
        assert len(headers) == 2
        assert "Content-Type" in headers

    def test_headers_case_insensitive(self):
        """Test Headers case-insensitive access"""
        headers = http.Headers({"Content-Type": "application/json"})

        # Test case-insensitive access
        assert headers["content-type"] == "application/json"
        assert headers["CONTENT-TYPE"] == "application/json"
        assert headers["Content-Type"] == "application/json"

    def test_headers_get_method(self):
        """Test Headers.get method"""
        headers = http.Headers({"Content-Type": "application/json"})

        assert headers.get("content-type") == "application/json"
        assert headers.get("nonexistent") is None
        assert headers.get("nonexistent", "default") == "default"

    def test_headers_get_list_method(self):
        """Test Headers.get_list method"""
        headers = http.Headers({"Content-Type": "application/json"})

        result = headers.get_list("content-type")
        assert isinstance(result, list)
        assert result == ["application/json"]

        # Test non-existent header
        assert headers.get_list("nonexistent") == []

    def test_headers_iteration(self):
        """Test Headers iteration"""
        headers = http.Headers({"Content-Type": "application/json", "X-Custom": "value"})

        # Test iteration
        keys = list(headers)
        assert len(keys) == 2
        assert "Content-Type" in keys or "content-type" in keys
        assert "X-Custom" in keys or "x-custom" in keys

        # Test for loop
        count = 0
        for key in headers:
            assert isinstance(key, str)
            count += 1
        assert count == 2

    def test_headers_methods(self):
        """Test Headers various methods"""
        headers = http.Headers({"Content-Type": "application/json", "X-Custom": "value"})

        # Test keys(), values(), items()
        keys = headers.keys()
        values = headers.values()
        items = headers.items()

        assert len(keys) == 2
        assert len(values) == 2
        assert len(items) == 2

        assert "application/json" in values
        assert "value" in values

    def test_headers_modification(self):
        """Test Headers modification operations"""
        headers = http.Headers()

        # Test setting headers
        headers["Content-Type"] = "application/json"
        assert headers["content-type"] == "application/json"

        # Test update
        headers.update({"X-Custom": "value"})
        assert len(headers) == 2

        # Test deletion
        headers["X-Test"] = "test-value"
        assert len(headers) == 3
        del headers["x-test"]  # Test case-insensitive deletion
        assert len(headers) == 2
        assert "x-test" not in headers

    def test_headers_httpx_compatibility(self):
        """Test Headers compatibility with httpx.Headers"""
        data = {"Content-Type": "application/json", "X-Custom": "value"}
        httpx_headers = httpx.Headers(data)
        faster_headers = http.Headers(data)

        # Test case-insensitive access compatibility
        assert httpx_headers["content-type"] == faster_headers["content-type"]
        assert len(httpx_headers) == len(faster_headers)


class TestCookies:
    """Test Cookies class compatibility with httpx.Cookies"""

    def test_cookies_creation(self):
        """Test Cookies creation and basic operations"""
        cookies = http.Cookies({"session": "abc123", "user": "john"})
        assert len(cookies) == 2
        assert "session" in cookies

    def test_cookies_access(self):
        """Test Cookies access methods"""
        cookies = http.Cookies({"session": "abc123", "user": "john"})

        # Test direct access
        assert cookies["session"] == "abc123"
        assert cookies["user"] == "john"

        # Test get method
        assert cookies.get("session") == "abc123"
        assert cookies.get("nonexistent") is None
        assert cookies.get("nonexistent", "default") == "default"

    def test_cookies_iteration(self):
        """Test Cookies iteration"""
        cookies = http.Cookies({"session": "abc123", "user": "john", "theme": "dark"})

        # Test iteration
        keys = list(cookies)
        assert len(keys) == 3
        assert "session" in keys
        assert "user" in keys
        assert "theme" in keys

        # Test for loop
        count = 0
        for key in cookies:
            assert isinstance(key, str)
            count += 1
        assert count == 3

    def test_cookies_methods(self):
        """Test Cookies various methods"""
        cookies = http.Cookies({"session": "abc123", "user": "john"})

        # Test keys(), values(), items()
        keys = cookies.keys()
        values = cookies.values()
        items = cookies.items()

        assert len(keys) == 2
        assert len(values) == 2
        assert len(items) == 2

        assert "session" in keys
        assert "abc123" in values
        assert ("session", "abc123") in items

    def test_cookies_modification(self):
        """Test Cookies modification operations"""
        cookies = http.Cookies()

        # Test setting cookies
        cookies["session"] = "abc123"
        assert cookies["session"] == "abc123"

        # Test set method with domain (domain should be ignored for now)
        cookies.set("user", "john", domain="example.com")
        assert cookies["user"] == "john"

        # Test update
        cookies.update({"theme": "dark"})
        assert len(cookies) == 3

        # Test deletion
        cookies["temp"] = "temp-value"
        assert len(cookies) == 4
        del cookies["temp"]
        assert len(cookies) == 3
        assert "temp" not in cookies

    def test_cookies_httpx_compatibility(self):
        """Test Cookies basic compatibility with httpx.Cookies"""
        data = {"session": "abc123", "user": "john"}
        httpx_cookies = httpx.Cookies(data)
        faster_cookies = http.Cookies(data)

        # Test basic functionality compatibility
        assert httpx_cookies["session"] == faster_cookies["session"]
        assert len(httpx_cookies) == len(faster_cookies)


class TestIntegration:
    """Integration tests for tool classes working together"""

    def test_url_with_query_params(self):
        """Test URL working with QueryParams"""
        url = http.URL("https://api.example.com/search?q=python&limit=10")
        params = url.params

        # Test that params work correctly
        params_dict = dict(params.items())
        assert params_dict["q"] == "python"
        assert params_dict["limit"] == "10"

    def test_tool_classes_in_request_context(self):
        """Test that tool classes work in HTTP request context"""
        # This test ensures tool classes can be used with Client
        url = http.URL("https://httpbin.org/get")
        headers = http.Headers({"User-Agent": "faster-http-test"})
        cookies = http.Cookies({"test": "value"})

        # Verify objects are created successfully and have expected properties
        assert str(url) == "https://httpbin.org/get"
        assert headers["user-agent"] == "faster-http-test"
        assert cookies["test"] == "value"

        # Test that they can be iterated (important for HTTP client usage)
        assert len(list(headers)) >= 1
        assert len(list(cookies)) >= 1
