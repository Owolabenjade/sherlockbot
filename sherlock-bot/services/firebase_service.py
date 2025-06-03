# services/firebase_service.py - Consolidated Firebase service
import os
import uuid
import time
import requests
from datetime import datetime, timedelta
from firebase_admin import firestore, storage
from utils.logger import get_logger

# Initialize logger
logger = get_logger()

# User session functions
def get_user_session(phone_number):
    """
    Get or create user session
    
    Args:
        phone_number (str): User's phone number
        
    Returns:
        dict: User session data
    """
    try:
        # Get Firestore client
        db = firestore.client()
        
        # Get user session
        session_ref = db.collection('sessions').document(phone_number)
        session = session_ref.get()
        
        if session.exists:
            # Return existing session
            session_data = session.to_dict()
            
            # Check if session is expired (24 hours)
            last_activity = session_data.get('last_activity')
            if last_activity:
                last_activity_time = datetime.fromisoformat(last_activity)
                if datetime.now() - last_activity_time > timedelta(hours=24):
                    # Session expired, create new session
                    session_data = {
                        'phone_number': phone_number,
                        'created_at': datetime.now().isoformat(),
                        'last_activity': datetime.now().isoformat(),
                        'state': 'welcome'
                    }
                    session_ref.set(session_data)
            
            # Update last activity
            session_ref.update({
                'last_activity': datetime.now().isoformat()
            })
            
            return session_data
        
        else:
            # Create new session
            session_data = {
                'phone_number': phone_number,
                'created_at': datetime.now().isoformat(),
                'last_activity': datetime.now().isoformat(),
                'state': 'welcome'
            }
            session_ref.set(session_data)
            
            return session_data
    
    except Exception as e:
        logger.error(f"Error getting user session: {str(e)}")
        
        # Return empty session
        return {
            'phone_number': phone_number,
            'created_at': datetime.now().isoformat(),
            'last_activity': datetime.now().isoformat(),
            'state': 'welcome'
        }

def update_user_session(phone_number, session_data):
    """
    Update user session
    
    Args:
        phone_number (str): User's phone number
        session_data (dict): Session data to update
        
    Returns:
        bool: Success status
    """
    try:
        # Get Firestore client
        db = firestore.client()
        
        # Update session with last activity timestamp
        session_data['last_activity'] = datetime.now().isoformat()
        
        # Update session
        db.collection('sessions').document(phone_number).set(session_data, merge=True)
        
        return True
    
    except Exception as e:
        logger.error(f"Error updating user session: {str(e)}")
        return False

# Storage functions
def upload_file_to_storage(file_path, destination_path):
    """
    Upload a file to Firebase Storage
    
    Args:
        file_path (str): Path to local file
        destination_path (str): Path in Firebase Storage
        
    Returns:
        str: Storage path
    """
    try:
        # Get bucket
        bucket = storage.bucket()
        
        # Upload file
        blob = bucket.blob(destination_path)
        blob.upload_from_filename(file_path)
        
        # Set content type based on file extension
        file_extension = os.path.splitext(file_path)[1].lower()
        if file_extension == '.pdf':
            blob.content_type = 'application/pdf'
        elif file_extension == '.docx':
            blob.content_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        elif file_extension == '.doc':
            blob.content_type = 'application/msword'
        
        logger.info(f"Uploaded file to {destination_path}")
        
        return destination_path
    
    except Exception as e:
        logger.error(f"Error uploading file to storage: {str(e)}")
        raise e

def upload_cv_to_storage(file_path, phone_number):
    """
    Upload CV file to Firebase Storage
    
    Args:
        file_path (str): Path to local CV file
        phone_number (str): User's phone number
        
    Returns:
        str: Storage path
    """
    try:
        # Format phone number (remove whatsapp: prefix)
        formatted_phone = phone_number.replace('whatsapp:', '')
        
        # Generate filename
        file_extension = os.path.splitext(file_path)[1]
        filename = f"cv_{int(time.time())}_{uuid.uuid4().hex[:8]}{file_extension}"
        
        # Define storage path
        storage_path = f"cv-uploads/{formatted_phone}/{filename}"
        
        # Upload file
        return upload_file_to_storage(file_path, storage_path)
    
    except Exception as e:
        logger.error(f"Error uploading CV to storage: {str(e)}")
        raise e

