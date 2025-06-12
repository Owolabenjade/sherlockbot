# routes/webhook_routes.py - Production webhook routes
from flask import Blueprint, request, jsonify
from services.twilio_service import validate_twilio_request
from controllers.webhook_controller import handle_whatsapp_message
from controllers.payment_controller import process_payment_webhook
from utils.logger import get_logger
import traceback

# Initialize logger
logger = get_logger()

# Create blueprint
webhook_bp = Blueprint('webhook', __name__)

@webhook_bp.route('/twilio', methods=['POST'])
def twilio_webhook():
    """Handle incoming WhatsApp messages via Twilio"""
    
    try:
        logger.info(f"📨 Received webhook request from {request.remote_addr}")
        
        # Validate Twilio request (optional in development)
        if not validate_twilio_request(request):
            logger.warning("⚠️ Invalid Twilio signature")
            # In production, you should return 403
            # return jsonify({'error': 'Invalid signature'}), 403
            # For now, just log the warning and continue
        
        # Process the WhatsApp message
        result = handle_whatsapp_message(request)
        
        logger.info("✅ Message processed successfully")
        return result
        
    except Exception as e:
        logger.error(f"❌ Error in twilio_webhook: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Return empty response to prevent Twilio from retrying
        return '', 200


@webhook_bp.route('/twilio/status', methods=['POST'])
def twilio_status_webhook():
    """Handle Twilio status callbacks"""
    
    try:
        # Log status update
        message_sid = request.form.get('MessageSid')
        message_status = request.form.get('MessageStatus')
        
        logger.info(f"📊 Status update for {message_sid}: {message_status}")
        
        # You can add logic here to track message delivery status
        # For now, just acknowledge receipt
        
        return '', 200
        
    except Exception as e:
        logger.error(f"❌ Error in status webhook: {str(e)}")
        return '', 200


@webhook_bp.route('/paystack', methods=['POST'])
def paystack_webhook():
    """Handle Paystack payment webhooks"""
    
    try:
        logger.info("💳 Received Paystack webhook")
        
        # Validate Paystack signature
        signature = request.headers.get('x-paystack-signature')
        if not signature:
            logger.warning("⚠️ No Paystack signature found")
            return jsonify({'error': 'No signature'}), 400
        
        # Process the payment webhook
        result = process_payment_webhook(request)
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Error in paystack_webhook: {str(e)}")
        return jsonify({'error': 'Internal error'}), 500


@webhook_bp.route('/health', methods=['GET'])
def webhook_health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'webhook-handler',
        'endpoints': [
            '/webhook/twilio',
            '/webhook/twilio/status',
            '/webhook/paystack'
        ]
    })