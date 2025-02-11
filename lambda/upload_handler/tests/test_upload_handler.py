import pytest
import json
from unittest.mock import Mock, patch
from src.main import handler, get_presigned_url
from botocore.exceptions import ClientError

@pytest.fixture
def mock_event():
    return {
        'body': json.dumps({
            'filename': 'test-video.mp4'
        }),
        'requestContext': {
            'authorizer': {
                'claims': {
                    'sub': 'test-user-id',
                    'email': 'test@example.com'
                }
            }
        }
    }

@pytest.fixture
def mock_context():
    return Mock()

@pytest.fixture
def mock_aws_clients():
    with patch('boto3.client') as mock_client:
        s3 = Mock()
        sqs = Mock()
        dynamodb = Mock()
        
        def get_mock_client(service):
            if service == 's3':
                return s3
            elif service == 'sqs':
                return sqs
            return dynamodb
        
        mock_client.side_effect = get_mock_client
        yield s3, sqs, dynamodb

def test_get_presigned_url():
    s3_client = Mock()
    s3_client.generate_presigned_url.return_value = 'https://test-url'
    
    url = get_presigned_url(s3_client, 'test-bucket', 'test-key')
    
    assert url == 'https://test-url'
    s3_client.generate_presigned_url.assert_called_with(
        'put_object',
        Params={
            'Bucket': 'test-bucket',
            'Key': 'test-key',
            'ContentType': 'video/mp4'
        },
        ExpiresIn=3600
    )

def test_get_presigned_url_error():
    s3_client = Mock()
    s3_client.generate_presigned_url.side_effect = ClientError(
        {'Error': {'Code': 'TestException', 'Message': 'Test error'}},
        'generate_presigned_url'
    )
    
    url = get_presigned_url(s3_client, 'test-bucket', 'test-key')
    
    assert url is None

def test_handler_success(mock_event, mock_context, mock_aws_clients):
    s3, sqs, dynamodb = mock_aws_clients
    
    s3.generate_presigned_url.return_value = 'https://test-url'
    
    with patch('uuid.uuid4', return_value='test-video-id'):
        response = handler(mock_event, mock_context)
    
    assert response['statusCode'] == 200
    response_body = json.loads(response['body'])
    assert 'upload_url' in response_body
    assert response_body['video_id'] == 'test-video-id'
    
    # Verify DynamoDB put_item was called
    dynamodb.put_item.assert_called_once()
    
    # Verify SQS message was sent
    sqs.send_message.assert_called_once()

def test_handler_missing_filename(mock_context, mock_aws_clients):
    event = {
        'body': json.dumps({}),
        'requestContext': {
            'authorizer': {
                'claims': {
                    'sub': 'test-user-id'
                }
            }
        }
    }
    
    response = handler(event, mock_context)
    
    assert response['statusCode'] == 400
    assert 'Filename is required' in response['body']

def test_handler_presigned_url_error(mock_event, mock_context, mock_aws_clients):
    s3, _, _ = mock_aws_clients
    s3.generate_presigned_url.side_effect = ClientError(
        {'Error': {'Code': 'TestException', 'Message': 'Test error'}},
        'generate_presigned_url'
    )
    
    response = handler(mock_event, mock_context)
    
    assert response['statusCode'] == 500
    assert 'Error processing upload request' in response['body']

# Add integration tests
@pytest.mark.integration
def test_integration_upload_flow():
    """
    Integration test for the complete upload flow.
    Requires AWS credentials and real AWS services.
    """
    import boto3
    import os
    
    # This test should only run if specifically enabled
    if not os.getenv('RUN_INTEGRATION_TESTS'):
        pytest.skip('Integration tests disabled')
        
    # Use real AWS clients
    s3 = boto3.client('s3')
    sqs = boto3.client('sqs')
    dynamodb = boto3.resource('dynamodb')
    
    # Test the entire flow
    event = {
        'body': json.dumps({
            'filename': 'integration-test.mp4'
        }),
        'requestContext': {
            'authorizer': {
                'claims': {
                    'sub': 'integration-test-user',
                    'email': 'test@example.com'
                }
            }
        }
    }
    
    response = handler(event, None)
    assert response['statusCode'] == 200
    
    # Verify the results in AWS services
    response_body = json.loads(response['body'])
    video_id = response_body['video_id']
    
    # Check DynamoDB entry
    table = dynamodb.Table(os.environ['DYNAMODB_TABLE'])
    item = table.get_item(
        Key={
            'user_id': 'integration-test-user',
            'video_id': video_id
        }
    )
    assert 'Item' in item
    assert item['Item']['status'] == 'PENDING'