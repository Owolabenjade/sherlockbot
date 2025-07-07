# utils/file_utils.py - Production WhatsApp File Handling
import os
import uuid
import time
import requests
from twilio.rest import Client
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

def get_file_extension(content_type):
    """
    Get file extension from content type
    
    Args:
        content_type (str): Content type (MIME type)
        
    Returns:
        str: File extension
    """
    # Use the mapping from config
    return Config.WHATSAPP_SUPPORTED_FORMATS.get(content_type, 'pdf')

def save_temp_file(media_url, extension):
    """
    Download file from WhatsApp Media URL
    
    Args:
        media_url (str): WhatsApp media URL
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
        
        logger.info(f"📥 Downloading WhatsApp media file")
        
        # Initialize Twilio client for authenticated download
        client = Client(Config.TWILIO_ACCOUNT_SID, Config.TWILIO_AUTH_TOKEN)
        
        # Extract message SID and media SID from URL
        url_parts = media_url.split('/')
        
        if 'Messages' in url_parts and 'Media' in url_parts:
            message_sid_index = url_parts.index('Messages') + 1
            media_sid_index = url_parts.index('Media') + 1
            
            message_sid = url_parts[message_sid_index]
            media_sid = url_parts[media_sid_index]
            
            logger.info(f"Message SID: {message_sid}, Media SID: {media_sid}")
            
            # Get the media resource
            try:
                media = client.messages(message_sid).media(media_sid).fetch()
                
                # Construct the actual media URL
                media_download_url = f"https://api.twilio.com{media.uri}"
                
                # Remove .json extension if present
                if media_download_url.endswith('.json'):
                    media_download_url = media_download_url[:-5]
                
                # Download with authentication
                auth = (Config.TWILIO_ACCOUNT_SID, Config.TWILIO_AUTH_TOKEN)
                response = requests.get(media_download_url, stream=True, timeout=30, auth=auth)
                
                if response.status_code == 200:
                    # Save file
                    file_size = 0
                    with open(file_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                                file_size += len(chunk)
                                
                                # Check file size limit
                                if file_size > Config.WHATSAPP_MAX_FILE_SIZE:
                                    logger.error(f"File size ({file_size}) exceeds WhatsApp limit")
                                    raise Exception("File too large. Maximum size is 16MB.")
                    
                    logger.info(f"✅ Downloaded file to {file_path} (size: {file_size} bytes)")
                    
                    # Verify file was downloaded
                    if file_size == 0:
                        raise Exception("Downloaded file is empty")
                    
                    return file_path
                else:
                    logger.error(f"Failed to download media. Status: {response.status_code}")
                    raise Exception(f"Failed to download file: HTTP {response.status_code}")
                    
            except Exception as e:
                logger.error(f"Error using Twilio SDK: {str(e)}")
                raise e
        else:
            raise Exception("Invalid Twilio media URL format")
    
    except Exception as e:
        logger.error(f"Error saving temp file: {str(e)}")
        # Clean up partial file if it exists
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)
        raise e

def validate_file_size(file_path):
    """
    Validate file size is within WhatsApp limits
    
    Args:
        file_path (str): Path to file
        
    Returns:
        bool: True if file size is valid
    """
    try:
        file_size = os.path.getsize(file_path)
        max_size = Config.WHATSAPP_MAX_FILE_SIZE
        
        if file_size > max_size:
            logger.error(f"File size {file_size} exceeds limit of {max_size}")
            return False
            
        logger.info(f"File size {file_size} is within limits")
        return True
        
    except Exception as e:
        logger.error(f"Error checking file size: {str(e)}")
        return False

def cleanup_temp_files(directory=None, older_than_hours=1):
    """
    Clean up old temporary files
    
    Args:
        directory (str): Directory to clean (default: Config.UPLOAD_FOLDER)
        older_than_hours (int): Delete files older than this many hours
    """
    try:
        if directory is None:
            directory = Config.UPLOAD_FOLDER
            
        if not os.path.exists(directory):
            return
            
        current_time = time.time()
        cutoff_time = current_time - (older_than_hours * 3600)
        
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            
            # Only clean up CV files
            if filename.startswith('cv_') and os.path.isfile(file_path):
                file_modified = os.path.getmtime(file_path)
                
                if file_modified < cutoff_time:
                    os.remove(file_path)
                    logger.info(f"🗑️ Cleaned up old file: {filename}")
                    
    except Exception as e:
        logger.error(f"Error cleaning up temp files: {str(e)}")