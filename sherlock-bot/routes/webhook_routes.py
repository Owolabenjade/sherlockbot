# routes/webhook_routes.py - Production WhatsApp Business Routes
from flask import Blueprint, request, jsonify
from services.twilio_service import validate_twilio_request
from controllers.webhook_controller import handle_whatsapp_message
from controllers.payment_controller import process_payment_webhook
from utils.logger import get_logger
from utils.file_utils import cleanup_temp_files
from config import Config
import traceback

# Initialize logger
logger = get_logger()

# Create blueprint
webhook_bp = Blueprint('webhook', __name__)

@webhook_bp.route('/twilio', methods=['POST'])
def twilio_webhook():
    """Handle incoming WhatsApp messages via Twilio"""
    
    try:
        logger.info(f"📨 Received WhatsApp webhook from {request.remote_addr}")
        
        # Validate Twilio request in production
        if Config.IS_PRODUCTION:
            if not validate_twilio_request(request):
                logger.warning("⚠️ Invalid Twilio signature - rejecting request")
                return jsonify({'error': 'Invalid signature'}), 403
        else:
            # In development, log validation status but continue
            is_valid = validate_twilio_request(request)
            logger.info(f"Development mode - Signature valid: {is_valid}")
        
        # Process the WhatsApp message
        result = handle_whatsapp_message(request)
        
        # Clean up old temp files periodically
        try:
            cleanup_temp_files()
        except Exception as e:
            logger.warning(f"Failed to clean temp files: {e}")
        
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
        to = request.form.get('To')
        error_code = request.form.get('ErrorCode')
        
        logger.info(f"📊 Status update for {message_sid}: {message_status}")
        
        # Log errors if any
        if error_code:
            logger.error(f"❌ Message error {error_code} for {to}")
        
        # You can add logic here to track message delivery status
        # For example, update session status, retry failed messages, etc.
        
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
        'environment': 'production' if Config.IS_PRODUCTION else 'development',
        'whatsapp_number': Config.TWILIO_PHONE_NUMBER,
        'business_name': Config.BUSINESS_NAME,
        'endpoints': [
            '/webhook/twilio',
            '/webhook/twilio/status',
            '/webhook/paystack',
            '/webhook/health'
        ]
    })


@webhook_bp.route('/test', methods=['GET', 'POST'])
def webhook_test():
    """Test endpoint for webhook configuration"""
    if Config.IS_PRODUCTION:
        return jsonify({'error': 'Test endpoint disabled in production'}), 404
    
    return jsonify({
        'status': 'ok',
        'method': request.method,
        'headers': dict(request.headers),
        'webhook_url': 'https://africa-south1-cvreview-d1d4b.cloudfunctions.net/app_function/webhook/twilio'
    })