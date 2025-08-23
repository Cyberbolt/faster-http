"""
Mock HTTP response system for faster-http testing.

This module provides mock responses that completely eliminate the need for
network connections, ensuring tests can run in fully isolated environments.
"""

import json
import time
from typing import Any


class MockResponse:
    """Mock HTTP response that mimics faster_http Response interface."""

    def __init__(
        self,
        status_code: int = 200,
        headers: dict[str, str] | None = None,
        content: str | bytes | dict = "",
        url: str = "http://mock-server/test",
        elapsed: float = 0.001,
        encoding: str = "utf-8",
    ):
        self.status_code = status_code
        self.headers = headers or {"content-type": "application/json"}
        self.url = url
        self.elapsed = elapsed
        self.encoding = encoding

        # Handle different content types
        if isinstance(content, dict):
            self._content = json.dumps(content).encode(encoding)
            self._text = json.dumps(content)
            self._json_data = content
        elif isinstance(content, str):
            self._content = content.encode(encoding)
            self._text = content
            try:
                self._json_data = json.loads(content)
            except json.JSONDecodeError:
                self._json_data = None
        elif isinstance(content, bytes):
            self._content = content
            try:
                self._text = content.decode(encoding)
                self._json_data = json.loads(self._text)
            except (UnicodeDecodeError, json.JSONDecodeError):
                self._text = content.decode(encoding, errors="replace")
                self._json_data = None
        else:
            self._content = b""
            self._text = ""
            self._json_data = None

    @property
    def text(self) -> str:
        """Get response text."""
        return self._text

    @property
    def content(self) -> bytes:
        """Get response content as bytes."""
        return self._content

    def json(self) -> Any:
        """Get response as JSON."""
        if self._json_data is not None:
            return self._json_data
        raise ValueError("Response content is not valid JSON")

    @property
    def is_success(self) -> bool:
        """Check if response indicates success."""
        return 200 <= self.status_code < 400

    @property
    def is_error(self) -> bool:
        """Check if response indicates error."""
        return self.status_code >= 400


class MockClient:
    """Mock HTTP client that returns predefined responses."""

    def __init__(self, default_response: MockResponse | None = None):
        self.default_response = default_response or MockResponse()
        self.responses = {}  # URL -> MockResponse mapping
        self.request_history = []

    def set_response(self, url: str, response: MockResponse):
        """Set a specific response for a URL."""
        self.responses[url] = response

    def set_response_for_pattern(self, pattern: str, response: MockResponse):
        """Set response for URLs matching a pattern."""
        self.responses[pattern] = response

    def _find_response(self, url: str) -> MockResponse:
        """Find appropriate response for URL."""
        # Exact match
        if url in self.responses:
            return self.responses[url]

        # Pattern match
        for pattern, response in self.responses.items():
            if pattern in url or url.endswith(pattern):
                return response

        return self.default_response

    def get(self, url: str, **kwargs) -> MockResponse:
        """Mock GET request."""
        response = self._find_response(url)
        self.request_history.append({"method": "GET", "url": url, "kwargs": kwargs, "timestamp": time.time()})
        return response

    def post(self, url: str, **kwargs) -> MockResponse:
        """Mock POST request."""
        response = self._find_response(url)
        self.request_history.append({"method": "POST", "url": url, "kwargs": kwargs, "timestamp": time.time()})
        return response

    def put(self, url: str, **kwargs) -> MockResponse:
        """Mock PUT request."""
        response = self._find_response(url)
        self.request_history.append({"method": "PUT", "url": url, "kwargs": kwargs, "timestamp": time.time()})
        return response

    def patch(self, url: str, **kwargs) -> MockResponse:
        """Mock PATCH request."""
        response = self._find_response(url)
        self.request_history.append({"method": "PATCH", "url": url, "kwargs": kwargs, "timestamp": time.time()})
        return response

    def delete(self, url: str, **kwargs) -> MockResponse:
        """Mock DELETE request."""
        response = self._find_response(url)
        self.request_history.append({"method": "DELETE", "url": url, "kwargs": kwargs, "timestamp": time.time()})
        return response

    def head(self, url: str, **kwargs) -> MockResponse:
        """Mock HEAD request."""
        response = self._find_response(url)
        self.request_history.append({"method": "HEAD", "url": url, "kwargs": kwargs, "timestamp": time.time()})
        return response

    def options(self, url: str, **kwargs) -> MockResponse:
        """Mock OPTIONS request."""
        response = self._find_response(url)
        self.request_history.append({"method": "OPTIONS", "url": url, "kwargs": kwargs, "timestamp": time.time()})
        return response


def create_mock_responses() -> dict[str, MockResponse]:
    """Create common mock responses for testing."""
    return {
        # GET endpoint
        "/get": MockResponse(
            status_code=200,
            content={
                "url": "http://mock-server/get",
                "method": "GET",
                "headers": {"host": "mock-server", "user-agent": "faster-http"},
                "args": {},
                "origin": "127.0.0.1",
            },
        ),
        # JSON endpoint
        "/json": MockResponse(
            status_code=200,
            content={
                "slideshow": {
                    "author": "Yours Truly",
                    "date": "date of publication",
                    "slides": [{"title": "Wake up to WonderWidgets!", "type": "all"}],
                    "title": "Sample Slide Show",
                }
            },
        ),
        # Status endpoint
        "/status/200": MockResponse(status_code=200, content={"status": 200}),
        "/status/404": MockResponse(status_code=404, content={"status": 404}),
        # Headers endpoint
        "/headers": MockResponse(
            status_code=200, content={"headers": {"host": "mock-server", "user-agent": "faster-http", "accept": "*/*"}}
        ),
        # Basic HTML content for legacy compatibility
        "/": MockResponse(
            status_code=200,
            content="<html><head><title>Mock Server</title></head><body><h1>Mock Server Response</h1></body></html>",
            headers={"content-type": "text/html"},
        ),
        # Mock server endpoints
        "/test": MockResponse(
            status_code=200, content="Test response from mock server", headers={"content-type": "text/plain"}
        ),
        "mock-server": MockResponse(
            status_code=200, content={"message": "Mock server response", "status": "success", "mock": True}
        ),
    }


def create_default_mock_client() -> MockClient:
    """Create a mock client with default responses."""
    client = MockClient()
    responses = create_mock_responses()

    for pattern, response in responses.items():
        client.set_response_for_pattern(pattern, response)

    return client
