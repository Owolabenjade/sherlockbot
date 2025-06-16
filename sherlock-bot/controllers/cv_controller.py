# controllers/cv_controller.py
import os
import uuid
import time
import requests
import tempfile
from datetime import datetime
from services.firebase_service import upload_file_to_storage, get_file_download_url
from services.cv_service import process_basic_review, process_advanced_review
from services.firestore_service import save_review_result, get_review
from services.sendgrid_service import send_review_email
from utils.logger import get_logger

# Initialize logger
logger = get_logger()

def process_cv_upload(cloud_link_or_storage_path, review_type, phone_number, email=None):
    """
    Process CV file from cloud link or storage path - FIXED VERSION
    
    Args:
        cloud_link_or_storage_path (str): Cloud link URL or Firebase Storage path
        review_type (str): Type of review (basic or advanced)
        phone_number (str): User's phone number
        email (str, optional): User's email address
        
    Returns:
        dict: Review results
    """
    logger.info(f"🚀 Starting CV processing for {review_type} review")
    logger.info(f"📁 Input: {cloud_link_or_storage_path[:100]}...")
    
    storage_path = None
    local_file_path = None
    
    try:
        # Check if input is a cloud link or storage path
        if cloud_link_or_storage_path.startswith('http'):
            # It's a cloud link - download and upload to Firebase Storage
            logger.info(f"🔗 Processing CV from cloud link: {cloud_link_or_storage_path[:50]}...")
            
            try:
                # Download from cloud link using direct approach
                local_file_path = download_from_google_drive(cloud_link_or_storage_path)
                logger.info(f"✅ Downloaded CV to: {local_file_path}")
                
                # Upload to Firebase Storage
                storage_path = upload_cv_to_firebase(local_file_path, phone_number)
                logger.info(f"☁️ Uploaded CV to Firebase Storage: {storage_path}")
                
            except Exception as download_error:
                logger.error(f"❌ Error downloading from cloud link: {str(download_error)}")
                
                # Return early with error for cloud links that fail
                return {
                    'success': False,
                    'error': f"Could not access CV from the provided link. Please ensure the link has public view access and try again. Error: {str(download_error)}"
                }
        else:
            # It's already a storage path
            storage_path = cloud_link_or_storage_path
            logger.info(f"📂 Using existing storage path: {storage_path}")
        
        # Process the review using the storage path
        logger.info(f"🔄 Starting {review_type} review processing...")
        
        if review_type == 'basic':
            review_result = process_basic_review(storage_path)
        else:
            review_result = process_advanced_review(storage_path)
        
        # Check if review was successful
        if not review_result.get('success'):
            error_msg = review_result.get('error', 'Failed to process review')
            logger.error(f"❌ Error processing {review_type} review: {error_msg}")
            return {
                'success': False,
                'error': error_msg
            }
        
        # Add metadata
        review_result['timestamp'] = datetime.now().isoformat()
        review_result['review_type'] = review_type
        review_result['cv_storage_path'] = storage_path
        
        # Store original cloud link if provided
        if cloud_link_or_storage_path.startswith('http'):
            review_result['cv_cloud_link'] = cloud_link_or_storage_path
        
        # Handle email for advanced review
        if email and review_type == 'advanced':
            download_link = review_result.get('download_link', '')
            
            if download_link:
                try:
                    email_result = send_review_email(
                        email,
                        phone_number,
                        review_result,
                        download_link
                    )
                    review_result['email_sent'] = email_result.get('success', False)
                    review_result['email'] = email
                    logger.info(f"📧 Email sent to {email}: {email_result.get('success', False)}")
                except Exception as email_error:
                    logger.error(f"❌ Error sending email: {str(email_error)}")
                    review_result['email_sent'] = False
        
        # Save review to Firestore
        try:
            review_id = save_review_result(phone_number, review_result)
            review_result['id'] = review_id
            logger.info(f"💾 Review saved with ID: {review_id}")
        except Exception as save_error:
            logger.error(f"❌ Error saving review: {str(save_error)}")
            # Continue even if save fails - user still gets results
        
        logger.info(f"✅ Completed {review_type} review for {phone_number}")
        
        return review_result
    
    except Exception as e:
        logger.error(f"❌ Error in process_cv_upload: {str(e)}")
        return {
            'success': False,
            'error': f"An error occurred while processing your CV: {str(e)}"
        }
    
    finally:
        # Clean up local file if it was downloaded
        if local_file_path and os.path.exists(local_file_path):
            try:
                os.remove(local_file_path)
                logger.info(f"🗑️ Cleaned up temporary file: {local_file_path}")
            except Exception as cleanup_error:
                logger.warning(f"⚠️ Could not clean up temporary file: {cleanup_error}")

