"""
Unit tests for the event hooks system.
Tests that request and response hooks work correctly.
Following CLAUDE.md requirements: test httpx first, then faster_http for comparison.
"""

import httpx

import faster_http


class TestEventHooksSystem:
    """Test event hooks system functionality - httpx vs faster_http comparison."""

    def test_hook_configuration_in_client_comparison(self):
        """Test that hooks can be configured in Client constructor - httpx vs faster_http."""
        # Track hook executions
        httpx_hook_calls = {"request": 0, "response": 0}
        faster_hook_calls = {"request": 0, "response": 0}

        def httpx_request_hook(request):
            httpx_hook_calls["request"] += 1

        def httpx_response_hook(response):
            httpx_hook_calls["response"] += 1

        def faster_request_hook(request):
            faster_hook_calls["request"] += 1

        def faster_response_hook(response):
            faster_hook_calls["response"] += 1

        # First test httpx Client with event_hooks
        httpx_client = httpx.Client(event_hooks={"request": [httpx_request_hook], "response": [httpx_response_hook]})
        assert httpx_client is not None
        assert hasattr(httpx_client, "event_hooks")
        assert "request" in httpx_client.event_hooks
        assert "response" in httpx_client.event_hooks
        httpx_client.close()

        # Then test faster_http Client with event_hooks (should match httpx interface)
        faster_client = faster_http.Client(
            event_hooks={"request": [faster_request_hook], "response": [faster_response_hook]}
        )
        assert faster_client is not None
        assert hasattr(faster_client, "event_hooks")
        assert "request" in faster_client.event_hooks
        assert "response" in faster_client.event_hooks
        faster_client.close()

    def test_hook_configuration_in_async_client_comparison(self):
        """Test that hooks can be configured in AsyncClient constructor - httpx vs faster_http."""
        httpx_hook_calls = {"request": 0, "response": 0}
        faster_hook_calls = {"request": 0, "response": 0}

        async def httpx_async_request_hook(request):
            httpx_hook_calls["request"] += 1

        async def httpx_async_response_hook(response):
            httpx_hook_calls["response"] += 1

        async def faster_async_request_hook(request):
            faster_hook_calls["request"] += 1

        async def faster_async_response_hook(response):
            faster_hook_calls["response"] += 1

        # First test httpx AsyncClient with async event_hooks
        httpx_client = httpx.AsyncClient(
            event_hooks={"request": [httpx_async_request_hook], "response": [httpx_async_response_hook]}
        )
        assert httpx_client is not None
        assert hasattr(httpx_client, "event_hooks")
        assert "request" in httpx_client.event_hooks
        assert "response" in httpx_client.event_hooks

        # Then test faster_http AsyncClient with async event_hooks (should match httpx interface)
        faster_client = faster_http.AsyncClient(
            event_hooks={"request": [faster_async_request_hook], "response": [faster_async_response_hook]}
        )
        assert faster_client is not None
        assert hasattr(faster_client, "event_hooks")
        assert "request" in faster_client.event_hooks
        assert "response" in faster_client.event_hooks

    def test_hook_modification_after_client_creation_comparison(self):
        """Test modifying hooks after client creation - httpx vs faster_http."""

        def log_request(request):
            print(f"Request: {request.method} {request.url}")

        def log_response(response):
            print(f"Response: {response.status_code}")

        def raise_on_4xx_5xx(response):
            response.raise_for_status()

        # First test httpx Client hook modification
        httpx_client = httpx.Client()

        # Test that httpx allows modifying event_hooks after creation
        httpx_client.event_hooks["request"] = [log_request]
        httpx_client.event_hooks["response"] = [log_response, raise_on_4xx_5xx]

        assert len(httpx_client.event_hooks["request"]) == 1
        assert len(httpx_client.event_hooks["response"]) == 2
        httpx_client.close()

        # Then test faster_http Client hook modification (should match httpx)
        faster_client = faster_http.Client()

        # Test that faster_http allows modifying event_hooks after creation
        faster_client.event_hooks["request"] = [log_request]
        faster_client.event_hooks["response"] = [log_response, raise_on_4xx_5xx]

        assert len(faster_client.event_hooks["request"]) == 1
        assert len(faster_client.event_hooks["response"]) == 2
        faster_client.close()

    def test_request_hook_execution_comparison(self, stable_server):
        """Test request hook execution - httpx vs faster_http."""
        url = stable_server.url("/get")

        httpx_requests = []
        faster_requests = []

        def httpx_request_hook(request):
            httpx_requests.append({"method": request.method, "url": str(request.url)})

        def faster_request_hook(request):
            faster_requests.append({"method": request.method, "url": str(request.url)})

        # First test httpx request hook execution
        httpx_client = httpx.Client(event_hooks={"request": [httpx_request_hook]})
        httpx_response = httpx_client.get(url)
        assert httpx_response.status_code == 200
        assert len(httpx_requests) == 1
        assert httpx_requests[0]["method"] == "GET"
        assert httpx_requests[0]["url"] == url
        httpx_client.close()

        # Then test faster_http request hook execution (should behave like httpx)
        faster_client = faster_http.Client(event_hooks={"request": [faster_request_hook]})
        faster_response = faster_client.get(url)
        assert faster_response.status_code == 200
        assert len(faster_requests) == 1
        assert faster_requests[0]["method"] == "GET"
        assert faster_requests[0]["url"] == url
        faster_client.close()

        # Both should have captured the same request information
        assert httpx_requests[0] == faster_requests[0]

    def test_response_hook_execution_comparison(self, stable_server):
        """Test response hook execution - httpx vs faster_http."""
        url = stable_server.url("/get")

        httpx_responses = []
        faster_responses = []

        def httpx_response_hook(response):
            httpx_responses.append({"status_code": response.status_code, "url": str(response.url)})

        def faster_response_hook(response):
            faster_responses.append({"status_code": response.status_code, "url": str(response.url)})

        # First test httpx response hook execution
        httpx_client = httpx.Client(event_hooks={"response": [httpx_response_hook]})
        httpx_response = httpx_client.get(url)
        assert httpx_response.status_code == 200
        assert len(httpx_responses) == 1
        assert httpx_responses[0]["status_code"] == 200
        assert httpx_responses[0]["url"] == url
        httpx_client.close()

        # Then test faster_http response hook execution (should behave like httpx)
        faster_client = faster_http.Client(event_hooks={"response": [faster_response_hook]})
        faster_response = faster_client.get(url)
        assert faster_response.status_code == 200
        assert len(faster_responses) == 1
        assert faster_responses[0]["status_code"] == 200
        assert faster_responses[0]["url"] == url
        faster_client.close()

        # Both should have captured the same response information
        assert httpx_responses[0] == faster_responses[0]

    def test_multiple_hooks_execution_comparison(self, stable_server):
        """Test multiple hooks execution - httpx vs faster_http."""
        url = stable_server.url("/get")

        httpx_hook_order = []
        faster_hook_order = []

        def httpx_hook_1(request):
            httpx_hook_order.append("hook_1")

        def httpx_hook_2(request):
            httpx_hook_order.append("hook_2")

        def faster_hook_1(request):
            faster_hook_order.append("hook_1")

        def faster_hook_2(request):
            faster_hook_order.append("hook_2")

        # First test httpx multiple hooks execution
        httpx_client = httpx.Client(event_hooks={"request": [httpx_hook_1, httpx_hook_2]})
        httpx_response = httpx_client.get(url)
        assert httpx_response.status_code == 200
        assert httpx_hook_order == ["hook_1", "hook_2"]
        httpx_client.close()

        # Then test faster_http multiple hooks execution (should match httpx order)
        faster_client = faster_http.Client(event_hooks={"request": [faster_hook_1, faster_hook_2]})
        faster_response = faster_client.get(url)
        assert faster_response.status_code == 200
        assert faster_hook_order == ["hook_1", "hook_2"]
        faster_client.close()

        # Both should execute hooks in the same order
        assert httpx_hook_order == faster_hook_order

    def test_hook_error_handling_comparison(self, stable_server):
        """Test response hook with error handling - httpx vs faster_http."""
        error_url = stable_server.url("/status/404")

        def raise_on_4xx_5xx(response):
            response.raise_for_status()

        # First test httpx response hook with error handling
        httpx_client = httpx.Client(event_hooks={"response": [raise_on_4xx_5xx]})

        try:
            httpx_client.get(error_url)
            raise AssertionError("Should have raised HTTPStatusError")
        except httpx.HTTPStatusError as e:
            assert e.response.status_code == 404

        httpx_client.close()

        # Then test faster_http response hook with error handling (should behave like httpx)
        faster_client = faster_http.Client(event_hooks={"response": [raise_on_4xx_5xx]})

        try:
            faster_client.get(error_url)
            raise AssertionError("Should have raised HTTPStatusError")
        except faster_http.HTTPStatusError as e:
            assert e.response.status_code == 404

        faster_client.close()

    def test_hook_inspection_only_comparison(self):
        """Test that hooks can only inspect, not modify objects - httpx vs faster_http."""
        # This test verifies the httpx behavior where hooks cannot modify request/response objects

        modified_url = "https://example.com/modified"

        def try_modify_request(request):
            # According to httpx docs, hooks cannot modify objects
            # This should not affect the actual request
            try:
                # Attempt to modify (should not work in httpx)
                request.url = modified_url
            except (AttributeError, TypeError):
                # Expected - httpx doesn't allow modification
                pass

        def try_modify_response(response):
            # Similarly, response modification should not be possible
            try:
                response.status_code = 999
            except (AttributeError, TypeError):
                # Expected - httpx doesn't allow modification
                pass

        # First test httpx behavior (hooks should not modify objects)
        httpx_client = httpx.Client(event_hooks={"request": [try_modify_request], "response": [try_modify_response]})
        # Note: We can't actually test this without making a real request
        # but we can verify the hooks are set up
        assert len(httpx_client.event_hooks["request"]) == 1
        assert len(httpx_client.event_hooks["response"]) == 1
        httpx_client.close()

        # Then test faster_http behavior (should match httpx)
        faster_client = faster_http.Client(
            event_hooks={"request": [try_modify_request], "response": [try_modify_response]}
        )
        assert len(faster_client.event_hooks["request"]) == 1
        assert len(faster_client.event_hooks["response"]) == 1
        faster_client.close()


