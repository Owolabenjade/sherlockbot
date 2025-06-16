# config.py - Updated to work with Firebase Functions environment variables
import os
from dotenv import load_dotenv

# Only load .env in local development
if not os.getenv('K_SERVICE') and not os.getenv('FUNCTION_TARGET'):
    load_dotenv()

def get_firebase_config(key, default=None):
    """Get config from Firebase Functions config or environment"""
    # In Cloud Functions, Firebase config is available as environment variables
    # Format: firebase.functions.config().section.key becomes SECTION_KEY
    
    # Try direct environment variable first
    value = os.getenv(key, None)
    if value:
        return value
    
    # Try Firebase Functions config format (uppercase with underscores)
    firebase_key = key.upper().replace('.', '_')
    value = os.getenv(firebase_key, None)
    if value:
        return value
    
    # Try with common prefixes
    for prefix in ['TWILIO_', 'PAYSTACK_', 'SENDGRID_', 'APP_', 'EMAIL_']:
        if key.upper().startswith(prefix):
            simple_key = key.upper().replace(prefix, '')
            value = os.getenv(f"{prefix}{simple_key}", None)
            if value:
                return value
    
    return default

class Config:
    # Flask configuration
    SECRET_KEY = get_firebase_config('SECRET_KEY', 'dev-secret-key')
    DEBUG = get_firebase_config('FLASK_ENV') != 'production'
    
    # Twilio configuration - CRITICAL FOR YOUR ISSUE
    TWILIO_ACCOUNT_SID = get_firebase_config('TWILIO_ACCOUNT_SID') or get_firebase_config('twilio_account_sid')
    TWILIO_AUTH_TOKEN = get_firebase_config('TWILIO_AUTH_TOKEN') or get_firebase_config('twilio_auth_token')
    TWILIO_PHONE_NUMBER = get_firebase_config('TWILIO_PHONE_NUMBER') or get_firebase_config('twilio_phone_number')
    
    # Firebase configuration
    STORAGE_BUCKET = get_firebase_config('STORAGE_BUCKET', 'cvreview-d1d4b.firebasestorage.app')
    
    # Paystack configuration
    PAYSTACK_SECRET_KEY = get_firebase_config('PAYSTACK_SECRET_KEY') or get_firebase_config('paystack_secret_key')
    PAYSTACK_PUBLIC_KEY = get_firebase_config('PAYSTACK_PUBLIC_KEY') or get_firebase_config('paystack_public_key')
    
    # SendGrid configuration
    SENDGRID_API_KEY = get_firebase_config('SENDGRID_API_KEY') or get_firebase_config('sendgrid_api_key')
    EMAIL_FROM = get_firebase_config('EMAIL_FROM', 'reviews@sherlockbot.com')
    EMAIL_FROM_NAME = get_firebase_config('EMAIL_FROM_NAME', 'Sherlock Bot CV Review')
    
    # CV Analysis API
    CV_ANALYSIS_API_URL = get_firebase_config('CV_ANALYSIS_API_URL', 'https://cv-review-1.onrender.com/api/upload-and-analyze')
    
    # Payment configuration
    ADVANCED_REVIEW_PRICE = int(get_firebase_config('ADVANCED_REVIEW_PRICE', '5000'))
    PAYMENT_CURRENCY = get_firebase_config('PAYMENT_CURRENCY', 'NGN')
    PAYMENT_SUCCESS_URL = get_firebase_config('PAYMENT_SUCCESS_URL', '/payment/success')
    PAYMENT_CANCEL_URL = get_firebase_config('PAYMENT_CANCEL_URL', '/payment/cancel')
    
    # File handling
    UPLOAD_FOLDER = get_firebase_config('UPLOAD_FOLDER', '/tmp/uploads')  # Cloud Functions use /tmp
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload size
    ALLOWED_EXTENSIONS = {'pdf', 'docx', 'doc'}
    
    # Admin configuration
    ADMIN_USERNAME = get_firebase_config('ADMIN_USERNAME', 'admin')
    ADMIN_PASSWORD = get_firebase_config('ADMIN_PASSWORD')
    
    # Session configuration
    SESSION_LIFETIME = int(get_firebase_config('SESSION_LIFETIME', '3600'))  # 1 hour
    
    # Logger configuration
    LOG_LEVEL = get_firebase_config('LOG_LEVEL', 'INFO')

# Debug: Log loaded configuration (without sensitive values)
if os.getenv('K_SERVICE') or os.getenv('FUNCTION_TARGET'):
    import logging
    logger = logging.getLogger('sherlock_bot')
    logger.info("Configuration loaded in Cloud Functions:")
    logger.info(f"TWILIO_ACCOUNT_SID: {'Set' if Config.TWILIO_ACCOUNT_SID else 'Not set'}")
    logger.info(f"TWILIO_AUTH_TOKEN: {'Set' if Config.TWILIO_AUTH_TOKEN else 'Not set'}")
    logger.info(f"TWILIO_PHONE_NUMBER: {Config.TWILIO_PHONE_NUMBER if Config.TWILIO_PHONE_NUMBER else 'Not set'}")