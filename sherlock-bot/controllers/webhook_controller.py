# controllers/webhook_controller.py - Minimal version for testing
import os
import traceback
from flask import request
from twilio.twiml.messaging_response import MessagingResponse
from utils.logger import get_logger

# Initialize logger
logger = get_logger()

def handle_whatsapp_message(request):
    """
    Process incoming WhatsApp message - MINIMAL VERSION FOR TESTING
    
    Args:
        request: Flask request object
        
    Returns:
        Response: TwiML response
    """
    logger.info("🚀 MINIMAL: Starting handle_whatsapp_message function")
    
    try:
        # Extract basic message data
        logger.info("📝 MINIMAL: Extracting message data...")
        message_body = request.form.get('Body', '').strip()
        sender = request.form.get('From', '')
        to = request.form.get('To', '')
        
        logger.info(f"📨 MINIMAL: Message details:")
        logger.info(f"  - From: {sender}")
        logger.info(f"  - To: {to}")
        logger.info(f"  - Body: {message_body}")
        logger.info(f"  - All form keys: {list(request.form.keys())}")
        
        # Create TwiML response
        resp = MessagingResponse()
        
        # Simple responses based on message content
        if message_body.lower() == 'debug':
            debug_info = f"""🔍 DEBUG INFO:
From: {sender}
To: {to}
Body: {message_body}
Form data: {dict(request.form)}
Environment: {os.getenv('FLASK_ENV', 'production')}
Function region: africa-south1
"""
            resp.message(debug_info)
            logger.info("✅ MINIMAL: Sent debug response")
            
        elif message_body.lower() in ['hello', 'hi', 'test']:
            resp.message("👋 Hello! Sherlock Bot webhook is working! This is a minimal test response.")
            logger.info("✅ MINIMAL: Sent hello response")
            
        elif message_body.lower() == 'error':
            # Test error handling
            raise Exception("This is a test error")
            
        else:
            # Default response for any other message
            default_msg = f"""🤖 Sherlock Bot CV Review (Test Mode)

You sent: {message_body}

Available test commands:
• debug - Show debug info
• hello - Test greeting
• error - Test error handling

Full service coming soon!"""
            
            resp.message(default_msg)
            logger.info("✅ MINIMAL: Sent default response")
        
        return str(resp)
        
    except Exception as e:
        logger.error(f"❌ MINIMAL: Error in handle_whatsapp_message: {str(e)}")
        logger.error(f"MINIMAL: Full traceback: {traceback.format_exc()}")
        
        # Return basic error response
        resp = MessagingResponse()
        resp.message(f"⚠️ Error occurred: {str(e)[:100]}...")
        return str(resp)