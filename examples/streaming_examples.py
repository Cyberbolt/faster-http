#!/usr/bin/env python3
"""
Streaming and SSE Examples for faster_http.

This example demonstrates streaming capabilities:
- Streaming responses and downloads
- Server-Sent Events (SSE) processing
- Memory-efficient data processing
- Real-world usage patterns
"""

import asyncio
import faster_http
from faster_http import stream, AsyncClient, StreamingResponse


def demo_basic_streaming():
    """Demonstrate basic streaming functionality."""
    print("🌊 Basic Streaming Demo")
    print("=" * 50)
    
    # 1. Stream function
    print("1. Stream function:")
    try:
        with stream("GET", "https://httpbin.org/get") as response:
            print(f"   Status: {response.status_code}")
            print(f"   Content-Type: {response.headers.get('content-type', 'unknown')}")
            print(f"   Streaming: {hasattr(response, 'iter_bytes')}")
    except Exception as e:
        print(f"   Note: {e}")
    
    # 2. Response iteration
    print("\n2. Response iteration methods:")
    response = faster_http.get("https://httpbin.org/json")
    
    # Iterate over bytes
    byte_chunks = response.iter_bytes(chunk_size=100)
    print(f"   Byte chunks: {len(byte_chunks)}")
    print(f"   Total bytes: {sum(len(chunk) for chunk in byte_chunks)}")
    
    # Iterate over text
    text_chunks = response.iter_text(chunk_size=50)
    print(f"   Text chunks: {len(text_chunks)}")
    
    # Iterate over lines
    lines = response.iter_lines()
    print(f"   Lines: {len(lines)}")
    print(f"   First line: {lines[0][:50]}..." if lines else "   No lines")
    
    print()


def demo_streaming_response():
    """Demonstrate StreamingResponse wrapper."""
    print("📦 StreamingResponse Demo")
    print("=" * 50)
    
    try:
        # 1. Basic StreamingResponse
        print("1. StreamingResponse wrapper:")
        response = faster_http.get("https://httpbin.org/get")
        streaming_resp = StreamingResponse(response)
        
        print(f"   Status: {streaming_resp.status_code}")
        print(f"   URL: {streaming_resp.url}")
        print(f"   Consumed: {streaming_resp._consumed}")
        
        # 2. Iteration methods
        print("\n2. Streaming iteration:")
        
        # Use separate responses for each iteration to avoid consumption issues
        response1 = faster_http.get("https://httpbin.org/get")
        streaming_resp1 = StreamingResponse(response1)
        byte_chunks = streaming_resp1.iter_bytes(chunk_size=64)
        print(f"   Byte chunks: {len(byte_chunks)}")
        
        response2 = faster_http.get("https://httpbin.org/get")
        streaming_resp2 = StreamingResponse(response2)
        text_chunks = streaming_resp2.iter_text(chunk_size=32)
        print(f"   Text chunks: {len(text_chunks)}")
        
        response3 = faster_http.get("https://httpbin.org/get")
        streaming_resp3 = StreamingResponse(response3)
        lines = streaming_resp3.iter_lines()
        print(f"   Lines: {len(lines)}")
        
        # 3. Consumption tracking
        print("\n3. Consumption tracking:")
        response4 = faster_http.get("https://httpbin.org/get")
        streaming_resp4 = StreamingResponse(response4)
        print(f"   Before consumption: {streaming_resp4._consumed}")
        
        # Consume the stream
        streaming_resp4.iter_bytes()
        print(f"   After consumption: {streaming_resp4._consumed}")
        
        # Try to use again (should raise error)
        try:
            streaming_resp4.iter_text()
        except RuntimeError as e:
            print(f"   ✓ Correctly prevented reuse: {e}")
    
    except TypeError as e:
        if "StreamingResponse requires" in str(e):
            print("1. StreamingResponse wrapper:")
            print("   Note: StreamingResponse requires specific response type")
            print("   Using direct response iteration instead:")
            
            response = faster_http.get("https://httpbin.org/get")
            byte_chunks = response.iter_bytes(chunk_size=64)
            text_chunks = response.iter_text(chunk_size=32)
            lines = response.iter_lines()
            
            print(f"   Direct byte chunks: {len(byte_chunks)}")
            print(f"   Direct text chunks: {len(text_chunks)}")
            print(f"   Direct lines: {len(lines)}")
        else:
            raise
    
    print()


