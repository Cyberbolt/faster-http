"""Tests for Request objects."""

import pytest

from tests.utils.httpx_comparison import httpx_compatibility_test


class TestRequest:
    """Test Request object functionality."""

    @pytest.fixture(autouse=True)
    def setup(self, test_server):
        """Setup for each test."""
        self.base_url = test_server.base_url

    @httpx_compatibility_test
    def test_request_method(self, client_factory):
        """Test request method property."""
        # TDD: Red phase - this will fail initially
        with client_factory() as client:
            request = client.build_request("GET", f"{self.base_url}/get")
            assert request.method == "GET"

    @httpx_compatibility_test
    def test_request_url(self, client_factory):
        """Test request url property."""
        # TDD: Red phase - this will fail initially
        with client_factory() as client:
            url = f"{self.base_url}/get"
            request = client.build_request("GET", url)
            assert str(request.url) == url

    @httpx_compatibility_test
    def test_request_headers(self, client_factory):
        """Test request headers property."""
        # TDD: Red phase - this will fail initially
        with client_factory() as client:
            headers = {"User-Agent": "test-agent"}
            request = client.build_request("GET", f"{self.base_url}/get", headers=headers)
            assert "User-Agent" in request.headers
            assert request.headers["User-Agent"] == "test-agent"

    @httpx_compatibility_test
    def test_request_content(self, client_factory):
        """Test request content property."""
        # TDD: Red phase - this will fail initially
        with client_factory() as client:
            data = b"test data"
            request = client.build_request("POST", f"{self.base_url}/post", content=data)
            assert request.content == data

    @httpx_compatibility_test
    def test_request_json(self, client_factory):
        """Test request with JSON data."""
        # TDD: Red phase - this will fail initially
        with client_factory() as client:
            json_data = {"key": "value"}
            request = client.build_request("POST", f"{self.base_url}/post", json=json_data)
            assert request.headers.get("content-type") == "application/json"

    @httpx_compatibility_test
    def test_request_params(self, client_factory):
        """Test request with query parameters."""
        # TDD: Red phase - this will fail initially
        with client_factory() as client:
            params = {"key": "value", "test": "data"}
            request = client.build_request("GET", f"{self.base_url}/get", params=params)
            assert "key=value" in str(request.url)
            assert "test=data" in str(request.url)

    @httpx_compatibility_test
    def test_request_cookies(self, client_factory):
        """Test request with cookies."""
        # TDD: Red phase - this will fail initially
        with client_factory() as client:
            cookies = {"session": "abc123"}
            request = client.build_request("GET", f"{self.base_url}/get", cookies=cookies)
            assert "Cookie" in request.headers or "cookie" in request.headers
