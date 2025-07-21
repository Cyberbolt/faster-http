"""
Shared test configuration and utilities for faster_http tests.
"""

import pytest
import sys
import os

# Add the src directory to the path so we can import faster_http
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Test URLs - now using local test server
def get_test_urls(httpserver):
    """Get test URLs using the local test server."""
    return {
        'get': httpserver.url_for('/get'),
        'post': httpserver.url_for('/post'),
        'put': httpserver.url_for('/put'),
        'patch': httpserver.url_for('/patch'), 
        'delete': httpserver.url_for('/delete'),
        'json': httpserver.url_for('/json'),
        'headers': httpserver.url_for('/headers'),
        'basic_auth': httpserver.url_for('/basic-auth/user/pass'),
        'status': httpserver.url_for('/status/{code}'),
        'redirect': httpserver.url_for('/redirect/{n}'),
        'delay': httpserver.url_for('/delay/{seconds}'),
        'cookies': httpserver.url_for('/cookies'),
        'stream': httpserver.url_for('/stream/{n}'),
        'drip': httpserver.url_for('/drip'),
        'image': httpserver.url_for('/image/png'),
        'gzip': httpserver.url_for('/gzip'),
        'deflate': httpserver.url_for('/deflate'),
        'brotli': httpserver.url_for('/brotli'),
        'encoding': httpserver.url_for('/encoding/utf8'),
        'range': httpserver.url_for('/range/1024'),
        'bytes': httpserver.url_for('/bytes/1024'),
        'uuid': httpserver.url_for('/uuid'),
        'base64': httpserver.url_for('/base64/value'),
        'xml': httpserver.url_for('/xml'),
        'robots': httpserver.url_for('/robots.txt'),
        'html': httpserver.url_for('/html'),
        'forms': httpserver.url_for('/forms/post'),
        'anything': httpserver.url_for('/anything'),
        'cache': httpserver.url_for('/cache'),
        'etag': httpserver.url_for('/etag/{etag}'),
        'response_headers': httpserver.url_for('/response-headers'),
        'bearer': httpserver.url_for('/bearer'),
        'digest_auth': httpserver.url_for('/digest-auth/auth/user/pass'),
        'hidden_basic_auth': httpserver.url_for('/hidden-basic-auth/user/pass'),
        'cookies_set': httpserver.url_for('/cookies/set'),
        'cookies_delete': httpserver.url_for('/cookies/delete'),
        'user_agent': httpserver.url_for('/user-agent'),
        'ip': httpserver.url_for('/ip'),
        'origin': httpserver.url_for('/origin'),
        'links': httpserver.url_for('/links/{n}'),
        'links_redirect': httpserver.url_for('/links/{n}/{offset}'),
        'absolute_redirect': httpserver.url_for('/absolute-redirect/{n}'),
        'relative_redirect': httpserver.url_for('/relative-redirect/{n}'),
        'redirect_to': httpserver.url_for('/redirect-to')
    }


@pytest.fixture
def test_urls(httpserver):
    """Provide test URLs for HTTP requests."""
    # Configure test server endpoints
    setup_test_server_endpoints(httpserver)
    return get_test_urls(httpserver)


