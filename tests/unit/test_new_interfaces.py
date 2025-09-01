"""Tests for newly added interfaces: AsyncBaseTransport, main, Auth."""

import pytest

from tests.utils.httpx_comparison import httpx_compatibility_test


class TestAsyncBaseTransport:
    """Test AsyncBaseTransport functionality."""

    @httpx_compatibility_test
    def test_async_base_transport_creation(self, client_factory):
        """Test AsyncBaseTransport can be created and has correct methods."""
        if client_factory.client_type == "httpx":
            import httpx

            transport = httpx.AsyncBaseTransport()
        else:
            import faster_http

            transport = faster_http.AsyncBaseTransport()

        # Test basic creation
        assert transport is not None

        # Test required methods exist
        assert hasattr(transport, "aclose")
        assert hasattr(transport, "handle_async_request")

    @httpx_compatibility_test
    def test_async_base_transport_methods_signature(self, client_factory):
        """Test AsyncBaseTransport methods have correct signatures."""
        if client_factory.client_type == "httpx":
            import httpx

            transport = httpx.AsyncBaseTransport()
        else:
            import faster_http

            transport = faster_http.AsyncBaseTransport()

        # Test aclose signature (should be async)
        aclose_method = transport.aclose
        assert callable(aclose_method)

        # Test handle_async_request signature (should be async)
        handle_method = transport.handle_async_request
        assert callable(handle_method)

    @pytest.mark.asyncio
    @httpx_compatibility_test
    async def test_async_base_transport_aclose(self, client_factory):
        """Test AsyncBaseTransport.aclose() method works."""
        if client_factory.client_type == "httpx":
            import httpx

            transport = httpx.AsyncBaseTransport()
        else:
            import faster_http

            transport = faster_http.AsyncBaseTransport()

        # aclose should not raise an error and should be awaitable
        try:
            await transport.aclose()
        except Exception as e:
            # For faster-http, we might have a different implementation
            # The important thing is that the method exists and is callable
            raise AssertionError(f"aclose() should not raise an error: {e}")

    @pytest.mark.asyncio
    @httpx_compatibility_test
    async def test_async_base_transport_handle_request_raises(self, client_factory):
        """Test AsyncBaseTransport.handle_async_request() raises NotImplementedError."""
        if client_factory.client_type == "httpx":
            import httpx

            transport = httpx.AsyncBaseTransport()
        else:
            import faster_http

            transport = faster_http.AsyncBaseTransport()

        # Create a mock request object
        class MockRequest:
            pass

        request = MockRequest()

        # handle_async_request should raise NotImplementedError
        with pytest.raises(NotImplementedError):
            await transport.handle_async_request(request)


class TestMainFunction:
    """Test main function functionality."""

    @httpx_compatibility_test
    def test_main_function_exists(self, client_factory):
        """Test main function exists and can be called."""
        if client_factory.client_type == "httpx":
            import httpx

            main_func = httpx.main
        else:
            import faster_http

            main_func = faster_http.main

        # Test function exists
        assert main_func is not None
        assert callable(main_func)

    @httpx_compatibility_test
    def test_main_function_signature(self, client_factory):
        """Test main function has correct signature."""
        if client_factory.client_type == "httpx":
            import httpx

            main_func = httpx.main
        else:
            import faster_http

            main_func = faster_http.main

        import inspect

        # Test signature - should accept no arguments
        sig = inspect.signature(main_func)
        assert len(sig.parameters) == 0

    @httpx_compatibility_test
    def test_main_function_call(self, client_factory):
        """Test main function can be called without errors."""
        if client_factory.client_type == "httpx":
            import httpx

            main_func = httpx.main
        else:
            import faster_http

            main_func = faster_http.main

        # Test function call - should not raise an error
        try:
            result = main_func()
            # Result should be None for httpx, and our implementation should match
            assert result is None
        except Exception as e:
            raise AssertionError(f"main() should not raise an error: {e}")


class TestInterfaceCompatibility:
    """Test compatibility between httpx and faster-http interfaces."""

    @httpx_compatibility_test
    def test_all_interfaces_exist_in_all_list(self, client_factory):
        """Test all new interfaces are properly exported in __all__."""
        if client_factory.client_type == "httpx":
            import httpx as module
        else:
            import faster_http as module

        # Test that all new interfaces are in __all__
        all_exports = getattr(module, "__all__", [])

        required_interfaces = ["AsyncBaseTransport", "Auth", "main"]

        for interface in required_interfaces:
            assert interface in all_exports, f"{interface} should be in __all__"
            assert hasattr(module, interface), f"{interface} should be importable"

    @httpx_compatibility_test
    def test_interface_string_representations(self, client_factory):
        """Test string representations of new interfaces."""
        if client_factory.client_type == "httpx":
            import httpx

            transport = httpx.AsyncBaseTransport()
            auth = httpx.Auth()
        else:
            import faster_http

            transport = faster_http.AsyncBaseTransport()
            auth = faster_http.Auth()

        # Test string representations exist and don't raise errors
        transport_repr = repr(transport)
        assert isinstance(transport_repr, str)
        assert len(transport_repr) > 0

        auth_repr = repr(auth)
        assert isinstance(auth_repr, str)
        assert len(auth_repr) > 0
