# config.py - Production WhatsApp Business Configuration
import os
from dotenv import load_dotenv

# Only load .env in local development
if not os.getenv('K_SERVICE') and not os.getenv('FUNCTION_TARGET'):
    load_dotenv()

class Config:
    # Flask configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    DEBUG = os.getenv('FLASK_ENV') != 'production'
    
    # Twilio Production Configuration
    TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
    TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
    TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER', 'whatsapp:+18383682677')  # Your production WhatsApp number
    
    # WhatsApp Business Profile
    BUSINESS_NAME = "Sherlock CV Review"
    BUSINESS_DESCRIPTION = "AI-powered CV review and optimization service"
    BUSINESS_CATEGORY = "Professional Services"
    BUSINESS_WEBSITE = "https://cvreview-d1d4b.web.app"  # Your Firebase hosting URL
    
    # Firebase configuration
    STORAGE_BUCKET = os.getenv('STORAGE_BUCKET', 'cvreview-d1d4b.firebasestorage.app')
    
    # Paystack configuration
    PAYSTACK_SECRET_KEY = os.getenv('PAYSTACK_SECRET_KEY')
    PAYSTACK_PUBLIC_KEY = os.getenv('PAYSTACK_PUBLIC_KEY')
    
    # SendGrid configuration
    SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY')
    EMAIL_FROM = os.getenv('EMAIL_FROM', 'reviews@sherlockbot.com')
    EMAIL_FROM_NAME = os.getenv('EMAIL_FROM_NAME', 'Sherlock CV Review')
    
    # CV Analysis API
    CV_ANALYSIS_API_URL = os.getenv('CV_ANALYSIS_API_URL', 'https://cv-review-1.onrender.com/api/upload-and-analyze')
    
    # Payment configuration
    ADVANCED_REVIEW_PRICE = int(os.getenv('ADVANCED_REVIEW_PRICE', 5000))
    PAYMENT_CURRENCY = os.getenv('PAYMENT_CURRENCY', 'NGN')
    PAYMENT_SUCCESS_URL = os.getenv('PAYMENT_SUCCESS_URL', '/payment/success')
    PAYMENT_CANCEL_URL = os.getenv('PAYMENT_CANCEL_URL', '/payment/cancel')
    
    # File handling - Enhanced for Production WhatsApp
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', '/tmp/uploads' if os.path.exists('/tmp') else 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max for WhatsApp Business
    ALLOWED_EXTENSIONS = {'pdf', 'docx', 'doc'}
    
    # WhatsApp Media limits
    WHATSAPP_MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB for documents
    WHATSAPP_SUPPORTED_FORMATS = {
        'application/pdf': 'pdf',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx',
        'application/msword': 'doc'
    }
    
    # Admin configuration
    ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
    ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD')
    
    # Session configuration
    SESSION_LIFETIME = int(os.getenv('SESSION_LIFETIME', 3600))  # 1 hour
    
    # Logger configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    # Production flags
    IS_PRODUCTION = os.getenv('FLASK_ENV') == 'production'
    SKIP_TWILIO_VALIDATION = os.getenv('SKIP_TWILIO_VALIDATION', 'false').lower() == 'true'