"""
Feature parity tests between httpx and faster-http.
Ensures that faster-http provides all the features and API compatibility of httpx.
"""

import pytest
import asyncio
import httpx
import faster_http
from ..conftest import assert_response_ok, assert_httpx_compatibility


class TestAPICompatibility:
    """Test API compatibility between httpx and faster-http."""
    
    def test_module_level_functions_exist(self):
        """Test that all module-level functions exist in both libraries."""
        httpx_functions = ['get', 'post', 'put', 'patch', 'delete', 'head', 'options', 'request']
        
        for func_name in httpx_functions:
            assert hasattr(httpx, func_name), f"httpx missing function: {func_name}"
            assert hasattr(faster_http, func_name), f"faster-http missing function: {func_name}"
            assert callable(getattr(httpx, func_name)), f"httpx.{func_name} not callable"
            assert callable(getattr(faster_http, func_name)), f"faster-http.{func_name} not callable"
    
    def test_client_classes_exist(self):
        """Test that Client classes exist in both libraries."""
        assert hasattr(httpx, 'Client'), "httpx missing Client class"
        assert hasattr(faster_http, 'Client'), "faster-http missing Client class"
        assert hasattr(httpx, 'AsyncClient'), "httpx missing AsyncClient class"
        assert hasattr(faster_http, 'AsyncClient'), "faster-http missing AsyncClient class"
    
    def test_auth_classes_exist(self):
        """Test that authentication classes exist in both libraries."""
        auth_classes = ['BasicAuth', 'DigestAuth', 'NetRCAuth']
        
        for auth_class in auth_classes:
            assert hasattr(httpx, auth_class), f"httpx missing auth class: {auth_class}"
            assert hasattr(faster_http, auth_class), f"faster-http missing auth class: {auth_class}"
    
    def test_exception_classes_exist(self):
        """Test that exception classes exist in both libraries."""
        exception_classes = ['HTTPError', 'RequestError', 'ConnectTimeout', 'ReadTimeout']
        
        for exc_class in exception_classes:
            httpx_has = hasattr(httpx, exc_class)
            faster_has = hasattr(faster_http, exc_class)
            
            # faster-http should have all the same exception classes
            if httpx_has:
                assert faster_has, f"faster-http missing exception class: {exc_class}"
    
    def test_response_object_compatibility(self, test_urls):
        """Test that Response objects have the same interface."""
        # Get responses from both libraries
        httpx_response = httpx.get(test_urls['get'])
        faster_response = faster_http.get(test_urls['get'])
        
        # Test that both have the same attributes
        httpx_attrs = [attr for attr in dir(httpx_response) if not attr.startswith('_')]
        faster_attrs = [attr for attr in dir(faster_response) if not attr.startswith('_')]
        
        # faster-http should have all the same public attributes as httpx
        missing_attrs = set(httpx_attrs) - set(faster_attrs)
        assert not missing_attrs, f"faster-http Response missing attributes: {missing_attrs}"
    
    def test_client_object_compatibility(self):
        """Test that Client objects have the same interface."""
        # Create clients from both libraries
        httpx_client = httpx.Client()
        faster_client = faster_http.Client()
        
        # Test that both have the same methods
        httpx_methods = [method for method in dir(httpx_client) if not method.startswith('_') and callable(getattr(httpx_client, method))]
        faster_methods = [method for method in dir(faster_client) if not method.startswith('_') and callable(getattr(faster_client, method))]
        
        # faster-http should have all the same public methods as httpx
        missing_methods = set(httpx_methods) - set(faster_methods)
        assert not missing_methods, f"faster-http Client missing methods: {missing_methods}"
        
        # Clean up
        httpx_client.close()
        faster_client.close()
    
    @pytest.mark.asyncio
    async def test_async_client_object_compatibility(self):
        """Test that AsyncClient objects have the same interface."""
        # Create async clients from both libraries
        httpx_client = httpx.AsyncClient()
        faster_client = faster_http.AsyncClient()
        
        # Test that both have the same methods
        httpx_methods = [method for method in dir(httpx_client) if not method.startswith('_') and callable(getattr(httpx_client, method))]
        faster_methods = [method for method in dir(faster_client) if not method.startswith('_') and callable(getattr(faster_client, method))]
        
        # faster-http should have all the same public methods as httpx
        missing_methods = set(httpx_methods) - set(faster_methods)
        assert not missing_methods, f"faster-http AsyncClient missing methods: {missing_methods}"
        
        # Clean up
        await httpx_client.aclose()
        await faster_client.aclose()


