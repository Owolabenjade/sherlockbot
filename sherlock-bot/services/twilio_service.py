# services/twilio_service.py - Twilio WhatsApp integration
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
    """
    Send a WhatsApp message via Twilio
    
    Args:
        to (str): Recipient's phone number
        body (str): Message body
        
    Returns:
        dict: Message SID and status
    """
    try:
        # Ensure phone number is in the right format
        recipient = to if to.startswith('whatsapp:') else f"whatsapp:{to}"
        sender = Config.TWILIO_PHONE_NUMBER
        
        # Ensure sender has whatsapp: prefix
        if not sender.startswith('whatsapp:'):
            sender = f"whatsapp:{sender}"
        
        # Send message
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
    
    except TwilioRestException as e:
        logger.error(f"Twilio error sending message to {to}: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }
    
    except Exception as e:
        logger.error(f"Error sending WhatsApp message to {to}: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

def send_whatsapp_message_with_media(to, body, media_url):
    """
    Send a WhatsApp message with media attachment
    
    Args:
        to (str): Recipient's phone number
        body (str): Message body
        media_url (str): URL to media file
        
    Returns:
        dict: Message SID and status
    """
    try:
        # Ensure phone number is in the right format
        recipient = to if to.startswith('whatsapp:') else f"whatsapp:{to}"
        sender = Config.TWILIO_PHONE_NUMBER
        
        # Ensure sender has whatsapp: prefix
        if not sender.startswith('whatsapp:'):
            sender = f"whatsapp:{sender}"
        
        # Send message with media
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
    
    except TwilioRestException as e:
        logger.error(f"Twilio error sending message with media to {to}: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }
    
    except Exception as e:
        logger.error(f"Error sending WhatsApp message with media to {to}: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

def validate_twilio_request(request):
    """
    Validate that a webhook request is from Twilio
    
    Args:
        request: Flask request object
        
    Returns:
        bool: Whether the request is valid
    """
    # Skip validation in development mode
    if os.getenv('FLASK_ENV') == 'development' and os.getenv('SKIP_TWILIO_VALIDATION'):
        return True
    
    try:
        # Get the signature from the request headers
        signature = request.headers.get('X-Twilio-Signature', '')
        
        # Get the full URL of the request
        url = request.url
        
        # Validate the request
        return twilio_validator.validate(url, request.form, signature)
    
    except Exception as e:
        logger.error(f"Error validating Twilio request: {str(e)}")
        return False