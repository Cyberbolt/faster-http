"""
Complete streaming functionality tests for faster_http.

Tests all streaming capabilities:
- Top-level stream() function
- Client.stream() method
- AsyncClient.stream() method
- Response streaming iterators
- Context manager protocol
- httpx compatibility
"""

import pytest

import faster_http


class TestStreamingBasics:
    """Test basic streaming functionality."""

    @pytest.fixture(autouse=True)
    def setup(self, test_server):
        """Setup test server URL for each test."""
        self.base_url = test_server.base_url

    def test_top_level_stream_function_exists(self):
        """Test that the top-level stream function exists and is callable."""
        assert hasattr(faster_http, "stream")
        assert callable(faster_http.stream)

    def test_client_stream_method_exists(self):
        """Test that Client.stream method exists."""
        client = faster_http.Client()
        assert hasattr(client, "stream")
        assert callable(client.stream)
        client.close()

    def test_async_client_stream_method_exists(self):
        """Test that AsyncClient.stream method exists."""
        client = faster_http.AsyncClient()
        assert hasattr(client, "stream")
        assert callable(client.stream)

    def test_stream_response_type(self):
        """Test that stream functions return the correct type."""
        url = f"{self.base_url}/json"

        # Test top-level stream function
        with faster_http.stream("GET", url) as response:
            # Should return StreamingClient, not regular Response
            assert type(response).__name__ == "StreamingClient"
            assert hasattr(response, "iter_bytes")
            assert hasattr(response, "iter_lines")
            assert hasattr(response, "status_code")


class TestStreamingContextManager:
    """Test streaming context manager protocol."""

    @pytest.fixture(autouse=True)
    def setup(self, test_server):
        """Setup test server URL for each test."""
        self.base_url = test_server.base_url

    def test_stream_context_manager(self):
        """Test that streaming responses work as context managers."""
        url = f"{self.base_url}/json"

        with faster_http.stream("GET", url) as response:
            assert response.status_code == 200
            assert response.is_ready
            assert not response.is_closed

        # After exiting context, should be closed
        assert response.is_closed

    def test_client_stream_context_manager(self):
        """Test Client.stream context manager."""
        url = f"{self.base_url}/json"

        with faster_http.Client() as client:
            with client.stream("GET", url, timeout=10.0) as response:
                assert response.status_code == 200
                assert response.is_ready

            assert response.is_closed

    def test_stream_early_close(self):
        """Test manually closing streaming response."""
        url = f"{self.base_url}/json"

        with faster_http.stream("GET", url) as response:
            assert not response.is_closed
            response.close()
            assert response.is_closed


class TestStreamingIterators:
    """Test streaming iterator methods."""

    @pytest.fixture(autouse=True)
    def setup(self, test_server):
        """Setup test server URL for each test."""
        self.base_url = test_server.base_url

    def test_iter_bytes(self):
        """Test iter_bytes streaming iterator."""
        url = f"{self.base_url}/json"

        with faster_http.stream("GET", url) as response:
            chunks = []
            total_bytes = 0

            for chunk in response.iter_bytes(chunk_size=10):
                chunks.append(chunk)
                total_bytes += len(chunk)
                if len(chunks) >= 5:  # Limit to first 5 chunks
                    break

            assert len(chunks) > 0
            assert all(isinstance(chunk, bytes) for chunk in chunks)
            assert total_bytes > 0

    def test_iter_text(self):
        """Test iter_text streaming iterator."""
        url = f"{self.base_url}/json"

        with faster_http.stream("GET", url) as response:
            text_chunks = []

            for chunk in response.iter_text(chunk_size=20):
                text_chunks.append(chunk)
                if len(text_chunks) >= 3:  # Limit to first 3 chunks
                    break

            assert len(text_chunks) > 0
            assert all(isinstance(chunk, str) for chunk in text_chunks)

    def test_iter_lines(self):
        """Test iter_lines streaming iterator."""
        # Use the get endpoint which should return some content we can split into lines
        url = f"{self.base_url}/get"

        with faster_http.stream("GET", url) as response:
            lines = []

            for line in response.iter_lines():
                lines.append(line)

            assert len(lines) > 0
            assert all(isinstance(line, str) for line in lines)

    def test_iter_raw(self):
        """Test iter_raw streaming iterator."""
        url = f"{self.base_url}/json"

        with faster_http.stream("GET", url) as response:
            raw_chunks = []

            for chunk in response.iter_raw(chunk_size=15):
                raw_chunks.append(chunk)
                if len(raw_chunks) >= 4:  # Limit to first 4 chunks
                    break

            assert len(raw_chunks) > 0
            assert all(isinstance(chunk, bytes) for chunk in raw_chunks)


