"""
Stable HTTP server for testing without external dependencies.
Fixes BrokenPipe issues and ensures reliable local testing.
"""

import json
import threading
import time
import socket
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Dict, Any, Optional
from urllib.parse import urlparse, parse_qs
import sys


def get_working_localhost_address():
    """
    获取在当前环境中可工作的本地地址。
    保持简单，使用127.0.0.1。
    """
    return "127.0.0.1"


class StableHTTPRequestHandler(BaseHTTPRequestHandler):
    """Stable HTTP server request handler that handles connection issues gracefully."""
    
    def log_message(self, format, *args):
        # Suppress server logs during testing
        pass
    
    def _safe_send_response(self, status_code: int, data: Dict[str, Any], headers: Optional[Dict[str, str]] = None):
        """Safely send JSON response, handling broken pipe errors."""
        try:
            # Prepare response data first
            response_data = json.dumps(data).encode('utf-8')
            
            # Send status and headers
            self.send_response(status_code)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(response_data)))
            self.send_header('Connection', 'close')  # Ensure connection closes properly
            
            if headers:
                for key, value in headers.items():
                    self.send_header(key, value)
            
            self.end_headers()
            
            # Send response body
            self.wfile.write(response_data)
            self.wfile.flush()  # Ensure data is sent immediately
            
        except (BrokenPipeError, ConnectionResetError, OSError):
            # Client disconnected before we could send response
            # This is normal in some test scenarios, just ignore
            pass
        except Exception as e:
            # Log other exceptions but don't fail
            print(f"Error sending response: {e}", file=sys.stderr)
    
    def _get_request_info(self) -> Dict[str, Any]:
        """Extract request information safely."""
        try:
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
        except Exception:
            return {
                'method': self.command,
                'url': self.path,
                'path': self.path,
                'query': '',
                'query_params': {},
                'headers': {},
            }
    
    def do_GET(self):
        """Handle GET requests safely."""
        request_data = self._get_request_info()
        path = request_data['path']
        
        if path == '/get':
            self._safe_send_response(200, request_data)
        elif path == '/json':
            self._safe_send_response(200, {
                'test': 'data',
                'number': 42,
                'boolean': True,
                'null_value': None,
                'nested': {'key': 'value', 'items': [1, 2, 3]}
            })
        elif path == '/headers':
            self._safe_send_response(200, {'headers': request_data['headers']})
        elif path == '/user-agent':
            user_agent = request_data['headers'].get('User-Agent', 'Unknown')
            self._safe_send_response(200, {'user-agent': user_agent})
        elif path.startswith('/status/'):
            try:
                status_code = int(path.split('/')[-1])
                self._safe_send_response(status_code, {
                    'status': status_code,
                    'message': f'HTTP {status_code}'
                })
            except ValueError:
                self._safe_send_response(404, {'error': 'Invalid status code'})
        elif path == '/redirect':
            try:
                self.send_response(302)
                self.send_header('Location', '/get')
                self.send_header('Connection', 'close')
                self.end_headers()
            except (BrokenPipeError, ConnectionResetError, OSError):
                pass
        elif path == '/cookies':
            cookies = {}
            cookie_header = self.headers.get('Cookie', '')
            if cookie_header:
                for cookie in cookie_header.split(';'):
                    if '=' in cookie:
                        key, value = cookie.strip().split('=', 1)
                        cookies[key] = value
            self._safe_send_response(200, {'cookies': cookies})
        else:
            self._safe_send_response(404, {'error': 'Not Found', 'path': path})
    
    def do_POST(self):
        """Handle POST requests safely."""
        request_data = self._get_request_info()
        path = request_data['path']
        
        try:
            # Read request body safely
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = b''
            if content_length > 0:
                post_data = self.rfile.read(content_length)
            
            request_data['data'] = post_data.decode('utf-8', errors='ignore') if post_data else ''
            request_data['content_length'] = content_length
            
            # Parse JSON if content type is application/json
            if self.headers.get('Content-Type') == 'application/json':
                try:
                    request_data['json'] = json.loads(post_data.decode())
                except (json.JSONDecodeError, UnicodeDecodeError):
                    request_data['json'] = None
            
            if path == '/post':
                self._safe_send_response(200, request_data)
            elif path == '/echo':
                self._safe_send_response(200, {
                    'echoed': request_data,
                    'received_data': request_data.get('json') or request_data.get('data')
                })
            else:
                self._safe_send_response(404, {'error': 'Not Found', 'path': path})
        
        except Exception:
            # If anything goes wrong, send a simple response
            self._safe_send_response(500, {'error': 'Internal Server Error'})
    
    def do_PUT(self):
        """Handle PUT requests."""
        self.do_POST()  # Same logic as POST
    
    def do_PATCH(self):
        """Handle PATCH requests."""
        self.do_POST()  # Same logic as POST
    
    def do_DELETE(self):
        """Handle DELETE requests safely."""
        request_data = self._get_request_info()
        path = request_data['path']
        
        if path == '/delete':
            self._safe_send_response(200, request_data)
        else:
            self._safe_send_response(404, {'error': 'Not Found', 'path': path})
    
    def do_HEAD(self):
        """Handle HEAD requests safely."""
        path = urlparse(self.path).path
        
        try:
            if path == '/head':
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('X-Test-Header', 'test-value')
                self.send_header('Connection', 'close')
                self.end_headers()
            else:
                self.send_response(404)
                self.send_header('Connection', 'close')
                self.end_headers()
        except (BrokenPipeError, ConnectionResetError, OSError):
            pass
    
    def do_OPTIONS(self):
        """Handle OPTIONS requests safely."""
        path = urlparse(self.path).path
        
        if path == '/options':
            self._safe_send_response(200, {
                'method': 'OPTIONS',
                'allowed_methods': ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'HEAD', 'OPTIONS']
            }, {'Allow': 'GET, POST, PUT, PATCH, DELETE, HEAD, OPTIONS'})
        else:
            self._safe_send_response(404, {'error': 'Not Found'})


