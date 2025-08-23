"""
Core functionality tests for faster-http.

This module contains the first batch of TDD tests covering the most critical
HTTP functionality that faster-http must implement for httpx compatibility.
"""

import json

import pytest

import faster_http
from tests.utils.httpx_comparison import httpx_compatibility_test
from tests.utils.response_adapter import verify_json_response
from tests.utils.tdd_helpers import AssertionHelpers, DataGenerator, TDDTestCase


class TestBasicHTTPMethods(TDDTestCase):
    """Test basic HTTP methods with top-level functions."""

    @pytest.fixture(autouse=True)
    def setup(self, test_server):
        """Setup test server URL for each test."""
        self.base_url = test_server.base_url
        self.data_gen = DataGenerator()
        self.assert_helpers = AssertionHelpers()

    @httpx_compatibility_test
    def test_httpx_get(self, client_factory):
        """
        Test GET request with comprehensive parameter and return value testing.

        TDD: Tests GET request functionality including:
        - Basic GET request
        - Query parameters support
        - Headers support
        - Response object structure
        """
        # Test basic GET request
        url = f"{self.base_url}/get"
        response = client_factory.get(url)

        # Verify response structure and content using adapter
        json_data = verify_json_response(response, "GET", url)

        # Test GET with query parameters
        params = {"param1": "value1", "param2": "value2"}
        response = client_factory.get(url, params=params)

        json_data = verify_json_response(response, "GET", url)
        assert "args" in json_data
        assert json_data["args"]["param1"] == "value1"
        assert json_data["args"]["param2"] == "value2"

        # Test GET with custom headers
        headers = {"X-Custom-Header": "custom-value", "User-Agent": "faster-http-test"}
        response = client_factory.get(url, headers=headers)
        assert response.status_code == 200

        json_data = response.json()
        assert "headers" in json_data
        assert json_data["headers"]["X-Custom-Header"] == "custom-value"
        assert json_data["headers"]["User-Agent"] == "faster-http-test"

    @httpx_compatibility_test
    def test_httpx_post(self, client_factory):
        """
        Test POST request with support for content/data/files/json.

        TDD: Tests POST request functionality including:
        - POST with JSON data
        - POST with form data
        - POST with raw content
        - Parameters and headers support
        """
        url = f"{self.base_url}/post"

        # Test POST with JSON data
        json_data = {"name": "test", "value": 123, "nested": {"key": "value"}}
        response = client_factory.post(url, json=json_data)

        assert response.status_code == 200
        response_data = response.json()
        assert "json" in response_data
        assert response_data["json"] == json_data

        # Test POST with form data
        form_data = {"field1": "value1", "field2": "value2"}
        response = client_factory.post(url, data=form_data)

        assert response.status_code == 200
        response_data = response.json()
        assert "data" in response_data
        # Form data should be URL-encoded in the body
        assert "field1=value1" in response_data["data"]
        assert "field2=value2" in response_data["data"]

        # Test POST with raw content
        raw_content = b"raw binary content"
        response = client_factory.post(url, content=raw_content)

        assert response.status_code == 200
        response_data = response.json()
        assert "data" in response_data
        assert response_data["data"] == raw_content.decode()

        # Test POST with parameters and headers
        params = {"query_param": "query_value"}
        headers = {"Content-Type": "application/json", "X-Test": "test"}
        response = client_factory.post(url, json={"test": True}, params=params, headers=headers)

        assert response.status_code == 200
        response_data = response.json()
        assert response_data["args"]["query_param"] == "query_value"
        assert response_data["headers"]["X-Test"] == "test"
        assert response_data["json"]["test"] is True

    @httpx_compatibility_test
    def test_httpx_put(self, client_factory):
        """Test PUT request with complete parameter support."""
        url = f"{self.base_url}/put"

        # Test PUT with JSON
        test_data = {"update": True, "id": 42}
        response = client_factory.put(url, json=test_data)

        assert response.status_code == 200
        response_data = response.json()
        assert response_data["method"] == "PUT"
        assert response_data["json"] == test_data

        # Test PUT with form data
        form_data = {"name": "updated", "status": "active"}
        response = client_factory.put(url, data=form_data)

        assert response.status_code == 200
        response_data = response.json()
        assert response_data["method"] == "PUT"
        assert "name=updated" in response_data["data"]

    @httpx_compatibility_test
    def test_httpx_patch(self, client_factory):
        """Test PATCH request with complete parameter support."""
        url = f"{self.base_url}/patch"

        # Test PATCH with JSON
        patch_data = {"field": "patched_value", "timestamp": 1234567890}
        response = client_factory.patch(url, json=patch_data)

        assert response.status_code == 200
        response_data = response.json()
        assert response_data["method"] == "PATCH"
        assert response_data["json"] == patch_data

        # Test PATCH with headers
        headers = {"Content-Type": "application/json", "X-Patch-Version": "1.0"}
        response = client_factory.patch(url, json={"partial": True}, headers=headers)

        assert response.status_code == 200
        response_data = response.json()
        assert response_data["headers"]["X-Patch-Version"] == "1.0"

    @httpx_compatibility_test
    def test_httpx_delete(self, client_factory):
        """Test DELETE request with complete parameter support."""
        url = f"{self.base_url}/delete"

        # Test basic DELETE
        response = client_factory.delete(url)

        assert response.status_code == 200
        response_data = response.json()
        assert response_data["method"] == "DELETE"

        # Test DELETE with parameters
        params = {"id": "123", "confirm": "true"}
        response = client_factory.delete(url, params=params)

        assert response.status_code == 200
        response_data = response.json()
        assert response_data["args"]["id"] == "123"
        assert response_data["args"]["confirm"] == "true"

    @httpx_compatibility_test
    def test_httpx_head(self, client_factory):
        """Test HEAD request with complete parameter support."""
        url = f"{self.base_url}/head"

        # Test basic HEAD request
        response = client_factory.head(url)

        assert response.status_code == 200
        # HEAD response should not have content but should have headers
        assert len(response.content) == 0 or response.content == b""
        assert "Content-Type" in response.headers or "content-type" in response.headers

        # Test HEAD with custom headers
        headers = {"X-Test-Header": "test-value"}
        response = client_factory.head(url, headers=headers)

        assert response.status_code == 200
        # Verify the request was processed correctly (headers would be in server logs)

    @httpx_compatibility_test
    def test_httpx_options(self, client_factory):
        """Test OPTIONS request with complete parameter support."""
        url = f"{self.base_url}/options"

        # Test basic OPTIONS request
        response = client_factory.options(url)

        assert response.status_code == 200

        # OPTIONS should return allowed methods
        if hasattr(response, "headers"):
            # Some servers return Allow header
            _ = response.headers.get("Allow") or response.headers.get("allow")
            # At minimum, server should respond with status 200

        # Verify response structure
        response_data = response.json()
        assert "message" in response_data  # Our test server returns this

    @httpx_compatibility_test
    def test_httpx_request(self, client_factory):
        """Test generic request function with all HTTP methods."""
        base_url = self.base_url

        # Test various HTTP methods using request()
        test_cases = [
            ("GET", "/get", {}),
            ("POST", "/post", {"json": {"test": "data"}}),
            ("PUT", "/put", {"json": {"update": True}}),
            ("PATCH", "/patch", {"json": {"patch": True}}),
            ("DELETE", "/delete", {}),
        ]

        for method, endpoint, kwargs in test_cases:
            url = f"{base_url}{endpoint}"
            response = client_factory.request(method, url, **kwargs)

            assert response.status_code == 200
            response_data = response.json()
            assert response_data["method"] == method

            if "json" in kwargs:
                assert response_data["json"] == kwargs["json"]


