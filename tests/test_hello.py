"""Tests the basic functionality of the faster_http module"""

import pytest
from faster_http import hello_from_bin


class TestHelloFromBin:
    """Tests the functionality of the hello_from_bin function"""
    
    def test_hello_from_bin_returns_correct_message(self):
        """Tests if the hello_from_bin function returns the correct message"""
        expected_message = "Hello from faster-http!"
        actual_message = hello_from_bin()
        assert actual_message == expected_message
    
    def test_hello_from_bin_returns_string(self):
        """Tests if the hello_from_bin function returns a string type"""
        result = hello_from_bin()
        assert isinstance(result, str)
    
    def test_hello_from_bin_not_empty(self):
        """Tests that the hello_from_bin function does not return an empty value"""
        result = hello_from_bin()
        assert result
        assert len(result) > 0


def test_hello_from_bin_direct():
    """Directly tests the function - maintaining the original simple test style"""
    assert hello_from_bin() == "Hello from faster-http!"


if __name__ == "__main__":
    # Allows this file to be run directly for testing
    pytest.main([__file__])
