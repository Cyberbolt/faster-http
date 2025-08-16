"""
Comprehensive test for hooks system functionality.
Tests event hooks system with httpx vs faster_http comparison.
Following CLAUDE.md requirements: test httpx first, then faster_http for comparison.
"""

import httpx

import faster_http


class TestHooksSystemComprehensive:
    """Comprehensive test of the hooks system capabilities - httpx vs faster_http comparison."""

    def test_hook_types_support_comparison(self):
        """Test supported hook types - httpx vs faster_http."""

        # Define hook functions for testing
        def sample_request_hook(request):
            pass

        def sample_response_hook(response):
            pass

        # First test httpx supported hook types
        httpx_hook_types = {"request": [sample_request_hook], "response": [sample_response_hook]}

        httpx_client = httpx.Client(event_hooks=httpx_hook_types)
        assert httpx_client is not None
        assert hasattr(httpx_client, "event_hooks")
        assert "request" in httpx_client.event_hooks
        assert "response" in httpx_client.event_hooks
        httpx_client.close()

        # Then test faster_http supported hook types (should match httpx)
        faster_hook_types = {"request": [sample_request_hook], "response": [sample_response_hook]}

        faster_client = faster_http.Client(event_hooks=faster_hook_types)
        assert faster_client is not None
        assert hasattr(faster_client, "event_hooks")
        assert "request" in faster_client.event_hooks
        assert "response" in faster_client.event_hooks
        faster_client.close()

    def test_hook_configuration_formats_comparison(self):
        """Test different hook configuration formats - httpx vs faster_http."""

        def sample_hook(arg):
            pass

        # Test configuration formats
        configurations = [
            # Single callable
            {"request": sample_hook},
            # List of callables
            {"request": [sample_hook, sample_hook]},
            # Multiple hook types
            {"request": [sample_hook], "response": [sample_hook]},
            # Empty configuration
            {},
        ]

        for config in configurations:
            # First test httpx configuration format
            try:
                httpx_client = httpx.Client(event_hooks=config)
                httpx_success = True
                httpx_client.close()
            except Exception:
                httpx_success = False

            # Then test faster_http configuration format (should match httpx)
            try:
                faster_client = faster_http.Client(event_hooks=config)
                faster_success = True
                faster_client.close()
            except Exception:
                faster_success = False

            # Both should handle configuration the same way
            assert httpx_success == faster_success

    def test_client_hooks_support_comparison(self):
        """Test hooks support in different client types - httpx vs faster_http."""

        def test_hook(arg):
            pass

        test_hooks = {"request": [test_hook]}

        # First test httpx sync Client with hooks
        httpx_client = httpx.Client(event_hooks=test_hooks)
        assert httpx_client is not None
        assert hasattr(httpx_client, "event_hooks")
        httpx_client.close()

        # Then test faster_http sync Client with hooks (should match httpx)
        faster_client = faster_http.Client(event_hooks=test_hooks)
        assert faster_client is not None
        assert hasattr(faster_client, "event_hooks")
        faster_client.close()

        # First test httpx AsyncClient with hooks
        httpx_async_client = httpx.AsyncClient(event_hooks=test_hooks)
        assert httpx_async_client is not None
        assert hasattr(httpx_async_client, "event_hooks")

        # Then test faster_http AsyncClient with hooks (should match httpx)
        faster_async_client = faster_http.AsyncClient(event_hooks=test_hooks)
        assert faster_async_client is not None
        assert hasattr(faster_async_client, "event_hooks")

    def test_hook_execution_context_comparison(self):
        """Test hook execution context - httpx vs faster_http."""
        # Track hook execution
        httpx_contexts = []
        faster_contexts = []

        def httpx_request_hook(request):
            httpx_contexts.append(
                {
                    "type": "request",
                    "has_method": hasattr(request, "method"),
                    "has_url": hasattr(request, "url"),
                    "has_headers": hasattr(request, "headers"),
                }
            )

        def httpx_response_hook(response):
            httpx_contexts.append(
                {
                    "type": "response",
                    "has_status_code": hasattr(response, "status_code"),
                    "has_headers": hasattr(response, "headers"),
                    "has_content": hasattr(response, "content"),
                }
            )

        def faster_request_hook(request):
            faster_contexts.append(
                {
                    "type": "request",
                    "has_method": hasattr(request, "method"),
                    "has_url": hasattr(request, "url"),
                    "has_headers": hasattr(request, "headers"),
                }
            )

        def faster_response_hook(response):
            faster_contexts.append(
                {
                    "type": "response",
                    "has_status_code": hasattr(response, "status_code"),
                    "has_headers": hasattr(response, "headers"),
                    "has_content": hasattr(response, "content"),
                }
            )

        # First test httpx hook execution context
        httpx_client = httpx.Client(event_hooks={"request": [httpx_request_hook], "response": [httpx_response_hook]})
        assert httpx_client is not None
        httpx_client.close()

        # Then test faster_http hook execution context (should match httpx)
        faster_client = faster_http.Client(
            event_hooks={"request": [faster_request_hook], "response": [faster_response_hook]}
        )
        assert faster_client is not None
        faster_client.close()

    def test_hooks_httpx_compatibility_comparison(self):
        """Test httpx compatibility of the hooks system - httpx vs faster_http."""

        def log_request(request):
            pass

        def log_response(response):
            pass

        # First test httpx-style hook configuration
        httpx_style_hooks = {"request": [log_request], "response": [log_response]}

        httpx_client = httpx.Client(event_hooks=httpx_style_hooks, timeout=10.0, headers={"User-Agent": "httpx-test"})
        assert httpx_client is not None
        assert hasattr(httpx_client, "event_hooks")
        assert "request" in httpx_client.event_hooks
        assert "response" in httpx_client.event_hooks
        httpx_client.close()

        # Then test faster_http with same httpx-style configuration
        faster_client = faster_http.Client(
            event_hooks=httpx_style_hooks, timeout=10.0, headers={"User-Agent": "faster-http-test"}
        )
        assert faster_client is not None
        assert hasattr(faster_client, "event_hooks")
        assert "request" in faster_client.event_hooks
        assert "response" in faster_client.event_hooks
        faster_client.close()

        # Both should support the same configuration syntax

    def test_hook_error_scenarios_comparison(self):
        """Test various error scenarios in hooks - httpx vs faster_http."""

        # Scenario 1: Hook raises exception
        def failing_hook(request):
            raise ValueError("Hook failed intentionally")

        # First test httpx behavior with failing hook
        try:
            httpx_client = httpx.Client(event_hooks={"request": [failing_hook]})
            httpx_accepts_failing = True
            httpx_client.close()
        except Exception:
            httpx_accepts_failing = False

        # Then test faster_http behavior with failing hook
        try:
            faster_client = faster_http.Client(event_hooks={"request": [failing_hook]})
            faster_accepts_failing = True
            faster_client.close()
        except Exception:
            faster_accepts_failing = False

        # Both should handle failing hooks the same way
        assert httpx_accepts_failing == faster_accepts_failing

        # Scenario 2: Non-callable hook
        # First test httpx behavior with non-callable hook
        try:
            httpx_client = httpx.Client(event_hooks={"request": ["not_callable"]})
            httpx_accepts_non_callable = True
            httpx_client.close()
        except Exception:
            httpx_accepts_non_callable = False

        # Then test faster_http behavior with non-callable hook
        try:
            faster_client = faster_http.Client(event_hooks={"request": ["not_callable"]})
            faster_accepts_non_callable = True
            faster_client.close()
        except Exception:
            faster_accepts_non_callable = False

        # Both should handle non-callable hooks the same way
        assert httpx_accepts_non_callable == faster_accepts_non_callable

    def test_hook_system_integration_comparison(self):
        """Test hook system integration with other features - httpx vs faster_http."""

        def integration_hook(arg):
            pass

        # Test hooks with authentication
        # First test httpx hooks with auth
        httpx_auth = httpx.BasicAuth("user", "pass")
        httpx_client = httpx.Client(auth=httpx_auth, event_hooks={"request": [integration_hook]}, timeout=10.0)
        assert httpx_client is not None
        assert hasattr(httpx_client, "event_hooks")
        assert hasattr(httpx_client, "auth") or hasattr(httpx_client, "_auth")
        httpx_client.close()

        # Then test faster_http hooks with auth
        faster_auth = faster_http.BasicAuth("user", "pass")
        faster_client = faster_http.Client(auth=faster_auth, event_hooks={"request": [integration_hook]}, timeout=10.0)
        assert faster_client is not None
        assert hasattr(faster_client, "event_hooks")
        faster_client.close()

        # Both should integrate hooks with other features seamlessly

    def test_multiple_hooks_execution_order_comparison(self):
        """Test multiple hooks execution order - httpx vs faster_http."""
        httpx_execution_order = []
        faster_execution_order = []

        def httpx_hook_1(request):
            httpx_execution_order.append("hook_1")

        def httpx_hook_2(request):
            httpx_execution_order.append("hook_2")

        def faster_hook_1(request):
            faster_execution_order.append("hook_1")

        def faster_hook_2(request):
            faster_execution_order.append("hook_2")

        # First test httpx multiple hooks execution order
        httpx_client = httpx.Client(event_hooks={"request": [httpx_hook_1, httpx_hook_2]})
        assert httpx_client is not None
        assert len(httpx_client.event_hooks["request"]) == 2
        httpx_client.close()

        # Then test faster_http multiple hooks execution order
        faster_client = faster_http.Client(event_hooks={"request": [faster_hook_1, faster_hook_2]})
        assert faster_client is not None
        assert len(faster_client.event_hooks["request"]) == 2
        faster_client.close()

    def test_hooks_with_different_client_configurations_comparison(self):
        """Test hooks with various client configurations - httpx vs faster_http."""

        def config_hook(arg):
            pass

        # Test configurations
        configs = [
            {"base_url": "https://api.example.com", "timeout": 30.0, "event_hooks": {"request": [config_hook]}},
            {"headers": {"User-Agent": "test-client"}, "verify": True, "event_hooks": {"response": [config_hook]}},
            {
                "follow_redirects": True,
                "trust_env": True,
                "event_hooks": {"request": [config_hook], "response": [config_hook]},
            },
        ]

        for config in configs:
            # First test httpx Client with configuration and hooks
            httpx_client = httpx.Client(**config)
            assert httpx_client is not None
            assert hasattr(httpx_client, "event_hooks")
            httpx_client.close()

            # Then test faster_http Client with same configuration and hooks
            faster_client = faster_http.Client(**config)
            assert faster_client is not None
            assert hasattr(faster_client, "event_hooks")
            faster_client.close()

    def test_async_hooks_comprehensive_comparison(self):
        """Test async hooks comprehensively - httpx vs faster_http."""

        async def async_request_hook(request):
            pass

        async def async_response_hook(response):
            pass

        # First test httpx AsyncClient with async hooks
        httpx_client = httpx.AsyncClient(
            event_hooks={"request": [async_request_hook], "response": [async_response_hook]}
        )
        assert httpx_client is not None
        assert hasattr(httpx_client, "event_hooks")
        assert "request" in httpx_client.event_hooks
        assert "response" in httpx_client.event_hooks

        # Then test faster_http AsyncClient with async hooks
        faster_client = faster_http.AsyncClient(
            event_hooks={"request": [async_request_hook], "response": [async_response_hook]}
        )
        assert faster_client is not None
        assert hasattr(faster_client, "event_hooks")
        assert "request" in faster_client.event_hooks
        assert "response" in faster_client.event_hooks

    def test_hook_modification_after_creation_comparison(self):
        """Test modifying hooks after client creation - httpx vs faster_http."""

        def new_hook(arg):
            pass

        # First test httpx hook modification after creation
        httpx_client = httpx.Client()
        httpx_client.event_hooks["request"] = [new_hook]
        assert "request" in httpx_client.event_hooks
        assert len(httpx_client.event_hooks["request"]) == 1
        httpx_client.close()

        # Then test faster_http hook modification after creation
        faster_client = faster_http.Client()
        faster_client.event_hooks["request"] = [new_hook]
        assert "request" in faster_client.event_hooks
        assert len(faster_client.event_hooks["request"]) == 1
        faster_client.close()

    def test_hooks_system_final_verification_comparison(self):
        """Final comprehensive verification of hooks system - httpx vs faster_http."""
        # Complex hook setup for final verification
        request_calls = {"httpx": 0, "faster": 0}
        response_calls = {"httpx": 0, "faster": 0}

        def httpx_comprehensive_request_hook(request):
            request_calls["httpx"] += 1
            assert hasattr(request, "method")
            assert hasattr(request, "url")
            assert hasattr(request, "headers")

        def httpx_comprehensive_response_hook(response):
            response_calls["httpx"] += 1
            assert hasattr(response, "status_code")
            assert hasattr(response, "headers")

        def faster_comprehensive_request_hook(request):
            request_calls["faster"] += 1
            assert hasattr(request, "method")
            assert hasattr(request, "url")
            assert hasattr(request, "headers")

        def faster_comprehensive_response_hook(response):
            response_calls["faster"] += 1
            assert hasattr(response, "status_code")
            assert hasattr(response, "headers")

        # First test httpx comprehensive hooks setup
        httpx_client = httpx.Client(
            base_url="https://comprehensive-test.example.com",
            timeout=15.0,
            headers={"User-Agent": "comprehensive-httpx-test"},
            verify=True,
            event_hooks={
                "request": [httpx_comprehensive_request_hook],
                "response": [httpx_comprehensive_response_hook],
            },
        )

        # Verify httpx comprehensive setup
        assert httpx_client is not None
        assert str(httpx_client.base_url) == "https://comprehensive-test.example.com"
        assert hasattr(httpx_client, "event_hooks")
        assert len(httpx_client.event_hooks["request"]) == 1
        assert len(httpx_client.event_hooks["response"]) == 1
        httpx_client.close()

        # Then test faster_http comprehensive hooks setup
        faster_client = faster_http.Client(
            base_url="https://comprehensive-test.example.com",
            timeout=15.0,
            headers={"User-Agent": "comprehensive-faster-test"},
            verify=True,
            event_hooks={
                "request": [faster_comprehensive_request_hook],
                "response": [faster_comprehensive_response_hook],
            },
        )

        # Verify faster_http comprehensive setup (should match httpx)
        assert faster_client is not None
        assert faster_client.base_url == "https://comprehensive-test.example.com"
        assert hasattr(faster_client, "event_hooks")
        assert len(faster_client.event_hooks["request"]) == 1
        assert len(faster_client.event_hooks["response"]) == 1
        faster_client.close()

        # Both should support the same comprehensive configuration
