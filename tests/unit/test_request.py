"""
Unit tests for Request object functionality.
Tests request object constructor and properties.
"""

import faster_http


class TestRequestConstructor:
    """Test enhanced HttpRequest constructor with all parameters."""
    
    def test_request_enhanced_constructor(self):
        """Test enhanced HttpRequest constructor with all parameters."""
        # Test basic Request creation
        request = faster_http.Request(
            method="POST",
            url="https://api.example.com/data",
            headers={"Content-Type": "application/json", "User-Agent": "test"},
            content=b"test content",
            params={"api_key": "test123", "version": "v1"},
            cookies={"session": "abc123", "token": "xyz789"},
            data={"field1": "value1", "field2": "value2"},
            files={"file1": "content1"},
            json={"key": "value", "nested": {"inner": "data"}},
            stream=True
        )
        
        # Test all properties
        assert request.method == "POST"
        assert request.url == "https://api.example.com/data"
        assert "Content-Type" in request.headers
        assert request.content == b"test content"
        assert request.params["api_key"] == "test123"
        assert request.cookies["session"] == "abc123"
        assert request.data is not None
        assert request.files is not None
        assert request.json is not None
        assert request.stream == True
    
    def test_request_minimal_parameters(self):
        """Test Request with minimal parameters."""
        # Test with minimal parameters
        request = faster_http.Request(
            method="GET",
            url="https://example.com"
        )
        
        # Test default values
        assert request.method == "GET"
        assert request.url == "https://example.com"  
        assert len(request.headers) == 0  # Should be empty dict
        assert request.content is None
        assert len(request.params) == 0   # Should be empty dict
        assert len(request.cookies) == 0  # Should be empty dict
        assert request.data is None
        assert request.files is None
        assert request.json is None
        assert request.stream == False    # Should default to False
    
    def test_request_properties_exist(self):
        """Test that all expected properties exist on Request class."""
        expected_properties = [
            'method', 'url', 'headers', 'content', 
            'params', 'cookies', 'data', 'files', 'json', 'stream'
        ]
        
        for prop in expected_properties:
            assert hasattr(faster_http.Request, prop), f"Missing {prop} property"
    
    def test_request_representation(self):
        """Test Request string representation."""
        request = faster_http.Request(
            method="GET",
            url="https://example.com"
        )
        
        repr_str = repr(request)
        assert "Request" in repr_str
        assert "GET" in repr_str
        assert "https://example.com" in repr_str