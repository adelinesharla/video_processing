import pytest
import os
import json
from unittest.mock import Mock, patch, MagicMock
from src.utils.storage import StorageManager

def test_storage_manager():
    with patch('boto3.client') as mock_client, \
         patch('boto3.resource') as mock_resource:
        
        s3 = Mock()
        mock_client.return_value = s3
        
        storage = StorageManager()
        
        # Test download
        s3.download_file.return_value = None
        assert storage.download_video('bucket', 'key', 'local_path')
        s3.download_file.assert_called_with('bucket', 'key', 'local_path')
        
        # Test upload
        s3.upload_file.return_value = None
        assert storage.upload_zip('local_path', 'bucket', 'key')
        s3.upload_file.assert_called_with('local_path', 'bucket', 'key')