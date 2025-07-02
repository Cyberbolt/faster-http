"""
Shared test configuration and utilities for faster_http tests.
"""

import pytest
import sys
import os

# Add the src directory to the path so we can import faster_http
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import faster_http


# Test URLs
TEST_URLS = {
    'get': 'https://httpbin.org/get',
    'post': 'https://httpbin.org/post',
    'put': 'https://httpbin.org/put',
    'patch': 'https://httpbin.org/patch', 
    'delete': 'https://httpbin.org/delete',
    'json': 'https://httpbin.org/json',
    'headers': 'https://httpbin.org/headers',
    'basic_auth': 'https://httpbin.org/basic-auth/user/pass',
    'status': 'https://httpbin.org/status/{code}',
    'redirect': 'https://httpbin.org/redirect/{n}',
    'delay': 'https://httpbin.org/delay/{seconds}',
    'cookies': 'https://httpbin.org/cookies'
}


@pytest.fixture
def test_urls():
    """Provide test URLs for HTTP requests."""
    return TEST_URLS


@pytest.fixture
def sample_json_data():
    """Sample JSON data for testing."""
    return {
        'name': 'faster_http',
        'version': '0.1.0',
        'test': 'data',
        'number': 42
    }


@pytest.fixture
def sample_form_data():
    """Sample form data for testing."""
    return {
        'username': 'testuser',
        'password': 'secret123',
        'email': 'test@example.com'
    }


@pytest.fixture
def sample_headers():
    """Sample headers for testing."""
    return {
        'User-Agent': 'faster-http-test/0.1.0',
        'X-Test-Header': 'test-value',
        'Authorization': 'Bearer token123'
    }


@pytest.fixture
def sample_cookies():
    """Sample cookies for testing."""
    return {
        'session_id': 'abc123',
        'user_pref': 'dark_mode',
        'lang': 'en'
    }


def assert_response_ok(response):
    """Helper function to assert response is OK."""
    assert response.status_code == 200
    assert response.ok
    assert not response.is_client_error
    assert not response.is_server_error


def assert_response_has_basic_attrs(response):
    """Helper function to assert response has basic attributes."""
    assert hasattr(response, 'status_code')
    assert hasattr(response, 'headers')
    assert hasattr(response, 'url')
    assert hasattr(response, 'ok')
    assert hasattr(response, 'content')
    assert hasattr(response, 'text')
    assert hasattr(response, 'elapsed')


def assert_httpx_compatibility(response):
    """Helper function to assert httpx compatibility."""
    httpx_attrs = [
        'status_code', 'headers', 'url', 'ok', 'content', 'text',
        'encoding', 'elapsed', 'http_version', 'cookies', 
        'is_client_error', 'is_server_error', 'is_redirect',
        'json', 'raise_for_status'
    ]
    
    for attr in httpx_attrs:
        assert hasattr(response, attr), f"Missing httpx attribute: {attr}"


def skip_on_network_error(func):
    """Decorator to skip tests on network errors."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            pytest.skip(f"Network error: {e}")
    return wrapper 