"""
Clay filesystem storage module for handling file operations across different storage systems.
"""

from clay.storage.fs.interface import StorageProtocol
from clay.storage.fs.s3 import S3Storage
from clay.storage.fs.storage import create_provider, process_input_list, process_output_list

__all__ = [
    'StorageProtocol',
    'S3Storage',
    'process_input_list',
    'process_output_list',
    'create_provider'
]