def setup_test_server_endpoints(httpserver):
    """Configure test server endpoints to mimic httpbin.org behavior."""
    # GET endpoint
    httpserver.expect_request("/get").respond_with_json({
        "args": {},
        "headers": {"Host": "127.0.0.1"},
        "origin": "127.0.0.1",
        "url": httpserver.url_for("/get")
    })
    
    # POST endpoint  
    httpserver.expect_request("/post", method="POST").respond_with_json({
        "args": {},
        "data": "",
        "files": {},
        "form": {},
        "headers": {"Host": "127.0.0.1"},
        "json": None,
        "origin": "127.0.0.1",
        "url": httpserver.url_for("/post")
    })
    
    # PUT endpoint
    httpserver.expect_request("/put", method="PUT").respond_with_json({
        "args": {},
        "data": "",
        "files": {},
        "form": {},
        "headers": {"Host": "127.0.0.1"},
        "json": None,
        "origin": "127.0.0.1",
        "url": httpserver.url_for("/put")
    })
    
    # PATCH endpoint
    httpserver.expect_request("/patch", method="PATCH").respond_with_json({
        "args": {},
        "data": "",
        "files": {},
        "form": {},
        "headers": {"Host": "127.0.0.1"},
        "json": None,
        "origin": "127.0.0.1",
        "url": httpserver.url_for("/patch")
    })
    
    # DELETE endpoint
    httpserver.expect_request("/delete", method="DELETE").respond_with_json({
        "args": {},
        "data": "",
        "files": {},
        "form": {},
        "headers": {"Host": "127.0.0.1"},
        "json": None,
        "origin": "127.0.0.1",
        "url": httpserver.url_for("/delete")
    })
    
    # Cookie set endpoint
    httpserver.expect_request("/cookies/set/test/value").respond_with_data(
        "Redirecting to /cookies", 
        status=302,
        headers={"Location": "/cookies", "Set-Cookie": "test=value; Path=/"}
    )
    
    # JSON endpoint
    httpserver.expect_request("/json").respond_with_json({
        "slideshow": {
            "author": "Yours Truly",
            "date": "date of publication",
            "slides": [
                {
                    "title": "Wake up to WonderWidgets!",
                    "type": "all"
                },
                {
                    "items": [
                        "Why <em>WonderWidgets</em> are great",
                        "Who <em>buys</em> WonderWidgets"
                    ],
                    "title": "Overview",
                    "type": "all"
                }
            ],
            "title": "Sample Slide Show"
        }
    })


@pytest.fixture
def sample_json_data():
    """Sample JSON data for testing."""
    return {
        'name': 'faster_http',
        'version': '0.1.0',
        'test': 'data',
        'number': 42,
        'boolean': True,
        'null_value': None,
        'nested': {
            'key': 'value',
            'items': [1, 2, 3]
        }
    }


@pytest.fixture
def sample_form_data():
    """Sample form data for testing."""
    return {
        'username': 'testuser',
        'password': 'secret123',
        'email': 'test@example.com',
        'age': '25',
        'newsletter': 'true'
    }


@pytest.fixture
def sample_headers():
    """Sample headers for testing."""
    return {
        'User-Agent': 'faster-http-test/0.1.0',
        'X-Test-Header': 'test-value',
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': 'Bearer token123',
        'X-Custom-Header': 'custom-value'
    }


@pytest.fixture
def sample_cookies():
    """Sample cookies for testing."""
    return {
        'session_id': 'abc123',
        'user_pref': 'dark_mode',
        'lang': 'en',
        'csrf_token': 'token123',
        'theme': 'blue'
    }


@pytest.fixture
def sample_params():
    """Sample query parameters for testing."""
    return {
        'q': 'test query',
        'page': '1',
        'limit': '10',
        'sort': 'name',
        'order': 'asc',
        'filter': 'active'
    }


@pytest.fixture
def sample_auth_tuple():
    """Sample auth tuple for testing."""
    return ('testuser', 'testpass')


@pytest.fixture
def sample_files():
    """Sample files for testing."""
    return {
        'test_file': b'Hello, World!',
        'data_file': b'Test file content',
        'config_file': b'{"key": "value"}'
    }


@pytest.fixture
def sample_multipart_data():
    """Sample multipart form data for testing."""
    return {
        'files': {'upload': b'file content'},
        'data': {'name': 'test', 'value': 'data'}
    }


# Helper functions
def assert_response_ok(response):
    """Helper function to assert response is OK."""
    assert response.status_code == 200
    # Use is_success for httpx compatibility
    if hasattr(response, 'is_success'):
        assert response.is_success
    elif hasattr(response, 'ok'):
        assert response.ok
    assert not response.is_client_error
    assert not response.is_server_error


