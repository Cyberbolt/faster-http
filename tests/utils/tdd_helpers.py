"""
TDD (Test-Driven Development) helper utilities for faster-http testing.

This module provides utilities to support the red-green-refactor cycle
and streamline TDD practices in faster-http development.
"""

from collections.abc import Callable
from contextlib import contextmanager
import functools
import json
import random
import string
import time
from unittest.mock import Mock, patch

import pytest


class TDDTestCase:
    """Base class for TDD test cases with helper methods."""

    @staticmethod
    def fail_first_run():
        """Helper to make tests fail on first run (Red phase)."""
        # This can be overridden by environment variable for CI/CD
        import os

        if os.getenv("TDD_SKIP_RED_PHASE", "false").lower() == "true":
            pytest.skip("Skipping red phase for CI/CD")

        # Fail the first time this test runs
        pytest.fail("TDD Red phase: This test should fail initially")

    @staticmethod
    def expect_failure(func: Callable) -> Callable:
        """Decorator to expect test failure in red phase."""

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                # If test passes when it should fail, that's also a failure
                pytest.fail("Test passed when it should fail in red phase")
                return result
            except AssertionError:
                # Expected failure in red phase
                pytest.skip("Expected failure in TDD red phase")
            except Exception as e:
                # Unexpected error
                pytest.fail(f"Unexpected error in red phase: {e}")

        return wrapper


class DataGenerator:
    """Generate test data for various HTTP testing scenarios."""

    @staticmethod
    def random_string(length: int = 10, charset: str = string.ascii_letters + string.digits) -> str:
        """Generate a random string of specified length."""
        return "".join(random.choice(charset) for _ in range(length))

    @staticmethod
    def random_email() -> str:
        """Generate a random email address."""
        username = DataGenerator.random_string(8)
        domain = DataGenerator.random_string(6)
        return f"{username}@{domain}.com"

    @staticmethod
    def random_url(scheme: str = "https", path: str | None = None) -> str:
        """Generate a random URL."""
        domain = DataGenerator.random_string(8).lower()
        if path is None:
            path = "/" + "/".join(DataGenerator.random_string(6) for _ in range(random.randint(1, 3)))
        return f"{scheme}://{domain}.com{path}"

    @staticmethod
    def random_json_data(complexity: str = "simple") -> dict:
        """
        Generate random JSON data for testing.

        Args:
            complexity: "simple", "nested", or "complex"
        """
        if complexity == "simple":
            return {
                "string_field": DataGenerator.random_string(),
                "number_field": random.randint(1, 1000),
                "boolean_field": random.choice([True, False]),
                "null_field": None,
            }
        elif complexity == "nested":
            return {
                "user": {
                    "name": DataGenerator.random_string(),
                    "email": DataGenerator.random_email(),
                    "age": random.randint(18, 80),
                },
                "preferences": {
                    "notifications": random.choice([True, False]),
                    "theme": random.choice(["light", "dark", "auto"]),
                },
                "tags": [DataGenerator.random_string(5) for _ in range(random.randint(1, 5))],
            }
        elif complexity == "complex":
            return {
                "metadata": {
                    "version": f"{random.randint(1, 10)}.{random.randint(0, 99)}.{random.randint(0, 99)}",
                    "created_at": time.time(),
                    "author": {
                        "name": DataGenerator.random_string(),
                        "email": DataGenerator.random_email(),
                        "roles": [random.choice(["admin", "user", "editor"]) for _ in range(random.randint(1, 3))],
                    },
                },
                "data": {
                    "items": [
                        {
                            "id": i,
                            "title": DataGenerator.random_string(20),
                            "description": DataGenerator.random_string(100),
                            "attributes": {
                                "category": random.choice(["A", "B", "C"]),
                                "priority": random.randint(1, 5),
                                "active": random.choice([True, False]),
                            },
                        }
                        for i in range(random.randint(5, 15))
                    ]
                },
                "stats": {
                    "total_count": random.randint(100, 10000),
                    "active_count": random.randint(50, 5000),
                    "last_updated": time.time(),
                },
            }

    @staticmethod
    def random_headers() -> dict[str, str]:
        """Generate random but valid HTTP headers."""
        headers = {
            "User-Agent": f"faster-http-test/{random.randint(1, 10)}.{random.randint(0, 99)}",
            "Accept": random.choice(["application/json", "text/html", "application/xml", "*/*"]),
            "Accept-Language": random.choice(["en-US,en;q=0.9", "es-ES,es;q=0.9", "fr-FR,fr;q=0.9", "de-DE,de;q=0.9"]),
            "Custom-Header": DataGenerator.random_string(15),
            "X-Request-ID": DataGenerator.random_string(32),
        }

        # Sometimes add Authorization header
        if random.choice([True, False]):
            headers["Authorization"] = f"Bearer {DataGenerator.random_string(40)}"

        return headers

    @staticmethod
    def random_query_params() -> dict[str, str | list[str]]:
        """Generate random query parameters."""
        params = {}

        # Add some single-value params
        for _ in range(random.randint(1, 5)):
            key = DataGenerator.random_string(8)
            value = DataGenerator.random_string(10)
            params[key] = value

        # Sometimes add multi-value params
        if random.choice([True, False]):
            key = DataGenerator.random_string(8)
            values = [DataGenerator.random_string(8) for _ in range(random.randint(2, 4))]
            params[key] = values

        return params

    @staticmethod
    def sample_file_data() -> tuple[str, bytes, str]:
        """Generate sample file data for upload testing."""
        filename = f"test_{DataGenerator.random_string(8)}.txt"
        content = f"Test file content: {DataGenerator.random_string(50)}".encode()
        content_type = "text/plain"
        return filename, content, content_type


