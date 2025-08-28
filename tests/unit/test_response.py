"""Tests for Response objects."""

import pytest

from tests.utils.httpx_comparison import httpx_compatibility_test


class TestResponse:
    """Test Response object functionality."""

    @pytest.fixture(autouse=True)
    def setup(self, test_server):
        """Setup for each test."""
        self.base_url = test_server.base_url

    @httpx_compatibility_test
    def test_response_status_code(self, client_factory):
        """Test response status code property."""
        # TDD: Red phase - this will fail initially
        response = client_factory.get(f"{self.base_url}/get")
        assert response.status_code == 200
        assert isinstance(response.status_code, int)

    @httpx_compatibility_test
    def test_response_headers(self, client_factory):
        """Test response headers property."""
        # TDD: Red phase - this will fail initially
        response = client_factory.get(f"{self.base_url}/get")
        assert response.headers is not None
        assert "content-type" in response.headers

    @httpx_compatibility_test
    def test_response_text(self, client_factory):
        """Test response text property."""
        # TDD: Red phase - this will fail initially
        response = client_factory.get(f"{self.base_url}/get")
        assert isinstance(response.text, str)
        assert len(response.text) > 0

    @httpx_compatibility_test
    def test_response_content(self, client_factory):
        """Test response content property."""
        # TDD: Red phase - this will fail initially
        response = client_factory.get(f"{self.base_url}/get")
        assert isinstance(response.content, bytes)
        assert len(response.content) > 0

    @httpx_compatibility_test
    def test_response_json(self, client_factory):
        """Test response json() method."""
        # TDD: Red phase - this will fail initially
        response = client_factory.get(f"{self.base_url}/json")
        json_data = response.json()
        assert isinstance(json_data, dict)

    @httpx_compatibility_test
    def test_response_url(self, client_factory):
        """Test response url property."""
        # TDD: Red phase - this will fail initially
        response = client_factory.get(f"{self.base_url}/get")
        assert response.url is not None
        assert str(response.url).startswith(self.base_url)

    @httpx_compatibility_test
    def test_response_cookies(self, client_factory):
        """Test response cookies property."""
        # TDD: Red phase - this will fail initially
        response = client_factory.get(f"{self.base_url}/cookies/set/test/value")
        assert response.cookies is not None

    @httpx_compatibility_test
    def test_response_history(self, client_factory):
        """Test response history property for redirects."""
        # TDD: Red phase - this will fail initially
        response = client_factory.get(f"{self.base_url}/redirect/1")
        assert hasattr(response, "history")

    @httpx_compatibility_test
    def test_response_elapsed(self, client_factory):
        """Test response elapsed property."""
        # TDD: Red phase - this will fail initially
        response = client_factory.get(f"{self.base_url}/get")
        assert hasattr(response, "elapsed")

    @httpx_compatibility_test
    def test_response_encoding(self, client_factory):
        """Test response encoding property."""
        # TDD: Red phase - this will fail initially
        response = client_factory.get(f"{self.base_url}/get")
        assert hasattr(response, "encoding")

    @httpx_compatibility_test
    def test_response_is_error(self, client_factory):
        """Test response.is_error property."""
        # TDD: Red phase - this will fail initially
        response = client_factory.get(f"{self.base_url}/get")
        assert response.is_error is False

        error_response = client_factory.get(f"{self.base_url}/status/404")
        assert error_response.is_error is True

    @httpx_compatibility_test
    def test_response_raise_for_status(self, client_factory):
        """Test response.raise_for_status() method."""
        # TDD: Red phase - this will fail initially
        response = client_factory.get(f"{self.base_url}/get")
        response.raise_for_status()  # Should not raise

        error_response = client_factory.get(f"{self.base_url}/status/404")
        with pytest.raises((Exception, AttributeError)):
            error_response.raise_for_status()

    # === High Priority Response Property Tests ===

    @httpx_compatibility_test
    def test_response_reason_phrase(self, client_factory):
        """Test response.reason_phrase property for different status codes."""
        # Test 200 OK
        response = client_factory.get(f"{self.base_url}/get")
        assert hasattr(response, "reason_phrase")
        assert response.reason_phrase == "OK"

        # Test 404 Not Found
        response_404 = client_factory.get(f"{self.base_url}/status/404")
        assert response_404.reason_phrase == "Not Found"

        # Test 500 Internal Server Error
        response_500 = client_factory.get(f"{self.base_url}/status/500")
        assert response_500.reason_phrase == "Internal Server Error"

        # Test 302 Found (redirect)
        response_302 = client_factory.get(f"{self.base_url}/status/302")
        assert response_302.reason_phrase == "Found"

    @httpx_compatibility_test
    def test_response_is_redirect(self, client_factory):
        """Test response.is_redirect property for redirect status codes."""
        # Test non-redirect responses
        response = client_factory.get(f"{self.base_url}/get")
        assert hasattr(response, "is_redirect")
        assert response.is_redirect is False

        response_404 = client_factory.get(f"{self.base_url}/status/404")
        assert response_404.is_redirect is False

        # Test redirect responses
        response_301 = client_factory.get(f"{self.base_url}/status/301")
        assert response_301.is_redirect is True

        response_302 = client_factory.get(f"{self.base_url}/status/302")
        assert response_302.is_redirect is True

        response_304 = client_factory.get(f"{self.base_url}/status/304")
        assert response_304.is_redirect is True

        response_307 = client_factory.get(f"{self.base_url}/status/307")
        assert response_307.is_redirect is True

    @httpx_compatibility_test
    def test_response_is_client_error(self, client_factory):
        """Test response.is_client_error property for 4xx status codes."""
        # Test non-client-error responses
        response = client_factory.get(f"{self.base_url}/get")
        assert hasattr(response, "is_client_error")
        assert response.is_client_error is False

        response_500 = client_factory.get(f"{self.base_url}/status/500")
        assert response_500.is_client_error is False

        # Test client error responses
        response_400 = client_factory.get(f"{self.base_url}/status/400")
        assert response_400.is_client_error is True

        response_401 = client_factory.get(f"{self.base_url}/status/401")
        assert response_401.is_client_error is True

        response_404 = client_factory.get(f"{self.base_url}/status/404")
        assert response_404.is_client_error is True

        response_422 = client_factory.get(f"{self.base_url}/status/422")
        assert response_422.is_client_error is True

    @httpx_compatibility_test
    def test_response_is_server_error(self, client_factory):
        """Test response.is_server_error property for 5xx status codes."""
        # Test non-server-error responses
        response = client_factory.get(f"{self.base_url}/get")
        assert hasattr(response, "is_server_error")
        assert response.is_server_error is False

        response_404 = client_factory.get(f"{self.base_url}/status/404")
        assert response_404.is_server_error is False

        # Test server error responses
        response_500 = client_factory.get(f"{self.base_url}/status/500")
        assert response_500.is_server_error is True

        response_502 = client_factory.get(f"{self.base_url}/status/502")
        assert response_502.is_server_error is True

        response_503 = client_factory.get(f"{self.base_url}/status/503")
        assert response_503.is_server_error is True

    @httpx_compatibility_test
    def test_response_encoding_with_different_content_types(self, client_factory):
        """Test response.encoding property with different content types."""
        # Test default encoding
        response = client_factory.get(f"{self.base_url}/get")
        assert hasattr(response, "encoding")

        # Test that encoding property exists and is accessible
        encoding = response.encoding
        assert isinstance(encoding, str) or encoding is None

        # If encoding is not None, it should be a valid encoding name
        if encoding is not None:
            assert isinstance(encoding, str)
            assert len(encoding) > 0

    @httpx_compatibility_test
    def test_response_properties_consistency(self, client_factory):
        """Test that response properties are consistent with status codes."""
        # Test 200 - success
        response_200 = client_factory.get(f"{self.base_url}/get")
        assert response_200.reason_phrase == "OK"
        assert response_200.is_redirect is False
        assert response_200.is_client_error is False
        assert response_200.is_server_error is False

        # Test 302 - redirect
        response_302 = client_factory.get(f"{self.base_url}/status/302")
        assert response_302.reason_phrase == "Found"
        assert response_302.is_redirect is True
        assert response_302.is_client_error is False
        assert response_302.is_server_error is False

        # Test 404 - client error
        response_404 = client_factory.get(f"{self.base_url}/status/404")
        assert response_404.reason_phrase == "Not Found"
        assert response_404.is_redirect is False
        assert response_404.is_client_error is True
        assert response_404.is_server_error is False

        # Test 500 - server error
        response_500 = client_factory.get(f"{self.base_url}/status/500")
        assert response_500.reason_phrase == "Internal Server Error"
        assert response_500.is_redirect is False
        assert response_500.is_client_error is False
        assert response_500.is_server_error is True
