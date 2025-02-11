import json
import os
import boto3
import uuid
import logging
from datetime import datetime
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def get_presigned_url(s3_client, bucket, key, expires_in=3600):
    """
    Generate a presigned URL for S3 upload
    """
    try:
        url = s3_client.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': bucket,
                'Key': key,
                'ContentType': 'video/mp4'
            },
            ExpiresIn=expires_in
        )
        return url
    except ClientError as e:
        logger.error(f"Error generating presigned URL: {str(e)}")
        return None

def handler(event, context):
    """
    Lambda handler for initiating video uploads
    """
    try:
        # Parse request body
        body = json.loads(event['body'])
        filename = body.get('filename')
        
        if not filename:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'message': 'Filename is required'
                })
            }

        # Get user info from Cognito authorizer
        user_id = event['requestContext']['authorizer']['claims']['sub']
        
        # Initialize AWS clients
        s3 = boto3.client('s3')
        sqs = boto3.client('sqs')
        dynamodb = boto3.resource('dynamodb')
        
        # Generate unique video ID
        video_id = str(uuid.uuid4())
        
        # Generate S3 key
        video_key = f"inputs/{user_id}/{video_id}/{filename}"
        
        # Get presigned URL for upload
        upload_url = get_presigned_url(s3, os.environ['INPUT_BUCKET'], video_key)
        if not upload_url:
            raise Exception("Failed to generate upload URL")

        # Create entry in DynamoDB
        table = dynamodb.Table(os.environ['DYNAMODB_TABLE'])
        table.put_item(
            Item={
                'user_id': user_id,
                'video_id': video_id,
                'filename': filename,
                'status': 'PENDING',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
        )

        # Send message to SQS for processing
        sqs.send_message(
            QueueUrl=os.environ['SQS_QUEUE_URL'],
            MessageBody=json.dumps({
                'user_id': user_id,
                'video_id': video_id,
                'video_key': video_key
            })
        )

        return {
            'statusCode': 200,
            'body': json.dumps({
                'video_id': video_id,
                'upload_url': upload_url,
                'message': 'Upload URL generated successfully'
            })
        }

    except Exception as e:
        logger.error(f"Error handling upload request: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Error processing upload request',
                'error': str(e)
            })
        }