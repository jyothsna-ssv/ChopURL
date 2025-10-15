import hashlib
import secrets
import string
from app.core.config import settings

def generate_short_code(length: int = None) -> str:
    """Generate a random short code for URL shortening"""
    if length is None:
        length = settings.SHORT_URL_LENGTH
    
    # Use a combination of letters and numbers for better readability
    characters = string.ascii_letters + string.digits
    
    # Generate random short code
    short_code = ''.join(secrets.choice(characters) for _ in range(length))
    
    return short_code

def generate_hash_based_code(url: str, length: int = None) -> str:
    """Generate a short code based on URL hash (deterministic)"""
    if length is None:
        length = settings.SHORT_URL_LENGTH
    
    # Create hash of the URL
    url_hash = hashlib.md5(url.encode()).hexdigest()
    
    # Take first N characters and convert to base62-like encoding
    characters = string.ascii_letters + string.digits
    short_code = ""
    
    # Convert hash to our character set
    hash_int = int(url_hash[:8], 16)  # Use first 8 hex chars
    base = len(characters)
    
    while hash_int > 0 and len(short_code) < length:
        short_code = characters[hash_int % base] + short_code
        hash_int //= base
    
    # Ensure we have the right length
    while len(short_code) < length:
        short_code = characters[0] + short_code
    
    return short_code[:length]
