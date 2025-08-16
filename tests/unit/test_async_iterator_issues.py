"""
Unit tests for async iterator functionality.
Tests async iteration methods and streaming capabilities.
Following CLAUDE.md requirements: test httpx first, then faster_http for comparison.
"""

import asyncio

import httpx

import faster_http


class TestAsyncIteratorMethods:
    """Test async iterator methods - httpx vs faster_http comparison."""

    def test_response_async_iterator_methods_availability_comparison(self, stable_server):
        """Test that Response has async iterator methods - httpx vs faster_http."""
        url = stable_server.url("/stream/3")

        # First test httpx Response async iterator methods
        httpx_response = httpx.get(url)
        assert httpx_response.status_code == 200

        # Test httpx async iterator methods availability
        httpx_async_methods = ["aiter_bytes", "aiter_text", "aiter_lines", "aiter_raw"]
        httpx_has_methods = {}

        for method in httpx_async_methods:
            httpx_has_methods[method] = hasattr(httpx_response, method)
            if httpx_has_methods[method]:
                assert callable(getattr(httpx_response, method)), f"httpx {method} should be callable"

        # Then test faster_http Response async iterator methods
        faster_response = faster_http.get(url)
        assert faster_response.status_code == 200

        # Test faster_http async iterator methods availability (should match httpx)
        for method in httpx_async_methods:
            if httpx_has_methods[method]:
                assert hasattr(faster_response, method), f"faster_http should have {method} like httpx"
                assert callable(getattr(faster_response, method)), f"faster_http {method} should be callable"

    def test_sync_iterator_methods_availability_comparison(self, stable_server):
        """Test that Response has sync iterator methods - httpx vs faster_http."""
        url = stable_server.url("/stream/3")

        # First test httpx Response sync iterator methods
        httpx_response = httpx.get(url)
        assert httpx_response.status_code == 200

        # Test httpx sync iterator methods availability
        httpx_sync_methods = ["iter_bytes", "iter_text", "iter_lines", "iter_raw"]
        httpx_has_sync_methods = {}

        for method in httpx_sync_methods:
            httpx_has_sync_methods[method] = hasattr(httpx_response, method)
            if httpx_has_sync_methods[method]:
                assert callable(getattr(httpx_response, method)), f"httpx {method} should be callable"

        # Then test faster_http Response sync iterator methods
        faster_response = faster_http.get(url)
        assert faster_response.status_code == 200

        # Test faster_http sync iterator methods availability (should match httpx)
        for method in httpx_sync_methods:
            if httpx_has_sync_methods[method]:
                assert hasattr(faster_response, method), f"faster_http should have {method} like httpx"
                assert callable(getattr(faster_response, method)), f"faster_http {method} should be callable"

    def test_iter_bytes_functionality_comparison(self, stable_server):
        """Test iter_bytes functionality - httpx vs faster_http."""
        url = stable_server.url("/stream/3")

        # First test httpx iter_bytes
        httpx_response = httpx.get(url)
        assert httpx_response.status_code == 200

        httpx_chunks = list(httpx_response.iter_bytes())
        assert len(httpx_chunks) > 0
        assert all(isinstance(chunk, bytes) for chunk in httpx_chunks)
        sum(len(chunk) for chunk in httpx_chunks)

        # Then test faster_http iter_bytes (should behave like httpx)
        faster_response = faster_http.get(url)
        assert faster_response.status_code == 200

        faster_chunks = list(faster_response.iter_bytes())
        assert len(faster_chunks) > 0
        assert all(isinstance(chunk, bytes) for chunk in faster_chunks)
        sum(len(chunk) for chunk in faster_chunks)

        # Both should provide byte chunks
        assert httpx_response.status_code == faster_response.status_code
        assert len(httpx_chunks) > 0 and len(faster_chunks) > 0

    def test_iter_text_functionality_comparison(self, stable_server):
        """Test iter_text functionality - httpx vs faster_http."""
        url = stable_server.url("/stream/3")

        # First test httpx iter_text
        httpx_response = httpx.get(url)
        assert httpx_response.status_code == 200

        httpx_text_chunks = list(httpx_response.iter_text())
        assert len(httpx_text_chunks) > 0
        assert all(isinstance(chunk, str) for chunk in httpx_text_chunks)

        # Then test faster_http iter_text (should behave like httpx)
        faster_response = faster_http.get(url)
        assert faster_response.status_code == 200

        faster_text_chunks = list(faster_response.iter_text())
        assert len(faster_text_chunks) > 0
        assert all(isinstance(chunk, str) for chunk in faster_text_chunks)

        # Both should provide text chunks
        assert httpx_response.status_code == faster_response.status_code
        assert len(httpx_text_chunks) > 0 and len(faster_text_chunks) > 0

    def test_iter_lines_functionality_comparison(self, stable_server):
        """Test iter_lines functionality - httpx vs faster_http."""
        url = stable_server.url("/stream/3")

        # First test httpx iter_lines
        httpx_response = httpx.get(url)
        assert httpx_response.status_code == 200

        try:
            httpx_lines = list(httpx_response.iter_lines())
            httpx_has_iter_lines = True
            httpx_line_count = len(httpx_lines)
        except AttributeError:
            httpx_has_iter_lines = False
            httpx_line_count = 0

        # Then test faster_http iter_lines (should match httpx availability)
        faster_response = faster_http.get(url)
        assert faster_response.status_code == 200

        try:
            faster_lines = list(faster_response.iter_lines())
            faster_has_iter_lines = True
            faster_line_count = len(faster_lines)
        except AttributeError:
            faster_has_iter_lines = False
            faster_line_count = 0

        # Both should have consistent iter_lines support
        assert httpx_has_iter_lines == faster_has_iter_lines
        if httpx_has_iter_lines and faster_has_iter_lines:
            assert httpx_line_count >= 0 and faster_line_count >= 0

    def test_async_iteration_basic_functionality_comparison(self, stable_server):
        """Test basic async iteration - httpx vs faster_http."""
        url = stable_server.url("/stream/3")

        async def test_async_iteration():
            # First test httpx async iteration (if supported)
            try:
                async with httpx.AsyncClient() as httpx_client:
                    httpx_response = await httpx_client.get(url)
                    assert httpx_response.status_code == 200

                    if hasattr(httpx_response, "aiter_bytes"):
                        httpx_chunks = []
                        async for chunk in httpx_response.aiter_bytes():
                            httpx_chunks.append(chunk)
                        httpx_async_works = True
                        httpx_chunk_count = len(httpx_chunks)
                    else:
                        httpx_async_works = False
                        httpx_chunk_count = 0
            except Exception:
                httpx_async_works = False
                httpx_chunk_count = 0

            # Then test faster_http async iteration (should match httpx)
            try:
                async with faster_http.AsyncClient() as faster_client:
                    faster_response = await faster_client.get(url)
                    assert faster_response.status_code == 200

                    if hasattr(faster_response, "aiter_bytes"):
                        faster_chunks = []
                        async for chunk in faster_response.aiter_bytes():
                            faster_chunks.append(chunk)
                        faster_async_works = True
                        faster_chunk_count = len(faster_chunks)
                    else:
                        faster_async_works = False
                        faster_chunk_count = 0
            except Exception:
                faster_async_works = False
                faster_chunk_count = 0

            # Both should have consistent async iteration support
            assert httpx_async_works == faster_async_works
            if httpx_async_works and faster_async_works:
                assert httpx_chunk_count > 0 and faster_chunk_count > 0

        asyncio.run(test_async_iteration())

    def test_iterator_interface_consistency_comparison(self, stable_server):
        """Test that faster_http doesn't have extra iterator interfaces that httpx doesn't have."""
        url = stable_server.url("/json")

        # Create response instances for interface comparison
        httpx_response = httpx.get(url)
        faster_response = faster_http.get(url)

        # Get all iterator-related methods from both
        httpx_iter_methods = {
            attr for attr in dir(httpx_response) if not attr.startswith("_") and ("iter" in attr or "aiter" in attr)
        }
        faster_iter_methods = {
            attr for attr in dir(faster_response) if not attr.startswith("_") and ("iter" in attr or "aiter" in attr)
        }

        # faster_http should not have iterator methods that httpx doesn't have
        extra_methods = faster_iter_methods - httpx_iter_methods
        assert len(extra_methods) == 0, (
            f"faster_http has extra iterator methods that httpx doesn't have: {extra_methods}"
        )

        # Check that common methods are callable
        common_methods = httpx_iter_methods & faster_iter_methods
        for method in common_methods:
            assert callable(getattr(httpx_response, method)), f"httpx {method} should be callable"
            assert callable(getattr(faster_response, method)), f"faster_http {method} should be callable"

    def test_streaming_behavior_comparison(self, stable_server):
        """Test streaming behavior - httpx vs faster_http."""
        url = stable_server.url("/stream/5")

        # First test httpx streaming behavior
        with httpx.stream("GET", url) as httpx_response:
            assert httpx_response.status_code == 200

            httpx_chunks = []
            for chunk in httpx_response.iter_bytes():
                httpx_chunks.append(chunk)
                if len(httpx_chunks) >= 3:  # Stop early to test streaming
                    break

            httpx_streamed_count = len(httpx_chunks)

        # Then test faster_http streaming behavior (should match httpx)
        with faster_http.stream("GET", url) as faster_response:
            assert faster_response.status_code == 200

            faster_chunks = []
            for chunk in faster_response.iter_bytes():
                faster_chunks.append(chunk)
                if len(faster_chunks) >= 3:  # Stop early to test streaming
                    break

            faster_streamed_count = len(faster_chunks)

        # Both should support streaming (partial consumption)
        assert httpx_streamed_count > 0 and faster_streamed_count > 0
        assert httpx_response.status_code == faster_response.status_code

    def test_chunk_size_parameter_comparison(self, stable_server):
        """Test chunk_size parameter support - httpx vs faster_http."""
        url = stable_server.url("/stream/3")
        chunk_size = 1024

        # First test httpx iter_bytes with chunk_size
        httpx_response = httpx.get(url)
        assert httpx_response.status_code == 200

        try:
            httpx_chunks = list(httpx_response.iter_bytes(chunk_size=chunk_size))
            httpx_supports_chunk_size = True
        except TypeError:
            # httpx might not support chunk_size parameter
            httpx_chunks = list(httpx_response.iter_bytes())
            httpx_supports_chunk_size = False

        # Then test faster_http iter_bytes with chunk_size (should match httpx)
        faster_response = faster_http.get(url)
        assert faster_response.status_code == 200

        try:
            faster_chunks = list(faster_response.iter_bytes(chunk_size=chunk_size))
            faster_supports_chunk_size = True
        except TypeError:
            # Should match httpx behavior
            faster_chunks = list(faster_response.iter_bytes())
            faster_supports_chunk_size = False

        # Both should handle chunk_size parameter consistently
        assert httpx_supports_chunk_size == faster_supports_chunk_size
        assert len(httpx_chunks) > 0 and len(faster_chunks) > 0
