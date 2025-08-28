"""
Tests for HTTPS/TLS support in faster-http.

This module tests TLS/SSL functionality to ensure HTTPS requests work correctly
with faster-http after restoring TLS dependencies.
"""

from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
import ssl
import tempfile
import threading

import pytest

from tests.utils.httpx_comparison import httpx_compatibility_test


class HTTPSTestServer:
    """Simple HTTPS test server for testing TLS functionality."""

    def __init__(self):
        self.server = None
        self.thread = None
        self.port = None
        self.cert_file = None
        self.key_file = None

    def create_self_signed_cert(self):
        """Create a self-signed certificate for testing."""
        import datetime
        import ipaddress

        from cryptography import x509
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.x509.oid import NameOID

        # Generate private key
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )

        # Create certificate
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "CA"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "San Francisco"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Test"),
            x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
        ])

        cert = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(private_key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.datetime.now(datetime.timezone.utc))
            .not_valid_after(datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=1))
            .add_extension(
                x509.SubjectAlternativeName([
                    x509.DNSName("localhost"),
                    x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
                ]),
                critical=False,
            )
            .sign(private_key, hashes.SHA256())
        )

        # Write certificate and key to temporary files
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.crt') as cert_temp:
            cert_temp.write(cert.public_bytes(serialization.Encoding.PEM))
            cert_file_name = cert_temp.name

        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.key') as key_temp:
            key_temp.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ))
            key_file_name = key_temp.name

        self.cert_file = cert_file_name
        self.key_file = key_file_name

        return cert_file_name, key_file_name

    def start(self):
        """Start the HTTPS test server."""
        # Create self-signed certificate
        try:
            self.create_self_signed_cert()
        except ImportError:
            # If cryptography is not available, skip HTTPS tests
            pytest.skip("cryptography package not available for HTTPS testing")

        # Find available port
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(('localhost', 0))
        self.port = sock.getsockname()[1]
        sock.close()

        # Create HTTPS server
        class TestHandler(SimpleHTTPRequestHandler):
            def log_message(self, format, *args):
                pass  # Suppress logging

            def do_GET(self):
                if self.path == '/get':
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(b'{"url": "https://localhost/get", "method": "GET"}')
                elif self.path == '/status/200':
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(b'{"status": "ok"}')
                else:
                    self.send_response(404)
                    self.end_headers()

        self.server = HTTPServer(('localhost', self.port), TestHandler)

        # Create SSL context
        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        context.load_cert_chain(self.cert_file, self.key_file)
        self.server.socket = context.wrap_socket(self.server.socket, server_side=True)

        # Start server in background thread
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

        return f"https://localhost:{self.port}"

    def stop(self):
        """Stop the HTTPS test server."""
        if self.server:
            self.server.shutdown()
            self.server.server_close()
        if self.thread:
            self.thread.join(timeout=1)

        # Cleanup certificate files
        if self.cert_file:
            Path(self.cert_file).unlink(missing_ok=True)
        if self.key_file:
            Path(self.key_file).unlink(missing_ok=True)


@pytest.fixture(scope="class")
def https_server():
    """HTTPS test server fixture."""
    server = HTTPSTestServer()
    base_url = server.start()
    yield base_url
    server.stop()


class TestHTTPSSupport:
    """Test HTTPS/TLS support in faster-http."""

    @httpx_compatibility_test
    def test_https_get_request(self, client_factory, https_server):
        """Test basic HTTPS GET request."""
        try:
            # For HTTPS testing, we need to disable SSL verification for self-signed certs
            if client_factory.library == "httpx":
                import httpx
                client = httpx.Client(verify=False)
                response = client.get(f"{https_server}/get")
                client.close()
            else:
                # faster_http should also support verify=False parameter
                import faster_http
                response = faster_http.get(f"{https_server}/get", verify=False)

            assert response.status_code == 200
            # Basic validation that we got a response
            assert "url" in response.json() or response.json()

        except Exception as e:
            if "SSL" in str(e) or "TLS" in str(e) or "certificate" in str(e).lower():
                pytest.fail(f"HTTPS/TLS support failed: {e}")
            else:
                # Re-raise other exceptions
                raise

    @httpx_compatibility_test
    def test_https_status_codes(self, client_factory, https_server):
        """Test HTTPS requests return correct status codes."""
        try:
            if client_factory.library == "httpx":
                import httpx
                client = httpx.Client(verify=False)
                response = client.get(f"{https_server}/status/200")
                client.close()
            else:
                import faster_http
                response = faster_http.get(f"{https_server}/status/200", verify=False)

            assert response.status_code == 200

        except Exception as e:
            if "SSL" in str(e) or "TLS" in str(e) or "certificate" in str(e).lower():
                pytest.fail(f"HTTPS/TLS support failed: {e}")
            else:
                raise

    def test_https_client_creation(self):
        """Test that HTTPS-capable clients can be created."""
        try:
            import faster_http

            # Test that we can create a client that supports HTTPS
            client = faster_http.Client(verify=False)
            assert client is not None
            client.close()

            # Test async client as well
            import asyncio
            async def test_async_client():
                async_client = faster_http.AsyncClient(verify=False)
                assert async_client is not None
                await async_client.aclose()

            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            loop.run_until_complete(test_async_client())

        except ImportError:
            pytest.skip("faster_http not available")
        except Exception as e:
            if "SSL" in str(e) or "TLS" in str(e):
                pytest.fail(f"Failed to create HTTPS-capable client: {e}")
            else:
                raise

    def test_tls_verification_support(self):
        """Test that TLS certificate verification can be controlled."""
        try:
            import faster_http

            # Test that verify parameter is accepted
            # This doesn't make actual requests, just tests parameter handling
            client1 = faster_http.Client(verify=True)
            assert client1 is not None
            client1.close()

            client2 = faster_http.Client(verify=False)
            assert client2 is not None
            client2.close()

        except ImportError:
            pytest.skip("faster_http not available")
        except Exception as e:
            pytest.fail(f"TLS verification parameter handling failed: {e}")