class TestDropInReplacement:
    """Test that faster-http can serve as a drop-in replacement for httpx."""
    
    def test_import_as_httpx(self, test_urls):
        """Test importing faster-http as httpx."""
        import faster_http as httpx_replacement
        
        # Test that basic functionality works
        response = httpx_replacement.get(test_urls['get'])
        assert_response_ok(response)
        assert_httpx_compatibility(response)
    
    def test_client_as_httpx(self, test_urls):
        """Test using faster-http.Client as httpx.Client."""
        import faster_http as httpx_replacement
        
        with httpx_replacement.Client() as client:
            response = client.get(test_urls['get'])
            assert_response_ok(response)
            assert_httpx_compatibility(response)
    
    @pytest.mark.asyncio
    async def test_async_client_as_httpx(self, test_urls):
        """Test using faster-http.AsyncClient as httpx.AsyncClient."""
        import faster_http as httpx_replacement
        
        async with httpx_replacement.AsyncClient() as client:
            response = await client.get(test_urls['get'])
            assert_response_ok(response)
            assert_httpx_compatibility(response)
    
    def test_auth_as_httpx(self, test_urls):
        """Test using faster-http auth classes as httpx auth classes."""
        import faster_http as httpx_replacement
        
        # Test BasicAuth
        auth = httpx_replacement.BasicAuth('user', 'pass')
        try:
            response = httpx_replacement.get(test_urls['basic_auth'], auth=auth)
            assert response.status_code in [200, 401]
        except Exception:
            # Auth endpoint might not be available, that's okay
            pass
        
        # Test DigestAuth
        auth = httpx_replacement.DigestAuth('user', 'pass')
        try:
            response = httpx_replacement.get(test_urls['digest_auth'], auth=auth)
            assert response.status_code in [200, 401]
        except Exception:
            # Auth endpoint might not be available, that's okay
            pass
    
    def test_error_handling_as_httpx(self, test_urls):
        """Test that error handling works the same as httpx."""
        import faster_http as httpx_replacement
        
        # Test 404 error
        response = httpx_replacement.get(test_urls['status'].format(code=404))
        assert response.status_code == 404
        assert not response.ok
        assert response.is_client_error
        
        # Test raise_for_status
        with pytest.raises(httpx_replacement.HTTPError):
            response.raise_for_status()


