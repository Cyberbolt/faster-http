"""
Simple HTTP proxy server for testing proxy functionality
"""

import socket
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.request
import urllib.parse
import urllib.error
from socketserver import ThreadingMixIn


class ProxyHandler(BaseHTTPRequestHandler):
    """HTTP proxy request handler"""
    
    def __init__(self, *args, **kwargs):
        self.proxy_requests = []
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        self.handle_request()
    
    def do_POST(self):
        self.handle_request()
    
    def do_PUT(self):
        self.handle_request()
    
    def do_DELETE(self):
        self.handle_request()
    
    def do_HEAD(self):
        self.handle_request()
    
    def do_CONNECT(self):
        """Handle HTTPS CONNECT requests"""
        # For HTTPS proxy, we need to establish a tunnel
        host, port = self.path.split(':')
        port = int(port)
        
        try:
            # Connect to the target server
            target_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            target_socket.connect((host, port))
            
            # Send 200 Connection established
            self.send_response(200, 'Connection established')
            self.end_headers()
            
            # Start tunneling
            self.tunnel_data(self.connection, target_socket)
            
        except Exception as e:
            self.send_error(502, f"Bad Gateway: {str(e)}")
    
    def tunnel_data(self, client_socket, target_socket):
        """Tunnel data between client and target"""
        def forward_data(source, destination):
            try:
                while True:
                    data = source.recv(4096)
                    if not data:
                        break
                    destination.send(data)
            except:
                pass
            finally:
                source.close()
                destination.close()
        
        # Start forwarding in both directions
        client_to_target = threading.Thread(
            target=forward_data, 
            args=(client_socket, target_socket)
        )
        target_to_client = threading.Thread(
            target=forward_data, 
            args=(target_socket, client_socket)
        )
        
        client_to_target.daemon = True
        target_to_client.daemon = True
        
        client_to_target.start()
        target_to_client.start()
        
        # Wait for one direction to finish
        client_to_target.join()
        target_to_client.join()
    
    def handle_request(self):
        """Handle HTTP proxy request"""
        try:
            # Parse the URL
            url = self.path
            if not url.startswith('http'):
                # Relative URL, make it absolute
                url = f"http://{self.headers.get('Host', 'localhost')}{url}"
            
            # Record the request for testing
            request_info = {
                'method': self.command,
                'url': url,
                'headers': dict(self.headers),
                'timestamp': time.time()
            }
            
            # Get request body if present
            content_length = int(self.headers.get('Content-Length', 0))
            request_body = b''
            if content_length > 0:
                request_body = self.rfile.read(content_length)
            
            # Create the request
            req = urllib.request.Request(url, data=request_body, method=self.command)
            
            # Copy headers (except hop-by-hop headers)
            skip_headers = {'connection', 'proxy-connection', 'upgrade', 
                          'proxy-authenticate', 'proxy-authorization', 'te', 
                          'trailers', 'transfer-encoding'}
            
            for header, value in self.headers.items():
                if header.lower() not in skip_headers:
                    req.add_header(header, value)
            
            # Add proxy identification header
            req.add_header('X-Forwarded-By', 'faster-http-test-proxy')
            
            # Make the request
            response = urllib.request.urlopen(req, timeout=30)
            
            # Send response status
            self.send_response(response.getcode())
            
            # Send response headers
            for header, value in response.headers.items():
                if header.lower() not in skip_headers:
                    self.send_header(header, value)
            
            # Add proxy header to indicate request went through proxy
            self.send_header('X-Proxied-By', 'faster-http-test-proxy')
            self.end_headers()
            
            # Send response body
            self.wfile.write(response.read())
            
        except urllib.error.HTTPError as e:
            self.send_error(e.code, e.reason)
        except Exception as e:
            self.send_error(502, f"Proxy Error: {str(e)}")
    
    def log_message(self, format, *args):
        """Override to reduce logging noise during tests"""
        pass


class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    """Threading HTTP server for handling multiple requests"""
    daemon_threads = True
    allow_reuse_address = True


class TestProxyServer:
    """Test proxy server manager"""
    
    def __init__(self, host='127.0.0.1', port=0):
        self.host = host
        self.port = port
        self.server = None
        self.thread = None
        self.requests = []
    
    def start(self):
        """Start the proxy server"""
        self.server = ThreadingHTTPServer((self.host, self.port), ProxyHandler)
        self.port = self.server.server_address[1]  # Get actual port if 0 was specified
        
        self.thread = threading.Thread(target=self.server.serve_forever)
        self.thread.daemon = True
        self.thread.start()
        
        # Wait a bit for server to start
        time.sleep(0.1)
        
        return f"http://{self.host}:{self.port}"
    
    def stop(self):
        """Stop the proxy server"""
        if self.server:
            self.server.shutdown()
            self.server.server_close()
        if self.thread:
            self.thread.join(timeout=1)
    
    def get_proxy_url(self):
        """Get the proxy URL"""
        return f"http://{self.host}:{self.port}"
    
    def __enter__(self):
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()


# Authenticated proxy server
class AuthProxyHandler(ProxyHandler):
    """Proxy handler that requires authentication"""
    
    def handle_request(self):
        """Handle request with authentication check"""
        # Check for Proxy-Authorization header
        auth_header = self.headers.get('Proxy-Authorization')
        
        if not auth_header:
            self.send_response(407, 'Proxy Authentication Required')
            self.send_header('Proxy-Authenticate', 'Basic realm="Test Proxy"')
            self.end_headers()
            return
        
        # Check basic auth (for testing: user:pass = test:proxy)
        import base64
        try:
            auth_type, auth_string = auth_header.split(' ', 1)
            if auth_type.lower() == 'basic':
                decoded = base64.b64decode(auth_string).decode('utf-8')
                username, password = decoded.split(':', 1)
                
                if username == 'test' and password == 'proxy':
                    # Authentication successful, proceed with request
                    super().handle_request()
                    return
        except:
            pass
        
        # Authentication failed
        self.send_response(407, 'Proxy Authentication Required')
        self.send_header('Proxy-Authenticate', 'Basic realm="Test Proxy"')
        self.end_headers()


class AuthTestProxyServer(TestProxyServer):
    """Test proxy server with authentication"""
    
    def start(self):
        """Start the authenticated proxy server"""
        self.server = ThreadingHTTPServer((self.host, self.port), AuthProxyHandler)
        self.port = self.server.server_address[1]
        
        self.thread = threading.Thread(target=self.server.serve_forever)
        self.thread.daemon = True
        self.thread.start()
        
        time.sleep(0.1)
        return f"http://test:proxy@{self.host}:{self.port}"


if __name__ == "__main__":
    # Test the proxy server
    print("Starting test proxy server...")
    
    with TestProxyServer() as proxy:
        proxy_url = proxy.get_proxy_url()
        print(f"Proxy server running at: {proxy_url}")
        print("Press Ctrl+C to stop")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping proxy server...")