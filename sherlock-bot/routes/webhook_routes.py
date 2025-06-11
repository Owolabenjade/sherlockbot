# routes/webhook_routes.py - Minimal version for testing
from flask import Blueprint, request, jsonify
import os
import traceback
from datetime import datetime
from utils.logger import get_logger

# Initialize logger
logger = get_logger()

# Create blueprint
webhook_bp = Blueprint('webhook', __name__)

@webhook_bp.route('/twilio', methods=['POST', 'GET'])
def twilio_webhook():
    """Handle incoming WhatsApp messages via Twilio - MINIMAL VERSION"""
    
    try:
        logger.info(f"🔄 MINIMAL: Received {request.method} request to /webhook/twilio")
        logger.info(f"MINIMAL: Request URL: {request.url}")
        logger.info(f"MINIMAL: Content-Type: {request.content_type}")
        logger.info(f"MINIMAL: Headers: {dict(request.headers)}")
        
        # Handle GET requests
        if request.method == 'GET':
            return jsonify({
                'status': 'MINIMAL: Webhook endpoint is active',
                'method': 'GET',
                'url': request.url,
                'timestamp': datetime.now().isoformat(),
                'function_region': 'africa-south1'
            })
        
        # Handle POST requests
        if request.method == 'POST':
            logger.info(f"MINIMAL: Form data: {dict(request.form)}")
            
            # Skip validation for testing
            logger.info("⚠️ MINIMAL: Skipping all validation for testing")
            
            # Import the controller function here to avoid import issues
            try:
                from controllers.webhook_controller import handle_whatsapp_message
                logger.info("✅ MINIMAL: Successfully imported webhook controller")
                
                # Process the message
                result = handle_whatsapp_message(request)
                logger.info("✅ MINIMAL: Message processed successfully")
                return result
                
            except ImportError as import_error:
                logger.error(f"❌ MINIMAL: Import error: {str(import_error)}")
                return jsonify({
                    'error': 'Import error',
                    'message': str(import_error),
                    'timestamp': datetime.now().isoformat()
                }), 500
                
            except Exception as processing_error:
                logger.error(f"❌ MINIMAL: Processing error: {str(processing_error)}")
                logger.error(f"MINIMAL: Traceback: {traceback.format_exc()}")
                
                return jsonify({
                    'error': 'Processing error',
                    'message': str(processing_error),
                    'timestamp': datetime.now().isoformat()
                }), 500
    
    except Exception as e:
        logger.error(f"❌ MINIMAL: Error in twilio_webhook: {str(e)}")
        logger.error(f"MINIMAL: Traceback: {traceback.format_exc()}")
        
        return jsonify({
            'error': 'Webhook error',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@webhook_bp.route('/health', methods=['GET'])
def webhook_health():
    """Health check for webhook endpoints"""
    return jsonify({
        'status': 'healthy',
        'service': 'webhook-handler-minimal',
        'region': 'africa-south1',
        'timestamp': datetime.now().isoformat()
    })

@webhook_bp.route('/test', methods=['GET', 'POST'])
def webhook_test():
    """Test endpoint"""
    return jsonify({
        'status': 'MINIMAL TEST ENDPOINT',
        'method': request.method,
        'url': request.url,
        'headers': dict(request.headers),
        'form': dict(request.form),
        'timestamp': datetime.now().isoformat()
    })