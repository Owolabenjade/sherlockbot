# controllers/payment_controller.py - Payment processing logic
import os
import json
from flask import request, jsonify, url_for
from services.paystack_service import create_payment_session, verify_payment
from services.firebase_service import get_user_session, update_user_session
from services.twilio_service import send_whatsapp_message
from utils.logger import get_logger
from config import Config

# Initialize logger
logger = get_logger()

def create_payment_link(phone_number, amount, currency):
    """
    Create a payment link for advanced review
    
    Args:
        phone_number (str): User's phone number
        amount (int): Payment amount in kobo/cents
        currency (str): Currency code
        
    Returns:
        str: Payment link URL
    """
    try:
        # Format phone number (remove whatsapp: prefix)
        formatted_phone = phone_number.replace('whatsapp:', '')
        
        # Get success and cancel URLs
        base_url = os.getenv('BASE_URL', request.url_root.rstrip('/'))
        success_url = f"{base_url}{Config.PAYMENT_SUCCESS_URL}"
        cancel_url = f"{base_url}{Config.PAYMENT_CANCEL_URL}"
        
        # Create payment metadata
        metadata = {
            'phone_number': formatted_phone,
            'product_name': 'Advanced CV Review',
            'service': 'sherlock_bot'
        }
        
        # Create payment session
        payment_session = create_payment_session(
            amount,
            currency,
            'Advanced CV Review by Sherlock Bot',
            formatted_phone,
            metadata,
            success_url,
            cancel_url
        )
        
        if payment_session.get('success'):
            # Return payment link
            return payment_session.get('payment_url')
        else:
            logger.error(f"Failed to create payment session: {payment_session.get('error')}")
            return None
    
    except Exception as e:
        logger.error(f"Error creating payment link: {str(e)}")
        return None

def process_payment_webhook(request):
    """
    Process Paystack payment webhook
    
    Args:
        request: Flask request object
        
    Returns:
        Response: JSON response
    """
    try:
        # Parse webhook data
        payload = request.json
        event = payload.get('event')
        
        logger.info(f"Received Paystack webhook: {event}")
        
        # Handle different event types
        if event == 'charge.success':
            return handle_successful_payment(payload.get('data', {}))
        elif event == 'transfer.success':
            # Handle transfer success if needed
            logger.info('Transfer successful')
            return jsonify({'status': 'success', 'message': 'Transfer noted'})
        else:
            logger.info(f"Unhandled webhook event: {event}")
            return jsonify({'status': 'success', 'message': 'Event noted'})
    
    except Exception as e:
        logger.error(f"Error processing payment webhook: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

def handle_successful_payment(data):
    """
    Handle successful payment notification
    
    Args:
        data (dict): Payment data from webhook
        
    Returns:
        Response: JSON response
    """
    try:
        # Extract payment details
        reference = data.get('reference')
        status = data.get('status')
        
        if not reference or status != 'success':
            logger.warning(f"Payment not successful: {reference}, status: {status}")
            return jsonify({'status': 'error', 'message': 'Payment not successful'}), 400
        
        # Extract customer info from metadata
        metadata = data.get('metadata', {})
        phone_number = metadata.get('phone_number')
        
        if not phone_number:
            logger.warning(f"No phone number in metadata for payment {reference}")
            return jsonify({'status': 'error', 'message': 'No phone number in metadata'}), 400
        
        # Format phone number for WhatsApp
        formatted_phone = f"whatsapp:{phone_number}" if not phone_number.startswith('whatsapp:') else phone_number
        
        # Verify payment with Paystack API
        verification = verify_payment(reference)
        
        if not verification.get('success'):
            logger.warning(f"Payment verification failed for {reference}: {verification.get('error')}")
            return jsonify({'status': 'error', 'message': 'Payment verification failed'}), 400
        
        # Get user session
        session = get_user_session(formatted_phone)
        
        # Update session with payment info
        session['payment_status'] = 'completed'
        session['payment_reference'] = reference
        session['payment_amount'] = verification.get('amount')
        session['payment_date'] = verification.get('payment_date')
        session['state'] = 'awaiting_email'
        
        # Update user session in Firestore
        update_user_session(formatted_phone, session)
        
        # Send WhatsApp notification to user
        send_whatsapp_message(
            formatted_phone,
            "💰 Your payment has been confirmed! Would you like to receive your advanced review by email as well? If yes, please reply with your email address, or type 'skip' to continue without email."
        )
        
        logger.info(f"Payment processed successfully for {formatted_phone}")
        
        return jsonify({
            'status': 'success',
            'message': 'Payment processed successfully'
        })
    
    except Exception as e:
        logger.error(f"Error handling payment: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500