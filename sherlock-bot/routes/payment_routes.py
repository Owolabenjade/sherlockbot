# routes/payment_routes.py - Payment route handlers
from flask import Blueprint, render_template, request, redirect, jsonify, url_for
from models.payment import Payment
from utils.logger import get_logger

# Initialize logger
logger = get_logger()

# Create blueprint
payment_bp = Blueprint('payment', __name__)

@payment_bp.route('/success')
def payment_success():
    """
    Payment success page
    
    Returns:
        Template: Success page
    """
    # Get payment reference from query parameter
    reference = request.args.get('reference')
    
    return render_template('payments/success.html', reference=reference)

@payment_bp.route('/cancel')
def payment_cancel():
    """
    Payment cancel page
    
    Returns:
        Template: Cancel page
    """
    return render_template('payments/cancel.html')

@payment_bp.route('/feedback', methods=['POST'])
def submit_feedback():
    """
    Submit payment feedback
    
    Returns:
        JSON: Success status
    """
    try:
        reason = request.form.get('cancelReason')
        feedback = request.form.get('feedbackText')
        
        # Save feedback to database
        payment = Payment()
        payment.save_feedback(reason, feedback)
        
        return jsonify({'status': 'success'})
    
    except Exception as e:
        logger.error(f"Error saving payment feedback: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500