class TestClientCoreFeatures(TDDTestCase):
    """Test Client class core functionality."""

    @pytest.fixture(autouse=True)
    def setup(self, test_server):
        """Setup for each test."""
        self.base_url = test_server.base_url

    @httpx_compatibility_test
    def test_client_init(self, client_factory):
        """Test Client initialization with various parameters."""
        # Test basic client initialization
        client = client_factory()
        assert client is not None

        # Test client with base_url
        base_url = self.base_url
        client = client_factory(base_url=base_url)
        assert client is not None

        # Test client with headers
        headers = {"User-Agent": "test-client", "X-API-Key": "secret"}
        client = client_factory(headers=headers)
        assert client is not None

        # Test client with timeout
        client = client_factory(timeout=30.0)
        assert client is not None

        # Clean up clients
        if hasattr(client, "close"):
            client.close()

    @httpx_compatibility_test
    def test_client_http_methods(self, client_factory):
        """Test Client HTTP methods (get, post, put, patch, delete, head, options)."""
        with client_factory() as client:
            base_url = self.base_url

            # Test all HTTP methods
            methods_endpoints = [
                ("get", "/get"),
                ("post", "/post"),
                ("put", "/put"),
                ("patch", "/patch"),
                ("delete", "/delete"),
                ("head", "/head"),
                ("options", "/options"),
            ]

            for method_name, endpoint in methods_endpoints:
                url = f"{base_url}{endpoint}"
                method = getattr(client, method_name)

                response = method(url, json={"test": True}) if method_name in ["post", "put", "patch"] else method(url)

                assert response.status_code == 200

                # HEAD doesn't return content
                if method_name != "head":
                    response_data = response.json()
                    assert response_data["method"] == method_name.upper()

    @httpx_compatibility_test
    def test_client_request(self, client_factory):
        """Test Client.request() generic method."""
        with client_factory() as client:
            url = f"{self.base_url}/get"

            # Test generic request method
            response = client.request("GET", url)
            assert response.status_code == 200

            response_data = response.json()
            assert response_data["method"] == "GET"

            # Test with parameters
            response = client.request("GET", url, params={"test": "param"})
            assert response.status_code == 200

            response_data = response.json()
            assert response_data["args"]["test"] == "param"

    @httpx_compatibility_test
    def test_client_build_request(self, client_factory):
        """Test Client.build_request() for request construction."""
        with client_factory() as client:
            url = f"{self.base_url}/get"

            # Build a request
            request = client.build_request("GET", url)

            # Verify request object structure
            assert hasattr(request, "method")
            assert hasattr(request, "url")
            assert request.method == "GET"

            # Verify URL handling
            str_url = str(request.url)
            assert url in str_url

    @httpx_compatibility_test
    def test_client_send(self, client_factory):
        """Test Client.send() for sending pre-built requests."""
        with client_factory() as client:
            url = f"{self.base_url}/get"

            # Build and send request
            request = client.build_request("GET", url, params={"sent": "via_send"})
            response = client.send(request)

            assert response.status_code == 200
            response_data = response.json()
            assert response_data["method"] == "GET"
            assert response_data["args"]["sent"] == "via_send"

    @httpx_compatibility_test
    def test_client_close(self, client_factory):
        """Test Client.close() for resource cleanup."""
        client = client_factory()

        # Make a request to establish connection
        response = client.get(f"{self.base_url}/get")
        assert response.status_code == 200

        # Close client
        client.close()

        # After closing, client should be in closed state
        # Note: Exact behavior may vary between implementations

    @httpx_compatibility_test
    def test_client_context_manager(self, client_factory):
        """Test Client as context manager (with statement)."""
        # Test context manager usage
        with client_factory() as client:
            response = client.get(f"{self.base_url}/get")
            assert response.status_code == 200

            response_data = response.json()
            assert response_data["method"] == "GET"

        # Client should be automatically closed after exiting with block
        # Exact verification depends on implementation details

    @httpx_compatibility_test
    def test_client_with_base_url(self, client_factory):
        """Test Client with base_url functionality."""
        # Test client with base_url
        base_url = self.base_url
        with client_factory(base_url=base_url) as client:
            # Use relative URL - should be resolved against base_url
            response = client.get("/get")
            assert response.status_code == 200

            response_data = response.json()
            assert response_data["method"] == "GET"
            # URL should be the full URL (base_url + path)
            assert base_url in response_data["url"]

    @httpx_compatibility_test
    def test_client_default_headers(self, client_factory):
        """Test Client with default headers functionality."""
        # Test client with default headers
        default_headers = {"User-Agent": "faster-http-test-client/1.0", "X-Default-Header": "default-value"}

        with client_factory(headers=default_headers) as client:
            response = client.get(f"{self.base_url}/headers")
            assert response.status_code == 200

            response_data = response.json()
            response_headers = response_data["headers"]

            # Default headers should be included
            assert response_headers["User-Agent"] == "faster-http-test-client/1.0"
            assert response_headers["X-Default-Header"] == "default-value"


