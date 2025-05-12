"""
Main storage module that provides utility functions for processing data lists.
"""
import copy
import os
import shutil
from pathlib import Path
from typing import Dict

import datatypes

from clay.storage.fs.interface import StorageProtocol


def create_provider(path: str) -> StorageProtocol:
    """
    Factory function to create the appropriate storage provider based on the path.

    Args:
        path: Path string with protocol prefix

    Returns:
        Instance of StorageProtocol implementation
    """
    from clay.storage.fs.s3 import S3Storage

    protocol = StorageProtocol.get_protocol_from_path(path)

    if protocol == 's3':
        return S3Storage()
    else:
        # For local paths, we don't need a provider
        # since we're only handling remote-to-local and local-to-remote operations
        raise ValueError(f"No storage provider available for protocol: {protocol}")


def process_input_list(data_list: Dict[str, datatypes.DataWrapperInterface], destination_path: str) -> Dict[str, datatypes.DataWrapperInterface]:
    """
    Process input data list by downloading files from storage providers to local file system.
    
    For each artifact in the data list, this function:
    1. Downloads the file from its source (storage provider)
    2. Stores it in a namespace directory (destination_path/item_name/)
    3. Updates the item's value to point to the local file path
    
    Args:
        data_list: Dictionary mapping names to DataWrapperInterface objects
        destination_path: Local directory path where files will be downloaded
        
    Returns:
        Dict[str, datatypes.DataWrapperInterface]: Updated data dictionary with local file paths
    """
    # Create a deep copy of the input data to avoid modifying the original
    updated_data = copy.deepcopy(data_list)
    
    # Process each item in the data dictionary
    for item_name, item in updated_data.items():
        # Only process items that are marked as artifacts
        if item.get_is_artifact():
            # Get the source path (remote storage)
            source_path = item.get_value()
            
            # Skip if the source path is empty
            if not source_path:
                continue
            
            # Create a namespaced destination directory
            item_dest_dir = os.path.join(destination_path, item_name)
            Path(item_dest_dir).mkdir(parents=True, exist_ok=True)
            
            # Get filename from source path
            filename = os.path.basename(source_path)
            dest_path = os.path.join(item_dest_dir, filename)
            
            # Get protocol from source path
            protocol = StorageProtocol.get_protocol_from_path(source_path)
            
            if protocol == 'file':
                # For local files, just copy to the destination
                if os.path.isfile(source_path):
                    shutil.copy2(source_path, dest_path)
                else:
                    raise FileNotFoundError(f"Source file not found: {source_path}")
            else:
                # For remote files, use the appropriate provider
                provider = create_provider(source_path)
                provider.download(source_path, dest_path)
            
            # Update the value in the data item
            item.set_value(dest_path)
    
    return updated_data


def process_output_list(data_list: Dict[str, datatypes.DataWrapperInterface], destination_path: str) -> Dict[str, datatypes.DataWrapperInterface]:
    """
    Process output data list by uploading files from local file system to storage providers.
    
    For each artifact in the data list, this function:
    1. Uploads the file from its local path
    2. Stores it in a namespace directory (destination_path/item_name/)
    3. Updates the item's value to point to the remote file path
    
    Args:
        data_list: Dictionary mapping names to DataWrapperInterface objects
        destination_path: Remote directory path where files will be uploaded
        
    Returns:
        Dict[str, datatypes.DataWrapperInterface]: Updated data dictionary with remote file paths
    """
    # Create a deep copy of the input data to avoid modifying the original
    updated_data = copy.deepcopy(data_list)
    
    # Get protocol from destination path
    protocol = StorageProtocol.get_protocol_from_path(destination_path)
    
    # Process each item in the data dictionary
    for item_name, item in updated_data.items():
        # Only process items that are marked as artifacts
        if item.get_is_artifact():
            # Get the source path (local file)
            source_path = item.get_value()
            
            # Skip if the source path is empty
            if not source_path:
                continue
            
            # Ensure the source file exists
            if not os.path.isfile(source_path):
                continue
            
            # Get filename from source path
            filename = os.path.basename(source_path)
            
            if protocol == 'file':
                # For local destination, create the directory and copy the file
                item_dest_dir = os.path.join(destination_path, item_name)
                Path(item_dest_dir).mkdir(parents=True, exist_ok=True)
                dest_path = os.path.join(item_dest_dir, filename)
                shutil.copy2(source_path, dest_path)
            else:
                # For remote destination, upload using the provider
                dest_provider = create_provider(destination_path)
                dest_path = StorageProtocol.join_path(destination_path, item_name, filename)
                dest_provider.upload(source_path, dest_path)
            
            # Update the value in the data item
            item.set_value(dest_path)
    
    return updated_data