class ErrorSimulator:
    """Simulate various error conditions for testing error handling."""

    @staticmethod
    @contextmanager
    def network_error():
        """Context manager to simulate network errors."""
        with patch("socket.socket") as mock_socket:
            mock_socket.side_effect = OSError("Network unreachable")
            yield

    @staticmethod
    @contextmanager
    def timeout_error():
        """Context manager to simulate timeout errors."""
        with patch("socket.socket.settimeout") as mock_timeout:
            mock_timeout.side_effect = TimeoutError("Connection timed out")
            yield

    @staticmethod
    @contextmanager
    def ssl_error():
        """Context manager to simulate SSL errors."""
        import ssl

        with patch("ssl.create_default_context") as mock_ssl:
            mock_ssl.side_effect = ssl.SSLError("SSL handshake failed")
            yield

    @staticmethod
    def create_mock_response(status_code: int = 200, content: str = "", headers: dict[str, str] | None = None) -> Mock:
        """Create a mock HTTP response for testing."""
        mock_response = Mock()
        mock_response.status_code = status_code
        mock_response.text = content
        mock_response.content = content.encode("utf-8")
        mock_response.headers = headers or {}

        if content.strip().startswith("{") or content.strip().startswith("["):
            try:
                mock_response.json.return_value = json.loads(content)
            except json.JSONDecodeError:
                mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", content, 0)
        else:
            mock_response.json.side_effect = json.JSONDecodeError("Not JSON", content, 0)

        return mock_response


class PerformanceMeasurer:
    """Utilities for measuring and asserting performance characteristics."""

    def __init__(self):
        self._start_time = None
        self._measurements = []

    @contextmanager
    def measure(self, label: str = "operation"):
        """Context manager to measure execution time."""
        start_time = time.time()
        try:
            yield
        finally:
            end_time = time.time()
            duration = end_time - start_time
            self._measurements.append((label, duration))

    def assert_performance(self, max_duration: float, label: str | None = None):
        """Assert that the last (or labeled) measurement was within time limit."""
        if not self._measurements:
            pytest.fail("No performance measurements available")

        if label:
            # Find measurement with specific label
            measurement = next((m for m in reversed(self._measurements) if m[0] == label), None)
            if not measurement:
                pytest.fail(f"No measurement found with label: {label}")
        else:
            # Use last measurement
            measurement = self._measurements[-1]

        measured_label, duration = measurement

        if duration > max_duration:
            pytest.fail(
                f"Performance assertion failed: {measured_label} took {duration:.3f}s, expected <= {max_duration:.3f}s"
            )

    def get_measurements(self) -> list[tuple[str, float]]:
        """Get all performance measurements."""
        return self._measurements.copy()

    def reset(self):
        """Reset all measurements."""
        self._measurements.clear()


class AssertionHelpers:
    """Additional assertion helpers for HTTP testing."""

    @staticmethod
    def assert_response_structure(response, expected_structure: dict):
        """
        Assert that response JSON matches expected structure.

        Args:
            response: HTTP response object
            expected_structure: Dict describing expected JSON structure
        """
        if not hasattr(response, "json"):
            pytest.fail("Response does not have json() method")

        try:
            json_data = response.json()
        except Exception as e:
            pytest.fail(f"Failed to parse response as JSON: {e}")

        AssertionHelpers._assert_dict_structure(json_data, expected_structure, "root")

    @staticmethod
    def _assert_dict_structure(actual: dict, expected: dict, path: str):
        """Recursively assert dictionary structure."""
        for key, expected_type in expected.items():
            if key not in actual:
                pytest.fail(f"Missing key '{key}' at {path}")

            actual_value = actual[key]

            if isinstance(expected_type, type):
                if not isinstance(actual_value, expected_type):
                    pytest.fail(
                        f"Key '{key}' at {path}: expected {expected_type.__name__}, got {type(actual_value).__name__}"
                    )
            elif isinstance(expected_type, dict):
                if not isinstance(actual_value, dict):
                    pytest.fail(f"Key '{key}' at {path}: expected dict, got {type(actual_value).__name__}")
                AssertionHelpers._assert_dict_structure(actual_value, expected_type, f"{path}.{key}")

    @staticmethod
    def assert_headers_present(response, required_headers: list[str]):
        """Assert that required headers are present in response."""
        if not hasattr(response, "headers"):
            pytest.fail("Response does not have headers")

        response_headers = {k.lower(): v for k, v in response.headers.items()}

        for header in required_headers:
            header_lower = header.lower()
            if header_lower not in response_headers:
                pytest.fail(f"Required header '{header}' not found in response")

    @staticmethod
    def assert_status_code_in_range(response, min_code: int, max_code: int):
        """Assert that response status code is within specified range."""
        if not hasattr(response, "status_code"):
            pytest.fail("Response does not have status_code")

        if not (min_code <= response.status_code <= max_code):
            pytest.fail(f"Status code {response.status_code} not in range {min_code}-{max_code}")

    @staticmethod
    def assert_response_time(response, max_time: float):
        """Assert that response was received within specified time."""
        if hasattr(response, "elapsed"):
            elapsed = response.elapsed.total_seconds()
            if elapsed > max_time:
                pytest.fail(f"Response time {elapsed:.3f}s exceeded limit {max_time:.3f}s")


# Pytest fixtures for TDD helpers
@pytest.fixture
def data_generator():
    """Fixture providing data generator instance."""
    return DataGenerator()


@pytest.fixture
def error_simulator():
    """Fixture providing error simulator instance."""
    return ErrorSimulator()


@pytest.fixture
def performance_measurer():
    """Fixture providing performance measurer instance."""
    return PerformanceMeasurer()


@pytest.fixture
def assert_helpers():
    """Fixture providing assertion helpers."""
    return AssertionHelpers()