def download_file_from_storage(storage_path):
    """
    Download file from Firebase Storage
    
    Args:
        storage_path (str): Path in Firebase Storage
        
    Returns:
        str: Local file path
    """
    try:
        # Create a temporary file path
        local_file_dir = os.path.join(os.getcwd(), 'uploads')
        os.makedirs(local_file_dir, exist_ok=True)
        
        file_extension = os.path.splitext(storage_path)[1]
        if not file_extension:
            # If no extension in path, default to .pdf
            file_extension = '.pdf'
        
        local_file_path = os.path.join(
            local_file_dir,
            f"temp_{int(time.time())}_{uuid.uuid4().hex[:8]}{file_extension}"
        )
        
        # Get bucket
        bucket = storage.bucket()
        
        # Download file
        blob = bucket.blob(storage_path)
        blob.download_to_filename(local_file_path)
        
        logger.info(f"Downloaded {storage_path} to {local_file_path}")
        
        return local_file_path
    
    except Exception as e:
        logger.error(f"Error downloading file from storage: {str(e)}")
        raise e

def get_file_download_url(storage_path):
    """
    Get download URL for a file in Firebase Storage
    
    Args:
        storage_path (str): Path in Firebase Storage
        
    Returns:
        str: Download URL
    """
    try:
        # Get bucket
        bucket = storage.bucket()
        
        # Get blob
        blob = bucket.blob(storage_path)
        
        # Generate signed URL (valid for 1 day)
        url = blob.generate_signed_url(
            version='v4',
            expiration=timedelta(days=1),
            method='GET'
        )
        
        return url
    
    except Exception as e:
        logger.error(f"Error getting download URL: {str(e)}")
        return None

# Review and payment data functions
def save_review_result(phone_number, review_data):
    """
    Save review result to Firestore
    
    Args:
        phone_number (str): User's phone number
        review_data (dict): Review data
        
    Returns:
        str: Review ID
    """
    try:
        # Get Firestore client
        db = firestore.client()
        
        # Generate review ID
        review_id = str(uuid.uuid4())
        
        # Add metadata
        review_data['user_id'] = phone_number
        review_data['created_at'] = datetime.now().isoformat()
        
        # Save review
        db.collection('reviews').document(review_id).set(review_data)
        
        # Update user session with review reference
        user_ref = db.collection('sessions').document(phone_number)
        user_doc = user_ref.get()
        
        if user_doc.exists:
            user_data = user_doc.to_dict()
            
            # Create or update reviews array
            reviews = user_data.get('reviews', [])
            reviews.append(review_id)
            
            user_ref.update({
                'reviews': reviews,
                'last_review_id': review_id,
                'last_review_type': review_data.get('review_type', 'basic'),
                'last_review_date': datetime.now().isoformat()
            })
        
        return review_id
    
    except Exception as e:
        logger.error(f"Error saving review result: {str(e)}")
        return None

def get_review(review_id):
    """
    Get review by ID
    
    Args:
        review_id (str): Review ID
        
    Returns:
        dict: Review data
    """
    try:
        # Get Firestore client
        db = firestore.client()
        
        # Get review
        review_ref = db.collection('reviews').document(review_id)
        review_doc = review_ref.get()
        
        if review_doc.exists:
            review_data = review_doc.to_dict()
            review_data['id'] = review_id
            return review_data
        
        return None
    
    except Exception as e:
        logger.error(f"Error getting review {review_id}: {str(e)}")
        return None

def get_user_email(phone_number):
    """
    Get user's email address if available
    
    Args:
        phone_number (str): User's phone number
        
    Returns:
        str: Email address or None
    """
    try:
        # Get Firestore client
        db = firestore.client()
        
        # Get user document
        user_ref = db.collection('sessions').document(phone_number)
        user_doc = user_ref.get()
        
        if user_doc.exists:
            user_data = user_doc.to_dict()
            return user_data.get('email')
        
        return None
    
    except Exception as e:
        logger.error(f"Error getting user email: {str(e)}")
        return None