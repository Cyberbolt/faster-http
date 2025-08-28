"""
Local test HTTP server for faster-http testing.

This module provides a lightweight HTTP test server that supports various
scenarios for testing HTTP client functionality without depending on external services.

Now uses FastAPI for enhanced performance and reliability.
"""

import pytest

# Import FastAPI-based implementation
from tests.utils.fastapi_test_server import FastAPITestServer

# For backward compatibility, create an alias
HTTPTestServer = FastAPITestServer


# Global test server instance
_test_server_instance = None


@pytest.fixture(scope="session")
def test_server():
    """Pytest fixture providing a test server for the entire test session."""
    global _test_server_instance

    if _test_server_instance is None:
        _test_server_instance = HTTPTestServer()
        _test_server_instance.start()

    yield _test_server_instance

    # Cleanup happens at session end
    if _test_server_instance:
        _test_server_instance.stop()
        _test_server_instance = None


@pytest.fixture
def local_server():
    """Pytest fixture providing a local test server for individual tests."""
    server = HTTPTestServer()
    server.start()
    yield server
    server.stop()