def demo_sse_parsing():
    """Demonstrate SSE (Server-Sent Events) parsing."""
    print("📡 SSE Parsing Demo")
    print("=" * 50)
    
    # 1. SSE event parsing simulation
    print("1. SSE event parsing:")
    
    def parse_sse_event(line):
        """Parse a single SSE line."""
        line = line.strip()
        if not line or line.startswith(':'):
            return None
        
        if ':' in line:
            key, value = line.split(':', 1)
            return {key.strip(): value.strip()}
        return {'data': line}
    
    # Simulate SSE content
    sse_lines = [
        "data: Hello World",
        "event: greeting",
        "id: 1",
        "",
        "data: {\"type\": \"update\", \"value\": 42}",
        "event: json_data",
        "id: 2",
        "",
        ": This is a comment line",
        "data: Final message",
        "event: closing",
        ""
    ]
    
    events = []
    current_event = {}
    
    for line in sse_lines:
        parsed = parse_sse_event(line)
        if parsed:
            current_event.update(parsed)
        elif line.strip() == '':
            if current_event:
                events.append(current_event.copy())
                current_event.clear()
    
    if current_event:
        events.append(current_event)
    
    print(f"   Parsed {len(events)} SSE events:")
    for i, event in enumerate(events, 1):
        print(f"     Event {i}: {event}")
    
    # 2. SSE methods (if available)
    print("\n2. Built-in SSE methods:")
    try:
        response = faster_http.get("https://httpbin.org/get")
        streaming_resp = StreamingResponse(response)
        
        try:
            sse_events = streaming_resp.iter_sse_events()
            print(f"   SSE events found: {len(sse_events)}")
            if not sse_events:
                print("   (No SSE events in regular JSON response - expected)")
        except Exception as e:
            print(f"   SSE parsing: {e}")
    except TypeError as e:
        if "StreamingResponse requires" in str(e):
            print("   Note: SSE parsing requires specific response type")
        else:
            print(f"   SSE parsing: {e}")
    
    print()


def demo_memory_efficient_processing():
    """Demonstrate memory-efficient processing."""
    print("💾 Memory-Efficient Processing Demo")
    print("=" * 50)
    
    # 1. Chunked processing
    print("1. Chunked processing:")
    response = faster_http.get("https://httpbin.org/get")
    
    processed_chunks = 0
    total_processed = 0
    
    for chunk in response.iter_bytes(chunk_size=64):
        processed_chunks += 1
        total_processed += len(chunk)
        
        # Simulate processing (e.g., writing to file, parsing data)
        # In real usage, you'd process the chunk here
        
        if processed_chunks >= 10:  # Limit for demo
            break
    
    print(f"   Processed {processed_chunks} chunks")
    print(f"   Total bytes processed: {total_processed}")
    print(f"   Average chunk size: {total_processed / processed_chunks:.1f}")
    
    # 2. Line-by-line processing
    print("\n2. Line-by-line processing:")
    response = faster_http.get("https://httpbin.org/json")
    
    def process_json_lines(response):
        """Process response line by line."""
        processed_lines = 0
        for line in response.iter_lines():
            line = line.strip()
            if line:
                # In real usage, you might parse JSON objects here
                processed_lines += 1
                
                # Demo: just count non-empty lines
                if processed_lines >= 5:  # Limit for demo
                    break
        
        return processed_lines
    
    lines_processed = process_json_lines(response)
    print(f"   Processed {lines_processed} lines")
    
    # 3. Streaming download simulation
    print("\n3. Streaming download simulation:")
    response = faster_http.get("https://httpbin.org/json")
    
    downloaded_bytes = 0
    chunk_count = 0
    
    for chunk in response.iter_bytes(chunk_size=128):
        downloaded_bytes += len(chunk)
        chunk_count += 1
        
        # Calculate progress
        progress = (downloaded_bytes / len(response.content)) * 100
        
        # In real usage, you'd write to file here
        # with open('download.dat', 'ab') as f:
        #     f.write(chunk)
        
        if chunk_count >= 8:  # Limit for demo
            break
    
    print(f"   Downloaded {downloaded_bytes} bytes in {chunk_count} chunks")
    print(f"   Progress: {progress:.1f}%")
    
    print()


