import boto3
import json
import os
from datetime import datetime

class StorageManager:
    def __init__(self):
        self.s3 = boto3.client('s3')
        self.dynamodb = boto3.resource('dynamodb')
        self.sns = boto3.client('sns')
        self.table = self.dynamodb.Table(os.environ['DYNAMODB_TABLE'])

    def download_video(self, bucket, key, local_path):
        """Downloads video from S3"""
        try:
            self.s3.download_file(bucket, key, local_path)
            return True
        except Exception as e:
            return False

    def upload_zip(self, local_path, bucket, key):
        """Uploads ZIP file to S3"""
        try:
            self.s3.upload_file(local_path, bucket, key)
            return True
        except Exception as e:
            return False

    def update_status(self, user_id, video_id, status, output_url=None, error=None):
        """Updates processing status in DynamoDB"""
        try:
            item = {
                'user_id': user_id,
                'video_id': video_id,
                'status': status,
                'updated_at': datetime.now().isoformat()
            }
            if output_url:
                item['output_url'] = output_url
            if error:
                item['error'] = error

            self.table.update_item(
                Key={
                    'user_id': user_id,
                    'video_id': video_id
                },
                UpdateExpression='SET #status = :status, updated_at = :updated_at' + 
                                (', output_url = :output_url' if output_url else '') +
                                (', error = :error' if error else ''),
                ExpressionAttributeNames={
                    '#status': 'status'
                },
                ExpressionAttributeValues={
                    ':status': status,
                    ':updated_at': item['updated_at'],
                    **(dict([(':output_url', output_url)]) if output_url else {}),
                    **(dict([(':error', error)]) if error else {})
                }
            )
            return True
        except Exception as e:
            return False

    def notify_completion(self, user_id, video_id, status, output_url=None, error=None):
        """Sends notification via SNS"""
        try:
            message = {
                'user_id': user_id,
                'video_id': video_id,
                'status': status,
                'output_url': output_url,
                'error': error
            }
            self.sns.publish(
                TopicArn=os.environ['SNS_TOPIC_ARN'],
                Message=json.dumps(message)
            )
            return True
        except Exception as e:
            return False