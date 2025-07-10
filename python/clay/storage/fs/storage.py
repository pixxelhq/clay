"""
Main storage module that provides utility functions for processing data lists.
"""
import copy
import os
import shutil
from pathlib import Path
from typing import Dict
import json

import datatypes

import requests

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


def process_input_list(data_list: Dict[str, datatypes.DataWrapperInterface], destination_path: str, remote_destination_path: str) -> Dict[
    str, datatypes.DataWrapperInterface]:
    """
    Process input data list by downloading files from storage providers to local file system.
    
    For each artifact in the data list, this function:
    1. Downloads the file from its source (storage provider)
    2. Stores it in a namespace directory (destination_path/item_name/)
    3. Updates the item's value to point to the local file path
    4. Uploads all contents to remote_destination_path
    
    Args:
        data_list: Dictionary mapping names to DataWrapperInterface objects
        destination_path: Local directory path where files will be downloaded
        remote_destination_path: Remote path (local or S3) where files will be uploaded after download
        
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
            # Create a namespaced destination directory
            item_dest_dir = os.path.join(destination_path, item_name)
            Path(item_dest_dir).mkdir(parents=True, exist_ok=True)

            source_path = item.get_value()
            if item.get_format() == "vector":
                # For vector items (GeoJSON), handle source path differently
                # Check if source_path is a URL or a GeoJSON string
                if source_path and (source_path.startswith('http://') or source_path.startswith('https://') or source_path.startswith('s3://') or source_path.startswith('file://')):
                    # Value is a URL, continue to process normally at line 78
                    pass
                else:
                    # Value is a GeoJSON string, create .geojson file
                    geojson_filename = f"{item_name}.geojson"
                    geojson_dest_path = os.path.join(item_dest_dir, geojson_filename)
                    
                    # Write GeoJSON content to file
                    if isinstance(source_path, str):
                        try:
                            # Try to parse as JSON to validate
                            geojson_data = json.loads(source_path)
                        except json.JSONDecodeError:
                            # If not valid JSON, wrap in a simple structure
                            geojson_data = {"data": source_path}
                    else:
                        geojson_data = source_path
                    
                    with open(geojson_dest_path, "w") as f:
                        json.dump(geojson_data, f, indent=2)
                    
                    # Update the item's value to point to the GeoJSON file
                    item.set_value(geojson_dest_path)
                    continue  # Skip to next item since we've handled this one

            # Skip if the source path is empty
            if source_path:
                print(f"Processing item: {item_name} with source path: {source_path}")
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

            # process stac_url download
            if item.get_format() == "raster" and item.get_field("stac_url"):
                stac_dest_path = os.path.join(item_dest_dir, "stac.json")
                response = requests.get(item.get_field("stac_url")) # type: ignore
                if response.status_code == 200:
                    stac_data = response.json()
                    with open(stac_dest_path, "w+") as f:
                        json.dump(stac_data, f, indent=4)
                    item.set_field("stac_url", stac_dest_path)
                else:
                    raise ValueError(f"Failed to download STAC file: {item.get_field('stac_url')}")

        item_dest_dir = os.path.join(destination_path, item_name)
        Path(item_dest_dir).mkdir(parents=True, exist_ok=True)
        serialized_item = item.serialize_to_dict()
        with open(os.path.join(item_dest_dir, "spec.json"), "w+") as f:
            json.dump(serialized_item, f)

    # Upload all contents of destination_path to remote_destination_path
    remote_protocol = StorageProtocol.get_protocol_from_path(remote_destination_path)
    
    for root, dirs, files in os.walk(destination_path):
        for file in files:
            local_file_path = os.path.join(root, file)
            # Get relative path from destination_path
            relative_path = os.path.relpath(local_file_path, destination_path)
            
            if remote_protocol == 'file':
                # For local destination, create directory and copy file
                remote_file_path = os.path.join(remote_destination_path, relative_path)
                remote_dir = os.path.dirname(remote_file_path)
                Path(remote_dir).mkdir(parents=True, exist_ok=True)
                shutil.copy2(local_file_path, remote_file_path)
            else:
                # For remote destination, use storage provider
                remote_provider = create_provider(remote_destination_path)
                remote_key = StorageProtocol.join_path(remote_destination_path, relative_path)
                print(f"Uploading {local_file_path} to {remote_key}")
                remote_provider.upload(local_file_path, remote_key)

    return updated_data


def process_output_list(data_list: Dict[str, datatypes.DataWrapperInterface], destination_path: str) -> Dict[
    str, datatypes.DataWrapperInterface]:
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


def process_spec_files(spec_files: str, destination_path: str, output_name: str):
    """
    Process specification files by copying them to a destination directory.
    
    Args:
        spec_files: str to file paths
        destination_path: remote path where files will be copied
        
    """
    if not os.path.exists(spec_files):
        raise FileNotFoundError(f"Source file does not exist: {spec_files}")
    protocol = StorageProtocol.get_protocol_from_path(destination_path)
    if protocol != 'file':
        print("destination_path", destination_path)
        dest_provider = create_provider(destination_path)
        dest_path = StorageProtocol.join_path(destination_path, output_name, "spec.json")
        print(f"Processing spec files: {spec_files} to {dest_path}")
        dest_provider.upload(spec_files, dest_path)