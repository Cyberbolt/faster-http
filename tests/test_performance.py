"""
Performance comparison tests between faster_http, httpx, and requests.
"""

import pytest
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed

# Import the libraries to compare
import faster_http
try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


class TestPerformanceComparison:
    """Performance comparison tests."""
    
    def test_single_request_performance(self):
        """Compare single request performance."""
        url = "https://httpbin.org/get"
        
        # Test faster_http
        start_time = time.time()
        response = faster_http.get(url)
        faster_http_time = time.time() - start_time
        assert response.status_code == 200
        
        if HTTPX_AVAILABLE:
            # Test httpx
            start_time = time.time()
            response = httpx.get(url)
            httpx_time = time.time() - start_time
            assert response.status_code == 200
            
            print(f"Single request - faster_http: {faster_http_time:.4f}s, httpx: {httpx_time:.4f}s")
            print(f"Speedup: {httpx_time / faster_http_time:.2f}x")
        
        if REQUESTS_AVAILABLE:
            # Test requests
            start_time = time.time()
            response = requests.get(url)
            requests_time = time.time() - start_time
            assert response.status_code == 200
            
            print(f"Single request - faster_http: {faster_http_time:.4f}s, requests: {requests_time:.4f}s")
            print(f"Speedup vs requests: {requests_time / faster_http_time:.2f}x")
    
    def test_multiple_requests_sync(self):
        """Compare multiple synchronous requests."""
        url = "https://httpbin.org/get"
        num_requests = 10
        
        # Test faster_http
        start_time = time.time()
        with faster_http.Client() as client:
            for _ in range(num_requests):
                response = client.get(url)
                assert response.status_code == 200
        faster_http_time = time.time() - start_time
        
        if HTTPX_AVAILABLE:
            # Test httpx
            start_time = time.time()
            with httpx.Client() as client:
                for _ in range(num_requests):
                    response = client.get(url)
                    assert response.status_code == 200
            httpx_time = time.time() - start_time
            
            print(f"{num_requests} sync requests - faster_http: {faster_http_time:.4f}s, httpx: {httpx_time:.4f}s")
            print(f"Speedup: {httpx_time / faster_http_time:.2f}x")
        
        if REQUESTS_AVAILABLE:
            # Test requests
            start_time = time.time()
            with requests.Session() as session:
                for _ in range(num_requests):
                    response = session.get(url)
                    assert response.status_code == 200
            requests_time = time.time() - start_time
            
            print(f"{num_requests} sync requests - faster_http: {faster_http_time:.4f}s, requests: {requests_time:.4f}s")
            print(f"Speedup vs requests: {requests_time / faster_http_time:.2f}x")
    
    @pytest.mark.asyncio
    async def test_multiple_requests_async(self):
        """Compare multiple asynchronous requests."""
        url = "https://httpbin.org/get"
        num_requests = 10
        
        # Test faster_http async
        start_time = time.time()
        async with faster_http.AsyncClient() as client:
            tasks = [client.get(url) for _ in range(num_requests)]
            responses = await asyncio.gather(*tasks)
            for response in responses:
                assert response.status_code == 200
        faster_http_time = time.time() - start_time
        
        if HTTPX_AVAILABLE:
            # Test httpx async
            start_time = time.time()
            async with httpx.AsyncClient() as client:
                tasks = [client.get(url) for _ in range(num_requests)]
                responses = await asyncio.gather(*tasks)
                for response in responses:
                    assert response.status_code == 200
            httpx_time = time.time() - start_time
            
            print(f"{num_requests} async requests - faster_http: {faster_http_time:.4f}s, httpx: {httpx_time:.4f}s")
            print(f"Speedup: {httpx_time / faster_http_time:.2f}x")
    
    def test_concurrent_requests_threading(self):
        """Compare concurrent requests using threading."""
        url = "https://httpbin.org/get"
        num_requests = 20
        max_workers = 5
        
        def make_faster_http_request():
            response = faster_http.get(url)
            assert response.status_code == 200
            return response
        
        # Test faster_http with threading
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(make_faster_http_request) for _ in range(num_requests)]
            for future in as_completed(futures):
                future.result()
        faster_http_time = time.time() - start_time
        
        if REQUESTS_AVAILABLE:
            def make_requests_request():
                response = requests.get(url)
                assert response.status_code == 200
                return response
            
            # Test requests with threading
            start_time = time.time()
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = [executor.submit(make_requests_request) for _ in range(num_requests)]
                for future in as_completed(futures):
                    future.result()
            requests_time = time.time() - start_time
            
            print(f"{num_requests} concurrent requests - faster_http: {faster_http_time:.4f}s, requests: {requests_time:.4f}s")
            print(f"Speedup vs requests: {requests_time / faster_http_time:.2f}x")
    
    def test_json_parsing_performance(self):
        """Compare JSON parsing performance."""
        url = "https://httpbin.org/json"
        num_requests = 5
        
        # Test faster_http JSON parsing
        start_time = time.time()
        for _ in range(num_requests):
            response = faster_http.get(url)
            data = response.json()
            assert isinstance(data, dict)
        faster_http_time = time.time() - start_time
        
        if HTTPX_AVAILABLE:
            # Test httpx JSON parsing
            start_time = time.time()
            for _ in range(num_requests):
                response = httpx.get(url)
                data = response.json()
                assert isinstance(data, dict)
            httpx_time = time.time() - start_time
            
            print(f"JSON parsing {num_requests} requests - faster_http: {faster_http_time:.4f}s, httpx: {httpx_time:.4f}s")
            print(f"Speedup: {httpx_time / faster_http_time:.2f}x")
    
    def test_post_json_performance(self):
        """Compare POST JSON performance."""
        url = "https://httpbin.org/post"
        json_data = {"test": "data", "number": 42, "nested": {"key": "value"}}
        num_requests = 5
        
        # Test faster_http POST JSON
        start_time = time.time()
        for _ in range(num_requests):
            response = faster_http.post(url, json=json_data)
            assert response.status_code == 200
            data = response.json()
            assert data["json"] == json_data
        faster_http_time = time.time() - start_time
        
        if HTTPX_AVAILABLE:
            # Test httpx POST JSON
            start_time = time.time()
            for _ in range(num_requests):
                response = httpx.post(url, json=json_data)
                assert response.status_code == 200
                data = response.json()
                assert data["json"] == json_data
            httpx_time = time.time() - start_time
            
            print(f"POST JSON {num_requests} requests - faster_http: {faster_http_time:.4f}s, httpx: {httpx_time:.4f}s")
            print(f"Speedup: {httpx_time / faster_http_time:.2f}x")


@pytest.mark.benchmark
class TestBenchmarks:
    """Benchmark tests for performance measurement."""
    
    def test_benchmark_get_request(self, benchmark):
        """Benchmark a single GET request."""
        def make_request():
            response = faster_http.get("https://httpbin.org/get")
            assert response.status_code == 200
            return response
        
        result = benchmark(make_request)
        assert result.status_code == 200
    
    def test_benchmark_post_json(self, benchmark):
        """Benchmark a POST request with JSON."""
        json_data = {"benchmark": "test", "value": 123}
        
        def make_request():
            response = faster_http.post("https://httpbin.org/post", json=json_data)
            assert response.status_code == 200
            return response
        
        result = benchmark(make_request)
        assert result.status_code == 200
    
    def test_benchmark_client_reuse(self, benchmark):
        """Benchmark client reuse."""
        client = faster_http.Client()
        
        def make_request():
            response = client.get("https://httpbin.org/get")
            assert response.status_code == 200
            return response
        
        result = benchmark(make_request)
        assert result.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"]) 