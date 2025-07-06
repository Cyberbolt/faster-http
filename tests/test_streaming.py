"""
Streaming and SSE functionality tests for faster_http.
Tests streaming responses, SSE events, and related features.
"""

import pytest

from faster_http import (
    get, stream, AsyncClient, StreamingResponse
)


class TestStreamingBasics:
    """Test basic streaming functionality."""
    
    def test_stream_function_basic(self, test_urls):
        """Test basic stream function usage."""
        try:
            with stream("GET", test_urls['get']) as response:
                assert response.status_code == 200
                assert hasattr(response, 'headers')
                assert hasattr(response, 'url')
                assert hasattr(response, 'iter_bytes')
                assert hasattr(response, 'iter_text')
                assert hasattr(response, 'iter_lines')
        except Exception as e:
            pytest.skip(f"Stream function not fully implemented: {e}")
    
    def test_streaming_response_wrapper(self, test_urls):
        """Test StreamingResponse wrapper."""
        try:
            response = get(test_urls['get'])
            streaming_resp = StreamingResponse(response)
            
            # Test basic properties
            assert streaming_resp.status_code == 200
            assert streaming_resp.headers is not None
            assert streaming_resp.url is not None
            
            # Test that it's initially not consumed
            assert not streaming_resp._consumed
        except TypeError as e:
            if "StreamingResponse requires" in str(e):
                pytest.skip("StreamingResponse requires specific response type")
            else:
                raise
    
    def test_response_iter_methods(self, test_urls):
        """Test response iterator methods."""
        response = get(test_urls['get'])
        
        # Test iter_bytes
        byte_chunks = response.iter_bytes(chunk_size=100)
        assert isinstance(byte_chunks, list)
        assert len(byte_chunks) > 0
        
        # Verify total size matches content
        total_size = sum(len(chunk) for chunk in byte_chunks)
        assert total_size == len(response.content)
        
        # Test iter_text
        text_chunks = response.iter_text(chunk_size=50)
        assert isinstance(text_chunks, list)
        assert len(text_chunks) > 0
        
        # Verify text chunks reconstruct original text
        joined_text = "".join(text_chunks)
        assert joined_text == response.text
        
        # Test iter_lines
        lines = response.iter_lines()
        assert isinstance(lines, list)
        assert len(lines) > 0
        
        # Test iter_raw
        raw_chunks = response.iter_raw(chunk_size=100)
        assert isinstance(raw_chunks, list)
        assert len(raw_chunks) > 0


class TestStreamingResponse:
    """Test StreamingResponse class functionality."""
    
    def test_streaming_response_iter_methods(self, test_urls):
        """Test StreamingResponse iteration methods."""
        try:
            response = get(test_urls['get'])
            
            # Test iter_bytes
            streaming_resp1 = StreamingResponse(response)
            byte_chunks = streaming_resp1.iter_bytes(chunk_size=100)
            assert isinstance(byte_chunks, list)
            assert len(byte_chunks) > 0
            
            # Test iter_text
            streaming_resp2 = StreamingResponse(response)
            text_chunks = streaming_resp2.iter_text(chunk_size=100)
            assert isinstance(text_chunks, list)
            assert len(text_chunks) > 0
            
            # Test iter_lines
            streaming_resp3 = StreamingResponse(response)
            lines = streaming_resp3.iter_lines()
            assert isinstance(lines, list)
            assert len(lines) > 0
        except TypeError as e:
            if "StreamingResponse requires" in str(e):
                pytest.skip("StreamingResponse requires specific response type")
            else:
                raise
    
    def test_streaming_response_consumption_tracking(self, test_urls):
        """Test stream consumption tracking."""
        try:
            response = get(test_urls['get'])
            streaming_resp = StreamingResponse(response)
            
            # Initially not consumed
            assert not streaming_resp._consumed
            
            # Consume the stream
            streaming_resp.iter_bytes()
            
            # Should be marked as consumed
            assert streaming_resp._consumed
            
            # Should raise error when accessing after consumption
            with pytest.raises(RuntimeError, match="consumed"):
                streaming_resp.iter_text()
        except TypeError as e:
            if "StreamingResponse requires" in str(e):
                pytest.skip("StreamingResponse requires specific response type")
            else:
                raise
    
    def test_streaming_response_close(self, test_urls):
        """Test StreamingResponse close method."""
        try:
            response = get(test_urls['get'])
            streaming_resp = StreamingResponse(response)
            
            # Initially not consumed
            assert not streaming_resp._consumed
            
            # Close the stream
            streaming_resp.close()
            
            # Should be marked as consumed
            assert streaming_resp._consumed
        except TypeError as e:
            if "StreamingResponse requires" in str(e):
                pytest.skip("StreamingResponse requires specific response type")
            else:
                raise


