# controllers/webhook_controller.py - Webhook handling logic
import os
from flask import request, jsonify
from twilio.twiml.messaging_response import MessagingResponse
from services.twilio_service import send_whatsapp_message, send_whatsapp_message_with_media
from services.firebase_service import get_user_session, update_user_session, upload_cv_to_storage
from controllers.cv_controller import process_cv_upload, get_review_by_id
from controllers.payment_controller import create_payment_link
from utils.logger import get_logger
from utils.file_utils import allowed_file, save_temp_file
from config import Config

# Initialize logger
logger = get_logger()

def handle_whatsapp_message(request):
    """
    Process incoming WhatsApp message
    
    Args:
        request: Flask request object
        
    Returns:
        Response: TwiML response
    """
    try:
        # Extract message data
        message_body = request.form.get('Body', '').strip()
        media_count = int(request.form.get('NumMedia', 0))
        sender = request.form.get('From', '')
        
        logger.info(f"Received message from {sender}: {message_body}")
        
        # Get or create user session
        session = get_user_session(sender)
        
        # Check if this is a new user
        if not session.get('state'):
            # New user, send welcome message
            session['state'] = 'welcome'
            update_user_session(sender, session)
            return send_welcome_message(sender)
        
        # Handle media attachments (CV uploads)
        if media_count > 0:
            return handle_media_message(sender, request, session)
        
        # Process text message based on current state
        current_state = session.get('state', 'welcome')
        
        if current_state == 'welcome':
            return handle_welcome_response(sender, message_body, session)
        
        elif current_state == 'awaiting_cv':
            return handle_awaiting_cv_response(sender, message_body, session)
        
        elif current_state == 'awaiting_payment_option':
            return handle_payment_option_response(sender, message_body, session)
        
        elif current_state == 'awaiting_payment':
            return handle_awaiting_payment_response(sender, message_body, session)
        
        elif current_state == 'awaiting_email':
            return handle_email_response(sender, message_body, session)
        
        elif current_state == 'completed':
            return handle_completed_state(sender, message_body, session)
        
        else:
            # Unknown state, reset to welcome
            session['state'] = 'welcome'
            update_user_session(sender, session)
            return send_welcome_message(sender)
    
    except Exception as e:
        logger.error(f"Error handling WhatsApp message: {str(e)}")
        
        # Return error response
        resp = MessagingResponse()
        resp.message("Sorry, something went wrong. Please try again later.")
        return str(resp)

def send_welcome_message(phone_number):
    """Send welcome message to new user"""
    message = (
        "👋 Welcome to Sherlock Bot CV Review!\n\n"
        "I'll help you improve your CV to stand out to employers. "
        "Here's how it works:\n\n"
        "1️⃣ Upload your CV (PDF or Word format)\n"
        "2️⃣ Choose basic (free) or advanced (₦5,000) review\n"
        "3️⃣ Receive detailed feedback\n\n"
        "Ready to get started? Upload your CV now or type 'help' for more information."
    )
    
    send_whatsapp_message(phone_number, message)
    
    # Create TwiML response
    resp = MessagingResponse()
    return str(resp)

