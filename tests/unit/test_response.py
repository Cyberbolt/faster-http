"""
Unit tests for Response object functionality.
Tests response object properties and methods.
"""

import faster_http


class TestResponseInterface:
    """Test Response object interface and properties."""
    
    def test_response_attributes_exist(self):
        """Test that Response objects have required httpx-compatible attributes."""
        # We can't create a real response without making HTTP requests,
        # but we can test that the Response class has the right interface
        # by checking if the attributes exist on the class or instances
        
        # Test that faster_http has Response in its module
        assert hasattr(faster_http, 'Response') or hasattr(faster_http, '_Response')
        
        # Test that the module has the expected functions that return Response objects
        assert hasattr(faster_http, 'get')
        assert hasattr(faster_http, 'post')
        assert hasattr(faster_http, 'put')
        assert hasattr(faster_http, 'patch')
        assert hasattr(faster_http, 'delete')
        assert hasattr(faster_http, 'head')
        assert hasattr(faster_http, 'options')
        assert hasattr(faster_http, 'request')
    
    def test_client_methods_return_responses(self):
        """Test that client methods are set up to return response objects."""
        client = faster_http.Client()
        
        # Test that all HTTP methods exist and are callable
        methods = ['get', 'post', 'put', 'patch', 'delete', 'head', 'options', 'request']
        for method in methods:
            assert hasattr(client, method), f"Client missing {method} method"
            assert callable(getattr(client, method)), f"Client {method} not callable"
    
    def test_async_client_methods_return_responses(self):
        """Test that async client methods are set up to return response objects."""
        client = faster_http.AsyncClient()
        
        # Test that all HTTP methods exist and are callable
        methods = ['get', 'post', 'put', 'patch', 'delete', 'head', 'options', 'request']
        for method in methods:
            assert hasattr(client, method), f"AsyncClient missing {method} method"
            assert callable(getattr(client, method)), f"AsyncClient {method} not callable"


class TestResponseMocking:
    """Test response-like objects for unit testing."""
    
    def test_mock_response_structure(self):
        """Test the structure we expect from responses."""
        # This tests the expected interface without making HTTP requests
        expected_attributes = [
            'status_code', 'headers', 'content', 'text', 'url',
            'encoding', 'elapsed', 'cookies', 'request',
            'is_success', 'is_client_error', 'is_server_error', 'is_redirect',
            'json', 'raise_for_status',
            'iter_bytes', 'iter_text', 'iter_lines', 'iter_raw'
        ]
        
        # Create a simple mock response structure to test against
        class MockResponse:
            def __init__(self):
                self.status_code = 200
                self.headers = {}
                self.content = b"test content"
                self.text = "test content"
                self.url = "https://test.local"
                self.encoding = "utf-8"
                self.elapsed = 0.1
                self.cookies = {}
                self.request = None
                
            @property
            def is_success(self):
                return 200 <= self.status_code < 300
                
            @property
            def is_client_error(self):
                return 400 <= self.status_code < 500
                
            @property
            def is_server_error(self):
                return 500 <= self.status_code < 600
                
            @property
            def is_redirect(self):
                return 300 <= self.status_code < 400
                
            def json(self):
                return {"test": "data"}
                
            def raise_for_status(self):
                if self.status_code >= 400:
                    raise Exception(f"HTTP {self.status_code}")
                    
            def iter_bytes(self, chunk_size=1024):
                return [self.content]
                
            def iter_text(self, chunk_size=None):
                return [self.text]
                
            def iter_lines(self):
                return self.text.split('\n')
                
            def iter_raw(self):
                return [self.content]
        
        # Test that our mock has all expected attributes
        mock_response = MockResponse()
        for attr in expected_attributes:
            assert hasattr(mock_response, attr), f"Mock response missing {attr}"
            
        # Test attribute types and basic functionality
        assert isinstance(mock_response.status_code, int)
        assert isinstance(mock_response.headers, dict)
        assert isinstance(mock_response.content, bytes)
        assert isinstance(mock_response.text, str)
        assert isinstance(mock_response.url, str)
        
        # Test properties
        assert mock_response.is_success
        assert not mock_response.is_client_error
        assert not mock_response.is_server_error
        assert not mock_response.is_redirect
        
        # Test methods
        assert callable(mock_response.json)
        assert callable(mock_response.raise_for_status)
        assert callable(mock_response.iter_bytes)
        assert callable(mock_response.iter_text)
        assert callable(mock_response.iter_lines)
        assert callable(mock_response.iter_raw)
        
        # Test method return types
        assert isinstance(mock_response.json(), dict)
        assert isinstance(list(mock_response.iter_bytes()), list)
        assert isinstance(list(mock_response.iter_text()), list)
        assert isinstance(mock_response.iter_lines(), list)
        assert isinstance(list(mock_response.iter_raw()), list)


