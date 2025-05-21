# routes/webhook_routes.py - Webhook route handlers
from flask import Blueprint, request, jsonify
from controllers.webhook_controller import handle_whatsapp_message
from services.twilio_service import validate_twilio_request
from services.paystack_service import validate_webhook_signature
from controllers.payment_controller import process_payment_webhook
from utils.logger import get_logger

# Initialize logger
logger = get_logger()

# Create blueprint
webhook_bp = Blueprint('webhook', __name__)

@webhook_bp.route('/twilio', methods=['POST'])
def twilio_webhook():
    """Handle incoming WhatsApp messages via Twilio"""
    # Validate request is from Twilio
    if not validate_twilio_request(request):
        logger.warning("Invalid Twilio signature")
        return jsonify({'error': 'Invalid request signature'}), 403
    
    # Process the incoming message
    result = handle_whatsapp_message(request)
    
    return result

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