def handle_media_message(sender, request, session):
    """Handle uploaded media (CV documents)"""
    try:
        # Check current state
        current_state = session.get('state', 'welcome')
        
        if current_state not in ['welcome', 'awaiting_cv', 'completed']:
            # Not expecting a CV at this point
            resp = MessagingResponse()
            resp.message("I wasn't expecting a document at this stage. Please follow the prompts.")
            return str(resp)
        
        # Get media data
        media_url = request.form.get('MediaUrl0', '')
        media_content_type = request.form.get('MediaContentType0', '')
        
        # Check if it's a document
        if not media_content_type.startswith(('application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml')):
            resp = MessagingResponse()
            resp.message("Please upload your CV as a PDF or Word document.")
            return str(resp)
        
        # Download and save the file
        file_extension = 'pdf' if 'pdf' in media_content_type else 'docx'
        local_file_path = save_temp_file(media_url, file_extension)
        
        # Upload to Firebase Storage
        storage_path = upload_cv_to_storage(local_file_path, sender)
        
        # Update session
        session['cv_storage_path'] = storage_path
        
        if current_state == 'completed':
            # User is submitting a new CV after completing a review
            session['state'] = 'awaiting_cv'
            session['previous_reviews'] = session.get('previous_reviews', []) + [session.get('current_review_id')]
            session['current_review_id'] = None
        else:
            # First time or awaiting CV state
            session['state'] = 'awaiting_payment_option'
        
        update_user_session(sender, session)
        
        # Send confirmation and options
        message = (
            "✅ Thank you for uploading your CV!\n\n"
            "Now, please choose a review option:\n\n"
            "1️⃣ Basic Review (Free)\n"
            "• Key improvement areas\n"
            "• Quick suggestions\n\n"
            "2️⃣ Advanced Review (₦5,000)\n"
            "• Comprehensive analysis\n"
            "• Detailed section-by-section feedback\n"
            "• Formatted PDF report\n"
            "• Email delivery option\n\n"
            "Reply with '1' for Basic or '2' for Advanced."
        )
        
        send_whatsapp_message(sender, message)
        
        # Clean up local file
        if os.path.exists(local_file_path):
            os.remove(local_file_path)
        
        # Create TwiML response
        resp = MessagingResponse()
        return str(resp)
    
    except Exception as e:
        logger.error(f"Error handling media message: {str(e)}")
        
        # Return error response
        resp = MessagingResponse()
        resp.message("Sorry, there was an error processing your document. Please try again.")
        return str(resp)

def handle_welcome_response(sender, message, session):
    """Handle user response in welcome state"""
    message_lower = message.lower()
    
    if message_lower == 'help':
        # Send help information
        help_text = (
            "📄 *Sherlock Bot CV Review* 📄\n\n"
            "*How it works:*\n"
            "1. Upload your CV document (PDF or Word)\n"
            "2. Choose your review option\n"
            "3. Receive feedback\n\n"
            "*Commands:*\n"
            "• 'restart' - Start over\n"
            "• 'help' - Show this message\n"
            "• 'about' - About this service\n\n"
            "Ready to start? Upload your CV now!"
        )
        
        send_whatsapp_message(sender, help_text)
    
    elif message_lower == 'about':
        # Send about information
        about_text = (
            "🔍 *About Sherlock Bot* 🔍\n\n"
            "Sherlock Bot is an AI-powered CV review service that helps job seekers optimize their CVs for better results.\n\n"
            "Our advanced analysis identifies key improvements that can increase your chances of getting interviews.\n\n"
            "Created by a team of HR experts and developers, Sherlock Bot combines industry knowledge with AI technology."
        )
        
        send_whatsapp_message(sender, about_text)
    
    else:
        # Prompt to upload CV
        upload_prompt = (
            "Please upload your CV as a PDF or Word document to get started. "
            "If you need help, type 'help'."
        )
        
        send_whatsapp_message(sender, upload_prompt)
    
    # Create TwiML response
    resp = MessagingResponse()
    return str(resp)

def handle_awaiting_cv_response(sender, message, session):
    """Handle user response when awaiting CV upload"""
    message_lower = message.lower()
    
    if message_lower == 'restart':
        # Reset session to welcome state
        session['state'] = 'welcome'
        update_user_session(sender, session)
        return send_welcome_message(sender)
    
    else:
        # Remind to upload CV
        reminder = (
            "I'm waiting for you to upload your CV. "
            "Please upload a PDF or Word document. "
            "If you want to start over, type 'restart'."
        )
        
        send_whatsapp_message(sender, reminder)
    
    # Create TwiML response
    resp = MessagingResponse()
    return str(resp)

