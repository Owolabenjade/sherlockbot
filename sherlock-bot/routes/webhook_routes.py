# routes/webhook_routes.py - TEMPORARY DEBUG VERSION
from flask import Blueprint, request, jsonify
from controllers.webhook_controller import handle_whatsapp_message
from services.twilio_service import validate_twilio_request, validate_twilio_request_debug
from services.paystack_service import validate_webhook_signature
from controllers.payment_controller import process_payment_webhook
from utils.logger import get_logger

# Initialize logger
logger = get_logger()

# Create blueprint
webhook_bp = Blueprint('webhook', __name__)

@webhook_bp.route('/twilio', methods=['POST', 'GET'])
def twilio_webhook():
    """Handle incoming WhatsApp messages via Twilio - DEBUG VERSION"""
    
    # Log basic request info
    logger.info(f"🔄 Received {request.method} request to /webhook/twilio")
    logger.info(f"Request URL: {request.url}")
    logger.info(f"Content-Type: {request.content_type}")
    
    # Handle GET requests for testing
    if request.method == 'GET':
        return jsonify({
            'status': '✅ Webhook endpoint is active',
            'method': 'GET',
            'url': request.url,
            'timestamp': str(__import__('datetime').datetime.now())
        })
    
    # For POST requests, use debug validation first
    logger.info("🔍 Starting debug validation...")
    debug_valid = validate_twilio_request_debug(request)
    
    if not debug_valid:
        logger.warning("❌ Debug validation failed")
        # Try normal validation as fallback
        logger.info("🔄 Trying normal validation...")
        normal_valid = validate_twilio_request(request)
        
        if not normal_valid:
            logger.error("❌ Both debug and normal validation failed")
            return jsonify({
                'error': 'Invalid request signature',
                'debug_info': {
                    'url': request.url,
                    'method': request.method,
                    'headers': dict(request.headers),
                    'form': dict(request.form)
                }
            }), 403
        else:
            logger.info("✅ Normal validation succeeded")
    else:
        logger.info("✅ Debug validation succeeded")
    
    # Process the incoming message
    logger.info("📨 Processing WhatsApp message...")
    try:
        result = handle_whatsapp_message(request)
        logger.info("✅ Message processed successfully")
        return result
    except Exception as e:
        logger.error(f"❌ Error processing message: {str(e)}")
        return jsonify({'error': 'Message processing failed'}), 500

@webhook_bp.route('/twilio/status', methods=['POST'])
def twilio_status_webhook():
    """Handle Twilio status callbacks"""
    logger.info("📋 Received Twilio status callback")
    logger.info(f"Form data: {request.form.to_dict()}")
    return jsonify({'status': 'received'})

@webhook_bp.route('/paystack', methods=['POST'])
def paystack_webhook():
    """Handle Paystack payment webhooks"""
    # Validate request is from Paystack
    signature = request.headers.get('x-paystack-signature')
    if not validate_webhook_signature(request.data, signature):
        logger.warning("Invalid Paystack signature")
        return jsonify({'error': 'Invalid request signature'}), 403
    
    # Process the payment webhook
    result = process_payment_webhook(request)
    
    return result