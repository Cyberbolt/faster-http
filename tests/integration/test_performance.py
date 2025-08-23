"""Performance comparison tests between faster-http and httpx."""

import asyncio
from concurrent.futures import ThreadPoolExecutor
import time

import pytest


class TestPerformance:
    """Performance comparison tests."""

    @pytest.fixture(autouse=True)
    def setup(self, test_server):
        """Setup for each test."""
        self.base_url = test_server.base_url

    def test_sync_request_performance(self, benchmark):
        """Benchmark sync request performance."""
        # TDD: Red phase - this will fail initially
        import faster_http

        def make_request():
            response = faster_http.get(f"{self.base_url}/get")
            return response.status_code

        result = benchmark(make_request)
        assert result == 200

    def test_sync_client_performance(self, benchmark):
        """Benchmark sync client performance."""
        # TDD: Red phase - this will fail initially
        import faster_http

        def make_request_with_client():
            with faster_http.Client() as client:
                response = client.get(f"{self.base_url}/get")
                return response.status_code

        result = benchmark(make_request_with_client)
        assert result == 200

    @pytest.mark.asyncio
    async def test_async_request_performance(self, benchmark):
        """Benchmark async request performance."""
        # TDD: Red phase - this will fail initially
        import faster_http

        async def make_async_request():
            async with faster_http.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/get")
                return response.status_code

        result = await benchmark(make_async_request)
        assert result == 200

    def test_concurrent_requests_performance(self):
        """Test performance under concurrent load."""
        # TDD: Red phase - this will fail initially
        import faster_http

        num_requests = 100
        num_threads = 10

        def make_request():
            response = faster_http.get(f"{self.base_url}/get")
            return response.status_code == 200

        start_time = time.time()

        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(make_request) for _ in range(num_requests)]
            results = [future.result() for future in futures]

        end_time = time.time()
        duration = end_time - start_time

        # All requests should succeed
        assert all(results)

        # Performance assertion - should complete within reasonable time
        assert duration < 30.0  # 100 requests in under 30 seconds

        # Calculate requests per second
        rps = num_requests / duration
        print(f"Requests per second: {rps:.2f}")

    @pytest.mark.asyncio
    async def test_async_concurrent_performance(self):
        """Test async performance under concurrent load."""
        # TDD: Red phase - this will fail initially
        import faster_http

        num_requests = 100

        async def make_request(client):
            response = await client.get(f"{self.base_url}/get")
            return response.status_code == 200

        start_time = time.time()

        async with faster_http.AsyncClient() as client:
            tasks = [make_request(client) for _ in range(num_requests)]
            results = await asyncio.gather(*tasks)

        end_time = time.time()
        duration = end_time - start_time

        # All requests should succeed
        assert all(results)

        # Performance assertion - async should be faster
        assert duration < 15.0  # 100 async requests in under 15 seconds

        # Calculate requests per second
        rps = num_requests / duration
        print(f"Async requests per second: {rps:.2f}")

    def test_memory_efficiency(self):
        """Test memory usage efficiency."""
        # TDD: Red phase - this will fail initially
        import gc
        import os

        import psutil

        import faster_http

        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        # Make many requests
        responses = []
        for _ in range(1000):
            response = faster_http.get(f"{self.base_url}/get")
            responses.append(response.text)

        # Force garbage collection
        del responses
        gc.collect()

        # Check final memory usage
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory

        # Memory increase should be reasonable (less than 100MB for 1000 requests)
        assert memory_increase < 100 * 1024 * 1024

    def test_json_parsing_performance(self, benchmark):
        """Benchmark JSON parsing performance."""
        # TDD: Red phase - this will fail initially
        import faster_http

        def parse_json_response():
            response = faster_http.get(f"{self.base_url}/json")
            return response.json()

        result = benchmark(parse_json_response)
        assert isinstance(result, dict)

    def test_large_response_performance(self):
        """Test performance with large responses."""
        # TDD: Red phase - this will fail initially
        import faster_http

        # Request large amount of data (1MB)
        start_time = time.time()
        response = faster_http.get(f"{self.base_url}/bytes/1048576")  # 1MB
        content = response.content
        end_time = time.time()

        assert len(content) == 1048576
        assert end_time - start_time < 10.0  # Should download 1MB in under 10 seconds
