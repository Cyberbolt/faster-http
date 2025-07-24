"""
Mock HTTP server for testing without external dependencies.
This follows CLAUDE.md requirement that tests should not depend on external websites.
"""

import json
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Dict, Any, Optional
from urllib.parse import urlparse, parse_qs


class MockHTTPRequestHandler(BaseHTTPRequestHandler):
    """Mock HTTP server request handler with various test endpoints."""
    
    def log_message(self, format, *args):
        # Suppress server logs during testing
        pass
    
    def _send_json_response(self, status_code: int, data: Dict[str, Any], headers: Optional[Dict[str, str]] = None):
        """Send JSON response with given status code and data."""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        if headers:
            for key, value in headers.items():
                self.send_header(key, value)
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def _get_request_data(self) -> Dict[str, Any]:
        """Extract request data for response."""
        parsed_url = urlparse(self.path)
        query_params = parse_qs(parsed_url.query)
        
        return {
            'method': self.command,
            'url': self.path,
            'path': parsed_url.path,
            'query': parsed_url.query,
            'query_params': {k: v[0] if len(v) == 1 else v for k, v in query_params.items()},
            'headers': dict(self.headers),
        }
    
    def do_GET(self):
        """Handle GET requests."""
        request_data = self._get_request_data()
        path = request_data['path']
        
        if path == '/get':
            self._send_json_response(200, request_data)
        elif path == '/json':
            self._send_json_response(200, {
                'test': 'data',
                'number': 42,
                'boolean': True,
                'null_value': None,
                'nested': {'key': 'value', 'items': [1, 2, 3]}
            })
        elif path == '/headers':
            self._send_json_response(200, {'headers': request_data['headers']})
        elif path == '/user-agent':
            user_agent = request_data['headers'].get('User-Agent', 'Unknown')
            self._send_json_response(200, {'user-agent': user_agent})
        elif path.startswith('/status/'):
            status_code = int(path.split('/')[-1])
            self._send_json_response(status_code, {
                'status': status_code,
                'message': f'HTTP {status_code}'
            })
        elif path == '/redirect':
            self.send_response(302)
            self.send_header('Location', '/get')
            self.end_headers()
        elif path == '/cookies':
            cookies = {}
            cookie_header = self.headers.get('Cookie', '')
            if cookie_header:
                for cookie in cookie_header.split(';'):
                    if '=' in cookie:
                        key, value = cookie.strip().split('=', 1)
                        cookies[key] = value
            self._send_json_response(200, {'cookies': cookies})
        elif path == '/stream':
            # Simple streaming response
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.send_header('Transfer-Encoding', 'chunked')
            self.end_headers()
            
            for i in range(3):
                chunk = f"chunk {i + 1}\n"
                self.wfile.write(f"{len(chunk.encode()):x}\r\n".encode())
                self.wfile.write(chunk.encode())
                self.wfile.write(b"\r\n")
                time.sleep(0.1)
            
            self.wfile.write(b"0\r\n\r\n")
        else:
            self._send_json_response(404, {'error': 'Not Found', 'path': path})
    
    def do_POST(self):
        """Handle POST requests."""
        request_data = self._get_request_data()
        path = request_data['path']
        
        # Read request body
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length) if content_length > 0 else b''
        
        request_data['data'] = post_data.decode('utf-8', errors='ignore') if post_data else ''
        request_data['content_length'] = content_length
        
        # Parse JSON if content type is application/json
        if self.headers.get('Content-Type') == 'application/json':
            try:
                request_data['json'] = json.loads(post_data.decode())
            except (json.JSONDecodeError, UnicodeDecodeError):
                request_data['json'] = None
        
        if path == '/post':
            self._send_json_response(200, request_data)
        elif path == '/echo':
            # Echo back the request
            self._send_json_response(200, {
                'echoed': request_data,
                'received_data': request_data.get('json') or request_data.get('data')
            })
        else:
            self._send_json_response(404, {'error': 'Not Found', 'path': path})
    
    def do_PUT(self):
        """Handle PUT requests."""
        self.do_POST()  # Same logic as POST
    
    def do_PATCH(self):
        """Handle PATCH requests."""
        self.do_POST()  # Same logic as POST
    
    def do_DELETE(self):
        """Handle DELETE requests."""
        request_data = self._get_request_data()
        path = request_data['path']
        
        if path == '/delete':
            self._send_json_response(200, request_data)
        else:
            self._send_json_response(404, {'error': 'Not Found', 'path': path})
    
    def do_HEAD(self):
        """Handle HEAD requests."""
        path = urlparse(self.path).path
        
        if path == '/head':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('X-Test-Header', 'test-value')
            self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_OPTIONS(self):
        """Handle OPTIONS requests."""
        path = urlparse(self.path).path
        
        if path == '/options':
            self.send_response(200)
            self.send_header('Allow', 'GET, POST, PUT, PATCH, DELETE, HEAD, OPTIONS')
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                'method': 'OPTIONS',
                'allowed_methods': ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'HEAD', 'OPTIONS']
            }).encode())
        else:
            self.send_response(404)
            self.end_headers()


class MockHTTPServer:
    """Mock HTTP server for testing."""
    
    def __init__(self, host='localhost', port=0):
        self.server = HTTPServer((host, port), MockHTTPRequestHandler)
        self.host = host
        self.port = self.server.server_address[1]
        self.base_url = f"http://{self.host}:{self.port}"
        self.thread = None
        self.running = False
    
    def start(self):
        """Start the server in a background thread."""
        if not self.running:
            self.thread = threading.Thread(target=self.server.serve_forever)
            self.thread.daemon = True
            self.thread.start()
            self.running = True
            time.sleep(0.05)  # Give server time to start
    
    def stop(self):
        """Stop the server."""
        if self.running:
            self.server.shutdown()
            self.server.server_close()
            if self.thread:
                self.thread.join(timeout=1)
            self.running = False
    
    def __enter__(self):
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
    
    def url(self, path=''):
        """Get full URL for a path."""
        return f"{self.base_url}{path}"


# Convenience function for pytest fixtures
def create_mock_server():
    """Create and return a mock server instance."""
    return MockHTTPServer()