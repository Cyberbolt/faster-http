"""Tests for utility classes and functions."""

from tests.utils.httpx_comparison import httpx_compatibility_test


class TestUtils:
    """Test utility classes and functions."""

    @httpx_compatibility_test
    def test_url_creation(self, client_factory):
        """Test URL class creation and methods."""
        # TDD: Red phase - this will fail initially
        import faster_http

        url = faster_http.URL("https://localhost:8080/path?query=value")
        assert str(url) == "https://localhost:8080/path?query=value"
        assert url.scheme == "https"
        assert url.host == "localhost"
        assert url.path == "/path"

    @httpx_compatibility_test
    def test_url_join(self, client_factory):
        """Test URL joining functionality."""
        # TDD: Red phase - this will fail initially
        import faster_http

        base = faster_http.URL("https://localhost:8080/")
        joined = base.join("path/to/resource")
        assert str(joined) == "https://localhost:8080/path/to/resource"

    @httpx_compatibility_test
    def test_headers_creation(self, client_factory):
        """Test Headers class creation and methods."""
        # TDD: Red phase - this will fail initially
        import faster_http

        headers = faster_http.Headers({"Content-Type": "application/json"})
        assert headers["content-type"] == "application/json"
        assert "Content-Type" in headers

    @httpx_compatibility_test
    def test_headers_case_insensitive(self, client_factory):
        """Test Headers are case-insensitive like httpx."""
        # TDD: Red phase - this will fail initially
        import faster_http

        headers = faster_http.Headers({"Content-Type": "application/json"})
        assert headers["content-type"] == "application/json"
        assert headers["CONTENT-TYPE"] == "application/json"
        assert headers.get("Content-Type") == "application/json"

    @httpx_compatibility_test
    def test_query_params_creation(self, client_factory):
        """Test QueryParams class creation and methods."""
        # TDD: Red phase - this will fail initially
        import faster_http

        params = faster_http.QueryParams("key=value&test=data")
        assert "key" in params
        assert params["key"] == "value"
        assert params.get("test") == "data"

    @httpx_compatibility_test
    def test_query_params_from_dict(self, client_factory):
        """Test QueryParams from dictionary."""
        # TDD: Red phase - this will fail initially
        import faster_http

        params = faster_http.QueryParams({"key": "value", "test": ["data1", "data2"]})
        assert params["key"] == "value"
        assert params.get_list("test") == ["data1", "data2"]

    @httpx_compatibility_test
    def test_cookies_creation(self, client_factory):
        """Test Cookies class creation and methods."""
        # TDD: Red phase - this will fail initially
        import faster_http

        cookies = faster_http.Cookies({"session": "abc123"})
        assert cookies["session"] == "abc123"
        assert "session" in cookies

    @httpx_compatibility_test
    def test_cookies_from_response(self, client_factory, test_server):
        """Test extracting cookies from response."""
        # TDD: Red phase - this will fail initially
        response = client_factory.get(f"{test_server.base_url}/cookies/set/test/value")
        assert "test" in response.cookies
        assert response.cookies["test"] == "value"

    def test_codes_module(self):
        """Test codes module functionality."""
        # TDD: Red phase - this will fail initially
        import faster_http

        assert faster_http.codes.OK == 200
        assert faster_http.codes.NOT_FOUND == 404
        assert faster_http.codes.INTERNAL_SERVER_ERROR == 500
