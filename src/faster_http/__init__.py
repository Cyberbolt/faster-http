"""
faster-http: A high-performance HTTP client for Python, powered by Rust's reqwest library.

This library provides a drop-in replacement for httpx with significantly better performance
by leveraging Rust's reqwest library through PyO3 bindings.
"""

# Import everything we can
try:
    from ._core import *
    # Try to import specific classes
    from ._core import HttpClient, AsyncHttpClient, HttpRequest, HttpResponse
except ImportError as e:
    print(f"Import error: {e}")
    # Fallback imports
    from . import _core
    HttpClient = getattr(_core, 'HttpClient', None)
    AsyncHttpClient = getattr(_core, 'AsyncHttpClient', None)

__version__ = "0.1.0"

# Expose main API
Client = HttpClient
AsyncClient = AsyncHttpClient
Request = HttpRequest
Response = HttpResponse

# CLI entry point
def main():
    """CLI entry point."""
    import sys
    print("faster-http: High-performance HTTP client")
    print("Usage: python -m faster_http")
    sys.exit(0)

# Entry point
if __name__ == "__main__":
    main()
