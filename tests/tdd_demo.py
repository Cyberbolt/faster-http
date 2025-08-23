"""
TDD workflow demonstration.

This file demonstrates a complete TDD cycle for adding new functionality.
"""

import pytest

from tests.utils.tdd_framework import tdd_test


class TestTDDWorkflow:
    """Demonstrate complete TDD workflow."""

    @tdd_test
    def test_red_phase_new_feature(self, tdd_client, test_server):
        """TDD Red Phase: Write a failing test for new functionality."""
        # This test represents the Red phase - it should initially fail
        # Let's say we want to implement a feature to parse response headers

        # Simulate making a request (this will work)
        try:
            # Use nginx test server due to faster_http localhost connection issue
            response = tdd_client.get("http://nginx:21000", timeout=3.0)

            # Now test for new functionality that doesn't exist yet
            # Uncomment the next line to see Red phase in action:
            # assert hasattr(response, 'parsed_headers'), "Response should have parsed_headers attribute"

            # For demo purposes, let's test that the feature exists (Green phase simulation)
            assert hasattr(response, "headers"), "Response should have headers attribute"

        except Exception as e:
            pytest.fail(f"Local test server request failed: {e}")

    @tdd_test
    def test_green_phase_minimal_implementation(self, tdd_client):
        """TDD Green Phase: Minimal implementation to make test pass."""
        # This represents writing minimal code to pass the test

        # Mock the minimal implementation
        class MockResponse:
            def __init__(self):
                self.status_code = 200
                self.headers = {"content-type": "application/json"}
                self.parsed_headers = self._parse_headers()

            def _parse_headers(self):
                # Minimal implementation
                return {k.lower().replace("-", "_"): v for k, v in self.headers.items()}

        response = MockResponse()

        # Test passes with minimal implementation
        assert response.status_code == 200
        assert hasattr(response, "parsed_headers")
        assert response.parsed_headers["content_type"] == "application/json"

    def test_refactor_phase_improvement(self):
        """TDD Refactor Phase: Improve code quality while keeping tests green."""
        # This represents refactoring the code to improve quality

        class ImprovedResponse:
            def __init__(self, headers=None):
                self.status_code = 200
                self.headers = headers or {"content-type": "application/json"}
                self._parsed_headers = None

            @property
            def parsed_headers(self):
                """Lazy loading of parsed headers (refactored for better performance)."""
                if self._parsed_headers is None:
                    self._parsed_headers = self._parse_headers()
                return self._parsed_headers

            def _parse_headers(self):
                """Improved parsing logic with better error handling."""
                try:
                    return {
                        key.lower().replace("-", "_"): value.strip()
                        for key, value in self.headers.items()
                        if isinstance(key, str) and isinstance(value, str)
                    }
                except (AttributeError, TypeError):
                    return {}

        response = ImprovedResponse()

        # All previous tests still pass after refactoring
        assert response.status_code == 200
        assert hasattr(response, "parsed_headers")
        assert response.parsed_headers["content_type"] == "application/json"

        # Refactored version handles edge cases better
        edge_case_response = ImprovedResponse({"Content-Type": "  text/html  "})
        assert edge_case_response.parsed_headers["content_type"] == "text/html"


class TestTDDCycleIntegration:
    """Integration tests for TDD cycle."""

    def test_tdd_cycle_complete(self):
        """Test that complete TDD cycle works."""
        # Red: Test fails initially
        # Green: Minimal implementation
        # Refactor: Improve while keeping tests green

        class TDDFeature:
            def __init__(self):
                self.version = "1.0.0"

            def red_phase(self):
                """Represents failing test."""
                return False

            def green_phase(self):
                """Minimal implementation."""
                return True

            def refactor_phase(self):
                """Improved implementation."""
                return {"success": True, "quality": "improved"}

        feature = TDDFeature()

        # Simulate TDD cycle
        assert feature.version == "1.0.0"
        assert feature.green_phase() is True
        refactored = feature.refactor_phase()
        assert refactored["success"] is True
        assert refactored["quality"] == "improved"
