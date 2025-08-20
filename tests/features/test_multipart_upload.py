#!/usr/bin/env python3
"""Test multipart file upload functionality."""

import os
from pathlib import Path
import tempfile

import httpx
import pytest

import faster_http


class TestMultipartUpload:
    """Test multipart file upload features."""

    def test_simple_file_upload(self):
        """Test uploading a single file."""
        # Create a temporary file with test content
        test_content = "This is a test file content for multipart upload."

        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(test_content)
            temp_file_path = f.name

        try:
            # Test with faster_http
            with open(temp_file_path, 'rb') as f:
                files = {'file': f}

                # Use httpbin.org for testing multipart upload
                url = "https://httpbin.org/post"
                response = faster_http.post(url, files=files)

                # Verify response
                assert response.status_code == 200
                response_data = response.json()

                # Check that the file was uploaded correctly
                assert 'files' in response_data
                assert 'file' in response_data['files']
                assert response_data['files']['file'] == test_content

                # Check Content-Type header
                assert response_data['headers']['Content-Type'].startswith('multipart/form-data')

        finally:
            # Clean up
            os.unlink(temp_file_path)

    def test_multiple_file_upload(self):
        """Test uploading multiple files."""
        # Create multiple temporary files
        file_contents = {
            'file1.txt': "Content of first file",
            'file2.txt': "Content of second file",
            'file3.txt': "Content of third file"
        }

        temp_files = {}
        try:
            # Create temporary files
            for filename, content in file_contents.items():
                with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                    f.write(content)
                    temp_files[filename] = f.name

            # Test with faster_http
            files = {}
            file_handles = []
            try:
                for field_name, temp_path in temp_files.items():
                    f = open(temp_path, 'rb')  # noqa: SIM115
                    file_handles.append(f)
                    files[field_name.replace('.txt', '')] = f

                url = "https://httpbin.org/post"
                response = faster_http.post(url, files=files)

                # Verify response
                assert response.status_code == 200
                response_data = response.json()

                # Check that all files were uploaded correctly
                assert 'files' in response_data
                for field_name, expected_content in file_contents.items():
                    field_key = field_name.replace('.txt', '')
                    assert field_key in response_data['files']
                    assert response_data['files'][field_key] == expected_content

                # Check Content-Type header
                assert response_data['headers']['Content-Type'].startswith('multipart/form-data')

            finally:
                # Close file handles
                for f in file_handles:
                    f.close()

        finally:
            # Clean up temporary files
            for temp_path in temp_files.values():
                os.unlink(temp_path)

    def test_mixed_data_and_files(self):
        """Test uploading files along with form data."""
        # Create a temporary file
        test_file_content = "Test file content for mixed upload"

        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(test_file_content)
            temp_file_path = f.name

        try:
            # Test with faster_http
            with open(temp_file_path, 'rb') as f:
                files = {'file': f}
                data = {
                    'field1': 'value1',
                    'field2': 'value2',
                    'number': 42,
                    'boolean': True
                }

                url = "https://httpbin.org/post"
                response = faster_http.post(url, data=data, files=files)

                # Verify response
                assert response.status_code == 200
                response_data = response.json()

                # Check that the file was uploaded correctly
                assert 'files' in response_data
                assert 'file' in response_data['files']
                assert response_data['files']['file'] == test_file_content

                # Check that form data was uploaded correctly
                assert 'form' in response_data
                assert response_data['form']['field1'] == 'value1'
                assert response_data['form']['field2'] == 'value2'
                assert response_data['form']['number'] == '42'
                assert response_data['form']['boolean'] == 'true'  # Form data converts to string

                # Check Content-Type header
                assert response_data['headers']['Content-Type'].startswith('multipart/form-data')

        finally:
            # Clean up
            os.unlink(temp_file_path)

    def test_file_upload_with_custom_filename(self):
        """Test file upload where filename is extracted correctly."""
        # Create a temporary file with a specific name
        test_dir = tempfile.mkdtemp()
        test_file_path = Path(test_dir) / "custom_filename.txt"
        test_content = "Content with custom filename"

        try:
            # Write content to file
            with open(test_file_path, 'w') as f:
                f.write(test_content)

            # Test upload
            with open(test_file_path, 'rb') as f:
                files = {'document': f}

                url = "https://httpbin.org/post"
                response = faster_http.post(url, files=files)

                # Verify response
                assert response.status_code == 200
                response_data = response.json()

                # Check file upload
                assert 'files' in response_data
                assert 'document' in response_data['files']
                assert response_data['files']['document'] == test_content

        finally:
            # Clean up
            if test_file_path.exists():
                test_file_path.unlink()
            os.rmdir(test_dir)

    def test_httpx_compatibility(self):
        """Test that faster_http multipart upload is compatible with httpx."""
        # Create a temporary file
        test_content = "Compatibility test content"

        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(test_content)
            temp_file_path = f.name

        try:
            # Test with both httpx and faster_http
            with open(temp_file_path, 'rb') as f1, open(temp_file_path, 'rb') as f2:
                files = {'file': f1}
                data = {'field': 'value'}

                # Use httpx as reference
                url = "https://httpbin.org/post"
                httpx_response = httpx.post(url, data=data, files={'file': f2})

                # Reset file pointer and test with faster_http
                files = {'file': f1}
                faster_response = faster_http.post(url, data=data, files=files)

                # Both should succeed
                assert httpx_response.status_code == 200
                assert faster_response.status_code == 200

                # Parse responses
                httpx_data = httpx_response.json()
                faster_data = faster_response.json()

                # Check file content is the same
                assert httpx_data['files']['file'] == faster_data['files']['file']
                assert httpx_data['form']['field'] == faster_data['form']['field']

                # Both should use multipart/form-data
                assert httpx_data['headers']['Content-Type'].startswith('multipart/form-data')
                assert faster_data['headers']['Content-Type'].startswith('multipart/form-data')

        finally:
            # Clean up
            os.unlink(temp_file_path)

    def test_empty_files_parameter(self):
        """Test behavior when files parameter is empty dict."""
        # This should fall back to regular form data handling
        data = {'field': 'value'}

        url = "https://httpbin.org/post"
        response = faster_http.post(url, data=data, files={})

        assert response.status_code == 200
        response_data = response.json()

        # Should be form-encoded, not multipart
        assert response_data['headers']['Content-Type'] == 'application/x-www-form-urlencoded'
        assert response_data['form']['field'] == 'value'

    def test_large_file_upload(self):
        """Test uploading a larger file to check memory efficiency."""
        # Create a file with 1MB of content
        large_content = "x" * (1024 * 1024)  # 1MB

        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write(large_content)
            temp_file_path = f.name

        try:
            with open(temp_file_path, 'rb') as f:
                files = {'largefile': f}

                url = "https://httpbin.org/post"
                response = faster_http.post(url, files=files)

                # Should handle large files correctly
                assert response.status_code == 200
                response_data = response.json()

                assert 'files' in response_data
                assert 'largefile' in response_data['files']
                assert len(response_data['files']['largefile']) == len(large_content)

        finally:
            # Clean up
            os.unlink(temp_file_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