def handle_payment_option_response(sender, message, session):
    """Handle response to payment option prompt"""
    # Check user's choice
    if message == '1' or message.lower() in ['basic', 'free', 'basic review']:
        # Basic (free) review selected
        session['review_type'] = 'basic'
        session['state'] = 'processing_review'
        update_user_session(sender, session)
        
        # Send processing message
        send_whatsapp_message(
            sender,
            "🔍 Processing your Basic Review...\n\nThis will take just a moment."
        )
        
        # Process the CV
        cv_path = session.get('cv_storage_path')
        review_result = process_cv_upload(cv_path, 'basic', sender)
        
        if review_result.get('success'):
            # Store review ID in session
            session['current_review_id'] = review_result.get('id')
            session['state'] = 'completed'
            update_user_session(sender, session)
            
            # Send review results
            insights = review_result.get('insights', [])
            insights_text = "\n\n".join([f"• {insight}" for insight in insights])
            
            result_message = (
                "✅ *Your Basic CV Review is Ready!* ✅\n\n"
                "*Key Insights:*\n\n"
                f"{insights_text}\n\n"
                "Want a more detailed analysis? Try our Advanced Review for ₦5,000.\n"
                "Reply with 'upgrade' to get the Advanced Review, or 'new' to submit a different CV."
            )
            
            send_whatsapp_message(sender, result_message)
        
        else:
            # Error processing CV
            session['state'] = 'awaiting_cv'
            update_user_session(sender, session)
            
            error_message = (
                "❌ Sorry, there was an error processing your CV. "
                "Please try uploading it again, or contact support if the issue persists."
            )
            
            send_whatsapp_message(sender, error_message)
    
    elif message == '2' or message.lower() in ['advanced', 'paid', 'advanced review']:
        # Advanced (paid) review selected
        session['review_type'] = 'advanced'
        session['state'] = 'awaiting_payment'
        update_user_session(sender, session)
        
        # Create payment link
        payment_link = create_payment_link(sender, Config.ADVANCED_REVIEW_PRICE, Config.PAYMENT_CURRENCY)
        
        if payment_link:
            # Store payment link in session
            session['payment_link'] = payment_link
            update_user_session(sender, session)
            
            # Send payment instructions
            payment_message = (
                "💳 *Advanced Review Payment* 💳\n\n"
                f"To proceed with your Advanced CV Review (₦{Config.ADVANCED_REVIEW_PRICE}), "
                "please complete the payment using the link below:\n\n"
                f"{payment_link}\n\n"
                "After payment, you'll receive a comprehensive review with detailed feedback and suggestions."
            )
            
            send_whatsapp_message(sender, payment_message)
        
        else:
            # Error creating payment link
            session['state'] = 'awaiting_payment_option'
            update_user_session(sender, session)
            
            error_message = (
                "❌ Sorry, there was an error creating your payment link. "
                "Please try again, or type 'restart' to start over."
            )
            
            send_whatsapp_message(sender, error_message)
    
    else:
        # Invalid option
        invalid_option = (
            "Please reply with '1' for Basic Review (Free) or '2' for Advanced Review (₦5,000)."
        )
        
        send_whatsapp_message(sender, invalid_option)
    
    # Create TwiML response
    resp = MessagingResponse()
    return str(resp)

def handle_awaiting_payment_response(sender, message, session):
    """Handle user response when awaiting payment"""
    message_lower = message.lower()
    
    if message_lower == 'cancel' or message_lower == 'restart':
        # Reset to payment option state
        session['state'] = 'awaiting_payment_option'
        update_user_session(sender, session)
        
        cancel_message = (
            "Payment cancelled. Would you like to try the Basic Review instead? "
            "Reply with '1' for Basic Review (Free) or '2' to try the Advanced Review payment again."
        )
        
        send_whatsapp_message(sender, cancel_message)
    
    elif message_lower == 'payment link' or message_lower == 'link':
        # Resend payment link
        payment_link = session.get('payment_link')
        
        if payment_link:
            resend_message = (
                "Here's your payment link again:\n\n"
                f"{payment_link}\n\n"
                "After payment, you'll receive a comprehensive review with detailed feedback and suggestions."
            )
            
            send_whatsapp_message(sender, resend_message)
        
        else:
            # No payment link in session, create a new one
            payment_link = create_payment_link(sender, Config.ADVANCED_REVIEW_PRICE, Config.PAYMENT_CURRENCY)
            
            if payment_link:
                # Store payment link in session
                session['payment_link'] = payment_link
                update_user_session(sender, session)
                
                new_link_message = (
                    "Here's a new payment link:\n\n"
                    f"{payment_link}\n\n"
                    "After payment, you'll receive a comprehensive review with detailed feedback and suggestions."
                )
                
                send_whatsapp_message(sender, new_link_message)
            
            else:
                error_message = (
                    "❌ Sorry, there was an error creating your payment link. "
                    "Please type 'restart' to start over."
                )
                
                send_whatsapp_message(sender, error_message)
    
    else:
        # Remind about payment
        reminder = (
            "I'm waiting for you to complete the payment for your Advanced Review.\n\n"
            "Use the payment link sent earlier, or type 'payment link' to get it again.\n\n"
            "If you want to cancel, type 'cancel'."
        )
        
        send_whatsapp_message(sender, reminder)
    
    # Create TwiML response
    resp = MessagingResponse()
    return str(resp)