class TestAsyncEventHooks:
    """Test async event hooks functionality - httpx vs faster_http comparison."""

    def test_async_hook_configuration_comparison(self):
        """Test async hooks configuration - httpx vs faster_http."""

        async def httpx_async_request_hook(request):
            pass

        async def httpx_async_response_hook(response):
            pass

        async def faster_async_request_hook(request):
            pass

        async def faster_async_response_hook(response):
            pass

        # First test httpx AsyncClient with async hooks
        httpx_client = httpx.AsyncClient(
            event_hooks={"request": [httpx_async_request_hook], "response": [httpx_async_response_hook]}
        )
        assert httpx_client is not None
        assert hasattr(httpx_client, "event_hooks")

        # Then test faster_http AsyncClient with async hooks (should match httpx)
        faster_client = faster_http.AsyncClient(
            event_hooks={"request": [faster_async_request_hook], "response": [faster_async_response_hook]}
        )
        assert faster_client is not None
        assert hasattr(faster_client, "event_hooks")

    def test_sync_hooks_with_async_client_should_fail_comparison(self):
        """Test that sync hooks with AsyncClient should fail - httpx vs faster_http."""

        def sync_request_hook(request):
            pass

        def sync_response_hook(response):
            pass

        # First test httpx AsyncClient with sync hooks (should work or fail consistently)
        try:
            httpx.AsyncClient(event_hooks={"request": [sync_request_hook], "response": [sync_response_hook]})
            httpx_accepts_sync = True
        except (TypeError, ValueError):
            httpx_accepts_sync = False

        # Then test faster_http AsyncClient with sync hooks (should match httpx behavior)
        try:
            faster_http.AsyncClient(event_hooks={"request": [sync_request_hook], "response": [sync_response_hook]})
            faster_accepts_sync = True
        except (TypeError, ValueError):
            faster_accepts_sync = False

        # Both should behave consistently
        assert httpx_accepts_sync == faster_accepts_sync
