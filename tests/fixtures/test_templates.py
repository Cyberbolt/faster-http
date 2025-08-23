"""
Test templates for faster-http TDD development.

This module contains template test cases that demonstrate TDD practices
and provide starting points for new test development.
"""

import pytest

from tests.utils.httpx_comparison import httpx_compatibility_test
from tests.utils.tdd_helpers import TDDTestCase


class BasicHTTPTestTemplate(TDDTestCase):
    """Template for basic HTTP functionality tests."""

    @pytest.fixture(autouse=True)
    def setup(self, test_server):
        """Setup for each test - automatically used."""
        self.base_url = test_server.base_url

    @httpx_compatibility_test
    def test_basic_get_request_template(self, client_factory):
        """
        Template for basic GET request tests.

        TDD Steps:
        1. Red: Write test that fails
        2. Green: Implement minimal code to make test pass
        3. Refactor: Improve code while keeping tests green
        """
        # Arrange: Set up test data
        url = f"{self.base_url}/get"
        expected_status = 200

        # Act: Execute the functionality being tested
        response = client_factory.get(url)

        # Assert: Verify the expected behavior
        assert response.status_code == expected_status
        assert response.headers["content-type"].startswith("application/json")

        # Additional assertions for comprehensive testing
        json_data = response.json()
        assert "url" in json_data
        assert json_data["url"] == url

    @httpx_compatibility_test
    def test_post_with_json_template(self, client_factory):
        """Template for POST requests with JSON data."""
        # Arrange
        url = f"{self.base_url}/post"
        test_data = {"message": "test data", "timestamp": 1234567890, "nested": {"key": "value"}}

        # Act
        response = client_factory.post(url, json=test_data)

        # Assert
        assert response.status_code == 200

        response_data = response.json()
        assert "json" in response_data
        assert response_data["json"] == test_data

    @httpx_compatibility_test
    def test_error_handling_template(self, client_factory):
        """Template for error handling tests."""
        import faster_http

        # Test 404 error
        with pytest.raises(faster_http.HTTPStatusError):
            response = client_factory.get(f"{self.base_url}/status/404")
            response.raise_for_status()

        # Test connection error
        with pytest.raises(faster_http.ConnectError):
            client_factory.get("http://invalid-host-that-does-not-exist.local")


class AsyncHTTPTestTemplate(TDDTestCase):
    """Template for async HTTP functionality tests."""

    @pytest.fixture(autouse=True)
    def setup(self, test_server):
        """Setup for each test."""
        self.base_url = test_server.base_url

    @httpx_compatibility_test
    async def test_async_get_template(self, async_client_factory):
        """Template for async GET request tests."""
        # Arrange
        url = f"{self.base_url}/get"

        # Act
        async with async_client_factory() as client:
            response = await client.get(url)

        # Assert
        assert response.status_code == 200
        json_data = response.json()
        assert "url" in json_data

    @httpx_compatibility_test
    async def test_async_post_template(self, async_client_factory):
        """Template for async POST request tests."""
        # Arrange
        url = f"{self.base_url}/post"
        test_data = {"async": True, "test": "data"}

        # Act
        async with async_client_factory() as client:
            response = await client.post(url, json=test_data)

        # Assert
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["json"] == test_data


class PerformanceTestTemplate(TDDTestCase):
    """Template for performance tests."""

    @pytest.fixture(autouse=True)
    def setup(self, test_server):
        """Setup for each test."""
        self.base_url = test_server.base_url

    @pytest.mark.performance
    def test_performance_template(self, client_factory, performance_measurer):
        """Template for performance tests."""
        url = f"{self.base_url}/get"

        # Measure single request performance
        with performance_measurer.measure("single_request"):
            response = client_factory.get(url)
            assert response.status_code == 200

        # Assert performance within limits
        performance_measurer.assert_performance(max_duration=5.0, label="single_request")

    @pytest.mark.performance
    def test_concurrent_performance_template(self, client_factory, performance_measurer):
        """Template for concurrent performance tests."""
        import concurrent.futures

        url = f"{self.base_url}/get"
        num_requests = 10

        def make_request():
            response = client_factory.get(url)
            return response.status_code == 200

        # Measure concurrent requests
        with performance_measurer.measure("concurrent_requests"):
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(make_request) for _ in range(num_requests)]
                results = [future.result() for future in futures]

        # All requests should succeed
        assert all(results)

        # Performance should be reasonable
        performance_measurer.assert_performance(max_duration=10.0, label="concurrent_requests")