def handle_email_response(sender, message, session):
    """Handle user response when awaiting email address"""
    message_lower = message.lower()
    
    if message_lower == 'skip':
        # Skip email delivery
        session['state'] = 'processing_review'
        update_user_session(sender, session)
        
        # Send processing message
        send_whatsapp_message(
            sender,
            "👍 No problem! Processing your Advanced Review without email delivery...\n\nThis may take a few moments."
        )
        
        # Process the CV for advanced review
        cv_path = session.get('cv_storage_path')
        review_result = process_cv_upload(cv_path, 'advanced', sender)
        
        if review_result.get('success'):
            # Store review ID in session
            session['current_review_id'] = review_result.get('id')
            session['state'] = 'completed'
            update_user_session(sender, session)
            
            # Send review results
            score = review_result.get('improvement_score', 0)
            download_link = review_result.get('download_link', '')
            
            result_message = (
                f"✅ *Your Advanced CV Review is Ready!* ✅\n\n"
                f"*CV Score: {score}/100*\n\n"
                f"📊 *Detailed Analysis:*\n"
                f"Your CV has been thoroughly reviewed. Download your full report here:\n\n"
                f"{download_link}\n\n"
                f"To submit another CV for review, type 'new'."
            )
            
            send_whatsapp_message(sender, result_message)
        
        else:
            # Error processing CV
            session['state'] = 'awaiting_cv'
            update_user_session(sender, session)
            
            error_message = (
                "❌ Sorry, there was an error processing your CV. "
                "Please try uploading it again, or contact support if the issue persists."
            )
            
            send_whatsapp_message(sender, error_message)
    
    elif '@' in message and '.' in message:
        # Valid email format, store it
        session['email'] = message
        session['state'] = 'processing_review'
        update_user_session(sender, session)
        
        # Send processing message
        send_whatsapp_message(
            sender,
            f"📧 Great! We'll also send your review to {message}.\n\nProcessing your Advanced Review now...\n\nThis may take a few moments."
        )
        
        # Process the CV for advanced review with email
        cv_path = session.get('cv_storage_path')
        review_result = process_cv_upload(cv_path, 'advanced', sender, email=message)
        
        if review_result.get('success'):
            # Store review ID in session
            session['current_review_id'] = review_result.get('id')
            session['state'] = 'completed'
            update_user_session(sender, session)
            
            # Send review results
            score = review_result.get('improvement_score', 0)
            download_link = review_result.get('download_link', '')
            
            result_message = (
                f"✅ *Your Advanced CV Review is Ready!* ✅\n\n"
                f"*CV Score: {score}/100*\n\n"
                f"📊 *Detailed Analysis:*\n"
                f"Your CV has been thoroughly reviewed. Download your full report here:\n\n"
                f"{download_link}\n\n"
                f"📧 The report has also been sent to your email: {message}\n\n"
                f"To submit another CV for review, type 'new'."
            )
            
            send_whatsapp_message(sender, result_message)
        
        else:
            # Error processing CV
            session['state'] = 'awaiting_cv'
            update_user_session(sender, session)
            
            error_message = (
                "❌ Sorry, there was an error processing your CV. "
                "Please try uploading it again, or contact support if the issue persists."
            )
            
            send_whatsapp_message(sender, error_message)
    
    else:
        # Invalid email format
        invalid_email = (
            "That doesn't look like a valid email address. "
            "Please enter a valid email address or type 'skip' to continue without email delivery."
        )
        
        send_whatsapp_message(sender, invalid_email)
    
    # Create TwiML response
    resp = MessagingResponse()
    return str(resp)

