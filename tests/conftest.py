"""
Global pytest configuration and fixtures for faster-http tests.

This file provides shared fixtures and configuration that are available
to all test modules in the faster-http test suite.
"""

import asyncio
import os
from pathlib import Path
import sys

import pytest

# Add project root to Python path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

# Import test utilities after path setup
# These imports are done after sys.path modification for proper module loading
from tests.utils.httpx_comparison import AsyncClientFactory, ClientFactory  # noqa: E402
from tests.utils.tdd_framework import SimpleAsyncClientFactory, SimpleClientFactory  # noqa: E402
from tests.utils.tdd_helpers import AssertionHelpers, DataGenerator, ErrorSimulator, PerformanceMeasurer  # noqa: E402
from tests.utils.test_server import TestServer  # noqa: E402

# ============================================================================
# Session-scoped fixtures
# ============================================================================


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for the entire test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_server():
    """Session-wide test server for all tests."""
    server = TestServer()
    server.start()
    yield server
    server.stop()


# ============================================================================
# Module-scoped fixtures
# ============================================================================


@pytest.fixture(scope="module")
def module_server():
    """Module-scoped test server."""
    server = TestServer()
    server.start()
    yield server
    server.stop()


# ============================================================================
# Function-scoped fixtures
# ============================================================================


@pytest.fixture
def local_server():
    """Local test server for individual tests."""
    server = TestServer()
    server.start()
    yield server
    server.stop()


@pytest.fixture
def client_factory():
    """Factory for creating HTTP clients."""
    return ClientFactory("faster_http")


@pytest.fixture
def async_client_factory():
    """Factory for creating async HTTP clients."""
    return AsyncClientFactory("faster_http")


@pytest.fixture
def httpx_client_factory():
    """Factory for creating httpx clients for comparison."""
    return ClientFactory("httpx")


@pytest.fixture
def httpx_async_client_factory():
    """Factory for creating httpx async clients for comparison."""
    return AsyncClientFactory("httpx")


# ============================================================================
# TDD Helper fixtures
# ============================================================================


@pytest.fixture
def data_generator():
    """Data generator for creating test data."""
    return DataGenerator()


@pytest.fixture
def error_simulator():
    """Error simulator for testing error conditions."""
    return ErrorSimulator()


@pytest.fixture
def performance_measurer():
    """Performance measurement utilities."""
    return PerformanceMeasurer()


@pytest.fixture
def assert_helpers():
    """Additional assertion helpers."""
    return AssertionHelpers()


# ============================================================================
# TDD-specific fixtures
# ============================================================================


@pytest.fixture
def tdd_client():
    """Simple client factory for TDD tests."""
    return SimpleClientFactory()


@pytest.fixture
def tdd_async_client():
    """Simple async client factory for TDD tests."""
    return SimpleAsyncClientFactory()


# ============================================================================
# Test environment fixtures
# ============================================================================


@pytest.fixture
def temp_dir(tmp_path):
    """Temporary directory for test files."""
    return tmp_path


@pytest.fixture
def test_files(temp_dir):
    """Create sample test files."""
    files = {}

    # Text file
    text_file = temp_dir / "test.txt"
    text_file.write_text("This is a test file content")
    files["text"] = text_file

    # JSON file
    json_file = temp_dir / "test.json"
    json_file.write_text('{"key": "value", "number": 123}')
    files["json"] = json_file

    # Binary file
    binary_file = temp_dir / "test.bin"
    binary_file.write_bytes(b"\x00\x01\x02\x03\x04\x05")
    files["binary"] = binary_file

    return files


# ============================================================================
# Environment configuration
# ============================================================================


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Setup test environment before each test."""
    # Set environment variables for testing
    os.environ["FASTER_HTTP_TEST_MODE"] = "true"

    # Clean up after test
    yield

    # Cleanup environment
    if "FASTER_HTTP_TEST_MODE" in os.environ:
        del os.environ["FASTER_HTTP_TEST_MODE"]


# ============================================================================
# Markers and test configuration
# ============================================================================


def pytest_configure(config):
    """Configure pytest with custom markers and settings."""
    config.addinivalue_line("markers", "slow: mark test as slow running")
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "unit: mark test as unit test")
    config.addinivalue_line("markers", "compatibility: mark test as httpx compatibility test")
    config.addinivalue_line("markers", "performance: mark test as performance test")
    config.addinivalue_line("markers", "network: mark test as requiring network access")
    config.addinivalue_line("markers", "auth: mark test as testing authentication")
    config.addinivalue_line("markers", "tdd_red: mark test as TDD red phase (expected to fail)")


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add automatic markers."""
    for item in items:
        # Auto-mark tests based on file location
        if "unit/" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration/" in str(item.fspath):
            item.add_marker(pytest.mark.integration)

        # Auto-mark slow tests
        if "performance" in str(item.fspath) or "benchmark" in item.name:
            item.add_marker(pytest.mark.slow)

        # Auto-mark compatibility tests
        if hasattr(item, "function") and hasattr(item.function, "_httpx_compatibility_test"):
            item.add_marker(pytest.mark.compatibility)


# ============================================================================
# Utility fixtures for specific test scenarios
# ============================================================================


@pytest.fixture
def auth_credentials():
    """Sample authentication credentials for testing."""
    return {
        "basic": {"username": "testuser", "password": "testpass"},
        "digest": {"username": "digestuser", "password": "digestpass"},
        "bearer": {"token": "test-bearer-token-123"},
    }


@pytest.fixture
def sample_urls(test_server):
    """Sample URLs for testing."""
    base = test_server.base_url
    return {
        "get": f"{base}/get",
        "post": f"{base}/post",
        "put": f"{base}/put",
        "patch": f"{base}/patch",
        "delete": f"{base}/delete",
        "head": f"{base}/head",
        "options": f"{base}/options",
        "json": f"{base}/json",
        "headers": f"{base}/headers",
        "status": lambda code: f"{base}/status/{code}",
        "delay": lambda seconds: f"{base}/delay/{seconds}",
        "redirect": lambda count: f"{base}/redirect/{count}",
        "cookies": f"{base}/cookies",
        "basic_auth": lambda user, pwd: f"{base}/basic-auth/{user}/{pwd}",
        "digest_auth": lambda qop, user, pwd: f"{base}/digest-auth/{qop}/{user}/{pwd}",
        "stream": lambda count: f"{base}/stream/{count}",
        "bytes": lambda count: f"{base}/bytes/{count}",
    }


@pytest.fixture
def sample_headers():
    """Sample HTTP headers for testing."""
    return {
        "standard": {
            "User-Agent": "faster-http-test/1.0",
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
        "custom": {"X-Test-Header": "test-value", "X-Custom-ID": "123456", "X-Request-Source": "pytest"},
        "auth": {"Authorization": "Bearer test-token-123"},
    }


@pytest.fixture
def sample_json_data():
    """Sample JSON data for testing."""
    return {
        "simple": {"message": "Hello, World!", "timestamp": 1234567890, "success": True},
        "nested": {
            "user": {
                "id": 1,
                "name": "Test User",
                "email": "test@example.com",
                "profile": {"age": 25, "location": "Test City"},
            },
            "metadata": {"version": "1.0", "created_at": "2023-01-01T00:00:00Z"},
        },
        "array": [{"id": 1, "name": "Item 1"}, {"id": 2, "name": "Item 2"}, {"id": 3, "name": "Item 3"}],
    }
