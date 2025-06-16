# scripts/simple_twilio_test.py - Test Twilio without local dependencies
import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_twilio_credentials():
    """Test Twilio credentials using direct API call"""
    
    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    twilio_phone = os.getenv('TWILIO_PHONE_NUMBER')
    
    print("🔍 Testing Twilio Configuration...")
    print(f"📱 Account SID: {account_sid[:10] if account_sid else 'Not set'}...")
    print(f"🔑 Auth Token: {'Set' if auth_token else 'Not set'}")
    print(f"📞 Phone Number: {twilio_phone}")
    
    if not all([account_sid, auth_token, twilio_phone]):
        print("❌ Missing Twilio credentials in .env file")
        return False
    
    # Test by fetching account info
    try:
        url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}.json"
        
        response = requests.get(url, auth=(account_sid, auth_token))
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Twilio credentials are valid!")
            print(f"📊 Account Status: {data.get('status')}")
            print(f"💰 Account Type: {data.get('type')}")
            return True
        else:
            print(f"❌ Twilio API Error: {response.status_code}")
            print(f"📄 Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing Twilio: {str(e)}")
        return False

def send_test_message(to_number):
    """Send a test WhatsApp message using direct API"""
    
    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    from_number = os.getenv('TWILIO_PHONE_NUMBER')
    
    if not from_number.startswith('whatsapp:'):
        from_number = f"whatsapp:{from_number}"
    
    if not to_number.startswith('whatsapp:'):
        to_number = f"whatsapp:{to_number}"
    
    url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"
    
    data = {
        'From': from_number,
        'To': to_number,
        'Body': '🔍 Test message from Sherlock Bot! If you receive this, WhatsApp integration is working correctly.'
    }
    
    try:
        response = requests.post(url, data=data, auth=(account_sid, auth_token))
        
        if response.status_code == 201:
            result = response.json()
            print(f"✅ Message sent successfully!")
            print(f"📨 Message SID: {result['sid']}")
            print(f"📊 Status: {result['status']}")
            return True
        else:
            print(f"❌ Failed to send message: {response.status_code}")
            print(f"📄 Response: {response.text}")
            
            # Common error explanations
            if response.status_code == 401:
                print("\n🔧 This is an authentication error. Check:")
                print("   • TWILIO_ACCOUNT_SID is correct")
                print("   • TWILIO_AUTH_TOKEN is correct")
            elif response.status_code == 400:
                print("\n🔧 This might be a phone number format issue. Check:")
                print("   • TWILIO_PHONE_NUMBER includes country code")
                print("   • Target phone number is verified in Twilio sandbox")
            
            return False
            
    except Exception as e:
        print(f"❌ Error sending message: {str(e)}")
        return False

if __name__ == "__main__":
    import sys
    
    print("🚀 Simple Twilio WhatsApp Test\n")
    
    # Test credentials first
    if not test_twilio_credentials():
        print("\n❌ Credential test failed. Fix your .env file first.")
        sys.exit(1)
    
    # Get phone number
    if len(sys.argv) > 1:
        phone = sys.argv[1]
    else:
        phone = input("\n📱 Enter phone number to test (with country code, e.g., +2348100606935): ")
    
    if not phone.startswith('+'):
        print("❌ Phone number must start with + and country code")
        sys.exit(1)
    
    print(f"\n📤 Sending test message to {phone}...")
    
    if send_test_message(phone):
        print("\n🎉 Test completed successfully!")
        print("Check your WhatsApp for the test message.")
    else:
        print("\n❌ Test failed. Check the errors above and fix your configuration.")