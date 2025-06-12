# utils/file_utils.py - File handling utilities
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
        
        # Log the URL (sanitized for security)
        logger.info(f"Attempting to download from Twilio media URL")
        logger.info(f"URL domain: {url.split('/')[2] if '/' in url else 'unknown'}")
        
        # Download file with Twilio authentication
        # Twilio media URLs require basic authentication
        auth = HTTPBasicAuth(Config.TWILIO_ACCOUNT_SID, Config.TWILIO_AUTH_TOKEN)
        
        # Add headers that might be required
        headers = {
            'User-Agent': 'TwilioWhatsApp/1.0',
            'Accept': '*/*'
        }
        
        logger.info(f"Downloading file from Twilio media URL with authentication")
        logger.info(f"Using Account SID: {Config.TWILIO_ACCOUNT_SID[:8]}...")  # Log first 8 chars only
        
        response = requests.get(url, stream=True, timeout=30, auth=auth, headers=headers)
        
        if response.status_code == 401:
            # Try alternative authentication method
            logger.warning("Basic auth failed, trying with URL parameters")
            
            # Parse URL and add auth parameters
            if '?' in url:
                auth_url = f"{url}&AccountSid={Config.TWILIO_ACCOUNT_SID}&AuthToken={Config.TWILIO_AUTH_TOKEN}"
            else:
                auth_url = f"{url}?AccountSid={Config.TWILIO_ACCOUNT_SID}&AuthToken={Config.TWILIO_AUTH_TOKEN}"
            
            response = requests.get(auth_url, stream=True, timeout=30, headers=headers)
        
        if response.status_code != 200:
            logger.error(f"Failed to download file. Status code: {response.status_code}")
            logger.error(f"Response headers: {response.headers}")
            logger.error(f"Response content: {response.text[:500]}")  # First 500 chars
            raise Exception(f"Failed to download file: {response.status_code}")
        
        # Save file
        file_size = 0
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    file_size += len(chunk)
        
        logger.info(f"Downloaded file to {file_path} (size: {file_size} bytes)")
        
        # Verify file was downloaded
        if file_size == 0:
            raise Exception("Downloaded file is empty")
        
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