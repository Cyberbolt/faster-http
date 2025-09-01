"""Tests for medium priority features that have been implemented."""

import types

import pytest

import faster_http as http
from tests.utils.httpx_comparison import httpx_compatibility_test


class TestRequestObjectFeatures:
    """Test complete Request object functionality."""

    @pytest.fixture(autouse=True)
    def setup(self, test_server):
        """Setup for each test."""
        self.base_url = test_server.base_url

    @httpx_compatibility_test
    def test_request_object_complete_attributes(self, client_factory):
        """Test all Request object attributes are properly implemented."""
        with client_factory() as client:
            # Test all major Request attributes
            request = client.build_request(
                "POST",
                f"{self.base_url}/post",
                json={"test": "data"},
                headers={"Custom-Header": "value"},
                params={"param": "value"},
            )

            # Basic properties
            assert request.method == "POST"
            assert isinstance(request.url, str | object)  # URL object
            assert hasattr(request, "headers")
            assert hasattr(request, "content")
            assert hasattr(request, "stream")
            assert hasattr(request, "extensions")

            # Methods
            assert hasattr(request, "read")
            assert hasattr(request, "aread")

            # Verify content is accessible
            content = request.read()
            assert isinstance(content, bytes)
            assert b"test" in content

    @httpx_compatibility_test
    @pytest.mark.asyncio
    async def test_request_object_async_methods(self, async_client_factory):
        """Test Request object async methods."""
        async with async_client_factory() as client:
            request = client.build_request("GET", f"{self.base_url}/get")

            # Test async read method
            content = await request.aread()
            assert isinstance(content, bytes)


class TestClientExtendedMethods:
    """Test Client.build_request() and send() methods."""

    @pytest.fixture(autouse=True)
    def setup(self, test_server):
        """Setup for each test."""
        self.base_url = test_server.base_url

    @httpx_compatibility_test
    def test_client_build_request_method(self, client_factory):
        """Test Client.build_request() method works correctly."""
        with client_factory() as client:
            request = client.build_request(
                "POST", f"{self.base_url}/post", json={"key": "value"}, headers={"X-Test": "header"}
            )

            # Verify request object is properly built
            assert request.method == "POST"
            assert "X-Test" in request.headers
            assert request.headers["X-Test"] == "header"
            assert b"key" in request.read()

    @httpx_compatibility_test
    def test_client_send_method(self, client_factory):
        """Test Client.send() method works correctly."""
        with client_factory() as client:
            # Build a request
            request = client.build_request("GET", f"{self.base_url}/json")

            # Send the pre-built request
            response = client.send(request)

            # Verify response
            assert response.status_code == 200
            assert response.headers.get("Content-Type") == "application/json"

            # Verify JSON content
            json_data = response.json()
            assert isinstance(json_data, dict)

    @httpx_compatibility_test
    @pytest.mark.asyncio
    async def test_async_client_build_and_send(self, async_client_factory):
        """Test AsyncClient.build_request() and send() methods."""
        async with async_client_factory() as client:
            # Build a request
            request = client.build_request("POST", f"{self.base_url}/post", json={"async": True})

            # Verify request properties
            assert request.method == "POST"
            assert b"async" in request.read()

            # Send the request
            response = await client.send(request)

            # Verify response
            assert response.status_code == 200


class TestResponseStreamingMethods:
    """Test Response streaming methods return correct types."""

    @pytest.fixture(autouse=True)
    def setup(self, test_server):
        """Setup for each test."""
        self.base_url = test_server.base_url

    @httpx_compatibility_test
    def test_sync_streaming_methods_return_generators(self, client_factory):
        """Test sync streaming methods return generators."""
        with client_factory() as client:
            response = client.get(f"{self.base_url}/json")

            # Test iter_bytes returns generator
            iter_bytes_result = response.iter_bytes()
            assert isinstance(iter_bytes_result, types.GeneratorType)
            assert hasattr(iter_bytes_result, "__iter__")
            assert hasattr(iter_bytes_result, "__next__")

            # Test iter_text returns generator
            iter_text_result = response.iter_text()
            assert isinstance(iter_text_result, types.GeneratorType)

            # Test iter_lines returns generator
            iter_lines_result = response.iter_lines()
            assert isinstance(iter_lines_result, types.GeneratorType)

            # Test iter_raw returns generator
            iter_raw_result = response.iter_raw()
            assert isinstance(iter_raw_result, types.GeneratorType)

    @httpx_compatibility_test
    @pytest.mark.asyncio
    async def test_async_streaming_methods_return_async_generators(self, async_client_factory):
        """Test async streaming methods return async generators."""
        async with async_client_factory() as client:
            response = await client.get(f"{self.base_url}/json")

            # Test aiter_bytes returns async generator
            aiter_bytes_result = response.aiter_bytes()
            assert isinstance(aiter_bytes_result, types.AsyncGeneratorType)
            assert hasattr(aiter_bytes_result, "__aiter__")
            assert hasattr(aiter_bytes_result, "__anext__")

            # Test aiter_text returns async generator
            aiter_text_result = response.aiter_text()
            assert isinstance(aiter_text_result, types.AsyncGeneratorType)

            # Test aiter_lines returns async generator
            aiter_lines_result = response.aiter_lines()
            assert isinstance(aiter_lines_result, types.AsyncGeneratorType)

            # Test aiter_raw returns async generator
            aiter_raw_result = response.aiter_raw()
            assert isinstance(aiter_raw_result, types.AsyncGeneratorType)

    @httpx_compatibility_test
    def test_streaming_methods_iteration_works(self, client_factory):
        """Test streaming methods can be iterated over."""
        with client_factory() as client:
            response = client.get(f"{self.base_url}/json")

            # Test iter_bytes iteration
            bytes_chunks = list(response.iter_bytes(chunk_size=50))
            assert len(bytes_chunks) > 0
            assert all(isinstance(chunk, bytes) for chunk in bytes_chunks)

            # Test iter_text iteration
            text_chunks = list(response.iter_text(chunk_size=20))
            assert len(text_chunks) > 0
            assert all(isinstance(chunk, str) for chunk in text_chunks)

            # Test iter_lines iteration
            lines = list(response.iter_lines())
            assert len(lines) > 0
            assert all(isinstance(line, str) for line in lines)

    @httpx_compatibility_test
    @pytest.mark.asyncio
    async def test_async_streaming_methods_iteration_works(self, async_client_factory):
        """Test async streaming methods can be iterated over."""
        async with async_client_factory() as client:
            response = await client.get(f"{self.base_url}/json")

            # Test aiter_bytes iteration
            bytes_chunks = []
            async for chunk in response.aiter_bytes(chunk_size=50):
                bytes_chunks.append(chunk)
                if len(bytes_chunks) >= 3:  # Limit for test
                    break

            assert len(bytes_chunks) > 0
            assert all(isinstance(chunk, bytes) for chunk in bytes_chunks)


