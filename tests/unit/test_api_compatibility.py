"""
Test API compatibility with httpx.

This module ensures faster-http provides exactly the same public interface as httpx,
following the core project rule: "faster-http不得实现httpx不支持的接口"
"""



def test_api_exact_match():
    """Ensure faster-http interface exactly matches httpx."""
    import httpx

    import faster_http

    httpx_public = {attr for attr in dir(httpx) if not attr.startswith('_')}
    faster_http_public = {attr for attr in dir(faster_http) if not attr.startswith('_')}

    missing = httpx_public - faster_http_public
    extra = faster_http_public - httpx_public

    assert not missing, f"缺失httpx接口: {missing}"
    assert not extra, f"多余非httpx接口: {extra} - 违反项目规则!"
    assert httpx_public == faster_http_public, "接口必须完全匹配httpx"


def test_interface_count():
    """Verify interface count matches httpx exactly."""
    import httpx

    import faster_http

    httpx_count = len([attr for attr in dir(httpx) if not attr.startswith('_')])
    faster_http_count = len([attr for attr in dir(faster_http) if not attr.startswith('_')])

    assert httpx_count == faster_http_count, (
        f"Interface count mismatch: httpx has {httpx_count}, "
        f"faster-http has {faster_http_count}"
    )


def test_specific_interface_presence():
    """Test specific interfaces that must be present."""
    import faster_http

    # Core classes that httpx provides
    required_classes = [
        'AsyncClient', 'Client', 'Request', 'Response', 'URL',
        'Headers', 'QueryParams', 'Cookies', 'Timeout', 'Proxy',
        'HTTPError', 'HTTPStatusError', 'RequestError', 'NetworkError',
    ]

    for class_name in required_classes:
        assert hasattr(faster_http, class_name), f"Missing required class: {class_name}"


def test_specific_interface_absence():
    """Test that non-httpx interfaces are not present."""
    import faster_http

    # Interfaces that were incorrectly added but don't exist in httpx
    forbidden_interfaces = [
        'ConnectionError', 'RequestTimeout', 'SSLError',
        'new_http_status_error', 'DEFAULT_CIPHERS', 'DEFAULT_TIMEOUT_CONFIG',
        'proxy'  # module, not class
    ]

    for interface_name in forbidden_interfaces:
        assert not hasattr(faster_http, interface_name), (
            f"Forbidden interface present: {interface_name} - 违反项目规则!"
        )


def test_httpx_compatibility_types():
    """Test that major types are compatible."""
    import httpx

    import faster_http

    # Test that we have the same types for key interfaces
    for attr_name in ['AsyncClient', 'Client', 'Request', 'Response']:
        httpx_attr = getattr(httpx, attr_name)
        faster_http_attr = getattr(faster_http, attr_name)

        # Both should be classes/types
        assert callable(httpx_attr), f"httpx.{attr_name} should be callable"
        assert callable(faster_http_attr), f"faster_http.{attr_name} should be callable"
