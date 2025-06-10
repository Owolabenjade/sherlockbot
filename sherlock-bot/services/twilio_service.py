# services/twilio_service.py
import os
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from twilio.request_validator import RequestValidator
from utils.logger import get_logger
from config import Config

# Initialize logger
logger = get_logger()

# Initialize Twilio client
twilio_client = Client(Config.TWILIO_ACCOUNT_SID, Config.TWILIO_AUTH_TOKEN)
twilio_validator = RequestValidator(Config.TWILIO_AUTH_TOKEN)

def send_whatsapp_message(to, body):
    """Send a WhatsApp message via Twilio"""
    try:
        recipient = to if to.startswith('whatsapp:') else f"whatsapp:{to}"
        sender = Config.TWILIO_PHONE_NUMBER
        if not sender.startswith('whatsapp:'):
            sender = f"whatsapp:{sender}"

        message = twilio_client.messages.create(
            from_=sender,
            body=body,
            to=recipient
        )

        logger.info(f"Sent WhatsApp message to {to} with SID: {message.sid}")
        return {
            'success': True,
            'sid': message.sid,
            'status': message.status
        }

    except Exception as e:
        logger.error(f"Error sending WhatsApp message to {to}: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

def send_whatsapp_message_with_media(to, body, media_url):
    """Send a WhatsApp message with media attachment"""
    try:
        recipient = to if to.startswith('whatsapp:') else f"whatsapp:{to}"
        sender = Config.TWILIO_PHONE_NUMBER
        if not sender.startswith('whatsapp:'):
            sender = f"whatsapp:{sender}"

        message = twilio_client.messages.create(
            from_=sender,
            body=body,
            media_url=[media_url],
            to=recipient
        )

        logger.info(f"Sent WhatsApp message with media to {to} with SID: {message.sid}")
        return {
            'success': True,
            'sid': message.sid,
            'status': message.status
        }

    except Exception as e:
        logger.error(f"Error sending WhatsApp message with media to {to}: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

def get_firebase_webhook_url():
    """
    Get the correct webhook URL for Firebase Functions
    Option A: africa-south1 region with Gen 2 Functions
    """
    # Hardcoded URL for africa-south1 - this is the most reliable approach
    webhook_url = 'https://africa-south1-cvreview-d1d4b.cloudfunctions.net/app_function/webhook/twilio'
    
    logger.info(f"Using africa-south1 webhook URL: {webhook_url}")
    return webhook_url

def validate_twilio_request(request):
    """Validate that a webhook request is from Twilio - Option A"""
    if os.getenv('FLASK_ENV') == 'development' and os.getenv('SKIP_TWILIO_VALIDATION'):
        logger.warning("TWILIO VALIDATION SKIPPED - DEVELOPMENT MODE")
        return True

    try:
        signature = request.headers.get('X-Twilio-Signature', '')
        if not signature:
            logger.warning("No X-Twilio-Signature header found")
            return False

        webhook_url = get_firebase_webhook_url()
        
        logger.info(f"Validating Twilio request for africa-south1:")
        logger.info(f"Configured webhook URL: {webhook_url}")
        logger.info(f"Actual request URL: {request.url}")
        
        # Try multiple URL variations for africa-south1
        urls_to_try = [
            webhook_url,  # The configured URL
            request.url,  # The actual request URL
            request.url.replace('http://', 'https://'),  # Force HTTPS
            'https://africa-south1-cvreview-d1d4b.cloudfunctions.net/app_function/webhook/twilio',  # Backup
        ]
        
        for i, url in enumerate(urls_to_try, 1):
            try:
                is_valid = twilio_validator.validate(url, request.form, signature)
                if is_valid:
                    logger.info(f"✅ Validation succeeded with URL {i}: {url}")
                    return True
                else:
                    logger.info(f"❌ Validation failed with URL {i}: {url}")
            except Exception as e:
                logger.error(f"URL {i} validation error: {str(e)}")
        
        logger.error("❌ All validation attempts failed for africa-south1")
        return False

    except Exception as e:
        logger.error(f"Error validating Twilio request: {str(e)}")
        return False

def validate_twilio_request_debug(request):
    """Debug version with detailed logging for africa-south1"""
    try:
        signature = request.headers.get('X-Twilio-Signature', '')
        
        logger.info("=== TWILIO VALIDATION DEBUG (africa-south1) ===")
        logger.info(f"Request URL: {request.url}")
        logger.info(f"Request method: {request.method}")
        logger.info(f"Request headers: {dict(request.headers)}")
        logger.info(f"Request form data: {dict(request.form)}")
        logger.info(f"X-Twilio-Signature: {signature}")
        logger.info(f"Target region: africa-south1")
        
        # URLs specific to africa-south1
        urls_to_try = [
            'https://africa-south1-cvreview-d1d4b.cloudfunctions.net/app_function/webhook/twilio',
            request.url,
            request.url.replace('http://', 'https://'),
        ]
        
        for i, url in enumerate(urls_to_try, 1):
            logger.info(f"Trying africa-south1 URL {i}: {url}")
            try:
                is_valid = twilio_validator.validate(url, request.form, signature)
                logger.info(f"URL {i} validation result: {is_valid}")
                if is_valid:
                    logger.info(f"🎉 SUCCESS: Validation passed with africa-south1 URL: {url}")
                    return True
            except Exception as e:
                logger.error(f"URL {i} validation error: {str(e)}")
        
        logger.error("❌ All africa-south1 URL validation attempts failed")
        return False
        
    except Exception as e:
        logger.error(f"Debug validation error: {str(e)}")
        return False