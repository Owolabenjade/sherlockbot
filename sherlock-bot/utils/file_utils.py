# utils/file_utils.py - File handling utilities with Twilio authentication
import os
import uuid
import time
import requests
from requests.auth import HTTPBasicAuth
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
        
        # Download file with Twilio authentication
        # Twilio media URLs require HTTP Basic Auth using Account SID and Auth Token
        auth = HTTPBasicAuth(Config.TWILIO_ACCOUNT_SID, Config.TWILIO_AUTH_TOKEN)
        
        logger.info(f"Downloading file from Twilio: {url}")
        logger.info(f"Using Twilio Account SID: {Config.TWILIO_ACCOUNT_SID[:8]}...")
        
        response = requests.get(
            url, 
            stream=True, 
            timeout=30,
            auth=auth,  # Add Twilio authentication
            headers={
                'User-Agent': 'Sherlock-Bot/1.0'
            }
        )
        
        logger.info(f"Response status code: {response.status_code}")
        
        if response.status_code != 200:
            logger.error(f"Failed to download file from Twilio. Status: {response.status_code}")
            logger.error(f"Response headers: {dict(response.headers)}")
            logger.error(f"Response content: {response.text[:500]}")
            raise Exception(f"Failed to download file: {response.status_code}")
        
        # Save file
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        # Verify file was saved and has content
        if not os.path.exists(file_path):
            raise Exception("File was not saved successfully")
        
        file_size = os.path.getsize(file_path)
        if file_size == 0:
            raise Exception("Downloaded file is empty")
        
        logger.info(f"Downloaded file to {file_path} (size: {file_size} bytes)")
        
        return file_path
    
    except Exception as e:
        logger.error(f"Error saving temp file: {str(e)}")
        # Clean up partial file if it exists
        if 'file_path' in locals() and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
                pass
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