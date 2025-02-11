import json
import os
import boto3
import logging
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def get_user_email(cognito, user_pool_id, user_id):
    """
    Get user email from Cognito
    """
    try:
        response = cognito.admin_get_user(
            UserPoolId=user_pool_id,
            Username=user_id
        )
        for attr in response['UserAttributes']:
            if attr['Name'] == 'email':
                return attr['Value']
        return None
    except Exception as e:
        logger.error(f"Error getting user email: {str(e)}")
        return None

def send_email(ses, sender, recipient, subject, body):
    """
    Send email using SES
    """
    try:
        response = ses.send_email(
            Source=sender,
            Destination={
                'ToAddresses': [recipient]
            },
            Message={
                'Subject': {
                    'Data': subject
                },
                'Body': {
                    'Html': {
                        'Data': body
                    }
                }
            }
        )
        return True
    except ClientError as e:
        logger.error(f"Error sending email: {str(e)}")
        return False

def get_email_template(status, video_id, output_url=None, error=None):
    """
    Generate email content based on processing status
    """
    if status == 'COMPLETED':
        subject = "Video Processing Completed"
        body = f"""
        <h2>Video Processing Completed Successfully</h2>
        <p>Your video (ID: {video_id}) has been processed successfully.</p>
        <p>You can download your processed frames at: {output_url}</p>
        <br>
        <p>Thank you for using our service!</p>
        """
    elif status == 'ERROR':
        subject = "Video Processing Failed"
        body = f"""
        <h2>Video Processing Failed</h2>
        <p>Unfortunately, there was an error processing your video (ID: {video_id}).</p>
        <p>Error details: {error}</p>
        <p>Please try uploading your video again or contact support if the problem persists.</p>
        """
    else:
        subject = "Video Processing Update"
        body = f"""
        <h2>Video Processing Status Update</h2>
        <p>Your video (ID: {video_id}) status has been updated to: {status}</p>
        """
    
    return subject, body

def handler(event, context):
    """
    Lambda handler for sending notifications about video processing status
    """
    try:
        # Parse SNS message
        message = json.loads(event['Records'][0]['Sns']['Message'])
        user_id = message['user_id']
        video_id = message['video_id']
        status = message['status']
        output_url = message.get('output_url')
        error = message.get('error')

        # Initialize AWS clients
        cognito = boto3.client('cognito-idp')
        ses = boto3.client('ses')

        # Get user email from Cognito
        user_email = get_user_email(
            cognito,
            os.environ['COGNITO_USER_POOL_ID'],
            user_id
        )

        if not user_email:
            raise Exception(f"Could not find email for user {user_id}")

        # Generate email content
        subject, body = get_email_template(status, video_id, output_url, error)

        # Send email
        if not send_email(
            ses,
            os.environ['SENDER_EMAIL'],
            user_email,
            subject,
            body
        ):
            raise Exception("Failed to send email notification")

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Notification sent successfully',
                'user_id': user_id,
                'video_id': video_id
            })
        }

    except Exception as e:
        logger.error(f"Error sending notification: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Error sending notification',
                'error': str(e)
            })
        }