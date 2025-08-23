# faster-http Test Framework

A comprehensive TDD-focused testing framework for faster-http development.

## Overview

This test framework provides:
- **TDD Support**: Red-green-refactor cycle helpers
- **httpx Compatibility**: Automatic comparison with httpx behavior
- **Local Test Server**: No external dependencies
- **Performance Testing**: Built-in performance measurement tools
- **Comprehensive Fixtures**: Reusable test utilities

## Directory Structure

```
tests/
├── unit/                    # Unit tests
│   ├── test_http_methods.py    # Top-level HTTP methods
│   ├── test_client.py          # Client class tests
│   ├── test_async_client.py    # AsyncClient tests
│   ├── test_response.py        # Response object tests
│   ├── test_request.py         # Request object tests
│   ├── test_auth.py           # Authentication tests
│   ├── test_config.py         # Configuration tests
│   ├── test_exceptions.py     # Exception tests
│   └── test_utils.py          # Utility tests
├── integration/             # Integration tests
│   ├── test_compatibility.py  # httpx compatibility
│   ├── test_performance.py    # Performance comparisons
│   └── test_scenarios.py      # End-to-end scenarios
├── fixtures/               # Test data and templates
│   └── test_templates.py      # Template test cases
├── utils/                  # Test utilities
│   ├── httpx_comparison.py    # httpx comparison framework
│   ├── test_server.py         # Local test server
│   └── tdd_helpers.py         # TDD utility functions
└── conftest.py             # Global pytest configuration
```

## Quick Start

### Running Tests

```bash
# Run all tests with parallel execution
uv run -m pytest tests/ -n auto

# Run only unit tests
uv run -m pytest tests/unit/ -n auto

# Run only integration tests
uv run -m pytest tests/integration/ -n auto

# Run with coverage
uv run -m pytest tests/ --cov=faster_http --cov-report=html

# Run performance tests only
uv run -m pytest tests/ -m performance

# Skip slow tests
uv run -m pytest tests/ -m "not slow"
```

### Writing Tests

#### 1. Basic Test with httpx Compatibility

```python
from tests.utils.httpx_comparison import httpx_compatibility_test

class TestMyFeature:
    @httpx_compatibility_test
    def test_basic_get(self, client_factory, test_server):
        url = f"{test_server.base_url}/get"
        response = client_factory.get(url)
        assert response.status_code == 200
```

#### 2. TDD Red Phase Test

```python
from tests.utils.tdd_helpers import TDDTestCase

class TestNewFeature(TDDTestCase):
    @pytest.mark.tdd_red
    def test_new_feature_red_phase(self):
        # This will fail initially - that's expected!
        self.fail_first_run()
        
        # After removing fail_first_run(), implement actual test
        # response = faster_http.get("http://example.com/new-endpoint")
        # assert response.status_code == 200
```

#### 3. Async Test

```python
@httpx_compatibility_test
async def test_async_request(self, async_client_factory, test_server):
    async with async_client_factory() as client:
        response = await client.get(f"{test_server.base_url}/get")
        assert response.status_code == 200
```

#### 4. Performance Test

```python
@pytest.mark.performance
def test_performance(self, client_factory, performance_measurer, test_server):
    with performance_measurer.measure("request_time"):
        response = client_factory.get(f"{test_server.base_url}/get")
        assert response.status_code == 200
    
    performance_measurer.assert_performance(max_duration=1.0)
```

## Key Features

### httpx Compatibility Testing

The `@httpx_compatibility_test` decorator automatically runs tests with both httpx and faster-http, comparing results:

```python
@httpx_compatibility_test
def test_get_request(self, client_factory, test_server):
    # This test runs twice:
    # 1. With httpx (reference behavior)
    # 2. With faster-http (implementation under test)
    response = client_factory.get(f"{test_server.base_url}/get")
    assert response.status_code == 200
```

### Local Test Server

No external dependencies! All tests use a local test server:

