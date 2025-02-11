import pytest
import os
import json
from unittest.mock import Mock, patch, MagicMock
from src.main import handler
from src.utils.video import extract_frames, create_zip

@pytest.fixture
def mock_event():
    return {
        'Records': [{
            'body': json.dumps({
                'user_id': 'test-user',
                'video_id': 'test-video-123',
                'video_key': 'inputs/test-user/test-video-123/video.mp4'
            })
        }]
    }

@pytest.fixture
def mock_context():
    return Mock()

@pytest.fixture
def mock_storage():
    with patch('src.main.StorageManager') as mock:
        storage_instance = Mock()
        mock.return_value = storage_instance
        yield storage_instance

@pytest.fixture
def mock_video_utils():
    with patch('src.main.extract_frames') as mock_extract, \
         patch('src.main.create_zip') as mock_zip:
        mock_extract.return_value = (True, 10)
        mock_zip.return_value = True
        yield (mock_extract, mock_zip)

def test_extract_frames(tmp_path):
    # Create a small test video file
    video_path = str(tmp_path / "test.mp4")
    frames_dir = str(tmp_path / "frames")
    
    # Mock cv2.VideoCapture
    with patch('cv2.VideoCapture') as mock_cap:
        mock_cap.return_value.isOpened.return_value = True
        mock_cap.return_value.read.side_effect = [(True, Mock()), (True, Mock()), (False, None)]
        
        success, count = extract_frames(video_path, frames_dir, frame_interval=1)
        
        assert success
        assert count == 2

def test_create_zip(tmp_path):
    # Create test files
    source_dir = tmp_path / "frames"
    source_dir.mkdir()
    (source_dir / "frame1.jpg").write_text("test1")
    (source_dir / "frame2.jpg").write_text("test2")
    
    zip_path = str(tmp_path / "test.zip")
    
    assert create_zip(str(source_dir), zip_path)
    assert os.path.exists(zip_path)

def test_handler_success(mock_event, mock_context, mock_storage, mock_video_utils):
    mock_storage.download_video.return_value = True
    mock_storage.upload_zip.return_value = True
    mock_storage.update_status.return_value = True
    mock_storage.notify_completion.return_value = True
    
    response = handler(mock_event, mock_context)
    
    assert response['statusCode'] == 200
    assert 'video_id' in json.loads(response['body'])
    mock_storage.update_status.assert_called_with('test-user', 'test-video-123', 'COMPLETED', 
                                                output_url=mock.ANY)

def test_handler_download_failure(mock_event, mock_context, mock_storage):
    mock_storage.download_video.return_value = False
    
    response = handler(mock_event, mock_context)
    
    assert response['statusCode'] == 500
    mock_storage.update_status.assert_called_with('test-user', 'test-video-123', 'ERROR', 
                                                error=mock.ANY)

