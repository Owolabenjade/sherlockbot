# firebase_init.py
import os
import firebase_admin
from firebase_admin import credentials, firestore, storage
from utils.logger import get_logger

# Initialize logger
logger = get_logger()

def initialize_firebase():
    """
    Initialize Firebase Admin SDK for use across the application - FIXED VERSION
    
    Returns:
        bool: Whether initialization was successful
    """
    try:
        if firebase_admin._apps:
            # Already initialized
            logger.info("Firebase already initialized")
            return True
        
        # FIXED: Use correct storage bucket format
        storage_bucket = os.getenv('FIREBASE_STORAGE_BUCKET', 'cvreview-d1d4b.firebasestorage.app')
        
        # Check if we're in Cloud Functions/Cloud Run
        if os.getenv('K_SERVICE') or os.getenv('FUNCTION_TARGET') or os.getenv('GOOGLE_CLOUD_PROJECT'):
            # We're in Cloud Functions - use Application Default Credentials
            logger.info("Detected Cloud Functions environment")
            logger.info(f"Using storage bucket: {storage_bucket}")
            
            # Initialize without credentials (uses ADC automatically)
            firebase_admin.initialize_app(options={
                'storageBucket': storage_bucket
            })
            logger.info("Initialized Firebase with Application Default Credentials")
        else:
            # Local development - use service account
            cred_path = os.getenv('FIREBASE_SERVICE_ACCOUNT')
            if cred_path and os.path.exists(cred_path):
                logger.info(f"Initializing Firebase with service account: {cred_path}")
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred, {
                    'storageBucket': storage_bucket
                })
            else:
                # Try with default credentials anyway
                logger.warning("No service account found, attempting default credentials")
                try:
                    firebase_admin.initialize_app(options={
                        'storageBucket': storage_bucket
                    })
                    logger.info("Initialized with default credentials")
                except Exception as default_error:
                    logger.error(f"Failed to initialize with default credentials: {default_error}")
                    logger.error("FIREBASE_SERVICE_ACCOUNT not set and default credentials failed")
                    return False
        
        # Test the connection
        logger.info("Testing Firebase connection...")
        db = firestore.client()
        bucket = storage.bucket()
        logger.info(f"✅ Storage bucket name: {bucket.name}")
        logger.info(f"✅ Firestore connected successfully")
        
        logger.info("🎉 Firebase initialized successfully")
        return True
    
    except Exception as e:
        logger.error(f"❌ Error initializing Firebase: {str(e)}")
        logger.error(f"Environment: K_SERVICE={os.getenv('K_SERVICE')}, FUNCTION_TARGET={os.getenv('FUNCTION_TARGET')}")
        return False