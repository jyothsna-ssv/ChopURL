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
