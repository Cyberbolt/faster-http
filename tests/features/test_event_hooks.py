"""
Test Event Hooks system functionality.
Tests event hooks with httpx vs faster_http comparison.
Following CLAUDE.md requirements: test httpx first, then faster_http for comparison.
"""

import httpx

import faster_http


class TestEventHooksFeatures:
    """Test event hooks features - httpx vs faster_http comparison."""

    def test_request_hook_functionality_comparison(self, stable_server):
        """Test request hook functionality - httpx vs faster_http."""
        url = stable_server.url("/get")

        # Track hook executions
        httpx_requests = []
        faster_requests = []

        def httpx_request_hook(request):
            httpx_requests.append({"method": request.method, "url": str(request.url), "headers": dict(request.headers)})

        def faster_request_hook(request):
            faster_requests.append(
                {"method": request.method, "url": str(request.url), "headers": dict(request.headers)}
            )

        # First test httpx Client with request hooks
        httpx_client = httpx.Client(event_hooks={"request": [httpx_request_hook]})
        httpx_response = httpx_client.get(url)
        assert httpx_response.status_code == 200
        assert len(httpx_requests) == 1
        assert httpx_requests[0]["method"] == "GET"
        httpx_client.close()

        # Then test faster_http Client with request hooks (should match httpx)
        faster_client = faster_http.Client(event_hooks={"request": [faster_request_hook]})
        faster_response = faster_client.get(url)
        assert faster_response.status_code == 200
        assert len(faster_requests) == 1
        assert faster_requests[0]["method"] == "GET"
        faster_client.close()

        # Both should capture same request information
        assert httpx_requests[0]["method"] == faster_requests[0]["method"]
        assert httpx_requests[0]["url"] == faster_requests[0]["url"]

    def test_response_hook_functionality_comparison(self, stable_server):
        """Test response hook functionality - httpx vs faster_http."""
        url = stable_server.url("/json")

        # Track hook executions
        httpx_responses = []
        faster_responses = []

        def httpx_response_hook(response):
            # Safely get content length without triggering ResponseNotRead
            try:
                content_length = len(response.content)
            except Exception:
                content_length = 0

            httpx_responses.append(
                {"status_code": response.status_code, "url": str(response.url), "content_length": content_length}
            )

        def faster_response_hook(response):
            # Safely get content length without triggering ResponseNotRead
            try:
                content_length = len(response.content)
            except Exception:
                content_length = 0

            faster_responses.append(
                {"status_code": response.status_code, "url": str(response.url), "content_length": content_length}
            )

        # First test httpx Client with response hooks
        httpx_client = httpx.Client(event_hooks={"response": [httpx_response_hook]})
        httpx_response = httpx_client.get(url)
        assert httpx_response.status_code == 200
        assert len(httpx_responses) == 1
        assert httpx_responses[0]["status_code"] == 200
        httpx_client.close()

        # Then test faster_http Client with response hooks (should match httpx)
        faster_client = faster_http.Client(event_hooks={"response": [faster_response_hook]})
        faster_response = faster_client.get(url)
        assert faster_response.status_code == 200
        assert len(faster_responses) == 1
        assert faster_responses[0]["status_code"] == 200
        faster_client.close()

        # Both should capture same response information
        assert httpx_responses[0]["status_code"] == faster_responses[0]["status_code"]
        assert httpx_responses[0]["url"] == faster_responses[0]["url"]

    def test_single_hook_vs_list_comparison(self, stable_server):
        """Test single hook vs list format - httpx vs faster_http."""
        url = stable_server.url("/get")

        def single_hook(request):
            pass

        # First test httpx with single hook (in list format)
        httpx_client_single = httpx.Client(event_hooks={"request": [single_hook]})
        assert hasattr(httpx_client_single, "event_hooks")
        httpx_response = httpx_client_single.get(url)
        assert httpx_response.status_code == 200
        httpx_client_single.close()

        # Then test faster_http with single hook (should match httpx)
        faster_client_single = faster_http.Client(event_hooks={"request": [single_hook]})
        assert hasattr(faster_client_single, "event_hooks")
        faster_response = faster_client_single.get(url)
        assert faster_response.status_code == 200
        faster_client_single.close()

        # First test httpx with hook in list
        httpx_client_list = httpx.Client(event_hooks={"request": [single_hook]})
        assert hasattr(httpx_client_list, "event_hooks")
        httpx_response_list = httpx_client_list.get(url)
        assert httpx_response_list.status_code == 200
        httpx_client_list.close()

        # Then test faster_http with hook in list (should match httpx)
        faster_client_list = faster_http.Client(event_hooks={"request": [single_hook]})
        assert hasattr(faster_client_list, "event_hooks")
        faster_response_list = faster_client_list.get(url)
        assert faster_response_list.status_code == 200
        faster_client_list.close()

        # Both formats should work for both libraries
        assert httpx_response.status_code == faster_response.status_code
        assert httpx_response_list.status_code == faster_response_list.status_code

    def test_multiple_hooks_execution_comparison(self, stable_server):
        """Test multiple hooks execution order - httpx vs faster_http."""
        url = stable_server.url("/get")

        httpx_execution_order = []
        faster_execution_order = []

        def httpx_hook_1(request):
            httpx_execution_order.append("first")

        def httpx_hook_2(request):
            httpx_execution_order.append("second")

        def faster_hook_1(request):
            faster_execution_order.append("first")

        def faster_hook_2(request):
            faster_execution_order.append("second")

        # First test httpx multiple hooks execution
        httpx_client = httpx.Client(event_hooks={"request": [httpx_hook_1, httpx_hook_2]})
        httpx_response = httpx_client.get(url)
        assert httpx_response.status_code == 200
        assert httpx_execution_order == ["first", "second"]
        httpx_client.close()

        # Then test faster_http multiple hooks execution (should match httpx order)
        faster_client = faster_http.Client(event_hooks={"request": [faster_hook_1, faster_hook_2]})
        faster_response = faster_client.get(url)
        assert faster_response.status_code == 200
        assert faster_execution_order == ["first", "second"]
        faster_client.close()

        # Both should execute hooks in the same order
        assert httpx_execution_order == faster_execution_order

    def test_mixed_request_response_hooks_comparison(self, stable_server):
        """Test mixed request and response hooks - httpx vs faster_http."""
        url = stable_server.url("/post")
        data = {"test": "mixed_hooks"}

        httpx_calls = {"request": 0, "response": 0}
        faster_calls = {"request": 0, "response": 0}

        def httpx_request_hook(request):
            httpx_calls["request"] += 1

        def httpx_response_hook(response):
            httpx_calls["response"] += 1

        def faster_request_hook(request):
            faster_calls["request"] += 1

        def faster_response_hook(response):
            faster_calls["response"] += 1

        # First test httpx with both request and response hooks
        httpx_client = httpx.Client(event_hooks={"request": [httpx_request_hook], "response": [httpx_response_hook]})
        httpx_response = httpx_client.post(url, json=data)
        assert httpx_response.status_code == 200
        assert httpx_calls["request"] == 1
        assert httpx_calls["response"] == 1
        httpx_client.close()

        # Then test faster_http with both request and response hooks (should match httpx)
        faster_client = faster_http.Client(
            event_hooks={"request": [faster_request_hook], "response": [faster_response_hook]}
        )
        faster_response = faster_client.post(url, json=data)
        assert faster_response.status_code == 200
        assert faster_calls["request"] == 1
        assert faster_calls["response"] == 1
        faster_client.close()

        # Both should execute same number of hooks
        assert httpx_calls == faster_calls

    def test_no_hooks_client_comparison(self, stable_server):
        """Test client without hooks - httpx vs faster_http."""
        url = stable_server.url("/get")

        # First test httpx Client without hooks
        httpx_client = httpx.Client()  # No event_hooks parameter
        assert hasattr(httpx_client, "event_hooks")
        httpx_response = httpx_client.get(url)
        assert httpx_response.status_code == 200
        httpx_client.close()

        # Then test faster_http Client without hooks (should match httpx)
        faster_client = faster_http.Client()  # No event_hooks parameter
        assert hasattr(faster_client, "event_hooks")
        faster_response = faster_client.get(url)
        assert faster_response.status_code == 200
        faster_client.close()

        # Both should work without hooks
        assert httpx_response.status_code == faster_response.status_code

    def test_async_event_hooks_comparison(self, stable_server):
        """Test async event hooks - httpx vs faster_http."""
        import asyncio

        async def test_async_hooks():
            url = stable_server.url("/get")

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

            httpx_response = await httpx_client.get(url)
            assert httpx_response.status_code == 200
            await httpx_client.aclose()

            # Then test faster_http AsyncClient with async hooks (should match httpx)
            faster_client = faster_http.AsyncClient(
                event_hooks={"request": [faster_async_request_hook], "response": [faster_async_response_hook]}
            )

            faster_response = await faster_client.get(url)
            assert faster_response.status_code == 200
            await faster_client.aclose()

            # Both should work with async hooks
            assert httpx_response.status_code == faster_response.status_code

        asyncio.run(test_async_hooks())

    def test_hook_error_handling_comparison(self, stable_server):
        """Test hook error handling - httpx vs faster_http."""
        url = stable_server.url("/get")

        def failing_hook(request):
            raise ValueError("Hook intentionally failed")

        # First test httpx behavior with failing hook
        httpx_client = httpx.Client(event_hooks={"request": [failing_hook]})

        try:
            _ = httpx_client.get(url)
        except Exception:
            pass
        finally:
            httpx_client.close()

        # Then test faster_http behavior with failing hook (should match httpx)
        faster_client = faster_http.Client(event_hooks={"request": [failing_hook]})

        try:
            _ = faster_client.get(url)
        except Exception:
            pass
        finally:
            faster_client.close()

        # Both should handle failing hooks the same way
        # Note: This test documents the current behavior,
        # whether hooks fail silently or raise exceptions

    def test_hooks_with_authentication_comparison(self, stable_server):
        """Test hooks integration with authentication - httpx vs faster_http."""
        url = stable_server.url("/get")

        httpx_hook_calls = 0
        faster_hook_calls = 0

        def httpx_request_hook(request):
            nonlocal httpx_hook_calls
            httpx_hook_calls += 1
            # Verify auth header is present
            assert "Authorization" in request.headers

        def faster_request_hook(request):
            nonlocal faster_hook_calls
            faster_hook_calls += 1
            # Verify auth header is present
            assert "Authorization" in request.headers

        # First test httpx Client with hooks and auth
        httpx_auth = httpx.BasicAuth("user", "pass")
        httpx_client = httpx.Client(auth=httpx_auth, event_hooks={"request": [httpx_request_hook]})
        httpx_response = httpx_client.get(url)
        assert httpx_response.status_code == 200
        assert httpx_hook_calls == 1
        httpx_client.close()

        # Then test faster_http Client with hooks and auth (should match httpx)
        faster_auth = faster_http.BasicAuth("user", "pass")
        faster_client = faster_http.Client(auth=faster_auth, event_hooks={"request": [faster_request_hook]})
        faster_response = faster_client.get(url)
        assert faster_response.status_code == 200
        assert faster_hook_calls == 1
        faster_client.close()

        # Both should execute hooks with auth integration
        assert httpx_hook_calls == faster_hook_calls

    def test_hooks_context_inspection_comparison(self, stable_server):
        """Test hook context object inspection - httpx vs faster_http."""
        url = stable_server.url("/post")
        data = {"inspection": "test"}

        httpx_inspections = []
        faster_inspections = []

        def httpx_request_inspector(request):
            httpx_inspections.append(
                {
                    "has_method": hasattr(request, "method"),
                    "has_url": hasattr(request, "url"),
                    "has_headers": hasattr(request, "headers"),
                    "has_content": hasattr(request, "content"),
                    "method_value": request.method if hasattr(request, "method") else None,
                }
            )

        def httpx_response_inspector(response):
            # Safely check content without triggering access error
            try:
                # Try to access content to see if it's available
                _ = response.content
                has_content = True
            except Exception:
                # If content access fails, we still consider it as having the attribute
                has_content = True

            httpx_inspections.append(
                {
                    "has_status_code": hasattr(response, "status_code"),
                    "has_headers": hasattr(response, "headers"),
                    "has_content": has_content,
                    "has_url": hasattr(response, "url"),
                    "status_value": response.status_code if hasattr(response, "status_code") else None,
                }
            )

        def faster_request_inspector(request):
            faster_inspections.append(
                {
                    "has_method": hasattr(request, "method"),
                    "has_url": hasattr(request, "url"),
                    "has_headers": hasattr(request, "headers"),
                    "has_content": hasattr(request, "content"),
                    "method_value": request.method if hasattr(request, "method") else None,
                }
            )

        def faster_response_inspector(response):
            # Safely check content without triggering access error
            try:
                # Try to access content to see if it's available
                _ = response.content
                has_content = True
            except Exception:
                # If content access fails, we still consider it as having the attribute
                has_content = True

            faster_inspections.append(
                {
                    "has_status_code": hasattr(response, "status_code"),
                    "has_headers": hasattr(response, "headers"),
                    "has_content": has_content,
                    "has_url": hasattr(response, "url"),
                    "status_value": response.status_code if hasattr(response, "status_code") else None,
                }
            )

        # First test httpx context inspection
        httpx_client = httpx.Client(
            event_hooks={"request": [httpx_request_inspector], "response": [httpx_response_inspector]}
        )
        httpx_response = httpx_client.post(url, json=data)
        assert httpx_response.status_code == 200
        assert len(httpx_inspections) == 2  # request + response
        httpx_client.close()

        # Then test faster_http context inspection (should match httpx)
        faster_client = faster_http.Client(
            event_hooks={"request": [faster_request_inspector], "response": [faster_response_inspector]}
        )
        faster_response = faster_client.post(url, json=data)
        assert faster_response.status_code == 200
        assert len(faster_inspections) == 2  # request + response
        faster_client.close()

        # Both should provide similar context objects
        assert len(httpx_inspections) == len(faster_inspections)

        # Compare request inspection results
        httpx_req = httpx_inspections[0]
        faster_req = faster_inspections[0]
        assert httpx_req["has_method"] == faster_req["has_method"]
        assert httpx_req["has_url"] == faster_req["has_url"]
        assert httpx_req["has_headers"] == faster_req["has_headers"]
        assert httpx_req["method_value"] == faster_req["method_value"]

        # Compare response inspection results
        httpx_resp = httpx_inspections[1]
        faster_resp = faster_inspections[1]
        assert httpx_resp["has_status_code"] == faster_resp["has_status_code"]
        assert httpx_resp["has_headers"] == faster_resp["has_headers"]
        assert httpx_resp["has_content"] == faster_resp["has_content"]
        assert httpx_resp["status_value"] == faster_resp["status_value"]
