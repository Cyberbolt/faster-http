"""
Simple HTTP test server for faster-http testing.

This module provides a simple and reliable HTTP test server using Python's
built-in http.server module, optimized for testing HTTP client functionality.
"""

import base64
import hashlib
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import random
import socket
from socketserver import ThreadingMixIn
import threading
import time
import urllib.parse


class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    """Thread per request HTTP server."""

    daemon_threads = True
    allow_reuse_address = True


class SimpleHTTPTestHandler(BaseHTTPRequestHandler):
    """Optimized HTTP request handler for test server."""

    def log_message(self, format, *args):
        """Suppress default logging."""

    def _send_response(
        self,
        status_code: int,
        headers: dict[str, str] | None = None,
        content: bytes | None = None,
        content_type: str = "application/json",
    ):
        """Send HTTP response with given parameters."""
        try:
            self.send_response(status_code)

            if headers:
                for key, value in headers.items():
                    self.send_header(key, value)

            if content is not None:
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(len(content)))

            # Important: Always send Connection: close for reliability
            self.send_header("Connection", "close")
            self.end_headers()

            if content is not None:
                self.wfile.write(content)
                self.wfile.flush()

        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            # Client closed connection - ignore these errors
            pass

    def _get_request_data(self) -> dict:
        """Extract request data for response."""
        # Parse query parameters
        parsed_url = urllib.parse.urlparse(self.path)
        query_params = urllib.parse.parse_qs(parsed_url.query)

        # Flatten single-item lists in query params
        args = {}
        for key, values in query_params.items():
            if len(values) == 1:
                args[key] = values[0]
            else:
                args[key] = values

        # Get headers
        headers = dict(self.headers)

        # Get request body
        content_length = int(self.headers.get("Content-Length", 0))
        body = ""
        if content_length > 0:
            try:
                body = self.rfile.read(content_length).decode("utf-8")
            except (UnicodeDecodeError, OSError):
                body = ""

        # Try to parse body as JSON
        json_data = None
        if body and self.headers.get("Content-Type", "").startswith("application/json"):
            try:
                json_data = json.loads(body)
            except json.JSONDecodeError:
                pass

        return {
            "url": f"http://{self.headers.get('Host', 'localhost')}{self.path}",
            "method": self.command,
            "headers": headers,
            "args": args,
            "data": body,
            "json": json_data,
            "origin": self.client_address[0],
        }

    def do_GET(self):
        """Handle GET requests."""
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path

        try:
            # Route to appropriate handler
            if path == "/get":
                self._handle_get()
            elif path == "/json":
                self._handle_json()
            elif path == "/headers":
                self._handle_headers()
            elif path.startswith("/status/"):
                self._handle_status()
            elif path.startswith("/delay/"):
                self._handle_delay()
            elif path.startswith("/redirect/"):
                self._handle_redirect()
            elif path.startswith("/cookies"):
                self._handle_cookies()
            elif path.startswith("/basic-auth/"):
                self._handle_basic_auth()
            elif path.startswith("/digest-auth/"):
                self._handle_digest_auth()
            elif path.startswith("/stream/"):
                self._handle_stream()
            elif path.startswith("/bytes/"):
                self._handle_bytes()
            elif path == "/head":
                self._handle_head()
            elif path == "/options":
                self._handle_options()
            elif path == "/response-headers":
                self._handle_response_headers()
            else:
                self._send_404()
        except Exception:
            # Ignore any errors and close connection
            pass

    def do_POST(self):
        """Handle POST requests."""
        try:
            if self.path == "/post":
                self._handle_post()
            else:
                self._send_404()
        except Exception:
            pass

    def do_PUT(self):
        """Handle PUT requests."""
        try:
            if self.path == "/put":
                self._handle_put()
            else:
                self._send_404()
        except Exception:
            pass

    def do_PATCH(self):
        """Handle PATCH requests."""
        try:
            if self.path == "/patch":
                self._handle_patch()
            else:
                self._send_404()
        except Exception:
            pass

    def do_DELETE(self):
        """Handle DELETE requests."""
        try:
            if self.path == "/delete":
                self._handle_delete()
            else:
                self._send_404()
        except Exception:
            pass

    def do_HEAD(self):
        """Handle HEAD requests."""
        try:
            if self.path == "/head":
                self._handle_head(head_only=True)
            else:
                self._send_404()
        except Exception:
            pass

    def do_OPTIONS(self):
        """Handle OPTIONS requests."""
        try:
            if self.path == "/options":
                self._handle_options()
            else:
                self._send_404()
        except Exception:
            pass

    def _handle_get(self):
        """Handle /get endpoint."""
        data = self._get_request_data()
        content = json.dumps(data, indent=2).encode("utf-8")
        self._send_response(200, content=content)

    def _handle_json(self):
        """Handle /json endpoint - returns sample JSON data."""
        sample_data = {
            "slideshow": {
                "author": "Yours Truly",
                "date": "date of publication",
                "slides": [
                    {"title": "Wake up to WonderWidgets!", "type": "all"},
                    {
                        "items": ["Why <em>WonderWidgets</em> are great", "Who <em>buys</em> WonderWidgets"],
                        "title": "Overview",
                        "type": "all",
                    },
                ],
                "title": "Sample Slide Show",
            }
        }
        content = json.dumps(sample_data).encode("utf-8")
        self._send_response(200, content=content)

    def _handle_headers(self):
        """Handle /headers endpoint."""
        data = {"headers": dict(self.headers)}
        content = json.dumps(data, indent=2).encode("utf-8")
        self._send_response(200, content=content)

    def _handle_post(self):
        """Handle /post endpoint."""
        data = self._get_request_data()
        content = json.dumps(data, indent=2).encode("utf-8")
        self._send_response(200, content=content)

    def _handle_put(self):
        """Handle /put endpoint."""
        data = self._get_request_data()
        content = json.dumps(data, indent=2).encode("utf-8")
        self._send_response(200, content=content)

    def _handle_patch(self):
        """Handle /patch endpoint."""
        data = self._get_request_data()
        content = json.dumps(data, indent=2).encode("utf-8")
        self._send_response(200, content=content)

    def _handle_delete(self):
        """Handle /delete endpoint."""
        data = self._get_request_data()
        content = json.dumps(data, indent=2).encode("utf-8")
        self._send_response(200, content=content)

    def _handle_head(self, head_only=False):
        """Handle /head endpoint."""
        headers = {"X-Test-Header": "test-value", "Content-Type": "application/json"}
        if head_only:
            self._send_response(200, headers=headers)
        else:
            content = json.dumps({"message": "HEAD response"}).encode("utf-8")
            self._send_response(200, headers=headers, content=content)

    def _handle_options(self):
        """Handle /options endpoint."""
        headers = {
            "Allow": "GET, POST, PUT, PATCH, DELETE, HEAD, OPTIONS",
            "Access-Control-Allow-Methods": "GET, POST, PUT, PATCH, DELETE, HEAD, OPTIONS",
        }
        content = json.dumps({"message": "OPTIONS response"}).encode("utf-8")
        self._send_response(200, headers=headers, content=content)

    def _handle_status(self):
        """Handle /status/<code> endpoint."""
        try:
            status_code = int(self.path.split("/")[-1])
            if status_code == 200:
                content = json.dumps({"status": status_code}).encode("utf-8")
                self._send_response(status_code, content=content)
            else:
                self._send_response(status_code)
        except ValueError:
            self._send_404()

    def _handle_delay(self):
        """Handle /delay/<seconds> endpoint."""
        try:
            delay_seconds = min(float(self.path.split("/")[-1]), 5.0)  # Max 5 second delay
            time.sleep(delay_seconds)
            content = json.dumps({"delay": delay_seconds}).encode("utf-8")
            self._send_response(200, content=content)
        except ValueError:
            self._send_404()

    def _handle_redirect(self):
        """Handle /redirect/<count> endpoint."""
        try:
            count = int(self.path.split("/")[-1])
            if count <= 0:
                # End of redirects
                content = json.dumps({"redirected": True}).encode("utf-8")
                self._send_response(200, content=content)
            else:
                # Redirect to next count
                location = f"/redirect/{count - 1}"
                headers = {"Location": location}
                self._send_response(302, headers=headers)
        except ValueError:
            self._send_404()

    def _handle_cookies(self):
        """Handle cookies endpoints."""
        if self.path.startswith("/cookies/set/"):
            # Set cookie: /cookies/set/<name>/<value>
            parts = self.path.split("/")
            if len(parts) >= 5:
                name = parts[3]
                value = parts[4]
                headers = {"Set-Cookie": f"{name}={value}; Path=/", "Location": "/cookies"}
                self._send_response(302, headers=headers)
            else:
                self._send_404()
        elif self.path == "/cookies":
            # Return current cookies
            cookie_header = self.headers.get("Cookie", "")
            cookies = {}

            if cookie_header:
                for item in cookie_header.split(";"):
                    if "=" in item:
                        key, value = item.strip().split("=", 1)
                        cookies[key] = value

            data = {"cookies": cookies}
            content = json.dumps(data, indent=2).encode("utf-8")
            self._send_response(200, content=content)
        else:
            self._send_404()

    def _handle_basic_auth(self):
        """Handle /basic-auth/<user>/<passwd> endpoint."""
        parts = self.path.split("/")
        if len(parts) >= 4:
            expected_user = parts[2]
            expected_password = parts[3]

            auth_header = self.headers.get("Authorization", "")

            if auth_header.startswith("Basic "):
                try:
                    credentials = base64.b64decode(auth_header[6:]).decode("utf-8")
                    username, password = credentials.split(":", 1)

                    if username == expected_user and password == expected_password:
                        data = {"authenticated": True, "user": username}
                        content = json.dumps(data).encode("utf-8")
                        self._send_response(200, content=content)
                    else:
                        self._send_response(401, headers={"WWW-Authenticate": 'Basic realm="Test"'})
                except Exception:
                    self._send_response(401, headers={"WWW-Authenticate": 'Basic realm="Test"'})
            else:
                self._send_response(401, headers={"WWW-Authenticate": 'Basic realm="Test"'})
        else:
            self._send_404()

    def _handle_digest_auth(self):
        """Handle /digest-auth/<qop>/<user>/<passwd> endpoint."""
        parts = self.path.split("/")
        if len(parts) >= 5:
            qop = parts[2]
            expected_user = parts[3]

            auth_header = self.headers.get("Authorization", "")

            if auth_header.startswith("Digest "):
                # For simplicity, just check if digest auth is attempted
                data = {"authenticated": True, "user": expected_user}
                content = json.dumps(data).encode("utf-8")
                self._send_response(200, content=content)
            else:
                # Send digest challenge
                nonce = hashlib.md5(str(random.random()).encode()).hexdigest()
                challenge = f'Digest realm="Test", nonce="{nonce}", qop="{qop}"'
                self._send_response(401, headers={"WWW-Authenticate": challenge})
        else:
            self._send_404()

    def _handle_stream(self):
        """Handle /stream/<count> endpoint."""
        try:
            count = min(int(self.path.split("/")[-1]), 100)  # Max 100 lines

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Connection", "close")
            self.end_headers()

            for i in range(count):
                try:
                    line = json.dumps({"line": i, "data": f"Line {i} data"}) + "\n"
                    self.wfile.write(line.encode("utf-8"))
                    self.wfile.flush()
                    time.sleep(0.005)  # Very small delay
                except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
                    # Client closed connection
                    break

        except ValueError:
            self._send_404()

    def _handle_bytes(self):
        """Handle /bytes/<count> endpoint."""
        try:
            count = min(int(self.path.split("/")[-1]), 10240)  # Max 10KB
            # Generate random bytes
            content = bytes(random.randint(0, 255) for _ in range(count))
            self._send_response(200, content=content, content_type="application/octet-stream")
        except ValueError:
            self._send_404()

    def _handle_response_headers(self):
        """Handle /response-headers endpoint with custom headers via query params."""
        parsed_url = urllib.parse.urlparse(self.path)
        query_params = urllib.parse.parse_qs(parsed_url.query)

        # Build custom headers from query parameters
        custom_headers = {}
        for key, values in query_params.items():
            if values:
                custom_headers[key] = values[0]  # Take first value

        data = {
            "url": f"http://{self.headers.get('Host', 'localhost')}{self.path}",
            "headers": custom_headers,
            "method": "GET",
        }

        content = json.dumps(data, indent=2).encode("utf-8")
        self._send_response(200, headers=custom_headers, content=content)

    def _send_404(self):
        """Send 404 Not Found response."""
        content = json.dumps({"error": "Not Found"}).encode("utf-8")
        self._send_response(404, content=content)