def download_from_google_drive(share_url):
    """
    Download file from Google Drive share URL
    
    Args:
        share_url (str): Google Drive share URL
        
    Returns:
        str: Path to downloaded file
    """
    logger.info("📥 Attempting to download from Google Drive")
    
    try:
        # Extract file ID from Google Drive URL
        if '/document/d/' in share_url:
            # Google Docs format
            file_id = share_url.split('/document/d/')[1].split('/')[0]
            # Convert to export URL for DOCX format
            download_url = f"https://docs.google.com/document/d/{file_id}/export?format=docx"
            file_extension = '.docx'
        elif '/file/d/' in share_url:
            # Google Drive file format
            file_id = share_url.split('/file/d/')[1].split('/')[0]
            download_url = f"https://drive.google.com/uc?export=download&id={file_id}"
            file_extension = '.pdf'  # Default to PDF, will be detected later
        else:
            # Try direct download if it's already a direct link
            download_url = share_url
            file_extension = '.pdf'
        
        logger.info(f"🔗 Download URL: {download_url}")
        
        # Create temporary file
        temp_dir = tempfile.gettempdir()
        temp_filename = f"cv_download_{int(time.time())}_{uuid.uuid4().hex[:8]}{file_extension}"
        temp_path = os.path.join(temp_dir, temp_filename)
        
        # Download the file
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(download_url, headers=headers, timeout=30, stream=True)
        
        # Check if response is HTML (authentication required)
        content_type = response.headers.get('content-type', '').lower()
        if 'text/html' in content_type:
            logger.warning("⚠️ Received HTML instead of file. Link might require authentication.")
            raise Exception("Cloud link requires authentication or is not publicly accessible")
        
        # Check if download was successful
        if response.status_code != 200:
            raise Exception(f"Failed to download: HTTP {response.status_code}")
        
        # Save file
        with open(temp_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        # Verify file was downloaded and has content
        if not os.path.exists(temp_path) or os.path.getsize(temp_path) == 0:
            raise Exception("Downloaded file is empty or doesn't exist")
        
        logger.info(f"✅ Successfully downloaded file to: {temp_path}")
        logger.info(f"📏 File size: {os.path.getsize(temp_path)} bytes")
        
        return temp_path
        
    except Exception as e:
        logger.error(f"❌ Error downloading from cloud link: {str(e)}")
        raise Exception(f"Could not download CV from the provided link. Please ensure the link allows public access. Error: {str(e)}")

def upload_cv_to_firebase(local_file_path, phone_number):
    """
    Upload CV file to Firebase Storage
    
    Args:
        local_file_path (str): Path to local CV file
        phone_number (str): User's phone number
        
    Returns:
        str: Storage path in Firebase
    """
    try:
        # Format phone number (remove whatsapp: prefix)
        formatted_phone = phone_number.replace('whatsapp:', '').replace('+', '')
        
        # Get file extension
        file_extension = os.path.splitext(local_file_path)[1]
        if not file_extension:
            file_extension = '.pdf'  # Default extension
        
        # Generate filename
        filename = f"cv_{int(time.time())}_{uuid.uuid4().hex[:8]}{file_extension}"
        
        # Define storage path
        storage_path = f"cv-uploads/{formatted_phone}/{filename}"
        
        logger.info(f"📤 Uploading to Firebase Storage: {storage_path}")
        
        # Upload file using existing service
        uploaded_path = upload_file_to_storage(local_file_path, storage_path)
        
        logger.info(f"✅ Successfully uploaded to: {uploaded_path}")
        return uploaded_path
        
    except Exception as e:
        logger.error(f"❌ Error uploading CV to Firebase: {str(e)}")
        raise Exception(f"Failed to upload CV to storage: {str(e)}")

def get_review_by_id(review_id):
    """
    Get a review by ID
    
    Args:
        review_id (str): Review ID
        
    Returns:
        dict: Review data
    """
    try:
        review = get_review(review_id)
        return review
    
    except Exception as e:
        logger.error(f"Error getting review {review_id}: {str(e)}")
        return None