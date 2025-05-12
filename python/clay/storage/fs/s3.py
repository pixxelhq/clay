"""
Implementation of S3 storage operations.
"""
import os
from pathlib import Path
from typing import Tuple
from urllib.parse import urlparse

import boto3
from botocore.exceptions import ClientError

from clay.storage.fs.interface import StorageProtocol


class S3Storage(StorageProtocol):
    """Storage implementation for AWS S3 operations."""
    
    def __init__(self):
        """Initialize S3 client"""
        self.s3_client = boto3.client('s3')
    
    def download(self, source_path: str, destination_path: str) -> str:
        """
        Download a file from S3 to local file system.
        
        Args:
            source_path: S3 URI (s3://bucket/key)
            destination_path: Local path where the file should be downloaded
            
        Returns:
            String path to the downloaded file
        """
        bucket, key = self._get_bucket_and_key(source_path)
        
        # Ensure destination directory exists
        destination_dir = Path(destination_path).parent
        self.ensure_directory(destination_dir)
        
        try:
            self.s3_client.download_file(bucket, key, destination_path)
        except ClientError as e:
            raise FileNotFoundError(f"Failed to download from S3: {source_path}. Error: {str(e)}")
        
        return destination_path
    
    def upload(self, source_path: str, destination_path: str) -> str:
        """
        Upload a file from local file system to S3.
        
        Args:
            source_path: Local path of the file to upload
            destination_path: S3 URI (s3://bucket/key) where the file should be uploaded
            
        Returns:
            String S3 URI of the uploaded file
        """
        bucket, key = self._get_bucket_and_key(destination_path)
        
        if not os.path.isfile(source_path):
            raise FileNotFoundError(f"Source file not found: {source_path}")
        
        try:
            self.s3_client.upload_file(source_path, bucket, key)
        except ClientError as e:
            raise RuntimeError(f"Failed to upload to S3: {destination_path}. Error: {str(e)}")
        
        return destination_path
    
    def _get_bucket_and_key(self, uri: str) -> Tuple[str, str]:
        """
        Parse S3 URI into bucket and key components.
        
        Args:
            uri: S3 URI (s3://bucket/key)
            
        Returns:
            Tuple of (bucket, key)
            
        Raises:
            ValueError: If the URI is not a valid S3 URI
        """
        parsed = urlparse(uri)
        
        if parsed.scheme != 's3':
            raise ValueError(f"Not a valid S3 URI: {uri}")
        
        bucket = parsed.netloc
        key = parsed.path.lstrip('/')
        
        return bucket, key