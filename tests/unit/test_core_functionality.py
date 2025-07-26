"""
Unit tests for core functionality verification.
Tests that don't require network connections.
Following CLAUDE.md requirements: test httpx first, then faster_http for comparison.
"""

import httpx
import faster_http


class TestCoreFunctionality:
    """Test core functionality that doesn't require network - httpx vs faster_http comparison."""
    
    def test_client_creation_with_parameters_comparison(self):
        """Test Client creation with various parameters - httpx vs faster_http."""
        base_url = "https://example.com"
        headers = {"User-Agent": "test", "Accept": "application/json"}
        params = {"api_key": "test123", "version": "v1"}
        timeout = 10.0
        
        # First test httpx Client creation with parameters
        httpx_client = httpx.Client(
            base_url=base_url,
            timeout=timeout,
            headers=headers,
            params=params,
            follow_redirects=True
        )
        
        # Test httpx client properties
        assert str(httpx_client.base_url) == base_url
        assert "User-Agent" in httpx_client.headers
        assert "Accept" in httpx_client.headers
        assert httpx_client.params["api_key"] == "test123"
        assert httpx_client.params["version"] == "v1"
        
        httpx_client.close()
        
        # Then test faster_http Client creation with same parameters (should match httpx)
        faster_client = faster_http.Client(
            base_url=base_url,
            timeout=timeout,
            headers=headers,
            params=params,
            follow_redirects=True
        )
        
        # Test faster_http client properties (should match httpx exactly)
        assert faster_client.base_url == base_url
        assert "User-Agent" in faster_client.headers
        assert "Accept" in faster_client.headers
        assert faster_client.params["api_key"] == "test123"
        assert faster_client.params["version"] == "v1"
        
        faster_client.close()
        
        # Both should have identical core properties
        assert str(httpx_client.base_url) == faster_client.base_url
        assert httpx_client.params["api_key"] == faster_client.params["api_key"]
        assert httpx_client.params["version"] == faster_client.params["version"]
    
    def test_async_client_creation_with_parameters_comparison(self):
        """Test AsyncClient creation with various parameters - httpx vs faster_http."""
        base_url = "https://api.example.com"
        headers = {"Authorization": "Bearer token", "Content-Type": "application/json"}
        params = {"version": "v1", "format": "json"}
        timeout = 15.0
        
        # First test httpx AsyncClient creation with parameters
        try:
            httpx_client = httpx.AsyncClient(
                base_url=base_url,
                timeout=timeout,
                headers=headers,
                params=params,
                http2=True
            )
            httpx_http2_works = True
        except Exception:
            # If httpx doesn't support http2, test without it
            httpx_client = httpx.AsyncClient(
                base_url=base_url,
                timeout=timeout,
                headers=headers,
                params=params
            )
            httpx_http2_works = False
        
        # Test httpx async client properties
        assert str(httpx_client.base_url) == base_url
        assert "Authorization" in httpx_client.headers
        assert "Content-Type" in httpx_client.headers
        assert httpx_client.params["version"] == "v1"
        assert httpx_client.params["format"] == "json"
        
        # Then test faster_http AsyncClient creation with same parameters (should match httpx)
        try:
            if httpx_http2_works:
                faster_client = faster_http.AsyncClient(
                    base_url=base_url,
                    timeout=timeout,
                    headers=headers,
                    params=params,
                    http2=True
                )
            else:
                faster_client = faster_http.AsyncClient(
                    base_url=base_url,
                    timeout=timeout,
                    headers=headers,
                    params=params
                )
            faster_http2_works = httpx_http2_works
        except Exception:
            faster_client = faster_http.AsyncClient(
                base_url=base_url,
                timeout=timeout,
                headers=headers,
                params=params
            )
            faster_http2_works = False
        
        # Test faster_http async client properties (should match httpx exactly)
        assert faster_client.base_url == base_url
        assert "Authorization" in faster_client.headers
        assert "Content-Type" in faster_client.headers
        assert faster_client.params["version"] == "v1"
        assert faster_client.params["format"] == "json"
        
        # Both should have identical core properties
        assert str(httpx_client.base_url) == faster_client.base_url
        assert httpx_client.params["version"] == faster_client.params["version"]
        assert httpx_client.params["format"] == faster_client.params["format"]
        
        # Both should handle HTTP/2 consistently
        assert httpx_http2_works == faster_http2_works
    
    def test_request_constructor_comparison(self):
        """Test Request constructor - httpx vs faster_http."""
        method = "PUT"
        url = "https://api.example.com/data"
        headers = {"Content-Type": "application/json", "X-Custom": "value"}
        content = b"test content data"
        
        # First test httpx Request constructor
        httpx_request = httpx.Request(
            method=method,
            url=url,
            headers=headers,
            content=content
        )
        
        # Test httpx request properties
        assert httpx_request.method == method
        assert str(httpx_request.url) == url
        assert "Content-Type" in httpx_request.headers
        assert "X-Custom" in httpx_request.headers
        assert httpx_request.content == content
        
        # Then test faster_http Request constructor (should match httpx exactly)
        faster_request = faster_http.Request(
            method=method,
            url=url,
            headers=headers,
            content=content
        )
        
        # Test faster_http request properties (should match httpx exactly)
        assert faster_request.method == method
        assert faster_request.url == url
        assert "Content-Type" in faster_request.headers
        assert "X-Custom" in faster_request.headers
        assert faster_request.content == content
        
        # Both should have identical core properties
        assert httpx_request.method == faster_request.method
        assert str(httpx_request.url) == faster_request.url
        assert httpx_request.content == faster_request.content
        assert httpx_request.headers["Content-Type"] == faster_request.headers["Content-Type"]
        assert httpx_request.headers["X-Custom"] == faster_request.headers["X-Custom"]
    
    def test_timeout_object_comparison(self):
        """Test Timeout object creation - httpx vs faster_http."""
        connect_timeout = 5.0
        read_timeout = 30.0
        write_timeout = 10.0
        pool_timeout = 15.0
        
        # Test 1: All parameters explicitly set (httpx requirement)
        httpx_timeout = httpx.Timeout(connect=connect_timeout, read=read_timeout, 
                                      write=write_timeout, pool=pool_timeout)
        assert httpx_timeout.connect == connect_timeout
        assert httpx_timeout.read == read_timeout
        assert httpx_timeout.write == write_timeout
        assert httpx_timeout.pool == pool_timeout
        
        # Then test faster_http Timeout object (should match httpx interface exactly)
        faster_timeout = faster_http.Timeout(connect=connect_timeout, read=read_timeout,
                                            write=write_timeout, pool=pool_timeout)
        assert faster_timeout.connect == connect_timeout
        assert faster_timeout.read == read_timeout
        assert faster_timeout.write == write_timeout
        assert faster_timeout.pool == pool_timeout
        
        # Both should have identical values
        assert httpx_timeout.connect == faster_timeout.connect
        assert httpx_timeout.read == faster_timeout.read
        assert httpx_timeout.write == faster_timeout.write
        assert httpx_timeout.pool == faster_timeout.pool
        
        # Test 2: Default timeout
        default_timeout = 20.0
        httpx_default = httpx.Timeout(default_timeout)
        faster_default = faster_http.Timeout(default_timeout)
        
        assert httpx_default.connect == faster_default.connect == default_timeout
        assert httpx_default.read == faster_default.read == default_timeout
        assert httpx_default.write == faster_default.write == default_timeout
        assert httpx_default.pool == faster_default.pool == default_timeout
        
        # Test additional timeout parameters if httpx supports them
        if hasattr(httpx_timeout, 'write'):
            assert hasattr(faster_timeout, 'write')
        if hasattr(httpx_timeout, 'pool'):
            assert hasattr(faster_timeout, 'pool')
    
    def test_headers_object_comparison(self):
        """Test Headers object creation and case-insensitivity - httpx vs faster_http."""
        headers_data = {
            "Content-Type": "application/json",
            "User-Agent": "test-client/1.0",
            "Accept": "*/*"
        }
        
        # First test httpx Headers object
        httpx_headers = httpx.Headers(headers_data)
        
        # Test httpx headers case-insensitive access
        assert httpx_headers["content-type"] == "application/json"
        assert httpx_headers["USER-AGENT"] == "test-client/1.0"
        assert httpx_headers["Accept"] == "*/*"
        
        # Test httpx headers iteration
        httpx_header_keys = list(httpx_headers.keys())
        httpx_header_values = list(httpx_headers.values())
        assert len(httpx_header_keys) == 3
        assert len(httpx_header_values) == 3
        
        # Then test faster_http Headers object (should match httpx behavior exactly)
        faster_headers = faster_http.Headers(headers_data)
        
        # Test faster_http headers case-insensitive access
        assert faster_headers["content-type"] == "application/json"
        assert faster_headers["USER-AGENT"] == "test-client/1.0"
        assert faster_headers["Accept"] == "*/*"
        
        # Test faster_http headers iteration
        faster_header_keys = list(faster_headers.keys())
        faster_header_values = list(faster_headers.values())
        assert len(faster_header_keys) == 3
        assert len(faster_header_values) == 3
        
        # Both should provide identical case-insensitive access
        assert httpx_headers["content-type"] == faster_headers["content-type"]
        assert httpx_headers["USER-AGENT"] == faster_headers["USER-AGENT"]
        assert httpx_headers["Accept"] == faster_headers["Accept"]
        
        # Both should have same iteration behavior
        assert len(httpx_header_keys) == len(faster_header_keys)
        assert len(httpx_header_values) == len(faster_header_values)
    
    def test_cookies_object_comparison(self):
        """Test Cookies object creation - httpx vs faster_http."""
        # First test httpx Cookies object
        httpx_cookies = httpx.Cookies()
        httpx_cookies['session_id'] = 'abc123'
        httpx_cookies['user_pref'] = 'dark_mode'
        
        assert httpx_cookies['session_id'] == 'abc123'
        assert httpx_cookies['user_pref'] == 'dark_mode'
        
        # Test httpx cookies iteration
        httpx_cookie_items = list(httpx_cookies.items())
        assert len(httpx_cookie_items) == 2
        
        # Then test faster_http Cookies object (should match httpx behavior exactly)
        faster_cookies = faster_http.Cookies()
        faster_cookies['session_id'] = 'abc123'
        faster_cookies['user_pref'] = 'dark_mode'
        
        assert faster_cookies['session_id'] == 'abc123'
        assert faster_cookies['user_pref'] == 'dark_mode'
        
        # Test faster_http cookies iteration
        faster_cookie_items = list(faster_cookies.items())
        assert len(faster_cookie_items) == 2
        
        # Both should store and retrieve cookies identically
        assert httpx_cookies['session_id'] == faster_cookies['session_id']
        assert httpx_cookies['user_pref'] == faster_cookies['user_pref']
        assert len(httpx_cookie_items) == len(faster_cookie_items)
    
    def test_query_params_object_comparison(self):
        """Test QueryParams object creation - httpx vs faster_http."""
        params_data = {'search': 'python', 'limit': '10', 'sort': 'name'}
        
        # First test httpx QueryParams object
        httpx_params = httpx.QueryParams(params_data)
        httpx_params_dict = dict(httpx_params)
        assert httpx_params_dict['search'] == 'python'
        assert httpx_params_dict['limit'] == '10'
        assert httpx_params_dict['sort'] == 'name'
        
        # Test httpx QueryParams length and iteration
        assert len(httpx_params) == 3
        httpx_param_items = list(httpx_params.items())
        assert len(httpx_param_items) == 3
        
        # Test httpx QueryParams string representation
        httpx_query_str = str(httpx_params)
        assert 'search=python' in httpx_query_str
        assert 'limit=10' in httpx_query_str
        assert 'sort=name' in httpx_query_str
        
        # Then test faster_http QueryParams object (should match httpx behavior exactly)
        faster_params = faster_http.QueryParams(params_data)
        faster_params_dict = dict(faster_params)
        assert faster_params_dict['search'] == 'python'
        assert faster_params_dict['limit'] == '10'
        assert faster_params_dict['sort'] == 'name'
        
        # Test faster_http QueryParams length and iteration
        assert len(faster_params) == 3
        faster_param_items = list(faster_params.items())
        assert len(faster_param_items) == 3
        
        # Test faster_http QueryParams string representation
        faster_query_str = str(faster_params)
        assert 'search=python' in faster_query_str
        assert 'limit=10' in faster_query_str
        assert 'sort=name' in faster_query_str
        
        # Both should convert to dict with identical values
        assert httpx_params_dict == faster_params_dict
        assert len(httpx_params) == len(faster_params)
        assert len(httpx_param_items) == len(faster_param_items)
        
        # Test string initialization (both should parse identically)
        query_string = "search=python&limit=10&sort=name"
        
        # First test httpx QueryParams from string
        httpx_from_string = httpx.QueryParams(query_string)
        httpx_string_dict = dict(httpx_from_string)
        assert 'search' in httpx_string_dict
        assert 'limit' in httpx_string_dict
        assert 'sort' in httpx_string_dict
        
        # Then test faster_http QueryParams from string
        faster_from_string = faster_http.QueryParams(query_string)
        faster_string_dict = dict(faster_from_string)
        assert 'search' in faster_string_dict
        assert 'limit' in faster_string_dict
        assert 'sort' in faster_string_dict
        
        # Both should parse query string identically
        assert httpx_string_dict == faster_string_dict
    
    def test_url_object_comparison(self):
        """Test URL object creation - httpx vs faster_http.""" 
        url_string = "https://api.example.com:8080/v1/data?search=test&limit=10#section1"
        
        # First test httpx URL object
        httpx_url = httpx.URL(url_string)
        assert httpx_url.scheme == "https"
        assert httpx_url.host == "api.example.com"
        assert httpx_url.port == 8080
        assert httpx_url.path == "/v1/data"
        assert b"search=test" in httpx_url.query
        assert b"limit=10" in httpx_url.query
        assert httpx_url.fragment == "section1"
        
        # Test httpx URL string representation
        httpx_url_str = str(httpx_url)
        assert "https://" in httpx_url_str
        assert "api.example.com" in httpx_url_str
        assert ":8080" in httpx_url_str
        assert "/v1/data" in httpx_url_str
        
        # Then test faster_http URL object (should match httpx behavior exactly)
        faster_url = faster_http.URL(url_string)
        assert faster_url.scheme == "https"
        assert faster_url.host == "api.example.com"
        assert faster_url.port == 8080
        assert faster_url.path == "/v1/data"
        # faster_http returns query as bytes or None
        faster_query = faster_url.query
        if faster_query is not None:
            faster_query_bytes = bytes(faster_query)
            assert b"search=test" in faster_query_bytes
            assert b"limit=10" in faster_query_bytes
        assert faster_url.fragment == "section1"
        
        # Test faster_http URL string representation
        faster_url_str = str(faster_url)
        assert "https://" in faster_url_str
        assert "api.example.com" in faster_url_str
        assert ":8080" in faster_url_str
        assert "/v1/data" in faster_url_str
        
        # Both should parse the URL components identically
        assert httpx_url.scheme == faster_url.scheme
        assert httpx_url.host == faster_url.host
        assert httpx_url.port == faster_url.port
        assert httpx_url.path == faster_url.path
        assert httpx_url.fragment == faster_url.fragment
        
        # Query might have different parameter order, so check both contain same parameters
        httpx_query_params = set(httpx_url.query.decode().split('&'))
        faster_query_params = set(bytes(faster_url.query).decode().split('&')) if faster_url.query else set()
        assert httpx_query_params == faster_query_params
        
        # String representations should be equivalent (allowing for parameter order differences)
        assert httpx_url.scheme in faster_url_str
        assert httpx_url.host in faster_url_str
        assert str(httpx_url.port) in faster_url_str
    
    def test_interface_consistency_comparison(self):
        """Test that faster_http doesn't implement interfaces that httpx doesn't have."""
        # Get all public attributes from httpx
        httpx_client_attrs = set(attr for attr in dir(httpx.Client) if not attr.startswith('_'))
        faster_client_attrs = set(attr for attr in dir(faster_http.Client) if not attr.startswith('_'))
        
        # faster_http should not have methods/attributes that httpx doesn't have
        extra_attrs = faster_client_attrs - httpx_client_attrs
        assert len(extra_attrs) == 0, f"faster_http.Client has extra attributes that httpx.Client doesn't have: {extra_attrs}"
        
        # Test AsyncClient consistency
        httpx_async_attrs = set(attr for attr in dir(httpx.AsyncClient) if not attr.startswith('_'))
        faster_async_attrs = set(attr for attr in dir(faster_http.AsyncClient) if not attr.startswith('_'))
        
        extra_async_attrs = faster_async_attrs - httpx_async_attrs
        assert len(extra_async_attrs) == 0, f"faster_http.AsyncClient has extra attributes that httpx.AsyncClient doesn't have: {extra_async_attrs}"
        
        # Test Request consistency - compare instance attributes, not class attributes
        # Create request instances to get actual available attributes
        httpx_client = httpx.Client()
        httpx_request = httpx_client.build_request("GET", "https://example.com")
        httpx_request_attrs = set(attr for attr in dir(httpx_request) if not attr.startswith('_'))
        httpx_client.close()
        
        faster_request = faster_http.Request("GET", "https://example.com")
        faster_request_attrs = set(attr for attr in dir(faster_request) if not attr.startswith('_'))
        
        extra_request_attrs = faster_request_attrs - httpx_request_attrs
        assert len(extra_request_attrs) == 0, f"faster_http.Request has extra attributes that httpx.Request doesn't have: {extra_request_attrs}"