# services/sendgrid_service.py - Email service using SendGrid
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition
import base64
from utils.logger import get_logger
from config import Config

# Initialize logger
logger = get_logger()

def send_review_email(email, phone_number, review_result, download_link, report_path=None):
    """
    Send review email with PDF attachment
    
    Args:
        email (str): Recipient email
        phone_number (str): User's phone number
        review_result (dict): Review results
        download_link (str): Download link for the report
        report_path (str, optional): Path to PDF report file
        
    Returns:
        dict: Email send status
    """
    try:
        # Get review details
        review_type = review_result.get('review_type', 'basic')
        score = review_result.get('improvement_score', 0)
        
        # Create email
        message = Mail(
            from_email=(Config.EMAIL_FROM, Config.EMAIL_FROM_NAME),
            to_emails=email,
            subject='Your CV Review Report is Ready',
            html_content=generate_email_html(review_type, score, download_link, phone_number)
        )
        
        # Add PDF attachment if file path provided
        if report_path and os.path.exists(report_path):
            with open(report_path, 'rb') as f:
                file_content = f.read()
                
                attachment = Attachment()
                attachment.file_content = FileContent(base64.b64encode(file_content).decode())
                attachment.file_name = FileName('CV_Review_Report.pdf')
                attachment.file_type = FileType('application/pdf')
                attachment.disposition = Disposition('attachment')
                
                message.attachment = attachment
        
        # Send email
        sg = SendGridAPIClient(Config.SENDGRID_API_KEY)
        response = sg.send(message)
        
        # Log result
        if response.status_code == 202:
            logger.info(f"Email sent successfully to {email}")
            return {
                'success': True,
                'message': 'Email sent successfully'
            }
        else:
            logger.error(f"Failed to send email to {email}: {response.status_code} - {response.body}")
            return {
                'success': False,
                'error': f"Failed to send email: {response.status_code}"
            }
    
    except Exception as e:
        logger.error(f"Error sending email to {email}: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

def generate_email_html(review_type, score, download_link, phone_number):
    """
    Generate HTML content for review email
    
    Args:
        review_type (str): Type of review
        score (int): CV score
        download_link (str): Download link for the report
        phone_number (str): User's phone number
        
    Returns:
        str: HTML email content
    """
    # Create email HTML
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Your CV Review Report</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                margin: 0;
                padding: 0;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
            }}
            .header {{
                background-color: #4a6baf;
                padding: 20px;
                text-align: center;
                color: white;
            }}
            .content {{
                padding: 20px;
                background-color: #f9f9f9;
            }}
            .footer {{
                text-align: center;
                padding: 20px;
                font-size: 12px;
                color: #666;
            }}
            .button {{
                display: inline-block;
                background-color: #4a6baf;
                color: white;
                text-decoration: none;
                padding: 12px 24px;
                border-radius: 4px;
                margin: 20px 0;
            }}
            .score {{
                font-size: 24px;
                font-weight: bold;
                color: #4a6baf;
                text-align: center;
                margin: 20px 0;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Your CV Review Report</h1>
            </div>
            <div class="content">
                <p>Thank you for using Sherlock Bot CV Review Service!</p>
                
                <p>We've completed your {review_type.capitalize()} CV Review, and your report is now ready.</p>
    """
    
    # Add score for advanced review
    if review_type == 'advanced':
        html += f"""
                <div class="score">
                    <p>Your CV Score: {score}/100</p>
                </div>
                
                <p>Your comprehensive CV review includes detailed feedback on structure, content, formatting, and more. Use these insights to improve your CV and increase your chances of landing interviews.</p>
        """
    else:
        html += """
                <p>Your Basic CV Review provides key insights to help you improve your CV and make it more effective.</p>
        """
    
    html += f"""
                <p>To view your full report, click the button below:</p>
                
                <div style="text-align: center;">
                    <a href="{download_link}" class="button">Download Your Report</a>
                </div>
                
                <p>The report link will be active for 24 hours. If you need to access the report later, please contact us through WhatsApp.</p>
                
                <p>Best of luck with your job search!</p>
                
                <p>The Sherlock Bot Team</p>
            </div>
            <div class="footer">
                <p>This email was sent to you because you requested a CV review via WhatsApp.</p>
                <p>To contact us, message <a href="https://wa.me/{phone_number.replace('whatsapp:', '')}">{phone_number.replace('whatsapp:', '')}</a> on WhatsApp.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html