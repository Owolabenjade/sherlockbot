# utils/text_utils.py - Text processing utilities
import re
import string
from typing import List, Dict

def clean_text(text: str) -> str:
    """
    Clean and normalize text
    
    Args:
        text (str): Input text
        
    Returns:
        str: Cleaned text
    """
    if not text:
        return ""
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove non-printable characters
    text = ''.join(char for char in text if char.isprintable())
    
    # Strip leading/trailing whitespace
    return text.strip()

def extract_keywords(text: str, min_length: int = 3) -> List[str]:
    """
    Extract keywords from text
    
    Args:
        text (str): Input text
        min_length (int): Minimum keyword length
        
    Returns:
        List[str]: List of keywords
    """
    if not text:
        return []
    
    # Convert to lowercase and remove punctuation
    text = text.lower()
    text = text.translate(str.maketrans('', '', string.punctuation))
    
    # Split into words
    words = text.split()
    
    # Filter words by length and common stop words
    stop_words = {
        'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
        'by', 'from', 'up', 'about', 'into', 'through', 'during', 'before',
        'after', 'above', 'below', 'between', 'among', 'is', 'are', 'was',
        'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does',
        'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must',
        'can', 'shall', 'this', 'that', 'these', 'those', 'i', 'me', 'my',
        'myself', 'we', 'our', 'ours', 'ourselves', 'you', 'your', 'yours',
        'yourself', 'yourselves', 'he', 'him', 'his', 'himself', 'she', 'her',
        'hers', 'herself', 'it', 'its', 'itself', 'they', 'them', 'their',
        'theirs', 'themselves'
    }
    
    keywords = []
    for word in words:
        if len(word) >= min_length and word not in stop_words:
            keywords.append(word)
    
    # Remove duplicates while preserving order
    return list(dict.fromkeys(keywords))

def format_phone_number(phone: str) -> str:
    """
    Format phone number for WhatsApp
    
    Args:
        phone (str): Input phone number
        
    Returns:
        str: Formatted phone number
    """
    if not phone:
        return ""
    
    # Remove all non-digit characters
    digits = re.sub(r'\D', '', phone)
    
    # Add country code if missing (assuming Nigeria +234)
    if len(digits) == 10 and digits.startswith('0'):
        digits = '234' + digits[1:]
    elif len(digits) == 11 and digits.startswith('0'):
        digits = '234' + digits[1:]
    
    return f"+{digits}"

def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text to specified length
    
    Args:
        text (str): Input text
        max_length (int): Maximum length
        suffix (str): Suffix to add if truncated
        
    Returns:
        str: Truncated text
    """
    if not text or len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix