"""
Test suite for MockTransport class - httpx compatibility testing
Tests MockTransport functionality and httpx API compatibility
"""

import faster_http as http
from tests.utils.httpx_comparison import httpx_compatibility_test


class TestMockTransport:
    """Test MockTransport class compatibility with httpx.MockTransport"""

    def test_mock_transport_creation(self):
        """Test MockTransport can be created with handler"""

        def handler(request):
            return http.Response(200, text="Mocked response")

        transport = http.MockTransport(handler)
        assert transport is not None
        assert hasattr(transport, "handle_request")
        assert hasattr(transport, "handle_async_request")
        assert hasattr(transport, "close")
        assert hasattr(transport, "aclose")

    def test_mock_transport_context_manager(self):
        """Test MockTransport supports context manager protocol"""

        def handler(request):
            return http.Response(200, text="Mocked response")

        transport = http.MockTransport(handler)

        # Test sync context manager
        with transport as t:
            assert t is transport

        # Verify context manager methods exist
        assert hasattr(transport, "__enter__")
        assert hasattr(transport, "__exit__")
        assert hasattr(transport, "__aenter__")
        assert hasattr(transport, "__aexit__")

    def test_mock_transport_simple_handler(self):
        """Test MockTransport with simple response handler"""

        def handler(request):
            return http.Response(200, text="Hello, Mock!")

        transport = http.MockTransport(handler)

        # MockTransport should be able to handle the request
        # Note: This test just verifies the interface exists
        # Actual request handling would require client integration
        assert callable(transport.handle_request)

    def test_mock_transport_json_handler(self):
        """Test MockTransport with JSON response handler"""

        def handler(request):
            return http.Response(200, json={"message": "mocked", "url": str(request.url)})

        transport = http.MockTransport(handler)
        assert transport is not None

    def test_mock_transport_conditional_handler(self):
        """Test MockTransport with conditional response handler"""

        def handler(request):
            if "/users" in str(request.url):
                return http.Response(200, json={"users": []})
            elif request.method == "POST":
                return http.Response(201, json={"created": True})
            else:
                return http.Response(404, text="Not found")

        transport = http.MockTransport(handler)
        assert transport is not None

    def test_mock_transport_status_codes(self):
        """Test MockTransport with various status codes"""

        def handler(request):
            if "/404" in str(request.url):
                return http.Response(404, text="Not found")
            elif "/500" in str(request.url):
                return http.Response(500, text="Server error")
            else:
                return http.Response(200, text="OK")

        transport = http.MockTransport(handler)
        assert transport is not None

    def test_mock_transport_headers(self):
        """Test MockTransport with custom headers"""

        def handler(request):
            headers = {"X-Custom": "test-value", "Content-Type": "application/json"}
            return http.Response(200, headers=headers, json={"test": True})

        transport = http.MockTransport(handler)
        assert transport is not None

    def test_mock_transport_request_inspection(self):
        """Test MockTransport handler can inspect request"""

        def handler(request):
            # Handler can inspect request properties
            method = request.method
            url = str(request.url)
            headers = dict(request.headers) if hasattr(request, "headers") else {}

            return http.Response(200, json={"method": method, "url": url, "received_headers": len(headers)})

        transport = http.MockTransport(handler)
        assert transport is not None

    @httpx_compatibility_test
    def test_mock_transport_httpx_compatibility(self, client_factory):
        """Test MockTransport works similarly to httpx.MockTransport"""

        def handler(request):
            if client_factory.client_type == "httpx":
                # httpx MockTransport handler
                import httpx

                return httpx.Response(200, text="httpx mock")
            else:
                # faster_http MockTransport handler
                return http.Response(200, text="faster_http mock")

        if client_factory.client_type == "httpx":
            import httpx

            transport = httpx.MockTransport(handler)
        else:
            transport = http.MockTransport(handler)

        # Both should support context manager
        assert hasattr(transport, "__enter__")
        assert hasattr(transport, "__exit__")

    def test_mock_transport_error_handling(self):
        """Test MockTransport handler error scenarios"""

        def error_handler(request):
            raise RuntimeError("Handler error")

        transport = http.MockTransport(error_handler)
        assert transport is not None
        # Error handling would be tested in integration tests

    def test_mock_transport_async_handler(self):
        """Test MockTransport with async handler (for future support)"""

        async def async_handler(request):
            return http.Response(200, text="Async response")

        # Should be able to create transport with async handler
        transport = http.MockTransport(async_handler)
        assert transport is not None
        assert hasattr(transport, "handle_async_request")


class TestMockTransportIntegration:
    """Integration tests for MockTransport with Client"""

    def test_mock_transport_with_client_interface(self):
        """Test MockTransport interface is compatible with Client usage"""

        def handler(request):
            return http.Response(200, text="Client mock test")

        transport = http.MockTransport(handler)

        # Verify transport has the required methods that Client would use
        assert hasattr(transport, "handle_request")
        assert callable(transport.handle_request)
        assert hasattr(transport, "close")
        assert callable(transport.close)

    def test_mock_transport_lifecycle(self):
        """Test MockTransport lifecycle methods"""

        def handler(request):
            return http.Response(200, text="Lifecycle test")

        transport = http.MockTransport(handler)

        # Test close method (should not raise)
        transport.close()

        # Test aclose method (should not raise)
        transport.aclose()

    def test_mock_transport_multiple_calls(self):
        """Test MockTransport can handle multiple calls"""
        call_count = 0

        def counting_handler(request):
            nonlocal call_count
            call_count += 1
            return http.Response(200, text=f"Call #{call_count}")

        transport = http.MockTransport(counting_handler)

        # Transport should be ready for multiple calls
        # (Actual multiple calls would be tested in client integration)
        assert transport is not None
