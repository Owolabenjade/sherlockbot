# utils/file_utils.py - File handling utilities
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
        logger.info(f"URL: {url[:80]}..." if len(url) > 80 else f"URL: {url}")
        
        # Parse the URL to extract message SID and media SID
        # URL format: https://api.twilio.com/2010-04-01/Accounts/{AccountSid}/Messages/{MessageSid}/Media/{MediaSid}
        url_parts = url.split('/')
        
        if 'Messages' in url and 'Media' in url:
            # Extract the Message SID and Media SID from the URL
            message_sid_index = url_parts.index('Messages') + 1
            media_sid_index = url_parts.index('Media') + 1
            
            message_sid = url_parts[message_sid_index]
            media_sid = url_parts[media_sid_index]
            
            logger.info(f"Message SID: {message_sid}")
            logger.info(f"Media SID: {media_sid}")
            
            # Initialize Twilio client
            client = Client(Config.TWILIO_ACCOUNT_SID, Config.TWILIO_AUTH_TOKEN)
            
            # Get the media resource
            try:
                media = client.messages(message_sid).media(media_sid).fetch()
                
                # Get the actual media URL with authentication
                # The media.uri gives us the path, we need to construct the full URL
                media_url = f"https://api.twilio.com{media.uri}"
                
                # Remove .json extension if present
                if media_url.endswith('.json'):
                    media_url = media_url[:-5]
                
                logger.info(f"Fetching media from authenticated URL")
                
                # Now download with authentication
                auth = (Config.TWILIO_ACCOUNT_SID, Config.TWILIO_AUTH_TOKEN)
                response = requests.get(media_url, stream=True, timeout=30, auth=auth)
                
                if response.status_code == 200:
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
                else:
                    logger.error(f"Failed to download media. Status: {response.status_code}")
                    logger.error(f"Response: {response.text[:500]}")
                    raise Exception(f"Failed to download file: {response.status_code}")
                    
            except Exception as e:
                logger.error(f"Error using Twilio SDK: {str(e)}")
                # Fallback to direct download with basic auth
                logger.info("Falling back to direct download method")
                
        # Fallback method - direct download with basic auth
        auth = (Config.TWILIO_ACCOUNT_SID, Config.TWILIO_AUTH_TOKEN)
        headers = {
            'User-Agent': 'TwilioWhatsApp/1.0',
            'Accept': '*/*'
        }
        
        response = requests.get(url, stream=True, timeout=30, auth=auth, headers=headers)
        
        if response.status_code != 200:
            logger.error(f"Failed to download file. Status code: {response.status_code}")
            logger.error(f"Response headers: {dict(response.headers)}")
            logger.error(f"Response content: {response.text[:500]}")
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