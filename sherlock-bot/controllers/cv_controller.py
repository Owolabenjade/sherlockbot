# controllers/cv_controller.py - Production Direct File Upload Only
import os
from datetime import datetime
from services.firebase_service import get_file_download_url
from services.cv_service import process_basic_review, process_advanced_review
from services.firestore_service import save_review_result, get_review
from services.sendgrid_service import send_review_email
from utils.logger import get_logger

# Initialize logger
logger = get_logger()

def process_cv_upload(storage_path, review_type, phone_number, email=None):
    """
    Process CV file from Firebase Storage
    
    Args:
        storage_path (str): Firebase Storage path
        review_type (str): Type of review (basic or advanced)
        phone_number (str): User's phone number
        email (str, optional): User's email address
        
    Returns:
        dict: Review results
    """
    logger.info(f"🚀 Starting CV processing for {review_type} review")
    logger.info(f"📁 Storage path: {storage_path}")
    
    try:
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