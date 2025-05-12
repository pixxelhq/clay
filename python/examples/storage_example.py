"""
Example demonstrating the use of Clay's fs module with process_input_list and process_output_list.
Uses a local S3 server at localhost:9001 with a bucket named 'local-test'.
"""
import os
import tempfile

from clay.storage.fs import process_input_list, process_output_list
from clay.type_utils import TypeFromDict


def create_data_wrapper(value, is_artifact=True, format_type="raster"):
    """Create a data wrapper using TypeFromDict."""
    data_dict = {
        "name": "example_data",
        "type": "url",
        "value": value,
        "format": format_type,
        "is_artifact": is_artifact,
        "properties": {
            "source": "example",
            "collection": "example-data"
        }
    }
    
    return TypeFromDict(data_dict, to_v2=False)


def main():
    """Run example using process_input_list and process_output_list with S3."""
    print("Clay fs Module Example: process_input_list and process_output_list")
    print("==============================================================")
    
    # Configure environment variables for local S3 server
    os.environ['S3_ENDPOINT'] = 'http://localhost:9001'

    # Create a temporary local file to work with
    with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as temp_file:
        temp_file.write(b"This is test content for the Clay fs module example.")
        local_file_path = temp_file.name
    
    print(f"Created temporary file: {local_file_path}")
    
    try:
        # First, let's upload our local file to S3 using process_output_list
        s3_output_path = "s3://local-test/output"
        
        # Create data dictionary for the local file
        local_data = {
            "local_file": create_data_wrapper(local_file_path)
        }
        
        print("\nUploading local file to S3 using process_output_list")
        print(f"Destination: {s3_output_path}")
        
        # Process output (upload from local to S3)
        s3_result = process_output_list(local_data, s3_output_path)
        
        # Get the uploaded S3 path
        s3_path = s3_result["local_file"].get_value()
        print(f"File uploaded to S3: {s3_path}")
        
        # Now let's download from S3 using process_input_list
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create data dictionary for the S3 file
            s3_data = {
                "s3_file": create_data_wrapper(s3_path)
            }
            
            print("\nDownloading from S3 using process_input_list")
            print(f"Destination directory: {temp_dir}")
            
            # Process input (download from S3 to local)
            local_result = process_input_list(s3_data, temp_dir)
            
            # Get the downloaded local path
            downloaded_path = local_result["s3_file"].get_value()
            print(f"File downloaded to: {downloaded_path}")
            
            # Verify the content
            with open(downloaded_path, 'r') as f:
                content = f.read()
                print(f"Content of the downloaded file: '{content}'")
    
    finally:
        # Clean up the temporary file
        try:
            os.unlink(local_file_path)
            print(f"\nRemoved temporary file: {local_file_path}")
        except Exception:
            pass


if __name__ == "__main__":
    main()