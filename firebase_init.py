# firebase_init.py - Firebase initialization
import os
import firebase_admin
from firebase_admin import credentials, firestore, storage
from utils.logger import get_logger

# Initialize logger
logger = get_logger()

def initialize_firebase():
    """
    Initialize Firebase Admin SDK for use across the application
    
    Returns:
        bool: Whether initialization was successful
    """
    try:
        if firebase_admin._apps:
            # Already initialized
            logger.info("Firebase already initialized")
            return True
        
        # Check environment
        if os.getenv('FLASK_ENV') == 'production':
            logger.info("Initializing Firebase with application default credentials")
            firebase_admin.initialize_app(options={
                'storageBucket': os.getenv('FIREBASE_STORAGE_BUCKET')
            })
        else:
            # Use service account in development
            cred_path = os.getenv('FIREBASE_SERVICE_ACCOUNT')
            if cred_path:
                logger.info(f"Initializing Firebase with service account: {cred_path}")
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred, {
                    'storageBucket': os.getenv('FIREBASE_STORAGE_BUCKET')
                })
            else:
                logger.error("FIREBASE_SERVICE_ACCOUNT not set, Firebase initialization failed")
                return False
        
        # Test the connection
        db = firestore.client()
        bucket = storage.bucket()
        
        logger.info("Firebase initialized successfully")
        return True
    
    except Exception as e:
        logger.error(f"Error initializing Firebase: {str(e)}")
        return False