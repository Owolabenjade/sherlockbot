# controllers/cv_controller.py - CV processing logic
import os
import uuid
import time
from datetime import datetime
from services.firebase_service import download_file_from_storage, get_file_download_url
from services.cv_service import process_basic_review, process_advanced_review
from services.firestore_service import save_review_result, get_review
from services.sendgrid_service import send_review_email
from utils.logger import get_logger

# Initialize logger
logger = get_logger()

def process_cv_upload(storage_path, review_type, phone_number, email=None):
    """
    Process uploaded CV file
    
    Args:
        storage_path (str): Path to CV in Firebase Storage
        review_type (str): Type of review (basic or advanced)
        phone_number (str): User's phone number
        email (str, optional): User's email address
        
    Returns:
        dict: Review results
    """
    try:
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
        return review_result
    
    except Exception as e:
        logger.error(f"Error in process_cv_upload: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

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