# controllers/webhook_controller.py - Cloud Link Workaround Version - FIXED
import os
import time
import traceback
import re
from datetime import datetime
from flask import request
from twilio.twiml.messaging_response import MessagingResponse
from services.firebase_service import get_user_session, update_user_session, get_user_email
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
    Process incoming WhatsApp message with cloud link workflow
    
    Args:
        request: Flask request object
        
    Returns:
        Response: TwiML response
    """
    logger.info("🚀 Starting handle_whatsapp_message function")
    
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
            handle_awaiting_cv_state(resp, session, sender, message_body, num_media)
            
        elif current_state == STATES['AWAITING_REVIEW_TYPE']:
            handle_review_type_state(resp, session, sender, message_body)
            
        elif current_state == STATES['AWAITING_PAYMENT']:
            handle_payment_state(resp, session, sender, message_body)
            
        elif current_state == STATES['AWAITING_EMAIL']:
            handle_email_state(resp, session, sender, message_body)
            
        elif current_state == STATES['PROCESSING']:
            resp.message("⏳ Your CV review is still being processed. Please wait a moment...")
            
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
        welcome_msg = """🔍 Welcome to Sherlock Bot CV Review Service! 🔍

I'm here to help you improve your CV and increase your chances of landing your dream job.

📋 Our Services:
• **Basic Review (FREE)**: Get quick insights and key improvement areas
• **Advanced Review (₦5,000)**: Comprehensive analysis with detailed PDF report

To get started, please upload your CV to a cloud service (Google Drive, Dropbox, OneDrive, etc.) and share the link with me.

