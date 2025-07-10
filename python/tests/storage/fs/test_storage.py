"""
Tests for the storage module that handles file operations.
"""
import os
import tempfile
from unittest import mock

import pytest

from clay.storage.fs import process_input_list, process_output_list
from clay.storage.fs.s3 import S3Storage
from clay.type_utils import TypeFromDict


# Helper function to create a data wrapper for testing
def create_test_data_wrapper(value, is_artifact=True, format_type="raster"):
    """Create a data wrapper for testing using TypeFromDict."""
    data_dict = {
        "name": "test_data",
        "type": "url",
        "value": value,
        "format": format_type,
        "is_artifact": is_artifact,
    }
    
    # Add properties based on the format type
    if format_type == "raster":
        data_dict["properties"] = {
            "bands": ["B01", "B02", "B03"],
            "source": "test",
            "collection": "test-data"
        }
        data_dict["stac_url"] = "https://example.com/stac.json"  # Test URL
    elif format_type == "vector":
        data_dict["properties"] = {
            "geometry": "polygon"
        }
    
    # Use TypeFromDict to create a proper DataWrapperInterface instance
    return TypeFromDict(data_dict, to_v2=False)


class TestStorageModule:
    """Tests for the storage module functions."""

    @mock.patch('requests.get')
    def test_process_input_list_local_to_local(self, mock_requests_get):
        """Test processing local files to local directory."""
        # Mock the STAC URL request
        mock_response = mock.MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"test": "stac_data"}
        mock_requests_get.return_value = mock_response
        
        with tempfile.TemporaryDirectory() as source_dir, tempfile.TemporaryDirectory() as dest_dir:
            # Create a test file
            test_file_path = os.path.join(source_dir, "test_file.tif")
            with open(test_file_path, "w") as f:
                f.write("test content")
            
            # Create data list with local file
            data_list = {
                "test_item": create_test_data_wrapper(test_file_path)
            }
            
            # Process the input list
            with tempfile.TemporaryDirectory() as remote_dest_dir:
                result = process_input_list(data_list, dest_dir, remote_dest_dir)
            
            # Check that the file was copied
            expected_dest_path = os.path.join(dest_dir, "test_item", "test_file.tif")
            assert os.path.exists(expected_dest_path)
            
            # Check that the value was updated in the result
            assert result["test_item"].get_value() == expected_dest_path
    
    def test_process_input_list_ignores_non_artifacts(self):
        """Test that non-artifact items are not processed."""
        with tempfile.TemporaryDirectory() as dest_dir:
            # Create data list with non-artifact item
            data_list = {
                "test_param": create_test_data_wrapper("42", is_artifact=False, format_type="number")
            }
            
            # Process the input list
            with tempfile.TemporaryDirectory() as remote_dest_dir:
                result = process_input_list(data_list, dest_dir, remote_dest_dir)
            
            # Check that the value was not changed
            assert result["test_param"].get_value() == "42"
    
    def test_process_output_list_local_to_local(self):
        """Test processing local files to local output directory."""
        with tempfile.TemporaryDirectory() as source_dir, tempfile.TemporaryDirectory() as dest_dir:
            # Create a test file
            test_file_path = os.path.join(source_dir, "test_output.tif")
            with open(test_file_path, "w") as f:
                f.write("test output content")
            
            # Create data list with local file
            data_list = {
                "test_output": create_test_data_wrapper(test_file_path)
            }
            
            # Process the output list
            result = process_output_list(data_list, dest_dir)
            
            # Check that the file was copied
            expected_dest_path = os.path.join(dest_dir, "test_output", "test_output.tif")
            assert os.path.exists(expected_dest_path)
            
            # Check that the value was updated in the result
            assert result["test_output"].get_value() == expected_dest_path
    
    def test_process_output_list_ignores_non_artifacts(self):
        """Test that non-artifact items are not processed in output list."""
        with tempfile.TemporaryDirectory() as dest_dir:
            # Create data list with non-artifact item
            data_list = {
                "test_param": create_test_data_wrapper("84", is_artifact=False, format_type="number")
            }
            
            # Process the output list
            result = process_output_list(data_list, dest_dir)
            
            # Check that the value was not changed
            assert result["test_param"].get_value() == "84"
    
    @mock.patch('requests.get')
    def test_input_list_skips_missing_files(self, mock_requests_get):
        """Test that missing files are skipped in input list."""
        # Mock the STAC URL request
        mock_response = mock.MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"test": "stac_data"}
        mock_requests_get.return_value = mock_response
        
        with tempfile.TemporaryDirectory() as dest_dir:
            # Create data list with non-existent file
            data_list = {
                "missing_file": create_test_data_wrapper("/path/to/nonexistent/file.tif")
            }
            
            # Process the input list - this should raise an error since the file doesn't exist
            with tempfile.TemporaryDirectory() as remote_dest_dir:
                with pytest.raises(FileNotFoundError):
                    process_input_list(data_list, dest_dir, remote_dest_dir)
    
    def test_output_list_skips_missing_files(self):
        """Test that missing files are skipped in output list."""
        with tempfile.TemporaryDirectory() as dest_dir:
            # Create data list with non-existent file
            data_list = {
                "missing_file": create_test_data_wrapper("/path/to/nonexistent/file.tif")
            }
            
            # Process the output list - this should skip the file because it doesn't exist
            result = process_output_list(data_list, dest_dir)
            
            # The value should remain unchanged
            assert result["missing_file"].get_value() == "/path/to/nonexistent/file.tif"


