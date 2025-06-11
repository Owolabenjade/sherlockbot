# routes/webhook_routes.py - Webhook route handlers
from flask import Blueprint, request, jsonify
from controllers.webhook_controller import handle_whatsapp_message
from services.twilio_service import validate_twilio_request
from services.paystack_service import validate_webhook_signature
from controllers.payment_controller import process_payment_webhook
from utils.logger import get_logger
import os
import traceback
from datetime import datetime

# Initialize logger
logger = get_logger()

# Create blueprint
webhook_bp = Blueprint('webhook', __name__)

@webhook_bp.route('/twilio', methods=['POST', 'GET'])
def twilio_webhook():
    """Handle incoming WhatsApp messages via Twilio"""
    
    try:
        # Log basic request info
        logger.info(f"🔄 Received {request.method} request to /webhook/twilio")
        logger.info(f"Request URL: {request.url}")
        logger.info(f"Content-Type: {request.content_type}")
        logger.info(f"Headers: {dict(request.headers)}")
        
        # Handle GET requests for testing
        if request.method == 'GET':
            return jsonify({
                'status': 'Webhook endpoint is active',
                'method': 'GET',
                'url': request.url,
                'timestamp': datetime.now().isoformat(),
                'function_region': 'africa-south1'
            })
        
        # Handle POST requests (actual webhook)
        if request.method == 'POST':
            logger.info(f"Form data: {dict(request.form)}")
            
            # Check if we're in development mode to skip validation
            skip_validation = os.getenv('FLASK_ENV') == 'development' or os.getenv('SKIP_TWILIO_VALIDATION') == 'true'
            
            if skip_validation:
                logger.info("⚠️ DEVELOPMENT MODE: Skipping Twilio signature validation")
                validation_passed = True
            else:
                # Validate request is from Twilio
                logger.info("🔐 Validating Twilio signature...")
                validation_passed = validate_twilio_request(request)
                
                if not validation_passed:
                    logger.warning("❌ Invalid Twilio signature")
                    
                    # Log debugging info
                    logger.info("Debug info for failed validation:")
                    logger.info(f"  - X-Twilio-Signature: {request.headers.get('X-Twilio-Signature', 'MISSING')}")
                    logger.info(f"  - Request URL: {request.url}")
                    logger.info(f"  - Form data keys: {list(request.form.keys())}")
                    
                    return jsonify({
                        'error': 'Invalid request signature',
                        'debug_info': {
                            'url': request.url,
                            'method': request.method,
                            'signature_present': 'X-Twilio-Signature' in request.headers,
                            'form_keys': list(request.form.keys())
                        }
                    }), 403
                else:
                    logger.info("✅ Twilio signature validation passed")
            
            # Process the incoming message
            logger.info("📨 Processing WhatsApp message...")
            
            try:
                result = handle_whatsapp_message(request)
                logger.info("✅ Message processed successfully")
                return result
                
            except Exception as processing_error:
                logger.error(f"❌ Error processing message: {str(processing_error)}")
                logger.error(f"Processing traceback: {traceback.format_exc()}")
                
                # Return a basic success response to Twilio to avoid retries
                # while we debug the processing issue
                return jsonify({
                    'status': 'received',
                    'message': 'Message received but processing failed',
                    'error': str(processing_error)
                })
    
    except Exception as e:
        logger.error(f"❌ Error in twilio_webhook: {str(e)}")
        logger.error(f"Webhook traceback: {traceback.format_exc()}")
        
        # Return basic success to avoid Twilio retries during debugging
        return jsonify({
            'status': 'error',
            'message': 'Webhook processing failed',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        })

@webhook_bp.route('/twilio/status', methods=['POST'])
def twilio_status_webhook():
    """Handle Twilio status callbacks"""
    try:
        logger.info("📋 Received Twilio status callback")
        logger.info(f"Form data: {dict(request.form)}")
        
        return jsonify({
            'status': 'Status callback received',
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Error in status webhook: {str(e)}")
        return jsonify({'error': str(e)}), 500

@webhook_bp.route('/paystack', methods=['POST'])
def paystack_webhook():
    """Handle Paystack payment webhooks"""
    
    try:
        logger.info("💳 Received Paystack webhook")
        
        # Check if we're in development mode to skip validation
        skip_validation = os.getenv('FLASK_ENV') == 'development' or os.getenv('SKIP_PAYSTACK_VALIDATION') == 'true'
        
        if skip_validation:
            logger.info("⚠️ DEVELOPMENT MODE: Skipping Paystack signature validation")
        else:
            # Validate request is from Paystack
            signature = request.headers.get('x-paystack-signature')
            if not validate_webhook_signature(request.data, signature):
                logger.warning("Invalid Paystack signature")
                return jsonify({'error': 'Invalid request signature'}), 403
        
        # Process the payment webhook
        result = process_payment_webhook(request)
        
        return result
        
    except Exception as e:
        logger.error(f"Error in paystack webhook: {str(e)}")
        logger.error(f"Paystack traceback: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

# Add health check endpoints for debugging
@webhook_bp.route('/health', methods=['GET'])
def webhook_health():
    """Health check for webhook endpoints"""
    return jsonify({
        'status': 'healthy',
        'service': 'webhook-handler',
        'region': 'africa-south1',
        'timestamp': datetime.now().isoformat(),
        'endpoints': {
            'twilio': '/webhook/twilio',
            'paystack': '/webhook/paystack',
            'status': '/webhook/twilio/status'
        }
    })

@webhook_bp.route('/test', methods=['GET', 'POST'])
def webhook_test():
    """Test endpoint for debugging"""
    return jsonify({
        'method': request.method,
        'url': request.url,
        'headers': dict(request.headers),
        'form': dict(request.form),
        'json': request.json,
        'data': request.data.decode('utf-8') if request.data else None,
        'timestamp': datetime.now().isoformat()
    })