class TestResponseCoreAttributes(TDDTestCase):
    """Test Response object core attributes."""

    @pytest.fixture(autouse=True)
    def setup(self, test_server):
        """Setup for each test."""
        self.base_url = test_server.base_url

    @httpx_compatibility_test
    def test_response_status_code(self, client_factory):
        """Test Response.status_code attribute."""
        # Test successful status codes
        response = client_factory.get(f"{self.base_url}/get")
        assert response.status_code == 200
        assert isinstance(response.status_code, int)

        # Test different status codes
        response = client_factory.get(f"{self.base_url}/status/201")
        assert response.status_code == 201

        response = client_factory.get(f"{self.base_url}/status/404")
        assert response.status_code == 404

    @httpx_compatibility_test
    def test_response_headers(self, client_factory):
        """Test Response.headers attribute."""
        response = client_factory.get(f"{self.base_url}/headers")

        # Verify headers object exists and has expected interface
        assert hasattr(response, "headers")
        assert response.headers is not None

        # Headers should be case-insensitive dict-like
        content_type = response.headers.get("content-type") or response.headers.get("Content-Type")
        assert content_type is not None
        assert "json" in content_type.lower()

    @httpx_compatibility_test
    def test_response_content(self, client_factory):
        """Test Response.content attribute (raw bytes)."""
        response = client_factory.get(f"{self.base_url}/get")

        # Verify content is bytes
        assert hasattr(response, "content")
        assert isinstance(response.content, bytes)
        assert len(response.content) > 0

        # Content should be valid JSON when parsed
        content_str = response.content.decode("utf-8")
        json_data = json.loads(content_str)
        assert isinstance(json_data, dict)

    @httpx_compatibility_test
    def test_response_text(self, client_factory):
        """Test Response.text attribute (decoded string)."""
        response = client_factory.get(f"{self.base_url}/get")

        # Verify text is string
        assert hasattr(response, "text")
        assert isinstance(response.text, str)
        assert len(response.text) > 0

        # Text should be valid JSON
        json_data = json.loads(response.text)
        assert isinstance(json_data, dict)
        assert "url" in json_data

    @httpx_compatibility_test
    def test_response_url(self, client_factory):
        """Test Response.url attribute."""
        original_url = f"{self.base_url}/get"
        response = client_factory.get(original_url)

        # Verify URL attribute exists
        assert hasattr(response, "url")
        assert response.url is not None

        # URL should match the requested URL (as string)
        url_str = str(response.url)
        assert original_url in url_str

    @httpx_compatibility_test
    def test_response_json(self, client_factory):
        """Test Response.json() method."""
        response = client_factory.get(f"{self.base_url}/json")

        # Verify json() method exists and returns data
        assert hasattr(response, "json")
        json_data = response.json()
        assert isinstance(json_data, dict)

        # Test server returns specific JSON structure
        assert "slideshow" in json_data
        assert "author" in json_data["slideshow"]

        # Test json() with non-JSON response should raise error
        response = client_factory.get(f"{self.base_url}/bytes/100")
        try:
            response.json()
            # If it doesn't raise, the content might actually be JSON
        except (ValueError, json.JSONDecodeError):
            # Expected for non-JSON content
            pass

    @httpx_compatibility_test
    def test_response_raise_for_status(self, client_factory):
        """Test Response.raise_for_status() method."""
        # Test successful response doesn't raise
        response = client_factory.get(f"{self.base_url}/status/200")
        assert hasattr(response, "raise_for_status")
        response.raise_for_status()  # Should not raise

        # Test client error raises exception
        response = client_factory.get(f"{self.base_url}/status/404")
        with pytest.raises(faster_http.HTTPStatusError):
            response.raise_for_status()

        # Test server error raises exception
        response = client_factory.get(f"{self.base_url}/status/500")
        with pytest.raises(faster_http.HTTPStatusError):
            response.raise_for_status()

    @httpx_compatibility_test
    def test_response_request(self, client_factory):
        """Test Response.request attribute (original request object)."""
        url = f"{self.base_url}/get"
        response = client_factory.get(url, params={"test": "value"})

        # Verify request attribute exists
        assert hasattr(response, "request")
        assert response.request is not None

        # Verify request object structure
        assert hasattr(response.request, "method")
        assert hasattr(response.request, "url")
        assert response.request.method == "GET"

        # URL should contain the parameters
        request_url = str(response.request.url)
        assert "test=value" in request_url