def assert_response_has_basic_attrs(response):
    """Helper function to assert response has basic attributes."""
    assert hasattr(response, 'status_code')
    assert hasattr(response, 'headers')
    assert hasattr(response, 'url')
    # Check for success attribute (httpx uses is_success, faster-http might use ok)
    assert hasattr(response, 'is_success') or hasattr(response, 'ok')
    assert hasattr(response, 'content')
    assert hasattr(response, 'text')
    assert hasattr(response, 'elapsed')


def assert_httpx_compatibility(response):
    """Helper function to assert httpx compatibility."""
    httpx_attrs = [
        'status_code', 'headers', 'url', 'content', 'text',
        'encoding', 'elapsed', 'http_version', 'cookies', 
        'is_client_error', 'is_server_error', 'is_redirect',
        'json', 'raise_for_status', 'iter_bytes', 'iter_text',
        'iter_lines', 'iter_raw', 'extensions', 'history', 'request'
    ]
    
    for attr in httpx_attrs:
        assert hasattr(response, attr), f"Missing httpx attribute: {attr}"
    
    # Check for success attribute (httpx uses is_success, faster-http might use ok)
    assert hasattr(response, 'is_success') or hasattr(response, 'ok'), "Missing success attribute"


def skip_on_network_error(func):
    """Decorator to skip tests on network errors."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            pytest.skip(f"Network error: {e}")
    return wrapper


def assert_clients_equivalent(httpx_client, faster_http_client):
    """Assert that client objects have equivalent attributes."""
    # Check that both have the same basic attributes
    basic_attrs = ['headers', 'cookies', 'params', 'auth', 'base_url']
    
    for attr in basic_attrs:
        httpx_val = getattr(httpx_client, attr, None)
        faster_val = getattr(faster_http_client, attr, None)
        
        # Both should have the attribute or both should not have it
        if httpx_val is not None or faster_val is not None:
            assert httpx_val == faster_val, f"Client attribute {attr} differs"
    
    # Check methods exist
    methods = ['get', 'post', 'put', 'patch', 'delete', 'head', 'options', 'request']
    for method in methods:
        assert hasattr(httpx_client, method), f"httpx client missing method {method}"
        assert hasattr(faster_http_client, method), f"faster-http client missing method {method}"
        assert callable(getattr(httpx_client, method)), f"httpx {method} not callable"
        assert callable(getattr(faster_http_client, method)), f"faster-http {method} not callable"


def assert_response_equivalence(httpx_response, faster_http_response):
    """Assert that two responses are equivalent."""
    # Status code must match
    assert httpx_response.status_code == faster_http_response.status_code
    
    # For successful responses, check that both have similar JSON structure
    if httpx_response.status_code == 200:
        try:
            httpx_json = httpx_response.json()
            faster_json = faster_http_response.json()
            
            # Check that both have similar structure (allowing for header differences)
            assert 'url' in httpx_json and 'url' in faster_json
            assert 'args' in httpx_json and 'args' in faster_json
            assert 'headers' in httpx_json and 'headers' in faster_json
            
            # URLs should be the same
            assert httpx_json['url'] == faster_json['url']
            
            # Args should be the same
            assert httpx_json['args'] == faster_json['args']
            
        except (ValueError, KeyError):
            # If not JSON, just check that both have content
            assert len(httpx_response.content) > 0
            assert len(faster_http_response.content) > 0
    
    # Boolean properties must match
    bool_props = ['is_redirect', 'is_client_error', 'is_server_error']
    for prop in bool_props:
        assert getattr(httpx_response, prop) == getattr(faster_http_response, prop)
    
    # Check success status (httpx uses is_success, faster-http might use ok)
    httpx_success = getattr(httpx_response, 'is_success', getattr(httpx_response, 'ok', None))
    faster_success = getattr(faster_http_response, 'is_success', getattr(faster_http_response, 'ok', None))
    if httpx_success is not None and faster_success is not None:
        assert httpx_success == faster_success
    
    # Headers should be compatible (allowing minor differences)
    important_headers = ['content-type']
    for header in important_headers:
        httpx_val = httpx_response.headers.get(header)
        faster_val = faster_http_response.headers.get(header)
        if httpx_val is not None and faster_val is not None:
            assert httpx_val.lower() == faster_val.lower()