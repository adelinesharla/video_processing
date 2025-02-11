import pytest
import json
from unittest.mock import Mock, patch
from src.main import handler, get_user_email, send_email, get_email_template

@pytest.fixture
def mock_event():
    return {
        'Records': [{
            'Sns': {
                'Message': json.dumps({
                    'user_id': 'test-user',
                    'video_id': 'test-video-123',
                    'status': 'COMPLETED',
                    'output_url': 's3://test-bucket/test.zip'
                })
            }
        }]
    }

@pytest.fixture
def mock_context():
    return Mock()

@pytest.fixture
def mock_aws_clients():
    with patch('boto3.client') as mock_client:
        cognito = Mock()
        ses = Mock()
        
        def get_mock_client(service):
            if service == 'cognito-idp':
                return cognito
            return ses
        
        mock_client.side_effect = get_mock_client
        yield cognito, ses

def test_get_user_email():
    cognito = Mock()
    cognito.admin_get_user.return_value = {
        'UserAttributes': [
            {'Name': 'email', 'Value': 'test@example.com'}
        ]
    }
    
    email = get_user_email(cognito, 'user-pool-id', 'test-user')
    
    assert email == 'test@example.com'
    cognito.admin_get_user.assert_called_with(
        UserPoolId='user-pool-id',
        Username='test-user'
    )

def test_get_user_email_no_email():
    cognito = Mock()
    cognito.admin_get_user.return_value = {
        'UserAttributes': []
    }
    
    email = get_user_email(cognito, 'user-pool-id', 'test-user')
    
    assert email is None

def test_get_user_email_error():
    cognito = Mock()
    cognito.admin_get_user.side_effect = Exception('Test error')
    
    email = get_user_email(cognito, 'user-pool-id', 'test-user')
    
    assert email is None

def test_send_email():
    ses = Mock()
    
    success = send_email(
        ses,
        'sender@example.com',
        'recipient@example.com',
        'Test Subject',
        'Test Body'
    )
    
    assert success
    ses.send_email.assert_called_once()

def test_send_email_error():
    ses = Mock()
    ses.send_email.side_effect = Exception('Test error')
    
    success = send_email(
        ses,
        'sender@example.com',
        'recipient@example.com',
        'Test Subject',
        'Test Body'
    )
    
    assert not success

def test_get_email_template_completed():
    subject, body = get_email_template(
        'COMPLETED',
        'test-video-123',
        output_url='s3://test-bucket/test.zip'
    )
    
    assert 'Completed' in subject
    assert 'test-video-123' in body
    assert 's3://test-bucket/test.zip' in body

def test_get_email_template_error():
    subject, body = get_email_template(
        'ERROR',
        'test-video-123',
        error='Test error message'
    )
    
    assert 'Failed' in subject
    assert 'test-video-123' in body
    assert 'Test error message' in body

def test_handler_success(mock_event, mock_context, mock_aws_clients):
    cognito, ses = mock_aws_clients
    
    # Mock Cognito response
    cognito.admin_get_user.return_value = {
        'UserAttributes': [
            {'Name': 'email', 'Value': 'test@example.com'}
        ]
    }
    
    # Mock SES response
    ses.send_email.return_value = {'MessageId': 'test-message-id'}
    
    response = handler(mock_event, mock_context)
    
    assert response['statusCode'] == 200
    response_body = json.loads(response['body'])
    assert response_body['message'] == 'Notification sent successfully'
    assert response_body['user_id'] == 'test-user'
    assert response_body['video_id'] == 'test-video-123'
    
    # Verify email was sent
    ses.send_email.assert_called_once()

def test_handler_no_user_email(mock_event, mock_context, mock_aws_clients):
    cognito, ses = mock_aws_clients
    
    # Mock Cognito response with no email
    cognito.admin_get_user.return_value = {
        'UserAttributes': []
    }
    
    response = handler(mock_event, mock_context)
    
    assert response['statusCode'] == 500
    assert 'Could not find email' in response['body']
    
    # Verify email was not sent
    ses.send_email.assert_not_called()

def test_handler_cognito_error(mock_event, mock_context, mock_aws_clients):
    cognito, ses = mock_aws_clients
    
    # Mock Cognito error
    cognito.admin_get_user.side_effect = Exception('Cognito error')
    
    response = handler(mock_event, mock_context)
    
    assert response['statusCode'] == 500
    assert 'Error sending notification' in response['body']
    
    # Verify email was not sent
    ses.send_email.assert_not_called()

def test_handler_ses_error(mock_event, mock_context, mock_aws_clients):
    cognito, ses = mock_aws_clients
    
    # Mock Cognito success
    cognito.admin_get_user.return_value = {
        'UserAttributes': [
            {'Name': 'email', 'Value': 'test@example.com'}
        ]
    }
    
    # Mock SES error
    ses.send_email.side_effect = Exception('SES error')
    
    response = handler(mock_event, mock_context)
    
    assert response['statusCode'] == 500
    assert 'Error sending notification' in response['body']

@pytest.mark.integration
def test_integration_notification_flow():
    """
    Integration test for the complete notification flow.
    Requires AWS credentials and real AWS services.
    """
    import boto3
    import os
    
    # This test should only run if specifically enabled
    if not os.getenv('RUN_INTEGRATION_TESTS'):
        pytest.skip('Integration tests disabled')
    
    # Create event with real data
    event = {
        'Records': [{
            'Sns': {
                'Message': json.dumps({
                    'user_id': os.getenv('TEST_USER_ID'),
                    'video_id': 'integration-test-video',
                    'status': 'COMPLETED',
                    'output_url': 's3://test-bucket/test.zip'
                })
            }
        }]
    }
    
    response = handler(event, None)
    assert response['statusCode'] == 200
    
    # Verify email was sent (check SES logs or test email inbox)
    response_body = json.loads(response['body'])
    assert response_body['message'] == 'Notification sent successfully'