# controllers/webhook_controller.py - Debug version
import os
import traceback
from flask import request, jsonify
from twilio.twiml.messaging_response import MessagingResponse
from utils.logger import get_logger

# Initialize logger
logger = get_logger()

def handle_whatsapp_message(request):
    """
    Process incoming WhatsApp message with extensive debugging
    
    Args:
        request: Flask request object
        
    Returns:
        Response: TwiML response
    """
    logger.info("🚀 Starting handle_whatsapp_message function")
    
    try:
        # Extract message data with detailed logging
        logger.info("📝 Extracting message data...")
        message_body = request.form.get('Body', '').strip()
        media_count = int(request.form.get('NumMedia', 0))
        sender = request.form.get('From', '')
        
        logger.info(f"📨 Message details:")
        logger.info(f"  - From: {sender}")
        logger.info(f"  - Body: {message_body}")
        logger.info(f"  - Media count: {media_count}")
        logger.info(f"  - All form data: {dict(request.form)}")
        
        # Create response
        resp = MessagingResponse()
        
        # For now, let's just echo back with debugging info
        if message_body.lower() == 'debug':
            debug_message = f"""🔍 Debug Info:
From: {sender}
Body: {message_body}
Media: {media_count}
Form keys: {list(request.form.keys())}
Environment: {os.getenv('FLASK_ENV', 'production')}
"""
            resp.message(debug_message)
            logger.info("✅ Sent debug response")
            return str(resp)
        
        elif message_body.lower() in ['hello', 'hi', 'test']:
            # Simple test response
            test_message = "👋 Hello! I received your message. Sherlock Bot is working!"
            resp.message(test_message)
            logger.info("✅ Sent test response")
            return str(resp)
        
        else:
            # Try to import and use the actual service
            try:
                logger.info("🔄 Attempting to import services...")
                
                # Import services one by one with error handling
                try:
                    from services.firebase_service import get_user_session, update_user_session
                    logger.info("✅ Firebase service imported")
                except Exception as firebase_import_error:
                    logger.error(f"❌ Firebase service import failed: {str(firebase_import_error)}")
                    raise firebase_import_error
                
                try:
                    from services.twilio_service import send_whatsapp_message
                    logger.info("✅ Twilio service imported")
                except Exception as twilio_import_error:
                    logger.error(f"❌ Twilio service import failed: {str(twilio_import_error)}")
                    raise twilio_import_error
                
                # Test basic session handling
                logger.info("🔄 Testing session handling...")
                session = get_user_session(sender)
                logger.info(f"📊 Session retrieved: {session is not None}")
                
                # For now, just acknowledge the message
                welcome_message = """👋 Welcome to Sherlock Bot CV Review!
                
I'll help you improve your CV. Here's how it works:
1️⃣ Upload your CV (PDF or Word)
2️⃣ Choose basic (free) or advanced review
3️⃣ Get detailed feedback

Ready? Upload your CV now!"""
                
                resp.message(welcome_message)
                logger.info("✅ Sent welcome message")
                return str(resp)
                
            except Exception as service_error:
                logger.error(f"❌ Service error: {str(service_error)}")
                logger.error(f"Service traceback: {traceback.format_exc()}")
                
                # Fallback response
                error_message = f"⚠️ Service temporarily unavailable. Error: {str(service_error)[:100]}"
                resp.message(error_message)
                return str(resp)
    
    except Exception as e:
        logger.error(f"❌ Error in handle_whatsapp_message: {str(e)}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        
        # Return basic error response
        resp = MessagingResponse()
        resp.message("Sorry, something went wrong. Please try again later.")
        return str(resp)