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
