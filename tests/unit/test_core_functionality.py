"""
Unit tests for core functionality verification.
Tests that don't require network connections.
"""

import faster_http


class TestCoreFunctionality:
    """Test core functionality that doesn't require network."""
    
    def test_all_new_features_accessible(self):
        """Test that all new features are accessible."""
        # Test Client with new parameters (creation only)
        client = faster_http.Client(
            base_url="https://example.com",
            timeout=10.0,
            headers={"User-Agent": "test"},
            http1=True,
            http2=False,
            max_redirects=5,
            default_encoding="utf-8",
            params={"api_key": "test123"}
        )
        
        # Verify client properties
        assert client.base_url == "https://example.com"
        assert "User-Agent" in client.headers
        assert client.params["api_key"] == "test123"
        
        # Test AsyncClient with new parameters (creation only)
        async_client = faster_http.AsyncClient(
            base_url="https://api.example.com",
            timeout=15.0,
            http1=False,
            http2=True,
            max_redirects=10,
            default_encoding="utf-8",
            params={"version": "v1"}
        )
        
        # Verify async client properties
        assert async_client.base_url == "https://api.example.com"
        assert async_client.params["version"] == "v1"
    
    def test_request_enhanced_constructor_comprehensive(self):
        """Comprehensive test of enhanced Request constructor."""
        # Test with all parameters
        request = faster_http.Request(
            method="PUT",
            url="https://api.example.com/resource/123",
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer token123",
                "X-Custom-Header": "custom-value"
            },
            content=b'{"id": 123, "name": "test"}',
            params={
                "version": "v2",
                "format": "json",
                "include": "metadata"
            },
            cookies={
                "session_id": "sess_abc123",
                "preferences": "theme=dark",
                "auth_token": "auth_xyz789"
            },
            data={
                "form_field1": "value1",
                "form_field2": "value2",
                "nested": {"key": "value"}
            },
            files={
                "document": "document_content",
                "image": "image_data",
                "backup": "backup_file_content"
            },
            json={
                "user_id": 12345,
                "action": "update",
                "metadata": {
                    "timestamp": "2024-01-01",
                    "source": "api"
                }
            },
            stream=True
        )
        
        # Verify all properties
        assert request.method == "PUT"
        assert request.url == "https://api.example.com/resource/123"
        
        # Headers
        assert request.headers["Content-Type"] == "application/json"
        assert request.headers["Authorization"] == "Bearer token123"
        assert request.headers["X-Custom-Header"] == "custom-value"
        
        # Content
        assert request.content == b'{"id": 123, "name": "test"}'
        
        # Params
        assert request.params["version"] == "v2"
        assert request.params["format"] == "json"
        assert request.params["include"] == "metadata"
        
        # Cookies
        assert request.cookies["session_id"] == "sess_abc123"
        assert request.cookies["preferences"] == "theme=dark"
        assert request.cookies["auth_token"] == "auth_xyz789"
        
        # Data
        assert request.data["form_field1"] == "value1"
        assert request.data["form_field2"] == "value2"
        assert request.data["nested"]["key"] == "value"
        
        # Files
        assert request.files["document"] == "document_content"
        assert request.files["image"] == "image_data"
        assert request.files["backup"] == "backup_file_content"
        
        # JSON
        assert request.json["user_id"] == 12345
        assert request.json["action"] == "update"
        assert request.json["metadata"]["timestamp"] == "2024-01-01"
        assert request.json["metadata"]["source"] == "api"
        
        # Stream
        assert request.stream == True
    
    def test_response_methods_exist_and_callable(self):
        """Test that new Response methods exist and are callable."""
        # Test that Response class has the new methods
        assert hasattr(faster_http.Response, 'read')
        assert callable(getattr(faster_http.Response, 'read'))
        
        assert hasattr(faster_http.Response, 'next')
        assert callable(getattr(faster_http.Response, 'next'))
        
        assert hasattr(faster_http.Response, 'next_request')
        # next_request is a property, not a method, so it shouldn't be callable
        
        # Test that Response class has async methods too
        assert hasattr(faster_http.Response, 'aread')
        assert callable(getattr(faster_http.Response, 'aread'))
        
        assert hasattr(faster_http.Response, 'anext')
        assert callable(getattr(faster_http.Response, 'anext'))
    
    def test_exception_hierarchy_intact(self):
        """Test that exception hierarchy is intact."""
        # Test that all expected exceptions exist
        exceptions = [
            'HTTPError', 'ConnectError', 'ConnectTimeout', 'TimeoutException',
            'ReadTimeout', 'WriteTimeout', 'PoolTimeout', 'RequestError',
            'ResponseError', 'HTTPStatusError', 'ClientError', 'ServerError',
            'StreamError', 'StreamConsumed', 'StreamClosed', 'ProtocolError',
            'DecodingError', 'TooManyRedirects', 'TransportError', 'ProxyError',
            'SSLError', 'CertificateError', 'NetworkError', 'DNSError'
        ]
        
        for exc_name in exceptions:
            assert hasattr(faster_http, exc_name), f"Missing exception: {exc_name}"
            exc_class = getattr(faster_http, exc_name)
            assert issubclass(exc_class, Exception), f"{exc_name} is not an Exception subclass"
    
    def test_model_classes_intact(self):
        """Test that model classes are intact and functional."""
        model_classes = [
            'Headers', 'QueryParams', 'Cookies', 'URL', 'Timeout', 'Limits',
            'BasicAuth', 'DigestAuth', 'NetRCAuth'
        ]
        
        for model_name in model_classes:
            assert hasattr(faster_http, model_name), f"Missing model class: {model_name}"
            model_class = getattr(faster_http, model_name)
            assert callable(model_class), f"{model_name} is not callable"
        
        # Test basic instantiation
        headers = faster_http.Headers({"Content-Type": "application/json"})
        assert headers is not None
        
        params = faster_http.QueryParams({"key": "value"})
        assert params is not None
        
        cookies = faster_http.Cookies({"session": "abc123"})
        assert cookies is not None
        
        url = faster_http.URL("https://example.com")
        assert url is not None
        
        timeout = faster_http.Timeout(connect=5.0, read=10.0)
        assert timeout is not None
        
        limits = faster_http.Limits(max_connections=100)
        assert limits is not None
        
        basic_auth = faster_http.BasicAuth("user", "pass")
        assert basic_auth is not None