```python
def test_with_local_server(self, test_server, client_factory):
    # test_server provides endpoints like:
    # - /get, /post, /put, etc.
    # - /status/<code>
    # - /delay/<seconds>
    # - /redirect/<count>
    # - /basic-auth/<user>/<pass>
    response = client_factory.get(f"{test_server.base_url}/get")
    assert response.status_code == 200
```

### TDD Helpers

Built-in support for TDD practices:

```python
from tests.utils.tdd_helpers import DataGenerator, PerformanceMeasurer

def test_with_helpers(self, data_generator, performance_measurer):
    # Generate test data
    test_data = data_generator.random_json_data("complex")
    
    # Measure performance
    with performance_measurer.measure("operation"):
        # ... perform operation
        pass
    
    performance_measurer.assert_performance(max_duration=1.0)
```

### Data Generation

Generate realistic test data:

```python
def test_with_generated_data(self, data_generator):
    email = data_generator.random_email()
    headers = data_generator.random_headers()
    json_data = data_generator.random_json_data("nested")
    
    # Use generated data in tests
    assert "@" in email
    assert "User-Agent" in headers
```

### Error Simulation

Test error conditions easily:

```python
def test_error_handling(self, error_simulator):
    import faster_http
    
    with error_simulator.network_error():
        with pytest.raises(faster_http.ConnectError):
            faster_http.get("http://invalid-host-that-does-not-exist.local")
```

## Test Markers

Use pytest markers to categorize tests:

```python
@pytest.mark.unit          # Unit test
@pytest.mark.integration   # Integration test
@pytest.mark.performance   # Performance test
@pytest.mark.slow          # Slow-running test
@pytest.mark.auth          # Authentication test
@pytest.mark.tdd_red       # TDD red phase test
```

## Best Practices

### 1. Follow TDD Cycle

1. **Red**: Write a failing test
2. **Green**: Write minimal code to make it pass
3. **Refactor**: Improve code while keeping tests green

### 2. Use httpx Compatibility

Always use `@httpx_compatibility_test` to ensure API compatibility:

```python
@httpx_compatibility_test
def test_api_method(self, client_factory):
    # Test will automatically verify faster-http matches httpx behavior
    pass
```

### 3. Test Structure

Follow the Arrange-Act-Assert pattern:

```python
def test_feature(self):
    # Arrange: Set up test conditions
    url = f"{test_server.base_url}/api"  # Use local test server
    headers = {"Authorization": "Bearer token"}
    
    # Act: Execute the code being tested
    response = client.get(url, headers=headers)
    
    # Assert: Verify expected behavior
    assert response.status_code == 200
```

### 4. Use Fixtures Effectively

Leverage provided fixtures for consistent test setup:

```python
def test_with_fixtures(self, test_server, sample_headers, data_generator):
    # test_server: Local HTTP server
    # sample_headers: Pre-defined header sets
    # data_generator: Random data generation
    pass
```

### 5. Performance Testing

Always include performance tests for critical paths:

```python
@pytest.mark.performance
def test_performance_critical_path(self, performance_measurer):
    with performance_measurer.measure("critical_operation"):
        # ... critical operation
        pass
    
    performance_measurer.assert_performance(max_duration=0.5)
```

## Templates

See `tests/fixtures/test_templates.py` for comprehensive test templates covering:

- Basic HTTP tests
- Async tests
- Performance tests
- Data-driven tests
- TDD red phase tests
- Error handling tests
- Mocking examples

## Configuration

Key pytest configuration in `pytest.ini`:

- Parallel execution with `-n auto`
- Async support with `--asyncio-mode=auto`
- Coverage reporting
- Custom markers
- Timeout settings

## CI/CD Integration

Set environment variable to skip red phase tests in CI:

```bash
export TDD_SKIP_RED_PHASE=true
```

This allows TDD red phase tests to be skipped in automated environments while still being available for local development.