class TestS3Storage:
    """Tests for the S3 storage provider."""
    
    @mock.patch('boto3.client')
    def test_s3_download(self, mock_boto_client):
        """Test S3 download operation."""
        # Setup mock
        mock_s3 = mock.MagicMock()
        mock_boto_client.return_value = mock_s3
        
        # Create S3 storage provider
        s3_storage = S3Storage()
        
        # Test download
        source_path = "s3://test-bucket/test-file.tif"
        dest_path = "/tmp/test-file.tif"
        
        # Ensure we don't actually write to the filesystem
        with mock.patch('os.makedirs'):
            s3_storage.download(source_path, dest_path)
        
        # Verify S3 client was called correctly
        mock_s3.download_file.assert_called_once_with("test-bucket", "test-file.tif", dest_path)
    
    @mock.patch('boto3.client')
    def test_s3_upload(self, mock_boto_client):
        """Test S3 upload operation."""
        # Setup mock
        mock_s3 = mock.MagicMock()
        mock_boto_client.return_value = mock_s3
        
        # Create S3 storage provider
        s3_storage = S3Storage()
        
        # Create a temporary file to upload
        with tempfile.NamedTemporaryFile() as tmp_file:
            # Write some content
            tmp_file.write(b"test content")
            tmp_file.flush()
            
            # Test upload
            source_path = tmp_file.name
            dest_path = "s3://test-bucket/test-upload.tif"
            
            s3_storage.upload(source_path, dest_path)
            
            # Verify S3 client was called correctly
            mock_s3.upload_file.assert_called_once_with(source_path, "test-bucket", "test-upload.tif")
    
    @mock.patch('requests.get')
    @mock.patch('boto3.client')
    def test_s3_integration_with_process_input_list(self, mock_boto_client, mock_requests_get):
        """Test S3 integration with process_input_list."""
        # Mock the STAC URL request
        mock_response = mock.MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"test": "stac_data"}
        mock_requests_get.return_value = mock_response
        
        # Setup mock
        mock_s3 = mock.MagicMock()
        mock_boto_client.return_value = mock_s3
        
        # Mock the download operation to create a file
        def mock_download_file(bucket, key, filename):
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            with open(filename, 'w') as f:
                f.write("mocked s3 content")
        
        mock_s3.download_file.side_effect = mock_download_file
        
        # Create data list with S3 path
        data_list = {
            "test_s3_item": create_test_data_wrapper("s3://test-bucket/test-s3-file.tif")
        }
        
        # Process the input list
        with tempfile.TemporaryDirectory() as dest_dir:
            with tempfile.TemporaryDirectory() as remote_dest_dir:
                result = process_input_list(data_list, dest_dir, remote_dest_dir)
            
            # Check that the mock was called correctly
            mock_s3.download_file.assert_called_once_with(
                "test-bucket", "test-s3-file.tif", 
                os.path.join(dest_dir, "test_s3_item", "test-s3-file.tif")
            )
            
            # Check that the result has the updated path
            expected_path = os.path.join(dest_dir, "test_s3_item", "test-s3-file.tif")
            assert result["test_s3_item"].get_value() == expected_path
            
            # Verify the file exists and has content
            assert os.path.exists(expected_path)
            with open(expected_path, 'r') as f:
                assert f.read() == "mocked s3 content"
    
    @mock.patch('boto3.client')
    def test_s3_integration_with_process_output_list(self, mock_boto_client):
        """Test S3 integration with process_output_list."""
        # Setup mock
        mock_s3 = mock.MagicMock()
        mock_boto_client.return_value = mock_s3
        
        # Create a temporary source file
        with tempfile.TemporaryDirectory() as source_dir:
            test_file_path = os.path.join(source_dir, "test_output.tif")
            with open(test_file_path, 'w') as f:
                f.write("test content for s3 upload")
            
            # Create data list with local file
            data_list = {
                "test_s3_output": create_test_data_wrapper(test_file_path)
            }
            
            # Process the output list
            s3_dest = "s3://test-bucket/outputs"
            result = process_output_list(data_list, s3_dest)
            
            # Check that the mock was called correctly
            mock_s3.upload_file.assert_called_once_with(
                test_file_path, "test-bucket", "outputs/test_s3_output/test_output.tif"
            )
            
            # Check that the result has the updated path
            expected_s3_path = "s3://test-bucket/outputs/test_s3_output/test_output.tif"
            assert result["test_s3_output"].get_value() == expected_s3_path