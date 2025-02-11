import cv2
import os
import zipfile
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def extract_frames(video_path, output_dir, frame_interval=30):
    """
    Extracts frames from a video and saves them to a directory.
    """
    try:
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        cap = cv2.VideoCapture(video_path)
        frame_count = 0
        saved_count = 0
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            if frame_count % frame_interval == 0:
                frame_name = os.path.join(output_dir, f"frame_{saved_count:04d}.jpg")
                cv2.imwrite(frame_name, frame)
                saved_count += 1
            
            frame_count += 1
        
        cap.release()
        return True, saved_count
    except Exception as e:
        logger.error(f"Error extracting frames: {str(e)}")
        return False, 0

def create_zip(source_dir, zip_path):
    """
    Creates a ZIP file from a directory.
    """
    try:
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(source_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, source_dir)
                    zipf.write(file_path, arcname)
        return True
    except Exception as e:
        logger.error(f"Error creating ZIP: {str(e)}")
        return False