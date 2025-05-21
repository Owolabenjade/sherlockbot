# config.py - Configuration settings
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    # Flask configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    DEBUG = os.getenv('FLASK_ENV') != 'production'
    
    # Twilio configuration
    TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
    TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
    TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')
    
    # Firebase configuration
    FIREBASE_STORAGE_BUCKET = os.getenv('FIREBASE_STORAGE_BUCKET')
    
    # Paystack configuration
    PAYSTACK_SECRET_KEY = os.getenv('PAYSTACK_SECRET_KEY')
    PAYSTACK_PUBLIC_KEY = os.getenv('PAYSTACK_PUBLIC_KEY')
    
    # SendGrid configuration
    SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY')
    EMAIL_FROM = os.getenv('EMAIL_FROM', 'reviews@sherlockbot.com')
    EMAIL_FROM_NAME = os.getenv('EMAIL_FROM_NAME', 'Sherlock Bot CV Review')
    
    # CV Analysis API
    CV_ANALYSIS_API_URL = os.getenv('CV_ANALYSIS_API_URL')
    CV_ANALYSIS_API_KEY = os.getenv('CV_ANALYSIS_API_KEY')
    
    # Payment configuration
    ADVANCED_REVIEW_PRICE = int(os.getenv('ADVANCED_REVIEW_PRICE', 5000))
    PAYMENT_CURRENCY = os.getenv('PAYMENT_CURRENCY', 'NGN')
    PAYMENT_SUCCESS_URL = os.getenv('PAYMENT_SUCCESS_URL', '/payment/success')
    PAYMENT_CANCEL_URL = os.getenv('PAYMENT_CANCEL_URL', '/payment/cancel')
    
    # File handling
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload size
    ALLOWED_EXTENSIONS = {'pdf', 'docx', 'doc'}
    
    # Admin configuration
    ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
    ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD')
    
    # Session configuration
    SESSION_LIFETIME = int(os.getenv('SESSION_LIFETIME', 3600))  # 1 hour
    
    # Logger configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')