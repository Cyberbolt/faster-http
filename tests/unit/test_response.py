"""
Unit tests for Response object functionality.
Tests response object properties and methods.
Following CLAUDE.md requirements: test httpx first, then faster_http for comparison.
Based on accurate httpx documentation.
"""

import httpx

import faster_http


class TestResponseInterface:
    """Test Response object interface and properties - httpx vs faster_http comparison."""

    def test_response_basic_attributes_comparison(self):
        """Test that Response objects have required attributes - httpx vs faster_http."""
        url = "https://httpbin.org/get"

        # First test httpx Response attributes (based on official httpx API docs)
        httpx_response = httpx.get(url)

        # Test basic httpx Response attributes from official API documentation
        httpx_attrs = [
            "status_code",
            "reason_phrase",
            "http_version",
            "url",
            "headers",
            "content",
            "text",
            "encoding",
            "is_redirect",
            "request",
            "next_request",
            "cookies",
            "history",
            "elapsed",
        ]

        for attr in httpx_attrs:
            assert hasattr(httpx_response, attr), f"httpx Response missing {attr}"

        # Test httpx methods from official API documentation
        httpx_methods = [
            "raise_for_status",
            "json",
            "read",
            "iter_bytes",
            "iter_text",
            "iter_lines",
            "iter_raw",
            "close",
        ]
        for method in httpx_methods:
            assert hasattr(httpx_response, method), f"httpx Response missing {method}"
            assert callable(getattr(httpx_response, method)), f"httpx Response {method} not callable"

        # Test httpx success property (documented as is_success)
        assert hasattr(httpx_response, "is_success"), "httpx Response missing is_success"

        # Then test faster_http Response attributes
        faster_response = faster_http.get(url)

        # Test that faster_http Response has all httpx attributes
        for attr in httpx_attrs:
            assert hasattr(faster_response, attr), f"faster_http Response missing httpx-compatible {attr}"

        # Test that faster_http Response has all httpx methods
        for method in httpx_methods:
            assert hasattr(faster_response, method), f"faster_http Response missing httpx-compatible {method}"
            assert callable(getattr(faster_response, method)), f"faster_http Response {method} not callable"

        # Test faster_http success property (should match httpx)
        assert hasattr(faster_response, "is_success"), "faster_http Response missing httpx-compatible is_success"

    def test_response_status_code_comparison(self):
        """Test Response status_code property - httpx vs faster_http."""
        url = "https://httpbin.org/get"

        # First test httpx Response status_code
        httpx_response = httpx.get(url)
        assert httpx_response.status_code == 200
        assert isinstance(httpx_response.status_code, int)

        # Then test faster_http Response status_code
        faster_response = faster_http.get(url)
        assert faster_response.status_code == 200
        assert isinstance(faster_response.status_code, int)

        # Both should have the same status code
        assert httpx_response.status_code == faster_response.status_code

    def test_response_headers_comparison(self):
        """Test Response headers property - httpx vs faster_http."""
        url = "https://httpbin.org/headers"
        headers = {"X-Test-Header": "test-value", "User-Agent": "test-client"}

        # First test httpx Response headers
        httpx_response = httpx.get(url, headers=headers)
        assert httpx_response.status_code == 200

        # Test httpx headers properties (case-insensitive per docs)
        assert hasattr(httpx_response.headers, "get")
        assert callable(httpx_response.headers.get)
        assert "content-type" in httpx_response.headers  # Should be case-insensitive

        # Then test faster_http Response headers
        faster_response = faster_http.get(url, headers=headers)
        assert faster_response.status_code == 200

        # Test faster_http headers properties (should match httpx)
        assert hasattr(faster_response.headers, "get")
        assert callable(faster_response.headers.get)
        assert "content-type" in faster_response.headers  # Should be case-insensitive

        # Both should have similar headers structure
        assert httpx_response.status_code == faster_response.status_code

    def test_response_content_and_text_comparison(self):
        """Test Response content and text properties - httpx vs faster_http."""
        url = "https://httpbin.org/get"

        # First test httpx Response content and text
        httpx_response = httpx.get(url)
        assert httpx_response.status_code == 200

        # Test httpx content and text properties
        httpx_content = httpx_response.content
        assert isinstance(httpx_content, bytes)
        assert len(httpx_content) > 0

        httpx_text = httpx_response.text
        assert isinstance(httpx_text, str)
        assert len(httpx_text) > 0

        # Test httpx encoding property
        httpx_encoding = httpx_response.encoding
        assert isinstance(httpx_encoding, str)

        # Then test faster_http Response content and text
        faster_response = faster_http.get(url)
        assert faster_response.status_code == 200

        # Test faster_http content and text properties (should match httpx)
        faster_content = faster_response.content
        assert isinstance(faster_content, bytes)
        assert len(faster_content) > 0

        faster_text = faster_response.text
        assert isinstance(faster_text, str)
        assert len(faster_text) > 0

        # Test faster_http encoding property
        faster_encoding = faster_response.encoding
        assert isinstance(faster_encoding, str)

        # Both should produce similar content
        assert httpx_response.status_code == faster_response.status_code

    def test_response_json_method_comparison(self):
        """Test Response json() method - httpx vs faster_http."""
        url = "https://httpbin.org/get"

        # First test httpx Response json() method
        httpx_response = httpx.get(url)
        assert httpx_response.status_code == 200

        httpx_json = httpx_response.json()
        assert isinstance(httpx_json, dict)
        assert "url" in httpx_json  # httpbin.org/get returns request info

        # Then test faster_http Response json() method
        faster_response = faster_http.get(url)
        assert faster_response.status_code == 200

        faster_json = faster_response.json()
        assert isinstance(faster_json, dict)
        assert "url" in faster_json  # Both should have url field

        # Both should produce valid JSON with required fields
        assert httpx_response.status_code == faster_response.status_code
        # Both JSON responses should have the same structure
        assert set(httpx_json.keys()) == set(faster_json.keys())
        assert httpx_json["url"] == faster_json["url"]  # URL should be the same

    def test_response_is_success_comparison(self):
        """Test Response is_success property - httpx vs faster_http."""
        # Test successful response (documented as is_success for 2xx status codes)
        success_url = "https://httpbin.org/get"

        # First test httpx is_success for success
        httpx_success = httpx.get(success_url)
        assert httpx_success.status_code == 200
        assert httpx_success.is_success  # Official httpx API docs confirm this property

        # Then test faster_http is_success for success
        faster_success = faster_http.get(success_url)
        assert faster_success.status_code == 200
        assert faster_success.is_success  # Should match httpx

        # Both should agree on success status
        assert httpx_success.status_code == faster_success.status_code
        assert httpx_success.is_success == faster_success.is_success

        # Test client error response
        error_url = "https://httpbin.org/status/404"

        # First test httpx is_success for error
        httpx_error = httpx.get(error_url)
        assert httpx_error.status_code == 404
        assert not httpx_error.is_success  # Should be False for 4xx

        # Then test faster_http is_success for error
        faster_error = faster_http.get(error_url)
        assert faster_error.status_code == 404
        assert not faster_error.is_success  # Should match httpx

        # Both should agree on error status
        assert httpx_error.status_code == faster_error.status_code
        assert httpx_error.is_success == faster_error.is_success

    def test_response_is_redirect_comparison(self):
        """Test Response is_redirect property - httpx vs faster_http."""
        # Test redirect response
        redirect_url = "https://httpbin.org/redirect-to?url=https://httpbin.org/get"

        # First test httpx is_redirect
        httpx_response = httpx.get(redirect_url, follow_redirects=False)
        assert httpx_response.status_code == 302
        assert httpx_response.is_redirect  # Official httpx API docs confirm this property

        # Then test faster_http is_redirect
        faster_response = faster_http.get(redirect_url, follow_redirects=False)
        assert faster_response.status_code == 302
        assert faster_response.is_redirect  # Should match httpx

        # Both should agree on redirect status
        assert httpx_response.status_code == faster_response.status_code
        assert httpx_response.is_redirect == faster_response.is_redirect

        # Test non-redirect response
        normal_url = "https://httpbin.org/get"

        # First test httpx is_redirect for normal response
        httpx_normal = httpx.get(normal_url)
        assert httpx_normal.status_code == 200
        assert not httpx_normal.is_redirect

        # Then test faster_http is_redirect for normal response
        faster_normal = faster_http.get(normal_url)
        assert faster_normal.status_code == 200
        assert not faster_normal.is_redirect

        # Both should agree on non-redirect status
        assert httpx_normal.is_redirect == faster_normal.is_redirect

    def test_response_raise_for_status_comparison(self):
        """Test Response raise_for_status() method - httpx vs faster_http."""
        # Test successful response doesn't raise
        success_url = "https://httpbin.org/get"

        # First test httpx raise_for_status for success
        httpx_success = httpx.get(success_url)
        assert httpx_success.status_code == 200

        # Should not raise for 200 status
        try:
            httpx_success.raise_for_status()
        except Exception:
            raise AssertionError("httpx raise_for_status should not raise for 200 status")

        # Then test faster_http raise_for_status for success
        faster_success = faster_http.get(success_url)
        assert faster_success.status_code == 200

        # Should not raise for 200 status
        try:
            faster_success.raise_for_status()
        except Exception:
            raise AssertionError("faster_http raise_for_status should not raise for 200 status")

        # Test error response raises exception
        error_url = "https://httpbin.org/status/404"

        # First test httpx raise_for_status for error
        httpx_error = httpx.get(error_url)
        assert httpx_error.status_code == 404

        # Should raise HTTPStatusError for 404 status (per httpx docs)
        try:
            httpx_error.raise_for_status()
            raise AssertionError("httpx raise_for_status should raise for 404 status")
        except httpx.HTTPStatusError as e:
            assert e.response.status_code == 404

        # Then test faster_http raise_for_status for error
        faster_error = faster_http.get(error_url)
        assert faster_error.status_code == 404

        # Should raise HTTPStatusError for 404 status (same as httpx)
        try:
            faster_error.raise_for_status()
            raise AssertionError("faster_http raise_for_status should raise for 404 status")
        except faster_http.HTTPStatusError as e:
            assert e.response.status_code == 404

        # Both should handle errors the same way
        assert httpx_error.status_code == faster_error.status_code

    def test_response_url_property_comparison(self):
        """Test Response url property - httpx vs faster_http."""
        url = "https://httpbin.org/get"

        # First test httpx Response url property (httpx.URL type per docs)
        httpx_response = httpx.get(url)
        assert httpx_response.status_code == 200

        httpx_url = httpx_response.url
        assert str(httpx_url) == url  # Convert to string for comparison

        # Then test faster_http Response url property
        faster_response = faster_http.get(url)
        assert faster_response.status_code == 200

        faster_url = faster_response.url
        assert str(faster_url) == url

        # Both should have the same URL
        assert str(httpx_url) == str(faster_url)

    def test_response_cookies_property_comparison(self):
        """Test Response cookies property - httpx vs faster_http."""
        url = "https://httpbin.org/cookies"
        cookies = {"test": "value"}

        # First test httpx Response cookies property (httpx.Cookies per docs)
        httpx_response = httpx.get(url, cookies=cookies)
        assert httpx_response.status_code == 200

        httpx_cookies = httpx_response.cookies
        assert hasattr(httpx_cookies, "__getitem__")  # Should be dict-like

        # Then test faster_http Response cookies property
        faster_response = faster_http.get(url, cookies=cookies)
        assert faster_response.status_code == 200

        faster_cookies = faster_response.cookies
        assert hasattr(faster_cookies, "__getitem__")  # Should be dict-like

        # Both should have cookies structure
        assert httpx_response.status_code == faster_response.status_code

    def test_response_elapsed_property_comparison(self):
        """Test Response elapsed property - httpx vs faster_http."""
        url = "https://httpbin.org/get"

        # First test httpx Response elapsed property (datetime.timedelta per docs)
        httpx_response = httpx.get(url)
        assert httpx_response.status_code == 200

        httpx_elapsed = httpx_response.elapsed
        # Should be a timedelta-like object with total_seconds method
        assert hasattr(httpx_elapsed, "total_seconds")
        assert httpx_elapsed.total_seconds() >= 0

        # Then test faster_http Response elapsed property
        faster_response = faster_http.get(url)
        assert faster_response.status_code == 200

        faster_elapsed = faster_response.elapsed
        # Should match httpx interface
        assert hasattr(faster_elapsed, "total_seconds")
        assert faster_elapsed.total_seconds() >= 0

        # Both should have reasonable elapsed times
        assert httpx_response.status_code == faster_response.status_code
