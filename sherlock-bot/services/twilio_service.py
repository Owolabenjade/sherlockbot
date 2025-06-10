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

def get_firebase_webhook_url():
    """
    Get the correct webhook URL for Firebase Functions
    FIXED: Proper URL construction for Cloud Functions
    
    Returns:
        str: The webhook URL that Twilio should use
    """
    # Check if we're running in Firebase Functions/Cloud Run
    if os.getenv('K_SERVICE') or os.getenv('FUNCTION_TARGET'):
        # In Firebase Functions, GOOGLE_CLOUD_PROJECT is automatically set by the runtime
        # We don't need to set it in .env as it's reserved
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT') or os.getenv('GCP_PROJECT') or 'cvreview-d1d4b'
        
        # Your function is deployed in africa-south1
        region = 'africa-south1'
        function_name = 'app-function'  # This matches your main.py function name
        
        # Construct the proper Cloud Functions URL
        webhook_url = f"https://{region}-{project_id}.cloudfunctions.net/{function_name}/webhook/twilio"
        
        logger.info(f"Constructed Firebase webhook URL: {webhook_url}")
        return webhook_url
    
    # Fallback to environment variable or hardcoded URL for your project
    fallback_url = os.getenv('TWILIO_WEBHOOK_URL', 'https://africa-south1-cvreview-d1d4b.cloudfunctions.net/app-function/webhook/twilio')
    logger.info(f"Using fallback webhook URL: {fallback_url}")
    return fallback_url

def validate_twilio_request(request):
    """
    Validate that a webhook request is from Twilio
    FIXED: Proper URL handling for Firebase Functions

    Args:
        request: Flask request object

    Returns:
        bool: Whether the request is valid
    """
    # Skip validation in development mode
    if os.getenv('FLASK_ENV') == 'development' and os.getenv('SKIP_TWILIO_VALIDATION'):
        logger.warning("TWILIO VALIDATION SKIPPED - DEVELOPMENT MODE")
        return True

    try:
        # Get the signature from the request headers
        signature = request.headers.get('X-Twilio-Signature', '')
        
        if not signature:
            logger.warning("No X-Twilio-Signature header found")
            return False

        # Get the correct webhook URL that Twilio was configured to call
        webhook_url = get_firebase_webhook_url()
        
        # Log for debugging
        logger.info(f"Validating Twilio request:")
        logger.info(f"Configured webhook URL: {webhook_url}")
        logger.info(f"Actual request URL: {request.url}")
        logger.info(f"Signature: {signature[:20]}...")
        logger.info(f"Form data keys: {list(request.form.keys())}")
        
        # Validate the request using the configured webhook URL
        is_valid = twilio_validator.validate(webhook_url, request.form, signature)
        
        if is_valid:
            logger.info("✅ Twilio signature validation successful")
            return True
        else:
            logger.error("❌ Twilio signature validation failed with configured URL")
            
            # Try with the actual request URL as fallback
            logger.info("Trying validation with actual request URL as fallback...")
            is_valid_fallback = twilio_validator.validate(request.url, request.form, signature)
            
            if is_valid_fallback:
                logger.info("✅ Validation succeeded with actual request URL")
                return True
            else:
                logger.error("❌ Validation failed with both URLs")
                
                # Try with HTTPS version of request URL
                https_url = request.url.replace('http://', 'https://')
                if https_url != request.url:
                    logger.info("Trying with HTTPS version of request URL...")
                    is_valid_https = twilio_validator.validate(https_url, request.form, signature)
                    if is_valid_https:
                        logger.info("✅ Validation succeeded with HTTPS URL")
                        return True
                
                return False

    except Exception as e:
        logger.error(f"Error validating Twilio request: {str(e)}")
        return False

def validate_twilio_request_debug(request):
    """
    Debug version with detailed logging - use temporarily for troubleshooting
    
    Args:
        request: Flask request object
        
    Returns:
        bool: Whether the request is valid
    """
    try:
        # Get the signature from the request headers
        signature = request.headers.get('X-Twilio-Signature', '')
        
        # Log all the details
        logger.info("=== TWILIO VALIDATION DEBUG ===")
        logger.info(f"Request URL: {request.url}")
        logger.info(f"Request method: {request.method}")
        logger.info(f"Content-Type: {request.content_type}")
        logger.info(f"Request headers: {dict(request.headers)}")
        logger.info(f"Request form data: {dict(request.form)}")
        logger.info(f"X-Twilio-Signature: {signature}")
        logger.info(f"Environment - K_SERVICE: {os.getenv('K_SERVICE')}")
        logger.info(f"Environment - FUNCTION_TARGET: {os.getenv('FUNCTION_TARGET')}")
        logger.info(f"Environment - GOOGLE_CLOUD_PROJECT: {os.getenv('GOOGLE_CLOUD_PROJECT')}")
        
        # Try different URL variations
        urls_to_try = [
            get_firebase_webhook_url(),  # The configured URL
            request.url,  # The actual request URL
            request.url.replace('http://', 'https://'),  # Force HTTPS
            'https://africa-south1-cvreview-d1d4b.cloudfunctions.net/app-function/webhook/twilio',  # Hardcoded correct URL
        ]
        
        for i, url in enumerate(urls_to_try, 1):
            logger.info(f"Trying URL {i}: {url}")
            try:
                is_valid = twilio_validator.validate(url, request.form, signature)
                logger.info(f"URL {i} validation result: {is_valid}")
                if is_valid:
                    logger.info(f"🎉 SUCCESS: Validation passed with URL: {url}")
                    return True
            except Exception as e:
                logger.error(f"URL {i} validation error: {str(e)}")
        
        logger.error("❌ All URL validation attempts failed")
        return False
        
    except Exception as e:
        logger.error(f"Debug validation error: {str(e)}")
        return False