class DataDrivenTestTemplate(TDDTestCase):
    """Template for data-driven tests."""

    @pytest.fixture(autouse=True)
    def setup(self, test_server):
        """Setup for each test."""
        self.base_url = test_server.base_url

    @pytest.mark.parametrize(
        "method,endpoint",
        [
            ("GET", "/get"),
            ("POST", "/post"),
            ("PUT", "/put"),
            ("PATCH", "/patch"),
            ("DELETE", "/delete"),
        ],
    )
    @httpx_compatibility_test
    def test_http_methods_template(self, client_factory, method, endpoint):
        """Template for testing multiple HTTP methods."""
        url = f"{self.base_url}{endpoint}"

        # Use client.request for generic HTTP method testing
        with client_factory() as client:
            if method in ["POST", "PUT", "PATCH"]:
                response = client.request(method, url, json={"test": "data"})
            else:
                response = client.request(method, url)

        assert response.status_code == 200

    @pytest.mark.parametrize("status_code", [200, 201, 204, 400, 404, 500])
    @httpx_compatibility_test
    def test_status_codes_template(self, client_factory, status_code):
        """Template for testing various status codes."""
        url = f"{self.base_url}/status/{status_code}"

        response = client_factory.get(url)
        assert response.status_code == status_code

        # Test error handling for error status codes
        if status_code >= 400:
            import faster_http

            with pytest.raises(faster_http.HTTPStatusError):
                response.raise_for_status()
        else:
            response.raise_for_status()  # Should not raise


class TDDRedPhaseTestTemplate(TDDTestCase):
    """Template for TDD red phase tests."""

    @pytest.mark.tdd_red
    def test_red_phase_template(self):
        """
        Template for TDD red phase tests.

        This test should fail initially (red phase).
        After implementation, it should pass (green phase).
        Then code should be refactored while keeping tests green.
        """
        # This will cause the test to fail initially
        self.fail_first_run()

        # After fail_first_run is removed/skipped, implement actual test
        # Example:
        # response = faster_http.get(f"{test_server.base_url}/new-feature")
        # assert response.status_code == 200

    @TDDTestCase.expect_failure
    def test_expected_failure_template(self):
        """
        Template for tests that are expected to fail.

        Use the @expect_failure decorator for tests that should fail
        in the red phase but are ready for green phase implementation.
        """
        # This test is expected to fail until the feature is implemented
        import faster_http

        # Test a feature that doesn't exist yet
        response = faster_http.get(f"{self.base_url}/non-existent-endpoint")
        assert response.status_code == 200  # This will fail until implemented


class MockingTestTemplate(TDDTestCase):
    """Template for tests using mocks and fixtures."""

    def test_mock_response_template(self, error_simulator):
        """Template for testing with mock responses."""
        mock_response = error_simulator.create_mock_response(
            status_code=200, content='{"message": "mocked response"}', headers={"Content-Type": "application/json"}
        )

        assert mock_response.status_code == 200
        assert mock_response.json()["message"] == "mocked response"

    def test_error_simulation_template(self, error_simulator):
        """Template for testing error conditions."""
        import faster_http

        # Test network error simulation
        with error_simulator.network_error():
            with pytest.raises((faster_http.ConnectError, OSError)):
                faster_http.get("http://invalid-host-that-does-not-exist.local")


class FixtureUsageTestTemplate(TDDTestCase):
    """Template showing how to use various fixtures."""

    def test_data_generator_template(self, data_generator):
        """Template for using data generator fixture."""
        # Generate test data
        random_email = data_generator.random_email()
        assert "@" in random_email
        assert random_email.endswith(".com")

        # Generate JSON data
        json_data = data_generator.random_json_data("nested")
        assert isinstance(json_data, dict)
        assert "user" in json_data

    def test_assertion_helpers_template(self, client_factory, assert_helpers, test_server):
        """Template for using assertion helpers."""
        url = f"{test_server.base_url}/json"
        response = client_factory.get(url)

        # Use assertion helpers
        assert_helpers.assert_status_code_in_range(response, 200, 299)

        # Assert response structure
        expected_structure = {"slideshow": {"author": str, "title": str, "slides": list}}
        assert_helpers.assert_response_structure(response, expected_structure)

    def test_sample_data_template(self, sample_urls, sample_headers, sample_json_data):
        """Template for using sample data fixtures."""
        import faster_http

        # Use sample URLs
        response = faster_http.get(sample_urls["get"], headers=sample_headers["standard"])
        assert response.status_code == 200

        # Use sample JSON data
        response = faster_http.post(
            sample_urls["post"], json=sample_json_data["simple"], headers=sample_headers["standard"]
        )
        assert response.status_code == 200
