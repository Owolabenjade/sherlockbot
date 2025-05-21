# utils/file_utils.py - File handling utilities
import os
import uuid
import time
import requests
from config import Config
from utils.logger import get_logger

# Initialize logger
logger = get_logger()

def allowed_file(filename):
    """
    Check if file has allowed extension
    
    Args:
        filename (str): Filename to check
        
    Returns:
        bool: Whether file extension is allowed
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

def save_temp_file(url, extension):
    """
    Download file from URL and save to temp location
    
    Args:
        url (str): URL to download from
        extension (str): File extension
        
    Returns:
        str: Path to saved file
    """
    try:
        # Create temp folder if it doesn't exist
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        
        # Generate temp filename
        filename = f"cv_{int(time.time())}_{uuid.uuid4().hex[:8]}.{extension}"
        file_path = os.path.join(Config.UPLOAD_FOLDER, filename)
        
        # Download file
        response = requests.get(url, stream=True, timeout=30)
        
        if response.status_code != 200:
            raise Exception(f"Failed to download file: {response.status_code}")
        
        # Save file
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        logger.info(f"Downloaded file to {file_path}")
        
        return file_path
    
    except Exception as e:
        logger.error(f"Error saving temp file: {str(e)}")
        raise e

def get_file_extension(content_type):
    """
    Get file extension from content type
    
    Args:
        content_type (str): Content type (MIME type)
        
    Returns:
        str: File extension
    """
    if content_type == 'application/pdf':
        return 'pdf'
    elif content_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
        return 'docx'
    elif content_type == 'application/msword':
        return 'doc'
    else:
        return 'pdf'  # Default to PDF