💡 Make sure the link has view access enabled!"""
        
        resp.message(welcome_msg)
        
        # Update session state
        session['state'] = STATES['AWAITING_CV']
        update_user_session(sender, session)
    else:
        # User might be trying to send a command
        resp.message("👋 Hello! Type 'start' to begin your CV review journey.")


def handle_awaiting_cv_state(resp, session, sender, message_body, num_media):
    """Handle CV upload state - Cloud link version"""
    # Check if user sent a link
    cloud_link_pattern = r'https?://(?:www\.)?(?:drive\.google\.com|dropbox\.com|onedrive\.live\.com|docs\.google\.com|drive\.dropbox\.com|1drv\.ms|bit\.ly|tinyurl\.com|short\.link)[\S]+'
    
    # Check for cloud storage links
    cloud_links = re.findall(cloud_link_pattern, message_body)
    
    if cloud_links:
        # User provided a cloud link
        cloud_link = cloud_links[0]  # Take the first link
        logger.info(f"📄 Cloud link detected: {cloud_link[:50]}...")
        
        try:
            # Download the file from cloud link
            logger.info("Attempting to download CV from cloud link")
            
            # For now, we'll simulate successful processing
            # In production, you'd implement actual cloud download logic
            
            # Store the cloud link in session
            session['cv_cloud_link'] = cloud_link
            session['state'] = STATES['AWAITING_REVIEW_TYPE']
            update_user_session(sender, session)
            
            # Ask for review type
            review_type_msg = """✅ CV link received successfully!

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
            logger.info("✅ CV cloud link processed successfully")
            
        except Exception as e:
            logger.error(f"Error processing cloud link: {str(e)}")
            resp.message("❌ Sorry, I couldn't access your CV from the provided link. Please make sure the link has public view access and try again.")
            
    elif num_media > 0:
        # User tried to attach file directly
        resp.message("📎 Please upload your CV to a cloud service (Google Drive, Dropbox, etc.) and share the link with me. Make sure the link has view access enabled!")
        
    else:
        # Check if user wants to restart
        if message_body.lower() in ['restart', 'start over', 'cancel']:
            session['state'] = STATES['WELCOME']
            update_user_session(sender, session)
            resp.message("🔄 Restarting... Type 'start' to begin again.")
        else:
            # No link found in message
            resp.message("🔗 Please share a link to your CV from Google Drive, Dropbox, or another cloud service. Make sure the link has view access enabled!")


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
            payment_msg = f"""💳 Advanced Review Selected (₦5,000)

Please complete your payment to proceed:

🔗 Payment Link: {payment_link}

✅ After payment, you'll receive:
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
    """Handle completed state - prevent duplicate processing"""
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
    """Process CV review asynchronously - FIXED to prevent duplicate messages"""
    try:
        # Get CV cloud link from session
        cv_cloud_link = session.get('cv_cloud_link')
        
        if not cv_cloud_link:
            send_whatsapp_message(sender, "❌ Error: CV link not found. Please start over by typing 'start'.")
            session['state'] = STATES['WELCOME']
            update_user_session(sender, session)
            return
        
        # Process the CV using the cloud link directly
        logger.info(f"Processing CV from cloud link: {cv_cloud_link}")
        
        # Pass the cloud link directly to process_cv_upload
        result = process_cv_upload(cv_cloud_link, review_type, sender, email)
        
        if result.get('success'):
            # Update session state to COMPLETED FIRST to prevent duplicate processing messages
            session['state'] = STATES['COMPLETED']
            session['last_review'] = result
            update_user_session(sender, session)
            
            # THEN send results (this order is crucial)
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
    """Send basic review results via WhatsApp - COMPLETE insights in multiple messages"""
    insights = result.get('insights', [])
    
    # Send complete insights across multiple messages
    messages_sent = 0
    
    # Message 1: Header + First 2 complete insights
    if insights:
        message1 = "✅ **Basic CV Review Complete!**\n\n🔍 **Key Improvement Areas:**"
        
        # Add first 2 insights completely (no truncation)
        for i, insight in enumerate(insights[:2]):
            message1 += f"\n\n• **{insight.split(':')[0] if ':' in insight else f'Tip {i+1}'}:** {insight.split(':', 1)[1].strip() if ':' in insight else insight}"
        
        if send_whatsapp_message(sender, message1).get('success'):
            messages_sent += 1
    
    # Message 2: Next 2-3 insights
    if len(insights) > 2:
        remaining_insights = insights[2:]
        message2 = "🔍 **Additional Recommendations:**"
        
        for i, insight in enumerate(remaining_insights[:3]):
            message2 += f"\n\n• **{insight.split(':')[0] if ':' in insight else f'Tip {i+3}'}:** {insight.split(':', 1)[1].strip() if ':' in insight else insight}"
        
        if send_whatsapp_message(sender, message2).get('success'):
            messages_sent += 1
    
    # Message 3: Any remaining insights (if more than 5 total)
    if len(insights) > 5:
        final_insights = insights[5:]
        message3 = "🔍 **Final Recommendations:**"
        
        for i, insight in enumerate(final_insights[:3]):
            message3 += f"\n\n• **{insight.split(':')[0] if ':' in insight else f'Additional Tip {i+1}'}:** {insight.split(':', 1)[1].strip() if ':' in insight else insight}"
        
        if send_whatsapp_message(sender, message3).get('success'):
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
    
    return {'success': messages_sent > 0}


def send_advanced_review_results(sender, result):
    """Send advanced review results via WhatsApp - FIXED with character limit handling"""
    score = result.get('improvement_score', 0)
    download_link = result.get('download_link', '')
    insights = result.get('insights', [])
    
    # Message 1: Score and top insights
    top_insights = insights[:2] if insights else []
    top_insights_text = "\n".join([f"• {insight[:100]}..." if len(insight) > 100 else f"• {insight}" for insight in top_insights])
    
    message1 = f"""🎉 **Advanced CV Review Complete!**

📊 **Your CV Score: {score}/100**

🔍 **Top Findings:**
{top_insights_text}

📄 **Download Your Full Report:**
{download_link}"""
    
    # Send first message
    send_result1 = send_whatsapp_message(sender, message1)
    
    # Message 2: Report details and next steps
    message2 = f"""📋 **Your Report Includes:**
✅ Section-by-section analysis
✅ ATS optimization tips
✅ Industry-specific improvements
✅ Formatting recommendations
✅ Keyword optimization

💡 Report link active for 24 hours. {
'Also sent to your email!' if result.get('email_sent') else 'Save for reference!'
}

Type 'start' to review another CV!"""
    
    # Send second message
    send_result2 = send_whatsapp_message(sender, message2)
    
    logger.info(f"✅ Advanced review results sent to {sender} in 2 messages")
    
    # Return success if at least one message was sent
    return send_result1 if send_result1.get('success') else send_result2