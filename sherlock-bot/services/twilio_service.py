# services/twilio_service.py - Production WhatsApp Business
import os
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from twilio.request_validator import RequestValidator
from utils.logger import get_logger
from config import Config

# Initialize logger
logger = get_logger()

# Initialize Twilio client as None first (will be initialized when needed)
twilio_client = None
twilio_validator = None

def get_twilio_client():
    """Get or initialize Twilio client"""
    global twilio_client, twilio_validator
    
    if twilio_client is None:
        twilio_client = Client(Config.TWILIO_ACCOUNT_SID, Config.TWILIO_AUTH_TOKEN)
        twilio_validator = RequestValidator(Config.TWILIO_AUTH_TOKEN)
        logger.info(f"Initialized Twilio client with WhatsApp Business: {Config.TWILIO_PHONE_NUMBER}")
    
    return twilio_client

def send_whatsapp_message(to, body):
    """Send a WhatsApp message via Twilio"""
    try:
        # Get Twilio client
        client = get_twilio_client()
        
        recipient = to if to.startswith('whatsapp:') else f"whatsapp:{to}"
        sender = Config.TWILIO_PHONE_NUMBER
        if not sender.startswith('whatsapp:'):
            sender = f"whatsapp:{sender}"

        # Split long messages if needed (WhatsApp has a 1600 char limit)
        if len(body) > 1500:
            logger.warning(f"Message length ({len(body)}) exceeds recommended limit, sending anyway")

        message = client.messages.create(
            from_=sender,
            body=body,
            to=recipient
        )

        logger.info(f"✅ Sent WhatsApp message to {to} with SID: {message.sid}")
        return {
            'success': True,
            'sid': message.sid,
            'status': message.status
        }

    except TwilioRestException as e:
        logger.error(f"Twilio error sending WhatsApp message to {to}: {e.msg}")
        return {
            'success': False,
            'error': e.msg,
            'code': e.code
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
        # Get Twilio client
        client = get_twilio_client()
        
        recipient = to if to.startswith('whatsapp:') else f"whatsapp:{to}"
        sender = Config.TWILIO_PHONE_NUMBER
        if not sender.startswith('whatsapp:'):
            sender = f"whatsapp:{sender}"

        message = client.messages.create(
            from_=sender,
            body=body,
            media_url=[media_url],
            to=recipient
        )

        logger.info(f"✅ Sent WhatsApp message with media to {to} with SID: {message.sid}")
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
    """Get the correct webhook URL for Firebase Functions"""
    # Production webhook URL for africa-south1
    webhook_url = 'https://africa-south1-cvreview-d1d4b.cloudfunctions.net/app_function/webhook/twilio'
    
    logger.info(f"Using production webhook URL: {webhook_url}")
    return webhook_url

def validate_twilio_request(request):
    """Validate that a webhook request is from Twilio - Production"""
    # Skip validation in development if explicitly set
    if Config.SKIP_TWILIO_VALIDATION and not Config.IS_PRODUCTION:
        logger.warning("⚠️ TWILIO VALIDATION SKIPPED - DEVELOPMENT MODE")
        return True

    try:
        # Get validator
        if twilio_validator is None:
            get_twilio_client()  # This will initialize the validator
            
        signature = request.headers.get('X-Twilio-Signature', '')
        if not signature:
            logger.warning("No X-Twilio-Signature header found")
            return False

        webhook_url = get_firebase_webhook_url()
        
        # In production, validate with the exact webhook URL
        is_valid = twilio_validator.validate(webhook_url, request.form, signature)
        
        if is_valid:
            logger.info(f"✅ Valid Twilio request signature")
        else:
            logger.warning(f"❌ Invalid Twilio request signature")
            
            # Log additional debug info in non-production
            if not Config.IS_PRODUCTION:
                logger.info(f"Expected URL: {webhook_url}")
                logger.info(f"Request URL: {request.url}")
                logger.info(f"Signature: {signature[:20]}...")
        
        return is_valid

    except Exception as e:
        logger.error(f"Error validating Twilio request: {str(e)}")
        # In production, fail closed (reject if validation fails)
        return not Config.IS_PRODUCTION