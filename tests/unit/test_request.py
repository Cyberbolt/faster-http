"""
Unit tests for Request object functionality.
Tests request object constructor and properties.
Following CLAUDE.md requirements: test httpx first, then faster_http for comparison.
"""

import httpx
import faster_http


class TestRequestConstructor:
    """Test Request constructor functionality - httpx vs faster_http comparison."""
    
    def test_request_basic_constructor_comparison(self):
        """Test basic Request constructor - httpx vs faster_http."""
        method = "POST"
        url = "https://api.example.com/data"
        headers = {"Content-Type": "application/json", "User-Agent": "test-client"}
        content = b"test content data"
        
        # First test httpx Request creation
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
        assert "User-Agent" in httpx_request.headers
        assert httpx_request.headers["Content-Type"] == "application/json"
        assert httpx_request.headers["User-Agent"] == "test-client"
        assert httpx_request.content == content
        
        # Then test faster_http Request creation (should match httpx exactly)
        faster_request = faster_http.Request(
            method=method,
            url=url,
            headers=headers,
            content=content
        )
        
        # Test faster_http request properties (should be identical to httpx)
        assert faster_request.method == method
        assert faster_request.url == url
        assert "Content-Type" in faster_request.headers
        assert "User-Agent" in faster_request.headers
        assert faster_request.headers["Content-Type"] == "application/json"
        assert faster_request.headers["User-Agent"] == "test-client"
        assert faster_request.content == content
        
        # Both should have identical properties
        assert httpx_request.method == faster_request.method
        assert str(httpx_request.url) == faster_request.url
        assert httpx_request.content == faster_request.content
        assert httpx_request.headers["Content-Type"] == faster_request.headers["Content-Type"]
        assert httpx_request.headers["User-Agent"] == faster_request.headers["User-Agent"]
    
    def test_request_minimal_parameters_comparison(self):
        """Test Request with minimal parameters - httpx vs faster_http."""
        method = "GET"
        url = "https://example.com"
        
        # First test httpx Request with minimal parameters
        httpx_request = httpx.Request(method=method, url=url)
        
        # Test httpx minimal request properties
        assert httpx_request.method == method
        assert str(httpx_request.url) == url
        assert httpx_request.content == b""  # httpx defaults to empty bytes
        
        # Then test faster_http Request with minimal parameters (should match httpx)
        faster_request = faster_http.Request(method=method, url=url)
        
        # Test faster_http minimal request properties (should match httpx)
        assert faster_request.method == method
        assert faster_request.url == url
        assert faster_request.content == b""  # Should match httpx default
        
        # Both should have identical minimal properties
        assert httpx_request.method == faster_request.method
        assert str(httpx_request.url) == faster_request.url
        assert httpx_request.content == faster_request.content
    
    def test_request_with_empty_content_comparison(self):
        """Test Request with empty content - httpx vs faster_http."""
        method = "POST"
        url = "https://api.example.com/empty"
        empty_content = b""
        
        # First test httpx Request with empty content
        httpx_request = httpx.Request(
            method=method,
            url=url,
            content=empty_content
        )
        
        assert httpx_request.method == method
        assert str(httpx_request.url) == url
        assert httpx_request.content == empty_content
        assert len(httpx_request.content) == 0
        
        # Then test faster_http Request with empty content (should match httpx)
        faster_request = faster_http.Request(
            method=method,
            url=url,
            content=empty_content
        )
        
        assert faster_request.method == method
        assert faster_request.url == url
        assert faster_request.content == empty_content
        assert len(faster_request.content) == 0
        
        # Both should handle empty content identically
        assert httpx_request.method == faster_request.method
        assert str(httpx_request.url) == faster_request.url
        assert httpx_request.content == faster_request.content
        assert len(httpx_request.content) == len(faster_request.content)
    
    def test_request_with_none_content_comparison(self):
        """Test Request with None content - httpx vs faster_http."""
        method = "GET"
        url = "https://example.com/test"
        
        # First test httpx Request with None content
        try:
            httpx_request = httpx.Request(
                method=method,
                url=url,
                content=None
            )
            httpx_accepts_none = True
            httpx_content = httpx_request.content
        except Exception:
            httpx_accepts_none = False
            httpx_content = None
        
        # Then test faster_http Request with None content (should match httpx behavior)
        try:
            faster_request = faster_http.Request(
                method=method,
                url=url,
                content=None
            )
            faster_accepts_none = True
            faster_content = faster_request.content
        except Exception:
            faster_accepts_none = False
            faster_content = None
        
        # Both should handle None content consistently
        assert httpx_accepts_none == faster_accepts_none
        if httpx_accepts_none and faster_accepts_none:
            assert httpx_content == faster_content
    
    def test_request_with_different_methods_comparison(self):
        """Test Request with different HTTP methods - httpx vs faster_http."""
        url = "https://api.example.com/endpoint"
        methods = ["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"]
        
        for method in methods:
            # First test httpx Request with each method
            httpx_request = httpx.Request(method=method, url=url)
            assert httpx_request.method == method
            assert str(httpx_request.url) == url
            
            # Then test faster_http Request with same method (should match httpx)
            faster_request = faster_http.Request(method=method, url=url)
            assert faster_request.method == method
            assert faster_request.url == url
            
            # Both should handle each method identically
            assert httpx_request.method == faster_request.method
            assert str(httpx_request.url) == faster_request.url
    
    def test_request_with_headers_object_comparison(self):
        """Test Request with Headers object - httpx vs faster_http."""
        method = "POST"
        url = "https://api.example.com/headers-test"
        
        # First test httpx Request with httpx Headers object
        httpx_headers_data = {"Accept": "application/json", "Authorization": "Bearer token"}
        httpx_headers = httpx.Headers(httpx_headers_data)
        httpx_request = httpx.Request(
            method=method,
            url=url,
            headers=httpx_headers
        )
        
        assert httpx_request.method == method
        assert "Accept" in httpx_request.headers
        assert "Authorization" in httpx_request.headers
        assert httpx_request.headers["Accept"] == "application/json"
        assert httpx_request.headers["Authorization"] == "Bearer token"
        
        # Then test faster_http Request with faster_http Headers object
        faster_headers_data = {"Accept": "application/json", "Authorization": "Bearer token"}
        faster_headers = faster_http.Headers(faster_headers_data)
        faster_request = faster_http.Request(
            method=method,
            url=url,
            headers=faster_headers
        )
        
        assert faster_request.method == method
        assert "Accept" in faster_request.headers
        assert "Authorization" in faster_request.headers
        assert faster_request.headers["Accept"] == "application/json"
        assert faster_request.headers["Authorization"] == "Bearer token"
        
        # Both should handle Headers objects identically
        assert httpx_request.method == faster_request.method
        assert str(httpx_request.url) == faster_request.url
        assert httpx_request.headers["Accept"] == faster_request.headers["Accept"]
        assert httpx_request.headers["Authorization"] == faster_request.headers["Authorization"]
    
    def test_request_with_complex_url_comparison(self):
        """Test Request with complex URL - httpx vs faster_http."""
        method = "GET"
        complex_url = "https://api.example.com:8080/v1/data?search=test&limit=10#section1"
        
        # First test httpx Request with complex URL
        httpx_request = httpx.Request(method=method, url=complex_url)
        
        assert httpx_request.method == method
        assert str(httpx_request.url) == complex_url
        
        # Test URL components
        assert httpx_request.url.scheme == "https"
        assert httpx_request.url.host == "api.example.com"
        assert httpx_request.url.port == 8080
        assert httpx_request.url.path == "/v1/data"
        assert b"search=test" in httpx_request.url.query
        assert b"limit=10" in httpx_request.url.query
        assert httpx_request.url.fragment == "section1"
        
        # Then test faster_http Request with complex URL (should match httpx)
        faster_request = faster_http.Request(method=method, url=complex_url)
        
        assert faster_request.method == method
        assert faster_request.url == complex_url
        
        # Test URL components (should match httpx)
        assert faster_request.url.scheme == "https"
        assert faster_request.url.host == "api.example.com"
        assert faster_request.url.port == 8080
        assert faster_request.url.path == "/v1/data"
        assert b"search=test" in faster_request.url.query
        assert b"limit=10" in faster_request.url.query
        assert faster_request.url.fragment == "section1"
        
        # Both should parse complex URLs identically
        assert httpx_request.method == faster_request.method
        assert str(httpx_request.url) == faster_request.url
        assert httpx_request.url.scheme == faster_request.url.scheme
        assert httpx_request.url.host == faster_request.url.host
        assert httpx_request.url.port == faster_request.url.port
        assert httpx_request.url.path == faster_request.url.path
        assert httpx_request.url.fragment == faster_request.url.fragment
    
    def test_request_properties_consistency_comparison(self):
        """Test that Request objects have consistent properties - httpx vs faster_http."""
        method = "POST"
        url = "https://api.example.com/test"
        headers = {"Content-Type": "application/json"}
        content = b"test data"
        
        # First test httpx Request properties
        httpx_request = httpx.Request(
            method=method,
            url=url,
            headers=headers,
            content=content
        )
        
        # Get all public properties from httpx Request
        httpx_properties = [attr for attr in dir(httpx_request) if not attr.startswith('_')]
        
        # Then test faster_http Request properties
        faster_request = faster_http.Request(
            method=method,
            url=url,
            headers=headers,
            content=content
        )
        
        # Get all public properties from faster_http Request
        faster_properties = [attr for attr in dir(faster_request) if not attr.startswith('_')]
        
        # faster_http should have at least all httpx properties
        for prop in httpx_properties:
            assert hasattr(faster_request, prop), f"faster_http Request missing httpx property: {prop}"
        
        # Test that common properties have compatible values
        common_properties = ['method', 'url', 'headers', 'content']
        for prop in common_properties:
            if hasattr(httpx_request, prop) and hasattr(faster_request, prop):
                httpx_value = getattr(httpx_request, prop)
                faster_value = getattr(faster_request, prop)
                
                # Special handling for URL (might be string vs URL object)
                if prop == 'url':
                    assert str(httpx_value) == str(faster_value), f"Property {prop} differs"
                elif prop == 'headers':
                    # Headers should contain same key-value pairs
                    for key in httpx_value:
                        assert key in faster_value, f"Header {key} missing in faster_http"
                        assert httpx_value[key] == faster_value[key], f"Header {key} value differs"
                else:
                    assert httpx_value == faster_value, f"Property {prop} differs"
    
    def test_request_representation_comparison(self):
        """Test Request string representation - httpx vs faster_http."""
        method = "GET"
        url = "https://example.com/repr-test"
        
        # First test httpx Request representation
        httpx_request = httpx.Request(method=method, url=url)
        httpx_repr = repr(httpx_request)
        
        # httpx repr should contain method and some indication it's a Request
        assert "Request" in httpx_repr or method in httpx_repr
        
        # Then test faster_http Request representation
        faster_request = faster_http.Request(method=method, url=url)
        faster_repr = repr(faster_request)
        
        # faster_http repr should also contain method and indicate it's a Request
        assert "Request" in faster_repr
        assert method in faster_repr
        
        # Both should provide meaningful string representations
        # (exact format may differ, but both should be informative)
        assert len(httpx_repr) > 0
        assert len(faster_repr) > 0
    
    def test_request_interface_consistency_comparison(self):
        """Test that faster_http Request doesn't have extra interfaces that httpx Request doesn't have."""
        # Create instances for interface comparison
        httpx_request = httpx.Request("GET", "https://example.com")
        faster_request = faster_http.Request("GET", "https://example.com")
        
        # Get all public attributes/methods from both
        httpx_attrs = set(attr for attr in dir(httpx_request) if not attr.startswith('_'))
        faster_attrs = set(attr for attr in dir(faster_request) if not attr.startswith('_'))
        
        # faster_http should not have attributes that httpx doesn't have
        extra_attrs = faster_attrs - httpx_attrs
        assert len(extra_attrs) == 0, f"faster_http Request has extra attributes that httpx Request doesn't have: {extra_attrs}"
        
        # Verify that faster_http has all the httpx attributes
        missing_attrs = httpx_attrs - faster_attrs
        assert len(missing_attrs) == 0, f"faster_http Request is missing httpx attributes: {missing_attrs}"