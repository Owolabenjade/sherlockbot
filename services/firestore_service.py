# services/firestore_service.py - Firestore database service
import uuid
from datetime import datetime
from firebase_admin import firestore
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
            return session.to_dict()
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
        
        # Return empty session as fallback
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