#!/usr/bin/env python3
"""
Fast TDD runner script for faster-http development.

This script sets up environment for fastest possible TDD cycles:
- Skips httpx comparison tests for speed
- Uses shorter timeouts
- Focuses on faster-http only tests
"""

import os
import subprocess
import sys

def main():
    """Run tests in fast TDD mode."""
    print("🚀 Running fast TDD mode - skipping httpx comparisons for speed")
    
    # Set environment variables for fast TDD
    env = os.environ.copy()
    env["SKIP_HTTPX_COMPARISON"] = "true"
    env["FASTER_HTTP_FAST_TDD"] = "true"
    
    # Build pytest command
    cmd = [
        "uv", "run", "-m", "pytest",
        "tests/unit/",
        "-v",
        "--tb=short",
        "-x",  # Stop on first failure for faster feedback
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