class TestConfigurationClasses:
    """Test Timeout and Limits configuration classes."""

    def test_timeout_class_functionality(self):
        """Test Timeout class works correctly."""
        # Test basic timeout creation
        timeout = http.Timeout(5.0)
        assert timeout is not None

        # Test timeout with individual settings
        timeout = http.Timeout(connect=5.0, read=10.0, write=15.0, pool=20.0)
        assert timeout.connect == 5.0
        assert timeout.read == 10.0
        assert timeout.write == 15.0
        assert timeout.pool == 20.0

    def test_limits_class_functionality(self):
        """Test Limits class works correctly."""
        # Test basic limits creation
        limits = http.Limits()
        assert limits is not None

        # Test limits with parameters
        limits = http.Limits(max_connections=100, max_keepalive_connections=20)
        assert limits.max_connections == 100
        assert limits.max_keepalive_connections == 20
        assert hasattr(limits, "keepalive_expiry")


class TestResponseReadMethods:
    """Test Response read() and aread() methods."""

    @pytest.fixture(autouse=True)
    def setup(self, test_server):
        """Setup for each test."""
        self.base_url = test_server.base_url

    @httpx_compatibility_test
    def test_response_read_method(self, client_factory):
        """Test Response.read() method."""
        with client_factory() as client:
            response = client.get(f"{self.base_url}/json")

            # Test read method returns bytes
            content = response.read()
            assert isinstance(content, bytes)
            assert len(content) > 0

            # Should be able to call read multiple times
            content2 = response.read()
            assert content == content2

    @httpx_compatibility_test
    @pytest.mark.asyncio
    async def test_response_aread_method(self, async_client_factory):
        """Test Response.aread() method."""
        async with async_client_factory() as client:
            response = await client.get(f"{self.base_url}/json")

            # Test aread method returns bytes
            content = await response.aread()
            assert isinstance(content, bytes)
            assert len(content) > 0

            # Should be able to call aread multiple times
            content2 = await response.aread()
            assert content == content2


class TestIntegratedWorkflow:
    """Test integrated workflow using medium priority features."""

    @pytest.fixture(autouse=True)
    def setup(self, test_server):
        """Setup for each test."""
        self.base_url = test_server.base_url

    @httpx_compatibility_test
    def test_complete_request_response_workflow(self, client_factory):
        """Test complete workflow using all medium priority features."""
        with client_factory() as client:
            # 1. Build a complex request
            request = client.build_request(
                "POST",
                f"{self.base_url}/post",
                json={"workflow": "test", "features": ["request", "streaming", "config"]},
                headers={"X-Workflow": "medium-priority"},
                params={"test": "complete"},
            )

            # 2. Verify request properties
            assert request.method == "POST"
            assert "X-Workflow" in request.headers
            content = request.read()
            assert b"workflow" in content

            # 3. Send the request
            response = client.send(request)
            assert response.status_code == 200

            # 4. Use streaming to read response
            chunks = []
            for chunk in response.iter_bytes(chunk_size=100):
                chunks.append(chunk)
                if len(chunks) >= 5:  # Limit for test
                    break

            assert len(chunks) > 0
            assert all(isinstance(chunk, bytes) for chunk in chunks)

            # 5. Read full response content
            full_content = response.read()
            assert isinstance(full_content, bytes)
            assert len(full_content) > 0

    @httpx_compatibility_test
    @pytest.mark.asyncio
    async def test_complete_async_workflow(self, async_client_factory):
        """Test complete async workflow."""
        async with async_client_factory() as client:
            # 1. Build request
            request = client.build_request("GET", f"{self.base_url}/json", headers={"X-Async": "true"})

            # 2. Send request
            response = await client.send(request)
            assert response.status_code == 200

            # 3. Use async streaming
            chunks = []
            async for chunk in response.aiter_text(chunk_size=50):
                chunks.append(chunk)
                if len(chunks) >= 3:  # Limit for test
                    break

            assert len(chunks) > 0
            assert all(isinstance(chunk, str) for chunk in chunks)

            # 4. Async read
            content = await response.aread()
            assert isinstance(content, bytes)
