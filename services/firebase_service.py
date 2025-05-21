# services/firebase_service.py - Firebase integration
import os
import json
import uuid
import time
import requests
from datetime import datetime, timedelta
from firebase_admin import firestore, storage
from utils.logger import get_logger

# Initialize logger
logger = get_logger()

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
        
        # Get bucket
        bucket = storage.bucket()
        
        # Upload file
        blob = bucket.blob(storage_path)
        blob.upload_from_filename(file_path)
        
        # Set content type
        if file_extension == '.pdf':
            blob.content_type = 'application/pdf'
        elif file_extension == '.docx':
            blob.content_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        
        logger.info(f"Uploaded CV to {storage_path}")
        
        return storage_path
    
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