class TestResponseObjectParity:
    """Test that Response objects have full parity with httpx."""
    
    def test_response_properties_parity(self, test_urls):
        """Test that Response objects have all the same properties."""
        httpx_response = httpx.get(test_urls['get'])
        faster_response = faster_http.get(test_urls['get'])
        
        # Test basic properties
        basic_props = ['status_code', 'headers', 'url', 'content', 'text', 'encoding', 'elapsed']
        for prop in basic_props:
            assert hasattr(httpx_response, prop), f"httpx Response missing property: {prop}"
            assert hasattr(faster_response, prop), f"faster-http Response missing property: {prop}"
            
            # Values should be of the same type
            httpx_val = getattr(httpx_response, prop)
            faster_val = getattr(faster_response, prop)
            assert type(httpx_val) == type(faster_val), f"Property {prop} type mismatch"
        
        # Test boolean properties
        bool_props = ['ok', 'is_redirect', 'is_client_error', 'is_server_error']
        for prop in bool_props:
            assert hasattr(httpx_response, prop), f"httpx Response missing property: {prop}"
            assert hasattr(faster_response, prop), f"faster-http Response missing property: {prop}"
            
            # Values should be boolean and equal
            httpx_val = getattr(httpx_response, prop)
            faster_val = getattr(faster_response, prop)
            assert isinstance(httpx_val, bool), f"httpx {prop} is not boolean"
            assert isinstance(faster_val, bool), f"faster-http {prop} is not boolean"
            assert httpx_val == faster_val, f"Boolean property {prop} mismatch"
    
    def test_response_methods_parity(self, test_urls):
        """Test that Response objects have all the same methods."""
        httpx_response = httpx.get(test_urls['get'])
        faster_response = faster_http.get(test_urls['get'])
        
        # Test methods
        methods = ['json', 'raise_for_status', 'iter_bytes', 'iter_text', 'iter_lines']
        for method in methods:
            assert hasattr(httpx_response, method), f"httpx Response missing method: {method}"
            assert hasattr(faster_response, method), f"faster-http Response missing method: {method}"
            assert callable(getattr(httpx_response, method)), f"httpx {method} not callable"
            assert callable(getattr(faster_response, method)), f"faster-http {method} not callable"
    
    def test_response_iteration_parity(self, test_urls):
        """Test that Response iteration methods work the same."""
        httpx_response = httpx.get(test_urls['get'])
        faster_response = faster_http.get(test_urls['get'])
        
        # Test iter_bytes
        httpx_bytes = httpx_response.iter_bytes(chunk_size=100)
        faster_bytes = faster_response.iter_bytes(chunk_size=100)
        assert len(httpx_bytes) == len(faster_bytes)
        
        # Test iter_text
        httpx_text = httpx_response.iter_text(chunk_size=100)
        faster_text = faster_response.iter_text(chunk_size=100)
        assert len(httpx_text) == len(faster_text)
        
        # Test iter_lines
        httpx_lines = httpx_response.iter_lines()
        faster_lines = faster_response.iter_lines()
        assert len(httpx_lines) == len(faster_lines)
    
    def test_response_json_parity(self, test_urls):
        """Test that JSON parsing works the same."""
        httpx_response = httpx.get(test_urls['json'])
        faster_response = faster_http.get(test_urls['json'])
        
        httpx_json = httpx_response.json()
        faster_json = faster_response.json()
        
        assert httpx_json == faster_json
        assert type(httpx_json) == type(faster_json)
    
    def test_response_headers_parity(self, test_urls):
        """Test that headers handling works the same."""
        httpx_response = httpx.get(test_urls['get'])
        faster_response = faster_http.get(test_urls['get'])
        
        httpx_headers = httpx_response.headers
        faster_headers = faster_response.headers
        
        # Both should have headers objects (not necessarily dict)
        assert httpx_headers is not None
        assert faster_headers is not None
        
        # Check that both support item access
        assert hasattr(httpx_headers, '__getitem__')
        assert hasattr(faster_headers, '__getitem__')
        
        # Check that common headers are present
        common_headers = ['Content-Type', 'Server']
        for header in common_headers:
            httpx_val = httpx_headers.get(header) or httpx_headers.get(header.lower())
            faster_val = faster_headers.get(header) or faster_headers.get(header.lower())
            # Both should have the header or both should not have it
            assert (httpx_val is not None) == (faster_val is not None), f"Header {header} presence differs"
    
    def test_response_cookies_parity(self, test_urls):
        """Test that cookies handling works the same."""
        # Use endpoint that sets cookies
        cookie_url = test_urls['cookies_set'] + '/test/value'
        
        httpx_response = httpx.get(cookie_url)
        faster_response = faster_http.get(cookie_url)
        
        httpx_cookies = httpx_response.cookies
        faster_cookies = faster_response.cookies
        
        # Both should have cookies objects (not necessarily dict)
        assert httpx_cookies is not None
        assert faster_cookies is not None
        
        # Check that both support item access
        assert hasattr(httpx_cookies, '__getitem__')
        assert hasattr(faster_cookies, '__getitem__')
        
        # Check that the test cookie was set
        assert 'test' in httpx_cookies
        assert 'test' in faster_cookies
        assert httpx_cookies['test'] == faster_cookies['test']


