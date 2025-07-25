"""
Integration tests for new features added for httpx compatibility.
Tests the enhanced Client constructor, Response methods, and Request constructor.
"""

import faster_http
import asyncio
from tests.stable_server import StableHTTPServer as StableServer


class TestNewFeaturesIntegration:
    """Test new features in integration scenarios."""
    
    def test_client_new_parameters_integration(self):
        """Test new Client parameters in integration scenario."""
        server = StableServer()
        server.start()
        
        try:
            # Test Client with new parameters
            client = faster_http.Client(
                base_url=f"http://127.0.0.1:{server.port}",
                timeout=10.0,
                headers={"User-Agent": "faster-http-integration-test"},
                http1=True,
                http2=False,
                max_redirects=5,
                default_encoding="utf-8",
                params={"test": "integration"}
            )
            
            # Make a request to test the integration
            response = client.get("/json")
            
            # Verify the request succeeded
            assert response.status_code == 200
            data = response.json()
            assert "args" in data
            assert data["args"]["test"] == "integration"  # Default params should be applied
            
            # Test that headers were applied
            assert "User-Agent" in data["headers"]
            assert data["headers"]["User-Agent"] == "faster-http-integration-test"
            
        finally:
            server.stop()
    
    def test_response_new_methods_integration(self):
        """Test new Response methods in integration scenario."""
        server = StableServer()
        server.start()
        
        try:
            client = faster_http.Client()
            response = client.get(f"http://127.0.0.1:{server.port}/json")
            
            # Test read() method
            content = response.read()
            assert isinstance(content, bytes)
            assert len(content) > 0
            
            # Test next() method (should return None for non-redirect)
            next_response = response.next()
            assert next_response is None
            
            # Test next_request property
            next_request = response.next_request
            assert next_request is None
            
        finally:
            server.stop()
    
    async def test_async_response_methods_integration(self):
        """Test async Response methods in integration scenario."""
        server = StableServer()
        server.start()
        
        try:
            async with faster_http.AsyncClient() as client:
                response = await client.get(f"http://127.0.0.1:{server.port}/json")
                
                # Test aread() method
                content = await response.aread()
                assert isinstance(content, bytes)
                assert len(content) > 0
                
                # Test anext() method
                next_response = await response.anext()
                assert next_response is None
                
        finally:
            server.stop()
    
    def test_request_enhanced_constructor_integration(self):
        """Test enhanced Request constructor in integration scenario."""
        # Test that enhanced Request can be created
        request = faster_http.Request(
            method="POST",
            url="https://example.com/api",
            headers={"Content-Type": "application/json"},
            content=b'{"test": "data"}',
            params={"version": "v1"},
            cookies={"session": "abc123"},
            data={"form_field": "value"},
            files={"upload": "file_content"},
            json={"json_field": "json_value"},
            stream=False
        )
        
        # Verify all properties are accessible
        assert request.method == "POST"
        assert request.url == "https://example.com/api"
        assert request.headers["Content-Type"] == "application/json"
        assert request.content == b'{"test": "data"}'
        assert request.params["version"] == "v1"
        assert request.cookies["session"] == "abc123"
        assert request.data["form_field"] == "value"
        assert request.files["upload"] == "file_content"
        assert request.json["json_field"] == "json_value"
        assert request.stream == False
    
    def test_httpx_compatibility_integration(self):
        """Test that faster-http interfaces are compatible with httpx patterns."""
        server = StableServer()
        server.start()
        
        try:
            # Test that common httpx patterns work
            with faster_http.Client(
                base_url=f"http://127.0.0.1:{server.port}",
                headers={"X-Test": "compatibility"},
                timeout=30.0
            ) as client:
                # Test various HTTP methods
                response = client.get("/json", params={"test": "get"})
                assert response.status_code == 200
                
                response = client.post("/post", json={"test": "post"})
                assert response.status_code == 200
                
                # Test response methods
                content = response.read()
                assert isinstance(content, bytes)
                
        finally:
            server.stop()


def test_async_new_features_integration():
    """Async test wrapper for async integration tests."""
    test_instance = TestNewFeaturesIntegration()
    asyncio.run(test_instance.test_async_response_methods_integration())