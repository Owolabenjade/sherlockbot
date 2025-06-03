# utils/validation.py - Input validation utilities
import re
from typing import Optional, Dict, Any

def validate_email(email: str) -> bool:
    """
    Validate email address format
    
    Args:
        email (str): Email address to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not email:
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_phone_number(phone: str) -> bool:
    """
    Validate phone number format
    
    Args:
        phone (str): Phone number to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not phone:
        return False
    
    # Remove all non-digit characters
    digits = re.sub(r'\D', '', phone)
    
    # Check if it's a valid length (10-15 digits)
    return 10 <= len(digits) <= 15

def validate_whatsapp_number(phone: str) -> bool:
    """
    Validate WhatsApp phone number format
    
    Args:
        phone (str): Phone number to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not phone:
        return False
    
    # WhatsApp format: whatsapp:+1234567890
    if phone.startswith('whatsapp:'):
        phone = phone[9:]  # Remove 'whatsapp:' prefix
    
    if phone.startswith('+'):
        phone = phone[1:]  # Remove '+' prefix
    
    return validate_phone_number(phone)

def validate_payment_amount(amount: Any) -> Optional[float]:
    """
    Validate and convert payment amount
    
    Args:
        amount: Amount to validate
        
    Returns:
        Optional[float]: Valid amount or None if invalid
    """
    try:
        amount_float = float(amount)
        
        # Check if amount is positive and reasonable
        if 0 < amount_float <= 1000000:  # Max 1M Naira
            return amount_float
    except (ValueError, TypeError):
        pass
    
    return None

def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename for safe storage
    
    Args:
        filename (str): Original filename
        
    Returns:
        str: Sanitized filename
    """
    if not filename:
        return "unknown"
    
    # Remove path separators and dangerous characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Remove leading/trailing dots and spaces
    filename = filename.strip('. ')
    
    # Ensure it's not empty
    if not filename:
        return "unknown"
    
    return filename

def validate_file_extension(filename: str, allowed_extensions: set) -> bool:
    """
    Validate file extension
    
    Args:
        filename (str): Filename to check
        allowed_extensions (set): Set of allowed extensions
        
    Returns:
        bool: True if extension is allowed
    """
    if not filename or '.' not in filename:
        return False
    
    extension = filename.rsplit('.', 1)[1].lower()
    return extension in allowed_extensions