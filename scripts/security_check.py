#!/usr/bin/env python3
# scripts/security_check.py - Check for exposed secrets

import os
import re
import sys

def check_for_secrets():
    """Check for exposed secrets in code files"""
    
    # Patterns that might indicate exposed secrets
    secret_patterns = [
        r'sk_live_[a-zA-Z0-9]+',  # Paystack secret keys
        r'pk_live_[a-zA-Z0-9]+',  # Paystack public keys (less sensitive but still)
        r'AC[a-zA-Z0-9]{32}',     # Twilio Account SID
        r'SG\.[a-zA-Z0-9_\-\.]{22}\.[a-zA-Z0-9_\-\.]{43}',  # SendGrid API keys
        r'whsec_[a-zA-Z0-9]+',    # Webhook secrets
    ]
    
    # Files to check (exclude .env files as they're supposed to have secrets)
    files_to_check = []
    for root, dirs, files in os.walk('.'):
        # Skip certain directories
        dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'venv', '.env']]
        
        for file in files:
            if file.endswith(('.py', '.md', '.json', '.js', '.html')):
                if not file.startswith('.env'):  # Skip .env files
                    files_to_check.append(os.path.join(root, file))
    
    secrets_found = []
    
    for file_path in files_to_check:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
                for pattern in secret_patterns:
                    matches = re.findall(pattern, content)
                    if matches:
                        for match in matches:
                            secrets_found.append({
                                'file': file_path,
                                'pattern': pattern,
                                'match': match[:10] + '...'  # Only show first 10 chars
                            })
        except Exception as e:
            continue
    
    return secrets_found

if __name__ == "__main__":
    print("🔍 Checking for exposed secrets...")
    
    secrets = check_for_secrets()
    
    if secrets:
        print("❌ SECRETS FOUND! Do not commit these files:")
        for secret in secrets:
            print(f"  📄 {secret['file']}: {secret['match']}")
        print("\n🔒 Remove these secrets and use environment variables instead!")
        sys.exit(1)
    else:
        print("✅ No exposed secrets found. Safe to commit!")
        sys.exit(0)