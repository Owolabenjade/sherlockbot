# services/paystack_service.py - Enhanced Paystack integration
import os
import hmac
import hashlib
import requests
import uuid
from datetime import datetime
from utils.logger import get_logger
from config import Config

# Initialize logger
logger = get_logger()

def create_payment_session(amount, currency, description, customer_email, metadata, success_url, cancel_url):
    """
    Create a payment session with Paystack
    
    Args:
        amount (int): Amount in kobo/cents
        currency (str): Currency code
        description (str): Payment description
        customer_email (str): Customer email
        metadata (dict): Additional metadata
        success_url (str): Success redirect URL
        cancel_url (str): Cancel redirect URL
        
    Returns:
        dict: Payment session data
    """
    try:
        # Format amount (Paystack expects amount in kobo/cents)
        amount_in_kobo = int(amount * 100)
        
        # Generate a unique reference for this transaction
        reference = f"cv-review-{uuid.uuid4().hex[:10]}"
        
        # Prepare request data
        data = {
            'amount': amount_in_kobo,
            'currency': currency,
            'email': customer_email,
            'metadata': metadata,
            'callback_url': success_url,
            'reference': reference,
            'description': description
        }
        
        # Set headers with SECRET key (for server-side operations)
        headers = {
            'Authorization': f'Bearer {Config.PAYSTACK_SECRET_KEY}',
            'Content-Type': 'application/json'
        }
        
        # Make API request
        response = requests.post(
            'https://api.paystack.co/transaction/initialize',
            json=data,
            headers=headers
        )
        
        # Check response
        if response.status_code == 200:
            result = response.json()
            
            if result.get('status'):
                # Return success with payment data
                payment_data = result.get('data', {})
                
                # Log success but don't log sensitive details
                logger.info(f"Payment session created for {customer_email} with reference {reference}")
                
                return {
                    'success': True,
                    'payment_reference': payment_data.get('reference'),
                    'payment_url': payment_data.get('authorization_url'),
                    'access_code': payment_data.get('access_code')
                }
        
        # Return error
        logger.error(f"Paystack API error: {response.status_code} - {response.text}")
        return {
            'success': False,
            'error': response.text
        }
    
    except Exception as e:
        logger.error(f"Error creating payment session: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

def verify_payment(reference):
    """
    Verify payment status with Paystack
    
    Args:
        reference (str): Payment reference
        
    Returns:
        dict: Payment verification data
    """
    try:
        # Set headers with SECRET key (only for backend)
        headers = {
            'Authorization': f'Bearer {Config.PAYSTACK_SECRET_KEY}',
            'Content-Type': 'application/json'
        }
        
        # Make API request to verification endpoint
        response = requests.get(
            f'https://api.paystack.co/transaction/verify/{reference}',
            headers=headers
        )
        
        # Check response
        if response.status_code == 200:
            result = response.json()
            
            if result.get('status'):
                data = result.get('data', {})
                
                # Check if payment is successful
                if data.get('status') == 'success':
                    # Return success with payment data
                    logger.info(f"Payment verification successful for reference {reference}")
                    
                    return {
                        'success': True,
                        'reference': data.get('reference'),
                        'amount': data.get('amount') / 100,  # Convert from kobo/cents
                        'currency': data.get('currency'),
                        'payment_date': data.get('paid_at'),
                        'metadata': data.get('metadata', {})
                    }
                else:
                    logger.warning(f"Payment verification failed: status is {data.get('status')}")
                    return {
                        'success': False,
                        'error': f"Payment verification failed: status is {data.get('status')}"
                    }
        
        # Return error
        logger.error(f"Paystack verification error: {response.status_code} - {response.text}")
        return {
            'success': False,
            'error': response.text
        }
    
    except Exception as e:
        logger.error(f"Error verifying payment: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

def validate_webhook_signature(request_body, signature):
    """
    Validate Paystack webhook signature
    
    Args:
        request_body (bytes): Request body
        signature (str): Paystack signature
        
    Returns:
        bool: Whether the signature is valid
    """
    try:
        # Remove 'sha512=' prefix if present (some webhooks include this)
        if signature and signature.startswith('sha512='):
            signature = signature[7:]
        
        # Use the Paystack secret key for webhook validation
        secret = Config.PAYSTACK_SECRET_KEY
        expected_signature = hmac.new(
            secret.encode('utf-8'),
            request_body,
            hashlib.sha512
        ).hexdigest()
        
        # Compare signatures using constant-time comparison
        return hmac.compare_digest(expected_signature, signature)
    
    except Exception as e:
        logger.error(f"Error validating webhook signature: {str(e)}")
        return False