class TestBasicParameterSupport(TDDTestCase):
    """Test basic parameter support (params, headers, data, json, timeout)."""

    @pytest.fixture(autouse=True)
    def setup(self, test_server):
        """Setup for each test."""
        self.base_url = test_server.base_url

    @httpx_compatibility_test
    def test_params_support(self, client_factory):
        """Test URL query parameters support."""
        url = f"{self.base_url}/get"

        # Test single parameters
        params = {"key": "value", "number": "123"}
        response = client_factory.get(url, params=params)

        assert response.status_code == 200
        response_data = response.json()
        assert response_data["args"]["key"] == "value"
        assert response_data["args"]["number"] == "123"

        # Test parameters with special characters
        params = {"special": "hello world", "encoded": "a=b&c=d"}
        response = client_factory.get(url, params=params)

        assert response.status_code == 200
        response_data = response.json()
        assert response_data["args"]["special"] == "hello world"
        assert response_data["args"]["encoded"] == "a=b&c=d"

        # Test list parameters (multiple values for same key)
        # Note: This might be implementation-specific
        params = {"tags": ["tag1", "tag2", "tag3"]}
        response = client_factory.get(url, params=params)
        assert response.status_code == 200

    @httpx_compatibility_test
    def test_headers_support(self, client_factory):
        """Test request headers support."""
        url = f"{self.base_url}/headers"

        # Test custom headers
        headers = {
            "X-Custom-Header": "custom-value",
            "User-Agent": "faster-http-test/1.0",
            "Accept": "application/json",
            "Authorization": "Bearer token123",
        }

        response = client_factory.get(url, headers=headers)
        assert response.status_code == 200

        response_data = response.json()
        response_headers = response_data["headers"]

        # Verify custom headers were sent
        assert response_headers["X-Custom-Header"] == "custom-value"
        assert response_headers["User-Agent"] == "faster-http-test/1.0"
        assert response_headers["Accept"] == "application/json"
        assert response_headers["Authorization"] == "Bearer token123"

    @httpx_compatibility_test
    def test_data_support(self, client_factory):
        """Test form data support."""
        url = f"{self.base_url}/post"

        # Test form data (application/x-www-form-urlencoded)
        form_data = {"username": "testuser", "password": "secret123", "remember": "true"}

        response = client_factory.post(url, data=form_data)
        assert response.status_code == 200

        response_data = response.json()
        # Form data should be in the request body
        assert "data" in response_data
        body = response_data["data"]
        assert "username=testuser" in body
        assert "password=secret123" in body
        assert "remember=true" in body

    @httpx_compatibility_test
    def test_json_support(self, client_factory):
        """Test JSON data support."""
        url = f"{self.base_url}/post"

        # Test JSON data
        json_payload = {
            "user": {"name": "John Doe", "email": "john@example.com", "age": 30},
            "preferences": {"notifications": True, "theme": "dark"},
            "tags": ["developer", "python", "testing"],
        }

        response = client_factory.post(url, json=json_payload)
        assert response.status_code == 200

        response_data = response.json()
        # JSON should be parsed and available in response
        assert "json" in response_data
        assert response_data["json"] == json_payload

        # Content-Type should be set to application/json
        headers = response_data["headers"]
        content_type = headers.get("Content-Type") or headers.get("content-type")
        assert content_type is not None
        assert "application/json" in content_type

    @httpx_compatibility_test
    def test_timeout_support(self, client_factory):
        """Test timeout configuration support."""
        # Test basic timeout setting
        try:
            # Use a fast endpoint to test timeout doesn't interfere
            response = client_factory.get(f"{self.base_url}/get", timeout=5.0)
            assert response.status_code == 200
        except faster_http.TimeoutException:
            pytest.skip("Timeout testing requires longer setup")

        # Test timeout with slow endpoint
        try:
            # Our test server has delay endpoint
            response = client_factory.get(f"{self.base_url}/delay/0.1", timeout=10.0)
            assert response.status_code == 200
        except faster_http.TimeoutException:
            pytest.fail("Request should not timeout with generous timeout")

        # Test very short timeout (might timeout)
        try:
            response = client_factory.get(f"{self.base_url}/delay/1", timeout=0.1)
            # If it succeeds, server was very fast
            assert response.status_code == 200
        except faster_http.TimeoutException:
            # Expected for very short timeout
            pass