class SimpleHTTPTestServer:
    """Simple HTTP test server for testing HTTP client libraries."""

    def __init__(self, host: str = "127.0.0.1", port: int = 0):
        """
        Initialize simple test server.

        Args:
            host: Server host (default: 127.0.0.1)
            port: Server port (default: 0 for auto-assignment)
        """
        self.host = host
        self.port = port
        self.server = None
        self.thread = None
        self._started = False

    def start(self) -> None:
        """Start the test server."""
        if self._started:
            return

        try:
            # Use threading server for better performance
            self.server = ThreadingHTTPServer((self.host, self.port), SimpleHTTPTestHandler)

            # Set socket options for better reliability
            self.server.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            # Set timeout to prevent hanging connections
            self.server.timeout = 10.0

            # Get the actual port if auto-assigned
            self.port = self.server.server_address[1]

            # Start server in background thread
            self.thread = threading.Thread(target=self._serve_with_error_handling, daemon=True)
            self.thread.start()

            self._started = True

            # Wait for server to start
            time.sleep(0.1)

            # Verify server is actually responding
            for _ in range(20):  # Try up to 2 seconds total
                try:
                    test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    test_socket.settimeout(0.1)
                    result = test_socket.connect_ex((self.host, self.port))
                    test_socket.close()
                    if result == 0:
                        break  # Server is responding
                except Exception:
                    pass
                time.sleep(0.1)
            else:
                raise RuntimeError(f"Simple test server failed to start properly on {self.host}:{self.port}")

        except Exception as e:
            print(f"Failed to start simple test server: {e}")
            raise

    def stop(self) -> None:
        """Stop the test server."""
        if not self._started:
            return

        try:
            if self.server:
                self.server.shutdown()
                self.server.server_close()

            if self.thread and self.thread.is_alive():
                self.thread.join(timeout=1.0)
        except Exception:
            # Ignore errors during shutdown
            pass
        finally:
            self._started = False

    def _serve_with_error_handling(self):
        """Serve requests with proper error handling."""
        try:
            self.server.serve_forever()
        except Exception:
            # Log error but don't crash the test
            pass

    @property
    def base_url(self) -> str:
        """Get the base URL of the test server."""
        return f"http://{self.host}:{self.port}"

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()


# For backward compatibility, create an alias
HTTPTestServer = SimpleHTTPTestServer
