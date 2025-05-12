"""
Interface defining storage protocol for file operations.
"""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Union
from urllib.parse import urlparse


class StorageProtocol(ABC):
    """Interface for storage operations across different storage systems."""

    @classmethod
    def get_protocol_from_path(cls, path: str) -> str:
        """
        Extract protocol from a path string.
        
        Args:
            path: File path which may include a protocol prefix
            
        Returns:
            String protocol name (e.g., 's3', 'file', etc.)
        """
        result = urlparse(path)
        return result.scheme or 'file'
    

    @abstractmethod
    def download(self, source_path: str, destination_path: str) -> str:
        """
        Download a file from source path to destination path.
        
        Args:
            source_path: Path to the source file
            destination_path: Path where the file should be downloaded
            
        Returns:
            String path to the downloaded file
        """
        pass
    
    @abstractmethod
    def upload(self, source_path: str, destination_path: str) -> str:
        """
        Upload a file from source path to destination path.
        
        Args:
            source_path: Path to the source file
            destination_path: Path where the file should be uploaded
            
        Returns:
            String path to the uploaded file
        """
        pass

    @staticmethod
    def ensure_directory(path: Union[str, Path]) -> None:
        """
        Ensure a directory exists, creating it if necessary.
        
        Args:
            path: Directory path to ensure exists
        """
        path_obj = Path(path)
        path_obj.mkdir(parents=True, exist_ok=True)
    
    @staticmethod
    def join_path(base_path: str, *paths: str) -> str:
        """
        Join paths intelligently based on protocol.
        
        Args:
            base_path: Base path which may include protocol
            *paths: Additional path components to join
            
        Returns:
            Joined path as string
        """
        result = urlparse(base_path)
        protocol = result.scheme
        
        if protocol:
            # For URLs, join with forward slashes
            path_parts = [base_path.rstrip('/')]
            for part in paths:
                path_parts.append(part.strip('/'))
            return '/'.join(path_parts)
        else:
            # For local paths, use Path
            result = Path(base_path)
            for part in paths:
                result = result / part
            return str(result)