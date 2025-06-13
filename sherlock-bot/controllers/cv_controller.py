# controllers/cv_controller.py - CV processing logic with cloud link support
import os
import uuid
import time
from datetime import datetime
from services.firebase_service import upload_file_to_storage, get_file_download_url
from services.cv_service import process_basic_review, process_advanced_review
from services.firestore_service import save_review_result, get_review
from services.sendgrid_service import send_review_email
from utils.cloud_utils import download_from_cloud_link, is_valid_cloud_link
from utils.logger import get_logger

# Initialize logger
logger = get_logger()

def process_cv_upload(cloud_link_or_storage_path, review_type, phone_number, email=None):
    """
    Process CV file from cloud link or storage path
    
    Args:
        cloud_link_or_storage_path (str): Cloud link URL or Firebase Storage path
        review_type (str): Type of review (basic or advanced)
        phone_number (str): User's phone number
        email (str, optional): User's email address
        
    Returns:
        dict: Review results
    """
    try:
        storage_path = None
        local_file_path = None
        
        # Check if input is a cloud link or storage path
        if cloud_link_or_storage_path.startswith('http') and is_valid_cloud_link(cloud_link_or_storage_path):
            # It's a cloud link - download and upload to Firebase Storage
            logger.info(f"Processing CV from cloud link: {cloud_link_or_storage_path[:50]}...")
            
            try:
                # Download from cloud link
                local_file_path = download_from_cloud_link(cloud_link_or_storage_path)
                logger.info(f"Downloaded CV from cloud link to: {local_file_path}")
                
                # Upload to Firebase Storage
                storage_path = upload_cv_to_firebase(local_file_path, phone_number)
                logger.info(f"Uploaded CV to Firebase Storage: {storage_path}")
                
            except Exception as download_error:
                logger.error(f"Error downloading from cloud link: {str(download_error)}")
                
                # Try alternative approach - process directly from cloud link
                # This is a fallback for when direct download fails
                storage_path = cloud_link_or_storage_path
                logger.warning("Using cloud link directly as storage path (fallback mode)")
        else:
            # It's already a storage path
            storage_path = cloud_link_or_storage_path
            logger.info(f"Using existing storage path: {storage_path}")
        
        # Process the review
        if review_type == 'basic':
            # Process basic review
            review_result = process_basic_review(storage_path)
        else:
            # Process advanced review
            review_result = process_advanced_review(storage_path)
        
        # Check if review was successful
        if not review_result.get('success'):
            logger.error(f"Error processing {review_type} review: {review_result.get('error')}")
            return {
                'success': False,
                'error': review_result.get('error', 'Failed to process review')
            }
        
        # Add metadata
        review_result['timestamp'] = datetime.now().isoformat()
        review_result['review_type'] = review_type
        review_result['cv_storage_path'] = storage_path
        
        # Store original cloud link if provided
        if cloud_link_or_storage_path.startswith('http'):
            review_result['cv_cloud_link'] = cloud_link_or_storage_path
        
        # If there's an email and it's an advanced review, send the email
        if email and review_type == 'advanced':
            download_link = review_result.get('download_link', '')
            
            if download_link:
                email_result = send_review_email(
                    email,
                    phone_number,
                    review_result,
                    download_link
                )
                
                review_result['email_sent'] = email_result.get('success', False)
                review_result['email'] = email
        
        # Save review to Firestore
        review_id = save_review_result(phone_number, review_result)
        review_result['id'] = review_id
        
        logger.info(f"Completed {review_type} review for {phone_number}")
        
        # Clean up local file if it was downloaded
        if local_file_path and os.path.exists(local_file_path):
            try:
                os.remove(local_file_path)
                logger.info(f"Cleaned up temporary file: {local_file_path}")
            except Exception as cleanup_error:
                logger.warning(f"Could not clean up temporary file: {cleanup_error}")
        
        return review_result
    
    except Exception as e:
        logger.error(f"Error in process_cv_upload: {str(e)}")
        
        # Clean up local file on error
        if local_file_path and os.path.exists(local_file_path):
            try:
                os.remove(local_file_path)
            except:
                pass
        
        return {
            'success': False,
            'error': str(e)
        }

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
        formatted_phone = phone_number.replace('whatsapp:', '')
        
        # Get file extension
        file_extension = os.path.splitext(local_file_path)[1]
        
        # Generate filename
        filename = f"cv_{int(time.time())}_{uuid.uuid4().hex[:8]}{file_extension}"
        
        # Define storage path
        storage_path = f"cv-uploads/{formatted_phone}/{filename}"
        
        # Upload file using existing service
        from services.firebase_service import upload_file_to_storage
        uploaded_path = upload_file_to_storage(local_file_path, storage_path)
        
        return uploaded_path
        
    except Exception as e:
        logger.error(f"Error uploading CV to Firebase: {str(e)}")
        raise e

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

def process_cv_from_cloud_link(cloud_link, review_type, phone_number, email=None):
    """
    Convenience function specifically for processing CVs from cloud links
    
    Args:
        cloud_link (str): Cloud storage URL
        review_type (str): Type of review (basic or advanced)
        phone_number (str): User's phone number
        email (str, optional): User's email address
        
    Returns:
        dict: Review results
    """
    return process_cv_upload(cloud_link, review_type, phone_number, email)