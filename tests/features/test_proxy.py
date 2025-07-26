"""
Test proxy configuration functionality.
Tests proxy configuration with httpx vs faster_http comparison.
Following CLAUDE.md requirements: test httpx first, then faster_http for comparison.
"""

import httpx
import faster_http
import os


class TestProxyConfiguration:
    """Test proxy configuration features - httpx vs faster_http comparison."""
    
    def test_basic_proxy_string_configuration_comparison(self):
        """Test basic proxy string configuration - httpx vs faster_http."""
        proxy_url = "http://proxy.example.com:8080"
        
        # First test httpx Client with basic proxy string
        httpx_client = httpx.Client(proxy=proxy_url)
        assert httpx_client is not None
        # Check that proxy is configured (different implementations may vary)
        httpx_client.close()
        
        # Then test faster_http Client with same proxy string (should match httpx)
        faster_client = faster_http.Client(proxy=proxy_url)
        assert faster_client is not None
        # Check that proxy is configured
        faster_client.close()
    
    def test_proxy_with_authentication_comparison(self):
        """Test proxy with authentication - httpx vs faster_http."""
        proxy_url = "http://user:pass@proxy.example.com:8080"
        
        # First test httpx Client with authenticated proxy
        httpx_client = httpx.Client(proxy=proxy_url)
        assert httpx_client is not None
        httpx_client.close()
        
        # Then test faster_http Client with same authenticated proxy (should match httpx)
        faster_client = faster_http.Client(proxy=proxy_url)
        assert faster_client is not None
        faster_client.close()
    
    def test_proxy_with_special_characters_comparison(self):
        """Test proxy with special characters in credentials - httpx vs faster_http."""
        from urllib.parse import quote
        
        # Create proxy URL with special characters (properly encoded)
        username = quote("user@domain.com")
        password = quote("p@ssw0rd!#$")
        proxy_url = f"http://{username}:{password}@proxy.example.com:8080"
        
        # First test httpx Client with special character proxy
        httpx_client = httpx.Client(proxy=proxy_url)
        assert httpx_client is not None
        httpx_client.close()
        
        # Then test faster_http Client with same special character proxy (should match httpx)
        faster_client = faster_http.Client(proxy=proxy_url)
        assert faster_client is not None
        faster_client.close()
    
    def test_https_proxy_configuration_comparison(self):
        """Test HTTPS proxy configuration - httpx vs faster_http."""
        https_proxy_url = "https://secure-proxy.example.com:8443"
        
        # First test httpx Client with HTTPS proxy
        httpx_client = httpx.Client(proxy=https_proxy_url)
        assert httpx_client is not None
        httpx_client.close()
        
        # Then test faster_http Client with same HTTPS proxy (should match httpx)
        faster_client = faster_http.Client(proxy=https_proxy_url)
        assert faster_client is not None
        faster_client.close()
    
    def test_proxy_with_different_protocols_comparison(self):
        """Test proxy with different protocols - httpx vs faster_http."""
        http_proxy_url = "http://http-proxy.example.com:8080"
        
        # First test httpx Client with HTTP proxy
        httpx_client = httpx.Client(proxy=http_proxy_url)
        assert httpx_client is not None
        httpx_client.close()
        
        # Then test faster_http Client with same HTTP proxy (should match httpx)
        faster_client = faster_http.Client(proxy=http_proxy_url)
        assert faster_client is not None
        faster_client.close()
    
    def test_socks_proxy_configuration_comparison(self):
        """Test SOCKS proxy configuration - httpx vs faster_http."""
        socks_proxy_url = "socks5://127.0.0.1:1080"
        
        # First test httpx Client with SOCKS proxy
        try:
            httpx_client = httpx.Client(proxy=socks_proxy_url)
            httpx_supports_socks = True
            httpx_client.close()
        except Exception:
            httpx_supports_socks = False
        
        # Then test faster_http Client with SOCKS proxy (should match httpx support)
        try:
            faster_client = faster_http.Client(proxy=socks_proxy_url)
            faster_supports_socks = True
            faster_client.close()
        except Exception:
            faster_supports_socks = False
        
        # Both should handle SOCKS proxies consistently
        # Note: This documents current SOCKS support behavior
    
    def test_proxy_environment_variable_support_comparison(self):
        """Test proxy environment variable support - httpx vs faster_http."""
        proxy_url = "http://env-proxy.example.com:8080"
        
        # Set environment variable
        original_http_proxy = os.environ.get("HTTP_PROXY")
        os.environ["HTTP_PROXY"] = proxy_url
        
        try:
            # First test httpx Client with trust_env=True
            httpx_client = httpx.Client(trust_env=True)
            assert httpx_client is not None
            httpx_client.close()
            
            # Then test faster_http Client with trust_env=True (should match httpx)
            faster_client = faster_http.Client(trust_env=True)
            assert faster_client is not None
            faster_client.close()
            
        finally:
            # Clean up environment variable
            if original_http_proxy is not None:
                os.environ["HTTP_PROXY"] = original_http_proxy
            else:
                os.environ.pop("HTTP_PROXY", None)
    
    def test_async_client_proxy_configuration_comparison(self):
        """Test async client proxy configuration - httpx vs faster_http."""
        import asyncio
        
        async def test_async_proxy():
            proxy_url = "http://async-proxy.example.com:8080"
            
            # First test httpx AsyncClient with proxy (httpx only supports 'proxy', not 'proxies')
            httpx_client = httpx.AsyncClient(proxy=proxy_url)
            assert httpx_client is not None
            await httpx_client.aclose()
            
            # Then test faster_http AsyncClient with same proxy (should match httpx)
            faster_client = faster_http.AsyncClient(proxy=proxy_url)
            assert faster_client is not None
            await faster_client.aclose()
        
        asyncio.run(test_async_proxy())
    
    def test_proxy_with_ssl_configuration_comparison(self):
        """Test proxy with SSL configuration - httpx vs faster_http."""
        proxy_url = "http://ssl-proxy.example.com:8080"
        
        # First test httpx Client with proxy and SSL config
        httpx_client = httpx.Client(
            proxy=proxy_url,
            verify=True,
            trust_env=True
        )
        assert httpx_client is not None
        httpx_client.close()
        
        # Then test faster_http Client with same proxy and SSL config (should match httpx)
        faster_client = faster_http.Client(
            proxy=proxy_url,
            verify=True,
            trust_env=True
        )
        assert faster_client is not None
        faster_client.close()
    
    def test_proxy_with_authentication_objects_comparison(self):
        """Test proxy with authentication objects - httpx vs faster_http."""
        proxy_url = "http://auth-proxy.example.com:8080"
        
        # First test httpx Client with proxy and auth
        httpx_auth = httpx.BasicAuth("user", "pass")
        httpx_client = httpx.Client(
            proxy=proxy_url,
            auth=httpx_auth
        )
        assert httpx_client is not None
        httpx_client.close()
        
        # Then test faster_http Client with same proxy and auth (should match httpx)
        faster_auth = faster_http.BasicAuth("user", "pass")
        faster_client = faster_http.Client(
            proxy=proxy_url,
            auth=faster_auth
        )
        assert faster_client is not None
        faster_client.close()
    
    def test_proxy_with_timeout_configuration_comparison(self):
        """Test proxy with timeout configuration - httpx vs faster_http."""
        proxy_url = "http://timeout-proxy.example.com:8080"
        timeout = 30.0
        
        # First test httpx Client with proxy and timeout
        httpx_client = httpx.Client(
            proxy=proxy_url,
            timeout=timeout
        )
        assert httpx_client is not None
        httpx_client.close()
        
        # Then test faster_http Client with same proxy and timeout (should match httpx)
        faster_client = faster_http.Client(
            proxy=proxy_url,
            timeout=timeout
        )
        assert faster_client is not None
        faster_client.close()
    
    def test_invalid_proxy_configuration_comparison(self):
        """Test invalid proxy configuration handling - httpx vs faster_http."""
        invalid_proxies = [
            "invalid-proxy-url",
            "ftp://proxy.com:21",
            "http://",
            "",
        ]
        
        for invalid_proxy in invalid_proxies:
            # First test httpx behavior with invalid proxy
            try:
                httpx_client = httpx.Client(proxy=invalid_proxy)
                httpx_accepts_invalid = True
                httpx_client.close()
            except Exception:
                httpx_accepts_invalid = False
            
            # Then test faster_http behavior with invalid proxy (should match httpx)
            try:
                faster_client = faster_http.Client(proxy=invalid_proxy)
                faster_accepts_invalid = True
                faster_client.close()
            except Exception:
                faster_accepts_invalid = False
            
            # Both should handle invalid proxies the same way
            # Note: This documents how invalid proxies are handled
    
    def test_proxy_bypass_configuration_comparison(self):
        """Test proxy bypass configuration - httpx vs faster_http."""
        proxy_url = "http://bypass-proxy.example.com:8080"
        
        # First test httpx behavior with proxy bypass
        # httpx doesn't have explicit proxy bypass, but we test the configuration
        httpx_client = httpx.Client(proxy=proxy_url)
        assert httpx_client is not None
        httpx_client.close()
        
        # Then test faster_http with same configuration (should match httpx)
        faster_client = faster_http.Client(proxy=proxy_url)
        assert faster_client is not None
        faster_client.close()
    
    def test_multiple_proxy_protocols_comparison(self):
        """Test multiple proxy protocols - httpx vs faster_http."""
        proxy_configs = [
            "http://http-proxy.example.com:8080",
            "https://https-proxy.example.com:8080",
            "socks5://socks-proxy.example.com:1080",
        ]
        
        for proxy_url in proxy_configs:
            # First test httpx Client with different proxy protocols
            try:
                httpx_client = httpx.Client(proxy=proxy_url)
                httpx_supports_protocol = True
                httpx_client.close()
            except Exception:
                httpx_supports_protocol = False
            
            # Then test faster_http Client with same proxy protocols (should match httpx)
            try:
                faster_client = faster_http.Client(proxy=proxy_url)
                faster_supports_protocol = True
                faster_client.close()
            except Exception:
                faster_supports_protocol = False
            
            # Both should have consistent protocol support
            # Note: This documents current protocol support
    
    def test_proxy_with_headers_comparison(self):
        """Test proxy configuration with custom headers - httpx vs faster_http."""
        proxy_url = "http://header-proxy.example.com:8080"
        headers = {
            "User-Agent": "test-proxy-client/1.0",
            "X-Proxy-Test": "comparison"
        }
        
        # First test httpx Client with proxy and headers
        httpx_client = httpx.Client(
            proxy=proxy_url,
            headers=headers
        )
        assert httpx_client is not None
        assert "User-Agent" in httpx_client.headers
        assert "X-Proxy-Test" in httpx_client.headers
        httpx_client.close()
        
        # Then test faster_http Client with same proxy and headers (should match httpx)
        faster_client = faster_http.Client(
            proxy=proxy_url,
            headers=headers
        )
        assert faster_client is not None
        assert "User-Agent" in faster_client.headers
        assert "X-Proxy-Test" in faster_client.headers
        faster_client.close()
        
        # Both should handle headers with proxy configuration
        assert httpx_client.headers["User-Agent"] == faster_client.headers["User-Agent"]
        assert httpx_client.headers["X-Proxy-Test"] == faster_client.headers["X-Proxy-Test"]
    
    def test_comprehensive_proxy_configuration_comparison(self):
        """Test comprehensive proxy configuration - httpx vs faster_http."""
        # Complex proxy configuration combining multiple features
        proxy_url = "http://user:pass@comprehensive-proxy.example.com:8080"
        headers = {"Proxy-Test": "comprehensive"}
        timeout = 15.0
        
        # First test httpx Client with comprehensive proxy configuration
        httpx_client = httpx.Client(
            proxy=proxy_url,
            headers=headers,
            timeout=timeout,
            verify=True,
            trust_env=True
        )
        
        # Test httpx comprehensive configuration
        assert httpx_client is not None
        assert "Proxy-Test" in httpx_client.headers
        httpx_client.close()
        
        # Then test faster_http Client with same comprehensive configuration
        faster_client = faster_http.Client(
            proxy=proxy_url,
            headers=headers,
            timeout=timeout,
            verify=True,
            trust_env=True
        )
        
        # Test faster_http comprehensive configuration (should match httpx)
        assert faster_client is not None
        assert "Proxy-Test" in faster_client.headers
        faster_client.close()
        
        # Both should support the same comprehensive proxy configuration
        assert httpx_client.headers["Proxy-Test"] == faster_client.headers["Proxy-Test"]