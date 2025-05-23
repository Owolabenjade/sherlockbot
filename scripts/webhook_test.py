# scripts/webhook_test.py - Test webhook endpoints locally
import requests
import argparse
import json
from datetime import datetime

def test_twilio_webhook(webhook_url, phone_number, message_body=None):
    """
    Test Twilio webhook endpoint with simulated WhatsApp message
    
    Args:
        webhook_url (str): Webhook URL to test
        phone_number (str): Phone number to simulate message from
        message_body (str, optional): Message body
    """
    if not message_body:
        message_body = "Hello, this is a test message from webhook_test.py script."
    
    # Ensure phone number has correct format
    if not phone_number.startswith('whatsapp:'):
        phone_number = f"whatsapp:{phone_number}"
    
    # Create simulated Twilio webhook payload
    payload = {
        'From': phone_number,
        'To': 'whatsapp:+18383682677',  # Your Twilio number
        'Body': message_body,
        'NumMedia': '0',
        'MessageSid': f'SM{datetime.now().strftime("%Y%m%d%H%M%S")}',
        'AccountSid': 'AC33348c48abeccb764aa89188107369c7'
    }
    
    print(f"Sending test webhook to {webhook_url}...")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        # Send POST request to webhook URL
        response = requests.post(webhook_url, data=payload)
        
        # Check response
        if response.status_code == 200:
            print(f"✅ Webhook test successful! Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return True
        else:
            print(f"❌ Webhook test failed! Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    
    except Exception as e:
        print(f"❌ Error testing webhook: {str(e)}")
        return False

def test_paystack_webhook(webhook_url):
    """
    Test Paystack webhook endpoint with simulated payment event
    
    Args:
        webhook_url (str): Webhook URL to test
    """
    # Create simulated Paystack webhook payload
    payload = {
        'event': 'charge.success',
        'data': {
            'reference': f'test_ref_{datetime.now().strftime("%Y%m%d%H%M%S")}',
            'status': 'success',
            'amount': 500000,  # 5,000 in kobo
            'currency': 'NGN',
            'metadata': {
                'phone_number': '+2341234567890',
                'product_name': 'Advanced CV Review',
                'service': 'sherlock_bot'
            }
        }
    }
    
    # Paystack typically sends signature in headers
    headers = {
        'x-paystack-signature': 'test_signature',  # Not a valid signature for production
        'Content-Type': 'application/json'
    }
    
    print(f"Sending test webhook to {webhook_url}...")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        # Send POST request to webhook URL
        response = requests.post(webhook_url, json=payload, headers=headers)
        
        # Check response
        if response.status_code == 200:
            print(f"✅ Webhook test successful! Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return True
        else:
            print(f"❌ Webhook test failed! Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    
    except Exception as e:
        print(f"❌ Error testing webhook: {str(e)}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Test webhook endpoints')
    parser.add_argument('--url', required=True, help='Webhook URL to test')
    parser.add_argument('--type', choices=['twilio', 'paystack'], default='twilio', help='Type of webhook to test')
    parser.add_argument('--phone', help='Phone number for Twilio test (with country code, e.g., +2341234567890)')
    parser.add_argument('--message', help='Custom message body for Twilio test')
    
    args = parser.parse_args()
    
    if args.type == 'twilio':
        if not args.phone:
            parser.error("--phone is required for Twilio webhook test")
        test_twilio_webhook(args.url, args.phone, args.message)
    else:
        test_paystack_webhook(args.url)