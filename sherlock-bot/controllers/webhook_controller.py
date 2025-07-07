# controllers/webhook_controller.py - Production WhatsApp with Direct File Upload
import os
import time
import traceback
from datetime import datetime
from flask import request
from twilio.twiml.messaging_response import MessagingResponse
from services.firebase_service import get_user_session, update_user_session, upload_cv_to_storage
from services.twilio_service import send_whatsapp_message
from controllers.cv_controller import process_cv_upload
from controllers.payment_controller import create_payment_link
from utils.logger import get_logger
from utils.file_utils import save_temp_file, get_file_extension, allowed_file
from utils.validation import validate_email
from config import Config

# Initialize logger
logger = get_logger()

# Conversation states
STATES = {
    'WELCOME': 'welcome',
    'AWAITING_CV': 'awaiting_cv',
    'AWAITING_REVIEW_TYPE': 'awaiting_review_type',
    'AWAITING_PAYMENT': 'awaiting_payment',
    'AWAITING_EMAIL': 'awaiting_email',
    'PROCESSING': 'processing',
    'COMPLETED': 'completed'
}

def handle_whatsapp_message(request):
    """
    Process incoming WhatsApp message with direct file upload
    
    Args:
        request: Flask request object
        
    Returns:
        Response: TwiML response
    """
    logger.info("🚀 Starting production WhatsApp message handler")
    
    try:
        # Extract message data
        message_body = request.form.get('Body', '').strip()
        sender = request.form.get('From', '')
        num_media = int(request.form.get('NumMedia', 0))
        
        logger.info(f"📨 Message received from {sender}: {message_body}")
        logger.info(f"📎 Number of media attachments: {num_media}")
        
        # Get or create user session
        session = get_user_session(sender)
        current_state = session.get('state', STATES['WELCOME'])
        
        logger.info(f"👤 User state: {current_state}")
        
        # Create TwiML response
        resp = MessagingResponse()
        
        # Handle different conversation states
        if current_state == STATES['WELCOME']:
            handle_welcome_state(resp, session, sender, message_body)
            
        elif current_state == STATES['AWAITING_CV']:
            handle_awaiting_cv_state(resp, session, sender, message_body, num_media, request)
            
        elif current_state == STATES['AWAITING_REVIEW_TYPE']:
            handle_review_type_state(resp, session, sender, message_body)
            
        elif current_state == STATES['AWAITING_PAYMENT']:
            handle_payment_state(resp, session, sender, message_body)
            
        elif current_state == STATES['AWAITING_EMAIL']:
            handle_email_state(resp, session, sender, message_body)
            
        elif current_state == STATES['PROCESSING']:
            # Don't send duplicate processing messages
            # Just acknowledge without repeating the processing message
            logger.info(f"User {sender} sent message while processing - ignoring to prevent duplicates")
            # Return empty response to avoid duplicate messages
            return str(resp)
            
        elif current_state == STATES['COMPLETED']:
            handle_completed_state(resp, session, sender, message_body)
            
        else:
            # Reset to welcome state if unknown
            session['state'] = STATES['WELCOME']
            update_user_session(sender, session)
            handle_welcome_state(resp, session, sender, message_body)
        
        return str(resp)
        
    except Exception as e:
        logger.error(f"❌ Error in handle_whatsapp_message: {str(e)}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        
        # Return error response
        resp = MessagingResponse()
        resp.message("⚠️ Sorry, an error occurred while processing your request. Please try again or contact support if the issue persists.")
        return str(resp)


def handle_welcome_state(resp, session, sender, message_body):
    """Handle the welcome state"""
    # Check for restart keywords
    if message_body.lower() in ['start', 'restart', 'begin', 'hello', 'hi']:
        welcome_msg = """🔍 **Welcome to Sherlock CV Review!** 🔍

I'm here to help you improve your CV and increase your chances of landing your dream job.

📋 **Our Services:**
• **Basic Review (FREE)**: Get quick insights and key improvement areas
• **Advanced Review (₦5,000)**: Comprehensive analysis with detailed PDF report

📎 **To get started, simply send me your CV file** (PDF or Word document).

Ready? Just attach your CV and send it to me!"""
        
        resp.message(welcome_msg)
        
        # Update session state
        session['state'] = STATES['AWAITING_CV']
        update_user_session(sender, session)
    else:
        # User might be trying to send a command
        resp.message("👋 Hello! Type 'start' to begin your CV review journey.")


def handle_awaiting_cv_state(resp, session, sender, message_body, num_media, request):
    """Handle CV upload state - Direct file upload only"""
    
    if num_media > 0:
        # User sent a file attachment
        logger.info(f"📄 User sent {num_media} file(s)")
        
        try:
            # Get the first media attachment
            media_url = request.form.get('MediaUrl0')
            media_content_type = request.form.get('MediaContentType0', '')
            
            logger.info(f"📎 Media URL: {media_url}")
            logger.info(f"📎 Content Type: {media_content_type}")
            
            # Check if it's a supported file type
            file_extension = get_file_extension(media_content_type)
            
            if file_extension not in ['pdf', 'docx', 'doc']:
                resp.message("❌ Please send a PDF or Word document (DOC/DOCX). Other file types are not supported.")
                return
            
            # Download the file
            resp.message("📥 Receiving your CV... Please wait a moment.")
            
            # Download file from WhatsApp
            local_file_path = save_temp_file(media_url, file_extension)
            logger.info(f"✅ CV downloaded to: {local_file_path}")
            
            # Upload to Firebase Storage
            storage_path = upload_cv_to_storage(local_file_path, sender)
            logger.info(f"☁️ CV uploaded to Firebase: {storage_path}")
            
            # Store in session
            session['cv_storage_path'] = storage_path
            session['cv_file_name'] = f"cv.{file_extension}"
            session['state'] = STATES['AWAITING_REVIEW_TYPE']
            update_user_session(sender, session)
            
            # Clean up local file
            if os.path.exists(local_file_path):
                os.remove(local_file_path)
            
            # Ask for review type
            review_type_msg = """✅ **CV received successfully!**

Now, please choose your review type:

1️⃣ **Basic Review (FREE)**
   • Key strengths and weaknesses
   • Quick improvement suggestions
   • Essential formatting tips

2️⃣ **Advanced Review (₦5,000)**
   • Comprehensive analysis
   • Detailed PDF report
   • Section-by-section feedback
   • ATS optimization tips
   • Industry-specific recommendations
   • CV score out of 100

Reply with '1' for Basic Review or '2' for Advanced Review."""
            
            resp.message(review_type_msg)
            logger.info("✅ CV processed successfully")
            
        except Exception as e:
            logger.error(f"Error processing CV file: {str(e)}")
            resp.message("❌ Sorry, I couldn't process your CV file. Please make sure it's a valid PDF or Word document (max 16MB) and try again. If the issue persists, contact support.")
            
    else:
        # No file attached
        if message_body.lower() in ['restart', 'start over', 'cancel']:
            session['state'] = STATES['WELCOME']
            update_user_session(sender, session)
            resp.message("🔄 Restarting... Type 'start' to begin again.")
        else:
            resp.message("📎 Please send your CV as an attachment. Simply attach your PDF or Word document and send it to me!")


def handle_review_type_state(resp, session, sender, message_body):
    """Handle review type selection"""
    choice = message_body.strip()
    
    if choice == '1':
        # Basic review selected
        session['review_type'] = 'basic'
        session['state'] = STATES['PROCESSING']
        update_user_session(sender, session)
        
        resp.message("🔄 Processing your Basic CV Review. This will take a moment...")
        
        # Process CV asynchronously
        process_cv_async(sender, session, 'basic')
        
    elif choice == '2':
        # Advanced review selected
        session['review_type'] = 'advanced'
        session['state'] = STATES['AWAITING_PAYMENT']
        update_user_session(sender, session)
        
        # Create payment link
        payment_link = create_payment_link(
            sender,
            Config.ADVANCED_REVIEW_PRICE,
            Config.PAYMENT_CURRENCY
        )
        
        if payment_link:
            payment_msg = f"""💳 **Advanced Review Selected (₦5,000)**

Please complete your payment to proceed:

🔗 **Payment Link**: {payment_link}

✅ **After payment, you'll receive:**
• Comprehensive CV analysis
• Professional PDF report
• Personalized improvement plan
• ATS optimization tips

⏱️ Your review will be ready within 30 minutes after payment confirmation.

If you prefer the free Basic Review instead, reply with 'basic'."""
            
            resp.message(payment_msg)
            session['payment_link'] = payment_link
            update_user_session(sender, session)
        else:
            resp.message("❌ Sorry, I couldn't generate a payment link. Please try again or contact support.")
            
    elif message_body.lower() in ['restart', 'cancel']:
        session['state'] = STATES['WELCOME']
        update_user_session(sender, session)
        resp.message("🔄 Restarting... Type 'start' to begin again.")
        
    else:
        resp.message("❓ Please reply with '1' for Basic Review or '2' for Advanced Review.")


def handle_payment_state(resp, session, sender, message_body):
    """Handle payment confirmation state"""
    if message_body.lower() == 'basic':
        # User wants to switch to basic review
        session['review_type'] = 'basic'
        session['state'] = STATES['PROCESSING']
        update_user_session(sender, session)
        
        resp.message("🔄 Switching to Basic Review. Processing your CV...")
        process_cv_async(sender, session, 'basic')
        
    elif message_body.lower() in ['paid', 'done', 'completed']:
        resp.message("⏳ Checking your payment status. Please wait...")
        # Payment verification will be handled by the payment webhook
        
    else:
        # Resend payment link
        payment_link = session.get('payment_link', '')
        if payment_link:
            resp.message(f"💳 Please complete your payment here: {payment_link}\n\nOr reply 'basic' for the free Basic Review.")
        else:
            resp.message("❓ Please complete your payment or reply 'basic' for the free Basic Review.")


def handle_email_state(resp, session, sender, message_body):
    """Handle email collection for advanced review"""
    if message_body.lower() == 'skip':
        # Process without email
        session['state'] = STATES['PROCESSING']
        update_user_session(sender, session)
        
        resp.message("🔄 Processing your Advanced CV Review...")
        process_cv_async(sender, session, 'advanced')
        
    elif validate_email(message_body):
        # Valid email provided
        session['email'] = message_body
        session['state'] = STATES['PROCESSING']
        update_user_session(sender, session)
        
        resp.message(f"✅ Email saved: {message_body}\n\n🔄 Processing your Advanced CV Review...")
        process_cv_async(sender, session, 'advanced', email=message_body)
        
    else:
        resp.message("❌ Please provide a valid email address or type 'skip' to continue without email.")


def handle_completed_state(resp, session, sender, message_body):
    """Handle completed state"""
    if message_body.lower() in ['start', 'restart', 'again', 'new']:
        # Start new review - Reset session completely
        session = {
            'phone_number': sender,
            'state': STATES['WELCOME'],
            'created_at': datetime.now().isoformat(),
            'last_activity': datetime.now().isoformat()
        }
        update_user_session(sender, session)
        handle_welcome_state(resp, session, sender, 'start')
    else:
        resp.message("✅ Your CV review is complete! Type 'start' to review another CV.")


def process_cv_async(sender, session, review_type, email=None):
    """Process CV review asynchronously"""
    try:
        # Get CV storage path from session
        cv_storage_path = session.get('cv_storage_path')
        
        if not cv_storage_path:
            send_whatsapp_message(sender, "❌ Error: CV file not found. Please start over by typing 'start'.")
            session['state'] = STATES['WELCOME']
            update_user_session(sender, session)
            return
        
        # Process the CV
        logger.info(f"Processing CV from storage: {cv_storage_path}")
        
        # Process CV using storage path
        result = process_cv_upload(cv_storage_path, review_type, sender, email)
        
        if result.get('success'):
            # Update session state to COMPLETED FIRST
            session['state'] = STATES['COMPLETED']
            session['last_review'] = result
            update_user_session(sender, session)
            
            # Send results
            if review_type == 'basic':
                send_basic_review_results(sender, result)
            else:
                send_advanced_review_results(sender, result)
            
        else:
            error_msg = result.get('error', 'Unknown error occurred')
            send_whatsapp_message(sender, f"❌ Error processing your CV: {error_msg}\n\nPlease try again or contact support.")
            
            # Reset state
            session['state'] = STATES['WELCOME']
            update_user_session(sender, session)
            
    except Exception as e:
        logger.error(f"Error in process_cv_async: {str(e)}")
        send_whatsapp_message(sender, "❌ An error occurred while processing your CV. Please try again.")
        
        # Reset state
        session['state'] = STATES['WELCOME']
        update_user_session(sender, session)


def send_basic_review_results(sender, result):
    """Send basic review results via WhatsApp"""
    insights = result.get('insights', [])
    
    # Send complete insights across multiple messages
    messages_sent = 0
    
    # Message 1: Header + First 2-3 insights
    if insights:
        message1 = "✅ **Basic CV Review Complete!**\n\n🔍 **Key Improvement Areas:**"
        
        # Add first 3 insights
        for i, insight in enumerate(insights[:3]):
            message1 += f"\n\n{i+1}. {insight}"
        
        if send_whatsapp_message(sender, message1).get('success'):
            messages_sent += 1
    
    # Message 2: Remaining insights
    if len(insights) > 3:
        message2 = "🔍 **Additional Recommendations:**"
        
        for i, insight in enumerate(insights[3:6], start=4):
            message2 += f"\n\n{i}. {insight}"
        
        if send_whatsapp_message(sender, message2).get('success'):
            messages_sent += 1
    
    # Final message: Next steps
    final_message = """💡 **Next Steps:**
1. Update your CV based on these suggestions
2. Consider our Advanced Review for detailed analysis
3. Tailor your CV for each job application

Type 'start' to review another CV or upgrade to Advanced Review for comprehensive analysis with a professional PDF report!"""
    
    if send_whatsapp_message(sender, final_message).get('success'):
        messages_sent += 1
    
    logger.info(f"✅ Basic review results sent to {sender} in {messages_sent} messages")


def send_advanced_review_results(sender, result):
    """Send advanced review results via WhatsApp"""
    score = result.get('improvement_score', 0)
    download_link = result.get('download_link', '')
    insights = result.get('insights', [])
    
    # Message 1: Score and top insights
    top_insights = "\n• ".join(insights[:3]) if insights else "See your PDF report for detailed insights"
    
    message1 = f"""🎉 **Advanced CV Review Complete!**

📊 **Your CV Score: {score}/100**

🔍 **Top Findings:**
• {top_insights}

📄 **Download Your Full Report:**
{download_link}"""
    
    # Send first message
    send_whatsapp_message(sender, message1)
    
    # Message 2: Report details
    message2 = f"""📋 **Your Report Includes:**
✅ Section-by-section analysis
✅ ATS optimization tips
✅ Industry-specific improvements
✅ Formatting recommendations
✅ Keyword optimization

💡 Report link active for 24 hours. {'Also sent to your email!' if result.get('email_sent') else 'Save for reference!'}

Type 'start' to review another CV!"""
    
    # Send second message
    send_whatsapp_message(sender, message2)
    
    logger.info(f"✅ Advanced review results sent to {sender}")