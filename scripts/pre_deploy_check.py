# scripts/pre_deploy_check.py - Pre-deployment testing script
import os
import sys
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_api_keys():
    """Check if all required API keys are set"""
    required_keys = [
        "TWILIO_ACCOUNT_SID", 
        "TWILIO_AUTH_TOKEN", 
        "TWILIO_PHONE_NUMBER",
        "PAYSTACK_PUBLIC_KEY",
        "PAYSTACK_SECRET_KEY",
        "SENDGRID_API_KEY"
    ]
    
    missing_keys = []
    for key in required_keys:
        if not os.getenv(key):
            missing_keys.append(key)
    
    if missing_keys:
        print(f"❌ Missing required API keys: {', '.join(missing_keys)}")
        return False
    
    print("✅ All required API keys are set")
    return True

def check_paystack_api():
    """Check Paystack API connection"""
    public_key = os.getenv("PAYSTACK_PUBLIC_KEY")
    secret_key = os.getenv("PAYSTACK_SECRET_KEY")
    
    if not (public_key and secret_key):
        print("❌ Paystack API keys not set")
        return False
    
    # Check if public key format is valid
    if not public_key.startswith("pk_"):
        print("❌ Invalid Paystack public key format")
        return False
    
    # Check if secret key format is valid
    if not secret_key.startswith("sk_"):
        print("❌ Invalid Paystack secret key format")
        return False
    
    # Test the API
    try:
        headers = {
            'Authorization': f'Bearer {secret_key}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(
            'https://api.paystack.co/transaction',
            headers=headers
        )
        
        if response.status_code != 200:
            print(f"❌ Paystack API error: {response.status_code} - {response.text}")
            return False
        
        print("✅ Paystack API connection successful")
        return True
    
    except Exception as e:
        print(f"❌ Error testing Paystack API: {str(e)}")
        return False

def check_cv_analyzer_api():
    """Check CV Analyzer API connection"""
    api_url = os.getenv("CV_ANALYSIS_API_URL", "https://cv-review-1.onrender.com/api/upload-and-analyze")
    
    try:
        # Test with a simple OPTIONS request to check if endpoint is reachable
        response = requests.options(api_url, timeout=10)
        
        if response.status_code >= 500:
            print(f"❌ CV Analyzer API error: {response.status_code}")
            return False
        
        print("✅ CV Analyzer API is reachable")
        return True
    
    except Exception as e:
        print(f"❌ Error testing CV Analyzer API: {str(e)}")
        return False

def main():
    """Run all pre-deployment checks"""
    print("Running pre-deployment checks...")
    
    checks = [
        check_api_keys,
        check_paystack_api,
        check_cv_analyzer_api
    ]
    
    results = [check() for check in checks]
    
    if all(results):
        print("\n✅ All checks passed. Ready for deployment.")
        return 0
    else:
        print("\n❌ Some checks failed. Fix the issues before deploying.")
        return 1

if __name__ == "__main__":
    sys.exit(main())