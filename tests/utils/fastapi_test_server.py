"""
FastAPI-based test HTTP server for faster-http testing.

This module provides a FastAPI-based HTTP test server that supports various
scenarios for testing HTTP client functionality without depending on external services.
"""

import asyncio
import base64
import hashlib
import json
import random
import threading
import time
import urllib.parse
from typing import Any, Dict, Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.responses import StreamingResponse


class FastAPITestServer:
    """FastAPI-based test HTTP server for testing HTTP client libraries."""

    def __init__(self, host: str = "127.0.0.1", port: int = 0):
        """
        Initialize FastAPI test server.

        Args:
            host: Server host (default: 127.0.0.1)
            port: Server port (default: 0 for auto-assignment)
        """
        self.host = host
        self.port = port
        self.app = self._create_app()
        self.server = None
        self.thread = None
        self._started = False

    def _create_app(self) -> FastAPI:
        """Create FastAPI application with all endpoints."""
        app = FastAPI(title="FastAPI Test Server")

        @app.middleware("http")
        async def disable_server_header(request: Request, call_next):
            """Disable server header for consistency."""
            response = await call_next(request)
            if "server" in response.headers:
                del response.headers["server"]
            return response

        def _get_request_data(request: Request) -> Dict[str, Any]:
            """Extract request data for response."""
            # Get query parameters
            args = {}
            for key, value in request.query_params.items():
                args[key] = value

            # Get headers
            headers = dict(request.headers)

            return {
                "url": str(request.url),
                "method": request.method,
                "headers": headers,
                "args": args,
                "origin": request.client.host if request.client else "unknown",
            }

        # GET endpoints
        @app.get("/get")
        async def handle_get(request: Request):
            """Handle /get endpoint."""
            data = _get_request_data(request)
            return data

        @app.get("/json")
        async def handle_json():
            """Handle /json endpoint - returns sample JSON data."""
            return {
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

        @app.get("/headers")
        async def handle_headers(request: Request):
            """Handle /headers endpoint."""
            return {"headers": dict(request.headers)}

        # HTTP method endpoints
        @app.post("/post")
        async def handle_post(request: Request):
            """Handle /post endpoint."""
            data = _get_request_data(request)
            # Get request body
            body = await request.body()
            data["data"] = body.decode("utf-8") if body else ""
            
            # Try to parse JSON
            if body and request.headers.get("content-type", "").startswith("application/json"):
                try:
                    data["json"] = json.loads(body)
                except json.JSONDecodeError:
                    data["json"] = None
            else:
                data["json"] = None
                
            return data

        @app.put("/put")
        async def handle_put(request: Request):
            """Handle /put endpoint."""
            data = _get_request_data(request)
            body = await request.body()
            data["data"] = body.decode("utf-8") if body else ""
            
            if body and request.headers.get("content-type", "").startswith("application/json"):
                try:
                    data["json"] = json.loads(body)
                except json.JSONDecodeError:
                    data["json"] = None
            else:
                data["json"] = None
                
            return data

        @app.patch("/patch")
        async def handle_patch(request: Request):
            """Handle /patch endpoint."""
            data = _get_request_data(request)
            body = await request.body()
            data["data"] = body.decode("utf-8") if body else ""
            
            if body and request.headers.get("content-type", "").startswith("application/json"):
                try:
                    data["json"] = json.loads(body)
                except json.JSONDecodeError:
                    data["json"] = None
            else:
                data["json"] = None
                
            return data

        @app.delete("/delete")
        async def handle_delete(request: Request):
            """Handle /delete endpoint."""
            data = _get_request_data(request)
            body = await request.body()
            data["data"] = body.decode("utf-8") if body else ""
            
            if body and request.headers.get("content-type", "").startswith("application/json"):
                try:
                    data["json"] = json.loads(body)
                except json.JSONDecodeError:
                    data["json"] = None
            else:
                data["json"] = None
                
            return data

        @app.head("/head")
        async def handle_head():
            """Handle /head endpoint."""
            return Response(headers={"X-Test-Header": "test-value"})

        @app.options("/options")
        async def handle_options():
            """Handle /options endpoint."""
            headers = {
                "Allow": "GET, POST, PUT, PATCH, DELETE, HEAD, OPTIONS",
                "Access-Control-Allow-Methods": "GET, POST, PUT, PATCH, DELETE, HEAD, OPTIONS",
            }
            return Response(content=json.dumps({"message": "OPTIONS response"}), headers=headers)

        # Status endpoint
        @app.get("/status/{status_code}")
        async def handle_status(status_code: int):
            """Handle /status/<code> endpoint."""
            if status_code == 200:
                return {"status": status_code}
            else:
                raise HTTPException(status_code=status_code)

        # Delay endpoint
        @app.get("/delay/{delay_seconds}")
        async def handle_delay(delay_seconds: float):
            """Handle /delay/<seconds> endpoint."""
            await asyncio.sleep(delay_seconds)
            return {"delay": delay_seconds}

        # Redirect endpoint
        @app.get("/redirect/{count}")
        async def handle_redirect(count: int, response: Response):
            """Handle /redirect/<count> endpoint."""
            if count <= 0:
                return {"redirected": True}
            else:
                response.status_code = status.HTTP_302_FOUND
                response.headers["Location"] = f"/redirect/{count - 1}"
                return response

        # Cookies endpoints
        @app.get("/cookies/set/{name}/{value}")
        async def set_cookie(name: str, value: str, response: Response):
            """Set cookie endpoint."""
            response.set_cookie(key=name, value=value, path="/")
            response.status_code = status.HTTP_302_FOUND
            response.headers["Location"] = "/cookies"
            return response

        @app.get("/cookies")
        async def get_cookies(request: Request):
            """Get cookies endpoint."""
            return {"cookies": dict(request.cookies)}

        # Basic auth endpoint
        @app.get("/basic-auth/{username}/{password}")
        async def handle_basic_auth(username: str, password: str, request: Request):
            """Handle /basic-auth/<user>/<passwd> endpoint."""
            auth_header = request.headers.get("authorization", "")
            
            if not auth_header.startswith("Basic "):
                raise HTTPException(
                    status_code=401,
                    headers={"WWW-Authenticate": 'Basic realm="Test"'}
                )
            
            try:
                credentials = base64.b64decode(auth_header[6:]).decode("utf-8")
                auth_username, auth_password = credentials.split(":", 1)
                
                if auth_username == username and auth_password == password:
                    return {"authenticated": True, "user": auth_username}
                else:
                    raise HTTPException(
                        status_code=401,
                        headers={"WWW-Authenticate": 'Basic realm="Test"'}
                    )
            except Exception:
                raise HTTPException(
                    status_code=401,
                    headers={"WWW-Authenticate": 'Basic realm="Test"'}
                )

        # Digest auth endpoint
        @app.get("/digest-auth/{qop}/{username}/{password}")
        async def handle_digest_auth(qop: str, username: str, password: str, request: Request):
            """Handle /digest-auth/<qop>/<user>/<passwd> endpoint."""
            auth_header = request.headers.get("authorization", "")
            
            if auth_header.startswith("Digest "):
                # Simplified digest auth - just check if digest auth is attempted
                return {"authenticated": True, "user": username}
            else:
                # Send digest challenge
                nonce = hashlib.md5(str(random.random()).encode()).hexdigest()
                challenge = f'Digest realm="Test", nonce="{nonce}", qop="{qop}"'
                raise HTTPException(
                    status_code=401,
                    headers={"WWW-Authenticate": challenge}
                )

        # Stream endpoint
        @app.get("/stream/{count}")
        async def handle_stream(count: int):
            """Handle /stream/<count> endpoint."""
            async def generate_stream():
                for i in range(count):
                    line = json.dumps({"line": i, "data": f"Line {i} data"}) + "\n"
                    yield line.encode("utf-8")
                    await asyncio.sleep(0.01)  # Small delay
            
            return StreamingResponse(generate_stream(), media_type="application/json")

        # Bytes endpoint
        @app.get("/bytes/{count}")
        async def handle_bytes(count: int):
            """Handle /bytes/<count> endpoint."""
            content = bytes(random.randint(0, 255) for _ in range(count))
            return Response(content=content, media_type="application/octet-stream")

        return app

    def start(self) -> None:
        """Start the FastAPI test server."""
        if self._started:
            return

        try:
            import asyncio
            
            # Create server manually for better control
            import socket
            if self.port == 0:
                # Find available port manually
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.bind((self.host, 0))
                self.port = sock.getsockname()[1]
                sock.close()
            
            config = uvicorn.Config(
                self.app,
                host=self.host,
                port=self.port,
                log_level="critical",  # Reduce logging even more
                access_log=False,      # Disable access logging
                server_header=False,   # Disable server header
                date_header=False,     # Disable date header
            )
            
            self.server = uvicorn.Server(config)
            
            # Start server in background thread
            def run_server():
                try:
                    asyncio.run(self.server.serve())
                except Exception as e:
                    print(f"Server thread error: {e}")
            
            self.thread = threading.Thread(target=run_server, daemon=True)
            self.thread.start()
            
            # Wait for server to start with better checking
            start_time = time.time()
            max_wait = 10.0
            
            while (time.time() - start_time) < max_wait:
                if self.server.started:
                    break
                time.sleep(0.01)
            else:
                raise RuntimeError(f"FastAPI test server failed to start within {max_wait} seconds")
            
            self._started = True
            
            # Verify server is responding with socket test
            for attempt in range(50):  # Try up to 5 seconds
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
                raise RuntimeError(f"FastAPI test server not responding on {self.host}:{self.port}")
            
        except Exception as e:
            print(f"Failed to start FastAPI test server: {e}")
            raise

    def stop(self) -> None:
        """Stop the FastAPI test server."""
        if not self._started:
            return

        try:
            if self.server:
                self.server.should_exit = True
                
            if self.thread and self.thread.is_alive():
                self.thread.join(timeout=1.0)
        except Exception:
            # Ignore errors during shutdown
            pass
        finally:
            self._started = False

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


# For backward compatibility, we can create an alias
HTTPTestServer = FastAPITestServer