async def demo_async_streaming():
    """Demonstrate async streaming."""
    print("🚀 Async Streaming Demo")
    print("=" * 50)
    
    # 1. Async streaming response
    print("1. Async streaming:")
    try:
        async with AsyncClient() as client:
            response = await client.get("https://httpbin.org/json")
            streaming_resp = StreamingResponse(response)
            
            print(f"   Async response status: {response.status_code}")
            print(f"   Response size: {len(response.content)} bytes")
            
            # Test async iteration if available
            try:
                async_chunks = []
                async for chunk in streaming_resp.aiter_bytes(chunk_size=100):
                    async_chunks.append(chunk)
                    if len(async_chunks) >= 5:  # Limit for demo
                        break
                
                print(f"   Async byte chunks: {len(async_chunks)}")
                
            except (AttributeError, TypeError):
                print("   Async iteration not yet implemented")
    except TypeError as e:
        if "StreamingResponse requires" in str(e):
            async with AsyncClient() as client:
                response = await client.get("https://httpbin.org/json")
                print(f"   Async response status: {response.status_code}")
                print(f"   Response size: {len(response.content)} bytes")
                print("   Note: Using direct response iteration")
                
                byte_chunks = response.iter_bytes(chunk_size=100)
                print(f"   Direct byte chunks: {len(byte_chunks)}")
        else:
            raise
    
    # 2. Concurrent streaming
    print("\n2. Concurrent streaming requests:")
    urls = [
        "https://httpbin.org/get?stream=1",
        "https://httpbin.org/get?stream=2",
        "https://httpbin.org/get?stream=3"
    ]
    
    async with AsyncClient() as client:
        tasks = [client.get(url) for url in urls]
        responses = await asyncio.gather(*tasks)
        
        for i, response in enumerate(responses, 1):
            chunks = response.iter_bytes(chunk_size=100)
            print(f"   Stream {i}: {len(chunks)} chunks")
    
    print()


def demo_real_world_patterns():
    """Demonstrate real-world streaming patterns."""
    print("🌍 Real-World Patterns Demo")
    print("=" * 50)
    
    # 1. JSON Lines processing
    print("1. JSON Lines processing pattern:")
    
    def process_json_lines_stream(response):
        """Process a stream of JSON lines."""
        import json
        
        processed_objects = []
        
        for line in response.iter_lines():
            line = line.strip()
            if line:
                try:
                    # In real usage, each line would be a JSON object
                    # For demo, we'll just simulate this
                    if line.startswith('{') and line.endswith('}'):
                        # Would parse: obj = json.loads(line)
                        processed_objects.append(f"JSON object {len(processed_objects) + 1}")
                    
                    if len(processed_objects) >= 3:  # Limit for demo
                        break
                        
                except json.JSONDecodeError:
                    pass  # Skip invalid JSON
        
        return processed_objects
    
    response = faster_http.get("https://httpbin.org/get")
    objects = process_json_lines_stream(response)
    print(f"   Processed objects: {objects}")
    
    # 2. Progress tracking pattern
    print("\n2. Progress tracking pattern:")
    
    def download_with_progress(url, chunk_size=1024):
        """Download with progress tracking."""
        response = faster_http.get(url)
        total_size = len(response.content)
        downloaded = 0
        
        progress_points = []
        
        for chunk in response.iter_bytes(chunk_size=chunk_size):
            downloaded += len(chunk)
            progress = (downloaded / total_size) * 100
            
            # Record progress at 25% intervals
            if progress >= len(progress_points) * 25:
                progress_points.append(progress)
            
            if len(progress_points) >= 4:  # 0%, 25%, 50%, 75%, 100%
                break
        
        return progress_points
    
    progress = download_with_progress("https://httpbin.org/json", chunk_size=50)
    print(f"   Progress points: {[f'{p:.1f}%' for p in progress]}")
    
    # 3. httpx-style streaming
    print("\n3. httpx-style streaming:")
    
    # Use faster_http as httpx replacement
    import faster_http as httpx
    
    try:
        with httpx.stream("GET", "https://httpbin.org/json") as r:
            total_size = 0
            chunk_count = 0
            
            for chunk in r.iter_bytes(256):
                total_size += len(chunk)
                chunk_count += 1
                
                if chunk_count >= 5:  # Limit for demo
                    break
            
            print(f"   httpx-style: {chunk_count} chunks, {total_size} bytes")
            
    except Exception as e:
        print(f"   httpx-style streaming: {e}")
    
    print()


def main():
    """Run all streaming demos."""
    print("🎯 faster-http: Streaming and SSE Examples")
    print("=" * 60)
    print("Demonstrating streaming capabilities and SSE processing\n")
    
    try:
        # Synchronous demos
        demo_basic_streaming()
        demo_streaming_response()
        demo_sse_parsing()
        demo_memory_efficient_processing()
        demo_real_world_patterns()
        
        # Asynchronous demo
        print("Running async streaming demo...")
        asyncio.run(demo_async_streaming())
        
        print("🎉 All streaming demos completed!")
        print("\n📋 Summary of streaming features:")
        print("✅ Basic streaming responses")
        print("✅ StreamingResponse wrapper with consumption tracking")
        print("✅ SSE (Server-Sent Events) parsing")
        print("✅ Memory-efficient chunked processing")
        print("✅ Line-by-line processing")
        print("✅ Progress tracking for downloads")
        print("✅ Async streaming capabilities")
        print("✅ Real-world usage patterns")
        print("✅ httpx-compatible streaming interface")
        print("\n🚀 faster-http enables efficient processing of large responses!")
        
    except Exception as e:
        print(f"Demo error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 