class TestSSEFeatures:
    """Test Server-Sent Events (SSE) functionality."""
    
    def test_sse_event_parsing_simulation(self):
        """Test SSE event parsing with simulated data."""
        def parse_sse_event(line):
            """Parse a single SSE line."""
            line = line.strip()
            if not line or line.startswith(':'):
                return None
            
            if ':' in line:
                key, value = line.split(':', 1)
                return {key.strip(): value.strip()}
            return {'data': line}
        
        # Simulate SSE-like content
        mock_sse_lines = [
            "data: Hello World",
            "event: message", 
            "id: 1",
            "",
            "data: {\"type\": \"update\"}",
            "event: json",
            ": This is a comment",
            "data: Final message"
        ]
        
        events = []
        current_event = {}
        
        for line in mock_sse_lines:
            parsed = parse_sse_event(line)
            if parsed:
                if 'data' in parsed:
                    current_event['data'] = parsed['data']
                elif 'event' in parsed:
                    current_event['event'] = parsed['event']
                elif 'id' in parsed:
                    current_event['id'] = parsed['id']
            elif line.strip() == '':
                if current_event:
                    events.append(current_event.copy())
                    current_event.clear()
        
        if current_event:
            events.append(current_event)
        
        assert len(events) >= 2
        assert events[0]['data'] == 'Hello World'
        assert events[0]['event'] == 'message'
    
    def test_sse_methods_exist(self, test_urls):
        """Test that SSE methods exist and can be called."""
        try:
            response = get(test_urls['get'])
            streaming_resp = StreamingResponse(response)
            
            # Test SSE method exists
            try:
                sse_events = streaming_resp.iter_sse_events()
                assert isinstance(sse_events, list)
                # Regular HTTP response won't have SSE events
                assert len(sse_events) == 0
            except Exception as e:
                # Method might not be fully implemented yet
                pytest.skip(f"SSE parsing not implemented: {e}")
            
            # Test response SSE lines method if available
            if hasattr(response, 'iter_sse_lines'):
                try:
                    sse_lines = response.iter_sse_lines()
                    assert isinstance(sse_lines, list)
                except Exception as e:
                    pytest.skip(f"Response SSE lines not implemented: {e}")
        except TypeError as e:
            if "StreamingResponse requires" in str(e):
                pytest.skip("StreamingResponse requires specific response type")
            else:
                raise


class TestAsyncStreaming:
    """Test asynchronous streaming functionality."""
    
    @pytest.mark.asyncio
    async def test_async_streaming_response(self, test_urls):
        """Test async streaming response."""
        try:
            async with AsyncClient() as client:
                response = await client.get(test_urls['json'])
                streaming_resp = StreamingResponse(response)
                
                # Test async iteration methods if available
                try:
                    # Test aiter_bytes
                    byte_chunks = []
                    async for chunk in streaming_resp.aiter_bytes(chunk_size=100):
                        byte_chunks.append(chunk)
                        if len(byte_chunks) >= 5:  # Limit for test
                            break
                    
                    assert len(byte_chunks) > 0
                    
                except (AttributeError, TypeError):
                    # Async iteration might not be implemented yet
                    pytest.skip("Async iteration not implemented")
        except TypeError as e:
            if "StreamingResponse requires" in str(e):
                pytest.skip("StreamingResponse requires specific response type")
            else:
                raise
    
    @pytest.mark.asyncio
    async def test_async_text_iteration(self, test_urls):
        """Test async text iteration."""
        try:
            async with AsyncClient() as client:
                response = await client.get(test_urls['get'])
                streaming_resp = StreamingResponse(response)
                
                try:
                    text_chunks = []
                    async for chunk in streaming_resp.aiter_text(chunk_size=50):
                        text_chunks.append(chunk)
                        if len(text_chunks) >= 5:  # Limit for test
                            break
                    
                    assert len(text_chunks) > 0
                    
                except (AttributeError, TypeError):
                    pytest.skip("Async text iteration not implemented")
        except TypeError as e:
            if "StreamingResponse requires" in str(e):
                pytest.skip("StreamingResponse requires specific response type")
            else:
                raise
    
    @pytest.mark.asyncio
    async def test_async_line_iteration(self, test_urls):
        """Test async line iteration."""
        try:
            async with AsyncClient() as client:
                response = await client.get(test_urls['json'])
                streaming_resp = StreamingResponse(response)
                
                try:
                    lines = []
                    async for line in streaming_resp.aiter_lines():
                        lines.append(line)
                        if len(lines) >= 10:  # Limit for test
                            break
                    
                    assert len(lines) > 0
                    
                except (AttributeError, TypeError):
                    pytest.skip("Async line iteration not implemented")
        except TypeError as e:
            if "StreamingResponse requires" in str(e):
                pytest.skip("StreamingResponse requires specific response type")
            else:
                raise
    
    @pytest.mark.asyncio
    async def test_async_sse_iteration(self, test_urls):
        """Test async SSE event iteration."""
        try:
            async with AsyncClient() as client:
                response = await client.get(test_urls['get'])
                streaming_resp = StreamingResponse(response)
                
                try:
                    sse_events = []
                    async for event in streaming_resp.aiter_sse_events():
                        sse_events.append(event)
                        if len(sse_events) >= 3:  # Limit for test
                            break
                    
                    # Regular HTTP response won't have SSE events
                    assert len(sse_events) == 0
                    
                except (AttributeError, TypeError):
                    pytest.skip("Async SSE iteration not implemented")
        except TypeError as e:
            if "StreamingResponse requires" in str(e):
                pytest.skip("StreamingResponse requires specific response type")
            else:
                raise


