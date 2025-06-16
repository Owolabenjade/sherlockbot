# scripts/test_whatsapp.py - FIXED version with correct path
import os
import sys
import argparse
from dotenv import load_dotenv

# Add sherlock-bot directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'sherlock-bot'))

# Load environment variables
load_dotenv()

try:
    from services.twilio_service import send_whatsapp_message
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running this from the project root directory")
    sys.exit(1)

def test_whatsapp_message(to_number, test_message=None):
    """
    Send a test WhatsApp message
    
    Args:
        to_number (str): Phone number to send message to
        test_message (str, optional): Custom test message
    """
    if not test_message:
        test_message = (
            "🔍 *Sherlock Bot CV Review - Test Message* 🔍\n\n"
            "This is a test message from Sherlock Bot CV Review service.\n\n"
            "If you're seeing this, the WhatsApp integration is working correctly!\n\n"
            "Reply with anything to confirm receipt."
        )
    
    # Ensure to_number has correct format
    if not to_number.startswith('+'):
        print("Error: Phone number must start with country code (e.g., +234...)")
        return False
    
    # Create whatsapp format if needed
    if not to_number.startswith('whatsapp:'):
        to_number = f"whatsapp:{to_number}"
    
    print(f"📞 Sending test message to {to_number}...")
    print(f"🔑 Using Twilio Account SID: {os.getenv('TWILIO_ACCOUNT_SID', 'Not set')[:10]}...")
    print(f"📱 From number: {os.getenv('TWILIO_PHONE_NUMBER', 'Not set')}")
    
    result = send_whatsapp_message(to_number, test_message)
    
    if result.get('success'):
        print(f"✅ Message sent successfully! SID: {result.get('sid')}")
        print(f"📊 Status: {result.get('status')}")
        return True
    else:
        print(f"❌ Failed to send message: {result.get('error')}")
        print("\n🔧 Troubleshooting tips:")
        print("1. Check your Twilio credentials in .env file")
        print("2. Ensure your phone number is verified in Twilio sandbox")
        print("3. Make sure TWILIO_PHONE_NUMBER includes 'whatsapp:' prefix")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Test Twilio WhatsApp integration')
    parser.add_argument('phone', help='Phone number to send test message to (with country code, e.g., +2341234567890)')
    parser.add_argument('--message', '-m', help='Custom test message')
    
    args = parser.parse_args()
    success = test_whatsapp_message(args.phone, args.message)
    
    sys.exit(0 if success else 1)