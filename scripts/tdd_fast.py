#!/usr/bin/env python3
"""
TDD runner script for faster-http development.

This script sets up environment for efficient TDD cycles:
- Skips httpx comparison tests for simplicity
- Uses shorter timeouts
- Focuses on faster-http only tests
"""

import os
import subprocess
import sys


def main():
    """Run tests in TDD mode."""
    print("🚀 Running TDD mode - skipping httpx comparisons for simplicity")

    # Set environment variables for TDD
    env = os.environ.copy()
    env["SKIP_HTTPX_COMPARISON"] = "true"
    env["FASTER_HTTP_FAST_TDD"] = "true"

    # Build pytest command
    cmd = [
        "uv",
        "run",
        "-m",
        "pytest",
        "tests/unit/",
        "-v",
        "--tb=short",
        "-x",  # Stop on first failure for immediate feedback
        "--disable-warnings",
    ]

    # Add parallel execution if not specified otherwise
    if "-n" not in sys.argv:
        cmd.extend(["-n", "auto"])

    # Add user arguments
    cmd.extend(sys.argv[1:])

    # Run tests
    try:
        result = subprocess.run(cmd, env=env)
        return result.returncode
    except KeyboardInterrupt:
        print("\n⏹️ TDD session interrupted")
        return 130


if __name__ == "__main__":
    sys.exit(main())
