import json
import os
import tempfile
import logging
from utils.video import extract_frames, create_zip
from utils.storage import StorageManager

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event, context):
    """
    Lambda handler for processing videos and creating frame ZIPs.
    """
    try:
        # Parse SQS message
        message = json.loads(event['Records'][0]['body'])
        user_id = message['user_id']
        video_id = message['video_id']
        input_bucket = os.environ['INPUT_BUCKET']
        output_bucket = os.environ['OUTPUT_BUCKET']
        video_key = message['video_key']

        storage = StorageManager()
        
        # Update status to processing
        storage.update_status(user_id, video_id, 'PROCESSING')

        with tempfile.TemporaryDirectory() as temp_dir:
            video_path = os.path.join(temp_dir, 'video.mp4')
            frames_dir = os.path.join(temp_dir, 'frames')
            zip_path = os.path.join(temp_dir, 'frames.zip')

            # Download video
            if not storage.download_video(input_bucket, video_key, video_path):
                raise Exception("Failed to download video")

            # Extract frames
            success, frame_count = extract_frames(video_path, frames_dir)
            if not success:
                raise Exception("Failed to extract frames")

            # Create ZIP
            if not create_zip(frames_dir, zip_path):
                raise Exception("Failed to create ZIP")

            # Upload ZIP
            zip_key = f"outputs/{user_id}/{video_id}/frames.zip"
            if not storage.upload_zip(zip_path, output_bucket, zip_key):
                raise Exception("Failed to upload ZIP")

            # Update status and notify
            output_url = f"s3://{output_bucket}/{zip_key}"
            storage.update_status(user_id, video_id, 'COMPLETED', output_url=output_url)
            storage.notify_completion(user_id, video_id, 'COMPLETED', output_url=output_url)

            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': 'Processing completed successfully',
                    'video_id': video_id,
                    'output_url': output_url,
                    'frame_count': frame_count
                })
            }

    except Exception as e:
        error_message = str(e)
        logger.error(f"Error processing video: {error_message}")
        
        if 'storage' in locals() and 'user_id' in locals() and 'video_id' in locals():
            storage.update_status(user_id, video_id, 'ERROR', error=error_message)
            storage.notify_completion(user_id, video_id, 'ERROR', error=error_message)

        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Error processing video',
                'error': error_message
            })
        }