class StableHTTPServer:
    """Stable HTTP server that handles connection issues gracefully."""
    
    def __init__(self, host=None, port=0):
        # 确保服务器和客户端使用兼容的地址
        if host is not None:
            # 如果指定了host，直接使用
            bind_host = host
            client_host = host
        else:
            # 自动选择在当前环境中可工作的地址
            working_host = get_working_localhost_address()
            bind_host = working_host
            client_host = working_host
        
        # Use SO_REUSEADDR to avoid "Address already in use" errors
        self.server = HTTPServer((bind_host, port), StableHTTPRequestHandler)
        self.server.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        self.bind_host = bind_host
        self.port = self.server.server_address[1]
        self.client_host = client_host
        self.base_url = f"http://{self.client_host}:{self.port}"
        
        self.thread = None
        self.running = False
    
    def start(self):
        """Start the server in a background thread."""
        if not self.running:
            self.thread = threading.Thread(target=self._run_server)
            self.thread.daemon = True
            self.thread.start()
            self.running = True
            
            # Wait for server to start
            max_retries = 10
            for _ in range(max_retries):
                try:
                    # Test if server is responding using the client address
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(1)
                    result = sock.connect_ex((self.client_host, self.port))
                    sock.close()
                    if result == 0:
                        break
                except Exception:
                    pass
                time.sleep(0.1)
    
    def _run_server(self):
        """Run the server, handling shutdown gracefully."""
        try:
            self.server.serve_forever()
        except Exception:
            # Server was shut down
            pass
    
    def stop(self):
        """Stop the server."""
        if self.running:
            self.running = False
            self.server.shutdown()
            self.server.server_close()
            if self.thread and self.thread.is_alive():
                self.thread.join(timeout=1)
    
    def __enter__(self):
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
    
    def url(self, path=''):
        """Get full URL for a path."""
        return f"{self.base_url}{path}"


# Convenience function for pytest fixtures
def create_stable_server():
    """Create and return a stable server instance."""
    return StableHTTPServer()