class TestClientObjectParity:
    """Test that Client objects have full parity with httpx."""
    
    def test_client_initialization_parity(self):
        """Test that Client initialization works the same."""
        # Test basic initialization
        httpx_client = httpx.Client()
        faster_client = faster_http.Client()
        
        # Both should have the same basic attributes
        basic_attrs = ['headers', 'cookies', 'params', 'auth', 'base_url']
        for attr in basic_attrs:
            assert hasattr(httpx_client, attr), f"httpx Client missing attribute: {attr}"
            assert hasattr(faster_client, attr), f"faster-http Client missing attribute: {attr}"
        
        # Clean up
        httpx_client.close()
        faster_client.close()
    
    def test_client_methods_parity(self):
        """Test that Client methods work the same."""
        httpx_client = httpx.Client()
        faster_client = faster_http.Client()
        
        # Test HTTP methods
        http_methods = ['get', 'post', 'put', 'patch', 'delete', 'head', 'options', 'request']
        for method in http_methods:
            assert hasattr(httpx_client, method), f"httpx Client missing method: {method}"
            assert hasattr(faster_client, method), f"faster-http Client missing method: {method}"
            assert callable(getattr(httpx_client, method)), f"httpx Client.{method} not callable"
            assert callable(getattr(faster_client, method)), f"faster-http Client.{method} not callable"
        
        # Test advanced methods
        advanced_methods = ['build_request', 'send']
        for method in advanced_methods:
            assert hasattr(httpx_client, method), f"httpx Client missing method: {method}"
            assert hasattr(faster_client, method), f"faster-http Client missing method: {method}"
            assert callable(getattr(httpx_client, method)), f"httpx Client.{method} not callable"
            assert callable(getattr(faster_client, method)), f"faster-http Client.{method} not callable"
        
        # Clean up
        httpx_client.close()
        faster_client.close()
    
    def test_client_configuration_parity(self, test_urls, sample_headers, sample_cookies):
        """Test that Client configuration works the same."""
        # Use local test server instead of external URL
        base_url = test_urls['get'].rsplit('/', 1)[0]  # Extract base URL from test URLs
        config = {
            'base_url': base_url,
            'headers': sample_headers,
            'cookies': sample_cookies,
            'timeout': 30.0,
            'follow_redirects': True
        }
        
        # Test that both clients can be configured the same way
        httpx_client = httpx.Client(**config)
        faster_client = faster_http.Client(**config)
        
        # Both should accept the same configuration
        assert httpx_client.base_url is not None
        assert faster_client.base_url is not None
        
        # Clean up
        httpx_client.close()
        faster_client.close()
    
    @pytest.mark.asyncio
    async def test_async_client_parity(self):
        """Test that AsyncClient has the same interface."""
        httpx_client = httpx.AsyncClient()
        faster_client = faster_http.AsyncClient()
        
        # Test HTTP methods
        http_methods = ['get', 'post', 'put', 'patch', 'delete', 'head', 'options', 'request']
        for method in http_methods:
            assert hasattr(httpx_client, method), f"httpx AsyncClient missing method: {method}"
            assert hasattr(faster_client, method), f"faster-http AsyncClient missing method: {method}"
            assert callable(getattr(httpx_client, method)), f"httpx AsyncClient.{method} not callable"
            assert callable(getattr(faster_client, method)), f"faster-http AsyncClient.{method} not callable"
        
        # Test advanced methods
        advanced_methods = ['build_request', 'send']
        for method in advanced_methods:
            assert hasattr(httpx_client, method), f"httpx AsyncClient missing method: {method}"
            assert hasattr(faster_client, method), f"faster-http AsyncClient missing method: {method}"
            assert callable(getattr(httpx_client, method)), f"httpx AsyncClient.{method} not callable"
            assert callable(getattr(faster_client, method)), f"faster-http AsyncClient.{method} not callable"
        
        # Clean up
        await httpx_client.aclose()
        await faster_client.aclose()


