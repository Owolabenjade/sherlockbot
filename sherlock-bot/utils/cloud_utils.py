# utils/cloud_utils.py - Cloud link download utilities
import os
import re
import requests
import time
import uuid
from utils.logger import get_logger
from config import Config

# Initialize logger
logger = get_logger()

def is_valid_cloud_link(url):
    """
    Check if URL is a valid cloud storage link
    
    Args:
        url (str): URL to check
        
    Returns:
        bool: Whether URL is a valid cloud link
    """
    cloud_patterns = [
        r'drive\.google\.com',
        r'docs\.google\.com',
        r'dropbox\.com',
        r'onedrive\.live\.com',
        r'1drv\.ms',
        r'mega\.nz',
        r'mediafire\.com',
        r'wetransfer\.com'
    ]
    
    for pattern in cloud_patterns:
        if re.search(pattern, url, re.IGNORECASE):
            return True
    
    return False

def convert_to_direct_download_link(url):
    """
    Convert cloud share links to direct download links
    
    Args:
        url (str): Cloud share URL
        
    Returns:
        str: Direct download URL (if possible)
    """
    # Google Drive
    if 'drive.google.com' in url:
        # Extract file ID from various Google Drive URL formats
        file_id = None
        
        # Format: https://drive.google.com/file/d/FILE_ID/view
        match = re.search(r'/file/d/([a-zA-Z0-9_-]+)', url)
        if match:
            file_id = match.group(1)
        
        # Format: https://drive.google.com/open?id=FILE_ID
        match = re.search(r'[?&]id=([a-zA-Z0-9_-]+)', url)
        if match:
            file_id = match.group(1)
        
        if file_id:
            # Convert to direct download link
            return f"https://drive.google.com/uc?export=download&id={file_id}"
    
    # Dropbox
    elif 'dropbox.com' in url:
        # Replace dl=0 with dl=1 for direct download
        if '?dl=0' in url:
            return url.replace('?dl=0', '?dl=1')
        elif '?' in url:
            return url + '&dl=1'
        else:
            return url + '?dl=1'
    
    # OneDrive
    elif 'onedrive.live.com' in url or '1drv.ms' in url:
        # OneDrive direct download is complex, return as-is for now
        logger.warning("OneDrive direct download conversion not implemented")
        return url
    
    # Return original URL if no conversion available
    return url

def download_from_cloud_link(url, extension='pdf'):
    """
    Download file from cloud storage link
    
    Args:
        url (str): Cloud storage URL
        extension (str): Expected file extension
        
    Returns:
        str: Path to downloaded file
    """
    try:
        # Validate URL
        if not is_valid_cloud_link(url):
            raise Exception("Invalid cloud storage link")
        
        # Convert to direct download link if possible
        direct_url = convert_to_direct_download_link(url)
        logger.info(f"Attempting to download from cloud link")
        
        # Create temp folder if it doesn't exist
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        
        # Generate temp filename
        filename = f"cv_{int(time.time())}_{uuid.uuid4().hex[:8]}.{extension}"
        file_path = os.path.join(Config.UPLOAD_FOLDER, filename)
        
        # Download file
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(direct_url, headers=headers, stream=True, timeout=30)
        
        if response.status_code == 200:
            # Check if it's actually a file or an HTML page
            content_type = response.headers.get('content-type', '')
            
            if 'text/html' in content_type:
                logger.warning("Received HTML instead of file. Link might require authentication.")
                raise Exception("Cloud link requires authentication or is not publicly accessible")
            
            # Save file
            file_size = 0
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        file_size += len(chunk)
            
            logger.info(f"Downloaded file to {file_path} (size: {file_size} bytes)")
            
            if file_size == 0:
                raise Exception("Downloaded file is empty")
            
            # Try to detect actual file type
            actual_extension = detect_file_type(file_path)
            if actual_extension and actual_extension != extension:
                # Rename file with correct extension
                new_path = file_path.replace(f'.{extension}', f'.{actual_extension}')
                os.rename(file_path, new_path)
                file_path = new_path
                logger.info(f"Detected actual file type: {actual_extension}")
            
            return file_path
        else:
            raise Exception(f"Failed to download file: HTTP {response.status_code}")
            
    except Exception as e:
        logger.error(f"Error downloading from cloud link: {str(e)}")
        raise e

def detect_file_type(file_path):
    """
    Detect actual file type by reading file headers
    
    Args:
        file_path (str): Path to file
        
    Returns:
        str: Detected extension or None
    """
    try:
        with open(file_path, 'rb') as f:
            header = f.read(16)
        
        # PDF
        if header.startswith(b'%PDF'):
            return 'pdf'
        
        # DOCX (ZIP archive starting with PK)
        if header.startswith(b'PK\x03\x04'):
            return 'docx'
        
        # DOC
        if header.startswith(b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1'):
            return 'doc'
        
        return None
        
    except Exception as e:
        logger.error(f"Error detecting file type: {str(e)}")
        return None