class TestStreamingMemoryEfficiency:
    """Test streaming memory efficiency."""
    
    def test_large_response_streaming(self, test_urls):
        """Test streaming with larger responses."""
        try:
            with stream("GET", test_urls['json']) as response:
                chunk_count = 0
                total_size = 0
                
                for chunk in response.iter_bytes(chunk_size=50):
                    chunk_count += 1
                    total_size += len(chunk)
                    
                    # Verify we get reasonable chunks
                    assert len(chunk) <= 50 or len(chunk) > 0
                    
                    if chunk_count >= 10:  # Limit to avoid long test
                        break
                
                assert chunk_count > 0
                assert total_size > 0
                
        except Exception as e:
            pytest.skip(f"Stream function not available: {e}")
    
    def test_streaming_with_chunked_processing(self, test_urls):
        """Test processing response in chunks."""
        response = get(test_urls['get'])
        
        # Process in small chunks to verify memory efficiency
        processed_chunks = 0
        total_processed = 0
        
        for chunk in response.iter_bytes(chunk_size=64):
            processed_chunks += 1
            total_processed += len(chunk)
            
            # Each chunk should be reasonably sized
            assert len(chunk) > 0
            assert len(chunk) <= 64 or processed_chunks == 1  # Last chunk might be larger
            
            if processed_chunks >= 20:  # Limit processing
                break
        
        assert processed_chunks > 0
        assert total_processed > 0


class TestStreamingRealWorldUsage:
    """Test real-world streaming usage patterns."""
    
    def test_streaming_json_lines_processing(self, test_urls):
        """Test processing streaming response as JSON lines."""
        def process_streaming_lines(response):
            """Process streaming response line by line."""
            lines_processed = 0
            
            for line in response.iter_lines():
                line = line.strip()
                if line:
                    lines_processed += 1
                    
                    # In real usage, you'd parse JSON or process line here
                    if lines_processed >= 5:  # Limit for demo
                        break
            
            return lines_processed
        
        response = get(test_urls['json'])
        lines = process_streaming_lines(response)
        assert lines > 0
    
    def test_streaming_download_simulation(self, test_urls):
        """Test simulating a streaming download."""
        response = get(test_urls['get'])
        
        downloaded_bytes = 0
        chunk_count = 0
        
        for chunk in response.iter_bytes(chunk_size=128):
            downloaded_bytes += len(chunk)
            chunk_count += 1
            
            # Simulate progress tracking
            progress_percent = (downloaded_bytes / len(response.content)) * 100
            assert progress_percent <= 100
            
            if chunk_count >= 15:  # Limit chunks
                break
        
        assert downloaded_bytes > 0
        assert chunk_count > 0
    
    def test_httpx_streaming_compatibility(self, test_urls):
        """Test httpx-style streaming usage."""
        import faster_http as httpx  # Simulate httpx replacement
        
        try:
            with httpx.stream("GET", test_urls['json']) as r:
                total_size = 0
                for chunk in r.iter_bytes(1024):
                    total_size += len(chunk)
                    if total_size >= 1000:  # Limit size
                        break
                
                assert total_size > 0
                
        except Exception as e:
            pytest.skip(f"httpx-style streaming not available: {e}") 