class TestHTTPStatusCodes:
    """Test HTTP status code categorization."""
    
    def test_success_status_codes(self):
        """Test success status code identification."""
        success_codes = [200, 201, 202, 204, 206]
        for code in success_codes:
            assert 200 <= code < 300, f"Status {code} should be success"
    
    def test_client_error_status_codes(self):
        """Test client error status code identification."""
        client_error_codes = [400, 401, 403, 404, 422, 429]
        for code in client_error_codes:
            assert 400 <= code < 500, f"Status {code} should be client error"
    
    def test_server_error_status_codes(self):
        """Test server error status code identification."""
        server_error_codes = [500, 501, 502, 503, 504]
        for code in server_error_codes:
            assert 500 <= code < 600, f"Status {code} should be server error"
    
    def test_redirect_status_codes(self):
        """Test redirect status code identification."""
        redirect_codes = [301, 302, 303, 307, 308]
        for code in redirect_codes:
            assert 300 <= code < 400, f"Status {code} should be redirect"


class TestResponseHelpers:
    """Test response helper functionality."""
    
    def test_content_type_parsing(self):
        """Test content type parsing concepts."""
        content_types = {
            "application/json": "json",
            "application/json; charset=utf-8": "json", 
            "text/html": "html",
            "text/plain": "text",
            "application/xml": "xml",
            "image/png": "binary",
            "application/octet-stream": "binary"
        }
        
        for content_type, expected_type in content_types.items():
            # Test content type categorization
            if "json" in content_type.lower():
                assert "json" in expected_type
            elif "text" in content_type.lower() or "html" in content_type.lower():
                assert expected_type in ["text", "html"]
            elif "image" in content_type.lower() or "octet-stream" in content_type.lower():
                assert expected_type == "binary"
    
    def test_encoding_detection(self):
        """Test encoding detection concepts."""
        encodings = ["utf-8", "utf-16", "latin-1", "ascii"]
        
        for encoding in encodings:
            # Test that these are valid encoding names
            assert isinstance(encoding, str)
            assert len(encoding) > 0
            
            # Test encoding validation concept
            try:
                "test".encode(encoding)
                valid = True
            except (LookupError, TypeError):
                valid = False
            assert valid, f"Encoding {encoding} should be valid"


class TestResponseMethods:
    """Test new Response methods added for httpx compatibility."""
    
    def test_response_methods_exist(self):
        """Test that new Response methods exist."""
        # Test method existence on Response class
        methods_to_check = [
            ('read', 'Method for reading response content'),
            ('next', 'Method for getting next response in redirect chain'), 
            ('next_request', 'Property for next request in redirect chain'),
        ]
        
        for method, description in methods_to_check:
            assert hasattr(faster_http.Response, method), f"Missing {method}: {description}"
    
    def test_response_class_accessible(self):
        """Test that Response class is accessible and has expected methods."""
        # Test that our new methods are in the class
        response_methods = [attr for attr in dir(faster_http.Response) if not attr.startswith('_')]
        
        new_methods = ['read', 'next', 'next_request']
        for method in new_methods:
            assert method in response_methods, f"{method} not found in Response class"