class TestStreamingHttpxCompatibility:
    """Test streaming compatibility with httpx behavior."""

    @pytest.fixture(autouse=True)
    def setup(self, test_server):
        """Setup test server URL for each test."""
        self.base_url = test_server.base_url

    def test_stream_function_signature_compatibility(self):
        """Test that stream function accepts httpx-compatible parameters."""
        url = f"{self.base_url}/json"

        # Test with httpx-style parameters
        with faster_http.stream(
            "GET", url, headers={"User-Agent": "test"}, timeout=10.0, follow_redirects=True
        ) as response:
            assert response.status_code == 200

    def test_response_properties_compatibility(self):
        """Test that streaming response has httpx-compatible properties."""
        url = f"{self.base_url}/json"

        with faster_http.stream("GET", url) as response:
            # Basic properties
            assert hasattr(response, "status_code")
            assert hasattr(response, "headers")
            assert hasattr(response, "url_obj")
            assert hasattr(response, "elapsed")
            assert hasattr(response, "is_success")

            # Check property values
            assert isinstance(response.status_code, int)
            assert response.status_code == 200
            assert response.is_success

    def test_streaming_vs_regular_response(self):
        """Compare streaming response with regular response properties."""
        url = f"{self.base_url}/json"

        # Regular response
        regular_response = faster_http.get(url)

        # Streaming response
        with faster_http.stream("GET", url) as stream_response:
            # Both should have similar basic properties
            assert regular_response.status_code == stream_response.status_code
            assert regular_response.is_success == stream_response.is_success


class TestStreamingErrorHandling:
    """Test error handling in streaming operations."""

    @pytest.fixture(autouse=True)
    def setup(self, test_server):
        """Setup test server URL for each test."""
        self.base_url = test_server.base_url

    def test_stream_closed_error(self):
        """Test error when trying to use closed streaming response."""
        url = f"{self.base_url}/json"

        response = None
        with faster_http.stream("GET", url) as resp:
            response = resp
            assert not response.is_closed

        # Now response should be closed
        assert response.is_closed

        # Should get error trying to iterate
        with pytest.raises((RuntimeError, faster_http.StreamError)):
            list(response.iter_bytes())

    def test_stream_invalid_url(self):
        """Test streaming with invalid URL."""
        with pytest.raises((faster_http.NetworkError, faster_http.ConnectError)):
            with faster_http.stream("GET", "http://invalid-domain-12345.com") as response:
                list(response.iter_bytes())

    def test_stream_network_error_handling(self):
        """Test handling of network errors during streaming."""
        # Test with a URL that will cause connection issues
        with pytest.raises((faster_http.NetworkError, faster_http.ConnectError)):
            with faster_http.stream("GET", "http://127.0.0.1:99999") as response:
                list(response.iter_lines())


class TestStreamingMemoryEfficiency:
    """Test memory efficiency of streaming operations."""

    @pytest.fixture(autouse=True)
    def setup(self, test_server):
        """Setup test server URL for each test."""
        self.base_url = test_server.base_url

    def test_chunk_size_control(self):
        """Test that streaming respects chunk size settings."""
        url = f"{self.base_url}/json"

        with faster_http.stream("GET", url) as response:
            chunk_count = 0
            max_chunk_size = 0

            for chunk in response.iter_bytes(chunk_size=50):
                chunk_count += 1
                max_chunk_size = max(max_chunk_size, len(chunk))

                # Memory efficiency check - chunks should be reasonably small
                assert len(chunk) <= 100  # Allow some overhead

                if chunk_count >= 5:  # Test first 5 chunks
                    break

            assert chunk_count >= 1
            assert max_chunk_size <= 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