def handle_completed_state(sender, message, session):
    """Handle user response after review is completed"""
    message_lower = message.lower()
    
    if message_lower in ['new', 'restart', 'start over']:
        # Reset to awaiting CV state
        session['state'] = 'awaiting_cv'
        session['previous_reviews'] = session.get('previous_reviews', []) + [session.get('current_review_id')]
        session['current_review_id'] = None
        update_user_session(sender, session)
        
        new_cv_message = (
            "🔄 Let's review another CV!\n\n"
            "Please upload your CV document (PDF or Word format)."
        )
        
        send_whatsapp_message(sender, new_cv_message)
    
    elif message_lower == 'upgrade' and session.get('review_type') == 'basic':
        # User wants to upgrade to advanced review
        session['review_type'] = 'advanced'
        session['state'] = 'awaiting_payment'
        update_user_session(sender, session)
        
        # Create payment link
        payment_link = create_payment_link(sender, Config.ADVANCED_REVIEW_PRICE, Config.PAYMENT_CURRENCY)
        
        if payment_link:
            # Store payment link in session
            session['payment_link'] = payment_link
            update_user_session(sender, session)
            
            # Send payment instructions
            payment_message = (
                "💳 *Upgrade to Advanced Review* 💳\n\n"
                f"To upgrade to the Advanced CV Review (₦{Config.ADVANCED_REVIEW_PRICE}), "
                "please complete the payment using the link below:\n\n"
                f"{payment_link}\n\n"
                "After payment, you'll receive a comprehensive review with detailed feedback and suggestions."
            )
            
            send_whatsapp_message(sender, payment_message)
        
        else:
            # Error creating payment link
            error_message = (
                "❌ Sorry, there was an error creating your payment link. "
                "Please try again later, or type 'new' to submit a different CV."
            )
            
            send_whatsapp_message(sender, error_message)
    
    elif message_lower.startswith('show review') or message_lower == 'view':
        # Show current review
        review_id = session.get('current_review_id')
        
        if review_id:
            review = get_review_by_id(review_id)
            
            if review:
                review_type = review.get('review_type', 'basic')
                
                if review_type == 'basic':
                    # Format basic review
                    insights = review.get('insights', [])
                    insights_text = "\n\n".join([f"• {insight}" for insight in insights])
                    
                    result_message = (
                        "📄 *Your Basic CV Review* 📄\n\n"
                        "*Key Insights:*\n\n"
                        f"{insights_text}\n\n"
                        "Want a more detailed analysis? Try our Advanced Review for ₦5,000.\n"
                        "Reply with 'upgrade' to get the Advanced Review, or 'new' to submit a different CV."
                    )
                
                else:
                    # Format advanced review
                    score = review.get('improvement_score', 0)
                    download_link = review.get('download_link', '')
                    
                    result_message = (
                        f"📄 *Your Advanced CV Review* 📄\n\n"
                        f"*CV Score: {score}/100*\n\n"
                        f"📊 *Detailed Analysis:*\n"
                        f"Download your full report here:\n\n"
                        f"{download_link}\n\n"
                        f"To submit another CV for review, type 'new'."
                    )
                
                send_whatsapp_message(sender, result_message)
            
            else:
                # Review not found
                not_found_message = (
                    "❌ Sorry, I couldn't find your review. "
                    "Please type 'new' to submit a CV for review."
                )
                
                send_whatsapp_message(sender, not_found_message)
        
        else:
            # No review ID in session
            no_review_message = (
                "You don't have any completed reviews yet. "
                "Please type 'new' to submit a CV for review."
            )
            
            send_whatsapp_message(sender, no_review_message)
    
    else:
        # Default response
        options_message = (
            "Your CV review is complete. Here are your options:\n\n"
            "• Type 'new' to submit another CV\n"
            "• Type 'view' to see your review again\n"
            f"• Type 'upgrade' to get an Advanced Review (if you had a Basic Review)\n"
            "• Type 'help' for more information"
        )
        
        send_whatsapp_message(sender, options_message)
    
    # Create TwiML response
    resp = MessagingResponse()
    return str(resp)