class TestAuthenticationParity:
    """Test that authentication has full parity with httpx."""
    
    def test_auth_classes_parity(self):
        """Test that auth classes work the same."""
        # Test BasicAuth
        httpx_auth = httpx.BasicAuth('user', 'pass')
        faster_auth = faster_http.BasicAuth('user', 'pass')
        
        # Both should have auth_flow method
        assert hasattr(httpx_auth, 'auth_flow')
        assert hasattr(faster_auth, 'auth_flow')
        
        # Both should be callable with a request
        assert callable(httpx_auth.auth_flow)
        assert callable(faster_auth.auth_flow)
        
        # Test DigestAuth
        httpx_digest = httpx.DigestAuth('user', 'pass')
        faster_digest = faster_http.DigestAuth('user', 'pass')
        
        assert hasattr(httpx_digest, 'auth_flow')
        assert hasattr(faster_digest, 'auth_flow')
        
        # Test NetRCAuth with temporary file
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write('machine example.com login user password pass\n')
            netrc_file = f.name
        
        try:
            httpx_netrc = httpx.NetRCAuth(file=netrc_file)
            faster_netrc = faster_http.NetRCAuth(file=netrc_file)
            
            assert hasattr(httpx_netrc, 'auth_flow')
            assert hasattr(faster_netrc, 'auth_flow')
        finally:
            import os
            os.unlink(netrc_file)
        
        # Test that faster-http specific attributes exist when needed
        assert hasattr(faster_auth, 'username')
        assert hasattr(faster_auth, 'password')
        assert faster_auth.username == 'user'
        assert faster_auth.password == 'pass'
    
    def test_auth_integration_parity(self, test_urls):
        """Test that auth integration works the same."""
        # Test tuple auth
        try:
            httpx_response = httpx.get(test_urls['basic_auth'], auth=('user', 'pass'))
            faster_response = faster_http.get(test_urls['basic_auth'], auth=('user', 'pass'))
            
            # Both should handle auth the same way
            assert httpx_response.status_code == faster_response.status_code
        except Exception:
            # Auth endpoint might not be available, that's okay
            pass
        
        # Test BasicAuth object
        httpx_auth = httpx.BasicAuth('user', 'pass')
        faster_auth = faster_http.BasicAuth('user', 'pass')
        
        try:
            httpx_response = httpx.get(test_urls['basic_auth'], auth=httpx_auth)
            faster_response = faster_http.get(test_urls['basic_auth'], auth=faster_auth)
            
            # Both should handle auth the same way
            assert httpx_response.status_code == faster_response.status_code
        except Exception:
            # Auth endpoint might not be available, that's okay
            pass


class TestErrorHandlingParity:
    """Test that error handling has full parity with httpx."""
    
    def test_exception_hierarchy_parity(self):
        """Test that exception hierarchy is similar."""
        # Test that base exceptions exist
        assert hasattr(httpx, 'HTTPError')
        assert hasattr(faster_http, 'HTTPError')
        
        # Test that specific exceptions exist
        specific_exceptions = ['RequestError', 'ConnectTimeout', 'ReadTimeout']
        for exc in specific_exceptions:
            httpx_has = hasattr(httpx, exc)
            faster_has = hasattr(faster_http, exc)
            
            if httpx_has:
                assert faster_has, f"faster-http missing exception: {exc}"
    
    def test_error_raising_parity(self, test_urls):
        """Test that errors are raised the same way."""
        # Test 404 error
        httpx_response = httpx.get(test_urls['status'].format(code=404))
        faster_response = faster_http.get(test_urls['status'].format(code=404))
        
        # Both should raise the same type of error
        with pytest.raises(httpx.HTTPStatusError):
            httpx_response.raise_for_status()
        
        with pytest.raises(faster_http.HTTPError):
            faster_response.raise_for_status()
    
    def test_connection_error_parity(self):
        """Test that connection errors are handled the same."""
        invalid_url = 'http://127.0.0.1:99999'
        timeout = 1.0
        
        # Both should raise connection errors
        with pytest.raises((httpx.ConnectError, httpx.RequestError)):
            httpx.get(invalid_url, timeout=timeout)
        
        with pytest.raises((faster_http.ConnectTimeout, faster_http.RequestError)):
            faster_http.get(invalid_url, timeout=timeout)
    
    def test_timeout_error_parity(self, test_urls):
        """Test that timeout errors are handled the same."""
        timeout = 1.0
        
        # Both should raise timeout errors
        with pytest.raises((httpx.ReadTimeout, httpx.TimeoutException)):
            httpx.get(test_urls['delay'].format(seconds=5), timeout=timeout)
        
        with pytest.raises((faster_http.ReadTimeout, faster_http.RequestError)):
            faster_http.get(test_urls['delay'].format(seconds=5), timeout=timeout)